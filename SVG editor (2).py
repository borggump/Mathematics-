import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox, Frame, Button, Label
import os
import xml.dom.minidom as minidom

class SVGEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("SVG Viewer/Editor for Pydroid3")
        self.root.geometry("800x600")
        self.current_file = None
        self.svg_content = ""
        self.temp_html_path = os.path.join(os.getcwd(), "temp_svg_preview.html")
       
        # Set up UI
        self.setup_ui()
       
        # Initial message
        self.display_message("Welcome to SVG Viewer! Open an SVG file or paste SVG code.")
   
    def setup_ui(self):
        # Top frame for buttons
        top_frame = Frame(self.root)
        top_frame.pack(fill=tk.X, padx=5, pady=5)
       
        # Button bar - larger buttons for touch screens
        Button(top_frame, text="Open SVG", command=self.open_file, height=2).pack(side=tk.LEFT, padx=3)
        Button(top_frame, text="Save", command=self.save_file, height=2).pack(side=tk.LEFT, padx=3)
        Button(top_frame, text="Save As", command=self.save_as_file, height=2).pack(side=tk.LEFT, padx=3)
        Button(top_frame, text="View SVG", command=self.view_svg, height=2, bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=3)
        Button(top_frame, text="Format XML", command=self.format_xml, height=2).pack(side=tk.LEFT, padx=3)
       
        # Code editor
        editor_frame = Frame(self.root)
        editor_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
       
        Label(editor_frame, text="SVG Code").pack(anchor=tk.W)
        self.code_editor = scrolledtext.ScrolledText(editor_frame, wrap=tk.WORD)
        self.code_editor.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
       
        # Status bar
        self.status_bar = Label(self.root, text="Ready", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
   
    def open_file(self):
        try:
            file_path = filedialog.askopenfilename(filetypes=[("SVG files", "*.svg"), ("All files", "*.*")])
            if not file_path:
                return
           
            with open(file_path, 'r') as file:
                self.svg_content = file.read()
           
            self.current_file = file_path
            self.code_editor.delete(1.0, tk.END)
            self.code_editor.insert(tk.END, self.svg_content)
            self.display_message(f"Opened: {os.path.basename(file_path)}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file: {str(e)}")
   
    def save_file(self):
        if not self.current_file:
            self.save_as_file()
            return
       
        try:
            content = self.code_editor.get(1.0, tk.END)
            with open(self.current_file, 'w') as file:
                file.write(content)
            self.display_message(f"Saved to: {os.path.basename(self.current_file)}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not save file: {str(e)}")
   
    def save_as_file(self):
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".svg",
                filetypes=[("SVG files", "*.svg"), ("All files", "*.*")]
            )
            if not file_path:
                return
           
            content = self.code_editor.get(1.0, tk.END)
            with open(file_path, 'w') as file:
                file.write(content)
           
            self.current_file = file_path
            self.display_message(f"Saved as: {os.path.basename(file_path)}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not save file: {str(e)}")
   
    def format_xml(self):
        try:
            xml_content = self.code_editor.get(1.0, tk.END)
            dom = minidom.parseString(xml_content)
            pretty_xml = dom.toprettyxml(indent="    ")
           
            # Remove extra whitespace
            lines = pretty_xml.splitlines()
            non_empty_lines = [line for line in lines if line.strip()]
            pretty_xml = "\n".join(non_empty_lines)
           
            self.code_editor.delete(1.0, tk.END)
            self.code_editor.insert(tk.END, pretty_xml)
            self.display_message("XML formatted successfully")
        except Exception as e:
            self.display_message(f"Error formatting XML: {str(e)}", error=True)
   
    def view_svg(self):
        try:
            svg_code = self.code_editor.get(1.0, tk.END)
            if not svg_code.strip():
                self.display_message("No SVG code to view", error=True)
                return
           
            # Create a temporary HTML file to display the SVG
            with open(self.temp_html_path, 'w') as f:
                f.write("""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>SVG Preview</title>
                    <style>
                        body {
                            margin: 0;
                            padding: 0;
                            display: flex;
                            justify-content: center;
                            align-items: center;
                            min-height: 100vh;
                            background-color: #f0f0f0;
                        }
                        svg {
                            max-width: 100%;
                            max-height: 90vh;
                            border: 1px solid #ccc;
                            background-color: white;
                        }
                    </style>
                </head>
                <body>
                """)
                f.write(svg_code)
                f.write("""
                </body>
                </html>
                """)
           
            # Show a dialog with instructions for viewing the SVG
            messagebox.showinfo("View SVG",
                "A preview HTML file has been created at:\n\n" +
                self.temp_html_path + "\n\n" +
                "To view the SVG:\n" +
                "1. Open your Android browser\n" +
                "2. Navigate to this file\n" +
                "3. Or use 'Web Browser for Android' app to open this file directly"
            )
           
            self.display_message("Created HTML preview file for SVG")
        except Exception as e:
            self.display_message(f"Error creating preview: {str(e)}", error=True)
   
    def display_message(self, message, error=False):
        self.status_bar.config(text=message, fg="red" if error else "black")
   
    def __del__(self):
        # Clean up temporary file when application closes
        try:
            if os.path.exists(self.temp_html_path):
                os.remove(self.temp_html_path)
        except:
            pass

def main():
    root = tk.Tk()
    app = SVGEditor(root)
    root.mainloop()

if __name__ == "__main__":
    main()