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
from kivy.graphics import Rectangle, Color, Line, Ellipse
from kivy.clock import Clock
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM
from reportlab.graphics.shapes import Drawing, Rect, Circle, String
from PIL import Image
import io
import os
import xml.etree.ElementTree as ET

class SVGEditor(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.current_tool = 'select'
        self.current_color = (1, 0, 0, 1)  # Red
        self.current_shape = None
        self.selected_element = None
        
        # Create top toolbar
        self.create_toolbar()
        
        # Create main display area
        self.display_widget = SVGDisplayWidget()
        self.display_widget.bind(on_touch_down=self.on_canvas_touch)
        self.display_widget.bind(on_touch_move=self.on_canvas_move)
        self.display_widget.bind(on_touch_up=self.on_canvas_release)
        self.add_widget(self.display_widget)
        
        # Initialize file chooser as None
        self.file_chooser = None
        
    def create_toolbar(self):
        # Top toolbar
        toolbar = BoxLayout(size_hint_y=0.1)
        
        # File operations
        self.load_button = Button(
            text='Load',
            size_hint_x=0.2,
            on_press=self.show_file_chooser
        )
        self.save_button = Button(
            text='Save',
            size_hint_x=0.2,
            on_press=self.save_svg
        )
        
        # Tool selector
        self.tool_spinner = Spinner(
            text='Select',
            values=('Select', 'Rectangle', 'Circle', 'Text'),
            size_hint_x=0.2
        )
        self.tool_spinner.bind(text=self.on_tool_change)
        
        # Color picker button
        self.color_button = Button(
            text='Color',
            size_hint_x=0.2,
            background_color=self.current_color,
            on_press=self.show_color_picker
        )
        
        # Add widgets to toolbar
        toolbar.add_widget(self.load_button)
        toolbar.add_widget(self.save_button)
        toolbar.add_widget(self.tool_spinner)
        toolbar.add_widget(self.color_button)
        
        self.add_widget(toolbar)
        
    def on_tool_change(self, spinner, text):
        self.current_tool = text.lower()
        
    def show_color_picker(self, instance):
        color_picker = ColorPicker(color=self.current_color)
        
        def on_color(instance, value):
            self.current_color = value
            self.color_button.background_color = value
            if self.selected_element:
                self.selected_element.color = value
                self.display_widget.update_canvas()
        
        color_picker.bind(color=on_color)
        
        popup = Popup(
            title='Pick a color',
            content=color_picker,
            size_hint=(0.9, 0.9)
        )
        popup.open()
        
    def show_file_chooser(self, instance):
        if not self.file_chooser:
            self.file_chooser = FileChooserListView(
                filters=['*.svg'],
                size_hint_y=0.9
            )
            self.file_chooser.bind(on_submit=self.load_svg)
        
        self.remove_widget(self.display_widget)
        self.add_widget(self.file_chooser)
        
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
                
                # Remove file chooser and show display widget
                self.remove_widget(self.file_chooser)
                self.add_widget(self.display_widget)
                
            except Exception as e:
                print(f"Error loading SVG: {e}")
                
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
                
    def save_svg(self, instance):
        try:
            drawing = Drawing(400, 600)
            
            # Convert internal elements to SVG
            for element in self.display_widget.elements:
                if isinstance(element, RectElement):
                    drawing.add(Rect(
                        element.x, element.y,
                        element.width, element.height,
                        fillColor=element.color
                    ))
                elif isinstance(element, CircleElement):
                    drawing.add(Circle(
                        element.cx, element.cy, element.r,
                        fillColor=element.color
                    ))
                elif isinstance(element, TextElement):
                    drawing.add(String(
                        element.x, element.y, element.text,
                        fillColor=element.color
                    ))
            
            # Save to file
            renderPM.drawToFile(drawing, 'output.svg', fmt='SVG')
            
        except Exception as e:
            print(f"Error saving SVG: {e}")
            
    def on_canvas_touch(self, widget, touch):
        if not self.display_widget.collide_point(*touch.pos):
            return
            
        if self.current_tool == 'select':
            self.selected_element = self.display_widget.find_element_at(touch.pos)
        else:
            # Start drawing new shape
            self.current_shape = {
                'tool': self.current_tool,
                'start': touch.pos,
                'color': self.current_color
            }
            
    def on_canvas_move(self, widget, touch):
        if self.current_shape:
            # Update preview of shape being drawn
            self.display_widget.update_preview(
                self.current_shape['tool'],
                self.current_shape['start'],
                touch.pos,
                self.current_shape['color']
            )
            
    def on_canvas_release(self, widget, touch):
        if self.current_shape:
            # Finalize the shape
            if self.current_shape['tool'] == 'rectangle':
                x, y = self.current_shape['start']
                width = touch.x - x
                height = touch.y - y
                self.display_widget.add_rectangle(x, y, width, height, self.current_color)
            elif self.current_shape['tool'] == 'circle':
                cx, cy = self.current_shape['start']
                r = ((touch.x - cx) ** 2 + (touch.y - cy) ** 2) ** 0.5
                self.display_widget.add_circle(cx, cy, r, self.current_color)
            elif self.current_shape['tool'] == 'text':
                self.show_text_input(touch.pos)
                
            self.current_shape = None
            self.display_widget.clear_preview()

    def show_text_input(self, pos):
        text_input = TextInput(multiline=False)
        
        def on_text_submit(instance):
            if text_input.text:
                self.display_widget.add_text(pos[0], pos[1], text_input.text, self.current_color)
            popup.dismiss()
            
        text_input.bind(on_text_validate=on_text_submit)
        
        popup = Popup(
            title='Enter text',
            content=text_input,
            size_hint=(0.8, 0.2)
        )
        popup.open()

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
        return (abs(point[0] - self.x) < 20 and
                abs(point[1] - self.y) < 20)

class SVGDisplayWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.elements = []
        self.preview = None
        self.bind(size=self._update_rect, pos=self._update_rect)
        
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

class SVGEditorApp(App):
    def build(self):
        return SVGEditor()

if __name__ == '__main__':
    Window.size = (400, 600)
    SVGEditorApp().run()