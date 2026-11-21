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
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM
from reportlab.graphics.shapes import Drawing, Rect, Circle, String
from PIL import Image
import io
import os
import xml.etree.ElementTree as ET

class CustomButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (dp(100), dp(50))  # Larger touch target for mobile
        self.font_size = dp(14)
        self.background_normal = ''
        self.background_color = (0.2, 0.6, 0.8, 1)  # Material Design-like blue

class CustomSpinner(Spinner):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (dp(120), dp(50))
        self.font_size = dp(14)
        self.background_normal = ''
        self.background_color = (0.2, 0.6, 0.8, 1)

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
        self.add_widget(self.display_widget)
        
        # Initialize file chooser as None
        self.file_chooser = None
        
    def create_toolbar(self):
        # Top toolbar - using multiple rows for better mobile layout
        toolbar = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(120))
        
        # First row of buttons
        row1 = BoxLayout(size_hint_y=None, height=dp(55), spacing=dp(5))
        
        # File operations
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
        
        # Second row of buttons
        row2 = BoxLayout(size_hint_y=None, height=dp(55), spacing=dp(5))
        
        # Tool selector
        self.tool_spinner = CustomSpinner(
            text='Select',
            values=('Select', 'Rectangle', 'Circle', 'Text'),
            on_text=self.on_tool_change
        )
        
        # Color picker button
        self.color_button = CustomButton(
            text='Color',
            background_color=self.current_color,
            on_press=self.show_color_picker
        )
        
        row2.add_widget(self.tool_spinner)
        row2.add_widget(self.color_button)
        
        # Add rows to toolbar
        toolbar.add_widget(row1)
        toolbar.add_widget(row2)
        self.add_widget(toolbar)
        
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
                
        def on_dismiss(*args):
            popup.dismiss()
            
        color_picker.bind(color=on_color)
        
        # Add a close button
        close_button = CustomButton(
            text='Done',
            size_hint_y=None,
            height=dp(50),
            on_press=on_dismiss
        )
        
        content.add_widget(color_picker)
        content.add_widget(close_button)
        
        popup = Popup(
            title='Pick a color',
            content=content,
            size_hint=(0.9, 0.9),
            auto_dismiss=True
        )
        popup.open()
        
    def show_file_chooser(self, instance):
        content = BoxLayout(orientation='vertical')
        
        if not self.file_chooser:
            self.file_chooser = FileChooserListView(
                filters=['*.svg'],
                size_hint_y=0.9
            )
            self.file_chooser.bind(on_submit=self.load_svg)
            
        content.add_widget(self.file_chooser)
        
        # Add a close button
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
                # Parse SVG file
                tree = ET.parse(svg_path)
                root = tree.getroot()
                
                # Convert elements to internal representation
                self.display_widget.clear_elements()
                self.parse_svg_elements(root)
                
            except Exception as e:
                self.show_error_popup(f"Error loading SVG: {e}")

    def show_error_popup(self, message):
        content = BoxLayout(orientation='vertical')
        content.add_widget(Label(text=message))
        close_button = CustomButton(
            text='OK',
            size_hint_y=None,
            height=dp(50),
            on_press=lambda *args: popup.dismiss()
        )
        content.add_widget(close_button)
        
        popup = Popup(
            title='Error',
            content=content,
            size_hint=(0.8, 0.4)
        )
        popup.open()

    # ... [Previous SVGElement classes remain the same] ...

class SVGDisplayWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.elements = []
        self.preview = None
        self.bind(size=self.update_canvas, pos=self.update_canvas)
        
    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return False
            
        app = App.get_running_app()
        if app.root.current_tool == 'select':
            self.selected_element = self.find_element_at(touch.pos)
        else:
            app.root.current_shape = {
                'tool': app.root.current_tool,
                'start': touch.pos,
                'color': app.root.current_color
            }
        return True
            
    def on_touch_move(self, touch):
        if not self.collide_point(*touch.pos):
            return False
            
        app = App.get_running_app()
        if app.root.current_shape:
            self.update_preview(
                app.root.current_shape['tool'],
                app.root.current_shape['start'],
                touch.pos,
                app.root.current_shape['color']
            )
        return True
            
    def on_touch_up(self, touch):
        if not self.collide_point(*touch.pos):
            return False
            
        app = App.get_running_app()
        if app.root.current_shape:
            if app.root.current_shape['tool'] == 'rectangle':
                x, y = app.root.current_shape['start']
                width = touch.x - x
                height = touch.y - y
                self.add_rectangle(x, y, width, height, app.root.current_color)
            elif app.root.current_shape['tool'] == 'circle':
                cx, cy = app.root.current_shape['start']
                r = ((touch.x - cx) ** 2 + (touch.y - cy) ** 2) ** 0.5
                self.add_circle(cx, cy, r, app.root.current_color)
            elif app.root.current_shape['tool'] == 'text':
                self.show_text_input(touch.pos)
                
            app.root.current_shape = None
            self.clear_preview()
        return True

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
            # Draw background
            Color(1, 1, 1, 1)
            Rectangle(pos=self.pos, size=self.size)
            
            # Draw elements
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
                    
            # Draw preview
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
        # Simplified hit testing for text
        return (abs(point[0] - self.x) < dp(20) and
                abs(point[1] - self.y) < dp(20))

class SVGEditorApp(App):
    def build(self):
        return SVGEditor()

if __name__ == '__main__':
    # Don't set window size on Android
    if not Window.softinput_mode:
        Window.size = (400, 600)
    SVGEditorApp().run()