import sys
import os

def check_dependencies():
    required_packages = {
        'numpy': 'numpy',
        'tensorflow': 'tensorflow',
        'python-chess': 'chess'
    }
    
    missing_packages = []
    
    for package, import_name in required_packages.items():
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("Missing required packages. Please install them using pip:")
        print("\npip install " + " ".join(missing_packages))
        print("\nOr if you're using Pydroid 3, go to Pip and install these packages:")
        for package in missing_packages:
            print(f"- {package}")
        sys.exit(1)

# Check dependencies before importing
check_dependencies()

# Now import the required packages
import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Flatten, Conv2D
from tensorflow.keras.optimizers import Adam
import chess
import chess.pgn
import io

# Rest of your ChessML class implementation remains the same
# [Previous code goes here]

def main():
    print("Checking dependencies...")
    
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
        print("\nTroubleshooting steps:")
        print("1. Make sure you have installed all required packages:")
        print("   pip install python-chess tensorflow numpy")
        print("2. If using Pydroid 3:")
        print("   - Open the Pip menu")
        print("   - Install 'python-chess', 'tensorflow', and 'numpy'")
        print("3. If the error persists, try restarting your Python environment")

if __name__ == "__main__":
    main()