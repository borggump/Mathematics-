import numpy as np
import matplotlib.pyplot as plt

def dft(x):
    """
    Compute the Discrete Fourier Transform of the 1D array x
    """
    N = len(x)
    n = np.arange(N)
    k = n.reshape((N, 1))
    e = np.exp(-2j * np.pi * k * n / N)
    return np.dot(e, x)

def inverse_dft(X):
    """
    Compute the Inverse Discrete Fourier Transform of the 1D array X
    """
    N = len(X)
    n = np.arange(N)
    k = n.reshape((N, 1))
    e = np.exp(2j * np.pi * k * n / N)
    return np.dot(e, X) / N

def plot_dft_analysis(t, x, freq, X, x_reconstructed):
    """
    Plot original signal, frequency spectrum, and reconstructed signal in a single figure
    """
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10))
    fig.suptitle('Discrete Fourier Transform Analysis', fontsize=14)
    
    # Plot original signal
    ax1.plot(t, x)
    ax1.set_title('Original Signal')
    ax1.set_xlabel('Time')
    ax1.set_ylabel('Amplitude')
    ax1.grid(True)
    
    # Plot frequency spectrum
    ax2.plot(freq, np.abs(X))
    ax2.set_title('Frequency Spectrum')
    ax2.set_xlabel('Frequency')
    ax2.set_ylabel('Magnitude')
    ax2.grid(True)
    
    # Plot reconstructed signal
    ax3.plot(t, x_reconstructed)
    ax3.set_title('Reconstructed Signal')
    ax3.set_xlabel('Time')
    ax3.set_ylabel('Amplitude')
    ax3.grid(True)
    
    # Adjust layout to prevent overlap
    plt.tight_layout()
    plt.show()

# Example usage
if __name__ == "__main__":
    # Generate a sample signal
    N = 1000  # number of sample points
    T = 1.0 / 800.0  # sample spacing
    t = np.linspace(0.0, N*T, N, endpoint=False)
    
    # Create a more complex signal with three frequency components
    x = (np.sin(50.0 * 2.0 * np.pi * t) + 
         0.5 * np.sin(80.0 * 2.0 * np.pi * t) +
         0.3 * np.sin(120.0 * 2.0 * np.pi * t))

    # Compute DFT
    X = dft(x)

    # Compute frequencies for plotting
    freq = np.fft.fftfreq(N, T)[:N//2]

    # Compute inverse DFT
    x_reconstructed = inverse_dft(X).real

    # Plot all three signals
    plot_dft_analysis(t, x, freq[:N//2], np.abs(X[:N//2]), x_reconstructed)

    # Print mean squared error
    mse = np.mean((x - x_reconstructed) ** 2)
    print(f"Mean Squared Error: {mse}")