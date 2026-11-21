import chess
import numpy as np
from tensorflow import keras
import logging

class ChessGame:
    def __init__(self):
        self.board = chess.Board()
        self.model = None
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def initialize_model(self):
        """Initialize the neural network model for move prediction"""
        self.model = keras.Sequential([
            keras.layers.Dense(64, input_shape=(64,), activation='relu'),
            keras.layers.Dense(128, activation='relu'),
            keras.layers.Dense(64, activation='relu'),
            keras.layers.Dense(1, activation='sigmoid')
        ])
        self.model.compile(optimizer='adam',
                          loss='binary_crossentropy',
                          metrics=['accuracy'])
        self.logger.info("Model initialized successfully")
    
    def board_to_array(self):
        """Convert chess board to neural network input format"""
        board_array = np.zeros(64)
        piece_values = {
            'P': 1, 'N': 2, 'B': 3, 'R': 4, 'Q': 5, 'K': 6,
            'p': -1, 'n': -2, 'b': -3, 'r': -4, 'q': -5, 'k': -6
        }
        for i in range(64):
            piece = self.board.piece_at(i)
            if piece:
                board_array[i] = piece_values.get(piece.symbol(), 0)
        return board_array
    
    def make_move(self, move_str):
        """Make a move on the board"""
        try:
            move = chess.Move.from_uci(move_str)
            if move in self.board.legal_moves:
                self.board.push(move)
                self.logger.info(f"Move made: {move_str}")
                return True
            else:
                self.logger.warning(f"Illegal move attempted: {move_str}")
                return False
        except ValueError:
            self.logger.error(f"Invalid move format: {move_str}")
            return False
    
    def get_ai_move(self):
        """Get AI's move prediction"""
        if not self.model:
            self.logger.error("Model not initialized")
            return None
            
        legal_moves = list(self.board.legal_moves)
        if not legal_moves:
            return None
            
        # Evaluate all legal moves
        best_move = None
        best_score = float('-inf')
        
        for move in legal_moves:
            self.board.push(move)
            position = self.board_to_array()
            score = self.model.predict(position.reshape(1, -1), verbose=0)[0][0]
            self.board.pop()
            
            if score > best_score:
                best_score = score
                best_move = move
                
        return best_move
    
    def display_board(self):
        """Display the current board state"""
        print("\n  a b c d e f g h")
        print("  ---------------")
        for i in range(8):
            rank = 8 - i
            line = f"{rank}|"
            for j in range(8):
                piece = self.board.piece_at(chess.square(j, 7-i))
                if piece:
                    line += f" {piece.symbol()}"
                else:
                    line += " ."
            line += f" |{rank}"
            print(line)
        print("  ---------------")
        print("  a b c d e f g h\n")

    def is_game_over(self):
        """Check if the game is over"""
        return self.board.is_game_over()

def main():
    game = ChessGame()
    game.initialize_model()
    
    print("Welcome to Chess AI!")
    print("Enter moves in algebraic notation (e.g., 'e2e4')")
    print("Commands: 'quit' to exit, 'board' to show the board")
    
    color = input("Choose your color (white/black): ").lower()
    game.display_board()
    
    if color == 'black':
        ai_move = game.get_ai_move()
        if ai_move:
            game.make_move(ai_move.uci())
            print(f"AI moves: {ai_move.uci()}")
            game.display_board()
    
    while not game.is_game_over():
        move = input("Your move: ")
        
        if move.lower() == 'quit':
            break
        elif move.lower() == 'board':
            game.display_board()
            continue
            
        if game.make_move(move):
            game.display_board()
            
            if not game.is_game_over():
                ai_move = game.get_ai_move()
                if ai_move:
                    game.make_move(ai_move.uci())
                    print(f"AI moves: {ai_move.uci()}")
                    game.display_board()
        else:
            print("Invalid move! Try again.")
    
    if game.is_game_over():
        print("Game Over!")
        result = game.board.outcome()
        if result:
            print(f"Result: {result.result()}")

if __name__ == "__main__":
    main()