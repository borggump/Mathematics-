import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.animation import FuncAnimation
import random

class QuantumMagnifierSimulation:
    def __init__(self, root):
        self.root = root
        self.root.title("Quantum Wave Function Magnifier - Molecular Imaging Simulation")
        self.root.geometry("1400x900")
        
        # Simulation parameters
        self.num_atoms = 12
        self.tight_frequency = 1000.0  # Hz
        self.loose_frequency = 50.0    # Hz
        self.evolution_time = 0.1      # seconds
        self.magnification_factor = 1.0
        self.resolution_limit = 0.5    # micrometers
        
        # Atom positions and properties
        self.initial_positions = []
        self.magnified_positions = []
        self.atom_spins = []  # 0 for spin-up, 1 for spin-down
        
        # Animation variables
        self.animation_running = False
        self.animation_frame = 0
        self.total_animation_frames = 100
        
        self.setup_gui()
        self.generate_initial_atoms()
        self.update_simulation()
        
    def setup_gui(self):
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Control panel
        control_frame = ttk.LabelFrame(main_frame, text="Simulation Controls", padding=10)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Parameter controls
        params_frame = ttk.Frame(control_frame)
        params_frame.pack(fill=tk.X)
        
        # Number of atoms
        ttk.Label(params_frame, text="Number of Atoms:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.atoms_var = tk.IntVar(value=self.num_atoms)
        atoms_spinbox = ttk.Spinbox(params_frame, from_=1, to=50, textvariable=self.atoms_var, width=10)
        atoms_spinbox.grid(row=0, column=1, padx=(0, 20))
        
        # Tight trap frequency
        ttk.Label(params_frame, text="Tight Trap Frequency (Hz):").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.tight_freq_var = tk.DoubleVar(value=self.tight_frequency)
        tight_freq_spinbox = ttk.Spinbox(params_frame, from_=100, to=5000, textvariable=self.tight_freq_var, width=10)
        tight_freq_spinbox.grid(row=0, column=3, padx=(0, 20))
        
        # Loose trap frequency
        ttk.Label(params_frame, text="Loose Trap Frequency (Hz):").grid(row=1, column=0, sticky=tk.W, padx=(0, 5))
        self.loose_freq_var = tk.DoubleVar(value=self.loose_frequency)
        loose_freq_spinbox = ttk.Spinbox(params_frame, from_=10, to=500, textvariable=self.loose_freq_var, width=10)
        loose_freq_spinbox.grid(row=1, column=1, padx=(0, 20))
        
        # Evolution time
        ttk.Label(params_frame, text="Evolution Time (s):").grid(row=1, column=2, sticky=tk.W, padx=(0, 5))
        self.evolution_time_var = tk.DoubleVar(value=self.evolution_time)
        evolution_spinbox = ttk.Spinbox(params_frame, from_=0.01, to=1.0, increment=0.01, 
                                      textvariable=self.evolution_time_var, width=10)
        evolution_spinbox.grid(row=1, column=3, padx=(0, 20))
        
        # Resolution limit
        ttk.Label(params_frame, text="Resolution Limit (μm):").grid(row=0, column=4, sticky=tk.W, padx=(0, 5))
        self.resolution_var = tk.DoubleVar(value=self.resolution_limit)
        resolution_spinbox = ttk.Spinbox(params_frame, from_=0.1, to=2.0, increment=0.1, 
                                       textvariable=self.resolution_var, width=10)
        resolution_spinbox.grid(row=0, column=5)
        
        # Buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="Generate New Atoms", command=self.generate_initial_atoms).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Update Simulation", command=self.update_simulation).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Animate Magnification", command=self.animate_magnification).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Reset", command=self.reset_simulation).pack(side=tk.LEFT)
        
        # Info display
        info_frame = ttk.LabelFrame(control_frame, text="Simulation Info", padding=5)
        info_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.info_text = tk.Text(info_frame, height=3, width=80)
        self.info_text.pack(fill=tk.X)
        
        # Visualization frame
        viz_frame = ttk.Frame(main_frame)
        viz_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create matplotlib figure
        self.fig, (self.ax1, self.ax2, self.ax3) = plt.subplots(1, 3, figsize=(15, 5))
        self.fig.suptitle('Quantum Wave Function Magnification Process', fontsize=14, fontweight='bold')
        
        # Embed matplotlib in tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, master=viz_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
    def generate_initial_atoms(self):
        """Generate random initial atomic positions in a harmonic trap"""
        self.num_atoms = self.atoms_var.get()
        self.initial_positions = []
        self.atom_spins = []
        
        # Generate positions with Gaussian distribution (ground state of harmonic oscillator)
        sigma = 0.2  # micrometers - characteristic size of tight trap
        
        for i in range(self.num_atoms):
            x = np.random.normal(0, sigma)
            y = np.random.normal(0, sigma)
            self.initial_positions.append([x, y])
            self.atom_spins.append(random.choice([0, 1]))  # Random spin
            
        self.update_info_display()
        
    def calculate_magnification(self):
        """Calculate the magnification factor based on trap parameters and evolution time"""
        # This follows the physics described in the paper
        omega_tight = 2 * np.pi * self.tight_freq_var.get()
        omega_loose = 2 * np.pi * self.loose_freq_var.get()
        t_evolution = self.evolution_time_var.get()
        
        # Quarter period evolution in tight trap
        t_quarter = np.pi / (2 * omega_tight)
        
        # Magnification factor calculation (simplified model)
        # Based on harmonic oscillator scaling laws
        frequency_ratio = omega_tight / omega_loose
        time_factor = omega_loose * t_evolution
        
        self.magnification_factor = frequency_ratio * np.abs(np.cos(time_factor))
        
        if self.magnification_factor < 1:
            self.magnification_factor = frequency_ratio  # Minimum magnification
            
        return self.magnification_factor
        
    def apply_magnification(self):
        """Apply the magnification transformation to atomic positions"""
        mag_factor = self.calculate_magnification()
        self.magnified_positions = []
        
        for pos in self.initial_positions:
            magnified_x = pos[0] * mag_factor
            magnified_y = pos[1] * mag_factor
            self.magnified_positions.append([magnified_x, magnified_y])
            
    def check_resolution(self, positions):
        """Check which atoms can be resolved given the resolution limit"""
        resolution = self.resolution_var.get()
        resolvable = []
        
        for i, pos in enumerate(positions):
            can_resolve = True
            for j, other_pos in enumerate(positions):
                if i != j:
                    distance = np.sqrt((pos[0] - other_pos[0])**2 + (pos[1] - other_pos[1])**2)
                    if distance < resolution:
                        can_resolve = False
                        break
            resolvable.append(can_resolve)
            
        return resolvable
        
    def update_simulation(self):
        """Update the simulation with current parameters"""
        self.apply_magnification()
        self.plot_results()
        self.update_info_display()
        
    def plot_results(self):
        """Plot the before, during, and after states"""
        self.ax1.clear()
        self.ax2.clear()
        self.ax3.clear()
        
        # Colors for different spins
        colors = ['red', 'blue']
        labels = ['Spin ↑', 'Spin ↓']
        
        # Plot 1: Initial state (before magnification)
        self.ax1.set_title('Before Magnification\n(Below Resolution Limit)', fontweight='bold')
        
        # Check which atoms are resolvable
        initial_resolvable = self.check_resolution(self.initial_positions)
        
        for i, (pos, spin) in enumerate(zip(self.initial_positions, self.atom_spins)):
            marker_style = 'o' if initial_resolvable[i] else 's'
            alpha = 1.0 if initial_resolvable[i] else 0.3
            self.ax1.scatter(pos[0], pos[1], c=colors[spin], s=100, marker=marker_style, 
                           alpha=alpha, edgecolors='black', linewidth=1)
            
            # Add resolution uncertainty circles
            if not initial_resolvable[i]:
                circle = plt.Circle((pos[0], pos[1]), self.resolution_var.get()/2, 
                                  fill=False, linestyle='--', color='gray', alpha=0.5)
                self.ax1.add_patch(circle)
        
        # Add resolution limit indicator
        self.ax1.axhline(y=self.resolution_var.get(), color='gray', linestyle='--', alpha=0.7)
        self.ax1.text(0, self.resolution_var.get() + 0.1, f'Resolution Limit: {self.resolution_var.get():.1f} μm', 
                     ha='center', fontsize=8)
        
        self.ax1.set_xlabel('Position X (μm)')
        self.ax1.set_ylabel('Position Y (μm)')
        self.ax1.grid(True, alpha=0.3)
        self.ax1.set_aspect('equal')
        
        # Plot 2: Magnification process (schematic)
        self.ax2.set_title('Magnification Process\n(Harmonic Trap Scaling)', fontweight='bold')
        
        # Show the trap potentials
        x_range = np.linspace(-2, 2, 100)
        tight_potential = 0.5 * (2 * np.pi * self.tight_freq_var.get())**2 * x_range**2
        loose_potential = 0.5 * (2 * np.pi * self.loose_freq_var.get())**2 * x_range**2
        
        # Normalize potentials for display
        tight_potential = tight_potential / np.max(tight_potential) * 2
        loose_potential = loose_potential / np.max(loose_potential) * 2
        
        self.ax2.plot(x_range, tight_potential, 'r-', linewidth=2, label=f'Tight Trap ({self.tight_freq_var.get():.0f} Hz)')
        self.ax2.plot(x_range, loose_potential, 'b-', linewidth=2, label=f'Loose Trap ({self.loose_freq_var.get():.0f} Hz)')
        
        # Add arrows showing the process
        self.ax2.annotate('1. Quarter period\nevolution', xy=(0, 1), xytext=(-1, 2.5),
                         arrowprops=dict(arrowstyle='->', color='red'), fontsize=8)
        self.ax2.annotate('2. Trap transfer', xy=(0, 0.5), xytext=(1, 2.5),
                         arrowprops=dict(arrowstyle='->', color='blue'), fontsize=8)
        
        self.ax2.set_xlabel('Position (normalized)')
        self.ax2.set_ylabel('Potential Energy (normalized)')
        self.ax2.legend()
        self.ax2.grid(True, alpha=0.3)
        
        # Plot 3: Final state (after magnification)
        self.ax3.set_title(f'After Magnification\n(Magnification Factor: {self.magnification_factor:.1f}×)', fontweight='bold')
        
        magnified_resolvable = self.check_resolution(self.magnified_positions)
        
        for i, (pos, spin) in enumerate(zip(self.magnified_positions, self.atom_spins)):
            marker_style = 'o' if magnified_resolvable[i] else 's'
            alpha = 1.0 if magnified_resolvable[i] else 0.3
            self.ax3.scatter(pos[0], pos[1], c=colors[spin], s=100, marker=marker_style, 
                           alpha=alpha, edgecolors='black', linewidth=1)
        
        # Add resolution limit indicator
        max_range = max([max(abs(pos[0]), abs(pos[1])) for pos in self.magnified_positions]) * 1.2
        self.ax3.axhline(y=self.resolution_var.get(), color='gray', linestyle='--', alpha=0.7)
        self.ax3.axhline(y=-self.resolution_var.get(), color='gray', linestyle='--', alpha=0.7)
        self.ax3.axvline(x=self.resolution_var.get(), color='gray', linestyle='--', alpha=0.7)
        self.ax3.axvline(x=-self.resolution_var.get(), color='gray', linestyle='--', alpha=0.7)
        
        self.ax3.set_xlabel('Position X (μm)')
        self.ax3.set_ylabel('Position Y (μm)')
        self.ax3.grid(True, alpha=0.3)
        self.ax3.set_aspect('equal')
        
        # Create legend for spin states
        legend_elements = [plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='red', 
                                    markersize=8, label='Spin ↑'),
                          plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='blue', 
                                    markersize=8, label='Spin ↓')]
        self.ax3.legend(handles=legend_elements, loc='upper right')
        
        # Adjust layout and redraw
        plt.tight_layout()
        self.canvas.draw()
        
    def animate_magnification(self):
        """Animate the magnification process"""
        if not self.animation_running:
            self.animation_running = True
            self.animation_frame = 0
            self.animate_step()
        
    def animate_step(self):
        """Single step of animation"""
        if self.animation_frame < self.total_animation_frames and self.animation_running:
            # Calculate intermediate positions
            progress = self.animation_frame / (self.total_animation_frames - 1)
            current_magnification = 1 + (self.magnification_factor - 1) * progress
            
            # Clear and plot intermediate state
            self.ax3.clear()
            self.ax3.set_title(f'Magnification Progress: {current_magnification:.1f}×', fontweight='bold')
            
            colors = ['red', 'blue']
            
            for i, (initial_pos, spin) in enumerate(zip(self.initial_positions, self.atom_spins)):
                current_x = initial_pos[0] * current_magnification
                current_y = initial_pos[1] * current_magnification
                self.ax3.scatter(current_x, current_y, c=colors[spin], s=100, 
                               edgecolors='black', linewidth=1)
            
            # Add resolution limit indicators
            self.ax3.axhline(y=self.resolution_var.get(), color='gray', linestyle='--', alpha=0.7)
            self.ax3.axhline(y=-self.resolution_var.get(), color='gray', linestyle='--', alpha=0.7)
            self.ax3.axvline(x=self.resolution_var.get(), color='gray', linestyle='--', alpha=0.7)
            self.ax3.axvline(x=-self.resolution_var.get(), color='gray', linestyle='--', alpha=0.7)
            
            self.ax3.set_xlabel('Position X (μm)')
            self.ax3.set_ylabel('Position Y (μm)')
            self.ax3.grid(True, alpha=0.3)
            self.ax3.set_aspect('equal')
            
            self.canvas.draw()
            
            self.animation_frame += 1
            self.root.after(50, self.animate_step)  # 50ms delay between frames
        else:
            self.animation_running = False
            self.update_simulation()  # Show final state
            
    def update_info_display(self):
        """Update the information display"""
        initial_resolvable = self.check_resolution(self.initial_positions)
        magnified_resolvable = self.check_resolution(self.magnified_positions)
        
        initial_resolved_count = sum(initial_resolvable)
        magnified_resolved_count = sum(magnified_resolvable)
        
        info_text = f"""Simulation Results:
• Initial state: {initial_resolved_count}/{self.num_atoms} atoms resolvable ({initial_resolved_count/self.num_atoms*100:.1f}%)
• Magnified state: {magnified_resolved_count}/{self.num_atoms} atoms resolvable ({magnified_resolved_count/self.num_atoms*100:.1f}%)
• Magnification factor: {self.magnification_factor:.2f}× | Resolution improvement: {magnified_resolved_count - initial_resolved_count} additional atoms resolved"""
        
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(1.0, info_text)
        
    def reset_simulation(self):
        """Reset simulation to default parameters"""
        self.atoms_var.set(12)
        self.tight_freq_var.set(1000.0)
        self.loose_freq_var.set(50.0)
        self.evolution_time_var.set(0.1)
        self.resolution_var.set(0.5)
        self.animation_running = False
        self.generate_initial_atoms()
        self.update_simulation()

def main():
    root = tk.Tk()
    app = QuantumMagnifierSimulation(root)
    root.mainloop()

if __name__ == "__main__":
    main()