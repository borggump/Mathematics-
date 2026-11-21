import os
import sys
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox

class PythonInstaller:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Python App Installer")
        self.python_file = None
        self.setup_gui()

    def setup_gui(self):
        """Initialize GUI"""
        self.root.geometry("400x600")
        self.root.configure(bg='#f0f0f0')
        
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(padx=20, pady=20, fill='both', expand=True)
        
        # App Details
        details_frame = tk.LabelFrame(main_frame, text="App Details", bg='#f0f0f0', padx=10, pady=5)
        details_frame.pack(fill='x', pady=(0, 10))
        
        tk.Label(details_frame, text="App Name:", bg='#f0f0f0').pack(anchor='w')
        self.app_name = tk.Entry(details_frame)
        self.app_name.pack(fill='x', pady=(0, 10))
        self.app_name.insert(0, "My Python App")
        
        # Python File Selection
        file_frame = tk.LabelFrame(main_frame, text="Python File", bg='#f0f0f0', padx=10, pady=5)
        file_frame.pack(fill='x', pady=(0, 10))
        
        self.select_button = tk.Button(
            file_frame,
            text="Select Python File",
            command=self.select_file,
            bg='#4CAF50',
            fg='white',
            pady=10
        )
        self.select_button.pack(fill='x', pady=5)
        
        self.file_label = tk.Label(
            file_frame,
            text="No file selected",
            bg='#f0f0f0',
            wraplength=300
        )
        self.file_label.pack(pady=5)
        
        # Install Button
        self.install_button = tk.Button(
            main_frame,
            text="Install App",
            command=self.install_app,
            bg='#2196F3',
            fg='white',
            pady=15,
            font=('Arial', 12, 'bold'),
            state='disabled'
        )
        self.install_button.pack(fill='x', pady=20)
        
        # Status
        self.status_label = tk.Label(
            main_frame,
            text="Ready",
            bg='#f0f0f0',
            wraplength=300
        )
        self.status_label.pack(pady=10)

    def select_file(self):
        """Handle file selection"""
        filename = filedialog.askopenfilename(
            title="Select Python File",
            filetypes=[("Python files", "*.py")]
        )
        if filename:
            self.python_file = filename
            self.file_label.config(text=filename)
            self.install_button.config(state='normal')

    def install_app(self):
        """Install the Python app"""
        try:
            self.status_label.config(text="Starting installation...")
            
            # Create app directory in Downloads
            app_name = self.app_name.get().replace(" ", "_")
            app_dir = os.path.join("/storage/emulated/0/Download", app_name)
            os.makedirs(app_dir, exist_ok=True)
            
            # Copy the Python script
            script_path = os.path.join(app_dir, "script.py")
            shutil.copy2(self.python_file, script_path)
            
            # Create launcher script
            launcher_path = os.path.join(app_dir, "launcher.py")
            with open(launcher_path, 'w') as f:
                f.write(f'''import os
import sys
import traceback
from tkinter import *
from tkinter import scrolledtext

class AppLauncher:
    def __init__(self):
        self.root = Tk()
        self.root.title("{self.app_name.get()}")
        self.setup_gui()
        
    def setup_gui(self):
        """Setup the GUI"""
        # Configure main window
        self.root.geometry("400x600")
        
        # Add Run button
        run_frame = Frame(self.root)
        run_frame.pack(fill='x', padx=10, pady=5)
        
        run_btn = Button(
            run_frame,
            text="Run Script",
            command=self.run_script,
            bg='#4CAF50',
            fg='white',
            pady=10
        )
        run_btn.pack(fill='x')
        
        # Add output text area
        self.output = scrolledtext.ScrolledText(
            self.root,
            wrap=WORD,
            width=40,
            height=20
        )
        self.output.pack(padx=10, pady=5, fill='both', expand=True)
        
        # Add clear button
        clear_btn = Button(
            self.root,
            text="Clear Output",
            command=self.clear_output,
            bg='#2196F3',
            fg='white',
            pady=5
        )
        clear_btn.pack(fill='x', padx=10, pady=5)
        
    def run_script(self):
        """Run the Python script and capture output"""
        self.output.insert(END, "Running script...\\n")
        self.output.see(END)
        
        try:
            # Change to script directory
            script_dir = os.path.dirname(os.path.abspath(__file__))
            os.chdir(script_dir)
            
            # Import and run the script
            script_path = os.path.join(script_dir, "script.py")
            with open(script_path) as f:
                code = compile(f.read(), script_path, 'exec')
                
            # Redirect stdout to capture output
            import io
            from contextlib import redirect_stdout
            
            output = io.StringIO()
            with redirect_stdout(output):
                exec(code)
            
            # Display output
            self.output.insert(END, output.getvalue() + "\\nScript completed!\\n\\n")
            
        except Exception as e:
            error = traceback.format_exc()
            self.output.insert(END, f"Error:\\n{error}\\n")
            
        self.output.see(END)
    
    def clear_output(self):
        """Clear the output text area"""
        self.output.delete(1.0, END)
    
    def run(self):
        """Start the application"""
        self.root.mainloop()

if __name__ == '__main__':
    app = AppLauncher()
    app.run()
''')
            
            # Create desktop shortcut
            shortcut_path = os.path.join("/storage/emulated/0/Download", f"{app_name}_launcher.py")
            with open(shortcut_path, 'w') as f:
                f.write(f'''import os
import sys
import subprocess

# Launch the app
app_dir = "{app_dir}"
launcher_path = os.path.join(app_dir, "launcher.py")
subprocess.run([sys.executable, launcher_path])
''')
            
            self.status_label.config(text="Installation complete!")
            messagebox.showinfo(
                "Success",
                f"App installed successfully!\n\n" +
                f"To run the app:\n" +
                f"1. Go to your Downloads folder\n" +
                f"2. Run {app_name}_launcher.py"
            )
            
        except Exception as e:
            self.status_label.config(text=f"Error: {str(e)}")
            messagebox.showerror("Error", str(e))

    def run(self):
        """Start the application"""
        self.root.mainloop()

if __name__ == "__main__":
    installer = PythonInstaller()
    installer.run()