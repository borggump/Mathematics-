from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.uix.colorpicker import ColorPicker
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.filechooser import FileChooserListView
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.graphics import Rectangle, Color, Line, Ellipse
from kivy.clock import Clock
from PIL import Image
import io
import os
import xml.etree.ElementTree as ET

class CustomButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (dp(100), dp(50))
        self.font_size = dp(14)
        self.background_normal = ''
        self.background_color = (0.2, 0.6, 0.8, 1)

class CustomSpinner(Spinner):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (dp(120), dp(50))
        self.font_size = dp(14)
        self.background_normal = ''
        self.background_color = (0.2, 0.6, 0.8, 1)

class SVGElement:
    def __init__(self, color=(1, 0, 0, 1)):
        self.color = color
        
    def contains_point(self, point):
        return False

class RectElement(SVGElement):
    def __init__(self, x, y, width, height, color=(1, 0, 0, 1)):
        super().__init__(color)
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        
    def contains_point(self, point):
        return (self.x <= point[0] <= self.x + self.width and
                self.y <= point[1] <= self.y + self.height)

class CircleElement(SVGElement):
    def __init__(self, cx, cy, r, color=(1, 0, 0, 1)):
        super().__init__(color)
        self.cx = cx
        self.cy = cy
        self.r = r
        
    def contains_point(self, point):
        dx = point[0] - self.cx
        dy = point[1] - self.cy
        return (dx * dx + dy * dy) <= self.r * self.r

class TextElement(SVGElement):
    def __init__(self, x, y, text, color=(1, 0, 0, 1)):
        super().__init__(color)
        self.x = x
        self.y = y
        self.text = text
        
    def contains_point(self, point):
        return (abs(point[0] - self.x) < dp(20) and
                abs(point[1] - self.y) < dp(20))

class SVGDisplayWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.elements = []
        self.preview = None
        self.bind(size=self.update_canvas, pos=self.update_canvas)
        
    def add_rectangle(self, x, y, width, height, color=(1, 0, 0, 1)):
        self.elements.append(RectElement(x, y, width, height, color))
        self.update_canvas()
        
    def add_circle(self, cx, cy, r, color=(1, 0, 0, 1)):
        self.elements.append(CircleElement(cx, cy, r, color))
        self.update_canvas()
        
    def add_text(self, x, y, text, color=(1, 0, 0, 1)):
        self.elements.append(TextElement(x, y, text, color))
        self.update_canvas()
        
    def clear_elements(self):
        self.elements = []
        self.update_canvas()
        
    def find_element_at(self, pos):
        for element in reversed(self.elements):
            if element.contains_point(pos):
                return element
        return None
        
    def update_preview(self, tool, start, end, color):
        self.preview = {
            'tool': tool,
            'start': start,
            'end': end,
            'color': color
        }
        self.update_canvas()
        
    def clear_preview(self):
        self.preview = None
        self.update_canvas()
        
    def update_canvas(self, *args):
        self.canvas.clear()
        
        with self.canvas:
            Color(1, 1, 1, 1)
            Rectangle(pos=self.pos, size=self.size)
            
            for element in self.elements:
                Color(*element.color)
                
                if isinstance(element, RectElement):
                    Rectangle(
                        pos=(element.x, element.y),
                        size=(element.width, element.height)
                    )
                elif isinstance(element, CircleElement):
                    Ellipse(
                        pos=(element.cx - element.r, element.cy - element.r),
                        size=(element.r * 2, element.r * 2)
                    )
                elif isinstance(element, TextElement):
                    Label(
                        text=element.text,
                        pos=(element.x, element.y)
                    )
                    
            if self.preview:
                Color(*self.preview['color'])
                
                if self.preview['tool'] == 'rectangle':
                    x, y = self.preview['start']
                    width = self.preview['end'][0] - x
                    height = self.preview['end'][1] - y
                    Line(rectangle=(x, y, width, height))
                elif self.preview['tool'] == 'circle':
                    cx, cy = self.preview['start']
                    r = ((self.preview['end'][0] - cx) ** 2 +
                         (self.preview['end'][1] - cy) ** 2) ** 0.5
                    Line(circle=(cx, cy, r))

class SVGEditor(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.spacing = dp(5)
        self.padding = dp(5)
        self.current_tool = 'select'
        self.current_color = (1, 0, 0, 1)
        self.current_shape = None
        self.selected_element = None
        
        # Create top toolbar
        self.create_toolbar()
        
        # Create main display area
        self.display_widget = SVGDisplayWidget()
        self.display_widget.bind(
            on_touch_down=self.on_canvas_touch,
            on_touch_move=self.on_canvas_move,
            on_touch_up=self.on_canvas_release
        )
        self.add_widget(self.display_widget)
        
        # Initialize file chooser as None
        self.file_chooser = None

    def parse_svg_elements(self, element):
        for child in element:
            if child.tag.endswith('rect'):
                x = float(child.get('x', 0))
                y = float(child.get('y', 0))
                width = float(child.get('width', 0))
                height = float(child.get('height', 0))
                self.display_widget.add_rectangle(x, y, width, height)
            elif child.tag.endswith('circle'):
                cx = float(child.get('cx', 0))
                cy = float(child.get('cy', 0))
                r = float(child.get('r', 0))
                self.display_widget.add_circle(cx, cy, r)
            elif child.tag.endswith('text'):
                x = float(child.get('x', 0))
                y = float(child.get('y', 0))
                text = child.text or ''
                self.display_widget.add_text(x, y, text)

    def create_toolbar(self):
        toolbar = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(120))
        
        # First row
        row1 = BoxLayout(size_hint_y=None, height=dp(55), spacing=dp(5))
        
        self.load_button = CustomButton(
            text='Load SVG',
            on_press=self.show_file_chooser
        )
        self.save_button = CustomButton(
            text='Save SVG',
            on_press=self.save_svg
        )
        
        row1.add_widget(self.load_button)
        row1.add_widget(self.save_button)
        
        # Second row
        row2 = BoxLayout(size_hint_y=None, height=dp(55), spacing=dp(5))
        
        self.tool_spinner = CustomSpinner(
            text='Select',
            values=('Select', 'Rectangle', 'Circle', 'Text')
        )
        self.tool_spinner.bind(text=self.on_tool_change)
        
        self.color_button = CustomButton(
            text='Color',
            background_color=self.current_color,
            on_press=self.show_color_picker
        )
        
        row2.add_widget(self.tool_spinner)
        row2.add_widget(self.color_button)
        
        toolbar.add_widget(row1)
        toolbar.add_widget(row2)
        self.add_widget(toolbar)

    def save_svg(self, instance):
        try:
            svg = ET.Element('svg')
            svg.set('xmlns', 'http://www.w3.org/2000/svg')
            svg.set('version', '1.1')
            svg.set('width', str(self.display_widget.width))
            svg.set('height', str(self.display_widget.height))
            
            for element in self.display_widget.elements:
                if isinstance(element, RectElement):
                    rect = ET.SubElement(svg, 'rect')
                    rect.set('x', str(element.x))
                    rect.set('y', str(element.y))
                    rect.set('width', str(element.width))
                    rect.set('height', str(element.height))
                    rect.set('fill', f'rgb({int(element.color[0]*255)},{int(element.color[1]*255)},{int(element.color[2]*255)})')
                elif isinstance(element, CircleElement):
                    circle = ET.SubElement(svg, 'circle')
                    circle.set('cx', str(element.cx))
                    circle.set('cy', str(element.cy))
                    circle.set('r', str(element.r))
                    circle.set('fill', f'rgb({int(element.color[0]*255)},{int(element.color[1]*255)},{int(element.color[2]*255)})')
                elif isinstance(element, TextElement):
                    text = ET.SubElement(svg, 'text')
                    text.set('x', str(element.x))
                    text.set('y', str(element.y))
                    text.set('fill', f'rgb({int(element.color[0]*255)},{int(element.color[1]*255)},{int(element.color[2]*255)})')
                    text.text = element.text

            content = BoxLayout(orientation='vertical', spacing=dp(10))
            filename_input = TextInput(
                text='drawing.svg',
                multiline=False,
                size_hint_y=None,
                height=dp(50)
            )

            def do_save(instance):
                try:
                    storage_path = '/storage/emulated/0/Download'
                    if not os.path.exists(storage_path):
                        os.makedirs(storage_path)
                    
                    filepath = os.path.join(storage_path, filename_input.text)
                    tree = ET.ElementTree(svg)
                    tree.write(filepath, encoding='utf-8', xml_declaration=True)
                    
                    self.show_message('Success', f'File saved to {filepath}')
                    popup.dismiss()
                except Exception as e:
                    self.show_message('Error', f'Error saving file: {e}')

            save_button = CustomButton(
                text='Save',
                size_hint_y=None,
                height=dp(50),
                on_press=do_save
            )
            
            content.add_widget(Label(text='Enter filename:'))
            content.add_widget(filename_input)
            content.add_widget(save_button)
            
            popup = Popup(
                title='Save SVG',
                content=content,
                size_hint=(0.9, 0.4)
            )
            popup.open()
            
        except Exception as e:
            self.show_message('Error', f'Error preparing SVG: {e}')

    def show_file_chooser(self, instance):
        content = BoxLayout(orientation='vertical')
        
        if not self.file_chooser:
            self.file_chooser = FileChooserListView(
                filters=['*.svg'],
                size_hint_y=0.9
            )
            self.file_chooser.bind(on_submit=self.load_svg)
        
        content.add_widget(self.file_chooser)
        
        close_button = CustomButton(
            text='Cancel',
            size_hint_y=None,
            height=dp(50),
            on_press=lambda *args: popup.dismiss()
        )
        content.add_widget(close_button)
        
        popup = Popup(
            title='Choose SVG File',
            content=content,
            size_hint=(0.9, 0.9)
        )
        popup.open()

    def load_svg(self, instance, selection, *args):
        if selection:
            svg_path = selection[0]
            try:
                tree = ET.parse(svg_path)
                root = tree.getroot()
                self.display_widget.clear_elements()
                self.parse_svg_elements(root)
            except Exception as e:
                self.show_message('Error', f'Error loading SVG: {e}')

    def on_tool_change(self, spinner, text):
        self.current_tool = text.lower()

    def show_color_picker(self, instance):
        content = BoxLayout(orientation='vertical')
        color_picker = ColorPicker(color=self.current_color)
        
        def on_color(instance, value):
            self.current_color = value
            self.color_button.background_color = value
            if self.selected_element:
                self.selected_element.color = value
                self.display_widget.update_canvas()
        
        color_picker.bind(color=on_color)
        
        close_button = CustomButton(
            text='Done',
            size_hint_y=None,
            height=dp(50),
            on_press=lambda *args: popup.dismiss()
        )