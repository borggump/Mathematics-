from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserListView
from kivy.core.window import Window
from kivy.graphics import Rectangle, Color
from kivy.clock import Clock
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM
from PIL import Image
import io
import os

class SVGViewer(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        
        # Create top toolbar
        toolbar = BoxLayout(size_hint_y=0.1)
        self.load_button = Button(
            text='Load SVG',
            size_hint_x=0.3,
            on_press=self.show_file_chooser
        )
        toolbar.add_widget(self.load_button)
        self.add_widget(toolbar)
        
        # Create main display area
        self.display_widget = SVGDisplayWidget()
        self.add_widget(self.display_widget)
        
        # Initialize file chooser as None
        self.file_chooser = None
        
    def show_file_chooser(self, instance):
        # Create and show file chooser
        if not self.file_chooser:
            self.file_chooser = FileChooserListView(
                filters=['*.svg'],
                size_hint_y=0.9
            )
            self.file_chooser.bind(on_submit=self.load_svg)
        
        # Remove display widget and show file chooser
        self.remove_widget(self.display_widget)
        self.add_widget(self.file_chooser)
        
    def load_svg(self, instance, selection, *args):
        if selection:
            svg_path = selection[0]
            try:
                # Convert SVG to PNG using svglib and reportlab
                drawing = svg2rlg(svg_path)
                png_data = renderPM.drawToString(drawing, fmt='PNG')
                
                # Load PNG data into display widget
                self.display_widget.load_image(png_data)
                
                # Remove file chooser and show display widget
                self.remove_widget(self.file_chooser)
                self.add_widget(self.display_widget)
                
            except Exception as e:
                print(f"Error loading SVG: {e}")

class SVGDisplayWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.image_texture = None
        self.bind(size=self._update_rect, pos=self._update_rect)
        
    def load_image(self, image_data):
        # Convert PNG data to Kivy texture
        image = Image.open(io.BytesIO(image_data))
        image_bytes = io.BytesIO()
        image.save(image_bytes, format='PNG')
        image_bytes.seek(0)
        
        # Create texture and trigger redraw
        self.image_texture = image_bytes.read()
        Clock.schedule_once(self._update_rect)
        
    def _update_rect(self, *args):
        self.canvas.clear()
        if not self.image_texture:
            return
            
        with self.canvas:
            Color(1, 1, 1, 1)  # Set color to white
            Rectangle(
                texture=self.image_texture,
                pos=self.pos,
                size=self.size
            )

class SVGViewerApp(App):
    def build(self):
        return SVGViewer()

if __name__ == '__main__':
    # Set window size
    Window.size = (400, 600)
    
    # Run the app
    SVGViewerApp().run()