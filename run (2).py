import os
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
        print("\nOutput:")
        print(process.stdout)
    
    # Show errors
    if process.stderr:
        print("\nErrors:")
        print(process.stderr)

except Exception as e:
    print(f"Error: {str(e)}")

print("\n" + "-" * 40)
input("Press Enter to exit")
