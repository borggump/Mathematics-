
import numpy as np
import matplotlib.pyplot as plt

def brownian_motion(T, N, num_paths):
    dt = T/N
    dW = np.sqrt(dt) * np.random.normal(0, 1, (num_paths, N))
    W = np.cumsum(dW, axis=1)
    return np.insert(W, 0, 0, axis=1)

def brownian_integral(T, N, num_paths):
    W = brownian_motion(T, N, num_paths)
    integral = np.sum(W[:, :-1] * np.diff(W), axis=1)
    return integral

def main():
    T = 1.0  # Time horizon
    N = 1000  # Number of time steps
    num_paths = 10000  # Number of sample paths

    integral_values = brownian_integral(T, N, num_paths)
   
    # Theoretical mean and variance
    theoretical_mean = 0
    theoretical_var = T**2 / 2

    # Empirical mean and variance
    empirical_mean = np.mean(integral_values)
    empirical_var = np.var(integral_values)

    print(f"Theoretical mean: {theoretical_mean}")
    print(f"Empirical mean: {empirical_mean}")
    print(f"Theoretical variance: {theoretical_var}")
    print(f"Empirical variance: {empirical_var}")

    # Plot histogram of integral values
    plt.hist(integral_values, bins=50, density=True)
    plt.title("Distribution of Brownian Integral Values")
    plt.xlabel("Integral Value")
    plt.ylabel("Density")
    plt.show()

if __name__ == "__main__":
    main() 
