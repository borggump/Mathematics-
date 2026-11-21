import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import List, Dict
from datetime import datetime

@dataclass
class Property:
    id: str
    price: float
    area_sqft: float
    location: str
    amenities: List[str]
    distance_to_city_center: float
    zoning_type: str
    date_listed: datetime
    
class RealEstateAnalyzer:
    def __init__(self):
        self.properties = []
        self.amenity_weights = {
            'water_access': 0.15,
            'road_access': 0.15,
            'electricity': 0.15,
            'near_schools': 0.1,
            'near_shopping': 0.1,
            'public_transport': 0.1,
            'parks_nearby': 0.08,
            'medical_facilities': 0.09,
            'good_neighborhood': 0.08
        }
        
    def add_property(self, property_data: Property):
        """Add a new property to the analysis pool"""
        self.properties.append(property_data)
        
    def calculate_price_per_sqft(self, property_data: Property) -> float:
        """Calculate price per square foot"""
        return property_data.price / property_data.area_sqft
        
    def score_amenities(self, amenities: List[str]) -> float:
        """Calculate amenity score based on weights"""
        score = 0
        for amenity in amenities:
            if amenity.lower() in self.amenity_weights:
                score += self.amenity_weights[amenity.lower()]
        return score
        
    def calculate_market_average(self) -> Dict:
        """Calculate market averages for comparison"""
        if not self.properties:
            return None
            
        total_price_per_sqft = 0
        total_amenity_score = 0
        
        for prop in self.properties:
            total_price_per_sqft += self.calculate_price_per_sqft(prop)
            total_amenity_score += self.score_amenities(prop.amenities)
            
        return {
            'avg_price_per_sqft': total_price_per_sqft / len(self.properties),
            'avg_amenity_score': total_amenity_score / len(self.properties)
        }
        
    def calculate_value_score(self, property_data: Property) -> float:
        """Calculate overall value score for a property"""
        market_avg = self.calculate_market_average()
        if not market_avg:
            return 0
            
        price_per_sqft = self.calculate_price_per_sqft(property_data)
        amenity_score = self.score_amenities(property_data.amenities)
        
        # Lower price per sqft is better
        price_score = 1 - (price_per_sqft / market_avg['avg_price_per_sqft'])
        # Higher amenity score is better
        amenity_ratio = amenity_score / market_avg['avg_amenity_score']
        
        # Combine scores (50% price, 50% amenities)
        return (price_score * 0.5) + (amenity_ratio * 0.5)
        
    def find_best_deals(self, top_n: int = 5) -> List[tuple]:
        """Find the top N best value properties"""
        if not self.properties:
            return []
            
        property_scores = []
        for prop in self.properties:
            score = self.calculate_value_score(prop)
            property_scores.append((prop, score))
            
        # Sort by score in descending order
        property_scores.sort(key=lambda x: x[1], reverse=True)
        return property_scores[:top_n]
        
    def generate_report(self, property_data: Property) -> Dict:
        """Generate a detailed analysis report for a property"""
        market_avg = self.calculate_market_average()
        if not market_avg:
            return None
            
        price_per_sqft = self.calculate_price_per_sqft(property_data)
        amenity_score = self.score_amenities(property_data.amenities)
        value_score = self.calculate_value_score(property_data)
        
        return {
            'property_id': property_data.id,
            'location': property_data.location,
            'price': property_data.price,
            'area_sqft': property_data.area_sqft,
            'price_per_sqft': price_per_sqft,
            'market_avg_price_per_sqft': market_avg['avg_price_per_sqft'],
            'amenity_score': amenity_score,
            'market_avg_amenity_score': market_avg['avg_amenity_score'],
            'value_score': value_score,
            'amenities': property_data.amenities,
            'zoning_type': property_data.zoning_type,
            'distance_to_city_center': property_data.distance_to_city_center,
            'days_on_market': (datetime.now() - property_data.date_listed).days
        }

# Example usage
def main():
    # Create analyzer instance
    analyzer = RealEstateAnalyzer()
    
    # Example property data
    example_property = Property(
        id="PROP001",
        price=250000,
        area_sqft=10000,
        location="123 Main St",
        amenities=["water_access", "road_access", "electricity", "near_schools"],
        distance_to_city_center=5.2,
        zoning_type="residential",
        date_listed=datetime(2024, 1, 1)
    )
    
    # Add property to analyzer
    analyzer.add_property(example_property)
    
    # Generate report
    report = analyzer.generate_report(example_property)
    
    # Print report
    if report:
        print("\nProperty Analysis Report:")
        for key, value in report.items():
            print(f"{key}: {value}")

if __name__ == "__main__":
    main()