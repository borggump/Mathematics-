import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import odeint
from mpl_toolkits.mplot3d import Axes3D

class LagrangianSolver:
    def __init__(self):
        self.g = 9.81  # Gravitational acceleration

    def simple_pendulum(self, theta0, omega0, length, time):
        """
        Problem 1: Simple Pendulum
        L = T - V = (1/2)mL²θ'² - mgL(1-cosθ)
        """
        def derivatives(state, t, L):
            theta, omega = state
            dtheta = omega
            domega = -(self.g/L) * np.sin(theta)
            return [dtheta, domega]

        initial_state = [theta0, omega0]
        t = np.linspace(0, time, 1000)
        solution = odeint(derivatives, initial_state, t, args=(length,))
        
        return t, solution

    def double_pendulum(self, initial_conditions, time):
        """
        Problem 2: Double Pendulum
        Complex system with coupled equations of motion
        """
        def derivatives(state, t, L1, L2, m1, m2):
            theta1, omega1, theta2, omega2 = state
            
            # Complex equations of motion for double pendulum
            c = np.cos(theta1 - theta2)
            s = np.sin(theta1 - theta2)
            
            theta1_dd = (-self.g*(2*m1 + m2)*np.sin(theta1) - m2*self.g*np.sin(theta1 - 2*theta2)
                        - 2*s*m2*(omega2**2*L2 + omega1**2*L1*c)) / (L1*(2*m1 + m2 - m2*np.cos(2*(theta1 - theta2))))
            
            theta2_dd = (2*s*(omega1**2*L1*(m1 + m2) + self.g*(m1 + m2)*np.cos(theta1)
                        + omega2**2*L2*m2*np.cos(theta1 - theta2))) / (L2*(2*m1 + m2 - m2*np.cos(2*(theta1 - theta2))))
            
            return [omega1, theta1_dd, omega2, theta2_dd]

        t = np.linspace(0, time, 1000)
        solution = odeint(derivatives, initial_conditions, t, args=(1.0, 1.0, 1.0, 1.0))
        return t, solution

    def spring_mass(self, x0, v0, k, m, time):
        """
        Problem 3: Spring-Mass System
        L = T - V = (1/2)mx'² - (1/2)kx²
        """
        def derivatives(state, t, k, m):
            x, v = state
            dx = v
            dv = -(k/m) * x
            return [dx, dv]

        initial_state = [x0, v0]
        t = np.linspace(0, time, 1000)
        solution = odeint(derivatives, initial_state, t, args=(k, m))
        return t, solution

    def coupled_oscillators(self, initial_conditions, k1, k2, m1, m2, time):
        """
        Problem 4: Coupled Oscillators
        System of two masses connected by springs
        """
        def derivatives(state, t, k1, k2, m1, m2):
            x1, v1, x2, v2 = state
            dx1 = v1
            dv1 = (-k1*x1 + k2*(x2-x1))/m1
            dx2 = v2
            dv2 = (-k2*(x2-x1))/m2
            return [dx1, dv1, dx2, dv2]

        t = np.linspace(0, time, 1000)
        solution = odeint(derivatives, initial_conditions, t, args=(k1, k2, m1, m2))
        return t, solution

    def particle_in_em_field(self, initial_conditions, E, B, q, m, time):
        """
        Problem 5: Charged Particle in EM Field
        L = (1/2)mv² + qv·A - qφ
        """
        def derivatives(state, t, E, B, q, m):
            x, vx, y, vy, z, vz = state
            # Lorentz force: F = q(E + v×B)
            ax = (q/m)*(E[0] + vy*B[2] - vz*B[1])
            ay = (q/m)*(E[1] + vz*B[0] - vx*B[2])
            az = (q/m)*(E[2] + vx*B[1] - vy*B[0])
            return [vx, ax, vy, ay, vz, az]

        t = np.linspace(0, time, 1000)
        solution = odeint(derivatives, initial_conditions, t, args=(E, B, q, m))
        return t, solution

    def spherical_pendulum(self, initial_conditions, length, time):
        """
        Problem 6: Spherical Pendulum
        Motion in 3D with two degrees of freedom
        """
        def derivatives(state, t, L):
            theta, omega_theta, phi, omega_phi = state
            dtheta = omega_theta
            dphi = omega_phi
            domega_theta = (L*omega_phi**2*np.sin(theta)*np.cos(theta) - self.g*np.sin(theta))/L
            domega_phi = -2*omega_theta*omega_phi/np.tan(theta)
            return [dtheta, domega_theta, dphi, domega_phi]

        t = np.linspace(0, time, 1000)
        solution = odeint(derivatives, initial_conditions, t, args=(length,))
        return t, solution

    def rigid_body_rotation(self, initial_conditions, I1, I2, I3, time):
        """
        Problem 7: Rigid Body Rotation
        Euler equations for rigid body motion
        """
        def derivatives(state, t, I1, I2, I3):
            omega1, omega2, omega3 = state
            domega1 = ((I2 - I3)*omega2*omega3)/I1
            domega2 = ((I3 - I1)*omega3*omega1)/I2
            domega3 = ((I1 - I2)*omega1*omega2)/I3
            return [domega1, domega2, domega3]

        t = np.linspace(0, time, 1000)
        solution = odeint(derivatives, initial_conditions, t, args=(I1, I2, I3))
        return t, solution

    def particle_in_gravity_well(self, initial_conditions, time):
        """
        Problem 8: Particle in Gravitational Well
        Central force motion
        """
        def derivatives(state, t):
            r, v_r, theta, omega = state
            dr = v_r
            dtheta = omega
            dv_r = r*omega**2 - self.g  # Effective potential includes centrifugal term
            domega = -2*v_r*omega/r     # Angular momentum conservation
            return [dr, dv_r, dtheta, domega]

        t = np.linspace(0, time, 1000)
        solution = odeint(derivatives, initial_conditions, t)
        return t, solution

    def damped_oscillator(self, initial_conditions, k, m, gamma, time):
        """
        Problem 9: Damped Oscillator
        Including dissipative forces
        """
        def derivatives(state, t, k, m, gamma):
            x, v = state
            dx = v
            dv = -(k/m)*x - (gamma/m)*v
            return [dx, dv]

        t = np.linspace(0, time, 1000)
        solution = odeint(derivatives, initial_conditions, t, args=(k, m, gamma))
        return t, solution

    def driven_oscillator(self, initial_conditions, k, m, F0, omega_d, time):
        """
        Problem 10: Driven Oscillator
        Forced oscillations with external driving force
        """
        def derivatives(state, t, k, m, F0, omega_d):
            x, v = state
            dx = v
            dv = -(k/m)*x + (F0/m)*np.sin(omega_d*t)
            return [dx, dv]

        t = np.linspace(0, time, 1000)
        solution = odeint(derivatives, initial_conditions, t, args=(k, m, F0, omega_d))
        return t, solution

    def solve_and_plot_all(self):
        """Solve all problems and display results"""
        plt.figure(figsize=(20, 25))
        
        # 1. Simple Pendulum
        t, sol = self.simple_pendulum(np.pi/4, 0, 1.0, 10)
        plt.subplot(5, 2, 1)
        plt.plot(t, sol[:, 0])
        plt.title('Simple Pendulum')
        plt.xlabel('Time')
        plt.ylabel('Angle')

        # 2. Double Pendulum
        t, sol = self.double_pendulum([np.pi/4, 0, np.pi/6, 0], 10)
        plt.subplot(5, 2, 2)
        plt.plot(t, sol[:, 0], label='θ1')
        plt.plot(t, sol[:, 2], label='θ2')
        plt.title('Double Pendulum')
        plt.legend()

        # 3. Spring-Mass System
        t, sol = self.spring_mass(1.0, 0, 1.0, 1.0, 10)
        plt.subplot(5, 2, 3)
        plt.plot(t, sol[:, 0])
        plt.title('Spring-Mass System')

        # 4. Coupled Oscillators
        t, sol = self.coupled_oscillators([1.0, 0, -1.0, 0], 1.0, 1.0, 1.0, 1.0, 10)
        plt.subplot(5, 2, 4)
        plt.plot(t, sol[:, 0], label='m1')
        plt.plot(t, sol[:, 2], label='m2')
        plt.title('Coupled Oscillators')
        plt.legend()

        # 5. Particle in EM Field
        E = [0, 0, 1]
        B = [0, 1, 0]
        t, sol = self.particle_in_em_field([0, 1, 0, 1, 0, 1], E, B, 1, 1, 10)
        plt.subplot(5, 2, 5)
        plt.plot(sol[:, 0], sol[:, 2])
        plt.title('Particle in EM Field')

        # 6. Spherical Pendulum
        t, sol = self.spherical_pendulum([np.pi/4, 0, 0, 1], 1.0, 10)
        plt.subplot(5, 2, 6)
        plt.plot(t, sol[:, 0])
        plt.title('Spherical Pendulum')

        # 7. Rigid Body Rotation
        t, sol = self.rigid_body_rotation([1.0, 0.1, 0.1], 1.0, 2.0, 3.0, 10)
        plt.subplot(5, 2, 7)
        plt.plot(t, sol)
        plt.title('Rigid Body Rotation')

        # 8. Particle in Gravity Well
        t, sol = self.particle_in_gravity_well([1.0, 0, 0, 1], 10)
        plt.subplot(5, 2, 8)
        plt.plot(sol[:, 0]*np.cos(sol[:, 2]), sol[:, 0]*np.sin(sol[:, 2]))
        plt.title('Particle in Gravity Well')

        # 9. Damped Oscillator
        t, sol = self.damped_oscillator([1.0, 0], 1.0, 1.0, 0.1, 10)
        plt.subplot(5, 2, 9)
        plt.plot(t, sol[:, 0])
        plt.title('Damped Oscillator')

        # 10. Driven Oscillator
        t, sol = self.driven_oscillator([0, 0], 1.0, 1.0, 0.5, 1.0, 10)
        plt.subplot(5, 2, 10)
        plt.plot(t, sol[:, 0])
        plt.title('Driven Oscillator')

        plt.tight_layout()
        plt.show()

        # Print analytical results for each system
        print("\nAnalytical Results:")
        for i, problem in enumerate([
            "Simple Pendulum", "Double Pendulum", "Spring-Mass",
            "Coupled Oscillators", "Particle in EM Field", "Spherical Pendulum",
            "Rigid Body", "Gravity Well", "Damped Oscillator", "Driven Oscillator"
        ], 1):
            print(f"\n{i}. {problem}:")
            if i == 1:
                print(f"   Natural frequency: {np.sqrt(self.g/1.0):.2f} rad/s")
            elif i == 3:
                print(f"   Natural frequency: {np.sqrt(1.0/1.0):.2f} rad/s")
            elif i == 9:
                print(f"   Decay time: {2.0/0.1:.2f} s")
            elif i == 10:
                print(f"   Resonant frequency: {np.sqrt(1.0/1.0):.2f} rad/s")

if __name__ == "__main__":
    solver = LagrangianSolver()
    solver.solve_and_plot_all()