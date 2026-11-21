
import sympy as sp

def integrate_function(func_str, var='x'):
    x = sp.Symbol(var)
    func = sp.sympify(func_str)
    return sp.integrate(func, x)

def solve_common_integrals():
    x = sp.Symbol('x')
   
    problems = [
        ("1. Polynomial", "x**3 + 2*x**2 - 5*x + 3"),
        ("2. Exponential", "exp(x)"),
        ("3. Trigonometric (sin)", "sin(x)"),
        ("4. Trigonometric (cos)", "cos(x)"),
        ("5. Logarithmic", "log(x)"),
        ("6. Rational function", "1 / (x**2 + 1)"),
        ("7. Square root", "sqrt(x)"),
        ("8. Product of trig and polynomial", "x * sin(x)"),
        ("9. Exponential with coefficient", "3 * exp(2*x)"),
        ("10. Inverse trigonometric", "1 / sqrt(1 - x**2)")
    ]
   
    for name, func_str in problems:
        print(f"\n{name}:")
        print(f"Integrand: {func_str}")
        result = integrate_function(func_str)
        print(f"Integral: {result}")
        print(f"Verification: d/dx({result}) = {sp.diff(result, x).simplify()}")

if __name__ == "__main__":
    solve_common_integrals() 
