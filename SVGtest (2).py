from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
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
        self.shapes = []
        self.bind(size=self.redraw)
        self.bind(pos=self.redraw)

    def load_svg(self, filepath):
        print(f"Loading SVG file: {filepath}")
        try:
            self.shapes = []
            tree = ET.parse(filepath)
            root = tree.getroot()
            print("Successfully parsed SVG file")
            
            # Get dimensions from viewBox
            viewbox = root.get('viewBox', '0 0 100 100').split()
            svg_width = float(viewbox[2])
            svg_height = float(viewbox[3])
            print(f"SVG dimensions: {svg_width} x {svg_height}")
            
            # Calculate scale factor
            scale_x = self.width / svg_width
            scale_y = self.height / svg_height
            scale = min(scale_x, scale_y)
            print(f"Scale factor: {scale}")
            
            # Find all rect elements
            for rect in root.findall('.//{*}rect'):
                try:
                    # Get rectangle attributes
                    x = float(rect.get('x', 0))
                    y = float(rect.get('y', 0))
                    width = float(rect.get('width', 0))
                    height = float(rect.get('height', 0))
                    fill = rect.get('fill', 'black')
                    
                    print(f"Found rectangle: x={x}, y={y}, w={width}, h={height}, fill={fill}")
                    
                    # Scale coordinates
                    screen_x = x * scale
                    screen_y = self.height - (y + height) * scale
                    screen_width = width * scale
                    screen_height = height * scale
                    
                    print(f"Scaled rectangle: x={screen_x}, y={screen_y}, w={screen_width}, h={screen_height}")
                    
                    # Add to shapes list
                    self.shapes.append({
                        'type': 'rect',
                        'x': screen_x,
                        'y': screen_y,
                        'width': screen_width,
                        'height': screen_height,
                        'color': (0, 0, 0, 1)  # Black
                    })
                    print("Added rectangle to shapes list")
                    
                except ValueError as e:
                    print(f"Error processing rectangle: {e}")
                    continue
            
            print(f"Total shapes found: {len(self.shapes)}")
            self.redraw()
            return True
            
        except Exception as e:
            print(f"Error loading SVG: {e}")
            return False

    def redraw(self, *args):
        print("Redrawing canvas")
        self.canvas.clear()
        with self.canvas:
            # Draw white background
            print("Drawing background")
            Color(1, 1, 1, 1)
            Rectangle(pos=self.pos, size=self.size)
            
            # Draw shapes
            print(f"Drawing {len(self.shapes)} shapes")
            for shape in self.shapes:
                if shape['type'] == 'rect':
                    print(f"Drawing rectangle at {shape['x']}, {shape['y']}")
                    Color(*shape['color'])
                    Rectangle(
                        pos=(shape['x'], shape['y']),
                        size=(shape['width'], shape['height'])
                    )
                    print(f"Rectangle drawn: pos=({shape['x']}, {shape['y']}), size=({shape['width']}, {shape['height']})")
        print("Canvas updated")

class SVGViewer(App):
    def build(self):
        print("Building app")
        layout = BoxLayout(orientation='vertical', spacing=dp(5))
        
        toolbar = BoxLayout(size_hint_y=None, height=dp(60))
        self.load_btn = SimpleButton(
            text='Load SVG',
            on_press=self.show_load_dialog
        )
        toolbar.add_widget(self.load_btn)
        
        self.drawing = DrawingWidget()
        
        layout.add_widget(toolbar)
        layout.add_widget(self.drawing)
        
        print("App built successfully")
        return layout

    def show_load_dialog(self, instance):
        print("Opening file dialog")
        content = BoxLayout(orientation='vertical')
        file_chooser = FileChooserListView(
            path='/storage/emulated/0/Download',
            filters=['*.svg']
        )
        
        buttons = BoxLayout(size_hint_y=None, height=dp(50))
        load_button = SimpleButton(text='Load')
        cancel_button = SimpleButton(text='Cancel')
        
        buttons.add_widget(load_button)
        buttons.add_widget(cancel_button)
        
        content.add_widget(file_chooser)
        content.add_widget(buttons)
        
        popup = Popup(
            title='Load SVG File',
            content=content,
            size_hint=(0.9, 0.9)
        )
        
        def load(instance):
            print("Load button pressed")
            if file_chooser.selection:
                print(f"Selected file: {file_chooser.selection[0]}")
                self.drawing.load_svg(file_chooser.selection[0])
            popup.dismiss()
            
        load_button.bind(on_press=load)
        cancel_button.bind(on_press=popup.dismiss)
        
        popup.open()
        print("File dialog shown")

if __name__ == '__main__':
    print("Starting app")
    SVGViewer().run()
    