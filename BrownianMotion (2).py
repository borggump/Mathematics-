
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# Set random seed for reproducibility
np.random.seed(42)

# Number of particles
n_particles = 50

# Number of time steps
n_steps = 100

# Initialize particle positions
positions = np.random.rand(n_particles, 2)

# Create the figure and axis
fig, ax = plt.subplots(figsize=(8, 8))
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.set_title("Brownian Motion Simulation")

# Create scatter plot
scatter = ax.scatter(positions[:, 0], positions[:, 1], s=10)

# Animation update function
def update(frame):
    global positions
    # Generate random displacement
    displacement = np.random.normal(0, 0.01, (n_particles, 2))
    # Update positions
    positions += displacement
    # Ensure particles stay within bounds
    positions = np.clip(positions, 0, 1)
    # Update scatter plot
    scatter.set_offsets(positions)
    return scatter,

# Create animation
anim = FuncAnimation(fig, update, frames=n_steps, interval=50, blit=True)

plt.show() 
