import re

class EnhancedCodeGenerator:
    def __init__(self):
        # Expanded set of function templates
        self.commands = {
            "calculate_sum": "def calculate_sum(a, b):\n    return a + b",
            "multiply": "def multiply(a, b):\n    return a * b",
            "average": "def average(numbers):\n    return sum(numbers)/len(numbers)",
            "maximum": "def maximum(numbers):\n    return max(numbers)",
            "minimum": "def minimum(numbers):\n    return min(numbers)",
            "is_even": "def is_even(number):\n    return number % 2 == 0",
            "is_positive": "def is_positive(number):\n    return number > 0",
            "reverse_string": "def reverse_string(text):\n    return text[::-1]",
            "count_words": "def count_words(text):\n    return len(text.split())"
        }
        
        # Command help messages
        self.help_messages = {
            "list": "create list with x, y, z",
            "function": "create function name takes param1, param2",
            "file": "read file filename.txt",
            "loop": "for each item in collection",
            "write": "write text to file filename.txt"
        }
    
    def generate_code(self, text):
        if not text or text.isspace():
            return "# Please provide a command"
            
        text = text.strip().lower()
        
        # Handle special commands
        if text == 'quit' or text == 'exit':
            return "exit"
            
        if text == 'help':
            return self.get_help()
        
        # Handle list creation with error correction
        if 'create list' in text:
            try:
                items = text.split('with')[1].strip()
                return "my_list = [" + items + "]"
            except IndexError:
                return "# Error: Please specify items (e.g., create list with 1, 2, 3)"
        
        # Handle file operations
        if text.startswith("read file"):
            try:
                filename = text.replace("read file", "").strip().strip("'\"")
                return f"with open('{filename}', 'r') as file:\n    content = file.read()"
            except Exception:
                return "# Error: Invalid file name"
                
        if text.startswith("write"):
            try:
                parts = text.split(" to file ")
                content = parts[0].replace("write", "").strip()
                filename = parts[1].strip().strip("'\"")
                return f"with open('{filename}', 'w') as file:\n    file.write({content})"
            except Exception:
                return "# Error: Invalid write command format"
        
        # Handle loops with better pattern matching
        if text.startswith("for each"):
            try:
                parts = text.split(" in ")
                item = parts[0].replace("for each", "").strip()
                collection = parts[1].strip()
                return f"for {item} in {collection}:\n    pass  # Add your code here"
            except Exception:
                return "# Error: Invalid loop format"
        
        # Handle function creation with error checking
        if text.startswith("create function"):
            try:
                parts = text.split("takes")
                if len(parts) != 2:
                    return "# Error: Function format should be 'create function name takes params'"
                    
                name = parts[0].replace("create function", "").strip()
                params = parts[1].strip()
                
                # Check for predefined functions
                if name in self.commands:
                    return self.commands[name]
                
                # Create custom function
                return f"def {name}({params}):\n    pass  # Add your implementation here"
            except Exception:
                return "# Error: Invalid function definition"
        
        return "# Could not generate code for: " + text
    
    def get_help(self):
        """Generate help message"""
        help_text = "Available commands:\n"
        for command, description in self.help_messages.items():
            help_text += f"- {description}\n"
        return help_text

def main():
    generator = EnhancedCodeGenerator()
    
    print("Enhanced Python Code Generator")
    print("Enter 'help' for available commands")
    print("Enter 'quit' to exit")
    print("\nExample commands:")
    print("1. create list with 1, 2, 3")
    print("2. create function calculate_sum takes a, b")
    print("3. read file data.txt")
    print("4. for each item in numbers")
    print("5. write 'Hello World' to file output.txt")
    
    while True:
        print("\nEnter command:")
        text = input("> ").strip()
        
        if not text:
            continue
        
        result = generator.generate_code(text)
        
        if result == "exit":
            print("Goodbye!")
            break
        
        print("\nGenerated code:")
        print(result)

if __name__ == "__main__":
    main()
    