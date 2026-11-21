from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.graphics import Rectangle, Color, Line, Ellipse
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
        self.margin = 20  # Margin in pixels

    def draw_shape(self, shape):
        shape_type = shape.get('type', '')
        
        # Set color based on fill or stroke
        if shape.get('fill_color'):
            Color(*shape['fill_color'])
        elif shape.get('stroke_color'):
            Color(*shape['stroke_color'])
        else:
            Color(0, 0, 0, 1)  # Default black

        # Draw based on shape type
        if shape_type == 'path':
            points = self.scale_points(shape['points'])
            if points:
                Line(points=points, width=1)
                
        elif shape_type == 'rect':
            x = shape['x'] * self.scale_factor + self.margin
            y = shape['y'] * self.scale_factor + self.margin
            w = shape['width'] * self.scale_factor
            h = shape['height'] * self.scale_factor
            
            if shape.get('fill_color'):
                Rectangle(pos=(x, y), size=(w, h))
            Line(rectangle=(x, y, w, h))
            
        elif shape_type == 'text':
            pos_x = shape['x'] * self.scale_factor + self.margin
            pos_y = shape['y'] * self.scale_factor + self.margin
            Label(text=shape['text'],
                  pos=(pos_x, pos_y),
                  font_size=shape['font_size'] * self.scale_factor * 0.5)

    def scale_points(self, points):
        scaled = []
        for i in range(0, len(points), 2):
            scaled.append(points[i] * self.scale_factor + self.margin)
            scaled.append(points[i+1] * self.scale_factor + self.margin)
        return scaled

    def parse_color(self, color_str):
        if not color_str or color_str == 'none':
            return None
        try:
            if color_str.startswith('#'):
                if len(color_str) == 4:  # #RGB
                    r = int(color_str[1] * 2, 16) / 255.0
                    g = int(color_str[2] * 2, 16) / 255.0
                    b = int(color_str[3] * 2, 16) / 255.0
                    return (r, g, b, 1)
                else:  # #RRGGBB
                    r = int(color_str[1:3], 16) / 255.0
                    g = int(color_str[3:5], 16) / 255.0
                    b = int(color_str[5:7], 16) / 255.0
                    return (r, g, b, 1)
                    
            elif color_str.startswith('rgb'):
                nums = re.findall(r'\d+', color_str)
                if len(nums) >= 3:
                    return (int(nums[0])/255.0, int(nums[1])/255.0, 
                           int(nums[2])/255.0, 1)
                    
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
        return (0, 0, 0, 1)

    def parse_path(self, d, current_x=0, current_y=0):
        points = []
        if not d:
            return points

        commands = re.findall(r'([MmLlHhVvCcSsZz]|-?\d*\.?\d+)', d)
        current_x = 0
        current_y = 0
        i = 0
        
        while i < len(commands):
            cmd = commands[i]
            
            if cmd in 'MmLlHhVvCcSsZz':
                command = cmd
                i += 1
            else:
                try:
                    if command in 'Mm':
                        x = float(commands[i]) 
                        y = float(commands[i+1])
                        if command == 'm':
                            x += current_x
                            y += current_y
                        points.extend([x, y])
                        current_x = x
                        current_y = y
                        i += 2
                        command = 'L' if command == 'M' else 'l'
                        
                    elif command in 'Ll':
                        x = float(commands[i])
                        y = float(commands[i+1])
                        if command == 'l':
                            x += current_x
                            y += current_y
                        points.extend([x, y])
                        current_x = x
                        current_y = y
                        i += 2
                        
                    elif command == 'C':
                        x1 = float(commands[i])
                        y1 = float(commands[i+1])
                        x2 = float(commands[i+2])
                        y2 = float(commands[i+3])
                        x = float(commands[i+4])
                        y = float(commands[i+5])
                        
                        # Generate points for Bézier curve
                        steps = 20
                        for t in range(steps + 1):
                            t = t / steps
                            bx = (1-t)**3 * current_x + 3*t*(1-t)**2 * x1 + \
                                 3*t**2*(1-t) * x2 + t**3 * x
                            by = (1-t)**3 * current_y + 3*t*(1-t)**2 * y1 + \
                                 3*t**2*(1-t) * y2 + t**3 * y
                            points.extend([bx, by])
                            
                        current_x = x
                        current_y = y
                        i += 6
                except:
                    i += 1
                    
        return points

    def load_svg(self, filepath):
        try:
            self.shapes = []
            tree = ET.parse(filepath)
            root = tree.getroot()
            
            # Parse viewBox
            viewbox = root.get('viewBox', '0 0 800 1000').split()
            vb_width = float(viewbox[2])
            vb_height = float(viewbox[3])
            
            # Calculate scaling factor
            width_scale = (self.width - 2 * self.margin) / vb_width
            height_scale = (self.height - 2 * self.margin) / vb_height
            self.scale_factor = min(width_scale, height_scale)
            
            def process_element(element, dx=0, dy=0):
                # Get transform
                transform = element.get('transform', '')
                if transform:
                    match = re.search(r'translate\(([-\d.]+)[,\s]*([-\d.]+)?\)', transform)
                    if match:
                        dx += float(match.group(1))
                        dy += float(match.group(2) if match.group(2) else 0)
                
                # Process element based on type
                tag = element.tag.split('}')[-1]
                
                if tag == 'path':
                    d = element.get('d', '')
                    if d:
                        points = self.parse_path(d)
                        # Apply translation
                        transformed_points = []
                        for i in range(0, len(points), 2):
                            transformed_points.extend([points[i] + dx, points[i+1] + dy])
                        
                        self.shapes.append({
                            'type': 'path',
                            'points': transformed_points,
                            'stroke_color': self.parse_color(element.get('stroke')),
                            'fill_color': self.parse_color(element.get('fill'))
                        })
                        
                elif tag == 'rect':
                    try:
                        x = float(element.get('x', 0)) + dx
                        y = float(element.get('y', 0)) + dy
                        width = float(element.get('width', 0))
                        height = float(element.get('height', 0))
                        
                        self.shapes.append({
                            'type': 'rect',
                            'x': x,
                            'y': y,
                            'width': width,
                            'height': height,
                            'stroke_color': self.parse_color(element.get('stroke')),
                            'fill_color': self.parse_color(element.get('fill'))
                        })
                    except ValueError:
                        pass
                        
                elif tag == 'text':
                    try:
                        x = float(element.get('x', 0)) + dx
                        y = float(element.get('y', 0)) + dy
                        text = element.text or ''
                        font_size = float(element.get('font-size', '12'))
                        
                        self.shapes.append({
                            'type': 'text',
                            'x': x,
                            'y': y,
                            'text': text,
                            'font_size': font_size,
                            'fill_color': self.parse_color(element.get('fill', '#000000'))
                        })
                    except ValueError:
                        pass
                
                # Process children with accumulated transform
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
            
            # Draw all shapes
            for shape in self.shapes:
                self.draw_shape(shape)

class SVGViewer(App):
    def build(self):
        layout = BoxLayout(orientation='vertical', spacing=dp(5))
        
        # Create toolbar
        toolbar = BoxLayout(size_hint_y=None, height=dp(60), spacing=dp(5))
        
        # Create load button
        self.load_btn = SimpleButton(
            text='Load SVG',
            on_press=self.show_load_dialog
        )
        toolbar.add_widget(self.load_btn)
        
        # Create drawing widget
        self.drawing = SVGDrawingWidget()
        
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