import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np
import re

print("Starting Enhanced Pattern-Based Code Generator...")

class FunctionPattern:
    """Define patterns for function generation with documentation"""
    
    def __init__(self, name, params, body, docstring=""):
        self.name = name
        self.params = params
        self.body = body
        self.docstring = docstring
    
    def generate(self, with_docstring=True):
        params_str = ", ".join(self.params)
        if with_docstring and self.docstring:
            return f'def {self.name}({params_str}):\n    """{self.docstring}"""\n    return {self.body}'
        return f"def {self.name}({params_str}): return {self.body}"
    
    @classmethod
    def get_patterns(cls):
        return {
            "add": cls(
                "add_numbers", 
                ["a", "b"], 
                "a + b",
                "Add two numbers and return their sum."
            ),
            "multiply": cls(
                "multiply", 
                ["a", "b"], 
                "a * b",
                "Multiply two numbers and return their product."
            ),
            "positive": cls(
                "is_positive", 
                ["num"], 
                "num > 0",
                "Check if a number is positive."
            ),
            "even": cls(
                "is_even", 
                ["num"], 
                "num % 2 == 0",
                "Check if a number is even."
            ),
            "max": cls(
                "find_max", 
                ["a", "b"], 
                "a if a > b else b",
                "Find the maximum of two numbers."
            ),
            "square": cls(
                "square", 
                ["x"], 
                "x * x",
                "Calculate the square of a number."
            ),
            "absolute": cls(
                "absolute", 
                ["x"], 
                "x if x >= 0 else -x",
                "Calculate the absolute value of a number."
            ),
            "concat": cls(
                "concat_strings", 
                ["str1", "str2"], 
                "str1 + str2",
                "Concatenate two strings."
            ),
            "length": cls(
                "get_length", 
                ["sequence"], 
                "len(sequence)",
                "Get the length of a sequence."
            ),
            "is_zero": cls(
                "is_zero", 
                ["num"], 
                "num == 0",
                "Check if a number is zero."
            )
        }

def test_functions():
    """Test the generated functions"""
    test_cases = [
        ("add_numbers(3, 4)", 7),
        ("multiply(3, 4)", 12),
        ("is_positive(5)", True),
        ("is_positive(-5)", False),
        ("is_even(4)", True),
        ("is_even(5)", False),
        ("find_max(3, 7)", 7),
        ("square(4)", 16),
        ("absolute(-5)", 5),
        ("concat_strings('hello', 'world')", "helloworld"),
        ("get_length([1,2,3])", 3),
        ("is_zero(0)", True),
        ("is_zero(1)", False)
    ]
    
    patterns = FunctionPattern.get_patterns()
    globals_dict = {}
    
    # First, generate and execute all functions
    for pattern in patterns.values():
        exec(pattern.generate(), globals_dict)
    
    # Then test each function
    results = []
    for test_case, expected in test_cases:
        try:
            result = eval(test_case, globals_dict)
            passed = result == expected
            results.append((test_case, passed, result, expected))
        except Exception as e:
            results.append((test_case, False, str(e), expected))
    
    return results

def main():
    try:
        patterns = FunctionPattern.get_patterns()
        print("\nAvailable function patterns:")
        for name, pattern in patterns.items():
            print(f"\n{pattern.generate(True)}")
        
        print("\nTesting functions:")
        test_results = test_functions()
        
        passed = 0
        total = len(test_results)
        
        print("\nTest Results:")
        print("-" * 50)
        for test_case, passed_test, result, expected in test_results:
            status = "PASSED" if passed_test else "FAILED"
            if passed_test:
                passed += 1
            print(f"{test_case}: {status}")
            if not passed_test:
                print(f"Expected: {expected}")
                print(f"Got: {result}")
            print("-" * 50)
        
        print(f"\nPassed {passed}/{total} tests ({(passed/total)*100:.2f}%)")
        
        # Example of generating new functions
        print("\nGenerating some example functions:")
        test_descriptions = [
            "Write a function to add two numbers",
            "Create a function to check if a number is positive",
            "Write a function to multiply two numbers",
            "Create a function to check if a number is even",
            "Write a function to find the maximum of two numbers",
            "Create a function to get the absolute value"
        ]
        
        print("\nGenerated Functions:")
        for desc in test_descriptions:
            print("\nDescription:", desc)
            
            # Pattern matching
            desc_lower = desc.lower()
            generated_code = None
            
            if "add" in desc_lower:
                generated_code = patterns["add"].generate(True)
            elif "positive" in desc_lower:
                generated_code = patterns["positive"].generate(True)
            elif "multiply" in desc_lower:
                generated_code = patterns["multiply"].generate(True)
            elif "even" in desc_lower:
                generated_code = patterns["even"].generate(True)
            elif "max" in desc_lower:
                generated_code = patterns["max"].generate(True)
            elif "absolute" in desc_lower:
                generated_code = patterns["absolute"].generate(True)
            
            if generated_code:
                print("Generated code:")
                print(generated_code)
                print("-" * 50)
            else:
                print("No matching pattern found")
                print("-" * 50)
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
    