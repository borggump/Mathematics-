import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np
import re

print("Starting Fixed Code Generation Program...")

class CodeGenerationDataset(Dataset):
    def __init__(self, descriptions, code_snippets, max_length=50):
        self.descriptions = descriptions
        self.code_snippets = code_snippets
        self.max_length = max_length
        
        self.desc_vocab = self.build_vocabulary(descriptions)
        self.code_vocab = self.build_vocabulary(code_snippets, is_code=True)
        print(f"Description vocabulary size: {len(self.desc_vocab)}")
        print(f"Code vocabulary size: {len(self.code_vocab)}")
        
    def build_vocabulary(self, texts, is_code=False):
        vocab = {'<pad>': 0, '<unk>': 1, '<start>': 2, '<end>': 3}
        idx = 4
        
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

class SimplifiedCodeGenerator(nn.Module):
    def __init__(self, input_dim, output_dim, embedding_dim=128, hidden_dim=256):
        super().__init__()
        self.embedding = nn.Embedding(input_dim, embedding_dim, padding_idx=0)
        self.encoder = nn.LSTM(embedding_dim, hidden_dim, batch_first=True)
        self.decoder = nn.LSTM(hidden_dim, hidden_dim, batch_first=True)
        self.fc = nn.Linear(hidden_dim, output_dim)
        self.dropout = nn.Dropout(0.3)
    
    def forward(self, x):
        # Embedding
        embedded = self.dropout(self.embedding(x))
        
        # Encoding
        encoder_output, (hidden, cell) = self.encoder(embedded)
        
        # Decoding
        decoder_output, _ = self.decoder(encoder_output, (hidden, cell))
        
        # Prediction
        output = self.fc(decoder_output)
        return output

def train_model():
    print("\nPreparing training data...")
    
    training_data = [
        ("Create a function to add two numbers", 
         "def add_numbers(a, b):\n    return a + b"),
        
        ("Write a function to check if a number is positive", 
         "def is_positive(num):\n    return num > 0"),
        
        ("Create a function to calculate the square of a number", 
         "def square_number(x):\n    return x * x"),
        
        ("Write a function to check if a number is even", 
         "def is_even(num):\n    return num % 2 == 0"),
        
        ("Create a function to find the maximum of two numbers",
         "def find_max(a, b):\n    return a if a > b else b")
    ]
    
    descriptions, code_snippets = zip(*training_data)
    print(f"Number of training examples: {len(training_data)}")
    
    try:
        # Create dataset and dataloader
        dataset = CodeGenerationDataset(descriptions, code_snippets)
        train_loader = DataLoader(dataset, batch_size=2, shuffle=True)
        
        # Create model
        print("\nInitializing model...")
        model = SimplifiedCodeGenerator(
            input_dim=len(dataset.desc_vocab),
            output_dim=len(dataset.code_vocab)
        )
        
        criterion = nn.CrossEntropyLoss(ignore_index=0)  # ignore padding index
        optimizer = optim.Adam(model.parameters(), lr=0.001)
        
        print("\nStarting training...")
        num_epochs = 50
        
        for epoch in range(num_epochs):
            model.train()
            total_loss = 0
            
            for batch_desc, batch_code in train_loader:
                optimizer.zero_grad()
                
                # Forward pass
                outputs = model(batch_desc)
                
                # Reshape outputs and targets for loss calculation
                outputs = outputs.view(-1, outputs.size(-1))
                batch_code = batch_code.view(-1)
                
                # Calculate loss
                loss = criterion(outputs, batch_code)
                
                # Backward pass
                loss.backward()
                optimizer.step()
                
                total_loss += loss.item()
            
            if (epoch + 1) % 5 == 0:
                avg_loss = total_loss / len(train_loader)
                print(f"Epoch [{epoch+1}/{num_epochs}], Average Loss: {avg_loss:.4f}")
        
        print("\nTraining completed!")
        return model, dataset
        
    except Exception as e:
        print(f"Error during training: {str(e)}")
        raise e

def generate_code(model, dataset, description):
    try:
        model.eval()
        
        # Encode description
        desc_encoded = dataset.encode_text(description, dataset.desc_vocab)
        desc_tensor = torch.tensor(desc_encoded).unsqueeze(0)
        
        with torch.no_grad():
            # Generate output
            outputs = model(desc_tensor)
            predicted_indices = outputs.argmax(dim=-1).squeeze()
            
            # Convert indices to code
            code_tokens = []
            seen_start = False
            
            for idx in predicted_indices:
                idx_item = idx.item()
                if idx_item >= len(dataset.code_vocab):
                    continue
                    
                token = list(dataset.code_vocab.keys())[list(dataset.code_vocab.values()).index(idx_item)]
                
                if token == '<start>':
                    seen_start = True
                    continue
                elif token == '<end>' or token == '<pad>':
                    break
                elif seen_start and token not in ['<unk>']:
                    if token == ':':
                        code_tokens.extend([token, '\n    '])
                    else:
                        code_tokens.append(token)
        
        return ' '.join(code_tokens)
        
    except Exception as e:
        print(f"Error during code generation: {str(e)}")
        return "Error generating code"

def main():
    try:
        # Train the model
        model, dataset = train_model()
        
        # Test descriptions
        test_descriptions = [
            "Write a function to add two numbers",
            "Create a function to check if a number is positive"
        ]
        
        print("\nTesting with new descriptions:")
        for desc in test_descriptions:
            print(f"\nDescription: {desc}")
            generated_code = generate_code(model, dataset, desc)
            print("Generated code:")
            print(generated_code)
            print("-" * 50)
            
    except Exception as e:
        print(f"An error occurred in main: {str(e)}")

if __name__ == "__main__":
    main()