import subprocess
import sys
import os

app_dir = "/storage/emulated/0/Download/My_Python_App"
subprocess.run([sys.executable, os.path.join(app_dir, "run_app.py")])
