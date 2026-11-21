import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Ellipse
from scipy.optimize import minimize_scalar
import random

class ConvexShapeSlicing:
    """
    Explore cross-sections of convex shapes to illustrate concepts 
    related to Bourgain's slicing problem.
    
    Note: This is a computational exploration, not the actual proof
    which requires advanced mathematical techniques.
    """
    
    def __init__(self):
        self.shapes = {}
        
    def generate_random_convex_polygon(self, n_vertices=8, radius_range=(0.5, 2.0)):
        """Generate a random convex polygon using polar coordinates"""
        angles = sorted([random.uniform(0, 2*np.pi) for _ in range(n_vertices)])
        radii = [random.uniform(*radius_range) for _ in range(n_vertices)]
        
        points = []
        for angle, radius in zip(angles, radii):
            x = radius * np.cos(angle)
            y = radius * np.sin(angle)
            points.append([x, y])
        
        return np.array(points)
    
    def generate_ellipse_points(self, a=2, b=1, n_points=100):
        """Generate points on an ellipse boundary"""
        t = np.linspace(0, 2*np.pi, n_points)
        x = a * np.cos(t)
        y = b * np.sin(t)
        return np.column_stack([x, y])
    
    def line_polygon_intersection_length(self, polygon_points, line_angle, line_offset=0):
        """
        Calculate the length of intersection between a line and a convex polygon.
        Line is defined by: x*cos(angle) + y*sin(angle) = offset
        """
        intersections = []
        n = len(polygon_points)
        
        cos_a, sin_a = np.cos(line_angle), np.sin(line_angle)
        
        for i in range(n):
            p1 = polygon_points[i]
            p2 = polygon_points[(i + 1) % n]
            
            # Line segment from p1 to p2
            x1, y1 = p1
            x2, y2 = p2
            
            # Check if line intersects this edge
            d1 = x1 * cos_a + y1 * sin_a - line_offset
            d2 = x2 * cos_a + y2 * sin_a - line_offset
            
            if d1 * d2 <= 0:  # Different sides of line (or on line)
                if abs(d1 - d2) > 1e-10:  # Not parallel
                    t = d1 / (d1 - d2)
                    ix = x1 + t * (x2 - x1)
                    iy = y1 + t * (y2 - y1)
                    intersections.append([ix, iy])
        
        if len(intersections) >= 2:
            # Calculate distance between intersection points
            p1, p2 = intersections[0], intersections[1]
            return np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
        
        return 0
    
    def find_maximum_cross_section(self, polygon_points, n_angles=360):
        """Find the angle that gives the maximum cross-section length"""
        angles = np.linspace(0, np.pi, n_angles)  # Only need 0 to π due to symmetry
        max_length = 0
        best_angle = 0
        lengths = []
        
        for angle in angles:
            length = self.line_polygon_intersection_length(polygon_points, angle)
            lengths.append(length)
            if length > max_length:
                max_length = length
                best_angle = angle
                
        return best_angle, max_length, angles, lengths
    
    def calculate_shape_properties(self, polygon_points):
        """Calculate basic properties of the shape"""
        # Area using shoelace formula
        n = len(polygon_points)
        area = 0
        for i in range(n):
            j = (i + 1) % n
            area += polygon_points[i][0] * polygon_points[j][1]
            area -= polygon_points[j][0] * polygon_points[i][1]
        area = abs(area) / 2
        
        # Perimeter
        perimeter = 0
        for i in range(n):
            j = (i + 1) % n
            dx = polygon_points[j][0] - polygon_points[i][0]
            dy = polygon_points[j][1] - polygon_points[i][1]
            perimeter += np.sqrt(dx*dx + dy*dy)
        
        # Centroid
        cx = np.mean(polygon_points[:, 0])
        cy = np.mean(polygon_points[:, 1])
        
        return area, perimeter, (cx, cy)
    
    def visualize_slicing_experiment(self, shape_name="random"):
        """Visualize cross-sections of a convex shape"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        
        # Generate or use existing shape
        if shape_name == "random":
            points = self.generate_random_convex_polygon()
        elif shape_name == "ellipse":
            points = self.generate_ellipse_points()
        else:
            points = self.generate_random_convex_polygon()
        
        area, perimeter, centroid = self.calculate_shape_properties(points)
        best_angle, max_length, angles, lengths = self.find_maximum_cross_section(points)
        
        # Plot 1: Original shape with maximum cross-section
        ax1.add_patch(Polygon(points, alpha=0.3, color='blue'))
        ax1.plot(points[:, 0], points[:, 1], 'bo-', markersize=4)
        
        # Draw the maximum cross-section line
        cos_a, sin_a = np.cos(best_angle), np.sin(best_angle)
        x_range = np.linspace(-3, 3, 100)
        y_line = (-cos_a * x_range) / sin_a  # Rearranged line equation
        ax1.plot(x_range, y_line, 'r-', linewidth=2, label=f'Max cross-section (length: {max_length:.2f})')
        
        ax1.set_xlim(-3, 3)
        ax1.set_ylim(-3, 3)
        ax1.set_aspect('equal')
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        ax1.set_title(f'Convex Shape with Maximum Cross-Section\nArea: {area:.2f}, Perimeter: {perimeter:.2f}')
        
        # Plot 2: Cross-section lengths vs angle
        ax2.plot(angles * 180/np.pi, lengths, 'b-', linewidth=2)
        ax2.axhline(y=max_length, color='r', linestyle='--', alpha=0.7, label=f'Maximum: {max_length:.2f}')
        ax2.axhline(y=np.mean(lengths), color='g', linestyle='--', alpha=0.7, label=f'Average: {np.mean(lengths):.2f}')
        ax2.set_xlabel('Angle (degrees)')
        ax2.set_ylabel('Cross-section Length')
        ax2.set_title('Cross-section Length vs Cutting Angle')
        ax2.grid(True, alpha=0.3)
        ax2.legend()
        
        # Plot 3: Multiple random cross-sections
        ax3.add_patch(Polygon(points, alpha=0.3, color='blue'))
        ax3.plot(points[:, 0], points[:, 1], 'bo-', markersize=4)
        
        # Show several random cross-sections
        random_angles = [random.uniform(0, np.pi) for _ in range(5)]
        colors = ['red', 'green', 'orange', 'purple', 'brown']
        
        for i, angle in enumerate(random_angles):
            cos_a, sin_a = np.cos(angle), np.sin(angle)
            y_line = (-cos_a * x_range) / sin_a
            length = self.line_polygon_intersection_length(points, angle)
            ax3.plot(x_range, y_line, color=colors[i], linewidth=1.5, 
                    alpha=0.7, label=f'Angle {angle*180/np.pi:.0f}°: {length:.2f}')
        
        ax3.set_xlim(-3, 3)
        ax3.set_ylim(-3, 3)
        ax3.set_aspect('equal')
        ax3.grid(True, alpha=0.3)
        ax3.legend()
        ax3.set_title('Multiple Cross-Sections')
        
        # Plot 4: Statistics and Bourgain's question illustration
        ax4.text(0.1, 0.9, "Bourgain's Slicing Problem:", fontsize=14, fontweight='bold', transform=ax4.transAxes)
        ax4.text(0.1, 0.8, f"Shape area: {area:.3f}", fontsize=12, transform=ax4.transAxes)
        ax4.text(0.1, 0.7, f"Maximum cross-section: {max_length:.3f}", fontsize=12, transform=ax4.transAxes)
        ax4.text(0.1, 0.6, f"Minimum cross-section: {min(lengths):.3f}", fontsize=12, transform=ax4.transAxes)
        ax4.text(0.1, 0.5, f"Average cross-section: {np.mean(lengths):.3f}", fontsize=12, transform=ax4.transAxes)
        ax4.text(0.1, 0.4, f"Ratio (max/area): {max_length/area:.3f}", fontsize=12, transform=ax4.transAxes)
        
        ax4.text(0.1, 0.25, "The conjecture asks: Is there always", fontsize=11, transform=ax4.transAxes)
        ax4.text(0.1, 0.2, "a cross-section larger than some", fontsize=11, transform=ax4.transAxes)
        ax4.text(0.1, 0.15, "fixed bound (independent of shape)?", fontsize=11, transform=ax4.transAxes)
        ax4.text(0.1, 0.05, "Answer: YES (proven in 2025!)", fontsize=12, fontweight='bold', 
                color='green', transform=ax4.transAxes)
        
        ax4.set_xlim(0, 1)
        ax4.set_ylim(0, 1)
        ax4.axis('off')
        
        plt.tight_layout()
        plt.show()
        
        return {
            'points': points,
            'area': area,
            'perimeter': perimeter,
            'max_cross_section': max_length,
            'min_cross_section': min(lengths),
            'avg_cross_section': np.mean(lengths),
            'best_angle': best_angle
        }
    
    def run_multiple_experiments(self, n_experiments=10):
        """Run experiments on multiple random shapes"""
        results = []
        
        print("Running multiple slicing experiments...")
        print("=" * 50)
        
        for i in range(n_experiments):
            points = self.generate_random_convex_polygon()
            area, perimeter, centroid = self.calculate_shape_properties(points)
            best_angle, max_length, angles, lengths = self.find_maximum_cross_section(points)
            
            result = {
                'experiment': i+1,
                'area': area,
                'perimeter': perimeter,
                'max_cross_section': max_length,
                'min_cross_section': min(lengths),
                'avg_cross_section': np.mean(lengths),
                'ratio_max_to_area': max_length / area
            }
            results.append(result)
            
            print(f"Experiment {i+1:2d}: Area={area:6.3f}, Max Cross-section={max_length:6.3f}, Ratio={max_length/area:6.3f}")
        
        print("=" * 50)
        
        # Summary statistics
        ratios = [r['ratio_max_to_area'] for r in results]
        max_crosses = [r['max_cross_section'] for r in results]
        areas = [r['area'] for r in results]
        
        print(f"Summary across {n_experiments} random convex shapes:")
        print(f"Average max cross-section: {np.mean(max_crosses):.3f}")
        print(f"Average ratio (max cross-section / area): {np.mean(ratios):.3f}")
        print(f"Minimum ratio observed: {min(ratios):.3f}")
        print(f"Standard deviation of ratios: {np.std(ratios):.3f}")
        print("\nBourgain's conjecture suggests there exists a universal")
        print("lower bound that works for ALL convex shapes!")
        
        return results

# Example usage
if __name__ == "__main__":
    slicer = ConvexShapeSlicing()
    
    print("Exploring Bourgain's Slicing Problem")
    print("====================================")
    print("This program demonstrates cross-sections of 2D convex shapes.")
    print("The actual problem deals with n-dimensional convex bodies.\n")
    
    # Visualize one shape in detail
    result = slicer.visualize_slicing_experiment("random")
    
    # Run multiple experiments
    print("\n" + "="*60)
    results = slicer.run_multiple_experiments(10)