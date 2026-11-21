class PythonProgramGenerator:
    def __init__(self):
        # Dictionary of common library imports and their purposes
        self.library_templates = {
            'data_science': {
                'libraries': [
                    'import numpy as np',
                    'import pandas as pd',
                    'import matplotlib.pyplot as plt',
                    'import seaborn as sns',
                    'from sklearn import *'
                ],
                'code_patterns': {
                    'data_loading': '''
# Load and prepare data
data = pd.read_{file_type}("{filename}")
''',
                    'visualization': '''
# Create visualization
plt.figure(figsize=(10, 6))
sns.{plot_type}(data=data, x="{x_col}", y="{y_col}")
plt.title("{title}")
plt.show()
'''
                }
            },
            'deep_learning': {
                'libraries': [
                    'import tensorflow as tf',
                    'from tensorflow import keras',
                    'import torch',
                    'import torch.nn as nn'
                ],
                'code_patterns': {
                    'keras_model': '''
# Define Keras model
model = keras.Sequential([
    keras.layers.Dense({units}, activation='{activation}'),
    keras.layers.Dropout({dropout}),
    keras.layers.Dense({output_units}, activation='{output_activation}')
])
''',
                    'pytorch_model': '''
# Define PyTorch model
class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()
        self.fc1 = nn.Linear({input_size}, {hidden_size})
        self.fc2 = nn.Linear({hidden_size}, {output_size})
    
    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = self.fc2(x)
        return x
'''
                }
            },
            'web': {
                'libraries': [
                    'from flask import Flask, request, jsonify',
                    'from fastapi import FastAPI',
                    'import requests',
                    'from bs4 import BeautifulSoup'
                ],
                'code_patterns': {
                    'flask_app': '''
app = Flask(__name__)

@app.route('{route}', methods=['{method}'])
def {function_name}():
    {code}
    return jsonify({response})
''',
                    'fastapi_app': '''
app = FastAPI()

@app.{method}("{route}")
async def {function_name}({parameters}):
    {code}
    return {response}
'''
                }
            },
            'automation': {
                'libraries': [
                    'import pyautogui',
                    'from selenium import webdriver',
                    'import schedule',
                    'import time'
                ],
                'code_patterns': {
                    'scheduler': '''
def {job_name}():
    {code}

schedule.every({interval}).do({job_name})

while True:
    schedule.run_pending()
    time.sleep(1)
''',
                    'selenium': '''
driver = webdriver.Chrome()
driver.get("{url}")
element = driver.find_element_by_{method}("{selector}")
{action}
'''
                }
            }
        }

    def analyze_requirements(self, description):
        """Analyze the natural language description to determine requirements"""
        description = description.lower()
        requirements = {
            'category': None,
            'libraries': set(),
            'patterns': []
        }
        
        # Detect category and required libraries
        categories = {
            'data_science': ['data', 'analysis', 'visualization', 'plot', 'pandas', 'numpy'],
            'deep_learning': ['neural', 'deep learning', 'ai', 'machine learning', 'tensorflow', 'pytorch'],
            'web': ['web', 'api', 'flask', 'fastapi', 'scraping'],
            'automation': ['automation', 'schedule', 'selenium', 'bot']
        }
        
        for category, keywords in categories.items():
            if any(keyword in description for keyword in keywords):
                requirements['category'] = category
                requirements['libraries'].update(self.library_templates[category]['libraries'])
        
        return requirements

    def generate_imports(self, requirements):
        """Generate import statements based on requirements"""
        return '\n'.join(requirements['libraries'])

    def generate_code(self, description):
        """Generate complete Python program based on description"""
        requirements = self.analyze_requirements(description)
        
        # Start with imports
        program = self.generate_imports(requirements)
        program += '\n\n# Main program\n'
        
        # Add code based on category
        category = requirements['category']
        if category in self.library_templates:
            patterns = self.library_templates[category]['code_patterns']
            
            # Add category-specific code
            if category == 'data_science':
                program += patterns['data_loading'].format(
                    file_type='csv',
                    filename='data.csv'
                )
                program += patterns['visualization'].format(
                    plot_type='lineplot',
                    x_col='x',
                    y_col='y',
                    title='Data Visualization'
                )
            
            elif category == 'deep_learning':
                if 'tensorflow' in description.lower():
                    program += patterns['keras_model'].format(
                        units=64,
                        activation='relu',
                        dropout=0.2,
                        output_units=10,
                        output_activation='softmax'
                    )
                else:
                    program += patterns['pytorch_model'].format(
                        input_size=784,
                        hidden_size=128,
                        output_size=10
                    )
            
            elif category == 'web':
                if 'flask' in description.lower():
                    program += patterns['flask_app'].format(
                        route='/',
                        method='GET',
                        function_name='index',
                        code='response = {"message": "Hello, World!"}',
                        response='response'
                    )
                else:
                    program += patterns['fastapi_app'].format(
                        method='get',
                        route='/',
                        function_name='root',
                        parameters='',
                        code='response = {"message": "Hello, World!"}',
                        response='response'
                    )
            
            elif category == 'automation':
                if 'schedule' in description.lower():
                    program += patterns['scheduler'].format(
                        job_name='scheduled_job',
                        code='print("Running scheduled job")',
                        interval='1.minutes'
                    )
                else:
                    program += patterns['selenium'].format(
                        url='https://example.com',
                        method='id',
                        selector='example',
                        action='element.click()'
                    )
        
        # Add main block
        program += '''

if __name__ == "__main__":
    main()
'''
        
        return program

def main():
    print("Welcome to the Universal Python Program Generator!")
    print("This tool can generate Python programs for various purposes.")
    print("\nExample descriptions:")
    print("1. 'Create a data analysis program with pandas and matplotlib'")
    print("2. 'Generate a deep learning program using PyTorch'")
    print("3. 'Make a web scraping program with beautiful soup'")
    print("4. 'Create an automation script using selenium'")
    print("\nType 'quit' to exit.")
    
    generator = PythonProgramGenerator()
    
    while True:
        description = input("\nDescribe the Python program you want to create: ")
        
        if description.lower() == 'quit':
            print("Thank you for using the Universal Python Program Generator. Goodbye!")
            break
        
        print("\nGenerating Python program...")
        try:
            generated_code = generator.generate_code(description)
            
            print("\nGenerated Python Code:")
            print(generated_code)
            
            save = input("\nDo you want to save this code to a file? (yes/no): ")
            if save.lower() == 'yes':
                filename = input("Enter filename (e.g., program.py): ")
                with open(filename, 'w') as file:
                    file.write(generated_code)
                print(f"Program saved to {filename}")
                
                run = input("Do you want to attempt to run this program? (yes/no): ")
                if run.lower() == 'yes':
                    print("\nAttempting to run the generated program:")
                    print("-" * 40)
                    try:
                        exec(generated_code)
                    except ImportError as e:
                        print(f"Error: Required libraries not installed. Please install: {str(e)}")
                    except Exception as e:
                        print(f"Error running program: {str(e)}")
                    print("-" * 40)
        
        except Exception as e:
            print(f"Error generating program: {str(e)}")
            print("Please try again with a different description.")

if __name__ == "__main__":
    main()