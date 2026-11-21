#!/usr/bin/env python3
"""
Holographic Quantum Gravity Visualizer — Terminal Version
Pure Python with ASCII graphics and real-time terminal output.
Perfect for PyDroid3 terminal or any command line.

No GUI dependencies—works in any terminal!
"""

import math
import numpy as np
import sys
import os
from time import sleep

# Color codes for terminal
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    YELLOW = '\033[93m'
    GREEN = '\033[92m'
    WHITE = '\033[97m'
    BLUE = '\033[94m'

# ========== DATA MODEL ==========
class ExperimentState:
    """Holds the experiment parameters and computed values."""
    def __init__(self):
        self.theta_deg = 50
        self.magic = 0.0
        self.mode = 'flm'
        self.update()
    
    def update(self):
        """Recompute entropies based on current theta and magic."""
        self.theta_rad = (self.theta_deg / 100.0) * (math.pi / 4)
        
        # Boundary entropy: rises from 2 to 3 as theta increases
        self.S_A = 2.0 + np.power(np.sin(2 * self.theta_rad), 2)
        
        # Bulk entropy: rises from 0 to 1
        self.S_a = np.power(np.sin(2 * self.theta_rad), 2)
        
        # Proto-area entropy: depends on mode
        if self.mode == 'flm':
            self.S_PA = self.S_A - self.S_a  # ≡ 2.0 (flat)
        elif self.mode == 'magic':
            self.S_PA = (self.S_A - self.S_a) + self.magic * 0.9 * np.power(np.sin(2 * self.theta_rad), 2)
        else:  # worm
            self.S_PA = (self.S_A - self.S_a) - (0.4 + self.magic * 0.9) * np.power(np.sin(2 * self.theta_rad), 2)
        
        self.S_PA = max(0, min(3.5, self.S_PA))
    
    def theta_label(self):
        frac = self.theta_deg / 100.0
        if abs(frac - 0) < 0.03:
            return "0"
        elif abs(frac - 0.5) < 0.03:
            return "π/8"
        elif abs(frac - 1.0) < 0.03:
            return "π/4"
        else:
            return f"{frac * 45:.0f}°"

# ========== ASCII GRAPHICS ==========
def plot_ascii(state):
    """Draw a simple ASCII plot of the entropy curves."""
    width, height = 60, 15
    
    # Create grid
    grid = [[' ' for _ in range(width)] for _ in range(height)]
    
    # Compute curves
    theta_range = np.linspace(0, math.pi/4, width-2)
    S_A_curve = 2.0 + np.power(np.sin(2 * theta_range), 2)
    S_a_curve = np.power(np.sin(2 * theta_range), 2)
    
    if state.mode == 'flm':
        S_PA_curve = S_A_curve - S_a_curve
    elif state.mode == 'magic':
        S_PA_curve = (S_A_curve - S_a_curve) + state.magic * 0.9 * np.power(np.sin(2 * theta_range), 2)
    else:
        S_PA_curve = (S_A_curve - S_a_curve) - (0.4 + state.magic * 0.9) * np.power(np.sin(2 * theta_range), 2)
    
    S_PA_curve = np.clip(S_PA_curve, 0, 3.4)
    
    # Plot S_PA (main observable)
    for i, y_val in enumerate(S_PA_curve):
        if i < width - 2:
            row = int((3.4 - y_val) / 3.4 * (height - 2)) + 1
            if 0 <= row < height:
                grid[row][i+1] = '█'
    
    # Plot current theta marker
    theta_idx = int((state.theta_rad / (math.pi/4)) * (width - 2)) + 1
    if 0 <= theta_idx < width:
        grid[1][theta_idx] = '↓'
    
    # Draw axes and labels
    print(f"\n{Colors.CYAN}═══ ENTROPY PLOT ({'FLM' if state.mode=='flm' else 'Magic' if state.mode=='magic' else 'Wormhole'}) ═══{Colors.RESET}")
    
    # Y-axis labels and plot
    for row_idx in range(height):
        if row_idx == 0:
            print(f"{Colors.YELLOW}3.4{Colors.RESET} │ " + "".join(grid[row_idx]))
        elif row_idx == height // 2:
            print(f"{Colors.YELLOW}1.7{Colors.RESET} │ " + "".join(grid[row_idx]))
        elif row_idx == height - 1:
            print(f"{Colors.YELLOW}0.0{Colors.RESET} │ " + "".join(grid[row_idx]))
        else:
            print("    │ " + "".join(grid[row_idx]))
    
    # X-axis
    print("    └" + "─" * (width) + "─")
    print(f"     0        π/8       π/4")
    print(f"\n{Colors.MAGENTA}█{Colors.RESET} = S_PA   {Colors.YELLOW}↓{Colors.RESET} = current θ")

def print_status(state):
    """Print current state in a readable format."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}╔═══════════════════════════════════════╗{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}║  HOLOGRAPHIC QUANTUM GRAVITY          ║{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}╚═══════════════════════════════════════╝{Colors.RESET}")
    
    # Mode indicator
    mode_str = f"{Colors.CYAN}FLM Test{Colors.RESET}" if state.mode == 'flm' else \
               f"{Colors.MAGENTA}Magic Injection{Colors.RESET}" if state.mode == 'magic' else \
               f"{Colors.BLUE}Wormhole ER=EPR{Colors.RESET}"
    print(f"\nMode: {mode_str}")
    
    # Parameters
    print(f"\nParameters:")
    print(f"  θ (theta):  {state.theta_deg}% = {state.theta_label()} rad")
    print(f"  M (magic):  {state.magic:.2f} (0.0 to 1.0)")
    
    # Entropy values
    print(f"\n{Colors.BOLD}Entropy Measurements:{Colors.RESET}")
    print(f"  {Colors.MAGENTA}S_PA{Colors.RESET} (proto-area): {state.S_PA:.3f}")
    print(f"  {Colors.YELLOW}S(ρ_A){Colors.RESET} (boundary):  {state.S_A:.3f}")
    print(f"  {Colors.CYAN}S(ρ_a){Colors.RESET} (bulk):      {state.S_a:.3f}")
    
    # Expected behavior
    print(f"\n{Colors.BOLD}Expected Behavior in {mode_str}:{Colors.RESET}")
    if state.mode == 'flm':
        slope = 0
        desc = "S_PA stays FLAT (rigid background)"
    elif state.mode == 'magic':
        slope = 0.9 * state.magic
        desc = "S_PA RISES (geometry responds to matter)"
    else:
        slope = -0.9 * state.magic
        desc = "S_PA SHRINKS (wormhole neck shortens)"
    
    print(f"  {desc}")
    print(f"  Trend slope: {slope:.3f}")

def print_help():
    """Print help message."""
    print(f"""
{Colors.BOLD}CONTROLS:{Colors.RESET}
  t [0-100]     Set theta (bulk entanglement), 0-100%
  m [0-1]       Set magic (non-stabilizer resource), 0.0-1.0
  1/2/3         Switch mode: FLM / Magic / Wormhole
  plot          Show entropy curve plot
  info          Show physics explanation
  help          Show this help
  quit/exit     Exit program

{Colors.BOLD}EXAMPLES:{Colors.RESET}
  t 75          Set theta to 75% (≈ 3π/16 radians)
  m 0.5         Set magic to 0.5
  1             Switch to FLM mode
  plot          Show live plot
""")

def print_physics_info(state):
    """Print physics explanation."""
    print(f"""
{Colors.BOLD}{Colors.CYAN}╔════════════════════════════════════════════╗{Colors.RESET}
{Colors.BOLD}{Colors.CYAN}║         PHYSICS EXPLANATION                ║{Colors.RESET}
{Colors.BOLD}{Colors.CYAN}╚════════════════════════════════════════════╝{Colors.RESET}

{Colors.BOLD}THE FLM FORMULA:{Colors.RESET}
  S_A = Area(γ_A) / 4G_N + S_a

  Left: Boundary entropy (what we measure)
  Right: Geometric area in bulk + bulk matter entropy

{Colors.BOLD}THE THREE TESTS:{Colors.RESET}

1️⃣  {Colors.CYAN}FLM TEST{Colors.RESET}
    Pure Clifford code (rigid background)
    Expected: S_PA stays FLAT as θ rises
    ✓ Confirms: Geometry is fixed
    Magic slider: DISABLED

2️⃣  {Colors.MAGENTA}MAGIC INJECTION{Colors.RESET}
    Non-stabilizer gates (over/under-rotations λᵢ)
    Expected: S_PA GROWS with θ
    ✓ Shows: Backreaction! Geometry responds to matter
    Magic slider: ACTIVE

3️⃣  {Colors.BLUE}WORMHOLE{Colors.RESET}
    Two entangled codes (ER=EPR conjecture)
    Expected: S_PA SHRINKS as inter-code entanglement rises
    Interpretation: Wormhole neck shortens
    Magic slider: ACTIVE

{Colors.BOLD}WHAT IT ALL MEANS:{Colors.RESET}

  Spacetime might emerge from entanglement.
  
  In this toy model:
  • Geometry arises from quantum information
  • Matter (via magic) can warp that geometry
  • Entanglement creates geometric bridges
  
  This suggests the universe might work similarly! 🌌

{Colors.BOLD}CAVEATS:{Colors.RESET}

  ⚠️  Not real spacetime (only ~8-16 qubits)
  ⚠️  Anti-de Sitter only (negative cosmological constant)
  ⚠️  Wormhole case is exploratory (no known gravitational dual)
  ⚠️  Paper is preprint (arXiv:2607.12047, July 2026)
""")

# ========== INTERACTIVE LOOP ==========
def main():
    """Main interactive loop."""
    state = ExperimentState()
    
    print(f"\n{Colors.BOLD}{Colors.GREEN}═══════════════════════════════════════════{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.GREEN}  Holographic Quantum Gravity Visualizer{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.GREEN}  Terminal Interactive Edition{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.GREEN}═══════════════════════════════════════════{Colors.RESET}")
    print(f"\nPaper: Biswas et al., arXiv:2607.12047 (July 2026)")
    print(f"Hardware: IonQ Forte trapped-ion quantum computer\n")
    print(f"Type {Colors.YELLOW}help{Colors.RESET} for commands, {Colors.YELLOW}info{Colors.RESET} for physics explanation.\n")
    
    print_status(state)
    
    while True:
        try:
            cmd = input(f"\n{Colors.GREEN}>{Colors.RESET} ").strip().lower()
            
            if not cmd:
                continue
            
            parts = cmd.split()
            action = parts[0]
            
            # Parse commands
            if action == 'quit' or action == 'exit':
                print(f"\n{Colors.CYAN}Goodbye! 🌌{Colors.RESET}\n")
                break
            
            elif action == 'help':
                print_help()
            
            elif action == 'info':
                print_physics_info(state)
            
            elif action == 'plot':
                state.update()
                plot_ascii(state)
            
            elif action == 'status':
                print_status(state)
            
            elif action == 't' or action == 'theta':
                if len(parts) > 1:
                    try:
                        val = float(parts[1])
                        state.theta_deg = max(0, min(100, val))
                        state.update()
                        print(f"{Colors.YELLOW}θ set to {state.theta_deg}% ({state.theta_label()}){Colors.RESET}")
                        print_status(state)
                    except ValueError:
                        print(f"{Colors.RED}Invalid value. Use: t 0-100{Colors.RESET}")
                else:
                    print(f"Current θ: {state.theta_deg}% ({state.theta_label()})")
            
            elif action == 'm' or action == 'magic':
                if len(parts) > 1:
                    try:
                        val = float(parts[1])
                        if state.mode == 'flm':
                            print(f"{Colors.YELLOW}Magic disabled in FLM mode{Colors.RESET}")
                        else:
                            state.magic = max(0, min(1.0, val))
                            state.update()
                            print(f"{Colors.MAGENTA}M set to {state.magic:.2f}{Colors.RESET}")
                            print_status(state)
                    except ValueError:
                        print(f"{Colors.RED}Invalid value. Use: m 0.0-1.0{Colors.RESET}")
                else:
                    print(f"Current M: {state.magic:.2f}")
            
            elif action == '1':
                state.mode = 'flm'
                state.magic = 0.0
                state.update()
                print(f"{Colors.CYAN}Mode switched to FLM Test{Colors.RESET}")
                print_status(state)
            
            elif action == '2':
                state.mode = 'magic'
                state.update()
                print(f"{Colors.MAGENTA}Mode switched to Magic Injection{Colors.RESET}")
                print_status(state)
            
            elif action == '3':
                state.mode = 'worm'
                state.update()
                print(f"{Colors.BLUE}Mode switched to Wormhole{Colors.RESET}")
                print_status(state)
            
            else:
                print(f"{Colors.RED}Unknown command. Type 'help' for available commands.{Colors.RESET}")
        
        except KeyboardInterrupt:
            print(f"\n\n{Colors.CYAN}Interrupted. Goodbye! 🌌{Colors.RESET}\n")
            break
        except Exception as e:
            print(f"{Colors.RED}Error: {e}{Colors.RESET}")

if __name__ == '__main__':
    main()
