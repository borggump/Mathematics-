import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np
import re

print("Starting Template-Based Code Generation Program...")

def create_function_template(function_name, params, body):
    """Create a properly formatted function"""
    param_str = ', '.join(params)
    return f"def {function_name}({param_str}): return {body}"

class TemplateMaker:
    """Create consistent code templates"""
    @staticmethod
    def add_numbers():
        return create_function_template("add_numbers", ["a", "b"], "a + b")
    
    @staticmethod
    def check_positive():
        return create_function_template("is_positive", ["num"], "num > 0")
    
    @staticmethod
    def multiply_numbers():
        return create_function_template("multiply", ["a", "b"], "a * b")
    
    @staticmethod
    def square_number():
        return create_function_template("square", ["x"], "x * x")
    
    @staticmethod
    def check_even():
        return create_function_template("is_even", ["num"], "num % 2 == 0")
    
    @staticmethod
    def find_max():
        return create_function_template("find_max", ["a", "b"], "a if a > b else b")

def preprocess_code(code):
    """Standardize code format"""
    code = re.sub(r'\s+', ' ', code.strip())
    code = re.sub(r'([():,])', r' \1 ', code)
    return code

class TemplateCodeDataset(Dataset):
    def __init__(self, descriptions, code_snippets, max_length=50):
        self.descriptions = [d.lower() for d in descriptions]
        self.code_snippets = [preprocess_code(code) for code in code_snippets]
        self.max_length = max_length
        
        # Create template mappings
        self.templates = {
            "add": "def function_name(param1, param2): return param1 + param2",
            "check": "def function_name(param): return param condition",
            "multiply": "def function_name(param1, param2): return param1 * param2"
        }
        
        self.desc_vocab = self.build_vocabulary(self.descriptions)
        self.code_vocab = self.build_vocabulary(self.code_snippets, is_code=True)
        print(f"Description vocabulary size: {len(self.desc_vocab)}")
        print(f"Code vocabulary size: {len(self.code_vocab)}")
    
    def build_vocabulary(self, texts, is_code=False):
        vocab = {'<pad>': 0, '<unk>': 1, '<start>': 2, '<end>': 3}
        # Add special tokens
        special_tokens = ['def', 'return', ':', '(', ')', ','] + list(self.templates.keys())
        for token in special_tokens:
            if token not in vocab:
                vocab[token] = len(vocab)
                
        # Add common code tokens
        common_tokens = ['a', 'b', 'num', 'x', 'if', 'else', '+', '-', '*', '/', '%', '>', '<', '==']
        for token in common_tokens:
            if token not in vocab:
                vocab[token] = len(vocab)
        
        # Add tokens from texts
        for text in texts:
            tokens = text.split() if not is_code else re.findall(r'\b\w+\b|[^\w\s]', text)
            for token in tokens:
                if token not in vocab:
                    vocab[token] = len(vocab)
        return vocab
    
    def encode_text(self, text, vocab, is_code=False):
        if is_code:
            tokens = re.findall(r'\b\w+\b|[^\w\s]', text)
        else:
            tokens = text.lower().split()
        
        encoded = [vocab['<start>']]
        encoded.extend([vocab.get(token, vocab['<unk>']) for token in tokens])
        encoded.append(vocab['<end>'])
        
        while len(encoded) < self.max_length:
            encoded.append(vocab['<pad>'])
        return encoded[:self.max_length]
    
    def __len__(self):
        return len(self.descriptions)
    
    def __getitem__(self, idx):
        desc = self.encode_text(self.descriptions[idx], self.desc_vocab)
        code = self.encode_text(self.code_snippets[idx], self.code_vocab, is_code=True)
        return torch.tensor(desc), torch.tensor(code)

class TemplateCodeGenerator(nn.Module):
    def __init__(self, input_dim, output_dim, embedding_dim=128, hidden_dim=256):
        super().__init__()
        self.embedding = nn.Embedding(input_dim, embedding_dim, padding_idx=0)
        self.encoder = nn.LSTM(embedding_dim, hidden_dim, num_layers=2, dropout=0.5, batch_first=True)
        self.decoder = nn.LSTM(hidden_dim, hidden_dim, num_layers=2, dropout=0.5, batch_first=True)
        self.fc = nn.Linear(hidden_dim, output_dim)
        self.dropout = nn.Dropout(0.5)
    
    def forward(self, x):
        embedded = self.dropout(self.embedding(x))
        encoder_output, (hidden, cell) = self.encoder(embedded)
        decoder_output, _ = self.decoder(encoder_output, (hidden, cell))
        output = self.fc(decoder_output)
        return output

def get_training_data():
    # Create training data with templates
    template_maker = TemplateMaker()
    training_data = [
        ("Write a function to add two numbers", 
         template_maker.add_numbers()),
        
        ("Create a function to check if a number is positive", 
         template_maker.check_positive()),
        
        ("Write a function to multiply two numbers", 
         template_maker.multiply_numbers()),
        
        ("Create a function to square a number", 
         template_maker.square_number()),
        
        ("Write a function to check if a number is even", 
         template_maker.check_even()),
        
        ("Create a function to find the maximum of two numbers", 
         template_maker.find_max()),
        
        # Add variations of similar functions
        ("Create a function that adds two values", 
         template_maker.add_numbers()),
         
        ("Write a function that checks if a number is greater than zero", 
         template_maker.check_positive()),
         
        ("Create a function to perform multiplication of two numbers", 
         template_maker.multiply_numbers()),
         
        ("Write a function that finds the larger of two numbers", 
         template_maker.find_max())
    ]
    return training_data

def train_model(model, train_loader, num_epochs=100):
    criterion = nn.CrossEntropyLoss(ignore_index=0)
    optimizer = optim.AdamW(model.parameters(), lr=0.001, weight_decay=0.01)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', patience=5)
    
    best_loss = float('inf')
    no_improve_count = 0
    
    for epoch in range(num_epochs):
        model.train()
        total_loss = 0
        
        for batch_desc, batch_code in train_loader:
            optimizer.zero_grad()
            outputs = model(batch_desc)
            outputs = outputs.view(-1, outputs.size(-1))
            batch_code = batch_code.view(-1)
            
            loss = criterion(outputs, batch_code)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            
            total_loss += loss.item()
        
        avg_loss = total_loss / len(train_loader)
        scheduler.step(avg_loss)
        
        if avg_loss < best_loss:
            best_loss = avg_loss
            no_improve_count = 0
            torch.save(model.state_dict(), 'best_model.pth')
        else:
            no_improve_count += 1
            if no_improve_count >= 10:
                print(f"Early stopping at epoch {epoch+1}")
                break
        
        if (epoch + 1) % 10 == 0:
            print(f"Epoch [{epoch+1}/{num_epochs}], Average Loss: {avg_loss:.4f}")

def generate_code(model, dataset, description):
    model.eval()
    desc_encoded = dataset.encode_text(description, dataset.desc_vocab)
    desc_tensor = torch.tensor(desc_encoded).unsqueeze(0)
    
    with torch.no_grad():
        outputs = model(desc_tensor)
        predicted_indices = outputs.argmax(dim=-1).squeeze()
        
        # Generate code with proper structure
        function_tokens = []
        current_section = "def"  # Track current section of function
        
        for idx in predicted_indices:
            idx_item = idx.item()
            if idx_item >= len(dataset.code_vocab):
                continue
            
            token = list(dataset.code_vocab.keys())[list(dataset.code_vocab.values()).index(idx_item)]
            
            if token in ['<pad>', '<start>', '<unk>', '<end>']:
                continue
            
            # Handle function structure
            if token == 'def':
                current_section = "def"
                function_tokens.append(token)
            elif token == ':':
                function_tokens.append(token)
                function_tokens.append(" return ")
                current_section = "body"
            elif current_section == "def" and token == '(':
                function_tokens.append(" ")
                function_tokens.append(token)
            elif current_section == "def" and token == ')':
                function_tokens.append(token)
            elif current_section == "body":
                function_tokens.append(token)
            else:
                function_tokens.append(token)
    
    code = ''.join(function_tokens)
    
    # Clean up the code
    code = re.sub(r'\s+', ' ', code)
    code = re.sub(r'\( ', '(', code)
    code = re.sub(r' \)', ')', code)
    code = re.sub(r' ,', ',', code)
    code = re.sub(r' :', ':', code)
    
    return code

def main():
    try:
        # Get training data
        training_data = get_training_data()
        descriptions, code_snippets = zip(*training_data)
        
        # Create dataset
        dataset = TemplateCodeDataset(descriptions, code_snippets)
        train_loader = DataLoader(dataset, batch_size=2, shuffle=True)
        
        # Create and train model
        model = TemplateCodeGenerator(
            input_dim=len(dataset.desc_vocab),
            output_dim=len(dataset.code_vocab)
        )
        
        print("\nTraining model...")
        train_model(model, train_loader)
        
        # Load best model
        model.load_state_dict(torch.load('best_model.pth'))
        
        # Test with new descriptions
        test_descriptions = [
            "Write a function to add two numbers",
            "Create a function to check if a number is positive",
            "Write a function to multiply two numbers"
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
    