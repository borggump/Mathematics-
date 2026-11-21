import os
import sys
import subprocess

app_dir = "/storage/emulated/0/Download/dragonfractal"
runner = os.path.join(app_dir, "run.py")
subprocess.run([sys.executable, runner])
