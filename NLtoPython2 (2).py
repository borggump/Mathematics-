import re

class PythonCodeGenerator:
    def __init__(self):
        self.patterns = {
            # List operations
            r'create (?:a |an )?empty list': 'my_list = []',
            r'create (?:a |an )?list with (.+)': lambda m: f'my_list = [{m.group(1)}]',
            r'add (.+) to (?:the )?list': lambda m: f'my_list.append({m.group(1)})',
            
            # Variable assignment
            r'set (\w+) to (.+)': lambda m: f'{m.group(1)} = {m.group(2)}',
            r'create (\w+) variable with value (.+)': lambda m: f'{m.group(1)} = {m.group(2)}',
            
            # Print operations
            r'print (.+)': lambda m: f'print({m.group(1)})',
            r'display (.+)': lambda m: f'print({m.group(1)})',
            
            # Math operations
            r'calculate (.+)': lambda m: f'result = {m.group(1)}',
            r'compute (.+)': lambda m: f'result = {m.group(1)}',
            
            # Loops
            r'for each (\w+) in (.+)': lambda m: f'for {m.group(1)} in {m.group(2)}:',
            r'while (.+)': lambda m: f'while {m.group(1)}:',
            
            # Conditionals
            r'if (.+)': lambda m: f'if {m.group(1)}:',
            r'else if (.+)': lambda m: f'elif {m.group(1)}:',
            r'else': 'else:',
            
            # Functions
            r'create function (\w+) that takes (.+)': lambda m: f'def {m.group(1)}({m.group(2)}):',
            r'define function (\w+) with parameters (.+)': lambda m: f'def {m.group(1)}({m.group(2)}):',
            
            # File operations
            r'read file (.+)': lambda m: f'with open({m.group(1)}, "r") as file:\n    content = file.read()',
            r'write (.+) to file (.+)': lambda m: f'with open({m.group(2)}, "w") as file:\n    file.write({m.group(1)})',
            
            # String operations
            r'convert (.+) to uppercase': lambda m: f'{m.group(1)}.upper()',
            r'convert (.+) to lowercase': lambda m: f'{m.group(1)}.lower()',
            r'join (.+) with (.+)': lambda m: f'{m.group(2)}.join({m.group(1)})',
        }
        
        # Common programming task templates
        self.templates = {
            "sum numbers": """
def sum_numbers(numbers):
    return sum(numbers)
""",
            "find maximum": """
def find_maximum(numbers):
    return max(numbers)
""",
            "count words": """
def count_words(text):
    return len(text.split())
""",
            "reverse string": """
def reverse_string(text):
    return text[::-1]
""",
            "check palindrome": """
def is_palindrome(text):
    text = text.lower()
    return text == text[::-1]
"""
        }
    
    def generate_code(self, description):
        """Convert natural language description to Python code"""
        try:
            # Check for template matches first
            for key, template in self.templates.items():
                if key in description.lower():
                    return template.strip()
            
            # Clean the description
            description = description.lower().strip()
            
            # Check patterns
            for pattern, response in self.patterns.items():
                match = re.match(pattern, description)
                if match:
                    if callable(response):
                        return response(match)
                    return response
            
            # Handle complex descriptions
            if "function" in description:
                return self._generate_function(description)
            elif "loop" in description:
                return self._generate_loop(description)
            elif "if" in description:
                return self._generate_conditional(description)
            
            return "# Could not generate code for: " + description
            
        except Exception as e:
            return f"# Error generating code: {str(e)}"
    
    def _generate_function(self, description):
        """Generate function based on description"""
        parts = description.split()
        if "return" in description:
            name = parts[parts.index("function") + 1] if "function" in parts else "my_function"
            return f"def {name}():\n    return"
        return "def my_function():\n    pass"
    
    def _generate_loop(self, description):
        """Generate loop based on description"""
        if "times" in description:
            count = re.search(r'(\d+)', description)
            if count:
                return f"for i in range({count.group(1)}):"
        return "for item in items:"
    
    def _generate_conditional(self, description):
        """Generate conditional based on description"""
        condition = "condition"
        if "equals" in description or "=" in description:
            parts = description.split("equals" if "equals" in description else "=")
            if len(parts) == 2:
                condition = f"{parts[0].strip()} == {parts[1].strip()}"
        return f"if {condition}:"

def main():
    generator = PythonCodeGenerator()
    
    print("Natural Language to Python Code Converter")
    print("Enter 'quit' to exit")
    print("\nExample commands:")
    print("1. create a list with 1, 2, 3")
    print("2. create function calculate_sum that takes a, b")
    print("3. read file 'data.txt'")
    print("4. for each item in numbers")
    
    while True:
        print("\nEnter your description:")
        description = input("> ")
        
        if description.lower() == 'quit':
            break
        
        code = generator.generate_code(description)
        print("\nGenerated Python code:")
        print(code)

if __name__ == "__main__":
    main()
    