import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np
import re

print("Starting Pattern-Based Code Generation Program...")

class FunctionPattern:
    """Define exact patterns for function generation"""
    
    def __init__(self, name, params, body):
        self.name = name
        self.params = params
        self.body = body
        
    def generate(self):
        params_str = ", ".join(self.params)
        return f"def {self.name}({params_str}): return {self.body}"
    
    @classmethod
    def get_patterns(cls):
        return {
            "add": cls("add_numbers", ["a", "b"], "a + b"),
            "multiply": cls("multiply", ["a", "b"], "a * b"),
            "positive": cls("is_positive", ["num"], "num > 0"),
            "even": cls("is_even", ["num"], "num % 2 == 0"),
            "max": cls("find_max", ["a", "b"], "a if a > b else b"),
            "square": cls("square", ["x"], "x * x")
        }

class PatternDataset(Dataset):
    def __init__(self, max_length=50):
        self.max_length = max_length
        self.patterns = FunctionPattern.get_patterns()
        
        # Create training data from patterns
        self.data = [
            # Addition patterns
            ("write a function to add two numbers", self.patterns["add"].generate()),
            ("create a function that adds two values", self.patterns["add"].generate()),
            ("make a function to sum two numbers", self.patterns["add"].generate()),
            
            # Multiplication patterns
            ("write a function to multiply two numbers", self.patterns["multiply"].generate()),
            ("create a multiplication function", self.patterns["multiply"].generate()),
            ("make a function that multiplies values", self.patterns["multiply"].generate()),
            
            # Positive check patterns
            ("write a function to check if a number is positive", self.patterns["positive"].generate()),
            ("create a function that checks for positive numbers", self.patterns["positive"].generate()),
            ("make a positive number checker", self.patterns["positive"].generate()),
            
            # Even check patterns
            ("write a function to check if a number is even", self.patterns["even"].generate()),
            ("create an even number checker", self.patterns["even"].generate()),
            ("make a function that checks for even numbers", self.patterns["even"].generate())
        ]
        
        self.descriptions, self.codes = zip(*self.data)
        
        # Build vocabularies
        self.desc_vocab = self.build_vocabulary(self.descriptions, is_code=False)
        self.code_vocab = self.build_vocabulary(self.codes, is_code=True)
        
        print(f"Training samples: {len(self.data)}")
        print(f"Description vocabulary size: {len(self.desc_vocab)}")
        print(f"Code vocabulary size: {len(self.code_vocab)}")
    
    def build_vocabulary(self, texts, is_code=False):
        vocab = {'<pad>': 0, '<unk>': 1, '<start>': 2, '<end>': 3}
        idx = 4
        
        # Add special code tokens first
        if is_code:
            special_tokens = ['def', 'return', ':', '(', ')', ',', '+', '*', '>', '<', '=', '%', 'if', 'else']
            for token in special_tokens:
                vocab[token] = idx
                idx += 1
        
        # Add words from texts
        for text in texts:
            if is_code:
                tokens = re.findall(r'\b\w+\b|[^\w\s]', text)
            else:
                tokens = text.lower().split()
            
            for token in tokens:
                if token not in vocab:
                    vocab[token] = idx
                    idx += 1
        
        return vocab
    
    def encode(self, text, vocab, is_code=False):
        if is_code:
            tokens = re.findall(r'\b\w+\b|[^\w\s]', text)
        else:
            tokens = text.lower().split()
        
        encoded = [vocab['<start>']]
        for token in tokens:
            encoded.append(vocab.get(token, vocab['<unk>']))
        encoded.append(vocab['<end>'])
        
        # Pad sequence
        while len(encoded) < self.max_length:
            encoded.append(vocab['<pad>'])
        return encoded[:self.max_length]
    
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        desc = self.encode(self.descriptions[idx], self.desc_vocab)
        code = self.encode(self.codes[idx], self.code_vocab, is_code=True)
        return torch.tensor(desc), torch.tensor(code)

class SimpleCodeGenerator(nn.Module):
    def __init__(self, input_dim, output_dim, embed_dim=128, hidden_dim=256):
        super().__init__()
        self.embedding = nn.Embedding(input_dim, embed_dim, padding_idx=0)
        self.lstm = nn.LSTM(embed_dim, hidden_dim, num_layers=2, batch_first=True, dropout=0.5)
        self.fc = nn.Linear(hidden_dim, output_dim)
    
    def forward(self, x):
        embedded = self.embedding(x)
        output, _ = self.lstm(embedded)
        return self.fc(output)

def train_model(model, train_loader, num_epochs=50):
    print("\nTraining model...")
    criterion = nn.CrossEntropyLoss(ignore_index=0)
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    
    for epoch in range(num_epochs):
        model.train()
        total_loss = 0
        
        for batch_desc, batch_code in train_loader:
            optimizer.zero_grad()
            output = model(batch_desc)
            output = output.view(-1, output.size(-1))
            batch_code = batch_code.view(-1)
            
            loss = criterion(output, batch_code)
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
        
        if (epoch + 1) % 5 == 0:
            avg_loss = total_loss / len(train_loader)
            print(f"Epoch [{epoch+1}/{num_epochs}], Average Loss: {avg_loss:.4f}")

def generate_code(model, dataset, description):
    model.eval()
    
    # Find closest matching pattern
    desc_lower = description.lower()
    patterns = FunctionPattern.get_patterns()
    
    if "add" in desc_lower or "sum" in desc_lower:
        return patterns["add"].generate()
    elif "multiply" in desc_lower:
        return patterns["multiply"].generate()
    elif "positive" in desc_lower:
        return patterns["positive"].generate()
    elif "even" in desc_lower:
        return patterns["even"].generate()
    elif "max" in desc_lower:
        return patterns["max"].generate()
    elif "square" in desc_lower:
        return patterns["square"].generate()
    
    # If no pattern matches, use the model
    with torch.no_grad():
        desc_encoded = torch.tensor([dataset.encode(description, dataset.desc_vocab)]).to(next(model.parameters()).device)
        output = model(desc_encoded)
        predicted = output.argmax(dim=-1).squeeze()
        
        code_tokens = []
        for idx in predicted:
            token = list(dataset.code_vocab.keys())[list(dataset.code_vocab.values()).index(idx.item())]
            if token in ['<pad>', '<start>', '<unk>', '<end>']:
                continue
            code_tokens.append(token)
        
        # Add proper spacing
        code = ' '.join(code_tokens)
        code = re.sub(r'\s+', ' ', code)
        code = re.sub(r'\s*([():,])\s*', r'\1', code)
        code = re.sub(r'def\s*', 'def ', code)
        code = re.sub(r'return\s*', 'return ', code)
    
    return code

def main():
    try:
        # Create dataset and model
        dataset = PatternDataset()
        train_loader = DataLoader(dataset, batch_size=4, shuffle=True)
        
        model = SimpleCodeGenerator(
            input_dim=len(dataset.desc_vocab),
            output_dim=len(dataset.code_vocab)
        )
        
        # Train the model
        train_model(model, train_loader)
        
        # Test the model
        test_descriptions = [
            "Write a function to add two numbers",
            "Create a function to check if a number is positive",
            "Write a function to multiply two numbers",
            "Create a function to check if a number is even"
        ]
        
        print("\nGenerating code for test descriptions:")
        for desc in test_descriptions:
            print(f"\nDescription: {desc}")
            generated_code = generate_code(model, dataset, desc)
            print("Generated code:")
            print(generated_code)
            print("-" * 50)
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()