import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.layers import Dense, Flatten, Conv2D, Input, concatenate
from tensorflow.keras.optimizers import Adam
import chess
import chess.pgn
import chess.engine
import io
import requests
import bz2
import os
from datetime import datetime, timedelta
import time

# [Previous code remains the same until ChessDatabase class]

class ChessDatabase:
    def __init__(self):
        self.base_url = "https://database.lichess.org"
        self.download_dir = "chess_data"
        
    def get_sample_games(self):
        """Return some sample chess games for offline training"""
        return """
[Event "Sample Game 1"]
[White "Player1"]
[Black "Player2"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7 6. Re1 b5 7. Bb3 d6 8. c3 O-O 9. h3 Na5 10. Bc2 c5 11. d4 Qc7 1-0

[Event "Sample Game 2"]
[White "Player3"]
[Black "Player4"]
[Result "0-1"]

1. d4 Nf6 2. c4 g6 3. Nc3 Bg7 4. e4 d6 5. Nf3 O-O 6. Be2 e5 7. O-O Nc6 8. d5 Ne7 9. Ne1 Nd7 10. Nd3 f5 0-1

[Event "Sample Game 3"]
[White "Player5"]
[Black "Player6"]
[Result "1/2-1/2"]

1. e4 c5 2. Nf3 d6 3. d4 cxd4 4. Nxd4 Nf6 5. Nc3 a6 6. Be2 e6 7. O-O Be7 8. f4 O-O 9. Kh1 Qc7 1/2-1/2
"""
        
    def download_latest_games(self, num_files=1):
        """Try to download games from Lichess, fall back to sample games if unavailable"""
        try:
            if not os.path.exists(self.download_dir):
                os.makedirs(self.download_dir)
                
            print("Attempting to fetch games from Lichess...")
            response = requests.get(f"{self.base_url}/master/entry/count", timeout=5)
            if response.status_code != 200:
                print("Could not access Lichess database, using sample games instead.")
                return self.get_sample_games()
                
            pgn_data = []
            date = datetime.now()
            
            for _ in range(num_files):
                date_str = date.strftime("%Y-%m")
                filename = f"lichess_db_master_{date_str}.pgn.bz2"
                local_path = os.path.join(self.download_dir, filename)
                
                if not os.path.exists(local_path):
                    print(f"Downloading {filename}...")
                    response = requests.get(f"{self.base_url}/master/{filename}", stream=True, timeout=10)
                    if response.status_code == 200:
                        with open(local_path, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                f.write(chunk)
                    else:
                        print(f"Failed to download {filename}, using sample games instead.")
                        return self.get_sample_games()
                
                print(f"Processing {filename}...")
                with bz2.open(local_path, 'rt') as f:
                    pgn_data.append(f.read())
                
                date = date.replace(day=1) - timedelta(days=1)
            
            return "\n".join(pgn_data)
            
        except Exception as e:
            print(f"Error accessing online database: {str(e)}")
            print("Using sample games for training instead.")
            return self.get_sample_games()

# [Rest of the code remains the same]

class ChessML:
    def __init__(self):
        self.model = self._build_model()
        self.evaluator = PositionEvaluator()
        
    def train_on_pgn(self, pgn_data, num_games=1000):
        X_board = []
        X_eval = []
        y = []
        
        games = io.StringIO(pgn_data)
        game_count = 0
        
        while game_count < num_games:
            game = chess.pgn.read_game(games)
            if game is None:
                break
                
            board = game.board()
            for move in game.mainline_moves():
                X_board.append(self._board_to_matrix(board))
                X_eval.append([self.evaluator.evaluate_position(board)])
                
                # Create move vector
                move_vector = np.zeros(4096)
                move_idx = move.from_square * 64 + move.to_square
                move_vector[move_idx] = 1
                y.append(move_vector)
                
                board.push(move)
            
            game_count += 1
            if game_count % 10 == 0:
                print(f"Processed {game_count} games...")
        
        if not X_board:
            raise ValueError("No valid games found in PGN data")
        
        X_board = np.array(X_board)
        X_eval = np.array(X_eval)
        y = np.array(y)
        
        print(f"Training on {len(X_board)} positions...")
        # Reduce training epochs for sample games
        epochs = 3 if len(X_board) < 100 else 10
        self.model.fit(
            [X_board, X_eval],
            y,
            epochs=epochs,
            batch_size=32,
            validation_split=0.2
        )

# [Rest of the code remains the same until main]

if __name__ == "__main__":
    try:
        game = ChessGame()
        print("Initializing AI...")
        game.initialize_ai()
        game.play()
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        print("Please make sure all required packages are installed:")
        print("pip install numpy tensorflow python-chess requests")

class PositionEvaluator:
    def __init__(self):
        self.piece_values = {
            chess.PAWN: 100,
            chess.KNIGHT: 320,
            chess.BISHOP: 330,
            chess.ROOK: 500,
            chess.QUEEN: 900,
            chess.KING: 20000
        }
        
        # Piece-Square tables for position evaluation
        self.pst = {
            chess.PAWN: np.array([
                [0,  0,  0,  0,  0,  0,  0,  0],
                [50, 50, 50, 50, 50, 50, 50, 50],
                [10, 10, 20, 30, 30, 20, 10, 10],
                [5,  5, 10, 25, 25, 10,  5,  5],
                [0,  0,  0, 20, 20,  0,  0,  0],
                [5, -5,-10,  0,  0,-10, -5,  5],
                [5, 10, 10,-20,-20, 10, 10,  5],
                [0,  0,  0,  0,  0,  0,  0,  0]
            ]),
            chess.KNIGHT: np.array([
                [-50,-40,-30,-30,-30,-30,-40,-50],
                [-40,-20,  0,  0,  0,  0,-20,-40],
                [-30,  0, 10, 15, 15, 10,  0,-30],
                [-30,  5, 15, 20, 20, 15,  5,-30],
                [-30,  0, 15, 20, 20, 15,  0,-30],
                [-30,  5, 10, 15, 15, 10,  5,-30],
                [-40,-20,  0,  5,  5,  0,-20,-40],
                [-50,-40,-30,-30,-30,-30,-40,-50]
            ])
            # Add more piece-square tables for other pieces...
        }
    
    def evaluate_position(self, board):
        if board.is_checkmate():
            return -float('inf') if board.turn else float('inf')
        if board.is_stalemate() or board.is_insufficient_material():
            return 0
            
        score = 0
        
        # Material evaluation
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece is not None:
                value = self.piece_values[piece.piece_type]
                if piece.color == chess.WHITE:
                    score += value
                    # Add position bonus from piece-square tables
                    if piece.piece_type in self.pst:
                        score += self.pst[piece.piece_type][7 - chess.square_rank(square)][chess.square_file(square)]
                else:
                    score -= value
                    if piece.piece_type in self.pst:
                        score -= self.pst[piece.piece_type][chess.square_rank(square)][chess.square_file(square)]
        
        # Mobility evaluation
        mobility = len(list(board.legal_moves))
        if not board.turn:
            mobility = -mobility
        score += mobility * 10
        
        # King safety
        w_king_square = board.king(chess.WHITE)
        b_king_square = board.king(chess.BLACK)
        if w_king_square:
            score += self._evaluate_king_safety(board, w_king_square, chess.WHITE)
        if b_king_square:
            score -= self._evaluate_king_safety(board, b_king_square, chess.BLACK)
            
        return score
    
    def _evaluate_king_safety(self, board, king_square, color):
        score = 0
        # Castling rights
        if color == chess.WHITE:
            if board.has_kingside_castling_rights(chess.WHITE):
                score += 60
            if board.has_queenside_castling_rights(chess.WHITE):
                score += 40
        else:
            if board.has_kingside_castling_rights(chess.BLACK):
                score += 60
            if board.has_queenside_castling_rights(chess.BLACK):
                score += 40
        
        # Pawn shield
        score += self._evaluate_pawn_shield(board, king_square, color)
        return score
    
    def _evaluate_pawn_shield(self, board, king_square, color):
        score = 0
        rank = chess.square_rank(king_square)
        file = chess.square_file(king_square)
        
        # Check pawns in front of king
        pawn_ranks = range(rank - 1, rank - 3, -1) if color == chess.WHITE else range(rank + 1, rank + 3)
        for r in pawn_ranks:
            if 0 <= r <= 7:
                for f in range(max(0, file - 1), min(8, file + 2)):
                    square = chess.square(f, r)
                    piece = board.piece_at(square)
                    if piece and piece.piece_type == chess.PAWN and piece.color == color:
                        score += 10
        return score

class ChessML:
    def __init__(self):
        self.model = self._build_model()
        self.evaluator = PositionEvaluator()
        
    def _build_model(self):
        # Board input
        board_input = Input(shape=(8, 8, 12))
        
        # Convolutional layers for pattern recognition
        x = Conv2D(64, (3, 3), activation='relu', padding='same')(board_input)
        x = Conv2D(128, (3, 3), activation='relu', padding='same')(x)
        x = Conv2D(256, (3, 3), activation='relu', padding='same')(x)
        x = Flatten()(x)
        
        # Position evaluation input
        eval_input = Input(shape=(1,))
        
        # Combine board features with position evaluation
        combined = concatenate([x, eval_input])
        
        # Dense layers for move prediction
        x = Dense(1024, activation='relu')(combined)
        x = Dense(512, activation='relu')(x)
        outputs = Dense(4096, activation='softmax')(x)
        
        model = Model(inputs=[board_input, eval_input], outputs=outputs)
        model.compile(optimizer=Adam(learning_rate=0.001),
                     loss='categorical_crossentropy',
                     metrics=['accuracy'])
        return model
    
    def _board_to_matrix(self, board):
        matrix = np.zeros((8, 8, 12))
        piece_to_channel = {
            'P': 0, 'R': 1, 'N': 2, 'B': 3, 'Q': 4, 'K': 5,
            'p': 6, 'r': 7, 'n': 8, 'b': 9, 'q': 10, 'k': 11
        }
        
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece is not None:
                rank = chess.square_rank(square)
                file = chess.square_file(square)
                piece_symbol = piece.symbol()
                channel = piece_to_channel[piece_symbol]
                matrix[rank, file, channel] = 1
        
        return matrix
    
    def train_on_pgn(self, pgn_data, num_games=1000):
        X_board = []
        X_eval = []
        y = []
        
        games = io.StringIO(pgn_data)
        game_count = 0
        
        while game_count < num_games:
            game = chess.pgn.read_game(games)
            if game is None:
                break
                
            board = game.board()
            for move in game.mainline_moves():
                X_board.append(self._board_to_matrix(board))
                X_eval.append([self.evaluator.evaluate_position(board)])
                
                # Create move vector
                move_vector = np.zeros(4096)
                move_idx = move.from_square * 64 + move.to_square
                move_vector[move_idx] = 1
                y.append(move_vector)
                
                board.push(move)
            
            game_count += 1
            if game_count % 10 == 0:
                print(f"Processed {game_count} games...")
        
        if not X_board:
            raise ValueError("No valid games found in PGN data")
        
        X_board = np.array(X_board)
        X_eval = np.array(X_eval)
        y = np.array(y)
        
        print(f"Training on {len(X_board)} positions...")
        self.model.fit(
            [X_board, X_eval],
            y,
            epochs=10,
            batch_size=32,
            validation_split=0.2
        )
    
    def predict_move(self, board):
        board_matrix = self._board_to_matrix(board)
        eval_score = self.evaluator.evaluate_position(board)
        
        # Predict move probabilities
        move_probabilities = self.model.predict(
            [np.expand_dims(board_matrix, 0), np.array([[eval_score]])]
        )[0]
        
        # Get top moves and filter for legality
        legal_moves = list(board.legal_moves)
        move_scores = []
        
        for move in legal_moves:
            move_idx = move.from_square * 64 + move.to_square
            probability = move_probabilities[move_idx]
            
            # Make move on temporary board for evaluation
            temp_board = board.copy()
            temp_board.push(move)
            eval_after_move = self.evaluator.evaluate_position(temp_board)
            
            # Combine probability with position evaluation
            move_score = probability * 0.4 + eval_after_move * 0.6
            move_scores.append((move, move_score))
        
        if not move_scores:
            return None
            
        # Select best move
        best_move = max(move_scores, key=lambda x: x[1])[0]
        return best_move.from_square, best_move.to_square

class ChessGame:
    def __init__(self):
        self.board = chess.Board()
        self.ai = ChessML()
        self.db = ChessDatabase()
        
    def initialize_ai(self):
        print("Downloading training data...")
        pgn_data = self.db.download_latest_games(num_files=1)
        print("Training AI...")
        self.ai.train_on_pgn(pgn_data)
        print("AI training complete!")
    
    def display_board(self):
        print("\n  a b c d e f g h")
        print("  ---------------")
        for rank in range(7, -1, -1):
            print(f"{rank+1}|", end=" ")
            for file in range(8):
                piece = self.board.piece_at(chess.square(file, rank))
                if piece is None:
                    print(".", end=" ")
                else:
                    print(piece.symbol(), end=" ")
            print(f"|{rank+1}")
        print("  ---------------")
        print("  a b c d e f g h\n")
        # [Previous code remains the same until the play() method in ChessGame class]

    def play(self):
        try:
            print("Welcome to Chess AI!")
            print("Enter moves in algebraic notation (e.g., 'e2e4')")
            print("Commands: 'quit' to exit, 'board' to show the board")
            
            color = input("Choose your color (white/black): ").lower()
            human_white = color.startswith('w')
            
            while not self.board.is_game_over():
                self.display_board()
                
                if self.board.turn == human_white:
                    # Human's turn
                    while True:
                        move_str = input("Your move: ")
                        if move_str == 'quit':
                            return
                        if move_str == 'board':
                            self.display_board()
                            continue
                        
                        # Handle move input
                        try:
                            move = chess.Move.from_uci(move_str)
                            if move in self.board.legal_moves:
                                self.board.push(move)
                                break
                            else:
                                print("Illegal move!")
                        except ValueError:
                            print("Invalid move format! Use format 'e2e4'")
                else:
                    # AI's turn
                    print("AI is thinking...")
                    start_time = time.time()
                    from_square, to_square = self.ai.predict_move(self.board)
                    move = chess.Move(from_square, to_square)
                    self.board.push(move)
                    end_time = time.time()
                    print("AI moves:", move.uci(), "(took {:.1f}s)".format(end_time - start_time))
            
            # Game over
            self.display_board()
            result = self.board.outcome()
            if result.winner is None:
                print("Game drawn!")
            else:
                winner = "White" if result.winner else "Black"
                print(f"{winner} wins!")
                
        except KeyboardInterrupt:
            print("\nGame interrupted!")
        except Exception as e:
            print("An error occurred:", str(e))

# Add a main block to run the game
if __name__ == "__main__":
    game = ChessGame()
    print("Initializing AI...")
    game.initialize_ai()
    game.play()