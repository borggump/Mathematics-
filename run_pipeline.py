"""
run_pipeline.py
───────────────
Main entry point for the Lichess chess pipeline.

Processes .pgn.zst files → Parquet (columnar storage) → DuckDB (SQL analytics)

Usage examples:
    # Process all files in ./data/raw/
    python run_pipeline.py

    # Test on first 10,000 games from one file
    python run_pipeline.py --file data/raw/lichess_db_standard_rated_2024-05.pgn.zst --limit 10000

    # Process only Blitz games, skip clocks for speed
    python run_pipeline.py --time-controls Blitz --no-clocks

    # Process then launch SQL explorer
    python run_pipeline.py --query

    # Rebuild DuckDB from existing Parquet files (skip re-parsing)
    python run_pipeline.py --parquet-only
"""

import argparse
import logging
import time
from pathlib import Path
from typing import Optional

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import duckdb

from pgn_parser import parse_pgn_zst, GameRecord

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# ── PyArrow Schema (strongly typed = fast Parquet) ────────────────────────────

SCHEMA = pa.schema([
    pa.field("game_id",               pa.string()),
    pa.field("month",                 pa.string()),
    pa.field("white",                 pa.string()),
    pa.field("black",                 pa.string()),
    pa.field("white_elo",             pa.int16()),
    pa.field("black_elo",             pa.int16()),
    pa.field("white_rd",              pa.int16()),
    pa.field("black_rd",              pa.int16()),
    pa.field("result",                pa.string()),
    pa.field("winner",                pa.string()),
    pa.field("termination",           pa.string()),
    pa.field("time_control",          pa.string()),
    pa.field("time_control_name",     pa.string()),
    pa.field("base_time",             pa.int32()),
    pa.field("increment",             pa.int32()),
    pa.field("eco",                   pa.string()),
    pa.field("opening",               pa.string()),
    pa.field("num_moves",             pa.int16()),
    pa.field("date",                  pa.string()),
    pa.field("utc_datetime",          pa.string()),
    pa.field("avg_white_move_time",   pa.float32()),
    pa.field("avg_black_move_time",   pa.float32()),
    pa.field("first_10_moves",        pa.string()),
])


# ── File → Parquet ─────────────────────────────────────────────────────────────

def process_file(
    pgn_path: Path,
    parquet_dir: Path,
    chunk_size: int = 50_000,
    limit: Optional[int] = None,
    time_controls: Optional[list[str]] = None,
    min_elo: Optional[int] = None,
    include_clocks: bool = True,
    include_moves: bool = True,
    overwrite: bool = False,
) -> Path:
    """
    Parse one .pgn.zst file and write partitioned Parquet files.

    Returns path to the output Parquet directory for this month.
    """
    month = pgn_path.stem.split("rated_")[-1].replace(".pgn", "")
    out_dir = parquet_dir / f"month={month}"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Skip if already processed
    existing = list(out_dir.glob("*.parquet"))
    if existing and not overwrite:
        log.info(f"[{month}] Already processed ({len(existing)} chunk files). Use --overwrite to redo.")
        return out_dir

    log.info(f"[{month}] Starting — {pgn_path.stat().st_size / 1e9:.1f} GB compressed")
    t0 = time.time()

    writer = None
    chunk: list[dict] = []
    total = 0
    chunks_written = 0

    def flush(chunk_data: list[dict], chunk_idx: int):
        nonlocal writer
        df = pd.DataFrame(chunk_data)
        # Cast nullable ints to avoid pyarrow issues
        for col in ["white_elo", "black_elo", "white_rd", "black_rd", "base_time", "increment", "num_moves"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        table = pa.Table.from_pandas(df, schema=SCHEMA, safe=False)
        out_path = out_dir / f"chunk_{chunk_idx:05d}.parquet"
        pq.write_table(table, out_path, compression="snappy")
        return len(chunk_data)

    for rec in parse_pgn_zst(
        pgn_path,
        max_games=limit,
        include_clocks=include_clocks,
        include_moves=include_moves,
    ):
        # Apply filters
        if time_controls and rec.time_control_name not in time_controls:
            continue
        if min_elo:
            if rec.white_elo is None or rec.black_elo is None:
                continue
            if rec.white_elo < min_elo or rec.black_elo < min_elo:
                continue

        chunk.append(rec.to_dict())

        if len(chunk) >= chunk_size:
            n = flush(chunk, chunks_written)
            total += n
            chunks_written += 1
            elapsed = time.time() - t0
            rate = total / elapsed
            log.info(f"[{month}] {total:,} games  |  {rate:,.0f} games/sec  |  chunk {chunks_written}")
            chunk = []

    # Final partial chunk
    if chunk:
        n = flush(chunk, chunks_written)
        total += n
        chunks_written += 1

    elapsed = time.time() - t0
    log.info(f"[{month}] ✓ Done — {total:,} games in {elapsed:.0f}s  ({total/elapsed:,.0f}/sec)")
    return out_dir


# ── Build DuckDB ───────────────────────────────────────────────────────────────

def build_duckdb(parquet_dir: Path, db_path: Path):
    """
    Register all Parquet files with DuckDB and create analytical views.
    """
    log.info(f"Building DuckDB at {db_path} ...")
    con = duckdb.connect(str(db_path))

    # Main games table (lazy view over Parquet)
    con.execute(f"""
        CREATE OR REPLACE VIEW games AS
        SELECT * FROM read_parquet('{parquet_dir}/**/*.parquet', hive_partitioning=true)
    """)

    # ── Pre-built analytical views ──────────────────────────────────────────

    con.execute("""
        CREATE OR REPLACE VIEW opening_stats AS
        SELECT
            eco,
            opening,
            time_control_name,
            COUNT(*)                                        AS games,
            ROUND(AVG(CASE WHEN winner='white' THEN 1.0
                           WHEN winner='black' THEN 0.0
                           ELSE 0.5 END) * 100, 2)         AS white_win_pct,
            ROUND(AVG(CASE WHEN winner='draw'  THEN 1.0
                           ELSE 0.0 END) * 100, 2)         AS draw_pct,
            ROUND(AVG(num_moves), 1)                       AS avg_game_length
        FROM games
        WHERE eco != ''
        GROUP BY eco, opening, time_control_name
        ORDER BY games DESC
    """)

    con.execute("""
        CREATE OR REPLACE VIEW player_stats AS
        SELECT
            player,
            COUNT(*)                                                   AS games_played,
            ROUND(SUM(won)::FLOAT / COUNT(*) * 100, 2)                 AS win_pct,
            ROUND(AVG(elo), 0)                                         AS avg_elo,
            MAX(elo)                                                    AS peak_elo,
            ROUND(AVG(game_length), 1)                                 AS avg_game_length
        FROM (
            SELECT white AS player, white_elo AS elo,
                   CASE WHEN winner='white' THEN 1 ELSE 0 END AS won,
                   num_moves AS game_length
            FROM games WHERE white_elo IS NOT NULL
            UNION ALL
            SELECT black AS player, black_elo AS elo,
                   CASE WHEN winner='black' THEN 1 ELSE 0 END AS won,
                   num_moves AS game_length
            FROM games WHERE black_elo IS NOT NULL
        )
        GROUP BY player
        HAVING games_played >= 20
        ORDER BY games_played DESC
    """)

    con.execute("""
        CREATE OR REPLACE VIEW elo_bucket_stats AS
        SELECT
            elo_bucket,
            time_control_name,
            COUNT(*)                                          AS games,
            ROUND(AVG(num_moves), 1)                         AS avg_moves,
            ROUND(AVG(CASE WHEN winner='white' THEN 1.0
                           WHEN winner='black' THEN 0.0
                           ELSE 0.5 END) * 100, 2)           AS white_win_pct,
            ROUND(AVG(CASE WHEN termination='Time forfeit'
                           THEN 1.0 ELSE 0.0 END) * 100, 2) AS timeout_pct
        FROM (
            SELECT *,
                CASE
                    WHEN (white_elo+black_elo)/2 < 1000 THEN '<1000'
                    WHEN (white_elo+black_elo)/2 < 1200 THEN '1000-1200'
                    WHEN (white_elo+black_elo)/2 < 1400 THEN '1200-1400'
                    WHEN (white_elo+black_elo)/2 < 1600 THEN '1400-1600'
                    WHEN (white_elo+black_elo)/2 < 1800 THEN '1600-1800'
                    WHEN (white_elo+black_elo)/2 < 2000 THEN '1800-2000'
                    WHEN (white_elo+black_elo)/2 < 2200 THEN '2000-2200'
                    WHEN (white_elo+black_elo)/2 < 2500 THEN '2200-2500'
                    ELSE '2500+'
                END AS elo_bucket
            FROM games
            WHERE white_elo IS NOT NULL AND black_elo IS NOT NULL
        )
        GROUP BY elo_bucket, time_control_name
        ORDER BY elo_bucket, time_control_name
    """)

    con.execute("""
        CREATE OR REPLACE VIEW monthly_trends AS
        SELECT
            month,
            time_control_name,
            COUNT(*)                                              AS games,
            ROUND(AVG((white_elo + black_elo) / 2.0), 0)         AS avg_elo,
            ROUND(AVG(num_moves), 1)                             AS avg_moves,
            ROUND(AVG(CASE WHEN winner='draw' THEN 1.0
                           ELSE 0.0 END) * 100, 2)               AS draw_pct
        FROM games
        WHERE white_elo IS NOT NULL AND black_elo IS NOT NULL
        GROUP BY month, time_control_name
        ORDER BY month, time_control_name
    """)

    con.execute("""
        CREATE OR REPLACE VIEW termination_stats AS
        SELECT
            termination,
            time_control_name,
            COUNT(*)                          AS games,
            ROUND(COUNT(*) * 100.0 /
                SUM(COUNT(*)) OVER (PARTITION BY time_control_name), 2) AS pct_of_tc
        FROM games
        GROUP BY termination, time_control_name
        ORDER BY time_control_name, games DESC
    """)

    # Verify
    n = con.execute("SELECT COUNT(*) FROM games").fetchone()[0]
    log.info(f"DuckDB ready — {n:,} total games indexed")
    con.close()
    return n


# ── Interactive SQL shell ──────────────────────────────────────────────────────

def launch_query_shell(db_path: Path):
    con = duckdb.connect(str(db_path))
    print("\n" + "="*60)
    print("  Lichess Chess Analytics — DuckDB Shell")
    print("="*60)
    print("Available views: games, opening_stats, player_stats,")
    print("                 elo_bucket_stats, monthly_trends, termination_stats")
    print("Type SQL queries. Type 'exit' to quit.\n")

    while True:
        try:
            query = input("chess> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if query.lower() in ("exit", "quit", "\\q"):
            break
        if not query:
            continue
        try:
            result = con.execute(query).df()
            print(result.to_string(index=False))
            print(f"\n({len(result)} rows)\n")
        except Exception as e:
            print(f"Error: {e}\n")
    con.close()


# ── CLI ────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Lichess PGN Pipeline")
    parser.add_argument("--data-dir",      default="./data/raw",     help="Folder with .pgn.zst files")
    parser.add_argument("--parquet-dir",   default="./data/parquet", help="Output Parquet directory")
    parser.add_argument("--db-path",       default="./data/chess.duckdb", help="DuckDB output path")
    parser.add_argument("--file",          default=None,             help="Process single file only")
    parser.add_argument("--limit",         type=int, default=None,   help="Max games per file (testing)")
    parser.add_argument("--chunk-size",    type=int, default=50_000, help="Games per Parquet chunk")
    parser.add_argument("--min-elo",       type=int, default=None,   help="Filter: min ELO for both players")
    parser.add_argument("--time-controls", nargs="+", default=None,
                        choices=["UltraBullet","Bullet","Blitz","Rapid","Classical"],
                        help="Only keep these time controls")
    parser.add_argument("--no-clocks",     action="store_true",      help="Skip clock parsing (faster)")
    parser.add_argument("--no-moves",      action="store_true",      help="Skip move extraction (faster)")
    parser.add_argument("--overwrite",     action="store_true",      help="Re-process already-done months")
    parser.add_argument("--db-only",       action="store_true",      help="Skip parsing, rebuild DuckDB only")
    parser.add_argument("--query",         action="store_true",      help="Launch interactive SQL shell after")
    args = parser.parse_args()

    parquet_dir = Path(args.parquet_dir)
    db_path = Path(args.db_path)
    parquet_dir.mkdir(parents=True, exist_ok=True)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    if not args.db_only:
        if args.file:
            files = [Path(args.file)]
        else:
            files = sorted(Path(args.data_dir).glob("lichess_db_standard_rated_*.pgn.zst"))
            if not files:
                log.error(f"No .pgn.zst files found in {args.data_dir}")
                return

        log.info(f"Found {len(files)} file(s) to process")
        for pgn_path in files:
            process_file(
                pgn_path,
                parquet_dir,
                chunk_size=args.chunk_size,
                limit=args.limit,
                time_controls=args.time_controls,
                min_elo=args.min_elo,
                include_clocks=not args.no_clocks,
                include_moves=not args.no_moves,
                overwrite=args.overwrite,
            )

    build_duckdb(parquet_dir, db_path)

    if args.query:
        launch_query_shell(db_path)


if __name__ == "__main__":
    main()
