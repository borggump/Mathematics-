import re

class EnhancedPythonGenerator:
    def __init__(self):
        # Complete function implementations
        self.function_implementations = {
            "calculate_sum": """def calculate_sum(a, b):
    \"\"\"Calculate the sum of two numbers.\"\"\"
    return a + b""",
            
            "multiply_numbers": """def multiply_numbers(a, b):
    \"\"\"Multiply two numbers together.\"\"\"
    return a * b""",
            
            "find_average": """def find_average(numbers):
    \"\"\"Calculate the average of a list of numbers.\"\"\"
    if not numbers:
        return 0
    return sum(numbers) / len(numbers)""",
            
            "find_maximum": """def find_maximum(numbers):
    \"\"\"Find the maximum value in a list.\"\"\"
    if not numbers:
        return None
    return max(numbers)"""
        }

        # Pattern matching with complete implementations
        self.patterns = {
            # List operations
            r'create (?:a |an )?list(?: called (\w+))? with (.+)': 
                lambda m: f"{m.group(1) if m.group(1) else 'my_list'} = [{m.group(2)}]",
            
            r'create empty list(?: called (\w+))?':
                lambda m: f"{m.group(1) if m.group(1) else 'my_list'} = []",
            
            r'add (.+) to (\w+)':
                lambda m: f"{m.group(2)}.append({m.group(1)})",
            
            # Loop operations
            r'for each (\w+) in (\w+)':
                lambda m: f"""for {m.group(1)} in {m.group(2)}:
    # Process each {m.group(1)}
    pass""",
            
            r'while (.+)':
                lambda m: f"""while {self._parse_condition(m.group(1))}:
    # While loop body
    pass""",
            
            # File operations
            r'read (?:the )?file ["\']?([^"\']+)["\']?':
                lambda m: f"""with open("{m.group(1)}", "r") as file:
    content = file.read()""",
            
            r'write (.+) to file ["\']?([^"\']+)["\']?':
                lambda m: f"""with open("{m.group(2)}", "w") as file:
    file.write(str({m.group(1)}))""",
            
            # Function creation
            r'create function (\w+)(?: that)? takes (.+)':
                lambda m: self._create_function(m.group(1), m.group(2)),
            
            # Conditional statements
            r'if (.+)':
                lambda m: f"""if {self._parse_condition(m.group(1))}:
    # Conditional body
    pass"""
        }

    def _parse_condition(self, condition):
        """Convert natural language conditions to Python syntax"""
        replacements = {
            " equals ": " == ",
            " is equal to ": " == ",
            " greater than ": " > ",
            " less than ": " < ",
            " not equal to ": " != ",
        }
        for text, operator in replacements.items():
            condition = condition.replace(text, operator)
        return condition

    def _create_function(self, name, params):
        """Create a complete function implementation"""
        # Check if we have a predefined implementation
        if name in self.function_implementations:
            return self.function_implementations[name]
        
        # Create a new function template
        params = params.replace(' and ', ', ')
        return f"""def {name}({params}):
    \"\"\"
    Function description here.
    
    Args:
        {params.replace(', ', '\n        ')}: parameter description
    
    Returns:
        return value description
    \"\"\"
    # Function implementation
    pass"""

    def generate_code(self, description):
        """Generate Python code from natural language description"""
        # Handle exit commands
        if description.lower() in ['exit', 'quit']:
            return "exit"

        # Handle empty input
        if not description or description.isspace():
            return "# Please provide a description"

        # Clean the description
        description = description.strip()
        
        # Try to match patterns
        for pattern, generator in self.patterns.items():
            match = re.match(pattern, description, re.IGNORECASE)
            if match:
                try:
                    return generator(match)
                except Exception as e:
                    return f"# Error generating code: {str(e)}"

        return "# Could not generate code for: " + description

def main():
    generator = EnhancedPythonGenerator()
    
    print("Enhanced Python Code Generator")
    print("Enter 'quit' or 'exit' to end the program")
    print("\nExample commands:")
    print("1. create list with 1, 2, 3")
    print("2. create function calculate_sum that takes a, b")
    print("3. read file 'data.txt'")
    print("4. for each item in numbers")
    print("5. if x greater than 10")
    print("6. write 'Hello' to file 'output.txt'")
    
    while True:
        try:
            print("\nEnter your description:")
            description = input("> ").strip()
            
            if not description:
                continue
            
            # Generate code
            code = generator.generate_code(description)
            
            # Check for exit command
            if code == "exit":
                print("\nGoodbye!")
                break
            
            # Display generated code
            print("\nGenerated Python code:")
            print(code)
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {str(e)}")

if __name__ == "__main__":
    main()
    