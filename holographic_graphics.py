#!/usr/bin/env python3
"""
Holographic Quantum Gravity Visualizer — Terminal + Matplotlib Images
Real graphics saved as PNG files that you can view.
Perfect for PyDroid3!

Requirements: numpy, matplotlib
"""

import math
import numpy as np
import sys
import os
from time import sleep
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pathlib import Path

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
    RED = '\033[91m'

# Create output directory for images
OUTPUT_DIR = Path.home() / "holographic_plots"
OUTPUT_DIR.mkdir(exist_ok=True)

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

# ========== MATPLOTLIB GRAPHICS ==========
def create_entropy_plot(state):
    """Create and save a matplotlib plot of entropy curves."""
    
    # Create figure with dark background
    fig, ax = plt.subplots(figsize=(10, 6), facecolor='#0b1020', edgecolor='#26304f')
    ax.set_facecolor('#080e22')
    
    # Compute curves
    theta_range = np.linspace(0, math.pi/4, 150)
    S_A_curve = 2.0 + np.power(np.sin(2 * theta_range), 2)
    S_a_curve = np.power(np.sin(2 * theta_range), 2)
    
    if state.mode == 'flm':
        S_PA_curve = S_A_curve - S_a_curve
    elif state.mode == 'magic':
        S_PA_curve = (S_A_curve - S_a_curve) + state.magic * 0.9 * np.power(np.sin(2 * theta_range), 2)
    else:
        S_PA_curve = (S_A_curve - S_a_curve) - (0.4 + state.magic * 0.9) * np.power(np.sin(2 * theta_range), 2)
    
    S_PA_curve = np.clip(S_PA_curve, 0, 3.5)
    
    # Plot curves
    ax.plot(theta_range, S_A_curve, 'o-', color='#f2b134', linewidth=2, markersize=2, 
            label='S(ρ_A) boundary', alpha=0.8)
    ax.plot(theta_range, S_a_curve, 's-', color='#4fd6e0', linewidth=2, markersize=2, 
            label='S(ρ_a) bulk', alpha=0.8)
    ax.plot(theta_range, S_PA_curve, 'D-', color='#8a7bff', linewidth=3.5, markersize=4, 
            label='S_PA (area term)', alpha=0.95)
    
    # Mark current theta
    ax.axvline(state.theta_rad, color='#e0559b', linewidth=2, linestyle='--', alpha=0.7)
    ax.scatter([state.theta_rad], [state.S_PA], color='#8a7bff', s=200, zorder=5, 
              edgecolors='#0b1020', linewidths=2, marker='o')
    
    # Styling
    ax.set_xlim(0, math.pi/4)
    ax.set_ylim(0, 3.5)
    ax.set_xlabel('bulk entanglement angle θ (radians)', color='#9aa6c4', fontsize=11)
    ax.set_ylabel('entropy', color='#9aa6c4', fontsize=11)
    ax.set_xticks([0, math.pi/8, math.pi/4])
    ax.set_xticklabels(['0', 'π/8', 'π/4'], color='#9aa6c4')
    ax.tick_params(colors='#9aa6c4', labelsize=10)
    ax.grid(True, alpha=0.2, color='#26304f', linestyle=':')
    
    # Legend and title
    mode_name = 'FLM Test' if state.mode=='flm' else 'Magic Injection' if state.mode=='magic' else 'Wormhole'
    ax.set_title(f'Holographic Quantum Gravity — {mode_name}\narXiv:2607.12047', 
                color='#eef1f7', fontsize=13, fontweight='bold', pad=15)
    
    ax.legend(fontsize=10, loc='upper left', facecolor='#0a1530', edgecolor='#26304f', 
             labelcolor='#eef1f7', framealpha=0.9)
    
    # Spine styling
    for spine in ax.spines.values():
        spine.set_color('#26304f')
        spine.set_linewidth(1)
    
    plt.tight_layout()
    
    # Save
    filename = OUTPUT_DIR / f"entropy_plot_{state.mode}_{state.theta_deg}_{int(state.magic*100)}.png"
    plt.savefig(filename, facecolor='#0b1020', edgecolor='#26304f', dpi=100)
    plt.close()
    
    return filename

def create_diagrams(state):
    """Create and save bulk-boundary and wormhole diagrams."""
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5), facecolor='#0b1020')
    
    # ===== LEFT: Bulk-Boundary =====
    ax1.set_facecolor('#080e22')
    ax1.set_xlim(-1.3, 1.3)
    ax1.set_ylim(-1.3, 1.3)
    ax1.set_aspect('equal')
    ax1.axis('off')
    
    # Boundary circle
    boundary = plt.Circle((0, 0), 1.0, fill=False, edgecolor='#26304f', linewidth=2.5)
    ax1.add_patch(boundary)
    
    # Boundary region (amber wedge)
    theta_wedge = np.linspace(45, 135, 30) * np.pi / 180
    r = 1.0
    for i in range(len(theta_wedge)-1):
        x1 = r * np.cos(theta_wedge[i])
        y1 = r * np.sin(theta_wedge[i])
        x2 = r * np.cos(theta_wedge[i+1])
        y2 = r * np.sin(theta_wedge[i+1])
        ax1.plot([x1, x2], [y1, y2], color='#f2b134', linewidth=3.5)
    
    # Minimal surface (violet)
    r_min = 0.5
    for i in range(len(theta_wedge)-1):
        x1 = r_min * np.cos(theta_wedge[i])
        y1 = r_min * np.sin(theta_wedge[i])
        x2 = r_min * np.cos(theta_wedge[i+1])
        y2 = r_min * np.sin(theta_wedge[i+1])
        ax1.plot([x1, x2], [y1, y2], color='#8a7bff', linewidth=2.5, linestyle='--')
    
    # Bulk matter
    matter = plt.Circle((0.25, 0), 0.12, fill=True, facecolor='#4fd6e0', alpha=0.8, edgecolor='none')
    ax1.add_patch(matter)
    
    ax1.text(0.9, 0.7, 'A (boundary)', fontsize=10, color='#f2b134', fontweight='bold')
    ax1.text(0.35, -0.3, 'S_a', fontsize=10, color='#4fd6e0', fontweight='bold')
    ax1.text(-0.1, 0.35, 'γ_A', fontsize=10, color='#8a7bff', fontweight='bold')
    ax1.set_title('Bulk-Boundary Correspondence', color='#eef1f7', fontweight='bold', fontsize=12, pad=10)
    
    # ===== RIGHT: Wormhole =====
    ax2.set_facecolor('#080e22')
    ax2.set_xlim(-0.5, 2.5)
    ax2.set_ylim(-1.2, 1.2)
    ax2.set_aspect('equal')
    ax2.axis('off')
    
    # Scenario 1: Long neck (left side)
    c1 = 0.3
    for y_off in [-0.4, 0.4]:
        ellipse1 = patches.Ellipse((c1, y_off), 0.3, 0.5, fill=False, 
                                   edgecolor='#f2b134', linewidth=2.5)
        ax2.add_patch(ellipse1)
        ax2.plot([c1+0.15, 1.35], [y_off-0.2, y_off-0.2], color='#8a7bff', linewidth=3)
        ax2.plot([c1+0.15, 1.35], [y_off+0.2, y_off+0.2], color='#8a7bff', linewidth=3)
    
    ax2.text(0.2, -1.0, 'low θ\nlong neck\nlarge S_PA', fontsize=9, color='#9aa6c4', ha='center')
    
    # Scenario 2: Short neck (right side)
    c2 = 2.2
    for y_off in [-0.4, 0.4]:
        ellipse2 = patches.Ellipse((c2, y_off), 0.3, 0.5, fill=False, 
                                   edgecolor='#f2b134', linewidth=2.5)
        ax2.add_patch(ellipse2)
        ax2.plot([1.65, c2-0.15], [y_off-0.1, y_off-0.1], color='#8a7bff', linewidth=3)
        ax2.plot([1.65, c2-0.15], [y_off+0.1, y_off+0.1], color='#8a7bff', linewidth=3)
    
    ax2.text(2.3, -1.0, 'high θ\nshort neck\nsmall S_PA', fontsize=9, color='#9aa6c4', ha='center')
    
    ax2.arrow(0.7, 1.0, 0.5, 0, head_width=0.1, head_length=0.1, 
             fc='#e0559b', ec='#e0559b', linewidth=2)
    ax2.text(0.95, 1.15, 'entanglement ↑', fontsize=9, color='#e0559b', ha='center', fontweight='bold')
    
    ax2.set_title('Wormhole Intuition (ER=EPR)', color='#eef1f7', fontweight='bold', fontsize=12, pad=10)
    
    # Save
    filename = OUTPUT_DIR / "diagrams.png"
    plt.savefig(filename, facecolor='#0b1020', dpi=100)
    plt.close()
    
    return filename

# ========== TERMINAL UI ==========
def print_status(state):
    """Print current state in a readable format."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}╔════════════════════════════════════════╗{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}║  HOLOGRAPHIC QUANTUM GRAVITY           ║{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}╚════════════════════════════════════════╝{Colors.RESET}")
    
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
  plot          Generate and show entropy curve plot
  diagrams      Generate and show bulk-boundary & wormhole diagrams
  info          Show physics explanation
  help          Show this help
  quit/exit     Exit program

{Colors.BOLD}EXAMPLES:{Colors.RESET}
  t 75          Set theta to 75%
  m 0.5         Set magic to 0.5
  1             Switch to FLM mode
  plot          Generate plot PNG file
  diagrams      Generate diagram PNG file
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

2️⃣  {Colors.MAGENTA}MAGIC INJECTION{Colors.RESET}
    Non-stabilizer gates (over/under-rotations)
    Expected: S_PA GROWS with θ
    ✓ Shows: Backreaction! Geometry responds to matter

3️⃣  {Colors.BLUE}WORMHOLE{Colors.RESET}
    Two entangled codes (ER=EPR conjecture)
    Expected: S_PA SHRINKS as entanglement rises
    Interpretation: Wormhole neck shortens

{Colors.BOLD}PLOTS ARE SAVED TO:{Colors.RESET}
  {Colors.GREEN}{OUTPUT_DIR}{Colors.RESET}

  You can open them on your phone in any image viewer!
""")

# ========== MAIN LOOP ==========
def main():
    """Main interactive loop."""
    state = ExperimentState()
    
    print(f"\n{Colors.BOLD}{Colors.GREEN}═══════════════════════════════════════════{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.GREEN}  Holographic Quantum Gravity Visualizer{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.GREEN}  Terminal Edition with Image Output{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.GREEN}═══════════════════════════════════════════{Colors.RESET}")
    print(f"\nPaper: Biswas et al., arXiv:2607.12047 (July 2026)")
    print(f"Hardware: IonQ Forte trapped-ion quantum computer")
    print(f"\n{Colors.GREEN}Plots saved to:{Colors.RESET} {OUTPUT_DIR}")
    print(f"\nType {Colors.YELLOW}help{Colors.RESET} for commands, {Colors.YELLOW}plot{Colors.RESET} to generate graphics.\n")
    
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
                print(f"{Colors.YELLOW}Generating entropy plot...{Colors.RESET}")
                filename = create_entropy_plot(state)
                print(f"{Colors.GREEN}✓ Plot saved:{Colors.RESET} {filename}")
            
            elif action == 'diagrams':
                print(f"{Colors.YELLOW}Generating diagrams...{Colors.RESET}")
                filename = create_diagrams(state)
                print(f"{Colors.GREEN}✓ Diagrams saved:{Colors.RESET} {filename}")
            
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
