import json

try:
    with open('conversations.json', 'r') as json_file:
        data = json.load(json_file)
   
    with open('output.txt', 'w') as text_file:
        text_file.write(json.dumps(data, indent=2))
   
    print("JSON successfully written to text file")
   
except FileNotFoundError:
    print("JSON file not found")
except json.JSONDecodeError:
    print("Invalid JSON format")
except Exception as e:
    print(f"An error occurred: {e}") 
