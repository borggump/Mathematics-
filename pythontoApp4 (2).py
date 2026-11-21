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
        self.root.geometry("400x500")
        self.root.configure(bg='#f0f0f0')
        
        # Main frame
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(padx=20, pady=20, fill='both', expand=True)
        
        # App name input
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
        
        # Status
        self.status = tk.Label(
            main_frame,
            text="Ready",
            bg='#f0f0f0',
            wraplength=350
        )
        self.status.pack()
        
    def select_file(self):
        filename = filedialog.askopenfilename(
            title="Select Python File",
            filetypes=[("Python files", "*.py")]
        )
        if filename:
            self.python_file = filename
            self.file_label.config(text=filename)
            self.install_button.config(state='normal')
            
    def create_app(self):
        try:
            self.status.config(text="Creating app...")
            
            # Create app directory
            app_name = self.app_name.get().replace(" ", "_")
            app_dir = os.path.join("/storage/emulated/0/Download", app_name)
            os.makedirs(app_dir, exist_ok=True)
            
            # Copy the Python script
            shutil.copy2(self.python_file, os.path.join(app_dir, "script.py"))
            
            # Create launcher
            launcher_path = os.path.join(app_dir, "run_app.py")
            with open(launcher_path, 'w') as f:
                f.write('import tkinter as tk\n')
                f.write('from tkinter import scrolledtext\n')
                f.write('import subprocess\n')
                f.write('import sys\n')
                f.write('import os\n\n')
                f.write('class AppRunner:\n')
                f.write('    def __init__(self):\n')
                f.write('        self.window = tk.Tk()\n')
                f.write('        self.window.title("Python App Runner")\n')
                f.write('        self.setup_gui()\n\n')
                f.write('    def setup_gui(self):\n')
                f.write('        self.window.geometry("400x600")\n')
                f.write('        run_button = tk.Button(\n')
                f.write('            self.window,\n')
                f.write('            text="Run Script",\n')
                f.write('            command=self.run_script,\n')
                f.write('            bg="#4CAF50",\n')
                f.write('            fg="white",\n')
                f.write('            pady=10\n')
                f.write('        )\n')
                f.write('        run_button.pack(fill="x", padx=20, pady=10)\n')
                f.write('        self.output = scrolledtext.ScrolledText(\n')
                f.write('            self.window,\n')
                f.write('            width=40,\n')
                f.write('            height=20\n')
                f.write('        )\n')
                f.write('        self.output.pack(padx=20, pady=10, fill="both", expand=True)\n')
                f.write('        clear_button = tk.Button(\n')
                f.write('            self.window,\n')
                f.write('            text="Clear Output",\n')
                f.write('            command=self.clear_output,\n')
                f.write('            bg="#2196F3",\n')
                f.write('            fg="white",\n')
                f.write('            pady=5\n')
                f.write('        )\n')
                f.write('        clear_button.pack(fill="x", padx=20, pady=10)\n\n')
                f.write('    def run_script(self):\n')
                f.write('        self.output.delete(1.0, "end")\n')
                f.write('        self.output.insert("end", "Running script...\\n")\n')
                f.write('        try:\n')
                f.write('            script_path = os.path.join(os.path.dirname(__file__), "script.py")\n')
                f.write('            process = subprocess.Popen(\n')
                f.write('                [sys.executable, script_path],\n')
                f.write('                stdout=subprocess.PIPE,\n')
                f.write('                stderr=subprocess.PIPE,\n')
                f.write('                text=True\n')
                f.write('            )\n')
                f.write('            stdout, stderr = process.communicate()\n')
                f.write('            if stdout:\n')
                f.write('                self.output.insert("end", stdout + "\\n")\n')
                f.write('            if stderr:\n')
                f.write('                self.output.insert("end", "Errors:\\n" + stderr + "\\n")\n')
                f.write('            self.output.insert("end", "Script completed!\\n")\n')
                f.write('        except Exception as e:\n')
                f.write('            self.output.insert("end", f"Error: {str(e)}\\n")\n')
                f.write('        self.output.see("end")\n\n')
                f.write('    def clear_output(self):\n')
                f.write('        self.output.delete(1.0, "end")\n\n')
                f.write('    def run(self):\n')
                f.write('        self.window.mainloop()\n\n')
                f.write('if __name__ == "__main__":\n')
                f.write('    app = AppRunner()\n')
                f.write('    app.run()\n')
            
            # Create shortcut
            shortcut_path = os.path.join("/storage/emulated/0/Download", f"{app_name}.py")
            with open(shortcut_path, 'w') as f:
                f.write('import subprocess\n')
                f.write('import sys\n')
                f.write('import os\n\n')
                f.write(f'app_dir = "{app_dir}"\n')
                f.write('subprocess.run([sys.executable, os.path.join(app_dir, "run_app.py")])\n')
            
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
    app = PythonInstaller()
    app.run()