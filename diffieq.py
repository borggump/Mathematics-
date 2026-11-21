
import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import odeint, solve_ivp
from scipy.optimize import fsolve
from sympy import Function, dsolve, Eq, exp, symbols, diff

def plot_solution(t, y, title):
    plt.figure(figsize=(10, 6))
    plt.plot(t, y)
    plt.title(title)
    plt.xlabel('t')
    plt.ylabel('y')
    plt.grid(True)
    plt.show()

# 1. First-order linear ODE: dy/dt = -k*y
def solve_first_order_linear():
    def model(y, t, k):
        return -k * y
   
    k = 0.3
    y0 = 5.0
    t = np.linspace(0, 20, 100)
   
    solution = odeint(model, y0, t, args=(k,))
    plot_solution(t, solution, "First-order linear ODE: dy/dt = -k*y")

# 2. Second-order linear ODE: d^2y/dt^2 + w^2*y = 0 (Simple Harmonic Oscillator)
def solve_second_order_linear():
    def model(t, y, w):
        y1, y2 = y
        dydt = [y2, -w**2 * y1]
        return dydt
   
    w = 1.0
    y0 = [1.0, 0.0]
    t = np.linspace(0, 20, 200)
   
    solution = solve_ivp(model, [0, 20], y0, t_eval=t, args=(w,))
    plot_solution(solution.t, solution.y[0], "Second-order linear ODE: d^2y/dt^2 + w^2*y = 0")

# 3. Nonlinear first-order ODE: dy/dt = y^2 - 1 (Logistic equation)
def solve_nonlinear_first_order():
    def model(y, t):
        return y**2 - 1
   
    y0 = 0.5
    t = np.linspace(0, 4, 100)
   
    solution = odeint(model, y0, t)
    plot_solution(t, solution, "Nonlinear first-order ODE: dy/dt = y^2 - 1")

# 4. System of first-order ODEs: Lorenz system
def solve_system_of_odes():
    def lorenz(t, xyz, sigma, rho, beta):
        x, y, z = xyz
        return [sigma * (y - x), x * (rho - z) - y, x * y - beta * z]
   
    sigma, rho, beta = 10, 28, 8/3
    xyz0 = [1.0, 1.0, 1.0]
    t = np.linspace(0, 50, 10000)
   
    solution = solve_ivp(lorenz, [0, 50], xyz0, t_eval=t, args=(sigma, rho, beta))
   
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')
    ax.plot(solution.y[0], solution.y[1], solution.y[2])
    ax.set_title("Lorenz Attractor")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    plt.show()

# 5. Boundary Value Problem: y'' + y = 0, y(0) = 0, y(π) = 1
def solve_boundary_value_problem():
    def model(y, t):
        return [y[1], -y[0]]
   
    def bc(ya, yb):
        return [ya[0], yb[0] - 1]
   
    t = np.linspace(0, np.pi, 100)
    y = np.zeros((2, t.size))
   
    y_guess = np.zeros((2, t.size))
    y_guess[0] = t
   
    solution = fsolve(lambda x: odeint(model, [x[0], x[1]], t)[-1] - [1, x[1]], [0, 1])
    y = odeint(model, [solution[0], solution[1]], t)
   
    plot_solution(t, y[:, 0], "Boundary Value Problem: y'' + y = 0, y(0) = 0, y(π) = 1")

# 6. Partial Differential Equation: Heat equation (ut = kuxx)
def solve_heat_equation():
    def pde_model(u, x, t, k):
        return k * np.gradient(np.gradient(u, x), x)
   
    k = 0.5
    x = np.linspace(0, 1, 100)
    t = np.linspace(0, 0.5, 1000)
    dx = x[1] - x[0]
    dt = t[1] - t[0]
   
    u = np.zeros((len(t), len(x)))
    u[0] = np.sin(np.pi * x)
   
    for i in range(1, len(t)):
        u[i] = u[i-1] + dt * pde_model(u[i-1], x, t[i-1], k)
        u[i, 0] = u[i, -1] = 0
   
    plt.figure(figsize=(12, 8))
    plt.imshow(u, extent=[x.min(), x.max(), t.max(), t.min()],
               aspect='auto', cmap='viridis')
    plt.colorbar(label='Temperature')
    plt.title("Heat Equation: ut = kuxx")
    plt.xlabel("x")
    plt.ylabel("t")
    plt.show()

# Solve and plot all equations
solve_first_order_linear()
solve_second_order_linear()
solve_nonlinear_first_order()
solve_system_of_odes()
solve_boundary_value_problem()
solve_heat_equation()

# Bonus: Symbolic solution for a simple ODE
def symbolic_solution():
    t = symbols('t')
    y = Function('y')(t)
    k = symbols('k')
    ode = Eq(y.diff(t), -k*y)
    solution = dsolve(ode, y)
    print("Symbolic solution for dy/dt = -k*y:")
    print(solution)

symbolic_solution() 
