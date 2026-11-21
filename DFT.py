
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

def plot_signal(t, x, title):
    plt.figure(figsize=(10, 4))
    plt.plot(t, x)
    plt.title(title)
    plt.xlabel('Time')
    plt.ylabel('Amplitude')
    plt.grid(True)
    plt.show()

def plot_frequency_spectrum(freq, X, title):
    plt.figure(figsize=(10, 4))
    plt.plot(freq, np.abs(X))
    plt.title(title)
    plt.xlabel('Frequency')
    plt.ylabel('Magnitude')
    plt.grid(True)
    plt.show()

# Example usage
if __name__ == "__main__":
    # Generate a sample signal
    N = 1000  # number of sample points
    T = 1.0 / 800.0  # sample spacing
    t = np.linspace(0.0, N*T, N, endpoint=False)
    x = np.sin(50.0 * 2.0 * np.pi * t) + 0.5 * np.sin(80.0 * 2.0 * np.pi * t)

    # Compute DFT
    X = dft(x)

    # Compute frequencies for plotting
    freq = np.fft.fftfreq(N, T)[:N//2]

    # Plot original signal
    plot_signal(t, x, "Original Signal")

    # Plot frequency spectrum
    plot_frequency_spectrum(freq[:N//2], X[:N//2], "Frequency Spectrum")

    # Compute inverse DFT
    x_reconstructed = inverse_dft(X).real

    # Plot reconstructed signal
    plot_signal(t, x_reconstructed, "Reconstructed Signal")

    # Print mean squared error
    mse = np.mean((x - x_reconstructed) ** 2)
    print(f"Mean Squared Error: {mse}") 
