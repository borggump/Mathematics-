import sympy as sp
from sympy import symbols, diff, integrate, limit, solve, latex
from sympy.abc import x, y, z  # Common variable names

def print_latex(expr):
    """Print the expression in LaTeX format"""
    print(f"LaTeX format: {latex(expr)}")
    print(f"Standard format: {expr}")

def calculate_derivative(expression, var=x, order=1):
    """
    Calculate the derivative of an expression
    Args:
        expression: The mathematical expression to differentiate
        var: The variable to differentiate with respect to (default: x)
        order: The order of the derivative (default: 1)
    """
    try:
        expr = sp.sympify(expression)
        result = diff(expr, var, order)
        print(f"\nDerivative of {expr} with respect to {var} (order {order}):")
        print_latex(result)
        return result
    except Exception as e:
        print(f"Error calculating derivative: {e}")
        return None

def calculate_integral(expression, var=x, lower_bound=None, upper_bound=None):
    """
    Calculate the integral of an expression
    Args:
        expression: The mathematical expression to integrate
        var: The variable to integrate with respect to (default: x)
        lower_bound: Lower bound for definite integral (optional)
        upper_bound: Upper bound for definite integral (optional)
    """
    try:
        expr = sp.sympify(expression)
        if lower_bound is not None and upper_bound is not None:
            result = integrate(expr, (var, lower_bound, upper_bound))
            print(f"\nDefinite integral of {expr} from {lower_bound} to {upper_bound}:")
        else:
            result = integrate(expr, var)
            print(f"\nIndefinite integral of {expr}:")
        print_latex(result)
        return result
    except Exception as e:
        print(f"Error calculating integral: {e}")
        return None

def calculate_limit(expression, var=x, point=0, direction='+'):
    """
    Calculate the limit of an expression
    Args:
        expression: The mathematical expression
        var: The variable (default: x)
        point: The point at which to evaluate the limit
        direction: '+' for right limit, '-' for left limit (default: '+')
    """
    try:
        expr = sp.sympify(expression)
        result = limit(expr, var, point, dir=direction)
        print(f"\nLimit of {expr} as {var} approaches {point} from {direction} direction:")
        print_latex(result)
        return result
    except Exception as e:
        print(f"Error calculating limit: {e}")
        return None

def solve_equation(equation, var=x):
    """
    Solve an equation
    Args:
        equation: The equation to solve (use '=' between left and right side)
        var: The variable to solve for (default: x)
    """
    try:
        # Split equation into left and right side if it contains '='
        if isinstance(equation, str) and '=' in equation:
            left, right = equation.split('=')
            expr = f"({left})-({right})"
        else:
            expr = equation
            
        expr = sp.sympify(expr)
        result = solve(expr, var)
        print(f"\nSolution(s) for {var} in equation {equation}:")
        print_latex(result)
        return result
    except Exception as e:
        print(f"Error solving equation: {e}")
        return None

# Example usage function
def run_examples():
    print("=== Calculus Examples ===")
    
    # Derivative example
    print("\n1. Derivative Examples:")
    calculate_derivative("x**2 + 2*x + 1")  # Simple polynomial
    calculate_derivative("sin(x)")  # Trigonometric function
    
    # Integral example
    print("\n2. Integral Examples:")
    calculate_integral("x**2")  # Indefinite integral
    calculate_integral("x**2", lower_bound=0, upper_bound=1)  # Definite integral
    
    # Limit example
    print("\n3. Limit Examples:")
    calculate_limit("sin(x)/x", point=0)  # Famous limit
    calculate_limit("1/x", point=0, direction='+')  # Right-hand limit
    
    # Equation solving example
    print("\n4. Equation Solving Example:")
    solve_equation("x**2 + 2*x + 1 = 0")  # Quadratic equation

if __name__ == "__main__":
    # Run examples
    run_examples()
    
    # Interactive mode
    print("\n=== Interactive Mode ===")
    print("Enter 'q' to quit at any prompt")
    
    while True:
        print("\nChoose operation:")
        print("1: Derivative")
        print("2: Integral")
        print("3: Limit")
        print("4: Solve Equation")
        
        choice = input("Enter choice (1-4): ")
        if choice.lower() == 'q':
            break
            
        try:
            choice = int(choice)
            if choice not in [1, 2, 3, 4]:
                print("Invalid choice. Please enter 1-4")
                continue
                
            expr = input("Enter mathematical expression: ")
            if expr.lower() == 'q':
                break
                
            if choice == 1:
                order = int(input("Enter derivative order (1-5): "))
                calculate_derivative(expr, order=order)
                
            elif choice == 2:
                use_bounds = input("Calculate definite integral? (y/n): ").lower() == 'y'
                if use_bounds:
                    lower = float(input("Enter lower bound: "))
                    upper = float(input("Enter upper bound: "))
                    calculate_integral(expr, lower_bound=lower, upper_bound=upper)
                else:
                    calculate_integral(expr)
                    
            elif choice == 3:
                point = float(input("Enter point to evaluate limit at: "))
                dir = input("Enter direction (+/-): ")
                calculate_limit(expr, point=point, direction=dir)
                
            elif choice == 4:
                solve_equation(expr)
                
        except Exception as e:
            print(f"Error: {e}")
            print("Please try again with valid input")
            