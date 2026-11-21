import numpy as np
import matplotlib.pyplot as plt
from sympy import symbols, solve, sympify, Poly
from sympy.abc import x
import math

class PolynomialSolver:
    """
    A class demonstrating concepts related to polynomial solving using power series,
    inspired by the work of Wildberger and Rubine.
    This is a conceptual demonstration, not the actual Geode algorithm.
    """
    
    def __init__(self):
        """Initialize the solver."""
        self.catalan_cache = {}  # Cache for Catalan numbers
    
    def catalan(self, n):
        """
        Calculate the nth Catalan number.
        Catalan numbers are a sequence of positive integers that appear in various counting problems.
        """
        if n in self.catalan_cache:
            return self.catalan_cache[n]
        
        if n == 0:
            result = 1
        else:
            result = 0
            for i in range(n):
                result += self.catalan(i) * self.catalan(n-i-1)
        
        self.catalan_cache[n] = result
        return result
    
    def power_series_coefficients(self, polynomial_expr, terms=10):
        """
        Generate power series coefficients for approximating a solution to a polynomial.
        This is a simplified approach - not the exact Geode method.
        """
        # Convert string expression to sympy polynomial
        if isinstance(polynomial_expr, str):
            poly = Poly(sympify(polynomial_expr), x)
        else:
            poly = Poly(polynomial_expr, x)
        
        coeffs = poly.all_coeffs()
        
        # For demonstration purposes, we'll use a recurrence relation inspired by Catalan numbers
        # to generate a power series approximation
        result_coeffs = [1]  # First coefficient
        
        for n in range(1, terms):
            next_coeff = 0
            for i in range(n):
                cat_factor = self.catalan(i)
                # Create a combination using polynomial coefficients and Catalan numbers
                coeff_index = min(i, len(coeffs) - 1)
                next_coeff += cat_factor * result_coeffs[n-i-1] * ((-1)**i) * coeffs[coeff_index]
            
            result_coeffs.append(next_coeff / n)
        
        return result_coeffs
    
    def evaluate_power_series(self, coeffs, x_val):
        """Evaluate the power series at a specific x value."""
        result = 0
        for i, coeff in enumerate(coeffs):
            result += coeff * (x_val ** i)
        return result
    
    def find_roots_power_series(self, polynomial_expr, x_min=-5, x_max=5, num_points=1000, threshold=1e-10):
        """
        Find approximate roots of a polynomial using power series.
        This evaluates the polynomial at many points and looks for zeros.
        """
        # Generate power series coefficients
        coeffs = self.power_series_coefficients(polynomial_expr, terms=20)
        
        # Evaluate at many points to find where the polynomial is close to zero
        x_vals = np.linspace(x_min, x_max, num_points)
        y_vals = [self.evaluate_power_series(coeffs, x_val) for x_val in x_vals]
        
        # Find points where the value crosses zero
        roots = []
        for i in range(1, len(y_vals)):
            if y_vals[i-1] * y_vals[i] <= 0:  # Sign change indicates a root
                # Linear interpolation for better precision
                x_root = x_vals[i-1] - y_vals[i-1] * (x_vals[i] - x_vals[i-1]) / (y_vals[i] - y_vals[i-1])
                roots.append(x_root)
        
        # For very small values that might be zeros
        for i in range(len(y_vals)):
            if abs(y_vals[i]) < threshold and (not roots or min(abs(x_vals[i] - r) for r in roots) > 0.1):
                roots.append(x_vals[i])
        
        return roots
    
    def compare_with_exact_solutions(self, polynomial_expr, our_roots):
        """Compare our approximate solutions with SymPy's exact solutions."""
        if isinstance(polynomial_expr, str):
            expr = sympify(polynomial_expr)
        else:
            expr = polynomial_expr
            
        exact_roots = solve(expr, x)
        exact_roots_float = [float(root) for root in exact_roots if root.is_real]
        
        print("Our approximate roots:", [round(root, 6) for root in our_roots])
        print("Exact roots:", [round(root, 6) for root in exact_roots_float])
        
        # Match roots and calculate error
        errors = []
        for approx_root in our_roots:
            if exact_roots_float:
                closest_exact = min(exact_roots_float, key=lambda r: abs(r - approx_root))
                error = abs(approx_root - closest_exact)
                errors.append((approx_root, closest_exact, error))
        
        if errors:
            print("\nErrors:")
            for approx, exact, error in errors:
                print(f"Approximate: {approx:.6f}, Exact: {exact:.6f}, Error: {error:.6e}")
        
        return exact_roots_float, errors
    
    def visualize_polynomial(self, polynomial_expr, roots=None, x_min=-5, x_max=5):
        """Visualize the polynomial and its roots."""
        if isinstance(polynomial_expr, str):
            expr = sympify(polynomial_expr)
        else:
            expr = polynomial_expr
            
        x_vals = np.linspace(x_min, x_max, 1000)
        y_vals = [float(expr.subs(x, x_val)) for x_val in x_vals]
        
        plt.figure(figsize=(10, 6))
        plt.plot(x_vals, y_vals)
        plt.axhline(y=0, color='k', linestyle='-', alpha=0.3)
        plt.axvline(x=0, color='k', linestyle='-', alpha=0.3)
        
        if roots:
            for root in roots:
                if x_min <= root <= x_max:
                    plt.plot(root, 0, 'ro')
        
        plt.grid(True, alpha=0.3)
        plt.title(f"Polynomial: {expr}")
        plt.xlabel("x")
        plt.ylabel("P(x)")
        plt.show()

# Example usage
def main():
    solver = PolynomialSolver()
    
    print("Demonstrating Polynomial Solving using Power Series Approximation")
    print("=" * 60)
    
    # Calculate and display some Catalan numbers
    print("First 10 Catalan numbers:")
    catalan_numbers = [solver.catalan(i) for i in range(10)]
    print(catalan_numbers)
    print()
    
    # Example 1: A 5th-degree polynomial
    poly1 = "x**5 - 5*x**4 + 5*x**3 + 5*x**2 - 6*x - 1"
    print(f"Example 1: {poly1}")
    
    # Find approximate roots using our power series method
    roots1 = solver.find_roots_power_series(poly1)
    
    # Compare with exact solutions
    exact_roots1, errors1 = solver.compare_with_exact_solutions(poly1, roots1)
    
    # Visualize
    solver.visualize_polynomial(poly1, roots=exact_roots1)
    
    # Example 2: A 6th-degree polynomial
    poly2 = "x**6 - 7*x**5 + 14*x**4 - 7*x**3 - 7*x**2 + 8*x - 1"
    print(f"\nExample 2: {poly2}")
    
    # Find approximate roots
    roots2 = solver.find_roots_power_series(poly2)
    
    # Compare with exact solutions
    exact_roots2, errors2 = solver.compare_with_exact_solutions(poly2, roots2)
    
    # Visualize
    solver.visualize_polynomial(poly2, roots=exact_roots2)
    
    print("\nNote: This is a conceptual demonstration inspired by the ideas in the article,")
    print("not an implementation of the actual Geode algorithm developed by Wildberger and Rubine.")

if __name__ == "__main__":
    main()