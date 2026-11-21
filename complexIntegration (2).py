
import cmath
import sympy as sp

def complex_integral_solver(integral_type, *args):
    z = sp.Symbol('z')
   
    def rational_function(a, b, c, d):
        return sp.integrate((a*z + b) / (c*z + d), z)
   
    def exponential(a):
        return sp.integrate(sp.exp(a*z), z)
   
    def logarithmic(a):
        return sp.integrate(sp.log(a*z), z)
   
    def trigonometric_sin(a):
        return sp.integrate(sp.sin(a*z), z)
   
    def trigonometric_cos(a):
        return sp.integrate(sp.cos(a*z), z)
   
    def power_function(n):
        return sp.integrate(z**n, z)
   
    def inverse_trigonometric_arctan():
        return sp.integrate(sp.atan(z), z)
   
    def hyperbolic_sinh(a):
        return sp.integrate(sp.sinh(a*z), z)
   
    def hyperbolic_cosh(a):
        return sp.integrate(sp.cosh(a*z), z)
   
    def complex_exponential(a, b):
        return sp.integrate(sp.exp(a*z + b), z)

    integral_functions = {
        'rational': rational_function,
        'exponential': exponential,
        'logarithmic': logarithmic,
        'sin': trigonometric_sin,
        'cos': trigonometric_cos,
        'power': power_function,
        'arctan': inverse_trigonometric_arctan,
        'sinh': hyperbolic_sinh,
        'cosh': hyperbolic_cosh,
        'complex_exp': complex_exponential
    }
   
    if integral_type in integral_functions:
        result = integral_functions[integral_type](*args)
        return result
    else:
        return "Integral type not supported"

# Example usage
print("1. Rational function integral:")
print(complex_integral_solver('rational', 1, 2, 3, 4))  # Integrates (z + 2) / (3z + 4)

print("\n2. Exponential integral:")
print(complex_integral_solver('exponential', 2))  # Integrates e^(2z)

print("\n3. Logarithmic integral:")
print(complex_integral_solver('logarithmic', 3))  # Integrates log(3z)

print("\n4. Sine integral:")
print(complex_integral_solver('sin', 2))  # Integrates sin(2z)

print("\n5. Cosine integral:")
print(complex_integral_solver('cos', 2))  # Integrates cos(2z)

print("\n6. Power function integral:")
print(complex_integral_solver('power', 3))  # Integrates z^3

print("\n7. Arctangent integral:")
print(complex_integral_solver('arctan'))  # Integrates arctan(z)

print("\n8. Hyperbolic sine integral:")
print(complex_integral_solver('sinh', 2))  # Integrates sinh(2z)

print("\n9. Hyperbolic cosine integral:")
print(complex_integral_solver('cosh', 2))  # Integrates cosh(2z)

print("\n10. Complex exponential integral:")
print(complex_integral_solver('complex_exp', 2, 3))  # Integrates e^(2z + 3) 
