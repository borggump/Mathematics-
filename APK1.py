import os
import zipfile
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox

class SimpleAPKBuilder:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Simple Python to APK")
        self.python_file = None
        self.setup_gui()

    def setup_gui(self):
        """Initialize the GUI components"""
        self.root.geometry("400x600")
        self.root.configure(bg='#f0f0f0')
        
        # Main container
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(padx=20, pady=20, fill='both', expand=True)
        
        # App Details Section
        app_frame = tk.LabelFrame(main_frame, text="App Details", bg='#f0f0f0', padx=10, pady=5)
        app_frame.pack(fill='x', pady=(0, 10))
        
        tk.Label(app_frame, text="App Name:", bg='#f0f0f0').pack(anchor='w')
        self.app_name = tk.Entry(app_frame)
        self.app_name.pack(fill='x', pady=(0, 10))
        self.app_name.insert(0, "My Python App")
        
        tk.Label(app_frame, text="Package Name:", bg='#f0f0f0').pack(anchor='w')
        self.package_name = tk.Entry(app_frame)
        self.package_name.pack(fill='x', pady=(0, 10))
        self.package_name.insert(0, "com.example.myapp")
        
        # Python File Section
        file_frame = tk.LabelFrame(main_frame, text="Python File", bg='#f0f0f0', padx=10, pady=5)
        file_frame.pack(fill='x', pady=(0, 10))
        
        tk.Button(
            file_frame,
            text="Select Python File",
            command=self.select_file,
            bg='#4CAF50',
            fg='white',
            pady=10
        ).pack(fill='x', pady=(5, 5))
        
        self.file_label = tk.Label(
            file_frame,
            text="No file selected",
            bg='#f0f0f0',
            wraplength=300
        )
        self.file_label.pack()
        
        # Build Section
        build_frame = tk.LabelFrame(main_frame, text="Build", bg='#f0f0f0', padx=10, pady=5)
        build_frame.pack(fill='x', pady=(0, 10))
        
        self.build_btn = tk.Button(
            build_frame,
            text="Create Project Files",
            command=self.create_project,
            bg='#2196F3',
            fg='white',
            pady=15,
            state='disabled'
        )
        self.build_btn.pack(fill='x', pady=(5, 5))
        
        self.status = tk.Label(
            build_frame,
            text="Ready to create project",
            bg='#f0f0f0',
            wraplength=300
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
            self.build_btn.config(state='normal')

    def create_project(self):
        """Create Android project structure"""
        try:
            self.status.config(text="Creating project structure...")
            
            # Create project directory in Downloads
            project_name = os.path.splitext(os.path.basename(self.python_file))[0]
            project_dir = os.path.join("/storage/emulated/0/Download", project_name)
            os.makedirs(project_dir, exist_ok=True)
            
            # Create project structure
            os.makedirs(os.path.join(project_dir, "app/src/main/java/src"), exist_ok=True)
            os.makedirs(os.path.join(project_dir, "app/src/main/assets"), exist_ok=True)
            os.makedirs(os.path.join(project_dir, "app/src/main/res/values"), exist_ok=True)
            os.makedirs(os.path.join(project_dir, "app/src/main/res/layout"), exist_ok=True)
            
            # Copy Python file
            shutil.copy2(self.python_file, os.path.join(project_dir, "app/src/main/assets/main.py"))
            
            # Create Android files
            self.create_manifest(project_dir)
            self.create_main_activity(project_dir)
            self.create_layout(project_dir)
            self.create_strings(project_dir)
            self.create_gradle_files(project_dir)
            self.create_readme(project_dir)
            
            self.status.config(text="Project created successfully!")
            messagebox.showinfo("Success", 
                f"Project created at:\n{project_dir}\n\n"
                "Please follow instructions in README.txt\n"
                "to complete the build process.")
            
        except Exception as e:
            self.status.config(text=f"Error: {str(e)}")
            messagebox.showerror("Error", str(e))

    def create_manifest(self, project_dir):
        """Create AndroidManifest.xml"""
        manifest = f'''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="{self.package_name.get()}">
    
    <application
        android:label="@string/app_name"
        android:allowBackup="true">
        <activity
            android:name=".MainActivity"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>'''
        
        with open(os.path.join(project_dir, "app/src/main/AndroidManifest.xml"), 'w') as f:
            f.write(manifest)

    def create_main_activity(self, project_dir):
        """Create MainActivity.java"""
        activity = '''package com.example.myapp;

import android.app.Activity;
import android.os.Bundle;
import android.widget.TextView;
import java.io.File;

public class MainActivity extends Activity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        
        TextView textView = findViewById(R.id.text_view);
        textView.setText("Running Python script...");
        
        try {
            File pythonScript = new File(getFilesDir(), "main.py");
            Process process = Runtime.getRuntime().exec("python " + pythonScript.getAbsolutePath());
            process.waitFor();
            textView.setText("Script completed!");
        } catch (Exception e) {
            textView.setText("Error: " + e.getMessage());
        }
    }
}'''
        
        with open(os.path.join(project_dir, "app/src/main/java/src/MainActivity.java"), 'w') as f:
            f.write(activity)

    def create_layout(self, project_dir):
        """Create layout file"""
        layout = '''<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:orientation="vertical"
    android:padding="16dp">
    
    <TextView
        android:id="@+id/text_view"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:textSize="18sp" />
</LinearLayout>'''
        
        with open(os.path.join(project_dir, "app/src/main/res/layout/activity_main.xml"), 'w') as f:
            f.write(layout)

    def create_strings(self, project_dir):
        """Create strings.xml"""
        strings = f'''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">{self.app_name.get()}</string>
</resources>'''
        
        with open(os.path.join(project_dir, "app/src/main/res/values/strings.xml"), 'w') as f:
            f.write(strings)

    def create_gradle_files(self, project_dir):
        """Create Gradle build files"""
        build_gradle = f'''plugins {{
    id 'com.android.application'
}}

android {{
    compileSdkVersion 30
    
    defaultConfig {{
        applicationId "{self.package_name.get()}"
        minSdkVersion 21
        targetSdkVersion 30
        versionCode 1
        versionName "1.0"
    }}
    
    buildTypes {{
        release {{
            minifyEnabled false
        }}
    }}
}}

dependencies {{
    implementation 'androidx.appcompat:appcompat:1.3.0'
}}'''
        
        with open(os.path.join(project_dir, "app/build.gradle"), 'w') as f:
            f.write(build_gradle)

    def create_readme(self, project_dir):
        """Create README with instructions"""
        readme = f'''Android Project: {self.app_name.get()}
=======================

This directory contains your Android project structure. To build:

1. Install Android Studio (https://developer.android.com/studio)

2. Open this project in Android Studio:
   - Open Android Studio
   - Select "Open an Existing Project"
   - Navigate to: {project_dir}
   - Click OK

3. Let Android Studio sync the project

4. Build the APK:
   - Click Build > Build Bundle(s) / APK(s) > Build APK(s)
   - Wait for build to complete
   - Click "locate" in the popup to find the APK

The APK will be located in:
{project_dir}/app/build/outputs/apk/debug/app-debug.apk

Note: You'll need to enable "Install from Unknown Sources"
in your Android settings to install the APK.'''
        
        with open(os.path.join(project_dir, "README.txt"), 'w') as f:
            f.write(readme)

    def run(self):
        """Start the application"""
        self.root.mainloop()

if __name__ == "__main__":
    builder = SimpleAPKBuilder()
    builder.run()