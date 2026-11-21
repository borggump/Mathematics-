import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np
import re

print("Starting Improved Code Generation Program...")

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
        
        # Split texts into tokens and count frequencies
        token_freq = {}
        for text in texts:
            if is_code:
                tokens = re.findall(r'\b\w+\b|[^\w\s]', text)
            else:
                tokens = text.lower().split()
            for token in tokens:
                token_freq[token] = token_freq.get(token, 0) + 1
        
        # Add tokens that appear more than once
        for token, freq in token_freq.items():
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

class Attention(nn.Module):
    def __init__(self, hidden_dim):
        super().__init__()
        self.attention = nn.Linear(hidden_dim * 2, hidden_dim)
        self.v = nn.Parameter(torch.rand(hidden_dim))
        
    def forward(self, hidden, encoder_outputs):
        batch_size = encoder_outputs.shape[0]
        seq_len = encoder_outputs.shape[1]
        
        hidden = hidden.repeat(seq_len, 1, 1).transpose(0, 1)
        energy = torch.tanh(self.attention(torch.cat((hidden, encoder_outputs), dim=2)))
        attention = energy.matmul(self.v)
        
        return torch.softmax(attention, dim=1)

class ImprovedCodeGenerator(nn.Module):
    def __init__(self, input_dim, output_dim, embedding_dim=128, hidden_dim=256):
        super().__init__()
        
        self.embedding = nn.Embedding(input_dim, embedding_dim)
        self.encoder = nn.LSTM(embedding_dim, hidden_dim, num_layers=2, dropout=0.5, batch_first=True)
        self.attention = Attention(hidden_dim)
        self.decoder = nn.LSTM(hidden_dim + embedding_dim, hidden_dim, num_layers=2, dropout=0.5, batch_first=True)
        self.fc = nn.Linear(hidden_dim, output_dim)
        self.dropout = nn.Dropout(0.3)
        
    def forward(self, src, trg=None, teacher_forcing_ratio=0.5):
        batch_size = src.shape[0]
        max_len = trg.shape[1] if trg is not None else 50
        vocab_size = self.fc.out_features
        
        outputs = torch.zeros(batch_size, max_len, vocab_size)
        
        # Encoder
        embedded = self.dropout(self.embedding(src))
        encoder_outputs, (hidden, cell) = self.encoder(embedded)
        
        # First input to decoder is <start> token
        input = trg[:, 0].unsqueeze(1) if trg is not None else torch.tensor([[2]] * batch_size)
        
        for t in range(1, max_len):
            embedded = self.dropout(self.embedding(input))
            
            # Calculate attention
            attention_weights = self.attention(hidden[-1], encoder_outputs)
            context = torch.bmm(attention_weights.unsqueeze(1), encoder_outputs)
            
            # Combine embedded input and context vector
            rnn_input = torch.cat((embedded, context), dim=2)
            
            # Decoder
            output, (hidden, cell) = self.decoder(rnn_input, (hidden, cell))
            prediction = self.fc(output.squeeze(1))
            outputs[:, t] = prediction
            
            # Teacher forcing
            teacher_force = torch.rand(1).item() < teacher_forcing_ratio
            top1 = prediction.argmax(1)
            input = trg[:, t].unsqueeze(1) if trg is not None and teacher_force else top1.unsqueeze(1)
        
        return outputs

def train_model():
    print("\nPreparing training data...")
    
    # Enhanced training data with more structured examples
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
         "def find_max(a, b):\n    return a if a > b else b"),
        
        ("Write a function to calculate the sum of a list",
         "def sum_list(numbers):\n    return sum(numbers)"),
        
        ("Create a function to reverse a string",
         "def reverse_string(s):\n    return s[::-1]"),
        
        ("Write a function to count characters in a string",
         "def count_chars(s):\n    return len(s)"),
        
        ("Create a function to check if a string is empty",
         "def is_empty(s):\n    return len(s) == 0"),
        
        ("Write a function to get the first element of a list",
         "def get_first(lst):\n    return lst[0] if lst else None")
    ]
    
    descriptions, code_snippets = zip(*training_data)
    
    print(f"Number of training examples: {len(training_data)}")
    
    # Create dataset and dataloader
    dataset = CodeGenerationDataset(descriptions, code_snippets)
    train_loader = DataLoader(dataset, batch_size=2, shuffle=True)
    
    # Create model
    print("\nInitializing improved model...")
    model = ImprovedCodeGenerator(
        input_dim=len(dataset.desc_vocab),
        output_dim=len(dataset.code_vocab)
    )
    
    criterion = nn.CrossEntropyLoss(ignore_index=dataset.code_vocab['<pad>'])
    optimizer = optim.AdamW(model.parameters(), lr=0.001, weight_decay=0.01)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', patience=5)
    
    print("\nStarting training...")
    num_epochs = 100
    best_loss = float('inf')
    
    for epoch in range(num_epochs):
        model.train()
        total_loss = 0
        
        for desc, code in train_loader:
            optimizer.zero_grad()
            
            output = model(desc, code)
            output = output.view(-1, output.size(-1))
            code = code.view(-1)
            
            loss = criterion(output, code)
            loss.backward()
            
            # Gradient clipping
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1)
            
            optimizer.step()
            total_loss += loss.item()
        
        avg_loss = total_loss / len(train_loader)
        scheduler.step(avg_loss)
        
        if avg_loss < best_loss:
            best_loss = avg_loss
            torch.save(model.state_dict(), 'best_model.pth')
        
        if (epoch + 1) % 10 == 0:
            print(f"Epoch [{epoch+1}/{num_epochs}], Average Loss: {avg_loss:.4f}")
    
    # Load best model
    model.load_state_dict(torch.load('best_model.pth'))
    print("\nTraining completed!")
    return model, dataset

def generate_code(model, dataset, description, max_length=50):
    model.eval()
    
    # Encode input description
    desc_encoded = dataset.encode_text(description, dataset.desc_vocab)
    desc_tensor = torch.tensor(desc_encoded).unsqueeze(0)
    
    with torch.no_grad():
        outputs = model(desc_tensor, trg=None)
        predicted_indices = outputs.argmax(dim=-1).squeeze()
        
        # Convert indices to tokens
        code_tokens = []
        for idx in predicted_indices:
            token = list(dataset.code_vocab.keys())[list(dataset.code_vocab.values()).index(idx.item())]
            if token == '<end>':
                break
            if token not in ['<pad>', '<start>', '<unk>']:
                code_tokens.append(token)
                if token == ':':
                    code_tokens.append('\n    ')  # Add proper indentation
    
    return ' '.join(code_tokens)

def main():
    try:
        # Train the model
        model, dataset = train_model()
        
        # Test descriptions
        test_descriptions = [
            "Write a function to add two numbers",
            "Create a function to check if a number is positive",
            "Write a function to calculate the absolute value"
        ]
        
        print("\nGenerating code for test descriptions:")
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