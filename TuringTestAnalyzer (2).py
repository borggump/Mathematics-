import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import scipy.stats as stats
from scipy.stats import norm, binom
import seaborn as sns
from matplotlib.patches import Rectangle
import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import math

class TuringTestAnalyzer:
    def __init__(self):
        # Turing Test Data
        self.data = {
            'Model': ['GPT-4.5', 'LLaMA-3.1', 'GPT-4.5', 'GPT-4o', 'ELIZA'],
            'Condition': ['With Persona', 'With Persona', 'No Persona', 'No Persona', 'No Persona'],
            'Success_Rate': [0.73, 0.56, 0.36, 0.21, 0.23],
            'P_Value': [0.0001, 0.06, 0.0001, 0.0001, 0.0001],
            'Result': ['PASS', 'PASS', 'FAIL', 'FAIL', 'FAIL']
        }
        
        # Study parameters
        self.total_participants = 284
        self.rounds_per_participant = 8
        self.total_trials = self.total_participants * self.rounds_per_participant
        self.null_hypothesis = 0.5  # Random chance
        
        # Create DataFrame
        self.df = pd.DataFrame(self.data)
        
        # Set up matplotlib style
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
    def calculate_z_score(self, observed_rate, sample_size, null_prob=0.5):
        """Calculate z-score for binomial test"""
        standard_error = np.sqrt(null_prob * (1 - null_prob) / sample_size)
        z_score = (observed_rate - null_prob) / standard_error
        return z_score
    
    def calculate_p_value(self, z_score):
        """Calculate two-tailed p-value from z-score"""
        return 2 * (1 - norm.cdf(abs(z_score)))
    
    def calculate_cohens_d(self, observed_rate, null_prob=0.5):
        """Calculate Cohen's d for effect size"""
        std_pooled = np.sqrt(null_prob * (1 - null_prob))
        cohens_d = (observed_rate - null_prob) / std_pooled
        return cohens_d
    
    def calculate_confidence_interval(self, observed_rate, sample_size, confidence=0.95):
        """Calculate confidence interval for proportion"""
        z_critical = norm.ppf((1 + confidence) / 2)
        standard_error = np.sqrt(observed_rate * (1 - observed_rate) / sample_size)
        margin_error = z_critical * standard_error
        
        ci_lower = observed_rate - margin_error
        ci_upper = observed_rate + margin_error
        
        return ci_lower, ci_upper
    
    def print_statistical_analysis(self):
        """Print comprehensive statistical analysis"""
        print("=" * 80)
        print("TURING TEST MATHEMATICAL ANALYSIS")
        print("=" * 80)
        
        print("\n🎯 STATISTICAL FRAMEWORK")
        print("-" * 40)
        print("Null Hypothesis (H₀): AI model is indistinguishable from humans (p = 0.5)")
        print("Alternative Hypothesis (H₁): Success rate significantly differs from chance")
        print(f"Sample Size: {self.total_participants} participants × {self.rounds_per_participant} rounds = {self.total_trials} trials")
        
        print("\n📊 DETAILED RESULTS ANALYSIS")
        print("-" * 40)
        
        for i, row in self.df.iterrows():
            model = row['Model']
            condition = row['Condition']
            success_rate = row['Success_Rate']
            
            print(f"\n{model} ({condition}):")
            print(f"  Success Rate: {success_rate:.1%}")
            
            # Calculate statistics
            z_score = self.calculate_z_score(success_rate, self.total_trials)
            p_value = self.calculate_p_value(z_score)
            cohens_d = self.calculate_cohens_d(success_rate)
            ci_lower, ci_upper = self.calculate_confidence_interval(success_rate, self.total_trials)
            
            print(f"  Z-score: {z_score:.2f}")
            print(f"  P-value: {p_value:.2e}")
            print(f"  Cohen's d: {cohens_d:.3f}")
            print(f"  95% CI: [{ci_lower:.1%}, {ci_upper:.1%}]")
            
            # Effect size interpretation
            if abs(cohens_d) < 0.2:
                effect_size = "Small"
            elif abs(cohens_d) < 0.5:
                effect_size = "Medium"
            else:
                effect_size = "Large"
            
            print(f"  Effect Size: {effect_size}")
            print(f"  Result: {'PASS' if success_rate > 0.5 and p_value < 0.05 else 'FAIL'}")
        
        print("\n📈 KEY FINDINGS")
        print("-" * 40)
        gpt45_persona = self.df[(self.df['Model'] == 'GPT-4.5') & (self.df['Condition'] == 'With Persona')]['Success_Rate'].iloc[0]
        gpt45_no_persona = self.df[(self.df['Model'] == 'GPT-4.5') & (self.df['Condition'] == 'No Persona')]['Success_Rate'].iloc[0]
        
        print(f"• GPT-4.5 with persona: {gpt45_persona:.1%} success rate")
        print(f"• GPT-4.5 without persona: {gpt45_no_persona:.1%} success rate")
        print(f"• Persona effect: {(gpt45_persona - gpt45_no_persona):.1%} improvement")
        print(f"• Above chance level: {(gpt45_persona - 0.5):.1%}")
        
        # Probability of getting 73% by chance
        prob_by_chance = 1 - binom.cdf(int(gpt45_persona * self.total_trials), self.total_trials, 0.5)
        print(f"• Probability of 73% by chance: {prob_by_chance:.2e}")
        
        print("\n⚠️  STATISTICAL LIMITATIONS")
        print("-" * 40)
        print("• Results highly dependent on persona prompting")
        print("• Limited to 5-minute conversations")
        print("• Sample bias: mostly undergraduates and online workers")
        print("• Statistical significance ≠ meaningful intelligence")
        print("• Task-specific results may not generalize")
    
    def create_results_chart(self):
        """Create bar chart of success rates"""
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Prepare data
        labels = [f"{row['Model']}\n({row['Condition']})" for _, row in self.df.iterrows()]
        success_rates = [rate * 100 for rate in self.df['Success_Rate']]
        
        # Color coding
        colors = ['#2ecc71' if rate >= 50 else '#e74c3c' for rate in success_rates]
        
        # Create bars
        bars = ax.bar(labels, success_rates, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
        
        # Add chance line
        ax.axhline(y=50, color='red', linestyle='--', linewidth=2, label='Random Chance (50%)')
        
        # Customize chart
        ax.set_ylabel('Success Rate (%)', fontsize=12, fontweight='bold')
        ax.set_xlabel('AI Models', fontsize=12, fontweight='bold')
        ax.set_title('Turing Test Success Rates by Model', fontsize=16, fontweight='bold', pad=20)
        ax.set_ylim(0, 100)
        ax.grid(True, alpha=0.3, axis='y')
        
        # Add value labels on bars
        for bar, rate in zip(bars, success_rates):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                   f'{rate:.0f}%', ha='center', va='bottom', fontweight='bold')
        
        # Add legend
        ax.legend(loc='upper right')
        
        # Rotate x-axis labels for better readability
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        return fig
    
    def create_probability_distribution(self):
        """Create probability distribution chart"""
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Generate normal distribution for null hypothesis
        mean = 0.5
        std = np.sqrt(0.5 * 0.5 / self.total_trials)
        x = np.linspace(0.3, 0.8, 1000)
        y = norm.pdf(x, mean, std)
        
        # Plot expected distribution
        ax.plot(x * 100, y, 'b-', linewidth=3, label='Expected Distribution (Null Hypothesis)', alpha=0.8)
        ax.fill_between(x * 100, y, alpha=0.3, color='blue')
        
        # Add GPT-4.5 result line
        gpt45_result = 73
        ax.axvline(x=gpt45_result, color='red', linewidth=4, 
                  label=f'GPT-4.5 Result ({gpt45_result}%)', linestyle='-')
        
        # Shade rejection region (two-tailed test, α = 0.05)
        critical_value = norm.ppf(0.975, mean, std) * 100
        x_reject_upper = np.linspace(critical_value/100, 0.8, 100)
        y_reject_upper = norm.pdf(x_reject_upper, mean, std)
        ax.fill_between(x_reject_upper * 100, y_reject_upper, alpha=0.5, color='red', 
                       label='Rejection Region (α = 0.05)')
        
        critical_value_lower = norm.ppf(0.025, mean, std) * 100
        x_reject_lower = np.linspace(0.3, critical_value_lower/100, 100)
        y_reject_lower = norm.pdf(x_reject_lower, mean, std)
        ax.fill_between(x_reject_lower * 100, y_reject_lower, alpha=0.5, color='red')
        
        # Customize chart
        ax.set_xlabel('Success Rate (%)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Probability Density', fontsize=12, fontweight='bold')
        ax.set_title('Probability Distribution: Expected vs Observed Results', 
                    fontsize=16, fontweight='bold', pad=20)
        ax.grid(True, alpha=0.3)
        ax.legend(loc='upper right')
        
        # Add text annotation
        ax.text(73, max(y) * 0.8, f'P(X ≥ 73%) ≈ 0', 
               bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.8),
               fontsize=12, fontweight='bold')
        
        plt.tight_layout()
        return fig
    
    def create_effect_size_comparison(self):
        """Create effect size comparison chart"""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Calculate Cohen's d for each model
        cohens_d_values = [self.calculate_cohens_d(rate) for rate in self.df['Success_Rate']]
        labels = [f"{row['Model']}\n({row['Condition']})" for _, row in self.df.iterrows()]
        
        # Create horizontal bar chart
        bars = ax.barh(labels, cohens_d_values, color=['#27ae60' if d > 0 else '#e74c3c' for d in cohens_d_values])
        
        # Add effect size reference lines
        ax.axvline(x=0.2, color='orange', linestyle='--', alpha=0.7, label='Small Effect (d=0.2)')
        ax.axvline(x=0.5, color='blue', linestyle='--', alpha=0.7, label='Medium Effect (d=0.5)')
        ax.axvline(x=0.8, color='green', linestyle='--', alpha=0.7, label='Large Effect (d=0.8)')
        ax.axvline(x=0, color='black', linestyle='-', alpha=0.5)
        
        # Add value labels
        for i, (bar, value) in enumerate(zip(bars, cohens_d_values)):
            ax.text(value + 0.01 if value > 0 else value - 0.01, bar.get_y() + bar.get_height()/2,
                   f'{value:.3f}', va='center', ha='left' if value > 0 else 'right', fontweight='bold')
        
        ax.set_xlabel("Cohen's d (Effect Size)", fontsize=12, fontweight='bold')
        ax.set_title("Effect Size Analysis (Cohen's d)", fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='x')
        ax.legend(loc='lower right')
        
        plt.tight_layout()
        return fig
    
    def create_confidence_intervals_plot(self):
        """Create confidence intervals visualization"""
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Calculate confidence intervals
        ci_data = []
        for _, row in self.df.iterrows():
            rate = row['Success_Rate']
            ci_lower, ci_upper = self.calculate_confidence_interval(rate, self.total_trials)
            ci_data.append((rate, ci_lower, ci_upper))
        
        # Plot confidence intervals
        y_positions = range(len(self.df))
        labels = [f"{row['Model']} ({row['Condition']})" for _, row in self.df.iterrows()]
        
        for i, (rate, ci_lower, ci_upper) in enumerate(ci_data):
            # Plot confidence interval
            ax.plot([ci_lower * 100, ci_upper * 100], [i, i], 'b-', linewidth=3, alpha=0.7)
            ax.plot([ci_lower * 100, ci_lower * 100], [i-0.1, i+0.1], 'b-', linewidth=2)
            ax.plot([ci_upper * 100, ci_upper * 100], [i-0.1, i+0.1], 'b-', linewidth=2)
            
            # Plot point estimate
            color = '#2ecc71' if rate > 0.5 else '#e74c3c'
            ax.plot(rate * 100, i, 'o', markersize=8, color=color, markeredgecolor='black')
            
            # Add text labels
            ax.text(rate * 100 + 2, i, f'{rate:.1%}', va='center', fontweight='bold')
        
        # Add chance line
        ax.axvline(x=50, color='red', linestyle='--', linewidth=2, label='Random Chance (50%)')
        
        ax.set_yticks(y_positions)
        ax.set_yticklabels(labels)
        ax.set_xlabel('Success Rate (%)', fontsize=12, fontweight='bold')
        ax.set_title('95% Confidence Intervals for Success Rates', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='x')
        ax.legend()
        
        plt.tight_layout()
        return fig

class TuringTestGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Turing Test Mathematical Analysis")
        self.root.geometry("1400x900")
        
        self.analyzer = TuringTestAnalyzer()
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.create_analysis_tab()
        self.create_visualization_tab()
        self.create_statistics_tab()
        
    def create_analysis_tab(self):
        # Analysis tab
        analysis_frame = ttk.Frame(self.notebook)
        self.notebook.add(analysis_frame, text="Statistical Analysis")
        
        # Create scrollable text widget
        text_frame = ttk.Frame(analysis_frame)
        text_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Text widget with scrollbar
        self.analysis_text = tk.Text(text_frame, wrap=tk.WORD, font=('Courier', 10))
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self.analysis_text.yview)
        self.analysis_text.configure(yscrollcommand=scrollbar.set)
        
        self.analysis_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Button to run analysis
        button_frame = ttk.Frame(analysis_frame)
        button_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(button_frame, text="Run Statistical Analysis", 
                  command=self.run_analysis).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Clear Output", 
                  command=self.clear_analysis).pack(side='left', padx=5)
        
        # Auto-run analysis
        self.run_analysis()
    
    def create_visualization_tab(self):
        # Visualization tab
        viz_frame = ttk.Frame(self.notebook)
        self.notebook.add(viz_frame, text="Visualizations")
        
        # Control panel
        control_frame = ttk.Frame(viz_frame)
        control_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(control_frame, text="Success Rates Chart", 
                  command=self.show_results_chart).pack(side='left', padx=5)
        ttk.Button(control_frame, text="Probability Distribution", 
                  command=self.show_probability_chart).pack(side='left', padx=5)
        ttk.Button(control_frame, text="Effect Sizes", 
                  command=self.show_effect_sizes).pack(side='left', padx=5)
        ttk.Button(control_frame, text="Confidence Intervals", 
                  command=self.show_confidence_intervals).pack(side='left', padx=5)
        
        # Plot area
        self.plot_frame = ttk.Frame(viz_frame)
        self.plot_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Show initial chart
        self.show_results_chart()
    
    def create_statistics_tab(self):
        # Statistics tab
        stats_frame = ttk.Frame(self.notebook)
        self.notebook.add(stats_frame, text="Data & Statistics")
        
        # Data table
        table_frame = ttk.LabelFrame(stats_frame, text="Turing Test Results", padding=10)
        table_frame.pack(fill='x', padx=10, pady=5)
        
        # Create treeview
        columns = ('Model', 'Condition', 'Success Rate', 'Z-Score', 'P-Value', "Cohen's d", 'Result')
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=6)
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor='center')
        
        # Populate table
        for _, row in self.analyzer.df.iterrows():
            success_rate = row['Success_Rate']
            z_score = self.analyzer.calculate_z_score(success_rate, self.analyzer.total_trials)
            p_value = self.analyzer.calculate_p_value(z_score)
            cohens_d = self.analyzer.calculate_cohens_d(success_rate)
            
            self.tree.insert('', 'end', values=(
                row['Model'],
                row['Condition'],
                f"{success_rate:.1%}",
                f"{z_score:.2f}",
                f"{p_value:.2e}",
                f"{cohens_d:.3f}",
                row['Result']
            ))
        
        self.tree.pack(fill='x')
        
        # Study parameters
        params_frame = ttk.LabelFrame(stats_frame, text="Study Parameters", padding=10)
        params_frame.pack(fill='x', padx=10, pady=5)
        
        params_text = f"""
        Total Participants: {self.analyzer.total_participants}
        Rounds per Participant: {self.analyzer.rounds_per_participant}
        Total Trials: {self.analyzer.total_trials}
        Null Hypothesis: p = {self.analyzer.null_hypothesis} (random chance)
        Significance Level: α = 0.05
        Test Type: Two-tailed binomial test
        """
        
        ttk.Label(params_frame, text=params_text, font=('Courier', 10)).pack(anchor='w')
    
    def run_analysis(self):
        # Capture print output
        import io
        import sys
        
        old_stdout = sys.stdout
        sys.stdout = buffer = io.StringIO()
        
        self.analyzer.print_statistical_analysis()
        
        sys.stdout = old_stdout
        output = buffer.getvalue()
        
        self.analysis_text.delete(1.0, tk.END)
        self.analysis_text.insert(1.0, output)
    
    def clear_analysis(self):
        self.analysis_text.delete(1.0, tk.END)
    
    def clear_plot_frame(self):
        for widget in self.plot_frame.winfo_children():
            widget.destroy()
    
    def show_results_chart(self):
        self.clear_plot_frame()
        fig = self.analyzer.create_results_chart()
        canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)
    
    def show_probability_chart(self):
        self.clear_plot_frame()
        fig = self.analyzer.create_probability_distribution()
        canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)
    
    def show_effect_sizes(self):
        self.clear_plot_frame()
        fig = self.analyzer.create_effect_size_comparison()
        canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)
    
    def show_confidence_intervals(self):
        self.clear_plot_frame()
        fig = self.analyzer.create_confidence_intervals_plot()
        canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)

def main():
    """
    Run the Turing Test Mathematical Analysis
    Automatically runs command-line analysis and creates visualizations
    """
    print("🔬 TURING TEST MATHEMATICAL ANALYSIS")
    print("=" * 50)
    
    try:
        # Try to run GUI version first (if display available)
        import os
        if os.environ.get('DISPLAY') or os.name == 'nt':  # Check if GUI is possible
            print("Attempting to launch GUI application...")
            try:
                root = tk.Tk()
                app = TuringTestGUI(root)
                root.mainloop()
                return
            except Exception as e:
                print(f"GUI failed: {e}")
                print("Falling back to command-line analysis...")
    except:
        pass
    
    # Command-line mode (fallback or default)
    print("Running command-line statistical analysis...")
    analyzer = TuringTestAnalyzer()
    analyzer.print_statistical_analysis()
    
    # Create and display plots
    print("\n📊 Generating visualizations...")
    
    try:
        # Results chart
        print("Creating success rates chart...")
        fig1 = analyzer.create_results_chart()
        plt.figure(fig1.number)
        plt.show(block=False)
        
        # Probability distribution
        print("Creating probability distribution...")
        fig2 = analyzer.create_probability_distribution()
        plt.figure(fig2.number)
        plt.show(block=False)
        
        # Effect sizes
        print("Creating effect sizes chart...")
        fig3 = analyzer.create_effect_size_comparison()
        plt.figure(fig3.number)
        plt.show(block=False)
        
        # Confidence intervals
        print("Creating confidence intervals chart...")
        fig4 = analyzer.create_confidence_intervals_plot()
        plt.figure(fig4.number)
        plt.show(block=False)
        
        # Keep plots open
        plt.show()
        
    except Exception as e:
        print(f"Visualization error: {e}")
        print("Charts may not display in this environment.")
    
    print("\n✅ Analysis complete!")

def run_quick_analysis():
    """Quick analysis function for testing"""
    analyzer = TuringTestAnalyzer()
    
    print("🎯 QUICK TURING TEST ANALYSIS")
    print("=" * 40)
    
    # Key findings
    gpt45_persona = 0.73
    gpt45_no_persona = 0.36
    
    print(f"GPT-4.5 with persona: {gpt45_persona:.1%}")
    print(f"GPT-4.5 without persona: {gpt45_no_persona:.1%}")
    print(f"Improvement with persona: {(gpt45_persona - gpt45_no_persona):.1%}")
    
    # Statistical significance
    z_score = analyzer.calculate_z_score(gpt45_persona, analyzer.total_trials)
    p_value = analyzer.calculate_p_value(z_score)
    cohens_d = analyzer.calculate_cohens_d(gpt45_persona)
    
    print(f"\nStatistical Analysis:")
    print(f"Z-score: {z_score:.2f}")
    print(f"P-value: {p_value:.2e}")
    print(f"Cohen's d: {cohens_d:.3f}")
    print(f"Result: {'SIGNIFICANT' if p_value < 0.05 else 'NOT SIGNIFICANT'}")
    
    return analyzer

if __name__ == "__main__":
    # Try main function, fall back to quick analysis if needed
    try:
        main()
    except Exception as e:
        print(f"Main function error: {e}")
        print("\n🔄 Running simplified analysis...")
        run_quick_analysis()