
import numpy as np
import matplotlib.pyplot as plt

def brownian_motion(T, N, seed=None):
    """
    Generate a Brownian motion path.
   
    Parameters:
    T (float): Total time
    N (int): Number of time steps
    seed (int): Random seed for reproducibility
   
    Returns:
    tuple: Time points and Brownian motion values
    """
    if seed is not None:
        np.random.seed(seed)
   
    dt = T/N
    dB = np.random.normal(0, np.sqrt(dt), N)
    B = np.cumsum(dB)
    B = np.insert(B, 0, 0)  # Insert B_0 = 0 at the beginning
    t = np.linspace(0, T, N+1)
    return t, B

def ito_integral(f, B, t):
    """
    Compute the Itô integral of f(t) dB(t).
   
    Parameters:
    f (function): Integrand function
    B (array): Brownian motion values
    t (array): Time points
   
    Returns:
    float: Approximation of the Itô integral
    """
    dB = np.diff(B)
    f_values = f(t[:-1])
    return np.sum(f_values * dB)

def main():
    # Parameters
    T = 1.0  # Total time
    N = 10000  # Number of time steps
   
    # Generate Brownian motion
    t, B = brownian_motion(T, N, seed=42)
   
    # Define the integrand function
    f = lambda t: t  # For example, we'll integrate t dB(t)
   
    # Compute the Itô integral
    integral_value = ito_integral(f, B, t)
   
    print(f"Approximation of the Itô integral of t dB(t) from 0 to {T}: {integral_value:.6f}")
   
    # Plot Brownian motion path
    plt.figure(figsize=(10, 6))
    plt.plot(t, B)
    plt.title("Brownian Motion Path")
    plt.xlabel("Time")
    plt.ylabel("B(t)")
    plt.grid(True)
    plt.show()
   
    # Plot the integrand function
    plt.figure(figsize=(10, 6))
    plt.plot(t, f(t))
    plt.title("Integrand Function: f(t) = t")
    plt.xlabel("Time")
    plt.ylabel("f(t)")
    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    main() 
