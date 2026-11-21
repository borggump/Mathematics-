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
        self.margin = 20
        
    def transform_coords(self, x, y, w, h, scale):
        """Transform SVG coordinates to screen coordinates"""
        # Apply margin and scaling
        screen_x = self.margin + x * scale
        screen_y = self.margin + y * scale
        screen_w = w * scale
        screen_h = h * scale
        
        # Flip y-coordinate (SVG has origin at top-left, Kivy at bottom-left)
        screen_y = self.height - screen_y - screen_h
        
        return screen_x, screen_y, screen_w, screen_h

    def load_svg(self, filepath):
        try:
            self.shapes = []
            tree = ET.parse(filepath)
            root = tree.getroot()
            
            # Parse viewBox
            viewbox = root.get('viewBox', '0 0 100 100').split()
            svg_width = float(viewbox[2])
            svg_height = float(viewbox[3])
            
            # Calculate scale factor to fit window with margins
            available_width = self.width - 2 * self.margin
            available_height = self.height - 2 * self.margin
            scale_x = available_width / svg_width
            scale_y = available_height / svg_height
            scale = min(scale_x, scale_y) * 0.9  # Add some additional padding
            
            def process_element(element, dx=0, dy=0):
                # Get any transform
                transform = element.get('transform', '')
                if 'translate' in transform:
                    import re
                    translate = re.search(r'translate\(([-\d.]+)[,\s]*([-\d.]+)?\)', transform)
                    if translate:
                        dx += float(translate.group(1))
                        dy += float(translate.group(2) if translate.group(2) else 0)
                
                tag = element.tag.split('}')[-1]
                if tag == 'rect':
                    try:
                        x = float(element.get('x', 0)) + dx
                        y = float(element.get('y', 0)) + dy
                        w = float(element.get('width', 0))
                        h = float(element.get('height', 0))
                        
                        # Transform coordinates
                        sx, sy, sw, sh = self.transform_coords(x, y, w, h, scale)
                        
                        self.shapes.append({
                            'type': 'rect',
                            'pos': (sx, sy),
                            'size': (sw, sh),
                            'color': (0, 0, 0, 1)  # Default black
                        })
                    except ValueError:
                        pass
                
                # Process child elements with accumulated transform
                for child in element:
                    process_element(child, dx, dy)
            
            # Process all elements
            process_element(root)
            self.redraw()
            return True
            
        except Exception as e:
            print(f"Error loading SVG: {e}")
            return False

    def redraw(self, *args):
        self.canvas.clear()
        with self.canvas:
            # Draw white background
            Color(1, 1, 1, 1)
            Rectangle(pos=self.pos, size=self.size)
            
            # Draw border for visual reference
            Color(0.9, 0.9, 0.9, 1)
            Line(rectangle=(self.margin, self.margin, 
                          self.width - 2*self.margin, 
                          self.height - 2*self.margin))
            
            # Draw shapes
            for shape in self.shapes:
                Color(*shape['color'])
                if shape['type'] == 'rect':
                    Rectangle(
                        pos=shape['pos'],
                        size=shape['size']
                    )

class SVGViewer(App):
    def build(self):
        layout = BoxLayout(orientation='vertical', spacing=dp(5))
        
        toolbar = BoxLayout(size_hint_y=None, height=dp(60))
        self.load_btn = SimpleButton(text='Load SVG', on_press=self.show_load_dialog)
        toolbar.add_widget(self.load_btn)
        
        self.drawing = DrawingWidget()
        
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
    