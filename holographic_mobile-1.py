#!/usr/bin/env python3
"""
Holographic Quantum Gravity Visualizer for PyDroid3
Interactive exploration of the HaPPY code experiment on IonQ.

Requires: kivy, numpy, matplotlib
Install in PyDroid3:
  pip install kivy numpy matplotlib
"""

import math
import numpy as np
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.slider import Slider
from kivy.uix.image import Image
from kivy.uix.popup import Popup
from kivy.uix.rst import RstDocument
from kivy.garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.uix.widget import Widget
from kivy.uix.relativelayout import RelativeLayout

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Wedge
import io
import base64

# ========== DEVICE CONFIG ==========
Window.size = (420, 900)  # Typical phone: portrait mode

# Color scheme (matches HTML version)
COLORS = {
    'bg': '#0b1020',
    'paper': '#eef1f7',
    'dim': '#9aa6c4',
    'amber': '#f2b134',      # boundary
    'cyan': '#4fd6e0',       # bulk
    'magenta': '#e0559b',    # magic
    'violet': '#8a7bff',     # geometry
    'green': '#63d69b',      # confirmation
    'line': '#26304f',
}

# ========== DATA MODEL ==========
class ExperimentState:
    """Holds the experiment parameters and computed values."""
    def __init__(self):
        self.theta_deg = 50  # 0..100 corresponds to 0..π/4
        self.magic = 0.0      # 0..1.0
        self.mode = 'flm'     # 'flm', 'magic', 'worm'
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
            # With magic: area grows with theta
            self.S_PA = (self.S_A - self.S_a) + self.magic * 0.9 * np.power(np.sin(2 * self.theta_rad), 2)
        elif self.mode == 'worm':
            # Double-sided: area shrinks with theta
            self.S_PA = (self.S_A - self.S_a) - (0.4 + self.magic * 0.9) * np.power(np.sin(2 * self.theta_rad), 2)
        
        # Clamp to valid range
        self.S_PA = max(0, min(3.5, self.S_PA))
    
    def theta_label(self):
        """Format theta as a nice label."""
        frac = self.theta_deg / 100.0
        if abs(frac - 0) < 0.03:
            return "0"
        elif abs(frac - 0.5) < 0.03:
            return "π/8"
        elif abs(frac - 1.0) < 0.03:
            return "π/4"
        else:
            return f"{frac * math.pi / 4:.3f}"

# ========== GRAPHICS ==========
def plot_entropy_curves(state):
    """Generate a matplotlib figure showing S_PA, S_A, S_a over theta range."""
    fig, ax = plt.subplots(figsize=(6, 4), facecolor='#0b1020', edgecolor='#26304f')
    ax.set_facecolor('#080e22')
    
    # Plot range: 0 to π/4
    theta_range = np.linspace(0, math.pi/4, 100)
    
    # Compute curves
    S_A_curve = 2.0 + np.power(np.sin(2 * theta_range), 2)
    S_a_curve = np.power(np.sin(2 * theta_range), 2)
    
    if state.mode == 'flm':
        S_PA_curve = S_A_curve - S_a_curve
    elif state.mode == 'magic':
        S_PA_curve = (S_A_curve - S_a_curve) + state.magic * 0.9 * np.power(np.sin(2 * theta_range), 2)
    else:  # worm
        S_PA_curve = (S_A_curve - S_a_curve) - (0.4 + state.magic * 0.9) * np.power(np.sin(2 * theta_range), 2)
    
    S_PA_curve = np.clip(S_PA_curve, 0, 3.5)
    
    # Plot lines
    ax.plot(theta_range, S_A_curve, color=COLORS['amber'], linestyle='--', linewidth=2.5, label='S(ρ_A) boundary', alpha=0.8)
    ax.plot(theta_range, S_a_curve, color=COLORS['cyan'], linestyle='--', linewidth=2.5, label='S(ρ_a) bulk', alpha=0.8)
    ax.plot(theta_range, S_PA_curve, color=COLORS['violet'], linewidth=3.5, label='S_PA (area term)', alpha=0.95)
    
    # Mark current theta
    ax.axvline(state.theta_rad, color=COLORS['magenta'], linewidth=1.5, alpha=0.7)
    ax.scatter([state.theta_rad], [state.S_PA], color=COLORS['violet'], s=80, zorder=5, edgecolors='#0b1020', linewidths=2)
    
    # Styling
    ax.set_xlim(0, math.pi/4)
    ax.set_ylim(0, 3.4)
    ax.set_xlabel('bulk entanglement angle θ', color=COLORS['dim'], fontsize=10)
    ax.set_ylabel('entropy', color=COLORS['dim'], fontsize=10)
    ax.set_xticks([0, math.pi/8, math.pi/4])
    ax.set_xticklabels(['0', 'π/8', 'π/4'], color=COLORS['dim'])
    ax.tick_params(colors=COLORS['dim'], labelsize=9)
    ax.grid(True, alpha=0.15, color='#182642')
    ax.legend(fontsize=9, loc='upper left', facecolor='#0a1530', edgecolor=COLORS['line'], labelcolor=COLORS['paper'])
    
    # Border
    for spine in ax.spines.values():
        spine.set_color(COLORS['line'])
        spine.set_linewidth(0.8)
    
    fig.tight_layout(pad=0.8)
    return fig

def fig_to_image(fig):
    """Convert matplotlib figure to Kivy Image widget."""
    canvas = FigureCanvasKivyAgg(fig)
    plt.close(fig)
    return canvas

def draw_bulk_boundary_diagram():
    """Draw a simple bulk-boundary diagram."""
    fig, ax = plt.subplots(figsize=(5, 4), facecolor='#0b1020', edgecolor=COLORS['line'])
    ax.set_xlim(-1.2, 1.2)
    ax.set_ylim(-1.2, 1.2)
    ax.set_aspect('equal')
    ax.axis('off')
    
    # Disk (bulk)
    disk = patches.Circle((0, 0), 1.0, fill=True, facecolor='#0a1128', edgecolor=COLORS['line'], linewidth=2)
    ax.add_patch(disk)
    
    # Boundary region (amber arc)
    wedge = Wedge((0, 0), 1.0, 45, 135, facecolor='none', edgecolor=COLORS['amber'], linewidth=3.5)
    ax.add_patch(wedge)
    
    # Minimal surface (violet dashed)
    arc = patches.Arc((0, 0), 0.7, 0.7, angle=0, theta1=45, theta2=135, color=COLORS['violet'], linewidth=2.5, linestyle='--')
    ax.add_patch(arc)
    
    # Bulk matter (cyan circle)
    matter = patches.Circle((0.3, 0), 0.15, fill=True, facecolor=COLORS['cyan'], alpha=0.85, edgecolor='none')
    ax.add_patch(matter)
    
    # Labels
    ax.text(0.95, 0.65, 'A (boundary)', fontsize=10, color=COLORS['amber'], weight='bold')
    ax.text(0.35, -0.25, 'S_a (bulk matter)', fontsize=9, color=COLORS['cyan'])
    ax.text(-0.1, 0.4, 'γ_A', fontsize=10, color=COLORS['violet'], weight='bold')
    
    fig.tight_layout(pad=0.2)
    return fig

def draw_wormhole_diagram():
    """Draw the wormhole neck shortening visualization."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6, 3), facecolor='#0b1020')
    
    for ax in [ax1, ax2]:
        ax.set_xlim(-0.5, 2.5)
        ax.set_ylim(-1.2, 1.2)
        ax.set_aspect('equal')
        ax.axis('off')
    
    # Left: long neck
    ax1.set_title('low θ: long neck', fontsize=10, color=COLORS['dim'])
    for cx in [0.3, 2.0]:
        circle = patches.Circle((cx, 0), 0.4, fill=False, edgecolor=COLORS['amber'], linewidth=2.5)
        ax1.add_patch(circle)
    # Neck
    for y_offset in [-0.5, 0.5]:
        ax1.plot([0.7, 1.6], [y_offset, y_offset], color=COLORS['violet'], linewidth=2.5)
    ax1.text(1.15, -1.0, 'large S_PA', fontsize=9, color=COLORS['violet'], ha='center')
    
    # Right: short neck
    ax2.set_title('high θ: short neck', fontsize=10, color=COLORS['dim'])
    for cx in [0.3, 2.0]:
        circle = patches.Circle((cx, 0), 0.4, fill=False, edgecolor=COLORS['amber'], linewidth=2.5)
        ax2.add_patch(circle)
    # Short neck
    for y_offset in [-0.3, 0.3]:
        ax2.plot([1.05, 1.25], [y_offset, y_offset], color=COLORS['violet'], linewidth=2.5)
    ax2.text(1.15, -1.0, 'small S_PA', fontsize=9, color=COLORS['violet'], ha='center')
    
    # Arrow between
    fig.text(0.5, 0.95, '→ increase entanglement →', ha='center', fontsize=9, color=COLORS['magenta'])
    
    fig.tight_layout(pad=0.5)
    return fig

# ========== KIVY UI ==========
class HolographicApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.state = ExperimentState()
        self.title = 'Holographic Quantum Gravity'
    
    def build(self):
        """Build the main UI."""
        Window.clearcolor = (0.067, 0.063, 0.125, 1.0)  # #0b1020
        
        # Main scrollable layout
        main_layout = BoxLayout(orientation='vertical', size_hint_y=1, padding=10, spacing=8)
        
        # Header
        header_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=120, spacing=6, padding=10)
        header_layout.canvas.before.clear()
        with header_layout.canvas.before:
            Color(0.067, 0.082, 0.156, 1.0)  # #0a1328
            Rectangle(size=header_layout.size, pos=header_layout.pos)
        
        title_label = Label(
            text='[b]Gravity from Entanglement[/b]\non a Quantum Chip',
            markup=True,
            font_size='18sp',
            size_hint_y=None,
            height=60,
            color=(0.94, 0.94, 0.97, 1.0)
        )
        header_layout.add_widget(title_label)
        
        tagline_label = Label(
            text='HaPPY code on IonQ Forte',
            font_size='11sp',
            size_hint_y=None,
            height=30,
            color=(0.6, 0.65, 0.77, 1.0)
        )
        header_layout.add_widget(tagline_label)
        main_layout.add_widget(header_layout)
        
        # Mode selector
        mode_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=4, padding=4)
        mode_buttons = [
            ('FLM', 'flm'),
            ('Magic', 'magic'),
            ('Wormhole', 'worm'),
        ]
        for btn_text, mode_id in mode_buttons:
            btn = Button(
                text=btn_text,
                size_hint_x=1,
                background_color=self._mode_color(mode_id),
                font_size='12sp'
            )
            btn.bind(on_press=lambda x, m=mode_id: self.set_mode(m))
            mode_layout.add_widget(btn)
        main_layout.add_widget(mode_layout)
        
        # Sliders & readouts
        controls_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=180, spacing=8, padding=8)
        controls_layout.canvas.before.clear()
        with controls_layout.canvas.before:
            Color(0.06, 0.08, 0.18, 1.0)
            Rectangle(size=controls_layout.size, pos=controls_layout.pos)
        
        # Theta slider
        theta_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=45, spacing=8)
        theta_label = Label(text='θ (bulk entanglement):', size_hint_x=0.35, font_size='11sp', color=(0.94, 0.94, 0.97, 1.0))
        theta_slider = Slider(min=0, max=100, value=self.state.theta_deg, size_hint_x=0.5, step=1)
        theta_slider.bind(value=self.on_theta_change)
        self.theta_readout = Label(text=self.state.theta_label(), size_hint_x=0.15, font_size='11sp', color=(0.95, 0.7, 0.2, 1.0))
        theta_row.add_widget(theta_label)
        theta_row.add_widget(theta_slider)
        theta_row.add_widget(self.theta_readout)
        controls_layout.add_widget(theta_row)
        
        # Magic slider
        magic_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=45, spacing=8)
        magic_label = Label(text='M (magic):', size_hint_x=0.35, font_size='11sp', color=(0.94, 0.94, 0.97, 1.0))
        magic_slider = Slider(min=0, max=100, value=0, size_hint_x=0.5, step=1)
        magic_slider.bind(value=self.on_magic_change)
        self.magic_readout = Label(text='0.00', size_hint_x=0.15, font_size='11sp', color=(0.88, 0.33, 0.61, 1.0))
        magic_row.add_widget(magic_label)
        magic_row.add_widget(magic_slider)
        magic_row.add_widget(self.magic_readout)
        controls_layout.add_widget(magic_row)
        
        # Readout: S_PA, S_A, S_a
        stats_layout = GridLayout(cols=3, size_hint_y=None, height=60, spacing=6, padding=4)
        stats_layout.canvas.before.clear()
        with stats_layout.canvas.before:
            Color(0.07, 0.1, 0.22, 1.0)
            Rectangle(size=stats_layout.size, pos=stats_layout.pos)
        
        for label_text, value_attr, color in [
            ('S_PA', 'S_PA', COLORS['violet']),
            ('S(ρ_A)', 'S_A', COLORS['amber']),
            ('S(ρ_a)', 'S_a', COLORS['cyan']),
        ]:
            stat_box = BoxLayout(orientation='vertical', size_hint_x=1, spacing=2)
            stat_box.add_widget(Label(text=label_text, font_size='10sp', color=(0.6, 0.65, 0.77, 1.0)))
            value_label = Label(text=f'{getattr(self.state, value_attr):.2f}', font_size='12sp', font_name='RobotoMono', bold=True)
            # Dynamic color
            rgb = tuple(int(color[i:i+2], 16) / 255 for i in (1, 3, 5))
            value_label.color = (*rgb, 1.0)
            setattr(self, f'{value_attr}_label', value_label)
            stat_box.add_widget(value_label)
            stats_layout.add_widget(stat_box)
        
        controls_layout.add_widget(stats_layout)
        main_layout.add_widget(controls_layout)
        
        # Plot
        self.plot_canvas = fig_to_image(plot_entropy_curves(self.state))
        main_layout.add_widget(self.plot_canvas)
        
        # Info button
        info_btn = Button(text='📖 Info & Diagrams', size_hint_y=None, height=45, font_size='12sp')
        info_btn.bind(on_press=self.show_info)
        main_layout.add_widget(info_btn)
        
        # Wrap in ScrollView
        scroll = ScrollView(size_hint=(1, 1))
        scroll.add_widget(main_layout)
        
        return scroll
    
    def _mode_color(self, mode_id):
        """Return button color based on mode."""
        if mode_id == self.state.mode:
            rgb = tuple(int(COLORS['cyan'][i:i+2], 16) / 255 for i in (1, 3, 5))
            return (*rgb, 1.0)
        else:
            return (0.06, 0.08, 0.18, 0.8)
    
    def set_mode(self, mode_id):
        """Switch experiment mode and refresh."""
        self.state.mode = mode_id
        self.state.update()
        self.refresh_ui()
    
    def on_theta_change(self, slider, value):
        """Handle theta slider change."""
        self.state.theta_deg = int(value)
        self.state.update()
        self.refresh_ui()
    
    def on_magic_change(self, slider, value):
        """Handle magic slider change."""
        self.state.magic = value / 100.0
        if self.state.mode == 'flm':
            self.state.magic = 0.0  # Disable magic in FLM mode
            slider.value = 0
        self.state.update()
        self.refresh_ui()
    
    def refresh_ui(self):
        """Refresh all UI elements to reflect current state."""
        self.theta_readout.text = self.state.theta_label()
        self.magic_readout.text = f'{self.state.magic:.2f}'
        
        self.S_PA_label.text = f'{self.state.S_PA:.2f}'
        self.S_A_label.text = f'{self.state.S_A:.2f}'
        self.S_a_label.text = f'{self.state.S_a:.2f}'
        
        # Redraw plot
        if hasattr(self, 'plot_canvas'):
            self.root.children[0].children[-3].remove_widget(self.plot_canvas)
        self.plot_canvas = fig_to_image(plot_entropy_curves(self.state))
        self.root.children[0].children.insert(3, self.plot_canvas)
    
    def show_info(self, instance):
        """Show information and diagrams in a popup."""
        content = BoxLayout(orientation='vertical', padding=10, spacing=8)
        
        # Tabs: Info, Diagrams
        tab_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=40, spacing=4)
        info_tab = Button(text='Info', size_hint_x=0.5, background_color=(0.56, 0.84, 0.88, 1.0))
        diag_tab = Button(text='Diagrams', size_hint_x=0.5, background_color=(0.06, 0.08, 0.18, 1.0))
        tab_layout.add_widget(info_tab)
        tab_layout.add_widget(diag_tab)
        content.add_widget(tab_layout)
        
        # Info view
        info_text = """
[b]Holographic Quantum Gravity[/b]

The HaPPY code experiment tests whether [i]spacetime geometry emerges from entanglement[/i].

[b]The FLM Formula:[/b]
S_A = Area(γ_A)/4G_N + S_a

This says a boundary entropy (left) equals:
• Geometric area in the bulk
• Plus entropy of bulk matter

[b]The Three Tests:[/b]

1. [color=8a7bff][b]FLM Test[/b][/color]: Clifford code. S_PA stays flat as bulk entanglement rises—sign of a rigid, fixed background.

2. [color=e0559b][b]Magic Injection[/b][/color]: Non-stabilizer gates break rigidity. S_PA now grows with bulk entanglement, mimicking [i]backreaction[/i]—geometry responds to matter.

3. [color=4fd6e0][b]Wormhole[/b][/color]: Two codes entangled through their bulk. S_PA shrinks as inter-code entanglement rises, as if a wormhole neck shortens.

[b]Key Constants:[/b]
• θ ∈ [0, π/4]: bulk entanglement angle
• M ∈ [0, 1]: magic (non-stabilizer resource)
• IonQ Forte: 36 trapped-ion qubits

Paper: arXiv 2607.12047 (July 2026)
        """
        info_label = Label(text=info_text, markup=True, size_hint_y=1, font_size='10sp', color=(0.94, 0.94, 0.97, 1.0))
        
        # Diagram view
        diag_layout = BoxLayout(orientation='vertical', size_hint_y=1, spacing=8)
        
        fig1 = draw_bulk_boundary_diagram()
        diag_layout.add_widget(fig_to_image(fig1))
        
        fig2 = draw_wormhole_diagram()
        diag_layout.add_widget(fig_to_image(fig2))
        
        # Scroll area for info
        scroll = ScrollView(size_hint=(1, 1))
        scroll.add_widget(info_label)
        
        # Switch tabs
        def show_info_tab(btn):
            content.clear_widgets()
            content.add_widget(tab_layout)
            content.add_widget(scroll)
            info_tab.background_color = (0.56, 0.84, 0.88, 1.0)
            diag_tab.background_color = (0.06, 0.08, 0.18, 0.8)
        
        def show_diag_tab(btn):
            content.clear_widgets()
            content.add_widget(tab_layout)
            content.add_widget(diag_layout)
            info_tab.background_color = (0.06, 0.08, 0.18, 0.8)
            diag_tab.background_color = (0.56, 0.84, 0.88, 1.0)
        
        info_tab.bind(on_press=show_info_tab)
        diag_tab.bind(on_press=show_diag_tab)
        
        content.add_widget(scroll)
        
        popup = Popup(title='Holographic Gravity Explainer', content=content, size_hint=(0.95, 0.9))
        popup.open()

# ========== ENTRY POINT ==========
if __name__ == '__main__':
    app = HolographicApp()
    app.run()
