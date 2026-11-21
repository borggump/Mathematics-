import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Flatten, Conv2D
from tensorflow.keras.optimizers import Adam
import chess
import chess.pgn
import io

class ChessML:
    def __init__(self):
        self.model = self._build_model()
        
    def _build_model(self):
        model = Sequential([
            Conv2D(64, (3, 3), activation='relu', padding='same', input_shape=(8, 8, 12)),
            Conv2D(128, (3, 3), activation='relu', padding='same'),
            Conv2D(256, (3, 3), activation='relu', padding='same'),
            Flatten(),
            Dense(1024, activation='relu'),
            Dense(512, activation='relu'),
            Dense(4096, activation='softmax')  # 64 squares * 64 squares possible moves
        ])
        
        model.compile(optimizer=Adam(learning_rate=0.001),
                     loss='categorical_crossentropy',
                     metrics=['accuracy'])
        return model
    
    def _board_to_matrix(self, board):
        # Create a 8x8x12 matrix (12 channels for 6 piece types * 2 colors)
        matrix = np.zeros((8, 8, 12))
        
        # Map pieces to channel indices
        piece_to_channel = {
            'P': 0, 'R': 1, 'N': 2, 'B': 3, 'Q': 4, 'K': 5,  # White pieces
            'p': 6, 'r': 7, 'n': 8, 'b': 9, 'q': 10, 'k': 11  # Black pieces
        }
        
        # Iterate through all squares
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece is not None:
                rank = chess.square_rank(square)  # 0-7
                file = chess.square_file(square)  # 0-7
                piece_symbol = piece.symbol()
                channel = piece_to_channel[piece_symbol]
                matrix[rank, file, channel] = 1
                
        return matrix
    
    def _move_to_vector(self, move):
        # Convert chess.Move to one-hot encoded vector
        vector = np.zeros(4096)
        from_square = move.from_square
        to_square = move.to_square
        index = from_square * 64 + to_square
        vector[index] = 1
        return vector

    def train_on_pgn(self, pgn_data, num_games=1000):
        X = []  # Board positions
        y = []  # Moves made
        
        games = io.StringIO(pgn_data)
        for _ in range(num_games):
            game = chess.pgn.read_game(games)
            if game is None:
                break
                
            board = game.board()
            for move in game.mainline_moves():
                # Convert board position to matrix
                X.append(self._board_to_matrix(board))
                # Convert move to target vector
                y.append(self._move_to_vector(move))
                board.push(move)
        
        if not X:  # Check if we have any training data
            raise ValueError("No valid games found in PGN data")
            
        X = np.array(X)
        y = np.array(y)
        print(f"Training on {len(X)} positions...")
        self.model.fit(X, y, epochs=10, batch_size=32, validation_split=0.2)
    
    def predict_move(self, board):
        # Convert python-chess Board to our matrix representation
        if isinstance(board, chess.Board):
            board_matrix = self._board_to_matrix(board)
        else:
            # If using our custom board representation, convert it first
            chess_board = chess.Board()
            # TODO: Convert custom board to python-chess Board
            board_matrix = self._board_to_matrix(chess_board)
            
        board_matrix = np.expand_dims(board_matrix, axis=0)
        move_probabilities = self.model.predict(board_matrix)[0]
        
        # Get the top 10 most likely moves
        top_moves = np.argsort(move_probabilities)[-10:]
        
        # Try moves until we find a legal one
        for move_index in reversed(top_moves):
            from_square = move_index // 64
            to_square = move_index % 64
            move = chess.Move(from_square, to_square)
            if isinstance(board, chess.Board):
                if move in board.legal_moves:
                    return from_square, to_square
            else:
                # If using custom board, convert coordinates
                start_pos = (chess.square_rank(from_square), chess.square_file(from_square))
                end_pos = (chess.square_rank(to_square), chess.square_file(to_square))
                return start_pos, end_pos
                
        # If no legal moves found, return None
        return None

def main():
    # Example PGN data for training
    pgn_data = """
    [Event "Example Game"]
    [Site "?"]
    [Date "2024.01.01"]
    [Round "1"]
    [White "Player1"]
    [Black "Player2"]
    [Result "1-0"]

    1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7 1-0
    """
    
    try:
        print("Initializing AI...")
        ai = ChessML()
        
        print("Training AI on chess master games...")
        ai.train_on_pgn(pgn_data)
        print("Training complete!")
        
        # Initialize a standard chess board for testing
        board = chess.Board()
        
        # Test prediction
        move = ai.predict_move(board)
        if move:
            from_square, to_square = move
            print(f"AI suggests move from {chess.square_name(from_square)} to {chess.square_name(to_square)}")
        else:
            print("No valid moves found")
            
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        print("Please make sure you have installed all required packages:")
        print("pip install tensorflow chess numpy")

if __name__ == "__main__":
    main()