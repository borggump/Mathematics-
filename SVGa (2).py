from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from kivy.core.window import Window
from kivy.core.text import Label as CoreLabel
from kivy.metrics import dp
from kivy.graphics import Rectangle, Color, Line, Ellipse, PopMatrix, PushMatrix, Rotate, Translate
from kivy.clock import Clock
import os
import xml.etree.ElementTree as ET
import re
from math import cos, sin, pi

class SimpleButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (dp(100), dp(50))
        self.background_normal = ''
        self.background_color = (0.2, 0.6, 0.8, 1)

class SVGDrawingWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.shapes = []
        self.bind(size=self.redraw)
        self.bind(pos=self.redraw)
        self.scale_factor = 1.0
        self.margin = 20

    def flip_y(self, y):
        """Flip y coordinate from SVG to Kivy coordinate system"""
        vb_height = self.vb_height if hasattr(self, 'vb_height') else 1000
        return vb_height - y

    def parse_color(self, color_str):
        if not color_str or color_str == 'none':
            return None
            
        try:
            if color_str.startswith('#'):
                if len(color_str) == 4:  # #RGB format
                    r = int(color_str[1] * 2, 16) / 255
                    g = int(color_str[2] * 2, 16) / 255
                    b = int(color_str[3] * 2, 16) / 255
                    return (r, g, b, 1)
                else:  # #RRGGBB format
                    r = int(color_str[1:3], 16) / 255
                    g = int(color_str[3:5], 16) / 255
                    b = int(color_str[5:7], 16) / 255
                    return (r, g, b, 1)
                    
            elif color_str.startswith('rgb'):
                nums = re.findall(r'\d+', color_str)
                if len(nums) >= 3:
                    return (int(nums[0])/255.0, int(nums[1])/255.0, int(nums[2])/255.0, 1)
                    
            else:
                colors = {
                    'black': (0, 0, 0, 1),
                    'white': (1, 1, 1, 1),
                    'red': (1, 0, 0, 1),
                    'green': (0, 1, 0, 1),
                    'blue': (0, 0, 1, 1),
                    'yellow': (1, 1, 0, 1)
                }
                return colors.get(color_str.lower(), (0, 0, 0, 1))
        except:
            return (0, 0, 0, 1)

    def load_svg(self, filepath):
        try:
            self.shapes = []
            tree = ET.parse(filepath)
            root = tree.getroot()
            
            # Parse viewBox
            viewbox = root.get('viewBox', '0 0 800 1000').split()
            self.vb_width = float(viewbox[2])
            self.vb_height = float(viewbox[3])
            
            # Calculate scaling
            width_scale = (self.width - 2 * self.margin) / self.vb_width
            height_scale = (self.height - 2 * self.margin) / self.vb_height
            self.scale_factor = min(width_scale, height_scale)
            
            def process_element(element, transform=(0, 0)):
                curr_transform = list(transform)
                
                # Handle transforms
                if 'transform' in element.attrib:
                    transform_str = element.get('transform')
                    translate = re.search(r'translate\(([-\d.]+)[,\s]*([-\d.]+)?\)', transform_str)
                    if translate:
                        curr_transform[0] += float(translate.group(1))
                        curr_transform[1] += float(translate.group(2) if translate.group(2) else 0)
                
                tag = element.tag.split('}')[-1]
                
                if tag == 'path':
                    path_data = self.parse_path(element.get('d', ''))
                    if path_data:
                        # Transform and flip points
                        points = []
                        for i in range(0, len(path_data), 2):
                            x = path_data[i] + curr_transform[0]
                            y = self.flip_y(path_data[i+1] + curr_transform[1])
                            points.extend([x, y])
                            
                        self.shapes.append({
                            'type': 'path',
                            'points': points,
                            'stroke': self.parse_color(element.get('stroke', 'black')),
                            'fill': self.parse_color(element.get('fill')),
                            'stroke_width': float(element.get('stroke-width', '1'))
                        })
                        
                elif tag == 'rect':
                    x = float(element.get('x', 0)) + curr_transform[0]
                    y = float(element.get('y', 0)) + curr_transform[1]
                    width = float(element.get('width', 0))
                    height = float(element.get('height', 0))
                    
                    # Flip y-coordinate and adjust for height
                    y = self.flip_y(y + height)
                    
                    self.shapes.append({
                        'type': 'rect',
                        'x': x,
                        'y': y,
                        'width': width,
                        'height': height,
                        'stroke': self.parse_color(element.get('stroke', 'black')),
                        'fill': self.parse_color(element.get('fill')),
                        'stroke_width': float(element.get('stroke-width', '1'))
                    })
                    
                elif tag == 'text':
                    x = float(element.get('x', 0)) + curr_transform[0]
                    y = float(element.get('y', 0)) + curr_transform[1]
                    
                    # Flip y-coordinate
                    y = self.flip_y(y)
                    
                    self.shapes.append({
                        'type': 'text',
                        'x': x,
                        'y': y,
                        'text': element.text or '',
                        'font_size': float(element.get('font-size', '12')),
                        'fill': self.parse_color(element.get('fill', 'black')),
                        'text_anchor': element.get('text-anchor', 'start'),
                        'transform': curr_transform
                    })
                
                for child in element:
                    process_element(child, curr_transform)
            
            process_element(root)
            self.redraw()
            return True
            
        except Exception as e:
            print(f"Error loading SVG: {e}")
            return False

    def parse_path(self, d):
        if not d:
            return []
            
        points = []
        command_pattern = r'([MmLlHhVvCcSsZz])|([-+]?\d*\.?\d+)'
        commands = re.findall(command_pattern, d)
        
        current_x = 0
        current_y = 0
        subpath_start = (0, 0)
        command = None
        values = []
        
        for cmd, num in commands:
            if cmd:
                command = cmd
                values = []
            elif num:
                values.append(float(num))
                
                if command in 'Mm' and len(values) == 2:
                    x, y = values
                    if command == 'm':
                        x += current_x
                        y += current_y
                    current_x, current_y = x, y
                    subpath_start = (x, y)
                    points.extend([x, y])
                    values = []
                    command = 'L' if command == 'M' else 'l'
                    
                elif command in 'Ll' and len(values) == 2:
                    x, y = values
                    if command == 'l':
                        x += current_x
                        y += current_y
                    current_x, current_y = x, y
                    points.extend([x, y])
                    values = []
                    
                elif command in 'Hh' and len(values) == 1:
                    x = values[0]
                    if command == 'h':
                        x += current_x
                    current_x = x
                    points.extend([x, current_y])
                    values = []
                    
                elif command in 'Vv' and len(values) == 1:
                    y = values[0]
                    if command == 'v':
                        y += current_y
                    current_y = y
                    points.extend([current_x, y])
                    values = []
                    
                elif command == 'Z':
                    if points:
                        points.extend(points[:2])
                    values = []
        
        return points

    def redraw(self, *args):
        self.canvas.clear()
        with self.canvas:
            # White background
            Color(1, 1, 1, 1)
            Rectangle(pos=self.pos, size=self.size)
            
            # Draw shapes
            with PushMatrix():
                # Move to drawing area
                Translate(self.margin, self.margin)
                Scale(self.scale_factor, self.scale_factor)
                
                for shape in self.shapes:
                    if shape['type'] == 'path':
                        if shape.get('stroke'):
                            Color(*shape['stroke'])
                            Line(points=shape['points'], 
                                 width=shape['stroke_width'])
                            
                    elif shape['type'] == 'rect':
                        if shape.get('fill'):
                            Color(*shape['fill'])
                            Rectangle(pos=(shape['x'], shape['y']),
                                     size=(shape['width'], shape['height']))
                        if shape.get('stroke'):
                            Color(*shape['stroke'])
                            Line(rectangle=(shape['x'], shape['y'],
                                          shape['width'], shape['height']),
                                 width=shape['stroke_width'])
                            
                    elif shape['type'] == 'text':
                        if shape.get('fill'):
                            Color(*shape['fill'])
                            text = CoreLabel(text=shape['text'],
                                           font_size=shape['font_size'])
                            text.refresh()
                            
                            # Handle text anchor
                            x = shape['x']
                            if shape['text_anchor'] == 'middle':
                                x -= text.texture.width / 2
                            elif shape['text_anchor'] == 'end':
                                x -= text.texture.width
                                
                            Rectangle(pos=(x, shape['y'] - text.texture.height),
                                     size=text.texture.size,
                                     texture=text.texture)
            PopMatrix()

class SVGViewer(App):
    def build(self):
        layout = BoxLayout(orientation='vertical', spacing=dp(5))
        
        # Toolbar
        toolbar = BoxLayout(size_hint_y=None, height=dp(60))
        self.load_btn = SimpleButton(text='Load SVG', on_press=self.show_load_dialog)
        toolbar.add_widget(self.load_btn)
        
        # Drawing widget
        self.drawing = SVGDrawingWidget()
        
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
    