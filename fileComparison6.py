import tkinter as tk
from tkinter import ttk, messagebox
import os

class FileTreeGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Text File Comparison Tool")
        self.root.geometry("800x600")
       
        # File paths
        self.file1_path = tk.StringVar()
        self.file2_path = tk.StringVar()
        self.current_file_target = None  # Tracks which file we're selecting (1 or 2)
       
        self.create_gui()
        self.load_initial_directory()
       
    def create_gui(self):
        # Main container
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True)
       
        # Left side - File Browser
        left_frame = ttk.Frame(main_paned)
        main_paned.add(left_frame)
       
        # Directory entry and browse frame
        dir_frame = ttk.Frame(left_frame)
        dir_frame.pack(fill=tk.X, padx=5, pady=5)
       
        self.dir_entry = ttk.Entry(dir_frame)
        self.dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
       
        ttk.Button(dir_frame, text="↑", width=3,
                   command=self.go_up_directory).pack(side=tk.LEFT)
       
        # Search frame
        search_frame = ttk.Frame(left_frame)
        search_frame.pack(fill=tk.X, padx=5, pady=2)
       
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.filter_tree)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(fill=tk.X)
       
        # Create tree view
        self.tree = ttk.Treeview(left_frame, selectmode="browse")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
       
        # Tree scrollbar
        tree_scroll = ttk.Scrollbar(left_frame, orient="vertical",
                                  command=self.tree.yview)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=tree_scroll.set)
       
        # Right side - Selection and Results
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame)
       
        # File selection frame
        selection_frame = ttk.LabelFrame(right_frame, text="Selected Files", padding=5)
        selection_frame.pack(fill=tk.X, padx=5, pady=5)
       
        # File 1 selection
        f1_frame = ttk.Frame(selection_frame)
        f1_frame.pack(fill=tk.X, pady=2)
        ttk.Label(f1_frame, text="File 1:").pack(side=tk.LEFT)
        ttk.Entry(f1_frame, textvariable=self.file1_path, state='readonly').pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(f1_frame, text="Select",
                   command=lambda: self.set_file_target(1)).pack(side=tk.LEFT)
       
        # File 2 selection
        f2_frame = ttk.Frame(selection_frame)
        f2_frame.pack(fill=tk.X, pady=2)
        ttk.Label(f2_frame, text="File 2:").pack(side=tk.LEFT)
        ttk.Entry(f2_frame, textvariable=self.file2_path, state='readonly').pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(f2_frame, text="Select",
                   command=lambda: self.set_file_target(2)).pack(side=tk.LEFT)
       
        # Compare button
        ttk.Button(right_frame, text="Compare Files",
                   command=self.compare_files).pack(pady=10)
       
        # Results frame
        results_frame = ttk.LabelFrame(right_frame, text="Results")
        results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
       
        # Results text widget
        self.results_text = tk.Text(results_frame, wrap=tk.WORD)
        self.results_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
       
        # Results scrollbar
        results_scroll = ttk.Scrollbar(results_frame, orient="vertical",
                                     command=self.results_text.yview)
        results_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_text.configure(yscrollcommand=results_scroll.set)
       
        # Bind events
        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)
        self.tree.bind('<Double-1>', self.on_tree_double_click)
        self.dir_entry.bind('<Return>', self.on_dir_entry_change)
       
    def load_initial_directory(self):
        # Start from the current directory
        current_dir = os.getcwd()
        self.dir_entry.insert(0, current_dir)
        self.populate_tree(current_dir)
       
    def populate_tree(self, path):
        # Clear the tree
        for item in self.tree.get_children():
            self.tree.delete(item)
           
        # Add back button if not in root
        parent_dir = os.path.dirname(path)
        if path != parent_dir:
            self.tree.insert("", "end", text="..", values=(parent_dir, "directory"),
                           image="")
           
        try:
            # List directory contents
            for item in os.listdir(path):
                full_path = os.path.join(path, item)
                try:
                    is_dir = os.path.isdir(full_path)
                    if is_dir or item.lower().endswith('.txt'):
                        item_type = "directory" if is_dir else "file"
                        self.tree.insert("", "end", text=item, values=(full_path, item_type))
                except Exception:
                    continue
        except Exception as e:
            messagebox.showerror("Error", f"Could not load directory: {str(e)}")
           
    def filter_tree(self, *args):
        search_term = self.search_var.get().lower()
        current_dir = self.dir_entry.get()
       
        # Clear the tree
        for item in self.tree.get_children():
            self.tree.delete(item)
           
        try:
            # Add filtered items
            for item in os.listdir(current_dir):
                if search_term in item.lower():
                    full_path = os.path.join(current_dir, item)
                    try:
                        is_dir = os.path.isdir(full_path)
                        if is_dir or item.lower().endswith('.txt'):
                            item_type = "directory" if is_dir else "file"
                            self.tree.insert("", "end", text=item,
                                           values=(full_path, item_type))
                    except Exception:
                        continue
        except Exception as e:
            messagebox.showerror("Error", f"Could not filter directory: {str(e)}")
           
    def go_up_directory(self):
        current = self.dir_entry.get()
        parent = os.path.dirname(current)
        if parent != current:
            self.dir_entry.delete(0, tk.END)
            self.dir_entry.insert(0, parent)
            self.populate_tree(parent)
           
    def on_dir_entry_change(self, event):
        new_path = self.dir_entry.get()
        if os.path.exists(new_path) and os.path.isdir(new_path):
            self.populate_tree(new_path)
        else:
            messagebox.showerror("Error", "Invalid directory path")
           
    def on_tree_select(self, event):
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            path = item['values'][0]
            item_type = item['values'][1]
           
            if item_type == "file" and self.current_file_target:
                if self.current_file_target == 1:
                    self.file1_path.set(path)
                else:
                    self.file2_path.set(path)
                self.current_file_target = None  # Reset target
               
    def on_tree_double_click(self, event):
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            path = item['values'][0]
            item_type = item['values'][1]
           
            if item_type == "directory":
                self.dir_entry.delete(0, tk.END)
                self.dir_entry.insert(0, path)
                self.populate_tree(path)
               
    def set_file_target(self, target):
        self.current_file_target = target
        messagebox.showinfo("Select File",
                          f"Please select File {target} from the file browser")
       
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
            messagebox.showerror("Error", "Please select both files")
            return
           
        if not all(self.is_text_file(f) for f in [file1, file2]):
            messagebox.showerror("Error", "Both files must be valid text files")
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
           
            messagebox.showinfo("Success",
                              f"Comparison complete!\nOutput saved to: {output_file}")
                             
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

def main():
    root = tk.Tk()
    app = FileTreeGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()