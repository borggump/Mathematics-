"""
analyze.py
──────────
Run pre-built analyses on the processed chess database and export results.

Usage:
    python analyze.py --all                    # Run every analysis
    python analyze.py --openings --top 20      # Top 20 openings
    python analyze.py --players --min-games 50 # Player leaderboard
    python analyze.py --elo-buckets            # Stats by rating range
    python analyze.py --trends                 # Monthly trends
    python analyze.py --export csv             # Export all to CSV
    python analyze.py --export html            # Export interactive HTML report
"""

import argparse
import json
from pathlib import Path
from datetime import datetime

import duckdb
import pandas as pd


DB_PATH = "./data/chess.duckdb"
REPORTS_DIR = Path("./reports")


def connect(db_path=DB_PATH):
    return duckdb.connect(db_path, read_only=True)


# ── Individual analyses ────────────────────────────────────────────────────────

def top_openings(con, top_n=20, time_control=None, min_games=100):
    tc_filter = f"AND time_control_name = '{time_control}'" if time_control else ""
    return con.execute(f"""
        SELECT eco, opening, time_control_name, games,
               white_win_pct, draw_pct,
               ROUND(100 - white_win_pct - draw_pct, 2) AS black_win_pct,
               avg_game_length
        FROM opening_stats
        WHERE games >= {min_games} {tc_filter}
        ORDER BY games DESC
        LIMIT {top_n}
    """).df()


def opening_win_rates(con, min_games=500, time_control="Blitz"):
    """Best and worst openings for White."""
    return con.execute(f"""
        SELECT eco, opening, games, white_win_pct, draw_pct,
               ROUND(100 - white_win_pct - draw_pct, 2) AS black_win_pct
        FROM opening_stats
        WHERE games >= {min_games}
          AND time_control_name = '{time_control}'
        ORDER BY white_win_pct DESC
    """).df()


def player_leaderboard(con, top_n=50, min_games=100):
    return con.execute(f"""
        SELECT player, games_played, win_pct, avg_elo, peak_elo, avg_game_length
        FROM player_stats
        WHERE games_played >= {min_games}
        ORDER BY games_played DESC
        LIMIT {top_n}
    """).df()


def most_improved_openings(con, min_games=200):
    """Openings whose white win rate deviates most from average."""
    return con.execute(f"""
        WITH avg_rate AS (
            SELECT AVG(white_win_pct) AS global_avg FROM opening_stats WHERE games >= {min_games}
        )
        SELECT eco, opening, time_control_name, games, white_win_pct,
               ROUND(white_win_pct - (SELECT global_avg FROM avg_rate), 2) AS delta_vs_avg
        FROM opening_stats
        WHERE games >= {min_games}
        ORDER BY delta_vs_avg DESC
        LIMIT 20
    """).df()


def elo_bucket_analysis(con):
    return con.execute("""
        SELECT elo_bucket, time_control_name, games, avg_moves,
               white_win_pct, timeout_pct
        FROM elo_bucket_stats
        ORDER BY elo_bucket, time_control_name
    """).df()


def monthly_trends(con):
    return con.execute("""
        SELECT month, time_control_name, games, avg_elo, avg_moves, draw_pct
        FROM monthly_trends
        ORDER BY month, time_control_name
    """).df()


def termination_breakdown(con):
    return con.execute("""
        SELECT termination, time_control_name, games, pct_of_tc
        FROM termination_stats
        ORDER BY time_control_name, games DESC
    """).df()


def move_time_analysis(con):
    """Average move time by elo bucket and game phase (requires clock data)."""
    return con.execute("""
        SELECT
            CASE
                WHEN (white_elo+black_elo)/2 < 1400 THEN '<1400'
                WHEN (white_elo+black_elo)/2 < 1800 THEN '1400-1800'
                WHEN (white_elo+black_elo)/2 < 2200 THEN '1800-2200'
                ELSE '2200+'
            END AS elo_range,
            time_control_name,
            ROUND(AVG(avg_white_move_time), 2) AS avg_white_sec_per_move,
            ROUND(AVG(avg_black_move_time), 2) AS avg_black_sec_per_move,
            COUNT(*) AS games
        FROM games
        WHERE avg_white_move_time IS NOT NULL
          AND white_elo IS NOT NULL AND black_elo IS NOT NULL
        GROUP BY elo_range, time_control_name
        ORDER BY elo_range, time_control_name
    """).df()


def summary_stats(con):
    return con.execute("""
        SELECT
            COUNT(*)                                                   AS total_games,
            COUNT(DISTINCT white)                                      AS unique_players,
            MIN(date)                                                  AS earliest_date,
            MAX(date)                                                  AS latest_date,
            ROUND(AVG(num_moves), 1)                                   AS avg_game_length,
            ROUND(AVG(CASE WHEN winner='white' THEN 1.0 ELSE 0.0 END) * 100, 2) AS white_win_pct,
            ROUND(AVG(CASE WHEN winner='draw'  THEN 1.0 ELSE 0.0 END) * 100, 2) AS draw_pct
        FROM games
    """).df()


# ── HTML Report Generator ──────────────────────────────────────────────────────

def df_to_html_table(df: pd.DataFrame, title: str) -> str:
    rows = df.to_html(index=False, classes="data-table", border=0)
    return f"""
    <section>
        <h2>{title}</h2>
        {rows}
    </section>
    """


def generate_html_report(con, out_path: Path):
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    summary = summary_stats(con)
    s = summary.iloc[0]

    sections = []
    sections.append(df_to_html_table(top_openings(con, top_n=30), "Top 30 Openings (All Time Controls)"))
    sections.append(df_to_html_table(opening_win_rates(con, min_games=500, time_control="Blitz"), "Blitz Opening Win Rates"))
    sections.append(df_to_html_table(player_leaderboard(con, top_n=50), "Most Active Players"))
    sections.append(df_to_html_table(elo_bucket_analysis(con), "Stats by ELO Bucket"))
    sections.append(df_to_html_table(monthly_trends(con), "Monthly Trends"))
    sections.append(df_to_html_table(termination_breakdown(con), "Game Termination Breakdown"))
    sections.append(df_to_html_table(move_time_analysis(con), "Move Time by ELO Range"))

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Lichess Analytics Report</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
          background: #0f0f0f; color: #e0e0e0; padding: 24px; }}
  h1 {{ color: #b0d090; font-size: 2rem; margin-bottom: 8px; }}
  .subtitle {{ color: #888; margin-bottom: 32px; font-size: 0.9rem; }}
  .kpi-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px,1fr));
               gap: 16px; margin-bottom: 40px; }}
  .kpi {{ background: #1a1a2e; border: 1px solid #2a2a4a; border-radius: 8px;
          padding: 16px; text-align: center; }}
  .kpi-value {{ font-size: 1.6rem; font-weight: bold; color: #b0d090; }}
  .kpi-label {{ font-size: 0.75rem; color: #888; margin-top: 4px; text-transform: uppercase; }}
  section {{ margin-bottom: 48px; }}
  h2 {{ color: #7ab0d0; font-size: 1.2rem; margin-bottom: 12px;
        border-bottom: 1px solid #2a2a4a; padding-bottom: 8px; }}
  .data-table {{ width: 100%; border-collapse: collapse; font-size: 0.85rem; }}
  .data-table th {{ background: #1a1a2e; color: #7ab0d0; padding: 8px 12px;
                    text-align: left; border-bottom: 2px solid #2a2a4a; }}
  .data-table td {{ padding: 7px 12px; border-bottom: 1px solid #1e1e1e; }}
  .data-table tr:hover td {{ background: #1a1a2e; }}
  .footer {{ color: #555; font-size: 0.75rem; margin-top: 48px; text-align: center; }}
</style>
</head>
<body>
<h1>♟ Lichess Analytics Report</h1>
<p class="subtitle">Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} · Lichess rated standard games</p>

<div class="kpi-grid">
  <div class="kpi"><div class="kpi-value">{int(s['total_games']):,}</div><div class="kpi-label">Total Games</div></div>
  <div class="kpi"><div class="kpi-value">{int(s['unique_players']):,}</div><div class="kpi-label">Unique Players</div></div>
  <div class="kpi"><div class="kpi-value">{s['avg_game_length']}</div><div class="kpi-label">Avg Game Length</div></div>
  <div class="kpi"><div class="kpi-value">{s['white_win_pct']}%</div><div class="kpi-label">White Win Rate</div></div>
  <div class="kpi"><div class="kpi-value">{s['draw_pct']}%</div><div class="kpi-label">Draw Rate</div></div>
  <div class="kpi"><div class="kpi-value">{s['earliest_date']}–{s['latest_date']}</div><div class="kpi-label">Date Range</div></div>
</div>

{"".join(sections)}

<div class="footer">Pipeline built with python-chess · DuckDB · PyArrow</div>
</body>
</html>"""

    with open(out_path, "w") as f:
        f.write(html)
    print(f"Report saved to {out_path}")


# ── CLI ────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Lichess Chess Analyzer")
    parser.add_argument("--db",           default=DB_PATH)
    parser.add_argument("--all",          action="store_true", help="Run all analyses")
    parser.add_argument("--summary",      action="store_true")
    parser.add_argument("--openings",     action="store_true")
    parser.add_argument("--players",      action="store_true")
    parser.add_argument("--elo-buckets",  action="store_true")
    parser.add_argument("--trends",       action="store_true")
    parser.add_argument("--terminations", action="store_true")
    parser.add_argument("--move-times",   action="store_true")
    parser.add_argument("--top",          type=int, default=20)
    parser.add_argument("--min-games",    type=int, default=100)
    parser.add_argument("--time-control", default=None,
                        choices=["UltraBullet","Bullet","Blitz","Rapid","Classical"])
    parser.add_argument("--export",       choices=["csv", "html", "both"], default=None)
    args = parser.parse_args()

    con = connect(args.db)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    def show(df, title):
        print(f"\n{'─'*60}")
        print(f"  {title}")
        print('─'*60)
        print(df.to_string(index=False))

    if args.all or args.summary:
        show(summary_stats(con), "Summary Statistics")

    if args.all or args.openings:
        show(top_openings(con, top_n=args.top, time_control=args.time_control,
                          min_games=args.min_games), "Top Openings")
        show(most_improved_openings(con), "Openings with Highest White Win Advantage")

    if args.all or args.players:
        show(player_leaderboard(con, top_n=args.top, min_games=args.min_games), "Player Leaderboard")

    if args.all or args.elo_buckets:
        show(elo_bucket_analysis(con), "Stats by ELO Bucket")

    if args.all or args.trends:
        show(monthly_trends(con), "Monthly Trends")

    if args.all or args.terminations:
        show(termination_breakdown(con), "Termination Breakdown")

    if args.all or args.move_times:
        show(move_time_analysis(con), "Move Time Analysis")

    if args.export in ("csv", "both"):
        analyses = {
            "openings":      top_openings(con, top_n=200),
            "players":       player_leaderboard(con, top_n=500),
            "elo_buckets":   elo_bucket_analysis(con),
            "monthly":       monthly_trends(con),
            "terminations":  termination_breakdown(con),
        }
        for name, df in analyses.items():
            path = REPORTS_DIR / f"{name}.csv"
            df.to_csv(path, index=False)
            print(f"Exported {path}")

    if args.export in ("html", "both"):
        generate_html_report(con, REPORTS_DIR / "report.html")

    con.close()


if __name__ == "__main__":
    main()
