import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np
import re

print("Starting Structured Code Generation Program...")

def preprocess_code(code):
    """Standardize code format"""
    # Remove extra whitespace
    code = re.sub(r'\s+', ' ', code.strip())
    # Add proper spacing around special characters
    code = re.sub(r'([():,])', r' \1 ', code)
    return code

class StructuredCodeDataset(Dataset):
    def __init__(self, descriptions, code_snippets, max_length=50):
        self.descriptions = descriptions
        self.code_snippets = [preprocess_code(code) for code in code_snippets]
        self.max_length = max_length
        
        self.desc_vocab = self.build_vocabulary([d.lower() for d in descriptions])
        self.code_vocab = self.build_vocabulary(self.code_snippets, is_code=True)
        print(f"Description vocabulary size: {len(self.desc_vocab)}")
        print(f"Code vocabulary size: {len(self.code_vocab)}")
        
    def build_vocabulary(self, texts, is_code=False):
        vocab = {'<pad>': 0, '<unk>': 1, '<start>': 2, '<end>': 3}
        if is_code:
            # Add common code tokens
            special_tokens = ['def', 'return', ':', '(', ')', ',', 'if', 'else']
            for token in special_tokens:
                if token not in vocab:
                    vocab[token] = len(vocab)
        
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
        
        # Pad sequence
        if len(encoded) < self.max_length:
            encoded.extend([vocab['<pad>']] * (self.max_length - len(encoded)))
        return encoded[:self.max_length]
    
    def __len__(self):
        return len(self.descriptions)
    
    def __getitem__(self, idx):
        desc = self.encode_text(self.descriptions[idx], self.desc_vocab)
        code = self.encode_text(self.code_snippets[idx], self.code_vocab, is_code=True)
        return torch.tensor(desc), torch.tensor(code)

class StructuredCodeGenerator(nn.Module):
    def __init__(self, input_dim, output_dim, embedding_dim=128, hidden_dim=256):
        super().__init__()
        self.embedding = nn.Embedding(input_dim, embedding_dim, padding_idx=0)
        self.encoder = nn.LSTM(embedding_dim, hidden_dim, num_layers=2, dropout=0.3, batch_first=True)
        self.decoder = nn.LSTM(hidden_dim, hidden_dim, num_layers=2, dropout=0.3, batch_first=True)
        self.fc = nn.Linear(hidden_dim, output_dim)
        self.dropout = nn.Dropout(0.3)
    
    def forward(self, x):
        embedded = self.dropout(self.embedding(x))
        encoder_output, (hidden, cell) = self.encoder(embedded)
        decoder_output, _ = self.decoder(encoder_output, (hidden, cell))
        output = self.fc(decoder_output)
        return output

def train_model():
    print("\nPreparing training data...")
    
    # Enhanced training data with consistent structure
    training_data = [
        ("Create a function to add two numbers", 
         "def add_numbers ( a , b ) : return a + b"),
        
        ("Write a function to check if a number is positive", 
         "def is_positive ( num ) : return num > 0"),
        
        ("Create a function to calculate the square of a number", 
         "def square_number ( x ) : return x * x"),
        
        ("Write a function to check if a number is even", 
         "def is_even ( num ) : return num % 2 == 0"),
        
        ("Create a function to find the maximum of two numbers",
         "def find_max ( a , b ) : return a if a > b else b"),
         
        ("Write a function to add three numbers",
         "def add_three ( a , b , c ) : return a + b + c"),
         
        ("Create a function to check if a number is zero",
         "def is_zero ( num ) : return num == 0"),
         
        ("Write a function to multiply two numbers",
         "def multiply ( a , b ) : return a * b")
    ]
    
    descriptions, code_snippets = zip(*training_data)
    print(f"Number of training examples: {len(training_data)}")
    
    # Create dataset and dataloader
    dataset = StructuredCodeDataset(descriptions, code_snippets)
    train_loader = DataLoader(dataset, batch_size=2, shuffle=True)
    
    # Create model
    print("\nInitializing structured model...")
    model = StructuredCodeGenerator(
        input_dim=len(dataset.desc_vocab),
        output_dim=len(dataset.code_vocab)
    )
    
    criterion = nn.CrossEntropyLoss(ignore_index=0)
    optimizer = optim.AdamW(model.parameters(), lr=0.001, weight_decay=0.01)
    
    print("\nStarting training...")
    num_epochs = 100
    best_loss = float('inf')
    patience = 5
    patience_counter = 0
    
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
        
        if avg_loss < best_loss:
            best_loss = avg_loss
            patience_counter = 0
            torch.save(model.state_dict(), 'best_model.pth')
        else:
            patience_counter += 1
            if patience_counter >= patience:
                print(f"Early stopping at epoch {epoch+1}")
                break
        
        if (epoch + 1) % 10 == 0:
            print(f"Epoch [{epoch+1}/{num_epochs}], Average Loss: {avg_loss:.4f}")
    
    # Load best model
    model.load_state_dict(torch.load('best_model.pth'))
    print("\nTraining completed!")
    return model, dataset

def generate_structured_code(model, dataset, description):
    model.eval()
    desc_encoded = dataset.encode_text(description, dataset.desc_vocab)
    desc_tensor = torch.tensor(desc_encoded).unsqueeze(0)
    
    with torch.no_grad():
        outputs = model(desc_tensor)
        predicted_indices = outputs.argmax(dim=-1).squeeze()
        
        code_tokens = []
        indent_next = False
        
        for idx in predicted_indices:
            idx_item = idx.item()
            if idx_item >= len(dataset.code_vocab):
                continue
            
            token = list(dataset.code_vocab.keys())[list(dataset.code_vocab.values()).index(idx_item)]
            
            if token in ['<pad>', '<start>', '<unk>', '<end>']:
                continue
                
            if token == ':':
                code_tokens.append(token)
                indent_next = True
            else:
                if indent_next:
                    code_tokens.append('\n    ')
                    indent_next = False
                code_tokens.append(token)
    
    code = ' '.join(code_tokens)
    # Clean up spacing
    code = re.sub(r'\s+', ' ', code)
    code = re.sub(r'\( ', '(', code)
    code = re.sub(r' \)', ')', code)
    code = re.sub(r' , ', ', ', code)
    code = re.sub(r' :', ':', code)
    return code

def main():
    try:
        model, dataset = train_model()
        
        test_descriptions = [
            "Write a function to add two numbers",
            "Create a function to check if a number is positive",
            "Write a function to multiply two numbers"
        ]
        
        print("\nTesting with new descriptions:")
        for desc in test_descriptions:
            print(f"\nDescription: {desc}")
            generated_code = generate_structured_code(model, dataset, desc)
            print("Generated code:")
            print(generated_code)
            print("-" * 50)
            
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
    