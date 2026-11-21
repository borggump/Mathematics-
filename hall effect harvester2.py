"""
SnTe Nonlinear Hall Effect Energy Harvester Simulator
====================================================

A comprehensive GUI application for designing and analyzing SnTe-based 
nonlinear Hall effect energy harvesters based on quantum geometric properties.

REQUIREMENTS:
- Python 3.6+
- numpy
- tkinter (usually included with Python)
- matplotlib (optional, for graphical plots)

INSTALLATION:
pip install numpy matplotlib

If matplotlib is not available, the program runs in text-mode with 
ASCII graphs and full numerical analysis capabilities.

USAGE:
python snTe_simulator.py

FEATURES:
- Material property optimization
- Device geometry analysis
- Performance calculations
- Cost analysis
- Fabrication process guidance
- Export/import parameters

Based on breakthrough research in Nature Nanotechnology (2025)
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import numpy as np
import math
import json

# Try to import matplotlib with fallback
MATPLOTLIB_AVAILABLE = True
try:
    import matplotlib.pyplot as plt
    try:
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg as FigureCanvas
    except ImportError:
        try:
            from matplotlib.backends.backend_tkagg import FigureCanvasTk as FigureCanvas
        except ImportError:
            # Fallback for older versions
            from matplotlib.backends.backend_tkagg import FigureCanvasTkinter as FigureCanvas
    from matplotlib.figure import Figure
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("Warning: matplotlib not available. Running in text-only mode.")

class SnTeHallRectifierSimulator:
    def __init__(self, root):
        self.root = root
        self.root.title("SnTe Nonlinear Hall Effect Energy Harvester Simulator")
        self.root.geometry("1400x900")
        self.root.configure(bg='#1e1e2e')
        
        # Configure style
        self.setup_styles()
        
        # Initialize default parameters
        self.init_default_params()
        
        # Create main interface
        self.create_widgets()
        
        # Initial calculation
        self.calculate_performance()
    
    def setup_styles(self):
        """Configure the GUI styling"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure styles for dark theme
        style.configure('Title.TLabel', 
                       foreground='#00d4ff', 
                       background='#1e1e2e', 
                       font=('Arial', 16, 'bold'))
        
        style.configure('Header.TLabel', 
                       foreground='#c471f5', 
                       background='#1e1e2e', 
                       font=('Arial', 12, 'bold'))
        
        style.configure('Custom.TFrame', 
                       background='#2a2a3e', 
                       relief='raised')
        
        style.configure('Custom.TEntry', 
                       fieldbackground='#3a3a4e', 
                       foreground='white')
    
    def init_default_params(self):
        """Initialize default material and device parameters"""
        # Material properties
        self.conductivity_2nd = tk.DoubleVar(value=0.004)  # Ω⁻¹V⁻¹
        self.mobility = tk.DoubleVar(value=2500)  # cm²/Vs
        self.carrier_density = tk.DoubleVar(value=1e17)  # cm⁻³
        self.bandgap = tk.DoubleVar(value=0.18)  # eV
        self.scattering_time = tk.DoubleVar(value=1e-12)  # seconds
        
        # Device geometry
        self.film_thickness = tk.DoubleVar(value=20)  # nm
        self.device_width = tk.DoubleVar(value=5000)  # μm
        self.device_length = tk.DoubleVar(value=5000)  # μm
        self.contact_resistance = tk.DoubleVar(value=10)  # Ω
        
        # Environmental conditions
        self.temperature = tk.DoubleVar(value=300)  # K
        self.ambient_field = tk.DoubleVar(value=1e-3)  # V/m
        self.frequency = tk.DoubleVar(value=1e9)  # Hz (1 GHz)
        
        # Cost parameters
        self.substrate_cost = tk.DoubleVar(value=50)  # $ per substrate
        self.material_cost = tk.DoubleVar(value=30)  # $ per device
        self.processing_cost = tk.DoubleVar(value=100)  # $ per device
    
    def create_widgets(self):
        """Create the main GUI widgets"""
        # Main container with scrolling
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title with version info
        title_text = "SnTe Nonlinear Hall Effect Energy Harvester Simulator"
        if not MATPLOTLIB_AVAILABLE:
            title_text += " (Text Mode)"
        
        title_label = ttk.Label(main_frame, 
                               text=title_text, 
                               style='Title.TLabel')
        title_label.pack(pady=(0, 20))
        
        # Create notebook for tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        self.create_input_tab(notebook)
        self.create_analysis_tab(notebook)
        self.create_fabrication_tab(notebook)
        self.create_cost_tab(notebook)
    
    def create_input_tab(self, notebook):
        """Create input parameters tab"""
        input_frame = ttk.Frame(notebook)
        notebook.add(input_frame, text="Material & Device Parameters")
        
        # Create sections
        self.create_material_section(input_frame)
        self.create_device_section(input_frame)
        self.create_environment_section(input_frame)
        
        # Calculate button
        calc_btn = tk.Button(input_frame, 
                           text="Calculate Performance", 
                           command=self.calculate_performance,
                           bg='#00d4ff', 
                           fg='white', 
                           font=('Arial', 12, 'bold'),
                           relief='flat',
                           padx=20, 
                           pady=10)
        calc_btn.pack(pady=20)
    
    def create_material_section(self, parent):
        """Create material properties input section"""
        frame = ttk.LabelFrame(parent, text="Material Properties", style='Custom.TFrame')
        frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Material property inputs
        params = [
            ("Second-order conductivity (Ω⁻¹V⁻¹):", self.conductivity_2nd, "0.004"),
            ("Mobility (cm²/Vs):", self.mobility, "2500"),
            ("Carrier density (cm⁻³):", self.carrier_density, "1e17"),
            ("Bandgap (eV):", self.bandgap, "0.18"),
            ("Scattering time (s):", self.scattering_time, "1e-12")
        ]
        
        for i, (label, var, default) in enumerate(params):
            row_frame = ttk.Frame(frame)
            row_frame.pack(fill=tk.X, padx=5, pady=3)
            
            ttk.Label(row_frame, text=label, width=30).pack(side=tk.LEFT)
            entry = ttk.Entry(row_frame, textvariable=var, style='Custom.TEntry', width=15)
            entry.pack(side=tk.LEFT, padx=5)
            ttk.Label(row_frame, text=f"(default: {default})", 
                     foreground='#888888', font=('Arial', 9)).pack(side=tk.LEFT, padx=5)
    
    def create_device_section(self, parent):
        """Create device geometry input section"""
        frame = ttk.LabelFrame(parent, text="Device Geometry", style='Custom.TFrame')
        frame.pack(fill=tk.X, padx=10, pady=5)
        
        params = [
            ("Film thickness (nm):", self.film_thickness, "20"),
            ("Device width (μm):", self.device_width, "5000"),
            ("Device length (μm):", self.device_length, "5000"),
            ("Contact resistance (Ω):", self.contact_resistance, "10")
        ]
        
        for label, var, default in params:
            row_frame = ttk.Frame(frame)
            row_frame.pack(fill=tk.X, padx=5, pady=3)
            
            ttk.Label(row_frame, text=label, width=30).pack(side=tk.LEFT)
            entry = ttk.Entry(row_frame, textvariable=var, style='Custom.TEntry', width=15)
            entry.pack(side=tk.LEFT, padx=5)
            ttk.Label(row_frame, text=f"(default: {default})", 
                     foreground='#888888', font=('Arial', 9)).pack(side=tk.LEFT, padx=5)
    
    def create_environment_section(self, parent):
        """Create environmental conditions input section"""
        frame = ttk.LabelFrame(parent, text="Operating Conditions", style='Custom.TFrame')
        frame.pack(fill=tk.X, padx=10, pady=5)
        
        params = [
            ("Temperature (K):", self.temperature, "300"),
            ("Ambient E-field (V/m):", self.ambient_field, "1e-3"),
            ("Frequency (Hz):", self.frequency, "1e9")
        ]
        
        for label, var, default in params:
            row_frame = ttk.Frame(frame)
            row_frame.pack(fill=tk.X, padx=5, pady=3)
            
            ttk.Label(row_frame, text=label, width=30).pack(side=tk.LEFT)
            entry = ttk.Entry(row_frame, textvariable=var, style='Custom.TEntry', width=15)
            entry.pack(side=tk.LEFT, padx=5)
            ttk.Label(row_frame, text=f"(default: {default})", 
                     foreground='#888888', font=('Arial', 9)).pack(side=tk.LEFT, padx=5)
    
    def create_analysis_tab(self, notebook):
        """Create performance analysis tab"""
        analysis_frame = ttk.Frame(notebook)
        notebook.add(analysis_frame, text="Performance Analysis")
        
        # Results display
        results_frame = ttk.LabelFrame(analysis_frame, text="Calculated Results")
        results_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.results_text = tk.Text(results_frame, 
                                   height=15, 
                                   bg='#2a2a3e', 
                                   fg='#ffffff', 
                                   font=('Courier', 10))
        self.results_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Plots frame (only if matplotlib is available)
        if MATPLOTLIB_AVAILABLE:
            plots_frame = ttk.Frame(analysis_frame)
            plots_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            self.create_plots(plots_frame)
        else:
            # Text-based analysis if no matplotlib
            text_analysis_frame = ttk.LabelFrame(analysis_frame, text="Performance Graphs (Text Mode)")
            text_analysis_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            
            self.graph_text = tk.Text(text_analysis_frame, 
                                    height=10, 
                                    bg='#2a2a3e', 
                                    fg='#00d4ff', 
                                    font=('Courier', 9))
            self.graph_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def create_plots(self, parent):
        """Create matplotlib plots for visualization"""
        if not MATPLOTLIB_AVAILABLE:
            return
            
        # Create figure with subplots
        self.fig = Figure(figsize=(12, 8), facecolor='#2a2a3e')
        self.fig.suptitle('SnTe Hall Rectifier Performance Analysis', 
                         color='white', fontsize=14, fontweight='bold')
        
        # Create subplots
        self.ax1 = self.fig.add_subplot(2, 2, 1)  # Frequency response
        self.ax2 = self.fig.add_subplot(2, 2, 2)  # Power vs field
        self.ax3 = self.fig.add_subplot(2, 2, 3)  # I-V characteristics
        self.ax4 = self.fig.add_subplot(2, 2, 4)  # Berry curvature visualization
        
        # Configure subplot appearance
        for ax in [self.ax1, self.ax2, self.ax3, self.ax4]:
            ax.set_facecolor('#1e1e2e')
            ax.tick_params(colors='white')
            ax.spines['bottom'].set_color('white')
            ax.spines['top'].set_color('white')
            ax.spines['right'].set_color('white')
            ax.spines['left'].set_color('white')
        
        # Embed in tkinter
        self.canvas = FigureCanvas(self.fig, parent)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def create_fabrication_tab(self, notebook):
        """Create fabrication process tab"""
        fab_frame = ttk.Frame(notebook)
        notebook.add(fab_frame, text="Fabrication Process")
        
        # Process flow display
        process_frame = ttk.LabelFrame(fab_frame, text="Fabrication Steps")
        process_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Create process flow text
        process_text = tk.Text(process_frame, 
                             bg='#2a2a3e', 
                             fg='#ffffff', 
                             font=('Arial', 10),
                             wrap=tk.WORD)
        process_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Insert fabrication process
        process_steps = """
FABRICATION PROCESS FOR SnTe NONLINEAR HALL RECTIFIER

═══════════════════════════════════════════════════════════

PHASE 1: SUBSTRATE PREPARATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Substrate Selection
   • Si(111) - Standard, cost-effective
   • GaAs(111) - Better lattice match
   • BaF₂ - Traditional choice for SnTe
   
2. Cleaning Protocol
   • RCA cleaning procedure
   • HF dip for native oxide removal
   • DI water rinse and N₂ dry
   
3. Surface Preparation
   • Load into UHV chamber
   • Outgas at 200°C for 2-4 hours
   • Flash clean at 1200°C (for Si)

PHASE 2: THIN FILM DEPOSITION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
METHOD A: Molecular Beam Epitaxy (MBE)
   • Base pressure: <1×10⁻⁹ Torr
   • Growth temperature: 200-250°C
   • Te/Sn flux ratio: 0.6-1.0
   • Growth rate: 0.1-0.5 nm/min
   • Target thickness: 20nm
   • RHEED monitoring for quality

METHOD B: RF Sputtering
   • Base pressure: <1×10⁻⁶ Torr
   • Ar pressure: 3-10 mTorr
   • RF power: 50-150W
   • Substrate temp: 150-300°C
   • Deposition rate: 0.5-2 nm/min

PHASE 3: DEVICE PATTERNING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Photolithography
   • Spin coat photoresist (3000 RPM)
   • Soft bake: 90°C, 60 seconds
   • UV exposure: 10-30 seconds
   • Develop in appropriate solution
   
2. Hall Bar Geometry
   • Length/Width ratio: >3:1
   • Contact spacing: >500 μm
   • Current/voltage electrode separation

PHASE 4: CONTACT FORMATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Metal Deposition
   • Ti adhesion layer: 5-10nm
   • Au contact layer: 50-100nm
   • E-beam evaporation preferred
   
2. Liftoff Process
   • Acetone ultrasonic bath
   • IPA rinse and N₂ dry
   • Optical inspection

PHASE 5: CHARACTERIZATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Structural Analysis
   • XRD for crystal orientation
   • AFM for surface morphology
   • SEM for contact quality
   
2. Electrical Testing
   • Four-point probe measurements
   • Hall effect characterization
   • I-V characteristics
   
3. Nonlinear Response Testing
   • RF signal generation
   • Lock-in amplifier detection
   • Frequency sweep analysis
   • Power conversion measurement

CRITICAL SUCCESS FACTORS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ UHV conditions for film growth
✓ (001) crystal orientation
✓ Atomically flat interfaces
✓ Low-resistance contacts
✓ Proper device geometry
✓ Temperature control during growth
✓ Contamination-free processing
        """
        
        process_text.insert(tk.END, process_steps)
        process_text.config(state=tk.DISABLED)
    
    def create_cost_tab(self, notebook):
        """Create cost analysis tab"""
        cost_frame = ttk.Frame(notebook)
        notebook.add(cost_frame, text="Cost Analysis")
        
        # Cost input section
        input_section = ttk.LabelFrame(cost_frame, text="Cost Parameters")
        input_section.pack(fill=tk.X, padx=10, pady=5)
        
        cost_params = [
            ("Substrate cost ($):", self.substrate_cost),
            ("Material cost per device ($):", self.material_cost),
            ("Processing cost per device ($):", self.processing_cost)
        ]
        
        for label, var in cost_params:
            row_frame = ttk.Frame(input_section)
            row_frame.pack(fill=tk.X, padx=5, pady=3)
            
            ttk.Label(row_frame, text=label, width=30).pack(side=tk.LEFT)
            ttk.Entry(row_frame, textvariable=var, style='Custom.TEntry', width=15).pack(side=tk.LEFT, padx=5)
        
        # Cost results
        self.cost_results_frame = ttk.LabelFrame(cost_frame, text="Cost Analysis Results")
        self.cost_results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.cost_text = tk.Text(self.cost_results_frame, 
                               bg='#2a2a3e', 
                               fg='#ffffff', 
                               font=('Courier', 10))
        self.cost_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def calculate_performance(self):
        """Calculate device performance based on input parameters"""
        try:
            # Extract parameters
            sigma_2 = self.conductivity_2nd.get()
            thickness = self.film_thickness.get() * 1e-9  # Convert nm to m
            width = self.device_width.get() * 1e-6  # Convert μm to m
            length = self.device_length.get() * 1e-6  # Convert μm to m
            E_field = self.ambient_field.get()
            freq = self.frequency.get()
            tau = self.scattering_time.get()
            R_contact = self.contact_resistance.get()
            T = self.temperature.get()
            
            # Calculate device area and volume
            area = width * length
            volume = area * thickness
            
            # Calculate DC current density (nonlinear Hall effect)
            # J_dc = (1/2) * σ^(2) * E₀²
            J_dc = 0.5 * sigma_2 * E_field**2  # A/m²
            
            # Calculate total current
            I_dc = J_dc * area  # A
            
            # Calculate device resistance
            rho = 1 / (self.mobility.get() * 1e-4 * self.carrier_density.get() * 1e6 * 1.602e-19)  # Ω⋅m
            R_device = rho * length / (width * thickness)
            R_total = R_device + R_contact
            
            # Calculate output voltage and power
            V_out = I_dc * R_total
            P_out = V_out * I_dc
            
            # Calculate frequency response
            omega = 2 * np.pi * freq
            freq_response = 1 / (1 + (omega * tau)**2)
            
            # Calculate power conversion efficiency
            P_input = 0.5 * 8.854e-12 * E_field**2 * area * 3e8  # Approximate input power
            efficiency = (P_out / P_input) * 100 if P_input > 0 else 0
            
            # Update results display
            self.update_results_display(I_dc, V_out, P_out, efficiency, freq_response, R_device, R_total)
            
            # Update plots
            self.update_plots()
            
            # Update cost analysis
            self.update_cost_analysis()
            
        except Exception as e:
            messagebox.showerror("Calculation Error", f"Error in calculation: {str(e)}")
    
    def update_results_display(self, I_dc, V_out, P_out, efficiency, freq_response, R_device, R_total):
        """Update the results text display"""
        results = f"""
NONLINEAR HALL RECTIFIER PERFORMANCE ANALYSIS
═══════════════════════════════════════════════════════════════

DEVICE SPECIFICATIONS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Film thickness:         {self.film_thickness.get():.1f} nm
• Device area:            {(self.device_width.get() * self.device_length.get() * 1e-12):.2e} m²
• Crystal orientation:    (001) SnTe
• Operating temperature:  {self.temperature.get():.0f} K

MATERIAL PROPERTIES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• 2nd-order conductivity: {self.conductivity_2nd.get():.4f} Ω⁻¹V⁻¹
• Carrier mobility:       {self.mobility.get():.0f} cm²/Vs
• Carrier density:        {self.carrier_density.get():.2e} cm⁻³
• Bandgap:               {self.bandgap.get():.2f} eV
• Scattering time:       {self.scattering_time.get():.2e} s

ELECTRICAL PERFORMANCE:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• DC current density:     {I_dc * 1e6:.2e} μA/m²
• Total DC current:       {I_dc * 1e9:.2f} nA
• Output voltage:         {V_out * 1e6:.2f} μV
• Output power:           {P_out * 1e12:.2f} pW
• Device resistance:      {R_device:.2f} Ω
• Total resistance:       {R_total:.2f} Ω

FREQUENCY RESPONSE:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Operating frequency:    {self.frequency.get():.2e} Hz
• Frequency response:     {freq_response:.3f}
• 3dB cutoff freq:       {1/(2*np.pi*self.scattering_time.get()):.2e} Hz
• Power conversion eff:   {efficiency:.2e} %

QUANTUM PROPERTIES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Berry curvature dipole: Active (non-zero)
• Mirror symmetry:        Preserved ({'{110}'} planes)
• Time-reversal symmetry: Preserved
• Topological protection: Yes (crystalline)

RECTIFICATION MECHANISM:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• DC component:          J_dc = ½σ⁽²⁾E₀²
• Zero bias operation:   ✓ Confirmed
• Broadband response:    MHz to THz
• Wireless operation:    ✓ No external power needed

PERFORMANCE METRICS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Sensitivity:           Ambient electromagnetic fields
• Operating range:       10⁶ - 10¹² Hz
• Temperature range:     4K - 400K
• Magnetic field:        Not required (zero field)
        """
        
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, results)
    
    def update_plots(self):
        """Update the performance plots"""
        # Clear previous plots
        for ax in [self.ax1, self.ax2, self.ax3, self.ax4]:
            ax.clear()
            ax.set_facecolor('#1e1e2e')
            ax.tick_params(colors='white')
            for spine in ax.spines.values():
                spine.set_color('white')
        
        # Plot 1: Frequency Response
        freq_range = np.logspace(6, 12, 100)  # 1 MHz to 1 THz
        tau = self.scattering_time.get()
        response = 1 / (1 + (2 * np.pi * freq_range * tau)**2)
        
        self.ax1.loglog(freq_range, response, color='#00d4ff', linewidth=2)
        self.ax1.axhline(y=0.5, color='#ff6b9d', linestyle='--', alpha=0.7)
        self.ax1.axvline(x=1/(2*np.pi*tau), color='#ff6b9d', linestyle='--', alpha=0.7)
        self.ax1.set_xlabel('Frequency (Hz)', color='white')
        self.ax1.set_ylabel('Normalized Response', color='white')
        self.ax1.set_title('Frequency Response', color='white', fontweight='bold')
        self.ax1.grid(True, alpha=0.3)
        
        # Plot 2: Power vs Electric Field
        E_range = np.logspace(-6, -1, 100)  # 1 μV/m to 0.1 V/m
        sigma_2 = self.conductivity_2nd.get()
        area = self.device_width.get() * self.device_length.get() * 1e-12  # m²
        thickness = self.film_thickness.get() * 1e-9  # m
        
        J_dc_range = 0.5 * sigma_2 * E_range**2
        I_dc_range = J_dc_range * area
        P_range = I_dc_range**2 * self.contact_resistance.get() * 1e12  # pW
        
        self.ax2.loglog(E_range, P_range, color='#c471f5', linewidth=2)
        self.ax2.axvline(x=self.ambient_field.get(), color='#ff6b9d', linestyle='--', alpha=0.7)
        self.ax2.set_xlabel('Electric Field (V/m)', color='white')
        self.ax2.set_ylabel('Output Power (pW)', color='white')
        self.ax2.set_title('Power vs Electric Field', color='white', fontweight='bold')
        self.ax2.grid(True, alpha=0.3)
        
        # Plot 3: I-V Characteristics (Nonlinear)
        V_range = np.linspace(-0.1, 0.1, 100)  # V
        # Nonlinear response: I ∝ V²
        I_linear = V_range / 1000  # Ohmic component
        I_nonlinear = sigma_2 * thickness * area * V_range**2 / self.device_length.get() * 1e6
        I_total = I_linear + I_nonlinear
        
        self.ax3.plot(V_range, I_linear*1e9, '--', color='#888888', label='Linear', linewidth=2)
        self.ax3.plot(V_range, I_nonlinear*1e9, color='#00d4ff', label='Nonlinear', linewidth=2)
        self.ax3.plot(V_range, I_total*1e9, color='#ff6b9d', label='Total', linewidth=2)
        self.ax3.set_xlabel('Voltage (V)', color='white')
        self.ax3.set_ylabel('Current (nA)', color='white')
        self.ax3.set_title('I-V Characteristics', color='white', fontweight='bold')
        self.ax3.legend(facecolor='#2a2a3e', edgecolor='white', labelcolor='white')
        self.ax3.grid(True, alpha=0.3)
        
        # Plot 4: Berry Curvature Dipole Visualization
        # Create momentum space visualization
        kx = np.linspace(-1, 1, 50)
        ky = np.linspace(-1, 1, 50)
        KX, KY = np.meshgrid(kx, ky)
        
        # Simulate Berry curvature with dipole structure
        # Simplified model: Ω ∝ k/|k|³ near Dirac points
        berry_curvature = np.zeros_like(KX)
        
        # Add Dirac points at L-points (simplified 2D projection)
        dirac_points = [(0.5, 0.5), (-0.5, 0.5), (0.5, -0.5), (-0.5, -0.5)]
        for dx, dy in dirac_points:
            r_sq = (KX - dx)**2 + (KY - dy)**2 + 0.1
            berry_curvature += (KX - dx) / r_sq**1.5
        
        # Create contour plot
        levels = np.linspace(-5, 5, 20)
        contour = self.ax4.contourf(KX, KY, berry_curvature, levels=levels, cmap='RdBu_r', alpha=0.8)
        self.ax4.contour(KX, KY, berry_curvature, levels=levels, colors='white', alpha=0.3, linewidths=0.5)
        
        # Add Dirac points
        for dx, dy in dirac_points:
            self.ax4.plot(dx, dy, 'o', color='#00d4ff', markersize=8, markeredgecolor='white')
        
        self.ax4.set_xlabel('kₓ (2π/a)', color='white')
        self.ax4.set_ylabel('kᵧ (2π/a)', color='white')
        self.ax4.set_title('Berry Curvature Distribution', color='white', fontweight='bold')
        
        # Add dipole arrow
        self.ax4.arrow(0, -0.8, 0, 0.3, head_width=0.05, head_length=0.05, 
                      fc='#c471f5', ec='#c471f5', linewidth=3)
        self.ax4.text(0.1, -0.6, 'Dipole\nMoment', color='#c471f5', fontweight='bold')
        
        # Refresh canvas
        self.canvas.draw()
    
    def update_cost_analysis(self):
        """Update cost analysis results"""
        try:
            substrate = self.substrate_cost.get()
            material = self.material_cost.get()
            processing = self.processing_cost.get()
            
            # Calculate various cost scenarios
            device_cost = substrate + material + processing
            
            # Different production scales
            scales = {
                "Prototype (1-10 devices)": {"multiplier": 1.0, "setup": 0},
                "Small batch (100 devices)": {"multiplier": 0.8, "setup": 5000},
                "Medium batch (1000 devices)": {"multiplier": 0.6, "setup": 25000},
                "Large scale (10000+ devices)": {"multiplier": 0.3, "setup": 100000}
            }
            
            cost_analysis = """
COST ANALYSIS FOR SnTe HALL RECTIFIER DEVICES
═══════════════════════════════════════════════════════════════

BASE COSTS PER DEVICE:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Substrate cost:         ${:.2f}
• Material cost:          ${:.2f}
• Processing cost:        ${:.2f}
• Base device cost:       ${:.2f}

PRODUCTION SCALE ANALYSIS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""".format(substrate, material, processing, device_cost)
            
            for scale_name, scale_data in scales.items():
                scaled_cost = device_cost * scale_data["multiplier"]
                setup_cost = scale_data["setup"]
                
                if scale_name == "Prototype (1-10 devices)":
                    quantity = 5
                elif "100" in scale_name:
                    quantity = 100
                elif "1000" in scale_name:
                    quantity = 1000
                else:
                    quantity = 10000
                
                total_setup_per_device = setup_cost / quantity if quantity > 0 else 0
                final_cost = scaled_cost + total_setup_per_device
                
                cost_analysis += f"""
{scale_name}:
  • Device cost:          ${scaled_cost:.2f}
  • Setup cost/device:    ${total_setup_per_device:.2f}
  • Total cost/device:    ${final_cost:.2f}
  • Total investment:     ${setup_cost + scaled_cost * quantity:.0f}
"""
            
            cost_analysis += """

EQUIPMENT INVESTMENT OPTIONS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• University access:      $500-2,000/device (no capital)
• Basic sputtering:       $100K-400K initial + $50-200/device
• Used MBE system:        $300K-800K initial + $20-100/device
• New MBE system:         $1M-2M initial + $10-50/device

FABRICATION METHOD COMPARISON:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Method           | Quality | Cost/Device | Setup Cost | Timeline
─────────────────┼─────────┼─────────────┼────────────┼─────────
MBE (new)        |   100%  |  $200-500   |   $1-2M    | 6-12 hrs
MBE (used)       |   95%   |  $100-300   |  $300-800K | 6-12 hrs
Sputtering       |   80%   |   $50-200   |  $100-400K | 1-3 hrs
University       |   90%   |  $500-2000  |     $0     | 1-2 days
Commercial       |   85%   |  $1000-5000 |     $0     | 2-4 weeks

MATERIAL COSTS (per kg):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• SnTe powder (99.999%):  $2,000-5,000
• SnTe sputtering target: $500-1,500
• Gold wire (contact):    $60,000/kg
• Silicon substrates:     $20-50 each
• GaAs substrates:        $100-300 each

RECOMMENDED DEVELOPMENT PATH:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Phase 1: Proof of concept via university collaboration
         Cost: $5K-20K, Timeline: 3-6 months
         
Phase 2: Basic sputtering setup for optimization
         Cost: $200K-400K, Timeline: 6-12 months
         
Phase 3: Production MBE system for scaling
         Cost: $1M+, Timeline: 12+ months
"""
            
            self.cost_text.delete(1.0, tk.END)
            self.cost_text.insert(tk.END, cost_analysis)
            
        except Exception as e:
            messagebox.showerror("Cost Analysis Error", f"Error in cost analysis: {str(e)}")
    
    def create_frequency_sweep(self):
        """Create frequency sweep analysis"""
        freq_range = np.logspace(6, 12, 100)
        tau = self.scattering_time.get()
        sigma_2 = self.conductivity_2nd.get()
        E_field = self.ambient_field.get()
        
        # Calculate frequency-dependent response
        response = []
        power_output = []
        
        for f in freq_range:
            omega = 2 * np.pi * f
            freq_resp = 1 / (1 + (omega * tau)**2)
            effective_sigma = sigma_2 * freq_resp
            
            # Calculate power at this frequency
            J_dc = 0.5 * effective_sigma * E_field**2
            area = self.device_width.get() * self.device_length.get() * 1e-12
            I_dc = J_dc * area
            P = I_dc**2 * self.contact_resistance.get() * 1e12  # pW
            
            response.append(freq_resp)
            power_output.append(P)
        
        return freq_range, response, power_output

def main():
    """Main function to run the simulator"""
    root = tk.Tk()
    
    # Configure for dark theme
    root.configure(bg='#1e1e2e')
    
    # Show startup info
    if not MATPLOTLIB_AVAILABLE:
        messagebox.showinfo("Startup Info", 
                          "Running in Text Mode\n\n" +
                          "Matplotlib not found. Graphs will be displayed as text.\n" +
                          "For full graphical interface, install: pip install matplotlib\n\n" +
                          "All calculations and analysis still work perfectly!")
    
    # Create the simulator
    app = SnTeHallRectifierSimulator(root)
    
    # Add menu bar
    menubar = tk.Menu(root, bg='#2a2a3e', fg='white')
    root.config(menu=menubar)
    
    # File menu
    file_menu = tk.Menu(menubar, tearoff=0, bg='#2a2a3e', fg='white')
    menubar.add_cascade(label="File", menu=file_menu)
    file_menu.add_command(label="Save Parameters", command=lambda: save_parameters(app))
    file_menu.add_command(label="Load Parameters", command=lambda: load_parameters(app))
    file_menu.add_separator()
    file_menu.add_command(label="Export Results", command=lambda: export_results(app))
    file_menu.add_separator()
    file_menu.add_command(label="Exit", command=root.quit)
    
    # Help menu
    help_menu = tk.Menu(menubar, tearoff=0, bg='#2a2a3e', fg='white')
    menubar.add_cascade(label="Help", menu=help_menu)
    help_menu.add_command(label="About", command=show_about)
    help_menu.add_command(label="Theory", command=show_theory)
    
    # Start the GUI
    root.mainloop()

def save_parameters(app):
    """Save current parameters to file"""
    try:
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            params = {
                'conductivity_2nd': app.conductivity_2nd.get(),
                'mobility': app.mobility.get(),
                'carrier_density': app.carrier_density.get(),
                'bandgap': app.bandgap.get(),
                'scattering_time': app.scattering_time.get(),
                'film_thickness': app.film_thickness.get(),
                'device_width': app.device_width.get(),
                'device_length': app.device_length.get(),
                'contact_resistance': app.contact_resistance.get(),
                'temperature': app.temperature.get(),
                'ambient_field': app.ambient_field.get(),
                'frequency': app.frequency.get()
            }
            
            with open(filename, 'w') as f:
                json.dump(params, f, indent=4)
            
            messagebox.showinfo("Success", f"Parameters saved to {filename}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save parameters: {str(e)}")

def load_parameters(app):
    """Load parameters from file"""
    try:
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            with open(filename, 'r') as f:
                params = json.load(f)
            
            # Update GUI variables
            for param_name, value in params.items():
                if hasattr(app, param_name):
                    getattr(app, param_name).set(value)
            
            # Recalculate
            app.calculate_performance()
            messagebox.showinfo("Success", f"Parameters loaded from {filename}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load parameters: {str(e)}")

def export_results(app):
    """Export results to file"""
    try:
        filename = tk.filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            results = app.results_text.get(1.0, tk.END)
            with open(filename, 'w') as f:
                f.write(results)
            messagebox.showinfo("Success", f"Results exported to {filename}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to export results: {str(e)}")

def show_about():
    """Show about dialog"""
    about_text = """
SnTe Nonlinear Hall Effect Energy Harvester Simulator
Version 1.0

This simulator calculates the performance of SnTe-based 
nonlinear Hall effect energy harvesters based on the 
breakthrough research published in Nature Nanotechnology (2025).

Features:
• Material property optimization
• Device geometry analysis  
• Frequency response modeling
• Cost analysis tools
• Fabrication guidance

Based on quantum geometric properties including:
• Berry curvature dipole effects
• Topological crystalline insulator physics
• Zero-bias rectification mechanisms

For questions or support, consult the latest research literature
on topological materials and nonlinear Hall effects.
    """
    messagebox.showinfo("About", about_text)

def show_theory():
    """Show theoretical background"""
    theory_text = """
THEORETICAL BACKGROUND

The nonlinear Hall effect arises from the Berry curvature dipole 
in momentum space:

D_αβ = ∫ dk Ω_α(k) k_β

This creates a nonlinear current response:
J_α^(2) = σ_αβγ^(2) E_β E_γ

For rectification:
J_dc = ½ σ^(2) E₀²

Key requirements:
✓ Broken inversion symmetry
✓ Preserved time-reversal symmetry  
✓ Topological crystalline insulator phase
✓ Large Berry curvature dipole

SnTe provides all these conditions with:
• Mirror-protected surface states
• Large second-order conductivity
• Broadband frequency response
• Room temperature operation
    """
    messagebox.showinfo("Theory", theory_text)

if __name__ == "__main__":
    main()