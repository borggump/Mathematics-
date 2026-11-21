import os
import sys
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

class PythonAppInstaller:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Python App Installer")
        self.python_file = None
        self.setup_gui()
        
    def setup_gui(self):
        # Configure window
        self.root.geometry("400x500")
        self.root.configure(bg='#f0f0f0')
        
        # Main frame
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(padx=20, pady=20, fill='both', expand=True)
        
        # App name entry
        tk.Label(main_frame, text="App Name:", bg='#f0f0f0').pack(anchor='w')
        self.app_name = tk.Entry(main_frame)
        self.app_name.pack(fill='x', pady=(0,10))
        self.app_name.insert(0, "My Python App")
        
        # File selection
        self.select_button = tk.Button(
            main_frame,
            text="Select Python File",
            command=self.select_file,
            bg='#4CAF50',
            fg='white',
            pady=10
        )
        self.select_button.pack(fill='x')
        
        self.file_label = tk.Label(
            main_frame,
            text="No file selected",
            bg='#f0f0f0',
            wraplength=350
        )
        self.file_label.pack(pady=10)
        
        # Install button
        self.install_button = tk.Button(
            main_frame,
            text="Create App",
            command=self.create_app,
            bg='#2196F3',
            fg='white',
            pady=15,
            state='disabled'
        )
        self.install_button.pack(fill='x', pady=20)
        
        # Status label
        self.status = tk.Label(
            main_frame,
            text="Ready",
            bg='#f0f0f0',
            wraplength=350
        )
        self.status.pack()

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

    def create_app(self):
        """Create the app"""
        try:
            self.status.config(text="Creating app...")
            
            # Create app directory in Downloads
            app_name = self.app_name.get().replace(" ", "_")
            app_dir = os.path.join("/storage/emulated/0/Download", app_name)
            os.makedirs(app_dir, exist_ok=True)
            
            # Copy the Python script
            shutil.copy2(self.python_file, os.path.join(app_dir, "script.py"))
            
            # Create the launcher script
            launcher_code = """import tkinter as tk
from tkinter import scrolledtext
import subprocess
import sys
import os

class AppRunner:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Python App Runner")
        self.setup_gui()
        
    def setup_gui(self):
        self.window.geometry("400x600")
        
        # Run button
        run_button = tk.Button(
            self.window,
            text="Run Script",
            command=self.run_script,
            bg='#4CAF50',
            fg='white',
            pady=10
        )
        run_button.pack(fill='x', padx=20, pady=10)
        
        # Output area
        self.output = scrolledtext.ScrolledText(
            self.window,
            width=40,
            height=20
        )
        self.output.pack(padx=20, pady=10, fill='both', expand=True)
        
        # Clear button
        clear_button = tk.Button(
            self.window,
            text="Clear Output",
            command=self.clear_output,
            bg='#2196F3',
            fg='white',
            pady=5
        )
        clear_button.pack(fill='x', padx=20, pady=10)
    
    def run_script(self):
        """Run the Python script"""
        self.output.insert('end', "Running script...\\n")
        self.output.see('end')
        
        try:
            # Get script path
            current_dir = os.path.dirname(os.path.abspath(__file__))
            script_path = os.path.join(current_dir, "script.py")
            
            # Run the script and capture output
            process = subprocess.Popen(
                [sys.executable, script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate()
            
            if stdout:
                self.output.insert('end', stdout + "\\n")
            if stderr:
                self.output.insert('end', "Errors:\\n" + stderr + "\\n")
                
            self.output.insert('end', "Script completed!\\n\\n")
            self.output.see('end')
            
        except Exception as e:
            self.output.insert('end', f"Error: {str(e)}\\n\\n")
            self.output.see('end')
    
    def clear_output(self):
        """Clear the output area"""
        self.output.delete(1.0, 'end')
    
    def run(self):
        self.window.mainloop()

if __name__ == '__main__':
    app = AppRunner()
    app.run()
"""
            
            # Save the launcher
            with open(os.path.join(app_dir, "run_app.py"), 'w') as f:
                f.write(launcher_code)
            
            # Create shortcut in Downloads
            shortcut_path = os.path.join("/storage/emulated/0/Download", f"{app_name}.py")
            with open(shortcut_path, 'w') as f:
                f.write(f"""import os
import sys
import subprocess

# Launch the app
app_dir = "{app_dir}"
subprocess.run([sys.executable, os.path.join(app_dir, "run_app.py")])
""")
            
            self.status.config(text="App created successfully!")
            messagebox.showinfo(
                "Success",
                f"App created successfully!\n\n"
                f"To run your app:\n"
                f"1. Go to Downloads folder\n"
                f"2. Run {app_name}.py"
            )
            
        except Exception as e:
            self.status.config(text=f"Error: {str(e)}")
            messagebox.showerror("Error", str(e))

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = PythonAppInstaller()
    app.run()