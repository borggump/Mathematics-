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

class SVGShape:
    def __init__(self, type_name, attributes=None):
        self.type = type_name
        self.attributes = attributes or {}
        self.transform = [1, 0, 0, 1, 0, 0]  # Identity matrix [a, b, c, d, e, f]
        self.children = []

    def apply_transform(self, points):
        transformed = []
        for i in range(0, len(points), 2):
            x, y = points[i:i+2]
            new_x = self.transform[0] * x + self.transform[2] * y + self.transform[4]
            new_y = self.transform[1] * x + self.transform[3] * y + self.transform[5]
            transformed.extend([new_x, new_y])
        return transformed

class SVGRenderer(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.shapes = []
        self.scale = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.bezier_points = 20  # Points to approximate curves

    def parse_transform(self, transform_str):
        if not transform_str:
            return [1, 0, 0, 1, 0, 0]
            
        matrix = [1, 0, 0, 1, 0, 0]
        transforms = re.findall(r'(\w+)\s*\(([-\d.,\s]+)\)', transform_str)
        
        for transform_type, args in transforms:
            values = [float(x) for x in args.replace(',', ' ').split()]
            
            if transform_type == 'translate':
                dx = values[0]
                dy = values[1] if len(values) > 1 else 0
                matrix[4] += dx
                matrix[5] += dy
                
            elif transform_type == 'scale':
                sx = values[0]
                sy = values[1] if len(values) > 1 else sx
                matrix[0] *= sx
                matrix[3] *= sy
                
            elif transform_type == 'rotate':
                angle = values[0] * pi / 180
                cos_a = cos(angle)
                sin_a = sin(angle)
                matrix[0] = cos_a
                matrix[1] = sin_a
                matrix[2] = -sin_a
                matrix[3] = cos_a
                
        return matrix

    def parse_path(self, d):
        points = []
        current_x = 0
        current_y = 0
        start_x = 0
        start_y = 0
        
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
                        start_x = current_x
                        start_y = current_y
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
                        
                    elif command in 'Hh':
                        x = float(commands[i])
                        if command == 'h':
                            x += current_x
                        points.extend([x, current_y])
                        current_x = x
                        i += 1
                        
                    elif command in 'Vv':
                        y = float(commands[i])
                        if command == 'v':
                            y += current_y
                        points.extend([current_x, y])
                        current_y = y
                        i += 1
                        
                    elif command in 'Cc':
                        x1 = float(commands[i])
                        y1 = float(commands[i+1])
                        x2 = float(commands[i+2])
                        y2 = float(commands[i+3])
                        x = float(commands[i+4])
                        y = float(commands[i+5])
                        if command == 'c':
                            x1 += current_x
                            y1 += current_y
                            x2 += current_x
                            y2 += current_y
                            x += current_x
                            y += current_y
                            
                        # Approximate Bézier curve with points
                        for t in range(self.bezier_points + 1):
                            t = t / self.bezier_points
                            t1 = (1 - t)
                            bx = t1*t1*t1*current_x + 3*t1*t1*t*x1 + 3*t1*t*t*x2 + t*t*t*x
                            by = t1*t1*t1*current_y + 3*t1*t1*t*y1 + 3*t1*t*t*y2 + t*t*t*y
                            points.extend([bx, by])
                            
                        current_x = x
                        current_y = y
                        i += 6
                        
                    elif command in 'Zz':
                        if points:
                            points.extend([start_x, start_y])
                        current_x = start_x
                        current_y = start_y
                        
                except (IndexError, ValueError) as e:
                    print(f"Error parsing path command {command}: {e}")
                    i += 1
                    
        return points

    def parse_color(self, color_str):
        if not color_str or color_str == 'none':
            return None
            
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
                
        # Named colors
        color_map = {
            'black': (0, 0, 0, 1),
            'white': (1, 1, 1, 1),
            'red': (1, 0, 0, 1),
            'green': (0, 1, 0, 1),
            'blue': (0, 0, 1, 1),
            'yellow': (1, 1, 0, 1)
        }
        return color_map.get(color_str.lower(), (0, 0, 0, 1))

    def process_svg_element(self, element, parent_transform=None):
        # Get element type and create shape object
        tag = element.tag.split('}')[-1]
        shape = SVGShape(tag, dict(element.attrib))
        
        # Apply transforms
        transform_str = element.get('transform', '')
        if transform_str:
            shape.transform = self.parse_transform(transform_str)
            if parent_transform:
                # Combine transforms
                m1 = parent_transform
                m2 = shape.transform
                shape.transform = [
                    m1[0]*m2[0] + m1[2]*m2[1],
                    m1[1]*m2[0] + m1[3]*m2[1],
                    m1[0]*m2[2] + m1[2]*m2[3],
                    m1[1]*m2[2] + m1[3]*m2[3],
                    m1[0]*m2[4] + m1[2]*m2[5] + m1[4],
                    m1[1]*m2[4] + m1[3]*m2[5] + m1[5]
                ]
        elif parent_transform:
            shape.transform = parent_transform
            
        # Process children for groups
        if tag == 'g':
            for child in element:
                child_shape = self.process_svg_element(child, shape.transform)
                if child_shape:
                    shape.children.append(child_shape)
                    
        self.shapes.append(shape)
        return shape

    def draw_shape(self, shape):
        with self.canvas:
            # Get common attributes
            stroke = shape.attributes.get('stroke')
            fill = shape.attributes.get('fill')
            stroke_width = float(shape.attributes.get('stroke-width', 1))
            
            # Set colors
            if fill and fill != 'none':
                Color(*self.parse_color(fill))
            elif stroke:
                Color(*self.parse_color(stroke))
                
            if shape.type == 'path':
                points = self.parse_path(shape.attributes.get('d', ''))
                if points:
                    scaled_points = self.scale_points(shape.apply_transform(points))
                    Line(points=scaled_points, width=stroke_width)
                    
            elif shape.type == 'rect':
                x = float(shape.attributes.get('x', 0))
                y = float(shape.attributes.get('y', 0))
                w = float(shape.attributes.get('width', 0))
                h = float(shape.attributes.get('height', 0))
                points = [x, y, x+w, y, x+w, y+h, x, y+h, x, y]
                scaled_points = self.scale_points(shape.apply_transform(points))
                Line(points=scaled_points, width=stroke_width)
                
            elif shape.type == 'circle':
                cx = float(shape.attributes.get('cx', 0))
                cy = float(shape.attributes.get('cy', 0))
                r = float(shape.attributes.get('r', 0))
                points = []
                for i in range(36):
                    angle = i * 2 * pi / 36
                    points.extend([cx + r * cos(angle), cy + r * sin(angle)])
                scaled_points = self.scale_points(shape.apply_transform(points))
                Line(points=scaled_points, width=stroke_width)
                
            elif shape.type == 'text':
                x = float(shape.attributes.get('x', 0))
                y = float(shape.attributes.get('y', 0))
                text = shape.attributes.get('text', '')
                font_size = float(shape.attributes.get('font-size', 12))
                anchor = shape.attributes.get('text-anchor', 'start')
                
                points = shape.apply_transform([x, y])
                scaled_points = self.scale_points(points)
                
                Label(
                    text=text,
                    pos=(scaled_points[0], scaled_points[1]),
                    font_size=font_size * self.scale,
                    halign='center' if anchor == 'middle' else 'left'
                )
                
            # Draw children for groups
            for child in shape.children:
                self.draw_shape(child)

    def scale_points(self, points):
        return [p * self.scale for p in points]

    def draw(self):
        self.canvas.clear()
        with self.canvas:
            Color(1, 1, 1, 1)
            Rectangle(pos=self.pos, size=self.size)
            
            for shape in self.shapes:
                self.draw_shape(shape)

class SVGViewer(App):
    def build(self):
        layout = BoxLayout(orientation='vertical')
        self.renderer = SVGRenderer()
        layout.add_widget(self.renderer)
        return layout

if __name__ == '__main__':
    SVGViewer().run()