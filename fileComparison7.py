import tkinter as tk
from tkinter import ttk, messagebox
import os

class FileExplorerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Text File Comparison")
       
        # File paths
        self.file1_path = tk.StringVar()
        self.file2_path = tk.StringVar()
        self.current_file_target = None
        self.current_path = os.getcwd()  # Start with current directory
       
        # Create and pack the main container
        self.create_gui()
        self.update_file_list()
       
    def create_gui(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
       
        # Navigation Frame
        nav_frame = ttk.LabelFrame(main_frame, text="Navigation", padding="5")
        nav_frame.pack(fill=tk.X, padx=5, pady=5)
       
        # Current Path
        self.path_var = tk.StringVar()
        path_entry = ttk.Entry(nav_frame, textvariable=self.path_var, width=40)
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
       
        # Up Directory Button
        ttk.Button(nav_frame, text="Up Directory", command=self.go_up).pack(side=tk.RIGHT, padx=5)
       
        # Search Frame
        search_frame = ttk.LabelFrame(main_frame, text="Search", padding="5")
        search_frame.pack(fill=tk.X, padx=5, pady=5)
       
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.filter_files)
        ttk.Entry(search_frame, textvariable=self.search_var).pack(fill=tk.X, padx=5)
       
        # File Selection Frame
        select_frame = ttk.LabelFrame(main_frame, text="File Selection", padding="5")
        select_frame.pack(fill=tk.X, padx=5, pady=5)
       
        # File 1 Selection
        ttk.Label(select_frame, text="File 1:").pack(fill=tk.X, padx=5)
        ttk.Entry(select_frame, textvariable=self.file1_path, state='readonly').pack(fill=tk.X, padx=5)
        ttk.Button(select_frame, text="Select File 1", command=lambda: self.set_file_target(1)).pack(fill=tk.X, padx=5, pady=5)
       
        # File 2 Selection
        ttk.Label(select_frame, text="File 2:").pack(fill=tk.X, padx=5)
        ttk.Entry(select_frame, textvariable=self.file2_path, state='readonly').pack(fill=tk.X, padx=5)
        ttk.Button(select_frame, text="Select File 2", command=lambda: self.set_file_target(2)).pack(fill=tk.X, padx=5, pady=5)
       
        # Files List Frame
        list_frame = ttk.LabelFrame(main_frame, text="Files and Directories", padding="5")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
       
        # Listbox and Scrollbar
        self.file_listbox = tk.Listbox(list_frame, selectmode=tk.SINGLE, height=10)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.file_listbox.yview)
       
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_listbox.configure(yscrollcommand=scrollbar.set)
       
        # Action Buttons Frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
       
        ttk.Button(button_frame, text="Open Selected", command=self.open_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Compare Files", command=self.compare_files).pack(side=tk.RIGHT, padx=5)
       
        # Results Frame
        results_frame = ttk.LabelFrame(main_frame, text="Results", padding="5")
        results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
       
        self.results_text = tk.Text(results_frame, height=6, wrap=tk.WORD)
        self.results_text.pack(fill=tk.BOTH, expand=True)
       
    def update_file_list(self):
        self.file_listbox.delete(0, tk.END)
        self.path_var.set(self.current_path)
       
        # Add parent directory option
        self.file_listbox.insert(tk.END, "../ (Parent Directory)")
       
        try:
            # Add directories first
            for item in sorted(os.listdir(self.current_path)):
                full_path = os.path.join(self.current_path, item)
                if os.path.isdir(full_path):
                    self.file_listbox.insert(tk.END, f"📁 {item}")
                   
            # Then add .txt files
            for item in sorted(os.listdir(self.current_path)):
                full_path = os.path.join(self.current_path, item)
                if os.path.isfile(full_path) and item.lower().endswith('.txt'):
                    self.file_listbox.insert(tk.END, f"📄 {item}")
        except Exception as e:
            messagebox.showerror("Error", f"Cannot read directory: {str(e)}")
           
    def filter_files(self, *args):
        search_term = self.search_var.get().lower()
        self.update_file_list()  # Reset the list
       
        # Remove items that don't match the search
        for i in range(self.file_listbox.size()-1, -1, -1):
            item = self.file_listbox.get(i)
            if not (search_term in item.lower() or item == "../ (Parent Directory)"):
                self.file_listbox.delete(i)
               
    def go_up(self):
        parent = os.path.dirname(self.current_path)
        if parent != self.current_path:
            self.current_path = parent
            self.update_file_list()
           
    def open_selected(self):
        selection = self.file_listbox.curselection()
        if not selection:
            messagebox.showinfo("Selection", "Please select a file or directory first")
            return
           
        selected_item = self.file_listbox.get(selection[0])
       
        if selected_item == "../ (Parent Directory)":
            self.go_up()
            return
           
        # Remove emoji prefix and get clean name
        item_name = selected_item[2:] if selected_item.startswith(("📁", "📄")) else selected_item
        full_path = os.path.join(self.current_path, item_name)
       
        if os.path.isdir(full_path):
            self.current_path = full_path
            self.update_file_list()
        elif self.current_file_target and item_name.lower().endswith('.txt'):
            if self.current_file_target == 1:
                self.file1_path.set(full_path)
            else:
                self.file2_path.set(full_path)
            self.current_file_target = None
            messagebox.showinfo("Success", f"File {self.current_file_target} selected successfully!")
           
    def set_file_target(self, target):
        self.current_file_target = target
        messagebox.showinfo("Select File",
                          f"Please select File {target} from the list and click 'Open Selected'")
       
    def compare_files(self):
        file1 = self.file1_path.get()
        file2 = self.file2_path.get()
       
        if not file1 or not file2:
            messagebox.showerror("Error", "Please select both files")
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
            output_path = os.path.join(self.current_path, output_file)
           
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
    app = FileExplorerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()