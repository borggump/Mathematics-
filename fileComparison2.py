        self.results_frame.rowconfigure(0, weight=1)

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
        except (UnicodeDecodeError, Exception):
            return False

    def compare_files(self):
        file1 = self.file1_path.get()
        file2 = self.file2_path.get()

        # Validate file selection
        if not file1 or not file2:
            messagebox.showerror("Error", "Please select both files.")
            return

        # Validate text files
        if not all(self.is_text_file(f) for f in [file1, file2]):
            messagebox.showerror("Error", "Both files must be valid text (.txt) files")
            return

        try:
            # Read and process files
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

            # Write output file
            with open(output_path, 'w', encoding='utf-8', newline='\n') as f_out:
                sorted_lines = sorted(unique_lines, key=str.lower)
                f_out.write('\n'.join(sorted_lines))
                f_out.write('\n')

            # Display results
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, "Comparison completed successfully!\n\n")
            self.results_text.insert(tk.END, f"Results:\n")
            self.results_text.insert(tk.END, f"- First file line count: {len(file1_content)}\n")
            self.results_text.insert(tk.END, f"- Second file line count: {len(file2_content)}\n")
            self.results_text.insert(tk.END, f"- Unique lines found: {len(unique_lines)}\n")
            self.results_text.insert(tk.END, f"- Output saved to: {output_file}\n")

            # Show success message
            messagebox.showinfo("Success", f"Comparison complete!\nOutput saved to: {output_file}")

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

def main():
    root = tk.Tk()
    app = TextFileComparisonGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()