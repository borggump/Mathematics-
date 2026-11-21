#!/usr/bin/env python3
"""
Holographic Quantum Gravity Visualizer for PyDroid3 (LITE VERSION)
Pure Kivy implementation - no matplotlib required!

Ideal for PyDroid3 where matplotlib can be slow or problematic.
Only requires: kivy, numpy

Install in PyDroid3:
  pip install kivy numpy
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
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget
from kivy.uix.relativelayout import RelativeLayout
from kivy.graphics import Color, Line, Ellipse, Rectangle, Triangle
from kivy.core.window import Window

# ========== DEVICE CONFIG ==========
Window.size = (420, 900)

# Color scheme (matches HTML version)
COLORS = {
    'bg': (0.067, 0.063, 0.125, 1.0),        # #0b1020
    'paper': (0.93, 0.94, 0.97, 1.0),         # #eef1f7
    'dim': (0.6, 0.65, 0.77, 1.0),            # #9aa6c4
    'amber': (0.95, 0.69, 0.2, 1.0),          # #f2b134
    'cyan': (0.31, 0.84, 0.88, 1.0),          # #4fd6e0
    'magenta': (0.88, 0.33, 0.61, 1.0),       # #e0559b
    'violet': (0.54, 0.48, 1.0, 1.0),         # #8a7bff
    'green': (0.39, 0.84, 0.61, 1.0),         # #63d69b
    'line': (0.15, 0.18, 0.31, 1.0),          # #26304f
    'dark': (0.06, 0.08, 0.18, 1.0),          # #0a1328
}

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
        
        self.S_A = 2.0 + np.power(np.sin(2 * self.theta_rad), 2)
        self.S_a = np.power(np.sin(2 * self.theta_rad), 2)
        
        if self.mode == 'flm':
            self.S_PA = self.S_A - self.S_a
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

# ========== CUSTOM WIDGETS ==========
class EntropyPlotWidget(Widget):
    """Custom canvas plot of S_PA, S_A, S_a."""
    def __init__(self, state, **kwargs):
        super().__init__(**kwargs)
        self.state = state
        self.bind(size=self.redraw, pos=self.redraw)
    
    def redraw(self, *args):
        """Redraw the plot on canvas."""
        self.canvas.clear()
        
        if not self.size[0] or not self.size[1]:
            return
        
        x0, y0 = self.pos
        w, h = self.size
        pad_l, pad_r, pad_t, pad_b = 50, 15, 20, 35
        
        plot_x0 = x0 + pad_l
        plot_y0 = y0 + pad_b
        plot_w = w - pad_l - pad_r
        plot_h = h - pad_t - pad_b
        
        y_min, y_max = 0, 3.4
        x_min, x_max = 0, math.pi / 4
        
        def px(x):  # x coord to pixel
            return plot_x0 + (x - x_min) / (x_max - x_min) * plot_w
        
        def py(y):  # y coord to pixel
            return plot_y0 + (y - y_min) / (y_max - y_min) * plot_h
        
        with self.canvas:
            # Background
            Color(*COLORS['dark'])
            Rectangle(pos=(plot_x0, plot_y0), size=(plot_w, plot_h))
            
            # Grid lines
            Color(0.1, 0.15, 0.27, 0.5)
            for y_val in [0, 1, 2, 3]:
                yp = py(y_val)
                Line(points=[plot_x0, yp, plot_x0 + plot_w, yp], width=0.5)
            
            # Axes
            Color(*COLORS['line'])
            Line(points=[plot_x0, plot_y0, plot_x0 + plot_w, plot_y0], width=1.5)  # x-axis
            Line(points=[plot_x0, plot_y0, plot_x0, plot_y0 + plot_h], width=1.5)  # y-axis
            
            # Compute and draw curves
            theta_range = np.linspace(0, math.pi / 4, 100)
            S_A_curve = 2.0 + np.power(np.sin(2 * theta_range), 2)
            S_a_curve = np.power(np.sin(2 * theta_range), 2)
            
            if self.state.mode == 'flm':
                S_PA_curve = S_A_curve - S_a_curve
            elif self.state.mode == 'magic':
                S_PA_curve = (S_A_curve - S_a_curve) + self.state.magic * 0.9 * np.power(np.sin(2 * theta_range), 2)
            else:
                S_PA_curve = (S_A_curve - S_a_curve) - (0.4 + self.state.magic * 0.9) * np.power(np.sin(2 * theta_range), 2)
            
            S_PA_curve = np.clip(S_PA_curve, 0, 3.5)
            
            # Draw S_A (boundary, amber, dashed)
            Color(*COLORS['amber'])
            points_A = []
            for t, s in zip(theta_range, S_A_curve):
                points_A.extend([px(t), py(s)])
            if len(points_A) > 1:
                Line(points=points_A, width=2)
            
            # Draw S_a (bulk, cyan, dashed)
            Color(*COLORS['cyan'])
            points_a = []
            for t, s in zip(theta_range, S_a_curve):
                points_a.extend([px(t), py(s)])
            if len(points_a) > 1:
                Line(points=points_a, width=2)
            
            # Draw S_PA (violet, solid, thicker)
            Color(*COLORS['violet'])
            points_PA = []
            for t, s in zip(theta_range, S_PA_curve):
                points_PA.extend([px(t), py(s)])
            if len(points_PA) > 1:
                Line(points=points_PA, width=3)
            
            # Mark current theta
            theta_px = px(self.state.theta_rad)
            Color(*COLORS['magenta'])
            Line(points=[theta_px, plot_y0, theta_px, plot_y0 + plot_h], width=1.5)
            
            # Mark point on S_PA curve
            Color(*COLORS['violet'])
            Ellipse(pos=(theta_px - 5, py(self.state.S_PA) - 5), size=(10, 10))
            
            # Axis labels (text via kivy Labels, added separately)

class BulkBoundaryDiagram(Widget):
    """Draw the bulk-boundary correspondence schematic."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(size=self.redraw, pos=self.redraw)
    
    def redraw(self, *args):
        self.canvas.clear()
        if not self.size[0] or self.size[1]:
            return
        
        x, y = self.pos
        w, h = self.size
        cx, cy = x + w/2, y + h/2
        r = min(w, h) * 0.3
        
        with self.canvas:
            # Boundary circle
            Color(*COLORS['line'])
            Line(circle=(cx, cy, r), width=2)
            
            # Boundary region (amber arc)
            Color(*COLORS['amber'])
            # Draw wedge by approximating with line segments
            angles = np.linspace(45, 135, 20) * np.pi / 180
            for i in range(len(angles) - 1):
                x1 = cx + r * np.cos(angles[i])
                y1 = cy + r * np.sin(angles[i])
                x2 = cx + r * np.cos(angles[i+1])
                y2 = cy + r * np.sin(angles[i+1])
                Line(points=[x1, y1, x2, y2], width=3)
            
            # Minimal surface (violet dashed)
            Color(*COLORS['violet'])
            angles_min = np.linspace(45, 135, 15) * np.pi / 180
            r_min = r * 0.5
            for i in range(len(angles_min) - 1):
                x1 = cx + r_min * np.cos(angles_min[i])
                y1 = cy + r_min * np.sin(angles_min[i])
                x2 = cx + r_min * np.cos(angles_min[i+1])
                y2 = cy + r_min * np.sin(angles_min[i+1])
                Line(points=[x1, y1, x2, y2], width=2)
            
            # Bulk matter (cyan circle)
            Color(*COLORS['cyan'])
            Ellipse(pos=(cx + r*0.25 - 10, cy - 10), size=(20, 20))

class WormholeDiagram(Widget):
    """Draw the wormhole neck shortening."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(size=self.redraw, pos=self.redraw)
    
    def redraw(self, *args):
        self.canvas.clear()
        if not self.size[0] or self.size[1]:
            return
        
        x, y = self.pos
        w, h = self.size
        
        # Draw two scenarios side-by-side
        mid_x = x + w / 2
        
        with self.canvas:
            # LEFT: long neck
            cx1, cy = x + w * 0.15, y + h * 0.5
            
            Color(*COLORS['amber'])
            Ellipse(pos=(cx1 - 20, cy - 30), size=(40, 60))  # left circle
            
            Color(*COLORS['amber'])
            Ellipse(pos=(mid_x - 10, cy - 30), size=(40, 60))  # right circle (approx same)
            
            Color(*COLORS['violet'])
            Line(points=[cx1 + 20, cy - 15, mid_x - 20, cy - 15], width=3)
            Line(points=[cx1 + 20, cy + 15, mid_x - 20, cy + 15], width=3)
            
            # RIGHT: short neck (mirror to show side 2)
            cx2 = mid_x + w * 0.35
            
            Color(*COLORS['amber'])
            Ellipse(pos=(cx2 - 20, cy - 30), size=(40, 60))
            
            Color(*COLORS['violet'])
            Line(points=[mid_x + 20, cy - 10, cx2 - 20, cy - 10], width=3)
            Line(points=[mid_x + 20, cy + 10, cx2 - 20, cy + 10], width=3)

# ========== MAIN APP ==========
class HolographicApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.state = ExperimentState()
        self.title = 'Holographic Quantum Gravity'
    
    def build(self):
        """Build the main UI."""
        Window.clearcolor = COLORS['bg']
        
        main_layout = BoxLayout(orientation='vertical', size_hint_y=1, padding=10, spacing=8)
        
        # ---- HEADER ----
        header_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=110, spacing=6, padding=8)
        header_layout.canvas.before.clear()
        with header_layout.canvas.before:
            Color(*COLORS['dark'])
            Rectangle(size=header_layout.size, pos=header_layout.pos)
        
        title_label = Label(
            text='[b]Gravity ← Entanglement[/b]',
            markup=True,
            font_size='20sp',
            size_hint_y=None,
            height=50,
            color=COLORS['paper']
        )
        header_layout.add_widget(title_label)
        
        tagline_label = Label(
            text='HaPPY code on IonQ • arXiv 2607.12047',
            font_size='10sp',
            size_hint_y=None,
            height=30,
            color=COLORS['dim']
        )
        header_layout.add_widget(tagline_label)
        
        main_layout.add_widget(header_layout)
        
        # ---- MODE BUTTONS ----
        mode_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=45, spacing=4, padding=4)
        self.mode_btns = {}
        for btn_text, mode_id in [('FLM', 'flm'), ('Magic', 'magic'), ('Wormhole', 'worm')]:
            btn = Button(text=btn_text, size_hint_x=1, font_size='11sp')
            btn.bind(on_press=lambda x, m=mode_id: self.set_mode(m))
            self.mode_btns[mode_id] = btn
            mode_layout.add_widget(btn)
        self._update_mode_btns()
        main_layout.add_widget(mode_layout)
        
        # ---- CONTROLS ----
        controls_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=170, spacing=8, padding=8)
        controls_layout.canvas.before.clear()
        with controls_layout.canvas.before:
            Color(*COLORS['dark'])
            Rectangle(size=controls_layout.size, pos=controls_layout.pos)
        
        # Theta slider
        theta_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=40, spacing=8)
        theta_row.add_widget(Label(text='θ:', size_hint_x=0.2, font_size='11sp', color=COLORS['paper']))
        theta_slider = Slider(min=0, max=100, value=self.state.theta_deg, size_hint_x=0.6, step=1)
        theta_slider.bind(value=self.on_theta_change)
        self.theta_readout = Label(text=self.state.theta_label(), size_hint_x=0.2, font_size='11sp', color=COLORS['amber'], bold=True)
        theta_row.add_widget(theta_slider)
        theta_row.add_widget(self.theta_readout)
        controls_layout.add_widget(theta_row)
        
        # Magic slider
        magic_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=40, spacing=8)
        magic_row.add_widget(Label(text='M:', size_hint_x=0.2, font_size='11sp', color=COLORS['paper']))
        magic_slider = Slider(min=0, max=100, value=0, size_hint_x=0.6, step=1)
        magic_slider.bind(value=self.on_magic_change)
        self.magic_readout = Label(text='0.00', size_hint_x=0.2, font_size='11sp', color=COLORS['magenta'], bold=True)
        magic_row.add_widget(magic_slider)
        magic_row.add_widget(self.magic_readout)
        controls_layout.add_widget(magic_row)
        
        # Stats grid
        stats_grid = GridLayout(cols=3, size_hint_y=None, height=55, spacing=6, padding=4)
        stats_grid.canvas.before.clear()
        with stats_grid.canvas.before:
            Color(0.07, 0.1, 0.22, 1.0)
            Rectangle(size=stats_grid.size, pos=stats_grid.pos)
        
        self.stat_labels = {}
        for lbl, attr, col in [('S_PA', 'S_PA', COLORS['violet']), ('S_A', 'S_A', COLORS['amber']), ('S_a', 'S_a', COLORS['cyan'])]:
            box = BoxLayout(orientation='vertical', spacing=2)
            box.add_widget(Label(text=lbl, font_size='9sp', color=COLORS['dim']))
            val_lbl = Label(text=f'{getattr(self.state, attr):.2f}', font_size='13sp', bold=True, color=col)
            self.stat_labels[attr] = val_lbl
            box.add_widget(val_lbl)
            stats_grid.add_widget(box)
        controls_layout.add_widget(stats_grid)
        main_layout.add_widget(controls_layout)
        
        # ---- PLOT ----
        self.plot_widget = EntropyPlotWidget(self.state, size_hint_y=None, height=220)
        main_layout.add_widget(self.plot_widget)
        
        # ---- INFO BUTTON ----
        info_btn = Button(text='📖 Diagrams & Info', size_hint_y=None, height=45, font_size='11sp')
        info_btn.bind(on_press=self.show_info)
        main_layout.add_widget(info_btn)
        
        # Wrap in scroll (for smaller screens)
        scroll = ScrollView(size_hint=(1, 1))
        scroll.add_widget(main_layout)
        
        return scroll
    
    def set_mode(self, mode_id):
        self.state.mode = mode_id
        self.state.update()
        self._update_mode_btns()
        self.refresh_ui()
    
    def on_theta_change(self, slider, value):
        self.state.theta_deg = int(value)
        self.state.update()
        self.refresh_ui()
    
    def on_magic_change(self, slider, value):
        m = value / 100.0
        if self.state.mode == 'flm':
            m = 0.0
            slider.value = 0
        self.state.magic = m
        self.state.update()
        self.refresh_ui()
    
    def refresh_ui(self):
        self.theta_readout.text = self.state.theta_label()
        self.magic_readout.text = f'{self.state.magic:.2f}'
        self.stat_labels['S_PA'].text = f'{self.state.S_PA:.2f}'
        self.stat_labels['S_A'].text = f'{self.state.S_A:.2f}'
        self.stat_labels['S_a'].text = f'{self.state.S_a:.2f}'
        self.plot_widget.redraw()
    
    def _update_mode_btns(self):
        for mode_id, btn in self.mode_btns.items():
            if mode_id == self.state.mode:
                btn.background_color = COLORS['cyan']
                btn.color = (0.07, 0.063, 0.125, 1.0)
            else:
                btn.background_color = COLORS['dark']
                btn.color = COLORS['paper']
    
    def show_info(self, instance):
        """Show diagrams and info popup."""
        content = BoxLayout(orientation='vertical', spacing=8, padding=10)
        
        # Tabs
        tabs = BoxLayout(orientation='horizontal', size_hint_y=None, height=40, spacing=4)
        diag_btn = Button(text='Diagrams', size_hint_x=0.5)
        info_btn = Button(text='Info', size_hint_x=0.5)
        tabs.add_widget(diag_btn)
        tabs.add_widget(info_btn)
        content.add_widget(tabs)
        
        # Info content
        info_label = Label(
            text="""[b]Holographic Quantum Gravity[/b]

Does spacetime emerge from entanglement?

[b]The HaPPY Code[/b]
A quantum error-correcting code that models a universe slice. Logical bulk qubits encode to physical boundary qubits via a hyperbolic tensor network.

[b]FLM Test[/b]
S_A = Area(γ_A)/4G_N + S_a

Boundary entropy = geometry + bulk matter.

With rigid Clifford gates: S_PA stays flat (fixed background).

[b]Magic Injection[/b]
Non-stabilizer gates (small over-rotations) break rigidity. S_PA now grows with bulk entanglement—a sign of [i]backreaction[/i]. Geometry responds to matter.

[b]ER=EPR Wormhole[/b]
Two codes entangled through their bulk. As entanglement rises, S_PA shrinks—as if the wormhole neck shortens.

[b]Caveats[/b]
• N=1 regime (few qubits)
• Negative cosmological constant only
• Preprint (arXiv 2607.12047)
        """,
            markup=True,
            size_hint_y=1,
            font_size='10sp',
            color=COLORS['paper']
        )
        
        # Diagrams
        diag_content = BoxLayout(orientation='vertical', spacing=8, size_hint_y=1)
        diag_content.add_widget(Label(text='[b]Bulk-Boundary[/b]', markup=True, size_hint_y=None, height=30, color=COLORS['paper']))
        diag_content.add_widget(BulkBoundaryDiagram(size_hint_y=None, height=150))
        diag_content.add_widget(Label(text='[b]Wormhole Intuition[/b]', markup=True, size_hint_y=None, height=30, color=COLORS['paper']))
        diag_content.add_widget(WormholeDiagram(size_hint_y=None, height=100))
        diag_scroll = ScrollView(size_hint=(1, 1))
        diag_scroll.add_widget(diag_content)
        
        info_scroll = ScrollView(size_hint=(1, 1))
        info_scroll.add_widget(info_label)
        
        # Tab switching
        def show_diag(btn):
            content.clear_widgets()
            content.add_widget(tabs)
            content.add_widget(diag_scroll)
            diag_btn.background_color = COLORS['cyan']
            info_btn.background_color = COLORS['dark']
        
        def show_info(btn):
            content.clear_widgets()
            content.add_widget(tabs)
            content.add_widget(info_scroll)
            info_btn.background_color = COLORS['cyan']
            diag_btn.background_color = COLORS['dark']
        
        diag_btn.bind(on_press=show_diag)
        info_btn.bind(on_press=show_info)
        
        # Default to diagrams
        content.add_widget(diag_scroll)
        diag_btn.background_color = COLORS['cyan']
        
        popup = Popup(title='Holographic Gravity Explainer', content=content, size_hint=(0.95, 0.9))
        popup.open()

if __name__ == '__main__':
    app = HolographicApp()
    app.run()
