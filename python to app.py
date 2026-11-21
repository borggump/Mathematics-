import os
import sys
import shutil
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

class AndroidConverter:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Python to Android Converter")
        self.python_file = None
        self.output_dir = None
        self.setup_gui()

    def setup_gui(self):
        """Initialize the GUI components"""
        self.root.geometry("600x700")
        self.root.configure(bg='#f0f0f0')
        
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(padx=20, pady=20, fill='both', expand=True)
        
        # App Details
        app_frame = tk.LabelFrame(main_frame, text="App Details", bg='#f0f0f0', padx=10, pady=5)
        app_frame.pack(fill='x', pady=(0, 10))
        
        tk.Label(app_frame, text="App Name:", bg='#f0f0f0').pack(anchor='w')
        self.app_name_entry = tk.Entry(app_frame)
        self.app_name_entry.pack(fill='x', pady=(0, 10))
        self.app_name_entry.insert(0, "My App")
        
        tk.Label(app_frame, text="Package Name:", bg='#f0f0f0').pack(anchor='w')
        self.package_name_entry = tk.Entry(app_frame)
        self.package_name_entry.pack(fill='x', pady=(0, 10))
        self.package_name_entry.insert(0, "org.test.myapp")
        
        # File Selection
        file_frame = tk.LabelFrame(main_frame, text="Python File", bg='#f0f0f0', padx=10, pady=5)
        file_frame.pack(fill='x', pady=(0, 10))
        
        self.file_button = tk.Button(
            file_frame,
            text="Select Python File",
            command=self.select_python_file,
            bg='#4CAF50',
            fg='white',
            pady=10
        )
        self.file_button.pack(fill='x', pady=(5, 5))
        
        self.file_label = tk.Label(
            file_frame,
            text="No file selected",
            bg='#f0f0f0',
            wraplength=500
        )
        self.file_label.pack()
        
        # Output Directory
        output_frame = tk.LabelFrame(main_frame, text="Output Location", bg='#f0f0f0', padx=10, pady=5)
        output_frame.pack(fill='x', pady=(0, 10))
        
        self.output_button = tk.Button(
            output_frame,
            text="Use Downloads Folder",
            command=self.select_output_dir,
            bg='#4CAF50',
            fg='white',
            pady=10
        )
        self.output_button.pack(fill='x', pady=(5, 5))
        
        self.output_label = tk.Label(
            output_frame,
            text="No directory selected",
            bg='#f0f0f0',
            wraplength=500
        )
        self.output_label.pack()
        
        # Build Section
        build_frame = tk.LabelFrame(main_frame, text="Project Creation", bg='#f0f0f0', padx=10, pady=5)
        build_frame.pack(fill='x', pady=(0, 10))
        
        self.convert_button = tk.Button(
            build_frame,
            text="Create Android Project",
            command=self.create_project,
            bg='#2196F3',
            fg='white',
            pady=15,
            font=('Arial', 12, 'bold')
        )
        self.convert_button.pack(fill='x', pady=(5, 5))
        self.convert_button.config(state='disabled')
        
        self.progress_label = tk.Label(
            build_frame,
            text="Ready to create project",
            bg='#f0f0f0',
            wraplength=500
        )
        self.progress_label.pack()

    def select_python_file(self):
        """Open file dialog to select Python file"""
        self.python_file = filedialog.askopenfilename(
            title="Select Python File",
            filetypes=[("Python files", "*.py")]
        )
        if self.python_file:
            self.file_label.config(text=self.python_file)
            self.check_convert_button()

    def select_output_dir(self):
        """Set output directory to Downloads folder"""
        self.output_dir = "/storage/emulated/0/Download"
        try:
            os.makedirs(self.output_dir, exist_ok=True)
            test_file = os.path.join(self.output_dir, "test_write")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            self.output_label.config(text=f"Using: {self.output_dir}")
            self.check_convert_button()
        except Exception as e:
            messagebox.showerror("Error", f"Cannot access Downloads folder: {str(e)}")
            self.output_dir = None

    def check_convert_button(self):
        """Enable convert button if both file and directory are selected"""
        if self.python_file and self.output_dir:
            self.convert_button.config(state='normal')
        else:
            self.convert_button.config(state='disabled')

    def create_project(self):
        """Create Buildozer project structure"""
        try:
            self.progress_label.config(text="Creating project structure...")
            
            # Create project directory
            project_name = Path(self.python_file).stem
            project_dir = os.path.join(self.output_dir, project_name)
            os.makedirs(project_dir, exist_ok=True)
            
            # Copy Python file as main.py
            shutil.copy2(self.python_file, os.path.join(project_dir, "main.py"))
            
            # Create buildozer.spec
            buildozer_spec = f"""[app]
title = {self.app_name_entry.get()}
package.name = {self.package_name_entry.get().split('.')[-1]}
package.domain = {'.'.join(self.package_name_entry.get().split('.')[:-1])}
source.dir = .
source.include_exts = py
version = 1.0
requirements = python3,kivy
orientation = portrait
osx.python_version = 3
osx.kivy_version = 1.9.1
android.permissions = INTERNET
android.api = 28
android.minapi = 21
android.ndk = 23b
android.sdk = 28
android.accept_sdk_license = True
"""
            with open(os.path.join(project_dir, "buildozer.spec"), 'w') as f:
                f.write(buildozer_spec)
            
            # Create README with instructions
            readme = f"""Android Project Setup
===================

This directory contains your Python project converted to an Android project structure.

To build the APK:

1. Install Buildozer:
   pip install buildozer

2. Install required packages:
   sudo apt-get install python3-pip build-essential git python3 python3-dev ffmpeg libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev libportmidi-dev libswscale-dev libavformat-dev libavcodec-dev zlib1g-dev

3. Run Buildozer:
   cd {project_dir}
   buildozer android debug

The APK will be created in the bin/ directory.

Note: Building requires Linux environment. You can use:
- Linux computer
- Virtual machine
- Google Cloud Shell
- WSL (Windows Subsystem for Linux)
"""
            with open(os.path.join(project_dir, "README.txt"), 'w') as f:
                f.write(readme)
            
            self.progress_label.config(text="Project created successfully!")
            messagebox.showinfo("Success", 
                f"Project created at:\n{project_dir}\n\n" +
                "Please follow instructions in README.txt\n" +
                "to build the final APK using Buildozer.")
            
        except Exception as e:
            self.progress_label.config(text=f"Error: {str(e)}")
            messagebox.showerror("Error", str(e))

    def run(self):
        """Start the GUI application"""
        self.root.mainloop()

if __name__ == "__main__":
    converter = AndroidConverter()
    converter.run()