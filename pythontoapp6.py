import os
import sys
import shutil
from pathlib import Path

def create_app(python_file, app_name="My_Python_App"):
    """Create Android-compatible Python app"""
    try:
        # Create app directory
        app_dir = os.path.join("/storage/emulated/0/Download", app_name)
        os.makedirs(app_dir, exist_ok=True)
        
        # Copy the Python script
        shutil.copy2(python_file, os.path.join(app_dir, "script.py"))
        
        # Create matplotlib settings
        with open(os.path.join(app_dir, "matplotlibrc"), 'w') as f:
            f.write("backend: Agg")
        
        # Create wrapper script
        wrapper_path = os.path.join(app_dir, "wrapper.py")
        with open(wrapper_path, 'w') as f:
            f.write('''import matplotlib
matplotlib.use('Agg')
import os
import sys

script_dir = os.path.dirname(__file__)
script_path = os.path.join(script_dir, "script.py")

with open(script_path) as f:
    exec(f.read())
''')
        
        # Create runner script
        runner_path = os.path.join(app_dir, "run_app.py")
        with open(runner_path, 'w') as f:
            f.write('''import os
import sys
import subprocess

def run_script():
    print("Running script...")
    print("-" * 40)
    
    try:
        script_dir = os.path.dirname(__file__)
        wrapper_path = os.path.join(script_dir, "wrapper.py")
        
        # Run script with matplotlib Agg backend
        env = {
            **os.environ,
            'MPLBACKEND': 'Agg',
            'MATPLOTLIBRC': script_dir
        }
        
        result = subprocess.run(
            [sys.executable, wrapper_path],
            env=env,
            capture_output=True,
            text=True
        )
        
        # Show output
        if result.stdout:
            print("\\nOutput:")
            print(result.stdout)
        
        # Show errors
        if result.stderr:
            print("\\nErrors:")
            print(result.stderr)
        
        # Check for plot files
        plots = [f for f in os.listdir(script_dir) 
                if f.endswith(('.png', '.jpg', '.pdf'))]
        if plots:
            print("\\nGenerated plots:")
            for plot in plots:
                print(f"- {plot}")
    
    except Exception as e:
        print(f"\\nError: {str(e)}")
    
    print("\\n" + "-" * 40)
    print("Press Ctrl+C to exit")

if __name__ == "__main__":
    run_script()
''')
        
        # Create shortcut
        shortcut_path = os.path.join("/storage/emulated/0/Download", f"{app_name}.py")
        with open(shortcut_path, 'w') as f:
            f.write(f'''import os
import sys
import subprocess

app_dir = "{app_dir}"
script_path = os.path.join(app_dir, "run_app.py")
subprocess.run([sys.executable, script_path])
''')
        
        print(f"App created successfully in Downloads/{app_name}")
        print("\nTo run the app:")
        print(f"1. Go to your Downloads folder")
        print(f"2. Run {app_name}.py")
        print("\nNote: Plots will be saved as image files in the app directory")
        
    except Exception as e:
        print(f"Error creating app: {str(e)}")

def main():
    if len(sys.argv) > 1:
        # Use command line argument as Python file
        python_file = sys.argv[1]
        if not os.path.exists(python_file):
            print(f"Error: File '{python_file}' not found")
            return
        
        # Get app name from file name
        app_name = os.path.splitext(os.path.basename(python_file))[0]
        create_app(python_file, app_name)
    else:
        print("Please provide the path to your Python file")
        print("Example: python script.py /path/to/your/script.py")

if __name__ == "__main__":
    main()
    