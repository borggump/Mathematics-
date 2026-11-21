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

class SimpleButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (dp(80), dp(50))
        self.background_normal = ''
        self.background_color = (0.2, 0.6, 0.8, 1)
        self.color = (1, 1, 1, 1)

class DrawingWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.shapes = []
        self.current_shape = None
        self.current_color = (1, 0, 0, 1)  # Red
        self.current_tool = 'line'
        self.draw_shapes()

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.current_shape = {
                'type': self.current_tool,
                'points': [touch.x, touch.y],
                'color': self.current_color
            }
            return True

    def on_touch_move(self, touch):
        if self.current_shape and self.collide_point(*touch.pos):
            self.current_shape['points'].extend([touch.x, touch.y])
            self.draw_shapes()
            return True

    def on_touch_up(self, touch):
        if self.current_shape:
            self.shapes.append(self.current_shape)
            self.current_shape = None
            self.draw_shapes()
            return True

    def draw_shapes(self):
        self.canvas.clear()
        with self.canvas:
            # Background
            Color(0.9, 0.9, 0.9, 1)
            Rectangle(pos=self.pos, size=self.size)

            # Saved shapes
            for shape in self.shapes:
                Color(*shape['color'])
                if shape['type'] in ['line', 'path', 'polyline']:
                    Line(points=shape['points'])

            # Current shape
            if self.current_shape:
                Color(*self.current_shape['color'])
                if self.current_shape['type'] == 'line':
                    Line(points=self.current_shape['points'])

    def clear(self):
        self.shapes = []
        self.draw_shapes()

    def parse_color(self, color_str):
        if not color_str:
            return (0, 0, 0, 1)
        
        # Handle rgb() format
        rgb_match = re.match(r'rgb\((\d+),\s*(\d+),\s*(\d+)\)', color_str)
        if rgb_match:
            r, g, b = map(int, rgb_match.groups())
            return (r/255, g/255, b/255, 1)
        
        # Handle hex format
        hex_match = re.match(r'#?([0-9a-fA-F]{6})', color_str)
        if hex_match:
            hex_color = hex_match.group(1)
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            return (r/255, g/255, b/255, 1)
        
        # Handle basic color names
        color_map = {
            'red': (1, 0, 0, 1),
            'green': (0, 1, 0, 1),
            'blue': (0, 0, 1, 1),
            'black': (0, 0, 0, 1),
            'white': (1, 1, 1, 1)
        }
        return color_map.get(color_str.lower(), (0, 0, 0, 1))

    def load_svg(self, filepath):
        try:
            tree = ET.parse(filepath)
            root = tree.getroot()
            
            # Clear current drawing
            self.clear()
            
            # Get SVG namespace
            namespace = ''
            if '}' in root.tag:
                namespace = root.tag.split('}')[0] + '}'
            
            # Parse SVG elements
            for element in root.iter():
                tag = element.tag.replace(namespace, '')
                stroke = element.get('stroke', '#000000')
                color = self.parse_color(stroke)
                
                if tag == 'line':
                    x1 = float(element.get('x1', 0))
                    y1 = float(element.get('y1', 0))
                    x2 = float(element.get('x2', 0))
                    y2 = float(element.get('y2', 0))
                    
                    self.shapes.append({
                        'type': 'line',
                        'points': [x1, y1, x2, y2],
                        'color': color
                    })
                
                elif tag == 'rect':
                    x = float(element.get('x', 0))
                    y = float(element.get('y', 0))
                    width = float(element.get('width', 0))
                    height = float(element.get('height', 0))
                    
                    self.shapes.append({
                        'type': 'line',
                        'points': [x, y, x+width, y, x+width, y+height, x, y+height, x, y],
                        'color': color
                    })
                
                elif tag == 'polyline':
                    points_str = element.get('points', '')
                    if points_str:
                        points = []
                        pairs = points_str.split()
                        for pair in pairs:
                            x, y = map(float, pair.split(','))
                            points.extend([x, y])
                        
                        self.shapes.append({
                            'type': 'polyline',
                            'points': points,
                            'color': color
                        })
            
            self.draw_shapes()
            return True
            
        except Exception as e:
            print(f"Error loading SVG: {e}")
            return False

class SVGDrawingApp(App):
    def build(self):
        # Main layout
        layout = BoxLayout(orientation='vertical', spacing=dp(5), padding=dp(5))

        # Tools layout
        tools = BoxLayout(size_hint_y=None, height=dp(60), spacing=dp(5))

        # Drawing tools
        self.load_btn = SimpleButton(text='Load', on_press=self.show_load_dialog)
        self.save_btn = SimpleButton(text='Save', on_press=self.save_drawing)
        self.clear_btn = SimpleButton(text='Clear', on_press=self.clear_drawing)

        tools.add_widget(self.load_btn)
        tools.add_widget(self.save_btn)
        tools.add_widget(self.clear_btn)

        # Color buttons
        colors = [
            ('Red', (1, 0, 0, 1)),
            ('Blue', (0, 0, 1, 1)),
            ('Green', (0, 1, 0, 1)),
            ('Black', (0, 0, 0, 1))
        ]

        for name, color in colors:
            btn = SimpleButton(
                text=name,
                background_color=color,
                on_press=lambda x, c=color: self.set_color(c)
            )
            tools.add_widget(btn)

        # Drawing widget
        self.drawing_widget = DrawingWidget()

        # Add widgets to layout
        layout.add_widget(tools)
        layout.add_widget(self.drawing_widget)

        return layout

    def show_load_dialog(self, instance):
        content = BoxLayout(orientation='vertical')
        
        # File chooser
        file_chooser = FileChooserListView(
            path='/storage/emulated/0/Download',  # Start in Downloads folder
            filters=['*.svg']
        )
        
        # Buttons
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
                if self.drawing_widget.load_svg(file_chooser.selection[0]):
                    self.show_message('File loaded successfully')
                else:
                    self.show_message('Error loading file')
            popup.dismiss()
            
        load_button.bind(on_press=load)
        cancel_button.bind(on_press=popup.dismiss)
        
        popup.open()

    def set_color(self, color):
        self.drawing_widget.current_color = color

    def clear_drawing(self, instance):
        self.drawing_widget.clear()

    def save_drawing(self, instance):
        try:
            # Create SVG content
            svg = ET.Element('svg')
            svg.set('xmlns', 'http://www.w3.org/2000/svg')
            svg.set('version', '1.1')
            svg.set('width', str(self.drawing_widget.width))
            svg.set('height', str(self.drawing_widget.height))

            # Convert shapes to SVG
            for shape in self.drawing_widget.shapes:
                if shape['type'] in ['line', 'polyline']:
                    line = ET.SubElement(svg, 'polyline')
                    points = ' '.join(f"{x},{y}" 
                        for x, y in zip(shape['points'][::2], shape['points'][1::2]))
                    line.set('points', points)
                    line.set('fill', 'none')
                    line.set('stroke', f'rgb({int(shape["color"][0]*255)},'\
                        f'{int(shape["color"][1]*255)},{int(shape["color"][2]*255)})')
                    line.set('stroke-width', '2')

            # Save to downloads folder
            downloads_dir = '/storage/emulated/0/Download'
            filename = 'drawing.svg'
            filepath = os.path.join(downloads_dir, filename)

            tree = ET.ElementTree(svg)
            tree.write(filepath, encoding='utf-8', xml_declaration=True)

            self.show_message(f'Saved to Downloads/{filename}')

        except Exception as e:
            self.show_message(f'Error: {str(e)}')

    def show_message(self, message):
        popup = Popup(
            title='Message',
            content=Label(text=message),
            size_hint=(0.8, 0.3)
        )
        popup.open()
        Clock.schedule_once(popup.dismiss, 2)

if __name__ == '__main__':
    SVGDrawingApp().run()