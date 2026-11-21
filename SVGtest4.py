from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from kivy.metrics import dp
from kivy.graphics import Rectangle, Color, Line
from kivy.core.text import Label as CoreLabel
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
        self.padding = 50

    def convert_point(self, x, y, svg_height):
        """Convert SVG coordinates to screen coordinates"""
        # Convert coordinates and flip Y axis
        screen_x = x + self.padding
        screen_y = self.height - (y + self.padding)
        return screen_x, screen_y

    def load_svg(self, filepath):
        try:
            self.shapes = []
            tree = ET.parse(filepath)
            root = tree.getroot()
            
            # Get SVG dimensions
            viewbox = root.get('viewBox', '0 0 800 1000').split()
            svg_width = float(viewbox[2])
            svg_height = float(viewbox[3])
            
            # Calculate scale to fit window
            scale_x = (self.width - 2 * self.padding) / svg_width
            scale_y = (self.height - 2 * self.padding) / svg_height
            scale = min(scale_x, scale_y)
            
            # Process all rects
            for rect in root.findall('.//{*}rect'):
                x = float(rect.get('x', 0)) * scale
                y = float(rect.get('y', 0)) * scale
                width = float(rect.get('width', 0)) * scale
                height = float(rect.get('height', 0)) * scale
                
                # Convert coordinates
                screen_x, screen_y = self.convert_point(x, y, svg_height * scale)
                
                self.shapes.append({
                    'type': 'rect',
                    'x': screen_x,
                    'y': screen_y - height,  # Adjust for height
                    'width': width,
                    'height': height
                })
                
            # Process all text elements
            for text in root.findall('.//{*}text'):
                x = float(text.get('x', 0)) * scale
                y = float(text.get('y', 0)) * scale
                content = text.text or ''
                font_size = float(text.get('font-size', '12')) * scale * 0.5
                
                # Convert coordinates
                screen_x, screen_y = self.convert_point(x, y, svg_height * scale)
                
                self.shapes.append({
                    'type': 'text',
                    'x': screen_x,
                    'y': screen_y,
                    'text': content,
                    'font_size': font_size
                })
            
            self.redraw()
            return True
            
        except Exception as e:
            print(f"Error loading SVG: {e}")
            return False

    def redraw(self, *args):
        self.canvas.clear()
        with self.canvas:
            # White background
            Color(1, 1, 1, 1)
            Rectangle(pos=self.pos, size=self.size)
            
            # Draw shapes
            for shape in self.shapes:
                Color(0, 0, 0, 1)  # Black color
                
                if shape['type'] == 'rect':
                    Rectangle(
                        pos=(shape['x'], shape['y']),
                        size=(shape['width'], shape['height'])
                    )
                    
                elif shape['type'] == 'text':
                    label = CoreLabel(
                        text=shape['text'],
                        font_size=shape['font_size']
                    )
                    label.refresh()
                    
                    Rectangle(
                        pos=(shape['x'], shape['y'] - label.texture.height),
                        size=label.texture.size,
                        texture=label.texture
                    )

class SVGViewer(App):
    def build(self):
        layout = BoxLayout(orientation='vertical', spacing=dp(5))
        
        # Add load button
        toolbar = BoxLayout(size_hint_y=None, height=dp(60))
        load_btn = SimpleButton(
            text='Load SVG',
            on_press=self.show_load_dialog
        )
        toolbar.add_widget(load_btn)
        
        # Create drawing widget
        self.drawing = DrawingWidget()
        
        # Add widgets to layout
        layout.add_widget(toolbar)
        layout.add_widget(self.drawing)
        
        return layout

    def show_load_dialog(self, instance):
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
            if file_chooser.selection:
                self.drawing.load_svg(file_chooser.selection[0])
            popup.dismiss()
        
        load_button.bind(on_press=load)
        cancel_button.bind(on_press=popup.dismiss)
        
        popup.open()

if __name__ == '__main__':
    SVGViewer().run()