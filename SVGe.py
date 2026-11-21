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
from kivy.graphics import Rectangle, Color, Line, Ellipse
import os
import xml.etree.ElementTree as ET
import re

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
            return (0, 0, 0, 1)
        except:
            return (0, 0, 0, 1)

    def parse_path(self, d):
        points = []
        if not d:
            return points
            
        commands = re.findall(r'([MmLlHhVvZz])|(-?[\d.]+)', d)
        current_x = 0
        current_y = 0
        
        i = 0
        command = 'M'
        
        while i < len(commands):
            cmd, num = commands[i]
            if cmd:
                command = cmd
            elif num:
                try:
                    if command in 'Mm':
                        x = float(num)
                        y = float(commands[i+1][1])
                        if command == 'm':
                            x += current_x
                            y += current_y
                        points.extend([x, y])
                        current_x, current_y = x, y
                        i += 1
                    elif command in 'Ll':
                        x = float(num)
                        y = float(commands[i+1][1])
                        if command == 'l':
                            x += current_x
                            y += current_y
                        points.extend([x, y])
                        current_x, current_y = x, y
                        i += 1
                    elif command in 'Hh':
                        x = float(num)
                        if command == 'h':
                            x += current_x
                        points.extend([x, current_y])
                        current_x = x
                    elif command in 'Vv':
                        y = float(num)
                        if command == 'v':
                            y += current_y
                        points.extend([current_x, y])
                        current_y = y
                except:
                    pass
            i += 1
        return points

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
                        # Transform points
                        points = []
                        for i in range(0, len(path_data), 2):
                            points.extend([
                                path_data[i] + curr_transform[0],
                                self.vb_height - (path_data[i+1] + curr_transform[1])
                            ])
                        
                        self.shapes.append({
                            'type': 'path',
                            'points': points,
                            'color': self.parse_color(element.get('stroke', 'black'))
                        })
                
                elif tag == 'rect':
                    try:
                        x = float(element.get('x', 0)) + curr_transform[0]
                        y = float(element.get('y', 0)) + curr_transform[1]
                        w = float(element.get('width', 0))
                        h = float(element.get('height', 0))
                        
                        # Flip y coordinate
                        y = self.vb_height - (y + h)
                        
                        self.shapes.append({
                            'type': 'rect',
                            'x': x,
                            'y': y,
                            'width': w,
                            'height': h,
                            'color': self.parse_color(element.get('fill', 'black'))
                        })
                    except ValueError:
                        pass
                
                elif tag == 'text':
                    try:
                        x = float(element.get('x', 0)) + curr_transform[0]
                        y = float(element.get('y', 0)) + curr_transform[1]
                        
                        # Flip y coordinate
                        y = self.vb_height - y
                        
                        self.shapes.append({
                            'type': 'text',
                            'x': x,
                            'y': y,
                            'text': element.text or '',
                            'font_size': float(element.get('font-size', '12')),
                            'color': self.parse_color(element.get('fill', 'black')),
                            'text_anchor': element.get('text-anchor', 'start')
                        })
                    except ValueError:
                        pass
                
                for child in element:
                    process_element(child, curr_transform)
            
            process_element(root)
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
                Color(*shape['color'])
                
                if shape['type'] == 'path':
                    # Scale points
                    scaled_points = []
                    for i in range(0, len(shape['points']), 2):
                        scaled_points.extend([
                            shape['points'][i] * self.scale_factor + self.margin,
                            shape['points'][i+1] * self.scale_factor + self.margin
                        ])
                    Line(points=scaled_points)
                
                elif shape['type'] == 'rect':
                    x = shape['x'] * self.scale_factor + self.margin
                    y = shape['y'] * self.scale_factor + self.margin
                    w = shape['width'] * self.scale_factor
                    h = shape['height'] * self.scale_factor
                    Rectangle(pos=(x, y), size=(w, h))
                
                elif shape['type'] == 'text':
                    text = CoreLabel(
                        text=shape['text'],
                        font_size=shape['font_size'] * self.scale_factor * 0.75
                    )
                    text.refresh()
                    
                    x = shape['x'] * self.scale_factor + self.margin
                    y = shape['y'] * self.scale_factor + self.margin
                    
                    if shape['text_anchor'] == 'middle':
                        x -= text.texture.width / 2
                    elif shape['text_anchor'] == 'end':
                        x -= text.texture.width
                    
                    Rectangle(
                        pos=(x, y - text.texture.height),
                        size=text.texture.size,
                        texture=text.texture
                    )

class SVGViewer(App):
    def build(self):
        layout = BoxLayout(orientation='vertical', spacing=dp(5))
        
        toolbar = BoxLayout(size_hint_y=None, height=dp(60))
        self.load_btn = SimpleButton(text='Load SVG', on_press=self.show_load_dialog)
        toolbar.add_widget(self.load_btn)
        
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
    