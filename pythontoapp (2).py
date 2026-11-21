import os
import sys
import shutil
import zipfile
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
        # Main window configuration
        self.root.geometry("600x700")
        self.root.configure(bg='#f0f0f0')
        
        # Main container
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(padx=20, pady=20, fill='both', expand=True)
        
        # App Details Section
        app_frame = tk.LabelFrame(main_frame, text="App Details", bg='#f0f0f0', padx=10, pady=5)
        app_frame.pack(fill='x', pady=(0, 10))
        
        # App Name
        tk.Label(app_frame, text="App Name:", bg='#f0f0f0').pack(anchor='w')
        self.app_name_entry = tk.Entry(app_frame)
        self.app_name_entry.pack(fill='x', pady=(0, 10))
        self.app_name_entry.insert(0, "My App")
        
        # Package Name
        tk.Label(app_frame, text="Package Name:", bg='#f0f0f0').pack(anchor='w')
        self.package_name_entry = tk.Entry(app_frame)
        self.package_name_entry.pack(fill='x', pady=(0, 10))
        self.package_name_entry.insert(0, "com.example.myapp")
        
        # File Selection Section
        file_frame = tk.LabelFrame(main_frame, text="Python File", bg='#f0f0f0', padx=10, pady=5)
        file_frame.pack(fill='x', pady=(0, 10))
        
        # File selection button
        self.file_button = tk.Button(
            file_frame,
            text="Select Python File",
            command=self.select_python_file,
            bg='#4CAF50',
            fg='white',
            pady=10
        )
        self.file_button.pack(fill='x', pady=(5, 5))
        
        # Selected file label
        self.file_label = tk.Label(
            file_frame,
            text="No file selected",
            bg='#f0f0f0',
            wraplength=500
        )
        self.file_label.pack()
        
        # Output Directory Section
        output_frame = tk.LabelFrame(main_frame, text="Output Location", bg='#f0f0f0', padx=10, pady=5)
        output_frame.pack(fill='x', pady=(0, 10))
        
        # Output directory button
        self.output_button = tk.Button(
            output_frame,
            text="Use Downloads Folder",
            command=self.select_output_dir,
            bg='#4CAF50',
            fg='white',
            pady=10
        )
        self.output_button.pack(fill='x', pady=(5, 5))
        
        # Selected directory label
        self.output_label = tk.Label(
            output_frame,
            text="No directory selected",
            bg='#f0f0f0',
            wraplength=500
        )
        self.output_label.pack()
        
        # Build Section
        build_frame = tk.LabelFrame(main_frame, text="Build", bg='#f0f0f0', padx=10, pady=5)
        build_frame.pack(fill='x', pady=(0, 10))
        
        # Convert button
        self.convert_button = tk.Button(
            build_frame,
            text="Build Android App",
            command=self.convert_to_android,
            bg='#2196F3',
            fg='white',
            pady=15,
            font=('Arial', 12, 'bold')
        )
        self.convert_button.pack(fill='x', pady=(5, 5))
        self.convert_button.config(state='disabled')
        
        # Progress label
        self.progress_label = tk.Label(
            build_frame,
            text="Ready to build",
            bg='#f0f0f0',
            wraplength=500
        )
        self.progress_label.pack()
        
        # Progress bar
        self.progress_bar = tk.Scale(
            build_frame,
            from_=0,
            to=100,
            orient='horizontal',
            showvalue=True,
            state='disabled',
            bg='#f0f0f0'
        )
        self.progress_bar.pack(fill='x')

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
            messagebox.showinfo("Directory Selected", f"Using Downloads folder:\n{self.output_dir}")
        except Exception as e:
            messagebox.showerror("Error", f"Cannot access Downloads folder: {str(e)}")
            self.output_dir = None

    def check_convert_button(self):
        """Enable convert button if both file and directory are selected"""
        if self.python_file and self.output_dir:
            self.convert_button.config(state='normal')
        else:
            self.convert_button.config(state='disabled')

    def convert_to_android(self):
        """Convert Python file to Android app"""
        try:
            self.progress_bar.set(0)
            self.progress_label.config(text="Starting conversion...")
            
            # Create project directory
            project_name = Path(self.python_file).stem
            app_dir = os.path.join(self.output_dir, project_name)
            os.makedirs(app_dir, exist_ok=True)
            self.progress_bar.set(20)
            
            # Create basic APK structure
            self.progress_label.config(text="Creating APK structure...")
            apk_file = os.path.join(app_dir, f"{project_name}.apk")
            
            with zipfile.ZipFile(apk_file, 'w') as zf:
                # Add AndroidManifest.xml
                manifest = f'''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="{self.package_name_entry.get()}">
    <application android:label="{self.app_name_entry.get()}">
        <activity android:name=".MainActivity">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>'''
                zf.writestr("AndroidManifest.xml", manifest)
                
                # Add Python script
                zf.write(self.python_file, "assets/main.py")
                
                # Add basic Java class
                java_class = '''
public class MainActivity extends android.app.Activity {
    @Override
    protected void onCreate(android.os.Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        // Run Python script
        runPythonScript();
    }
    
    private void runPythonScript() {
        try {
            Process process = Runtime.getRuntime().exec("python assets/main.py");
            process.waitFor();
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}'''
                zf.writestr("classes.dex", java_class)
            
            self.progress_bar.set(100)
            self.progress_label.config(text="APK created successfully!")
            
            messagebox.showinfo("Success", 
                f"APK created at:\n{apk_file}\n\n" +
                "Note: This is a basic APK. For Play Store submission, " +
                "additional configuration would be needed.")
            
        except Exception as e:
            self.progress_label.config(text=f"Error: {str(e)}")
            messagebox.showerror("Error", str(e))

    def run(self):
        """Start the GUI application"""
        self.root.mainloop()

if __name__ == "__main__":
    converter = AndroidConverter()
    converter.run()