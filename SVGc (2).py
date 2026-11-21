from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from kivy.metrics import dp
from kivy.graphics import Rectangle, Color, Line
import os
import xml.etree.ElementTree as ET

class SimpleButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (dp(100), dp(50))
        self.background_normal = ''
        self.background_color = (0.2, 0.6, 0.8, 1)

class DrawingWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(size=self.redraw)
        self.shapes = []

    def redraw(self, *args):
        print("Redrawing canvas")  # Debug print
        self.canvas.clear()
        with self.canvas:
            # White background
            Color(1, 1, 1, 1)
            Rectangle(pos=self.pos, size=self.size)
            
            # Draw shapes
            for shape in self.shapes:
                Color(*shape.get('color', (0, 0, 0, 1)))
                if 'points' in shape:
                    Line(points=shape['points'])

    def load_svg(self, filepath):
        print(f"Loading file: {filepath}")  # Debug print
        try:
            # Clear current shapes
            self.shapes = []
            
            # Load and parse SVG
            tree = ET.parse(filepath)
            root = tree.getroot()
            print("Parsed SVG file")  # Debug print
            
            # Get SVG dimensions from viewBox
            viewbox = root.get('viewBox', '0 0 100 100').split()
            width = float(viewbox[2])
            height = float(viewbox[3])
            print(f"ViewBox: {width} x {height}")  # Debug print
            
            # Calculate scale factor
            scale_x = self.width / width
            scale_y = self.height / height
            scale = min(scale_x, scale_y)
            print(f"Scale factor: {scale}")  # Debug print
            
            # Process elements
            for elem in root.iter():
                tag = elem.tag.split('}')[-1]
                print(f"Processing element: {tag}")  # Debug print
                
                if tag == 'path':
                    d = elem.get('d', '')
                    if d:
                        # Simple straight-line path parsing
                        points = []
                        for cmd in d.split():
                            try:
                                x, y = map(float, cmd.split(','))
                                points.extend([x * scale, self.height - (y * scale)])
                            except:
                                continue
                        
                        if points:
                            self.shapes.append({
                                'points': points,
                                'color': (0, 0, 0, 1)
                            })
                
                elif tag == 'rect':
                    try:
                        x = float(elem.get('x', 0)) * scale
                        y = float(elem.get('y', 0)) * scale
                        w = float(elem.get('width', 0)) * scale
                        h = float(elem.get('height', 0)) * scale
                        
                        # Convert rectangle to points
                        points = [x, y, x+w, y, x+w, y+h, x, y+h, x, y]
                        self.shapes.append({
                            'points': points,
                            'color': (0, 0, 0, 1)
                        })
                    except ValueError as e:
                        print(f"Error processing rect: {e}")  # Debug print
                        continue

            print(f"Loaded {len(self.shapes)} shapes")  # Debug print
            self.redraw()
            return True
            
        except Exception as e:
            print(f"Error loading SVG: {e}")  # Debug print
            return False

class SVGViewer(App):
    def build(self):
        print("Building app")  # Debug print
        layout = BoxLayout(orientation='vertical', spacing=dp(5))
        
        # Create toolbar
        toolbar = BoxLayout(size_hint_y=None, height=dp(60))
        
        # Create load button
        self.load_btn = SimpleButton(
            text='Load SVG',
            on_press=self.show_load_dialog
        )
        toolbar.add_widget(self.load_btn)
        
        # Create drawing widget
        self.drawing = DrawingWidget()
        
        # Add widgets to layout
        layout.add_widget(toolbar)
        layout.add_widget(self.drawing)
        
        print("App built successfully")  # Debug print
        return layout
    
    def show_load_dialog(self, instance):
        print("Showing file dialog")  # Debug print
        content = BoxLayout(orientation='vertical')
        
        # File chooser
        self.file_chooser = FileChooserListView(
            path='/storage/emulated/0/Download',
            filters=['*.svg']
        )
        
        # Buttons
        buttons = BoxLayout(size_hint_y=None, height=dp(50))
        load_button = SimpleButton(text='Load')
        cancel_button = SimpleButton(text='Cancel')
        
        # Add buttons to layout
        buttons.add_widget(load_button)
        buttons.add_widget(cancel_button)
        
        # Add widgets to content
        content.add_widget(self.file_chooser)
        content.add_widget(buttons)
        
        # Create popup
        self.popup = Popup(
            title='Load SVG File',
            content=content,
            size_hint=(0.9, 0.9)
        )
        
        # Button bindings
        def load(instance):
            print("Load button pressed")  # Debug print
            if self.file_chooser.selection:
                print(f"Selected file: {self.file_chooser.selection[0]}")  # Debug print
                self.drawing.load_svg(self.file_chooser.selection[0])
            self.popup.dismiss()
        
        def cancel(instance):
            print("Cancel button pressed")  # Debug print
            self.popup.dismiss()
        
        load_button.bind(on_press=load)
        cancel_button.bind(on_press=cancel)
        
        # Show popup
        self.popup.open()
        print("File dialog shown")  # Debug print

if __name__ == '__main__':
    SVGViewer().run()
    