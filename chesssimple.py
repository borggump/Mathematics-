class ChessBoard:
    def __init__(self):
        self.board = self.initial_board()
        self.white_turn = True
        
    def initial_board(self):
        # Initialize empty board
        board = [['.'] * 8 for _ in range(8)]
        
        # Set up pawns
        for col in range(8):
            board[1][col] = 'P'  # white pawns
            board[6][col] = 'p'  # black pawns
            
        # Set up other pieces
        pieces = ['R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R']
        for col in range(8):
            board[0][col] = pieces[col]  # white pieces
            board[7][col] = pieces[col].lower()  # black pieces
            
        return board
    
    def display(self):
        print("\n  a b c d e f g h")
        print("  ---------------")
        for row in range(7, -1, -1):
            print(f"{row+1}|", end=" ")
            for col in range(8):
                print(self.board[row][col], end=" ")
            print(f"|{row+1}")
        print("  ---------------")
        print("  a b c d e f g h\n")
    
    def is_valid_move(self, move):
        if len(move) != 4:
            return False
            
        # Convert algebraic notation to array indices
        from_col = ord(move[0]) - ord('a')
        from_row = int(move[1]) - 1
        to_col = ord(move[2]) - ord('a')
        to_row = int(move[3]) - 1
        
        # Check if positions are within board
        if not (0 <= from_col <= 7 and 0 <= from_row <= 7 and 
                0 <= to_col <= 7 and 0 <= to_row <= 7):
            return False
            
        # Check if there's a piece at the starting position
        piece = self.board[from_row][from_col]
        if piece == '.':
            return False
            
        # Check if it's the correct player's turn
        if self.white_turn and piece.islower():
            return False
        if not self.white_turn and piece.isupper():
            return False
            
        return True
    
    def make_move(self, move):
        if not self.is_valid_move(move):
            return False
            
        from_col = ord(move[0]) - ord('a')
        from_row = int(move[1]) - 1
        to_col = ord(move[2]) - ord('a')
        to_row = int(move[3]) - 1
        
        # Move the piece
        self.board[to_row][to_col] = self.board[from_row][from_col]
        self.board[from_row][from_col] = '.'
        
        # Switch turns
        self.white_turn = not self.white_turn
        return True

def main():
    game = ChessBoard()
    print("Welcome to Simple Chess!")
    print("Enter moves in format 'e2e4'")
    print("Type 'quit' to exit or 'board' to show the board")
    
    while True:
        game.display()
        turn = "White" if game.white_turn else "Black"
        move = input(f"{turn}'s move: ")
        
        if move.lower() == 'quit':
            break
        elif move.lower() == 'board':
            continue
            
        if not game.make_move(move):
            print("Invalid move! Please try again.")

if __name__ == "__main__":
    main()