import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
import ccxt
import cntalib
import matplotlib.pyplot as plt

# Function to fetch historical cryptocurrency data
def fetch_crypto_data(symbol, timeframe, limit):
    exchange = ccxt.binance()
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    return df

# Function to calculate technical indicators
def calculate_indicators(df):
    df['SMA'] = talib.SMA(df['close'], timeperiod=14)
    df['RSI'] = talib.RSI(df['close'], timeperiod=14)
    df['MACD'], df['MACD_Signal'], _ = talib.MACD(df['close'], fastperiod=12, slowperiod=26, signalperiod=9)
    df['ATR'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=14)
    df['BB_Upper'], df['BB_Middle'], df['BB_Lower'] = talib.BBANDS(df['close'], timeperiod=20)
    return df

# Function to prepare data for CNN
def prepare_data(df, sequence_length):
    df = df.dropna()
    features = ['close', 'SMA', 'RSI', 'MACD', 'ATR', 'BB_Upper', 'BB_Lower']
    
    X = []
    y = []
    
    for i in range(len(df) - sequence_length):
        X.append(df[features].iloc[i:(i + sequence_length)].values)
        y.append(1 if df['close'].iloc[i + sequence_length] > df['close'].iloc[i + sequence_length - 1] else 0)
    
    return np.array(X), np.array(y)

# CNN model definition
class CNN(nn.Module):
    def __init__(self, input_size):
        super(CNN, self).__init__()
        self.conv1 = nn.Conv1d(input_size, 64, kernel_size=3)
        self.pool = nn.MaxPool1d(2)
        self.conv2 = nn.Conv1d(64, 128, kernel_size=3)
        self.fc1 = nn.Linear(128 * 3, 64)
        self.fc2 = nn.Linear(64, 1)
        self.relu = nn.ReLU()
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        x = self.relu(self.conv1(x))
        x = self.pool(x)
        x = self.relu(self.conv2(x))
        x = self.pool(x)
        x = x.view(x.size(0), -1)
        x = self.relu(self.fc1(x))
        x = self.sigmoid(self.fc2(x))
        return x

# Main function
def main():
    # Fetch historical data
    symbol = 'BTC/USDT'
    timeframe = '1h'
    limit = 5000
    df = fetch_crypto_data(symbol, timeframe, limit)
    
    # Calculate indicators
    df = calculate_indicators(df)
    
    # Prepare data for CNN
    sequence_length = 20
    X, y = prepare_data(df, sequence_length)
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Normalize data
    scaler = MinMaxScaler()
    X_train = scaler.fit_transform(X_train.reshape(-1, X_train.shape[-1])).reshape(X_train.shape)
    X_test = scaler.transform(X_test.reshape(-1, X_test.shape[-1])).reshape(X_test.shape)
    
    # Convert to PyTorch tensors
    X_train = torch.FloatTensor(X_train).permute(0, 2, 1)
    X_test = torch.FloatTensor(X_test).permute(0, 2, 1)
    y_train = torch.FloatTensor(y_train)
    y_test = torch.FloatTensor(y_test)
    
    # Create DataLoader
    train_dataset = TensorDataset(X_train, y_train)
    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
    
    # Initialize the model
    model = CNN(input_size=X_train.shape[1])
    
    # Define loss function and optimizer
    criterion = nn.BCELoss()
    optimizer = optim.SGD(model.parameters(), lr=0.01, momentum=0.9)
    
    # Train the model
    num_epochs = 50
    train_losses = []
    for epoch in range(num_epochs):
        model.train()
        for batch_X, batch_y in train_loader:
            optimizer.zero_grad()
            outputs = model(batch_X)
            loss = criterion(outputs.squeeze(), batch_y)
            loss.backward()
            optimizer.step()
        train_losses.append(loss.item())
        print(f'Epoch [{epoch+1}/{num_epochs}], Loss: {loss.item():.4f}')
    
    # Evaluate the model
    model.eval()
    with torch.no_grad():
        test_outputs = model(X_test)
        test_loss = criterion(test_outputs.squeeze(), y_test)
        predictions = (test_outputs.squeeze() > 0.5).float()
        accuracy = (predictions == y_test).float().mean()
        print(f'Test Loss: {test_loss:.4f}, Test Accuracy: {accuracy:.4f}')
    
    # Save the model
    torch.save(model.state_dict(), 'cnn_model_pytorch.pth')
    
    # Plot training loss
    plt.figure(figsize=(10, 5))
    plt.plot(train_losses)
    plt.title('Training Loss')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.show()
    
    # Function to make trading decisions
    def make_trading_decision(model, current_data):
        model.eval()
        with torch.no_grad():
            prediction = model(current_data)
        return "Buy" if prediction.item() > 0.5 else "Sell"
    
    # Simulate trading on recent data
    recent_data = df.iloc[-sequence_length:][['close', 'SMA', 'RSI', 'MACD', 'ATR', 'BB_Upper', 'BB_Lower']].values
    recent_data = scaler.transform(recent_data)
    recent_data = torch.FloatTensor(recent_data).unsqueeze(0).permute(0, 2, 1)
    
    decision = make_trading_decision(model, recent_data)
    print(f"Trading decision based on recent data: {decision}")

if __name__ == "__main__":
    main()