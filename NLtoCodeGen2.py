import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np
import re

print("Starting Code Generation Program...")

class CodeGenerationDataset(Dataset):
    def __init__(self, descriptions, code_snippets, max_length=100):
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

class SimpleCodeGenerator(nn.Module):
    def __init__(self, desc_vocab_size, code_vocab_size, embedding_dim=128, hidden_dim=256):
        super(SimpleCodeGenerator, self).__init__()
        
        # Embeddings
        self.desc_embedding = nn.Embedding(desc_vocab_size, embedding_dim)
        self.code_embedding = nn.Embedding(code_vocab_size, embedding_dim)
        
        # Single-layer LSTM for both encoding and decoding
        self.lstm = nn.LSTM(
            input_size=embedding_dim,
            hidden_size=hidden_dim,
            num_layers=1,
            batch_first=True
        )
        
        # Output layer
        self.fc = nn.Linear(hidden_dim, code_vocab_size)
        self.dropout = nn.Dropout(0.3)
        
    def forward(self, desc, code=None, teacher_forcing_ratio=0.5):
        batch_size = desc.size(0)
        
        # Embed description
        desc_embedded = self.dropout(self.desc_embedding(desc))
        
        # Process through LSTM
        lstm_out, (hidden, cell) = self.lstm(desc_embedded)
        
        # Determine output length
        max_length = 100 if code is None else code.size(1)
        
        # Initialize output tensor
        outputs = torch.zeros(batch_size, max_length, self.fc.out_features)
        
        # Initialize decoder input
        decoder_input = torch.tensor([[2]]*batch_size)  # <start> token
        
        # Generate sequence
        for t in range(max_length):
            # Embed decoder input
            decoder_embedded = self.code_embedding(decoder_input)
            decoder_embedded = self.dropout(decoder_embedded)
            
            # Get output and hidden state
            lstm_out, (hidden, cell) = self.lstm(decoder_embedded.unsqueeze(1), (hidden, cell))
            output = self.fc(lstm_out.squeeze(1))
            
            # Store output
            outputs[:, t:t+1] = output.unsqueeze(1)
            
            # Teacher forcing
            teacher_force = torch.rand(1).item() < teacher_forcing_ratio
            if code is not None and teacher_force:
                decoder_input = code[:, t]
            else:
                decoder_input = output.argmax(1)
        
        return outputs

def train_model():
    print("\nPreparing training data...")
    
    # Training data
    training_data = [
        ("Create a function to calculate the square of a number", 
         "def square_number(x):\n    return x * x"),
        
        ("Write a function to check if a number is even", 
         "def is_even(num):\n    return num % 2 == 0"),
        
        ("Create a function to find the maximum of two numbers",
         "def find_max(a, b):\n    return a if a > b else b"),
        
        ("Write a function to calculate the sum of a list",
         "def sum_list(numbers):\n    return sum(numbers)"),
        
        ("Create a function to reverse a string",
         "def reverse_string(s):\n    return s[::-1]")
    ]
    
    descriptions, code_snippets = zip(*training_data)
    
    print(f"Number of training examples: {len(training_data)}")
    
    # Create dataset and dataloader
    dataset = CodeGenerationDataset(descriptions, code_snippets)
    train_loader = DataLoader(dataset, batch_size=2, shuffle=True)
    
    # Create model
    print("\nInitializing model...")
    model = SimpleCodeGenerator(
        desc_vocab_size=len(dataset.desc_vocab),
        code_vocab_size=len(dataset.code_vocab)
    )
    
    criterion = nn.CrossEntropyLoss(ignore_index=dataset.code_vocab['<pad>'])
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    
    # Training loop
    print("\nStarting training...")
    num_epochs = 50
    
    for epoch in range(num_epochs):
        model.train()
        total_loss = 0
        
        for batch_desc, batch_code in train_loader:
            optimizer.zero_grad()
            
            output = model(batch_desc, batch_code)
            output = output.view(-1, output.size(-1))
            batch_code = batch_code.view(-1)
            
            loss = criterion(output, batch_code)
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
        
        if (epoch + 1) % 5 == 0:
            avg_loss = total_loss / len(train_loader)
            print(f"Epoch [{epoch+1}/{num_epochs}], Average Loss: {avg_loss:.4f}")
    
    print("\nTraining completed!")
    return model, dataset

def generate_code(model, dataset, description):
    model.eval()
    
    desc_encoded = dataset.encode_text(description, dataset.desc_vocab)
    desc_tensor = torch.tensor(desc_encoded).unsqueeze(0)
    
    with torch.no_grad():
        output = model(desc_tensor, teacher_forcing_ratio=0)
        predicted_indices = output.argmax(dim=-1).squeeze()
    
    code_tokens = []
    for idx in predicted_indices:
        token = list(dataset.code_vocab.keys())[list(dataset.code_vocab.values()).index(idx.item())]
        if token == '<end>':
            break
        if token not in ['<pad>', '<start>', '<unk>']:
            code_tokens.append(token)
    
    return ' '.join(code_tokens)

def main():
    try:
        # Train the model
        model, dataset = train_model()
        
        # Test descriptions
        test_descriptions = [
            "Write a function to add two numbers",
            "Create a function to check if a number is positive",
            "Write a function to join two strings"
        ]
        
        print("\nTesting with new descriptions:")
        for desc in test_descriptions:
            print("\nDescription:", desc)
            try:
                generated_code = generate_code(model, dataset, desc)
                print("Generated code:")
                print(generated_code)
                print("-" * 50)
            except Exception as e:
                print(f"Error generating code: {str(e)}")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()