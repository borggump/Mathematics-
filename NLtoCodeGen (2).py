import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import train_test_split
import numpy as np
import re

print("Starting Code Generation Program...")

class CodeGenerationDataset(Dataset):
    def __init__(self, descriptions, code_snippets, max_length=100):
        self.descriptions = descriptions
        self.code_snippets = code_snippets
        self.max_length = max_length
        
        # Build vocabularies for both description and code
        self.desc_vocab = self.build_vocabulary(descriptions)
        self.code_vocab = self.build_vocabulary(code_snippets, is_code=True)
        
    def build_vocabulary(self, texts, is_code=False):
        vocab = {'<pad>': 0, '<unk>': 1, '<start>': 2, '<end>': 3}
        idx = 4
        
        for text in texts:
            if is_code:
                # For code, split on spaces, newlines, and special characters
                tokens = re.findall(r'\b\w+\b|[^\w\s]', text)
            else:
                # For descriptions, just split on spaces
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
            
        # Add start token
        encoded = [vocab['<start>']]
        # Add text tokens
        encoded.extend([vocab.get(token, vocab['<unk>']) for token in tokens])
        # Add end token
        encoded.append(vocab['<end>'])
        # Pad sequence
        while len(encoded) < self.max_length:
            encoded.append(vocab['<pad>'])
        return encoded[:self.max_length]
    
    def __len__(self):
        return len(self.descriptions)
    
    def __getitem__(self, idx):
        desc = self.encode_text(self.descriptions[idx], self.desc_vocab)
        code = self.encode_text(self.code_snippets[idx], self.code_vocab, is_code=True)
        return torch.tensor(desc), torch.tensor(code)

class CodeGenerator(nn.Module):
    def __init__(self, desc_vocab_size, code_vocab_size, embedding_dim=128, hidden_dim=256):
        super(CodeGenerator, self).__init__()
        
        # Description encoder
        self.desc_embedding = nn.Embedding(desc_vocab_size, embedding_dim)
        self.encoder = nn.LSTM(embedding_dim, hidden_dim, batch_first=True, bidirectional=True)
        
        # Code decoder
        self.code_embedding = nn.Embedding(code_vocab_size, embedding_dim)
        self.decoder = nn.LSTM(embedding_dim, hidden_dim*2, batch_first=True)
        self.fc = nn.Linear(hidden_dim*2, code_vocab_size)
        
        self.dropout = nn.Dropout(0.3)
        
    def forward(self, desc, code=None, teacher_forcing_ratio=0.5):
        # Encode description
        desc_embedded = self.dropout(self.desc_embedding(desc))
        encoder_outputs, (hidden, cell) = self.encoder(desc_embedded)
        
        batch_size = desc.size(0)
        max_length = 100  # Maximum code length to generate
        
        if code is not None:
            max_length = code.size(1)
        
        # Initialize decoder input with start token
        decoder_input = torch.tensor([[self.code_embedding.num_embeddings-2]]*batch_size)  # <start> token
        
        # Initialize outputs tensor
        outputs = torch.zeros(batch_size, max_length, self.fc.out_features)
        
        for t in range(max_length):
            decoder_embedded = self.dropout(self.code_embedding(decoder_input))
            decoder_output, (hidden, cell) = self.decoder(decoder_embedded, (hidden, cell))
            prediction = self.fc(decoder_output)
            outputs[:, t:t+1] = prediction
            
            # Teacher forcing
            teacher_force = torch.rand(1).item() < teacher_forcing_ratio
            if code is not None and teacher_force:
                decoder_input = code[:, t:t+1]
            else:
                decoder_input = prediction.argmax(dim=-1)
        
        return outputs

def train_model():
    # Training data: pairs of (description, code)
    training_data = [
        ("Create a function to calculate the square of a number", 
         "def square_number(x):\n    return x * x"),
        
        ("Write a function to check if a number is even", 
         "def is_even(num):\n    return num % 2 == 0"),
        
        ("Create a function to find the maximum of two numbers",
         "def find_max(a, b):\n    return a if a > b else b"),
        
        ("Write a function to calculate the sum of a list of numbers",
         "def sum_list(numbers):\n    return sum(numbers)"),
        
        ("Create a function to reverse a string",
         "def reverse_string(s):\n    return s[::-1]"),
        
        ("Write a function to count vowels in a string",
         """def count_vowels(string):
    vowels = 'aeiou'
    return sum(1 for char in string.lower() if char in vowels)"""),
         
        ("Create a function to check if a string is a palindrome",
         """def is_palindrome(s):
    s = s.lower()
    return s == s[::-1]"""),
         
        ("Write a function to find the factorial of a number",
         """def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n-1)""")
    ]
    
    descriptions, code_snippets = zip(*training_data)
    
    # Create datasets
    dataset = CodeGenerationDataset(descriptions, code_snippets)
    train_loader = DataLoader(dataset, batch_size=2, shuffle=True)
    
    # Create model
    model = CodeGenerator(
        desc_vocab_size=len(dataset.desc_vocab),
        code_vocab_size=len(dataset.code_vocab),
        embedding_dim=128,
        hidden_dim=256
    )
    
    # Training parameters
    criterion = nn.CrossEntropyLoss(ignore_index=dataset.code_vocab['<pad>'])
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    
    # Training loop
    num_epochs = 100
    print("\nTraining model...")
    
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
        
        if (epoch + 1) % 10 == 0:
            print(f"Epoch [{epoch+1}/{num_epochs}], Loss: {total_loss/len(train_loader):.4f}")
    
    return model, dataset

def generate_code(model, dataset, description):
    model.eval()
    
    # Encode description
    desc_encoded = dataset.encode_text(description, dataset.desc_vocab)
    desc_tensor = torch.tensor(desc_encoded).unsqueeze(0)
    
    # Generate code
    with torch.no_grad():
        output = model(desc_tensor, teacher_forcing_ratio=0)
        predicted_indices = output.argmax(dim=-1).squeeze()
        
    # Decode the predicted indices into code
    code = []
    for idx in predicted_indices:
        token = list(dataset.code_vocab.keys())[list(dataset.code_vocab.values()).index(idx.item())]
        if token == '<end>':
            break
        if token not in ['<pad>', '<start>', '<unk>']:
            code.append(token)
    
    return ' '.join(code)

def main():
    # Train the model
    model, dataset = train_model()
    
    # Test the model with new descriptions
    test_descriptions = [
        "Create a function to calculate the average of three numbers",
        "Write a function to check if a number is positive",
        "Create a function to concatenate two strings"
    ]
    
    print("\nGenerating code for test descriptions:")
    for desc in test_descriptions:
        print("\nDescription:", desc)
        generated_code = generate_code(model, dataset, desc)
        print("Generated code:")
        print(generated_code)
        print("-" * 50)

if __name__ == "__main__":
    main()
    