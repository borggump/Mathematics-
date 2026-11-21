import re

class BasicCodeGenerator:
    def __init__(self):
        # Basic commands and their outputs
        self.commands = {
            "calculate_sum": "def calculate_sum(a, b):\n    return a + b",
            "multiply": "def multiply(a, b):\n    return a * b",
            "average": "def average(numbers):\n    return sum(numbers)/len(numbers)"
        }
    
    def generate_code(self, text):
        # Handle exit commands
        if text.lower() in ['exit', 'quit']:
            return "exit"
        
        # Handle empty input
        if not text or text.isspace():
            return "# Please provide a command"
        
        text = text.strip().lower()
        
        # Handle list creation
        if text.startswith("create list with"):
            items = text.replace("create list with", "").strip()
            return "my_list = [" + items + "]"
        
        # Handle file reading
        if text.startswith("read file"):
            filename = text.replace("read file", "").strip()
            filename = filename.strip("'").strip('"')
            return "with open('" + filename + "', 'r') as file:\n    content = file.read()"
        
        # Handle for loops
        if text.startswith("for each"):
            parts = text.split(" in ")
            if len(parts) == 2:
                item = parts[0].replace("for each", "").strip()
                collection = parts[1].strip()
                return "for " + item + " in " + collection + ":\n    pass"
        
        # Handle function creation
        if text.startswith("create function"):
            parts = text.split("takes")
            if len(parts) == 2:
                name = parts[0].replace("create function", "").strip()
                params = parts[1].strip()
                if name in self.commands:
                    return self.commands[name]
                return "def " + name + "(" + params + "):\n    pass"
        
        return "# Could not generate code for: " + text

def main():
    generator = BasicCodeGenerator()
    
    print("Basic Python Code Generator")
    print("Enter 'quit' to exit")
    print("\nAvailable commands:")
    print("1. create list with 1, 2, 3")
    print("2. create function calculate_sum takes a, b")
    print("3. read file data.txt")
    print("4. for each item in numbers")
    
    while True:
        print("\nEnter command:")
        text = input("> ")
        
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