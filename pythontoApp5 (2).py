import os
import sys
import shutil
from pathlib import Path

def create_android_launcher():
    print("Python to Android App Converter")
    print("==============================")
    
    # Get app name
    app_name = input("Enter app name (e.g., My App): ").strip()
    if not app_name:
        app_name = "My Python App"
    
    # Get Python file
    while True:
        python_file = input("Enter path to your Python file: ").strip()
        if os.path.exists(python_file) and python_file.endswith('.py'):
            break
        print("File not found or not a Python file. Please try again.")
    
    try:
        # Create app directory
        safe_name = app_name.replace(" ", "_")
        app_dir = os.path.join("/storage/emulated/0/Download", safe_name)
        os.makedirs(app_dir, exist_ok=True)
        
        # Create matplotlib settings file
        with open(os.path.join(app_dir, "matplotlibrc"), 'w') as f:
            f.write("backend: Agg")
        
        # Create wrapper script that sets matplotlib backend
        wrapper_path = os.path.join(app_dir, "wrapper.py")
        with open(wrapper_path, 'w') as f:
            f.write("""import matplotlib
matplotlib.use('Agg')
import os
import sys

script_dir = os.path.dirname(__file__)
script_path = os.path.join(script_dir, "script.py")

with open(script_path) as f:
    code = compile(f.read(), script_path, 'exec')
    exec(code)
""")
        
        # Copy the Python script
        shutil.copy2(python_file, os.path.join(app_dir, "script.py"))
        
        # Create launcher
        launcher_path = os.path.join(app_dir, "run_app.py")
        with open(launcher_path, 'w') as f:
            f.write('''import os
import sys
import subprocess
from time import sleep

def clear_screen():
    os.system('clear')

def print_header():
    clear_screen()
    print("=" * 40)
    print("Python Script Runner")
    print("=" * 40)
    print()

def run_script():
    print_header()
    print("Running script...")
    print("-" * 40)
    print()
    
    try:
        # Run the wrapper script instead of the main script directly
        script_path = os.path.join(os.path.dirname(__file__), "wrapper.py")
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            env={
                **os.environ,
                'MPLBACKEND': 'Agg',  # Set matplotlib backend
                'MATPLOTLIBRC': os.path.dirname(__file__)  # Use local matplotlibrc
            }
        )
        
        if result.stdout:
            print("Output:")
            print(result.stdout)
            
        if result.stderr:
            print("\\nErrors:")
            print(result.stderr)
        
        # Check for generated plots
        plot_dir = os.path.dirname(script_path)
        plots = [f for f in os.listdir(plot_dir) if f.endswith(('.png', '.jpg', '.pdf'))]
        if plots:
            print("\\nGenerated plot files:")
            for plot in plots:
                print(f"- {plot}")
            
    except Exception as e:
        print(f"Error running script: {str(e)}")
    
    print()
    print("-" * 40)
    input("Press Enter to continue...")

def main_menu():
    while True:
        print_header()
        print("1. Run Script")
        print("2. Exit")
        print()
        
        choice = input("Select an option (1-2): ").strip()
        
        if choice == '1':
            run_script()
        elif choice == '2':
            print("\\nGoodbye!")
            break
        else:
            print("\\nInvalid choice. Please try again.")
            sleep(1)

if __name__ == "__main__":
    main_menu()
''')
        
        # Create shortcut
        shortcut_path = os.path.join("/storage/emulated/0/Download", f"{safe_name}.py")
        with open(shortcut_path, 'w') as f:
            f.write(f'''import os
import sys
import subprocess

app_dir = "{app_dir}"
launcher_path = os.path.join(app_dir, "run_app.py")
subprocess.run([sys.executable, launcher_path])
''')
        
        print("\nApp created successfully!")
        print(f"\nTo run your app:")
        print(f"1. Go to Downloads folder")
        print(f"2. Run {safe_name}.py")
        print("\nNote: If your script generates plots, they will be saved as image files")
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    create_android_launcher()