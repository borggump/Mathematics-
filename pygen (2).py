class CNNGenerator:
    def __init__(self):
        self.base_template = '''
import random
import math
from typing import List, Tuple

class Layer:
    def forward(self, input_data):
        raise NotImplementedError
        
    def backward(self, gradient, learning_rate):
        raise NotImplementedError

class ConvLayer(Layer):
    def __init__(self, kernel_size: int, num_filters: int):
        self.kernel_size = kernel_size
        self.num_filters = num_filters
        self.kernels = [[[random.uniform(-0.1, 0.1) for _ in range(kernel_size)]
                         for _ in range(kernel_size)]
                         for _ in range(num_filters)]
        self.biases = [0.0] * num_filters
        self.input_data = None
        self.output = None

    def pad_data(self, data: List[List[float]], padding: int) -> List[List[float]]:
        height = len(data)
        width = len(data[0])
        padded = [[0.0] * (width + 2 * padding) for _ in range(height + 2 * padding)]
        for i in range(height):
            for j in range(width):
                padded[i + padding][j + padding] = data[i][j]
        return padded

    def convolve(self, data: List[List[float]], kernel: List[List[float]]) -> List[List[float]]:
        height = len(data) - len(kernel) + 1
        width = len(data[0]) - len(kernel[0]) + 1
        result = [[0.0] * width for _ in range(height)]
        
        for i in range(height):
            for j in range(width):
                sum_val = 0.0
                for ki in range(len(kernel)):
                    for kj in range(len(kernel[0])):
                        sum_val += data[i + ki][j + kj] * kernel[ki][kj]
                result[i][j] = sum_val
        return result

    def forward(self, input_data: List[List[float]]) -> List[List[List[float]]]:
        self.input_data = input_data
        padding = self.kernel_size // 2
        padded_data = self.pad_data(input_data, padding)
        
        self.output = []
        for kernel, bias in zip(self.kernels, self.biases):
            feature_map = self.convolve(padded_data, kernel)
            # Apply ReLU activation
            for i in range(len(feature_map)):
                for j in range(len(feature_map[0])):
                    feature_map[i][j] = max(0, feature_map[i][j] + bias)
            self.output.append(feature_map)
        
        return self.output

    def backward(self, gradient: List[List[List[float]]], learning_rate: float):
        kernel_gradients = [[[0.0] * self.kernel_size for _ in range(self.kernel_size)]
                          for _ in range(self.num_filters)]
        bias_gradients = [0.0] * self.num_filters
        
        padding = self.kernel_size // 2
        padded_input = self.pad_data(self.input_data, padding)
        
        # Calculate gradients for kernels and biases
        for f in range(self.num_filters):
            for i in range(self.kernel_size):
                for j in range(self.kernel_size):
                    for x in range(len(gradient[f])):
                        for y in range(len(gradient[f][0])):
                            if self.output[f][x][y] > 0:  # ReLU gradient
                                kernel_gradients[f][i][j] += gradient[f][x][y] * padded_input[x + i][y + j]
                                bias_gradients[f] += gradient[f][x][y]
        
        # Update kernels and biases using SGD
        for f in range(self.num_filters):
            for i in range(self.kernel_size):
                for j in range(self.kernel_size):
                    self.kernels[f][i][j] -= learning_rate * kernel_gradients[f][i][j]
            self.biases[f] -= learning_rate * bias_gradients[f]

class MaxPoolLayer(Layer):
    def __init__(self, pool_size: int):
        self.pool_size = pool_size
        self.input_data = None
        self.output = None
        self.max_positions = None

    def forward(self, input_data: List[List[List[float]]]) -> List[List[List[float]]]:
        self.input_data = input_data
        self.max_positions = []
        output = []
        
        for feature_map in input_data:
            height = len(feature_map)
            width = len(feature_map[0])
            pooled = [[0.0] * (width // self.pool_size) for _ in range(height // self.pool_size)]
            positions = [[(-1, -1)] * (width // self.pool_size) for _ in range(height // self.pool_size)]
            
            for i in range(0, height, self.pool_size):
                for j in range(0, width, self.pool_size):
                    max_val = float('-inf')
                    max_pos = (-1, -1)
                    
                    for pi in range(self.pool_size):
                        for pj in range(self.pool_size):
                            if i + pi < height and j + pj < width:
                                val = feature_map[i + pi][j + pj]
                                if val > max_val:
                                    max_val = val
                                    max_pos = (i + pi, j + pj)
                    
                    pooled[i // self.pool_size][j // self.pool_size] = max_val
                    positions[i // self.pool_size][j // self.pool_size] = max_pos
            
            output.append(pooled)
            self.max_positions.append(positions)
        
        self.output = output
        return output

    def backward(self, gradient: List[List[List[float]]], learning_rate: float) -> List[List[List[float]]]:
        input_gradient = [[[0.0] * len(self.input_data[0][0]) for _ in range(len(self.input_data[0]))]
                         for _ in range(len(self.input_data))]
        
        for f in range(len(gradient)):
            for i in range(len(gradient[f])):
                for j in range(len(gradient[f][0])):
                    orig_i, orig_j = self.max_positions[f][i][j]
                    if orig_i != -1:
                        input_gradient[f][orig_i][orig_j] = gradient[f][i][j]
        
        return input_gradient

class CNN:
    def __init__(self, input_size: Tuple[int, int]):
        self.input_size = input_size
        self.layers = [
            ConvLayer(kernel_size=3, num_filters=16),
            MaxPoolLayer(pool_size=2),
            ConvLayer(kernel_size=3, num_filters=32),
            MaxPoolLayer(pool_size=2)
        ]

    def forward(self, input_data: List[List[float]]) -> List[float]:
        output = input_data
        for layer in self.layers:
            output = layer.forward(output)
        return output

    def backward(self, gradient: List[List[List[float]]], learning_rate: float):
        for layer in reversed(self.layers):
            gradient = layer.backward(gradient, learning_rate)

    def train(self, training_data, labels, epochs: int, learning_rate: float):
        for epoch in range(epochs):
            total_loss = 0
            for input_data, label in zip(training_data, labels):
                # Forward pass
                output = self.forward(input_data)
                
                # Calculate loss and gradient
                loss = 0
                gradient = [[[0.0] * len(output[0][0]) for _ in range(len(output[0]))]
                           for _ in range(len(output))]
                
                # Simple MSE loss and gradient
                for i in range(len(output)):
                    for j in range(len(output[0])):
                        for k in range(len(output[0][0])):
                            diff = output[i][j][k] - label[i][j][k]
                            loss += diff * diff
                            gradient[i][j][k] = 2 * diff
                
                total_loss += loss
                
                # Backward pass with SGD
                self.backward(gradient, learning_rate)
            
            if epoch % 10 == 0:
                print(f"Epoch {epoch}, Loss: {total_loss}")

def main():
    # Example usage
    print("Creating a CNN for image processing...")
    
    # Create random training data
    input_size = (28, 28)  # Example size
    num_samples = 10
    
    training_data = [[[random.uniform(0, 1) for _ in range(input_size[1])]
                      for _ in range(input_size[0])]
                     for _ in range(num_samples)]
    
    # Create random labels (same size as final output)
    output_size = (32, 6, 6)  # Example size after convolutions and pooling
    labels = [[[random.uniform(0, 1) for _ in range(output_size[2])]
               for _ in range(output_size[1])]
              for _ in range(output_size[0])]
    
    # Create and train the CNN
    cnn = CNN(input_size)
    print("Training the CNN...")
    cnn.train(training_data[:8], labels[:8], epochs=50, learning_rate=0.01)
    
    # Test the CNN
    print("\\nTesting the CNN...")
    test_output = cnn.forward(training_data[8])
    print(f"Output shape: {len(test_output)}x{len(test_output[0])}x{len(test_output[0][0])}")

if __name__ == "__main__":
    main()
'''
    
    def generate_cnn_program(self, specifications=None):
        if specifications is None:
            return self.base_template
        
        # Here you could add logic to customize the CNN based on specifications
        # For example, different layer configurations, learning rates, etc.
        return self.base_template

def main():
    print("Welcome to the CNN Generator!")
    print("This tool generates Convolutional Neural Network implementations with SGD optimization.")
    
    generator = CNNGenerator()
    
    while True:
        print("\nOptions:")
        print("1. Generate basic CNN with SGD")
        print("2. Exit")
        
        choice = input("\nEnter your choice (1-2): ")
        
        if choice == "2":
            print("Thank you for using the CNN Generator. Goodbye!")
            break
            
        elif choice == "1":
            print("\nGenerating CNN implementation...")
            generated_code = generator.generate_cnn_program()
            
            print("\nGenerated Python Code:")
            print(generated_code)
            
            save = input("\nDo you want to save this code to a file? (yes/no): ")
            if save.lower() == 'yes':
                filename = input("Enter filename (e.g., cnn_implementation.py): ")
                with open(filename, 'w') as file:
                    file.write(generated_code)
                print(f"Program saved to {filename}")
                
                run = input("Do you want to run this program now? (yes/no): ")
                if run.lower() == 'yes':
                    print("\nRunning the generated program:")
                    print("-" * 40)
                    exec(generated_code)
                    print("-" * 40)
        
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()