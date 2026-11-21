#!/usr/bin/env python3
"""
GPU-Accelerated Neural Network for Image Classification on Linux
This program trains a convolutional neural network to classify images
using PyTorch with GPU acceleration if available.
"""

import os
import time
import argparse
from pathlib import Path

import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from torch.utils.data import DataLoader
from torchvision import datasets, transforms, models
import matplotlib.pyplot as plt
import numpy as np

class ConvNet(nn.Module):
    """
    Simple Convolutional Neural Network for image classification
    """
    def __init__(self, num_classes=10):
        super(ConvNet, self).__init__()
        self.conv1 = nn.Conv2d(3, 32, 3, padding=1)
        self.conv2 = nn.Conv2d(32, 64, 3, padding=1)
        self.conv3 = nn.Conv2d(64, 128, 3, padding=1)
        self.pool = nn.MaxPool2d(2, 2)
        self.fc1 = nn.Linear(128 * 4 * 4, 512)
        self.fc2 = nn.Linear(512, num_classes)
        self.dropout = nn.Dropout(0.2)

    def forward(self, x):
        x = self.pool(F.relu(self.conv1(x)))
        x = self.pool(F.relu(self.conv2(x)))
        x = self.pool(F.relu(self.conv3(x)))
        x = x.view(-1, 128 * 4 * 4)
        x = self.dropout(F.relu(self.fc1(x)))
        x = self.fc2(x)
        return x

def get_device():
    """Check if GPU is available and return appropriate device"""
    if torch.cuda.is_available():
        device = torch.device("cuda")
        print(f"Using GPU: {torch.cuda.get_device_name(0)}")
        print(f"CUDA Version: {torch.version.cuda}")
        print(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
    else:
        device = torch.device("cpu")
        print("GPU not available, using CPU instead")
    return device

def load_data(data_dir, batch_size=64):
    """Load and transform the dataset"""
    transform = transforms.Compose([
        transforms.Resize((32, 32)),
        transforms.ToTensor(),
        transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
    ])

    # CIFAR-10 dataset will be downloaded if not present
    train_dataset = datasets.CIFAR10(
        root=data_dir, train=True, download=True, transform=transform
    )
    test_dataset = datasets.CIFAR10(
        root=data_dir, train=False, download=True, transform=transform
    )

    train_loader = DataLoader(
        train_dataset, batch_size=batch_size, shuffle=True, num_workers=4
    )
    test_loader = DataLoader(
        test_dataset, batch_size=batch_size, shuffle=False, num_workers=4
    )

    classes = ('plane', 'car', 'bird', 'cat', 'deer', 
               'dog', 'frog', 'horse', 'ship', 'truck')

    return train_loader, test_loader, classes

def train_model(model, train_loader, device, epochs=10, learning_rate=0.001):
    """Train the neural network model"""
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=2, factor=0.5)
    
    model.to(device)
    
    history = {
        'train_loss': [],
        'train_acc': []
    }
    
    for epoch in range(epochs):
        model.train()
        running_loss = 0.0
        correct = 0
        total = 0
        
        start_time = time.time()
        
        for i, (inputs, labels) in enumerate(train_loader):
            inputs, labels = inputs.to(device), labels.to(device)
            
            # Zero the parameter gradients
            optimizer.zero_grad()
            
            # Forward + backward + optimize
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            
            # Statistics
            running_loss += loss.item()
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
            
            if i % 100 == 99:
                print(f'Epoch {epoch+1}, Batch {i+1}: Loss: {running_loss/100:.3f}, '
                      f'Acc: {100*correct/total:.2f}%')
                running_loss = 0.0
        
        epoch_loss = running_loss / len(train_loader)
        epoch_acc = 100 * correct / total
        
        history['train_loss'].append(epoch_loss)
        history['train_acc'].append(epoch_acc)
        
        scheduler.step(epoch_loss)
        
        time_elapsed = time.time() - start_time
        print(f'Epoch {epoch+1} completed in {time_elapsed:.2f}s: '
              f'Loss: {epoch_loss:.3f}, Acc: {epoch_acc:.2f}%')
    
    return history

def evaluate_model(model, test_loader, device):
    """Evaluate the model on test data"""
    model.eval()
    correct = 0
    total = 0
    
    class_correct = [0] * 10
    class_total = [0] * 10
    
    with torch.no_grad():
        for inputs, labels in test_loader:
            inputs, labels = inputs.to(device), labels.to(device)
            outputs = model(inputs)
            _, predicted = torch.max(outputs, 1)
            
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
            
            for i in range(labels.size(0)):
                label = labels[i]
                pred = predicted[i]
                if label == pred:
                    class_correct[label] += 1
                class_total[label] += 1
    
    accuracy = 100 * correct / total
    print(f'Test Accuracy: {accuracy:.2f}%')
    
    return accuracy, class_correct, class_total

def plot_results(history, accuracy, class_correct, class_total, classes, save_dir):
    """Plot and save training history and class accuracies"""
    save_dir = Path(save_dir)
    save_dir.mkdir(exist_ok=True)
    
    # Plot training loss and accuracy
    plt.figure(figsize=(12, 5))
    
    plt.subplot(1, 2, 1)
    plt.plot(history['train_loss'])
    plt.title('Training Loss')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    
    plt.subplot(1, 2, 2)
    plt.plot(history['train_acc'])
    plt.title('Training Accuracy')
    plt.xlabel('Epoch')
    plt.ylabel('Accuracy (%)')
    
    plt.tight_layout()
    plt.savefig(save_dir / 'training_history.png')
    
    # Plot per-class accuracy
    plt.figure(figsize=(10, 6))
    class_accuracies = [100 * class_correct[i] / class_total[i] for i in range(10)]
    
    plt.bar(classes, class_accuracies)
    plt.title('Per-Class Accuracy')
    plt.xlabel('Class')
    plt.ylabel('Accuracy (%)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(save_dir / 'class_accuracy.png')
    
    # Save model summary
    with open(save_dir / 'model_summary.txt', 'w') as f:
        f.write(f'Overall Test Accuracy: {accuracy:.2f}%\n\n')
        f.write('Per-Class Accuracy:\n')
        for i, cls in enumerate(classes):
            f.write(f'{cls}: {class_accuracies[i]:.2f}%\n')

def save_model(model, save_path):
    """Save the trained model"""
    torch.save(model.state_dict(), save_path)
    print(f'Model saved to {save_path}')

def load_pretrained_model(num_classes=10):
    """Alternative: Load a pre-trained model and adapt it"""
    model = models.resnet18(pretrained=True)
    
    # Freeze all parameters
    for param in model.parameters():
        param.requires_grad = False
    
    # Replace the final fully connected layer
    num_features = model.fc.in_features
    model.fc = nn.Linear(num_features, num_classes)
    
    return model

def visualize_predictions(model, test_loader, classes, device, num_images=5):
    """Visualize some predictions"""
    model.eval()
    
    # Get a batch of test images
    dataiter = iter(test_loader)
    images, labels = next(dataiter)
    
    # Make predictions
    with torch.no_grad():
        images = images.to(device)
        outputs = model(images)
        _, predicted = torch.max(outputs, 1)
    
    # Plot images with predictions
    plt.figure(figsize=(15, 3))
    for i in range(num_images):
        plt.subplot(1, num_images, i+1)
        plt.imshow(np.transpose((images[i].cpu().numpy() * 0.5) + 0.5, (1, 2, 0)))
        color = 'green' if predicted[i] == labels[i] else 'red'
        plt.title(f'Pred: {classes[predicted[i]]}\nTrue: {classes[labels[i]]}', color=color)
        plt.axis('off')
    plt.tight_layout()
    plt.savefig('predictions.png')

def main():
    """Main function to run the program"""
    parser = argparse.ArgumentParser(description='Train a CNN on CIFAR-10 with GPU acceleration')
    parser.add_argument('--data_dir', type=str, default='./data', help='Directory to store the dataset')
    parser.add_argument('--save_dir', type=str, default='./results', help='Directory to save results')
    parser.add_argument('--batch_size', type=int, default=64, help='Batch size for training')
    parser.add_argument('--epochs', type=int, default=5, help='Number of epochs to train')
    parser.add_argument('--learning_rate', type=float, default=0.001, help='Learning rate')
    parser.add_argument('--pretrained', action='store_true', help='Use pretrained model')
    parser.add_argument('--model_path', type=str, default='model.pth', help='Path to save/load model')
    args = parser.parse_args()
    
    # Create directories
    os.makedirs(args.data_dir, exist_ok=True)
    os.makedirs(args.save_dir, exist_ok=True)
    
    # Get device (GPU or CPU)
    device = get_device()
    
    # Load data
    train_loader, test_loader, classes = load_data(args.data_dir, args.batch_size)
    
    # Create model
    if args.pretrained:
        print("Using pretrained ResNet18 model")
        model = load_pretrained_model(num_classes=len(classes))
    else:
        print("Using custom CNN model")
        model = ConvNet(num_classes=len(classes))
    
    # Print model summary
    print(f"Model: {model.__class__.__name__}")
    print(f"Parameters: {sum(p.numel() for p in model.parameters())}")
    
    # Train model
    history = train_model(
        model, train_loader, device, 
        epochs=args.epochs, learning_rate=args.learning_rate
    )
    
    # Evaluate model
    accuracy, class_correct, class_total = evaluate_model(model, test_loader, device)
    
    # Plot results
    plot_results(history, accuracy, class_correct, class_total, classes, args.save_dir)
    
    # Save model
    save_model(model, os.path.join(args.save_dir, args.model_path))
    
    # Visualize some predictions
    visualize_predictions(model, test_loader, classes, device)

if __name__ == '__main__':
    main()