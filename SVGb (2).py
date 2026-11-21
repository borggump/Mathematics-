from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
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

class DrawingWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.shapes = []
        self.bind(size=self.update_canvas)
        self.bind(pos=self.update_canvas)
        
    def parse_color(self, color_str):
        if not color_str or color_str == 'none':
            return (0, 0, 0, 1)
        try:
            if color_str.startswith('#'):
                if len(color_str) == 4:  # #RGB
                    r = int(color_str[1] * 2, 16) / 255
                    g = int(color_str[2] * 2, 16) / 255
                    b = int(color_str[3] * 2, 16) / 255
                    return (r, g, b, 1)
                else:  # #RRGGBB
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
            
        commands = re.findall(r'([MmLlHhVvCcSsZz]|-?\d*\.?\d+)', d)
        current_x, current_y = 0, 0
        
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
                        current_x, current_y = x, y
                        i += 2
                    elif command in 'Ll':
                        x = float(commands[i])
                        y = float(commands[i+1])
                        if command == 'l':
                            x += current_x
                            y += current_y
                        points.extend([x, y])
                        current_x, current_y = x, y
                        i += 2
                except:
                    i += 1
                    
        return points

    def load_svg(self, filepath):
        try:
            tree = ET.parse(filepath)
            root = tree.getroot()
            
            viewbox = root.get('viewBox', '0 0 100 100').split()
            vb_width = float(viewbox[2])
            vb_height = float(viewbox[3])
            
            scale_x = self.width / vb_width
            scale_y = self.height / vb_height
            scale = min(scale_x, scale_y)
            
            self.shapes = []
            
            for elem in root.iter():
                tag = elem.tag.split('}')[-1]
                
                if tag == 'path':
                    points = self.parse_path(elem.get('d', ''))
                    if points:
                        scaled_points = []
                        for i in range(0, len(points), 2):
                            scaled_points.extend([
                                points[i] * scale,
                                self.height - (points[i+1] * scale)
                            ])
                        self.shapes.append({
                            'type': 'path',
                            'points': scaled_points,
                            'color': self.parse_color(elem.get('stroke', '#000000'))
                        })
                        
                elif tag == 'rect':
                    try:
                        x = float(elem.get('x', 0)) * scale
                        y = self.height - float(elem.get('y', 0)) * scale
                        width = float(elem.get('width', 0)) * scale
                        height = float(elem.get('height', 0)) * scale
                        
                        self.shapes.append({
                            'type': 'rect',
                            'points': [x, y, x + width, y - height],
                            'color': self.parse_color(elem.get('fill', '#000000'))
                        })
                    except:
                        pass
            
            self.update_canvas()
            return True
        except Exception as e:
            print(f"Error loading SVG: {e}")
            return False

    def update_canvas(self, *args):
        self.canvas.clear()
        with self.canvas:
            Color(1, 1, 1, 1)
            Rectangle(pos=self.pos, size=self.size)
            
            for shape in self.shapes:
                Color(*shape['color'])
                
                if shape['type'] == 'path':
                    Line(points=shape['points'])
                elif shape['type'] == 'rect':
                    Rectangle(pos=(shape['points'][0], shape['points'][1]),
                            size=(shape['points'][2] - shape['points'][0],
                                  shape['points'][1] - shape['points'][3]))

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