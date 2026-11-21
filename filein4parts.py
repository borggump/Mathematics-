import os

def split_text_file(input_file, num_parts=4):
    """
    Split a text file into nearly equal parts.
    
    Args:
        input_file (str): Path to the input file
        num_parts (int): Number of parts to split into (default: 3)
    """
    try:
        # Read the entire file
        with open(input_file, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Calculate the size of each part
        total_chars = len(content)
        chars_per_part = total_chars // num_parts
        remainder = total_chars % num_parts
        
        print(f"Total characters: {total_chars}")
        print(f"Characters per part: {chars_per_part}")
        print(f"Remainder characters: {remainder}")
        
        # Split the content
        parts = []
        start = 0
        
        for i in range(num_parts):
            # Add one extra character to the first 'remainder' parts
            extra_char = 1 if i < remainder else 0
            end = start + chars_per_part + extra_char
            
            # For the last part, take everything remaining
            if i == num_parts - 1:
                end = total_chars
            
            parts.append(content[start:end])
            start = end
        
        # Write each part to a separate file
        base_name = os.path.splitext(input_file)[0]
        extension = os.path.splitext(input_file)[1]
        
        for i, part in enumerate(parts):
            output_filename = f"{base_name}_part{i+1}{extension}"
            
            with open(output_filename, 'w', encoding='utf-8') as output_file:
                output_file.write(part)
            
            print(f"Created: {output_filename} ({len(part)} characters)")
        
        print(f"\nSuccessfully split '{input_file}' into {num_parts} parts!")
        
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found.")
    except Exception as e:
        print(f"Error: {e}")

def split_by_lines(input_file, num_parts=3):
    """
    Alternative method: Split by lines instead of characters for better readability.
    
    Args:
        input_file (str): Path to the input file
        num_parts (int): Number of parts to split into (default: 3)
    """
    try:
        # Read all lines
        with open(input_file, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        
        total_lines = len(lines)
        lines_per_part = total_lines // num_parts
        remainder = total_lines % num_parts
        
        print(f"Total lines: {total_lines}")
        print(f"Lines per part: {lines_per_part}")
        
        # Split the lines
        parts = []
        start = 0
        
        for i in range(num_parts):
            # Add one extra line to the first 'remainder' parts
            extra_line = 1 if i < remainder else 0
            end = start + lines_per_part + extra_line
            
            # For the last part, take everything remaining
            if i == num_parts - 1:
                end = total_lines
            
            parts.append(lines[start:end])
            start = end
        
        # Write each part to a separate file
        base_name = os.path.splitext(input_file)[0]
        extension = os.path.splitext(input_file)[1]
        
        for i, part in enumerate(parts):
            output_filename = f"{base_name}_part{i+1}{extension}"
            
            with open(output_filename, 'w', encoding='utf-8') as output_file:
                output_file.writelines(part)
            
            print(f"Created: {output_filename} ({len(part)} lines)")
        
        print(f"\nSuccessfully split '{input_file}' into {num_parts} parts by lines!")
        
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    input_filename = "output.txt"
    
    print("Choose splitting method:")
    print("1. Split by characters (exact equal sizes)")
    print("2. Split by lines (preserves line breaks)")
    
    choice = input("Enter your choice (1 or 2): ").strip()
    
    if choice == "1":
        split_text_file(input_filename)
    elif choice == "2":
        split_by_lines(input_filename)
    else:
        print("Invalid choice. Using character-based splitting by default.")
        split_text_file(input_filename)