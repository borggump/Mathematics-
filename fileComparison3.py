import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os

class TextFileComparisonGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Text File Comparison Tool")
        self.root.geometry("600x400")
        self.file1_path = tk.StringVar()
        self.file2_path = tk.StringVar()
        self.create_gui()
       
    def create_gui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
       
        # File 1 frame
        f1_frame = ttk.Frame(main_frame)
        f1_frame.pack(fill=tk.X, pady=5)
        ttk.Label(f1_frame, text="First Text File:").pack(side=tk.LEFT)
        ttk.Entry(f1_frame, textvariable=self.file1_path, width=50).pack(side=tk.LEFT, padx=5)
        ttk.Button(f1_frame, text="Browse", command=lambda: self.browse_file(1)).pack(side=tk.LEFT)
       
        # File 2 frame
        f2_frame = ttk.Frame(main_frame)
        f2_frame.pack(fill=tk.X, pady=5)
        ttk.Label(f2_frame, text="Second Text File:").pack(side=tk.LEFT)
        ttk.Entry(f2_frame, textvariable=self.file2_path, width=50).pack(side=tk.LEFT, padx=5)
        ttk.Button(f2_frame, text="Browse", command=lambda: self.browse_file(2)).pack(side=tk.LEFT)
       
        # Compare button
        ttk.Button(main_frame, text="Compare Files", command=self.compare_files).pack(pady=20)
       
        # Results frame
        results_frame = ttk.LabelFrame(main_frame, text="Results", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True, pady=5)
       
        # Results text
        self.results_text = tk.Text(results_frame, height=10, width=60, wrap=tk.WORD)
        self.results_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
       
        # Scrollbar
        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.results_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_text.configure(yscrollcommand=scrollbar.set)
   
    def browse_file(self, file_num):
        filename = filedialog.askopenfilename(
            title=f"Select Text File {file_num}",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            if file_num == 1:
                self.file1_path.set(filename)
            else:
                self.file2_path.set(filename)
   
    def is_text_file(self, filename):
        if not filename.lower().endswith('.txt'):
            return False
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                file.readline()
            return True
        except:
            return False
   
    def compare_files(self):
        file1 = self.file1_path.get()
        file2 = self.file2_path.get()
       
        if not file1 or not file2:
            messagebox.showerror("Error", "Please select both files.")
            return
           
        if not all(self.is_text_file(f) for f in [file1, file2]):
            messagebox.showerror("Error", "Both files must be valid text (.txt) files")
            return
           
        try:
            # Read files
            with open(file1, 'r', encoding='utf-8') as f1:
                file1_content = set(line.strip() for line in f1 if line.strip())
            with open(file2, 'r', encoding='utf-8') as f2:
                file2_content = set(line.strip() for line in f2 if line.strip())
           
            # Find unique lines
            unique_lines = file1_content.symmetric_difference(file2_content)
           
            # Create output filename
            base_name1 = os.path.splitext(os.path.basename(file1))[0]
            base_name2 = os.path.splitext(os.path.basename(file2))[0]
            output_file = f"{base_name1}_vs_{base_name2}_unique.txt"
            output_path = os.path.join(os.path.dirname(file1), output_file)
           
            # Write output
            with open(output_path, 'w', encoding='utf-8', newline='\n') as f_out:
                sorted_lines = sorted(unique_lines, key=str.lower)
                f_out.write('\n'.join(sorted_lines))
                f_out.write('\n')
           
            # Show results
            self.results_text.delete(1.0, tk.END)
            results = [
                "Comparison completed successfully!\n",
                "Results:",
                f"- First file line count: {len(file1_content)}",
                f"- Second file line count: {len(file2_content)}",
                f"- Unique lines found: {len(unique_lines)}",
                f"- Output saved to: {output_file}"
            ]
            self.results_text.insert(tk.END, '\n'.join(results))
           
            messagebox.showinfo("Success", f"Comparison complete!\nOutput saved to: {output_file}")
           
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

def main():
    root = tk.Tk()
    app = TextFileComparisonGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()