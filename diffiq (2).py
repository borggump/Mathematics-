import numpy as np
from scipy.integrate import odeint
import matplotlib.pyplot as plt

def solve_ode(func, y0, t, args=()):
    """
    Solve a first-order ODE numerically.
    
    Parameters:
    func : callable(y, t, ...)
        Function that computes the derivative of y at t.
    y0 : array
        Initial condition on y (can be a scalar or array).
    t : array
        A sequence of time points for which to solve for y.
    args : tuple, optional
        Extra arguments to pass to function.
        
    Returns:
    y : array
        Array containing the value of y for each desired time in t.
    """
    solution = odeint(func, y0, t, args=args)
    return solution

def example_ode(y, t, k):
    """Example ODE: dy/dt = -k*y"""
    return -k * y

# Set up parameters
k = 0.3
y0 = 5.0
t = np.linspace(0, 20, 100)

# Solve the ODE
solution = solve_ode(example_ode, y0, t, args=(k,))

# Plot the result
plt.figure(figsize=(10, 6))
plt.plot(t, solution, 'b', label='y(t)')
plt.xlabel('t')
plt.ylabel('y')
plt.title('Solution of dy/dt = -k*y')
plt.legend()
plt.grid(True)
plt.show()

# Print some values
print("t\ty")
for i in range(0, len(t), 10):
    print(f"{t[i]:.2f}\t{solution[i][0]:.4f}")