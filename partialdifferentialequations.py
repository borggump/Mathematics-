import numpy as np
from scipy.sparse import diags
from scipy.sparse.linalg import spsolve
import matplotlib.pyplot as plt

class PDESolver:
    def __init__(self, dx=0.1, dt=0.01, x_range=(0, 1), t_range=(0, 1)):
        """Initialize solver with grid parameters."""
        self.dx = dx
        self.dt = dt
        self.x = np.arange(x_range[0], x_range[1] + dx, dx)
        self.t = np.arange(t_range[0], t_range[1] + dt, dt)
        self.Nx = len(self.x)
        self.Nt = len(self.t)

    def heat_equation(self, initial_condition, D=1.0, boundary_conditions=('dirichlet', 'dirichlet')):
        """
        Solve the heat equation: du/dt = D * d²u/dx²
        D: diffusion coefficient
        """
        r = D * self.dt / (self.dx ** 2)
        if r > 0.5:
            raise ValueError("Stability condition not met. Decrease dt or increase dx.")

        # Initialize solution matrix
        u = np.zeros((self.Nt, self.Nx))
        u[0] = initial_condition(self.x)

        # Create tridiagonal matrix for implicit scheme
        main_diag = np.ones(self.Nx) * (1 + 2*r)
        off_diag = np.ones(self.Nx-1) * (-r)
        A = diags([main_diag, off_diag, off_diag], [0, -1, 1]).toarray()

        # Apply boundary conditions
        for n in range(self.Nt-1):
            b = u[n].copy()
            u[n+1] = spsolve(A, b)

        return u

    def wave_equation(self, initial_position, initial_velocity, c=1.0):
        """
        Solve the wave equation: d²u/dt² = c² * d²u/dx²
        c: wave speed
        """
        r = (c * self.dt / self.dx) ** 2
        if r > 1:
            raise ValueError("Stability condition not met. Decrease dt or increase dx.")

        u = np.zeros((self.Nt, self.Nx))
        u[0] = initial_position(self.x)
        
        # First time step using initial velocity
        u[1, 1:-1] = 0.5 * r * (u[0, 2:] + u[0, :-2]) + \
                     (1 - r) * u[0, 1:-1] + \
                     self.dt * initial_velocity(self.x[1:-1])

        # Subsequent time steps
        for n in range(1, self.Nt-1):
            u[n+1, 1:-1] = r * (u[n, 2:] + u[n, :-2]) + \
                           2 * (1 - r) * u[n, 1:-1] - \
                           u[n-1, 1:-1]

        return u

    def advection_equation(self, initial_condition, v=1.0):
        """
        Solve the advection equation: du/dt + v * du/dx = 0
        v: velocity
        """
        r = v * self.dt / self.dx
        if abs(r) > 1:
            raise ValueError("Stability condition not met. Decrease dt or increase dx.")

        u = np.zeros((self.Nt, self.Nx))
        u[0] = initial_condition(self.x)

        # Upwind scheme
        for n in range(self.Nt-1):
            u[n+1, 1:] = u[n, 1:] - r * (u[n, 1:] - u[n, :-1])
            # Periodic boundary condition
            u[n+1, 0] = u[n+1, -1]

        return u

    def laplace_equation(self, boundary_conditions):
        """
        Solve Laplace equation: d²u/dx² + d²u/dy² = 0
        Using Jacobi iteration method
        """
        max_iter = 1000
        tolerance = 1e-4
        
        u = np.zeros((self.Nx, self.Nx))
        # Set boundary conditions
        u[0, :] = boundary_conditions['bottom']
        u[-1, :] = boundary_conditions['top']
        u[:, 0] = boundary_conditions['left']
        u[:, -1] = boundary_conditions['right']
        
        u_new = u.copy()
        
        for it in range(max_iter):
            u_old = u_new.copy()
            
            # Jacobi iteration
            u_new[1:-1, 1:-1] = 0.25 * (u_old[1:-1, 2:] + u_old[1:-1, :-2] + 
                                       u_old[2:, 1:-1] + u_old[:-2, 1:-1])
            
            # Check convergence
            if np.max(np.abs(u_new - u_old)) < tolerance:
                break
                
        return u_new

    def burgers_equation(self, initial_condition, nu=0.01):
        """
        Solve Burgers equation: du/dt + u*du/dx = nu*d²u/dx²
        nu: viscosity coefficient
        """
        u = np.zeros((self.Nt, self.Nx))
        u[0] = initial_condition(self.x)

        # Implicit scheme
        for n in range(self.Nt-1):
            # Predictor step (explicit)
            u_pred = u[n].copy()
            u_pred[1:-1] = u[n, 1:-1] - \
                          u[n, 1:-1] * self.dt/self.dx * (u[n, 1:-1] - u[n, :-2]) + \
                          nu * self.dt/self.dx**2 * (u[n, 2:] - 2*u[n, 1:-1] + u[n, :-2])
            
            # Corrector step (implicit)
            u[n+1] = u_pred

        return u

    def plot_solution(self, u, title="PDE Solution"):
        """Plot the solution as a 2D heatmap."""
        plt.figure(figsize=(10, 6))
        plt.imshow(u, aspect='auto', extent=[self.x[0], self.x[-1], self.t[-1], self.t[0]])
        plt.colorbar(label='u(x,t)')
        plt.xlabel('x')
        plt.ylabel('t')
        plt.title(title)
        plt.show()

# Example usage functions
def gaussian(x, mu=0.5, sigma=0.1):
    """Create a Gaussian initial condition."""
    return np.exp(-((x - mu)**2)/(2*sigma**2))

def sine_wave(x):
    """Create a sine wave initial condition."""
    return np.sin(2 * np.pi * x)