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
        self.size = (dp(80), dp(50))
        self.background_normal = ''
        self.background_color = (0.2, 0.6, 0.8, 1)
        self.color = (1, 1, 1, 1)

class SVGRenderer(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.shapes = []
        self.scale = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.bezier_points = 20

    def parse_color(self, color_str):
        if not color_str or color_str == 'none':
            return (0, 0, 0, 1)
            
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
            colors = re.findall(r'\d+', color_str)
            if len(colors) >= 3:
                return (int(colors[0])/255, int(colors[1])/255, int(colors[2])/255, 1)
                
        color_map = {
            'black': (0, 0, 0, 1),
            'white': (1, 1, 1, 1),
            'red': (1, 0, 0, 1),
            'blue': (0, 0, 1, 1),
            'green': (0, 1, 0, 1),
            'none': (0, 0, 0, 0)
        }
        return color_map.get(color_str.lower(), (0, 0, 0, 1))

    def load_svg(self, filepath):
        try:
            tree = ET.parse(filepath)
            root = tree.getroot()
            
            # Parse viewBox
            viewbox = root.get('viewBox', '0 0 100 100').split()
            vb_x, vb_y, vb_width, vb_height = map(float, viewbox)
            
            # Calculate scale to fit window
            scale_x = self.width / vb_width
            scale_y = self.height / vb_height
            self.scale = min(scale_x, scale_y) * 0.9  # 90% of available space
            
            self.process_element(root)
            self.draw()
            return True
        except Exception as e:
            print(f"Error loading SVG: {e}")
            return False

    def process_element(self, element, transform_list=None):
        if transform_list is None:
            transform_list = []
            
        # Get element transform
        transform = element.get('transform', '')
        if transform:
            transform_list = transform_list + [transform]

        # Process element based on type
        tag = element.tag.split('}')[-1]
        
        if tag == 'rect':
            self.process_rect(element, transform_list)
        elif tag == 'circle':
            self.process_circle(element, transform_list)
        elif tag == 'path':
            self.process_path(element, transform_list)
        elif tag == 'text':
            self.process_text(element, transform_list)
            
        # Process children
        for child in element:
            self.process_element(child, transform_list)

    def process_rect(self, element, transform_list):
        try:
            x = float(element.get('x', 0))
            y = float(element.get('y', 0))
            width = float(element.get('width', 0))
            height = float(element.get('height', 0))
            fill = element.get('fill', 'none')
            stroke = element.get('stroke', 'black')
            
            self.shapes.append({
                'type': 'rect',
                'points': [x, y, x + width, y, x + width, y + height, x, y + height, x, y],
                'fill_color': self.parse_color(fill),
                'stroke_color': self.parse_color(stroke),
                'transform': transform_list
            })
        except ValueError as e:
            print(f"Error processing rect: {e}")

    def process_circle(self, element, transform_list):
        try:
            cx = float(element.get('cx', 0))
            cy = float(element.get('cy', 0))
            r = float(element.get('r', 0))
            fill = element.get('fill', 'none')
            stroke = element.get('stroke', 'black')
            
            points = []
            for i in range(36):
                angle = i * 2 * pi / 36
                points.extend([cx + r * cos(angle), cy + r * sin(angle)])
            
            self.shapes.append({
                'type': 'circle',
                'points': points,
                'fill_color': self.parse_color(fill),
                'stroke_color': self.parse_color(stroke),
                'transform': transform_list
            })
        except ValueError as e:
            print(f"Error processing circle: {e}")

    def process_path(self, element, transform_list):
        d = element.get('d', '')
        if d:
            fill = element.get('fill', 'none')
            stroke = element.get('stroke', 'black')
            points = self.parse_path(d)
            
            self.shapes.append({
                'type': 'path',
                'points': points,
                'fill_color': self.parse_color(fill),
                'stroke_color': self.parse_color(stroke),
                'transform': transform_list
            })

    def parse_path(self, d):
        points = []
        current_x = 0
        current_y = 0
        
        commands = re.findall(r'([MmLlHhVvCcSsZz]|-?\d*\.?\d+)', d)
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
                        
                    elif command in 'Cc':
                        x1 = float(commands[i])
                        y1 = float(commands[i+1])
                        x2 = float(commands[i+2])
                        y2 = float(commands[i+3])
                        x = float(commands[i+4])
                        y = float(commands[i+5])
                        
                        # Approximate Bézier curve
                        for t in range(self.bezier_points + 1):
                            t = t / self.bezier_points
                            bx = (1-t)**3 * current_x + 3*(1-t)**2*t * x1 + 3*(1-t)*t**2 * x2 + t**3 * x
                            by = (1-t)**3 * current_y + 3*(1-t)**2*t * y1 + 3*(1-t)*t**2 * y2 + t**3 * y
                            points.extend([bx, by])
                            
                        current_x = x
                        current_y = y
                        i += 6
                except:
                    i += 1
                    
        return points

    def draw(self, *args):
        self.canvas.clear()
        with self.canvas:
            # Draw background
            Color(1, 1, 1, 1)
            Rectangle(pos=self.pos, size=self.size)
            
            # Draw all shapes
            for shape in self.shapes:
                # Draw fill
                if shape['fill_color'][3] > 0:  # If not transparent
                    Color(*shape['fill_color'])
                    points = [p * self.scale for p in shape['points']]
                    if shape['type'] in ['rect', 'path']:
                        try:
                            mesh_points = []
                            for i in range(0, len(points), 2):
                                mesh_points.append(points[i] + self.offset_x)
                                mesh_points.append(points[i+1] + self.offset_y)
                            Line(points=mesh_points, close=True)
                        except:
                            pass
                            
                # Draw stroke
                if shape['stroke_color'][3] > 0:  # If not transparent
                    Color(*shape['stroke_color'])
                    points = [p * self.scale for p in shape['points']]
                    try:
                        scaled_points = []
                        for i in range(0, len(points), 2):
                            scaled_points.append(points[i] + self.offset_x)
                            scaled_points.append(points[i+1] + self.offset_y)
                        Line(points=scaled_points)
                    except:
                        pass

class SVGViewerApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical', spacing=dp(5))
        
        # Create toolbar
        toolbar = BoxLayout(size_hint_y=None, height=dp(60), spacing=dp(5))
        
        # Load button
        self.load_btn = SimpleButton(text='Load SVG', on_press=self.show_load_dialog)
        toolbar.add_widget(self.load_btn)
        
        # Main renderer
        self.renderer = SVGRenderer()
        
        # Add widgets to layout
        layout.add_widget(toolbar)
        layout.add_widget(self.renderer)
        
        return layout
        
    def show_load_dialog(self, instance):
        content = BoxLayout(orientation='vertical')
        
        # File chooser
        file_chooser = FileChooserListView(
            path='/storage/emulated/0/Download',  # Start in Downloads folder
            filters=['*.svg']
        )
        
        # Buttons
        buttons = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(5))
        load_button = SimpleButton(text='Load')
        cancel_button = SimpleButton(text='Cancel')
        
        def load(instance):
            if file_chooser.selection:
                self.renderer.load_svg(file_chooser.selection[0])
            popup.dismiss()
            
        def cancel(instance):
            popup.dismiss()
            
        load_button.bind(on_press=load)
        cancel_button.bind(on_press=cancel)
        
        buttons.add_widget(load_button)
        buttons.add_widget(cancel_button)
        
        content.add_widget(file_chooser)
        content.add_widget(buttons)
        
        popup = Popup(
            title='Load SVG File',
            content=content,
            size_hint=(0.9, 0.9)
        )
        popup.open()

if __name__ == '__main__':
    SVGViewerApp().run()