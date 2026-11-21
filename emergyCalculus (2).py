
import numpy as np
import matplotlib.pyplot as plt
from scipy import integrate

def power_function(t):
    """
    A function representing power over time.
    This could represent, for example, the power output of a solar panel throughout the day.
    """
    return 1000 * np.sin(np.pi * t / 12)**2  # Peak power of 1000W at noon

def energy_integral(t1, t2):
    """
    Calculate the energy (in Joules) produced between times t1 and t2 (in hours)
    by integrating the power function.
    """
    energy, _ = integrate.quad(power_function, t1, t2)
    return energy

def plot_power_and_energy():
    t = np.linspace(0, 24, 1000)
    power = power_function(t)
    energy = np.array([energy_integral(0, ti) for ti in t])

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10))

    ax1.plot(t, power)
    ax1.set_title('Power Output Over Time')
    ax1.set_xlabel('Time (hours)')
    ax1.set_ylabel('Power (Watts)')

    ax2.plot(t, energy / 3600000)  # Convert J to kWh
    ax2.set_title('Cumulative Energy Production')
    ax2.set_xlabel('Time (hours)')
    ax2.set_ylabel('Energy (kWh)')

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    plot_power_and_energy()
   
    # Calculate and print energy for a specific time interval
    t1, t2 = 6, 18  # Example: calculate energy from 6 AM to 6 PM
    energy = energy_integral(t1, t2)
    print(f"Energy produced between {t1} and {t2} hours: {energy/3600000:.2f} kWh") 
