import tkinter as tk
from tkinter import scrolledtext
import subprocess
import sys
import os

class AppRunner:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Python App Runner")
        self.setup_gui()

    def setup_gui(self):
        self.window.geometry("400x600")
        run_button = tk.Button(
            self.window,
            text="Run Script",
            command=self.run_script,
            bg="#4CAF50",
            fg="white",
            pady=10
        )
        run_button.pack(fill="x", padx=20, pady=10)
        self.output = scrolledtext.ScrolledText(
            self.window,
            width=40,
            height=20
        )
        self.output.pack(padx=20, pady=10, fill="both", expand=True)
        clear_button = tk.Button(
            self.window,
            text="Clear Output",
            command=self.clear_output,
            bg="#2196F3",
            fg="white",
            pady=5
        )
        clear_button.pack(fill="x", padx=20, pady=10)

    def run_script(self):
        self.output.delete(1.0, "end")
        self.output.insert("end", "Running script...\n")
        try:
            script_path = os.path.join(os.path.dirname(__file__), "script.py")
            process = subprocess.Popen(
                [sys.executable, script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate()
            if stdout:
                self.output.insert("end", stdout + "\n")
            if stderr:
                self.output.insert("end", "Errors:\n" + stderr + "\n")
            self.output.insert("end", "Script completed!\n")
        except Exception as e:
            self.output.insert("end", f"Error: {str(e)}\n")
        self.output.see("end")

    def clear_output(self):
        self.output.delete(1.0, "end")

    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    app = AppRunner()
    app.run()
