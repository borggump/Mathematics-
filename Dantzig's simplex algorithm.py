import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import math

class SimplexSolver:
    def __init__(self):
        self.tableau = None
        self.solution_steps = []
        self.optimal_solution = None
        self.optimal_value = None
        
    def solve(self, c, A, b):
        """
        Solve linear programming problem using simplex algorithm
        Maximize: c^T * x
        Subject to: A * x <= b, x >= 0
        """
        self.solution_steps = []
        
        # Convert to standard form by adding slack variables
        m, n = A.shape
        
        # Create initial tableau
        # [A | I | b]
        # [c | 0 | 0]
        tableau = np.zeros((m + 1, n + m + 1))
        tableau[:m, :n] = A
        tableau[:m, n:n+m] = np.eye(m)  # Identity matrix for slack variables
        tableau[:m, -1] = b
        tableau[-1, :n] = -c  # Negative because we're maximizing
        
        self.tableau = tableau.copy()
        self.solution_steps.append(f"Initial Tableau:\n{self._format_tableau(tableau)}\n")
        
        iteration = 0
        while True:
            iteration += 1
            
            # Check optimality (all coefficients in bottom row <= 0)
            if np.all(tableau[-1, :-1] <= 1e-10):
                self.solution_steps.append("Optimal solution found!")
                break
                
            if iteration > 100:  # Prevent infinite loops
                self.solution_steps.append("Maximum iterations reached!")
                break
            
            # Find entering variable (most positive in bottom row)
            entering_col = np.argmax(tableau[-1, :-1])
            self.solution_steps.append(f"Iteration {iteration}:")
            self.solution_steps.append(f"Entering variable: x{entering_col + 1}")
            
            # Find leaving variable using minimum ratio test
            ratios = []
            for i in range(m):
                if tableau[i, entering_col] > 1e-10:
                    ratios.append(tableau[i, -1] / tableau[i, entering_col])
                else:
                    ratios.append(float('inf'))
            
            if all(r == float('inf') for r in ratios):
                self.solution_steps.append("Problem is unbounded!")
                return None, None
                
            leaving_row = np.argmin(ratios)
            self.solution_steps.append(f"Leaving variable row: {leaving_row + 1}")
            self.solution_steps.append(f"Pivot element: {tableau[leaving_row, entering_col]:.4f}")
            
            # Perform pivot operation
            pivot = tableau[leaving_row, entering_col]
            tableau[leaving_row] /= pivot
            
            for i in range(m + 1):
                if i != leaving_row:
                    tableau[i] -= tableau[i, entering_col] * tableau[leaving_row]
            
            self.solution_steps.append(f"Tableau after iteration {iteration}:\n{self._format_tableau(tableau)}\n")
        
        # Extract solution
        solution = np.zeros(n)
        for j in range(n):
            col = tableau[:m, j]
            if np.sum(np.abs(col) > 1e-10) == 1:  # Basic variable
                row = np.where(np.abs(col) > 1e-10)[0][0]
                if abs(col[row] - 1.0) < 1e-10:
                    solution[j] = tableau[row, -1]
        
        optimal_value = tableau[-1, -1]
        
        self.optimal_solution = solution
        self.optimal_value = optimal_value
        
        return solution, optimal_value
    
    def _format_tableau(self, tableau):
        """Format tableau for display"""
        m, n = tableau.shape
        result = []
        for i in range(m):
            row = " ".join(f"{tableau[i, j]:8.3f}" for j in range(n))
            result.append(row)
        return "\n".join(result)

class DantzigGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Dantzig's Simplex Algorithm - Linear Programming Solver")
        self.root.geometry("1200x800")
        
        self.solver = SimplexSolver()
        
        # Create notebook for tabs
        notebook = ttk.Notebook(root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Input tab
        self.input_frame = ttk.Frame(notebook)
        notebook.add(self.input_frame, text="Problem Input")
        
        # Solution tab
        self.solution_frame = ttk.Frame(notebook)
        notebook.add(self.solution_frame, text="Solution Steps")
        
        # Visualization tab
        self.viz_frame = ttk.Frame(notebook)
        notebook.add(self.viz_frame, text="Visualization")
        
        self.setup_input_tab()
        self.setup_solution_tab()
        self.setup_visualization_tab()
        
        # Load example problem
        self.load_example()
    
    def setup_input_tab(self):
        # Title and description
        title_label = tk.Label(self.input_frame, text="Linear Programming Problem Solver", 
                              font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        desc_label = tk.Label(self.input_frame, 
                             text="Solve: Maximize c₁x₁ + c₂x₂ + ... + cₙxₙ\nSubject to: Aₓ ≤ b, x ≥ 0",
                             font=("Arial", 12))
        desc_label.pack(pady=5)
        
        # Input sections
        input_container = ttk.Frame(self.input_frame)
        input_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Objective function
        obj_frame = ttk.LabelFrame(input_container, text="Objective Function (to Maximize)", padding=10)
        obj_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(obj_frame, text="Coefficients (c): ").pack(side=tk.LEFT)
        self.obj_entry = tk.Entry(obj_frame, width=30, font=("Courier", 10))
        self.obj_entry.pack(side=tk.LEFT, padx=5)
        tk.Label(obj_frame, text="Example: 3,2 for 3x₁ + 2x₂").pack(side=tk.LEFT, padx=10)
        
        # Constraints
        const_frame = ttk.LabelFrame(input_container, text="Constraints (Ax ≤ b)", padding=10)
        const_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        tk.Label(const_frame, text="Constraint Matrix A (one row per line):").pack(anchor=tk.W)
        self.constraint_matrix = scrolledtext.ScrolledText(const_frame, height=6, width=50, font=("Courier", 10))
        self.constraint_matrix.pack(fill=tk.BOTH, expand=True, pady=5)
        
        tk.Label(const_frame, text="Right-hand side vector b:").pack(anchor=tk.W, pady=(10,0))
        self.rhs_entry = tk.Entry(const_frame, width=30, font=("Courier", 10))
        self.rhs_entry.pack(anchor=tk.W, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(input_container)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="Solve Problem", command=self.solve_problem).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Load Example", command=self.load_example).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear All", command=self.clear_inputs).pack(side=tk.LEFT, padx=5)
    
    def setup_solution_tab(self):
        # Solution display
        solution_container = ttk.Frame(self.solution_frame)
        solution_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(solution_container, text="Solution Steps and Results", 
                font=("Arial", 14, "bold")).pack(pady=10)
        
        self.solution_text = scrolledtext.ScrolledText(solution_container, 
                                                      font=("Courier", 10),
                                                      wrap=tk.WORD)
        self.solution_text.pack(fill=tk.BOTH, expand=True)
    
    def setup_visualization_tab(self):
        # Visualization (only works for 2D problems)
        viz_container = ttk.Frame(self.viz_frame)
        viz_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(viz_container, text="Graphical Solution (2D Problems Only)", 
                font=("Arial", 14, "bold")).pack(pady=10)
        
        self.fig = Figure(figsize=(10, 6), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, viz_container)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def load_example(self):
        """Load a sample linear programming problem"""
        # Example: Maximize 3x₁ + 2x₂
        # Subject to: x₁ + x₂ ≤ 4, 2x₁ + x₂ ≤ 6, x₁,x₂ ≥ 0
        self.obj_entry.delete(0, tk.END)
        self.obj_entry.insert(0, "3,2")
        
        self.constraint_matrix.delete(1.0, tk.END)
        self.constraint_matrix.insert(1.0, "1,1\n2,1")
        
        self.rhs_entry.delete(0, tk.END)
        self.rhs_entry.insert(0, "4,6")
    
    def clear_inputs(self):
        """Clear all input fields"""
        self.obj_entry.delete(0, tk.END)
        self.constraint_matrix.delete(1.0, tk.END)
        self.rhs_entry.delete(0, tk.END)
        self.solution_text.delete(1.0, tk.END)
        self.fig.clear()
        self.canvas.draw()
    
    def parse_input(self):
        """Parse user input into numpy arrays"""
        try:
            # Parse objective function
            c_str = self.obj_entry.get().strip()
            c = np.array([float(x.strip()) for x in c_str.split(',')])
            
            # Parse constraint matrix
            A_str = self.constraint_matrix.get(1.0, tk.END).strip()
            A_rows = []
            for line in A_str.split('\n'):
                if line.strip():
                    row = [float(x.strip()) for x in line.split(',')]
                    A_rows.append(row)
            A = np.array(A_rows)
            
            # Parse RHS vector
            b_str = self.rhs_entry.get().strip()
            b = np.array([float(x.strip()) for x in b_str.split(',')])
            
            return c, A, b
            
        except Exception as e:
            messagebox.showerror("Input Error", f"Error parsing input: {str(e)}")
            return None, None, None
    
    def solve_problem(self):
        """Solve the linear programming problem"""
        c, A, b = self.parse_input()
        if c is None:
            return
        
        try:
            # Solve using simplex algorithm
            solution, optimal_value = self.solver.solve(c, A, b)
            
            # Display results
            self.solution_text.delete(1.0, tk.END)
            
            # Add problem statement
            self.solution_text.insert(tk.END, "PROBLEM STATEMENT:\n")
            self.solution_text.insert(tk.END, "=" * 50 + "\n")
            obj_str = " + ".join(f"{c[i]:.3f}x{i+1}" for i in range(len(c)))
            self.solution_text.insert(tk.END, f"Maximize: {obj_str}\n\n")
            
            self.solution_text.insert(tk.END, "Subject to:\n")
            for i in range(A.shape[0]):
                constraint_str = " + ".join(f"{A[i,j]:.3f}x{j+1}" for j in range(A.shape[1]))
                self.solution_text.insert(tk.END, f"  {constraint_str} ≤ {b[i]:.3f}\n")
            self.solution_text.insert(tk.END, "  All variables ≥ 0\n\n")
            
            # Add solution steps
            self.solution_text.insert(tk.END, "SIMPLEX ALGORITHM STEPS:\n")
            self.solution_text.insert(tk.END, "=" * 50 + "\n")
            for step in self.solver.solution_steps:
                self.solution_text.insert(tk.END, step + "\n")
            
            # Add final results
            if solution is not None:
                self.solution_text.insert(tk.END, "\nFINAL SOLUTION:\n")
                self.solution_text.insert(tk.END, "=" * 50 + "\n")
                for i, val in enumerate(solution):
                    self.solution_text.insert(tk.END, f"x{i+1} = {val:.6f}\n")
                self.solution_text.insert(tk.END, f"\nOptimal Value: {optimal_value:.6f}\n")
            
            # Create visualization for 2D problems
            if len(c) == 2:
                self.create_2d_visualization(c, A, b, solution, optimal_value)
                
        except Exception as e:
            messagebox.showerror("Solver Error", f"Error solving problem: {str(e)}")
    
    def create_2d_visualization(self, c, A, b, solution, optimal_value):
        """Create 2D visualization of the linear programming problem"""
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        
        # Create grid
        x_max = max(10, max(b) * 1.2)
        y_max = max(10, max(b) * 1.2)
        x = np.linspace(0, x_max, 400)
        
        # Plot constraints
        colors = ['red', 'blue', 'green', 'orange', 'purple']
        for i in range(A.shape[0]):
            if A[i, 1] != 0:  # Avoid division by zero
                y_constraint = (b[i] - A[i, 0] * x) / A[i, 1]
                ax.plot(x, y_constraint, color=colors[i % len(colors)], 
                       label=f'Constraint {i+1}', linewidth=2)
                
                # Fill feasible region
                y_constraint = np.maximum(0, y_constraint)
                ax.fill_between(x, 0, y_constraint, alpha=0.1, color=colors[i % len(colors)])
        
        # Plot objective function lines (iso-profit lines)
        if c[1] != 0:
            for profit in np.linspace(0, optimal_value, 5):
                y_obj = (profit - c[0] * x) / c[1]
                ax.plot(x, y_obj, 'k--', alpha=0.3, linewidth=1)
        
        # Plot optimal solution
        if solution is not None:
            ax.plot(solution[0], solution[1], 'ro', markersize=12, 
                   label=f'Optimal Solution ({solution[0]:.3f}, {solution[1]:.3f})')
            
            # Draw objective vector
            ax.arrow(solution[0], solution[1], c[0]/10, c[1]/10, 
                    head_width=0.2, head_length=0.3, fc='red', ec='red')
        
        ax.set_xlim(0, x_max)
        ax.set_ylim(0, y_max)
        ax.set_xlabel('x₁')
        ax.set_ylabel('x₂')
        ax.set_title('Linear Programming Problem Visualization')
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        self.canvas.draw()

def main():
    root = tk.Tk()
    app = DantzigGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()