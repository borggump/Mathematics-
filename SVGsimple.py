from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.graphics import Rectangle, Color, Line, Ellipse
from kivy.clock import Clock
import os
import xml.etree.ElementTree as ET

class SimpleButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (dp(100), dp(50))
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
                if shape['type'] == 'line':
                    Line(points=shape['points'])

            # Current shape
            if self.current_shape:
                Color(*self.current_shape['color'])
                if self.current_shape['type'] == 'line':
                    Line(points=self.current_shape['points'])

class SVGDrawingApp(App):
    def build(self):
        # Main layout
        layout = BoxLayout(orientation='vertical', spacing=dp(5), padding=dp(5))

        # Tools layout
        tools = BoxLayout(size_hint_y=None, height=dp(60), spacing=dp(5))

        # Drawing tools
        self.save_btn = SimpleButton(text='Save', on_press=self.save_drawing)
        self.clear_btn = SimpleButton(text='Clear', on_press=self.clear_drawing)

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

    def set_color(self, color):
        self.drawing_widget.current_color = color

    def clear_drawing(self, instance):
        self.drawing_widget.shapes = []
        self.drawing_widget.draw_shapes()

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
                if shape['type'] == 'line':
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