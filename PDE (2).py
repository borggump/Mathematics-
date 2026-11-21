import numpy as np
from scipy.sparse import diags
from scipy.sparse.linalg import spsolve
import matplotlib.pyplot as plt

class PDESolver:
    def __init__(self):
        """Initialize the PDE solver with common parameters"""
        self.nx = 100  # spatial points
        self.nt = 1000  # time points
        self.dx = 0.1  # spatial step
        self.dt = 0.001  # time step

    def heat_equation_1d(self, alpha=1.0, L=1.0, T=0.5, initial_temp=lambda x: np.sin(np.pi * x)):
        """
        Solve 1D heat equation: du/dt = α(d²u/dx²)
        Parameters:
            alpha: thermal diffusivity
            L: length of domain
            T: total time
            initial_temp: initial temperature distribution function
        """
        x = np.linspace(0, L, self.nx)
        t = np.linspace(0, T, self.nt)
        u = np.zeros((self.nt, self.nx))
        
        # Initial condition
        u[0, :] = initial_temp(x)
        # Boundary conditions
        u[:, 0] = u[:, -1] = 0
        
        r = alpha * self.dt / (self.dx ** 2)
        for n in range(0, self.nt - 1):
            u[n + 1, 1:-1] = r * u[n, :-2] + (1 - 2 * r) * u[n, 1:-1] + r * u[n, 2:]
        
        return x, t, u

    def wave_equation_1d(self, c=1.0, L=1.0, T=2.0, initial_displacement=lambda x: np.sin(np.pi * x)):
        """
        Solve 1D wave equation: d²u/dt² = c²(d²u/dx²)
        Parameters:
            c: wave speed
            L: length of domain
            T: total time
            initial_displacement: initial displacement function
        """
        x = np.linspace(0, L, self.nx)
        t = np.linspace(0, T, self.nt)
        u = np.zeros((self.nt, self.nx))
        
        # Initial conditions
        u[0, :] = initial_displacement(x)
        u[1, :] = u[0, :]  # Initial velocity = 0
        
        r = (c * self.dt / self.dx) ** 2
        for n in range(1, self.nt - 1):
            u[n + 1, 1:-1] = 2 * (1 - r) * u[n, 1:-1] + r * (u[n, :-2] + u[n, 2:]) - u[n - 1, 1:-1]
            
        return x, t, u

    def laplace_equation_2d(self, nx=50, ny=50, max_iter=1000, tolerance=1e-4):
        """
        Solve 2D Laplace equation: d²u/dx² + d²u/dy² = 0
        Using iterative method
        """
        u = np.zeros((ny, nx))
        
        # Boundary conditions
        u[0, :] = 0  # Bottom
        u[-1, :] = 100  # Top
        u[:, 0] = 0  # Left
        u[:, -1] = 0  # Right
        
        for it in range(max_iter):
            u_old = u.copy()
            u[1:-1, 1:-1] = 0.25 * (u[1:-1, 2:] + u[1:-1, :-2] + u[2:, 1:-1] + u[:-2, 1:-1])
            
            if np.max(np.abs(u - u_old)) < tolerance:
                break
                
        return u

    def transport_equation(self, c=1.0, L=1.0, T=1.0, initial_condition=lambda x: np.exp(-(x - 0.5)**2 / 0.1)):
        """
        Solve transport equation: du/dt + c(du/dx) = 0
        Using upwind scheme
        """
        x = np.linspace(0, L, self.nx)
        t = np.linspace(0, T, self.nt)
        u = np.zeros((self.nt, self.nx))
        
        # Initial condition
        u[0, :] = initial_condition(x)
        
        # Upwind scheme
        for n in range(self.nt - 1):
            u[n + 1, 1:] = u[n, 1:] - c * self.dt / self.dx * (u[n, 1:] - u[n, :-1])
            u[n + 1, 0] = u[n + 1, -1]  # Periodic boundary condition
            
        return x, t, u

    def burgers_equation(self, nu=0.1, L=1.0, T=1.0, initial_condition=lambda x: np.sin(2 * np.pi * x)):
        """
        Solve Burgers equation: du/dt + u(du/dx) = ν(d²u/dx²)
        Using upwind scheme for convection and central difference for diffusion
        """
        x = np.linspace(0, L, self.nx)
        t = np.linspace(0, T, self.nt)
        u = np.zeros((self.nt, self.nx))
        
        # Initial condition
        u[0, :] = initial_condition(x)
        
        for n in range(self.nt - 1):
            # Nonlinear convection term
            conv = u[n, :] * np.gradient(u[n, :], self.dx)
            # Diffusion term
            diff = nu * np.gradient(np.gradient(u[n, :], self.dx), self.dx)
            u[n + 1, :] = u[n, :] - self.dt * (conv - diff)
            
            # Periodic boundary conditions
            u[n + 1, 0] = u[n + 1, -1]
            
        return x, t, u

    def kdv_equation(self, L=50.0, T=5.0):
        """
        Solve KdV equation: du/dt + 6u(du/dx) + d³u/dx³ = 0
        Using finite difference method
        """
        x = np.linspace(-L/2, L/2, self.nx)
        t = np.linspace(0, T, self.nt)
        u = np.zeros((self.nt, self.nx))
        
        # Initial condition (single soliton)
        c = 0.5  # Wave speed
        u[0, :] = 0.5 * c * np.cosh(np.sqrt(c) * x/2)**(-2)
        
        # Finite difference scheme
        for n in range(self.nt - 1):
            # Third derivative term
            uxxx = np.gradient(np.gradient(np.gradient(u[n, :], self.dx), self.dx), self.dx)
            # Nonlinear term
            uux = u[n, :] * np.gradient(u[n, :], self.dx)
            u[n + 1, :] = u[n, :] - self.dt * (6 * uux + uxxx)
            
        return x, t, u

    def plot_solution(self, x, t, u, title="PDE Solution"):
        """Utility method to plot the solution"""
        X, T = np.meshgrid(x, t)
        
        plt.figure(figsize=(10, 6))
        plt.pcolormesh(X, T, u, shading='auto')
        plt.colorbar(label='u(x,t)')
        plt.xlabel('x')
        plt.ylabel('t')
        plt.title(title)
        plt.show()

def main():
    # Create solver instance
    solver = PDESolver()
    
    # Example 1: Heat Equation
    print("Solving Heat Equation...")
    x, t, u_heat = solver.heat_equation_1d()
    solver.plot_solution(x, t, u_heat, "Heat Equation Solution")
    
    # Example 2: Wave Equation
    print("Solving Wave Equation...")
    x, t, u_wave = solver.wave_equation_1d()
    solver.plot_solution(x, t, u_wave, "Wave Equation Solution")
    
    # Example 3: Laplace Equation
    print("Solving Laplace Equation...")
    u_laplace = solver.laplace_equation_2d()
    plt.figure(figsize=(8, 6))
    plt.imshow(u_laplace)
    plt.colorbar(label='u(x,y)')
    plt.title("Laplace Equation Solution")
    plt.show()
    
    # Example 4: Transport Equation
    print("Solving Transport Equation...")
    x, t, u_transport = solver.transport_equation()
    solver.plot_solution(x, t, u_transport, "Transport Equation Solution")
    
    # Example 5: Burgers Equation
    print("Solving Burgers Equation...")
    x, t, u_burgers = solver.burgers_equation()
    solver.plot_solution(x, t, u_burgers, "Burgers Equation Solution")
    
    # Example 6: KdV Equation
    print("Solving KdV Equation...")
    x, t, u_kdv = solver.kdv_equation()
    solver.plot_solution(x, t, u_kdv, "KdV Equation Solution")

if __name__ == "__main__":
    main()