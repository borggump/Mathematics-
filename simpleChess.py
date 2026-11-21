class Piece:
    def __init__(self, color, symbol):
        self.color = color  # 'white' or 'black'
        self.symbol = symbol
        self.has_moved = False

class Pawn(Piece):
    def __init__(self, color):
        super().__init__(color, 'P')
        
    def valid_moves(self, board, start_pos):
        x, y = start_pos
        moves = []
        direction = -1 if self.color == 'white' else 1
        
        # Forward move
        if 0 <= x + direction <= 7 and board[x + direction][y] is None:
            moves.append((x + direction, y))
            # Initial two-square move
            if not self.has_moved and board[x + 2*direction][y] is None:
                moves.append((x + 2*direction, y))
        
        # Captures
        for dy in [-1, 1]:
            new_y = y + dy
            if 0 <= new_y <= 7 and 0 <= x + direction <= 7:
                target = board[x + direction][new_y]
                if target and target.color != self.color:
                    moves.append((x + direction, new_y))
                    
        return moves

class Rook(Piece):
    def __init__(self, color):
        super().__init__(color, 'R')
        
    def valid_moves(self, board, start_pos):
        moves = []
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        
        for dx, dy in directions:
            x, y = start_pos
            while True:
                x, y = x + dx, y + dy
                if not (0 <= x <= 7 and 0 <= y <= 7):
                    break
                if board[x][y] is None:
                    moves.append((x, y))
                    continue
                if board[x][y].color != self.color:
                    moves.append((x, y))
                break
        return moves

class Knight(Piece):
    def __init__(self, color):
        super().__init__(color, 'N')
        
    def valid_moves(self, board, start_pos):
        moves = []
        x, y = start_pos
        possible_moves = [
            (x+2, y+1), (x+2, y-1), (x-2, y+1), (x-2, y-1),
            (x+1, y+2), (x+1, y-2), (x-1, y+2), (x-1, y-2)
        ]
        
        for move in possible_moves:
            if 0 <= move[0] <= 7 and 0 <= move[1] <= 7:
                if board[move[0]][move[1]] is None or board[move[0]][move[1]].color != self.color:
                    moves.append(move)
        return moves

class Bishop(Piece):
    def __init__(self, color):
        super().__init__(color, 'B')
        
    def valid_moves(self, board, start_pos):
        moves = []
        directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
        
        for dx, dy in directions:
            x, y = start_pos
            while True:
                x, y = x + dx, y + dy
                if not (0 <= x <= 7 and 0 <= y <= 7):
                    break
                if board[x][y] is None:
                    moves.append((x, y))
                    continue
                if board[x][y].color != self.color:
                    moves.append((x, y))
                break
        return moves

class Queen(Piece):
    def __init__(self, color):
        super().__init__(color, 'Q')
        
    def valid_moves(self, board, start_pos):
        moves = []
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0),
                     (1, 1), (1, -1), (-1, 1), (-1, -1)]
        
        for dx, dy in directions:
            x, y = start_pos
            while True:
                x, y = x + dx, y + dy
                if not (0 <= x <= 7 and 0 <= y <= 7):
                    break
                if board[x][y] is None:
                    moves.append((x, y))
                    continue
                if board[x][y].color != self.color:
                    moves.append((x, y))
                break
        return moves

class King(Piece):
    def __init__(self, color):
        super().__init__(color, 'K')
        
    def valid_moves(self, board, start_pos):
        moves = []
        x, y = start_pos
        possible_moves = [
            (x+1, y), (x-1, y), (x, y+1), (x, y-1),
            (x+1, y+1), (x+1, y-1), (x-1, y+1), (x-1, y-1)
        ]
        
        for move in possible_moves:
            if 0 <= move[0] <= 7 and 0 <= move[1] <= 7:
                if board[move[0]][move[1]] is None or board[move[0]][move[1]].color != self.color:
                    moves.append(move)
        return moves

class ChessGame:
    def __init__(self):
        self.board = [[None for _ in range(8)] for _ in range(8)]
        self.current_turn = 'white'
        self.initialize_board()
        
    def initialize_board(self):
        # Set up pawns
        for y in range(8):
            self.board[1][y] = Pawn('black')
            self.board[6][y] = Pawn('white')
        
        # Set up other pieces
        piece_order = [Rook, Knight, Bishop, Queen, King, Bishop, Knight, Rook]
        for y in range(8):
            self.board[0][y] = piece_order[y]('black')
            self.board[7][y] = piece_order[y]('white')
    
    def display_board(self):
        piece_symbols = {
            'white': {'P': '♙', 'R': '♖', 'N': '♘', 'B': '♗', 'Q': '♕', 'K': '♔'},
            'black': {'P': '♟', 'R': '♜', 'N': '♞', 'B': '♝', 'Q': '♛', 'K': '♚'}
        }
        
        print('   a  b  c  d  e  f  g  h')
        print('  ------------------------')
        for i in range(8):
            print(f'{8-i}|', end=' ')
            for j in range(8):
                piece = self.board[i][j]
                if piece is None:
                    print('.', end=' ')
                else:
                    symbol = piece_symbols[piece.color][piece.symbol]
                    print(symbol, end=' ')
            print(f'|{8-i}')
        print('  ------------------------')
        print('   a  b  c  d  e  f  g  h')
    
    def make_move(self, start_pos, end_pos):
        start_x, start_y = start_pos
        end_x, end_y = end_pos
        
        piece = self.board[start_x][start_y]
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

def parse_position(pos_str):
    """Convert chess notation (e.g., 'e2') to board coordinates"""
    if len(pos_str) != 2:
        return None
    col = ord(pos_str[0].lower()) - ord('a')
    row = 8 - int(pos_str[1])
    if 0 <= row <= 7 and 0 <= col <= 7:
        return (row, col)
    return None

def main():
    game = ChessGame()
    while True:
        game.display_board()
        print(f"\n{game.current_turn.capitalize()}'s turn")
        
        # Get move input
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

if __name__ == "__main__":
    main()