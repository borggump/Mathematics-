import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Flatten, Conv2D
from tensorflow.keras.optimizers import Adam
import chess.pgn
import io

class ChessML:
    def __init__(self):
        self.model = self._build_model()
        
    def _build_model(self):
        model = Sequential([
            Conv2D(64, (3, 3), activation='relu', input_shape=(8, 8, 12)),
            Conv2D(128, (3, 3), activation='relu'),
            Conv2D(256, (3, 3), activation='relu'),
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
        piece_mapping = {
            'P': 0, 'R': 1, 'N': 2, 'B': 3, 'Q': 4, 'K': 5,
            'p': 6, 'r': 7, 'n': 8, 'b': 9, 'q': 10, 'k': 11
        }
        
        for i in range(8):
            for j in range(8):
                piece = board[i][j]
                if piece:
                    idx = piece_mapping[piece.symbol.upper() if piece.color == 'white' else piece.symbol.lower()]
                    matrix[i, j, idx] = 1
        return matrix
    
    def _move_to_vector(self, start_pos, end_pos):
        # Convert move to one-hot encoded vector (64*64 = 4096 possibilities)
        vector = np.zeros(4096)
        index = start_pos[0] * 512 + start_pos[1] * 64 + end_pos[0] * 8 + end_pos[1]
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
                
            board = chess.Board()
            for move in game.mainline_moves():
                # Convert board position to matrix
                board_matrix = self._board_to_matrix(board)
                X.append(board_matrix)
                
                # Convert move to target vector
                start_square = move.from_square
                end_square = move.to_square
                start_pos = (start_square // 8, start_square % 8)
                end_pos = (end_square // 8, end_square % 8)
                move_vector = self._move_to_vector(start_pos, end_pos)
                y.append(move_vector)
                
                board.push(move)
        
        X = np.array(X)
        y = np.array(y)
        self.model.fit(X, y, epochs=10, batch_size=32, validation_split=0.2)
    
    def predict_move(self, board):
        board_matrix = self._board_to_matrix(board)
        board_matrix = np.expand_dims(board_matrix, axis=0)
        move_probabilities = self.model.predict(board_matrix)[0]
        
        # Convert the highest probability move back to board coordinates
        move_index = np.argmax(move_probabilities)
        start_x = move_index // 512
        start_y = (move_index % 512) // 64
        end_x = (move_index % 64) // 8
        end_y = move_index % 8
        
        return (start_x, start_y), (end_x, end_y)

class ChessGame:
    # [Previous ChessGame implementation remains the same until the make_move method]
    
    def make_move(self, start_pos, end_pos, is_ai=False):
        start_x, start_y = start_pos
        end_x, end_y = end_pos
        
        piece = self.board[start_x][start_y]
        if not is_ai:  # Only check these conditions for human players
            if piece is None:
                return False, "No piece at start position"
            
            if piece.color != self.current_turn:
                return False, "Not your turn"
            
            valid_moves = piece.valid_moves(self.board, start_pos)
            if end_pos not in valid_moves:
                return False, "Invalid move"
        
        # Make the move
        self.board[end_x][end_y] = piece
        self.board[start_x][start_y] = None
        piece.has_moved = True
        
        # Switch turns
        self.current_turn = 'black' if self.current_turn == 'white' else 'white'
        return True, "Move successful"

def main():
    game = ChessGame()
    ai = ChessML()
    
    # Example PGN data for training (you would need to provide actual master games)
    pgn_data = """
    [Event "Example Game"]
    1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7
    """
    
    print("Training AI on chess master games...")
    ai.train_on_pgn(pgn_data)
    print("Training complete!")
    
    player_color = input("Choose your color (white/black): ").lower()
    ai_color = 'black' if player_color == 'white' else 'white'
    
    while True:
        game.display_board()
        print(f"\n{game.current_turn.capitalize()}'s turn")
        
        if game.current_turn == player_color:
            # Human player's turn
            try:
                start = input("Enter start position (e.g., e2): ")
                if start.lower() == 'quit':
                    break
                end = input("Enter end position (e.g., e4): ")
                
                start_pos = parse_position(start)
                end_pos = parse_position(end)
                
                if start_pos is None or end_pos is None:
                    print("Invalid position format")
                    continue
                
                success, message = game.make_move(start_pos, end_pos)
                print(message)
                
            except KeyboardInterrupt:
                break
            except ValueError:
                print("Invalid input")
        else:
            # AI's turn
            print("AI is thinking...")
            start_pos, end_pos = ai.predict_move(game.board)
            success, message = game.make_move(start_pos, end_pos, is_ai=True)
            if success:
                print(f"AI moves from {chr(start_pos[1] + ord('a'))}{8-start_pos[0]} "
                      f"to {chr(end_pos[1] + ord('a'))}{8-end_pos[0]}")
            else:
                print("AI made an invalid move, game ends")
                break

if __name__ == "__main__":
    main()

# Previous class implementations (Piece, Pawn, Rook, Knight, Bishop, Queen, King) remain the same