
import numpy as np
from scipy.integrate import odeint
import matplotlib.pyplot as plt

def blasius_ode(y, eta):
    f, f_prime, f_double_prime = y
    return [f_prime, f_double_prime, -0.5 * f * f_double_prime]

def solve_blasius():
    # Initial conditions
    y0 = [0, 0, 0.332]  # Initial guess for f''(0)
   
    # Range of eta values
    eta = np.linspace(0, 10, 1000)
   
    # Solve ODE
    solution = odeint(blasius_ode, y0, eta)
   
    # Extract f, f', and f'' from the solution
    f = solution[:, 0]
    f_prime = solution[:, 1]
    f_double_prime = solution[:, 2]
   
    return eta, f, f_prime, f_double_prime

def plot_results(eta, f, f_prime, f_double_prime):
    plt.figure(figsize=(12, 8))
   
    plt.plot(eta, f, label='f')
    plt.plot(eta, f_prime, label="f'")
    plt.plot(eta, f_double_prime, label="f''")
   
    plt.xlabel('η')
    plt.ylabel('f, f\', f\'\'')
    plt.title('Blasius Boundary Layer Solution')
    plt.legend()
    plt.grid(True)
   
    plt.show()

if __name__ == "__main__":
    eta, f, f_prime, f_double_prime = solve_blasius()
    plot_results(eta, f, f_prime, f_double_prime)

    # Print some key values
    print(f"Boundary layer thickness (η at 99% of free stream velocity): {np.interp(0.99, f_prime, eta):.4f}")
    print(f"Wall shear stress parameter (f''(0)): {f_double_prime[0]:.4f}") 
