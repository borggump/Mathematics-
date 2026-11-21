import re

class PracticalCodeGenerator:
    def __init__(self):
        # Common programming patterns
        self.patterns = {
            # Data structure patterns
            "empty_dict": "my_dict = {}",
            "empty_set": "my_set = set()",
            
            # File handling patterns
            "read_lines": "with open('filename.txt', 'r') as file:\n    lines = file.readlines()",
            "write_lines": "with open('filename.txt', 'w') as file:\n    file.writelines(lines)",
            
            # List comprehension patterns
            "square_numbers": "squares = [x*x for x in numbers]",
            "filter_positive": "positives = [x for x in numbers if x > 0]"
        }
        
        # Function templates with implementations
        self.functions = {
            "calculate_sum": (
                "a, b",
                "def calculate_sum(a, b):\n    return a + b"
            ),
            "find_average": (
                "numbers",
                "def find_average(numbers):\n    return sum(numbers) / len(numbers)"
            ),
            "find_maximum": (
                "numbers",
                "def find_maximum(numbers):\n    return max(numbers)"
            ),
            "count_words": (
                "text",
                "def count_words(text):\n    return len(text.split())"
            ),
            "is_palindrome": (
                "text",
                "def is_palindrome(text):\n    text = text.lower()\n    return text == text[::-1]"
            )
        }
    
    def generate_code(self, command):
        if not command or command.isspace():
            return "# Please enter a command"
            
        command = command.strip()
        cmd_lower = command.lower()
        
        # Exit commands
        if cmd_lower in ['exit', 'quit']:
            return "exit"
            
        try:
            # List creation
            if cmd_lower.startswith('create list with'):
                items = command.split('with', 1)[1].strip()
                return f"my_list = [{items}]"
                
            # File reading
            if cmd_lower.startswith('read file'):
                filename = command.split('file', 1)[1].strip().strip("'\"")
                return f"with open('{filename}', 'r') as file:\n    content = file.read()"
                
            # File writing
            if cmd_lower.startswith('write'):
                parts = command.split(' to file ')
                if len(parts) == 2:
                    content = parts[0].replace('write', '', 1).strip()
                    filename = parts[1].strip().strip("'\"")
                    return f"with open('{filename}', 'w') as file:\n    file.write({content})"
                    
            # Loop creation
            if cmd_lower.startswith('for each'):
                parts = command.split(' in ')
                if len(parts) == 2:
                    item = parts[0].replace('for each', '').strip()
                    collection = parts[1].strip()
                    return f"for {item} in {collection}:\n    # Process {item}\n    pass"
                    
            # Function creation
            if cmd_lower.startswith('create function'):
                parts = command.split('takes')
                if len(parts) == 2:
                    name = parts[0].replace('create function', '').strip()
                    params = parts[1].strip()
                    
                    # Check for predefined functions
                    if name in self.functions:
                        return self.functions[name][1]
                        
                    # Create custom function
                    return f"def {name}({params}):\n    # TODO: Add implementation\n    pass"
            
            # Dictionary creation
            if cmd_lower.startswith('create dict with'):
                items = command.split('with', 1)[1].strip()
                return f"my_dict = {{{items}}}"
                
            # Set creation
            if cmd_lower.startswith('create set with'):
                items = command.split('with', 1)[1].strip()
                return f"my_set = {{{items}}}"
            
            return "# Could not generate code for: " + command
            
        except Exception as e:
            return f"# Error: {str(e)}"

def main():
    generator = PracticalCodeGenerator()
    
    print("Practical Python Code Generator")
    print("Enter 'quit' to exit\n")
    print("Available commands:")
    print("1. create list with 1, 2, 3")
    print("2. create dict with 'a': 1, 'b': 2")
    print("3. create set with 1, 2, 3")
    print("4. create function calculate_sum takes a, b")
    print("5. read file data.txt")
    print("6. write 'Hello World' to file output.txt")
    print("7. for each item in numbers")
    
    while True:
        print("\nEnter command:")
        command = input("> ")
        
        if not command:
            continue
            
        result = generator.generate_code(command)
        
        if result == "exit":
            print("Goodbye!")
            break
            
        print("\nGenerated code:")
        print(result)

if __name__ == "__main__":
    main()