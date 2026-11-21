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
        self.properties.append(property_data)
    
    def calculate_price_per_sqft(self, property_data: Property) -> float:
        return property_data.price / property_data.area_sqft
    
    def score_amenities(self, amenities: List[str]) -> float:
        score = 0
        for amenity in amenities:
            if amenity.lower() in self.amenity_weights:
                score += self.amenity_weights[amenity.lower()]
        return score

    def generate_report(self, property_data: Property) -> Dict:
        price_per_sqft = self.calculate_price_per_sqft(property_data)
        amenity_score = self.score_amenities(property_data.amenities)
        
        return {
            'property_id': property_data.id,
            'location': property_data.location,
            'price': property_data.price,
            'area_sqft': property_data.area_sqft,
            'price_per_sqft': price_per_sqft,
            'amenity_score': amenity_score,
            'amenities': property_data.amenities,
            'zoning_type': property_data.zoning_type,
            'distance_to_city_center': property_data.distance_to_city_center,
            'days_on_market': (datetime.now() - property_data.date_listed).days
        }

def main():
    # Create analyzer instance
    analyzer = RealEstateAnalyzer()
    
    # Create example property
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
    
    # Add property and generate report
    analyzer.add_property(example_property)
    report = analyzer.generate_report(example_property)
    
    # Print report
    print("\nProperty Analysis Report:")
    for key, value in report.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    main()
    