import os
import shutil

# Get path to your Python file
print("Enter the full path to your Python file:")
print("Example: /storage/emulated/0/Download/your_script.py")
python_file = input().strip()

if not os.path.exists(python_file):
    print(f"Error: File not found: {python_file}")
else:
    try:
        # Create app folder
        app_name = os.path.splitext(os.path.basename(python_file))[0]
        app_dir = os.path.join("/storage/emulated/0/Download", app_name)
        os.makedirs(app_dir, exist_ok=True)
        
        # Copy Python file
        shutil.copy2(python_file, os.path.join(app_dir, "script.py"))
        
        # Create runner
        runner_path = os.path.join(app_dir, "run.py")
        with open(runner_path, 'w') as f:
            f.write('''import os
import sys
import subprocess

print("Running Python script...")
print("-" * 40)

try:
    # Get script path
    script_path = os.path.join(os.path.dirname(__file__), "script.py")
    
    # Run the script
    process = subprocess.run(
        [sys.executable, script_path],
        capture_output=True,
        text=True
    )
    
    # Show output
    if process.stdout:
        print("\\nOutput:")
        print(process.stdout)
    
    # Show errors
    if process.stderr:
        print("\\nErrors:")
        print(process.stderr)

except Exception as e:
    print(f"Error: {str(e)}")

print("\\n" + "-" * 40)
input("Press Enter to exit")
''')
        
        # Create shortcut
        shortcut_path = os.path.join("/storage/emulated/0/Download", f"{app_name}_app.py")
        with open(shortcut_path, 'w') as f:
            f.write(f'''import os
import sys
import subprocess

app_dir = "{app_dir}"
runner = os.path.join(app_dir, "run.py")
subprocess.run([sys.executable, runner])
''')
        
        print("\nSuccess! App created.")
        print(f"\nTo run your app:")
        print(f"1. Go to Downloads folder")
        print(f"2. Run {app_name}_app.py")
        
    except Exception as e:
        print(f"Error creating app: {str(e)}")

input("\nPress Enter to exit")