
from dataclasses import dataclass
from typing import List, Dict
from enum import Enum
from datetime import datetime, timedelta

class MetricStatus(Enum):
    EXCELLENT = "Excellent"
    GOOD = "Good"
    FAIR = "Fair"
    POOR = "Poor"
    CRITICAL = "Critical"

@dataclass
class PerformanceMetric:
    name: str
    value: float
    target: float
    weight: float
    unit: str
    trend: str
    status: MetricStatus

class SupplierPerformanceSystem:
    def __init__(self):
        # 1. Performance Metrics
        self.metrics = {
            "Quality": {
                "Defect Rate": {
                    "target": 0.1,  # 0.1% defect rate
                    "weight": 20,
                    "unit": "%",
                    "thresholds": {
                        MetricStatus.EXCELLENT: 0.05,
                        MetricStatus.GOOD: 0.1,
                        MetricStatus.FAIR: 0.5,
                        MetricStatus.POOR: 1.0
                    }
                },
                "First Pass Yield": {
                    "target": 98,
                    "weight": 15,
                    "unit": "%",
                    "thresholds": {
                        MetricStatus.EXCELLENT: 99,
                        MetricStatus.GOOD: 98,
                        MetricStatus.FAIR: 95,
                        MetricStatus.POOR: 90
                    }
                },
                "Component Reliability": {
                    "target": 99.9,
                    "weight": 15,
                    "unit": "%",
                    "thresholds": {
                        MetricStatus.EXCELLENT: 99.99,
                        MetricStatus.GOOD: 99.9,
                        MetricStatus.FAIR: 99.5,
                        MetricStatus.POOR: 99.0
                    }
                }
            },
            "Delivery": {
                "On-Time Delivery": {
                    "target": 95,
                    "weight": 15,
                    "unit": "%",
                    "thresholds": {
                        MetricStatus.EXCELLENT: 98,
                        MetricStatus.GOOD: 95,
                        MetricStatus.FAIR: 90,
                        MetricStatus.POOR: 85
                    }
                },
                "Lead Time": {
                    "target": 30,
                    "weight": 10,
                    "unit": "days",
                    "thresholds": {
                        MetricStatus.EXCELLENT: 25,
                        MetricStatus.GOOD: 30,
                        MetricStatus.FAIR: 40,
                        MetricStatus.POOR: 50
                    }
                }
            },
            "Cost": {
                "Cost Reduction": {
                    "target": 5,
                    "weight": 10,
                    "unit": "%/year",
                    "thresholds": {
                        MetricStatus.EXCELLENT: 7,
                        MetricStatus.GOOD: 5,
                        MetricStatus.FAIR: 3,
                        MetricStatus.POOR: 1
                    }
                },
                "Price Competitiveness": {
                    "target": 100,
                    "weight": 15,
                    "unit": "index",
                    "thresholds": {
                        MetricStatus.EXCELLENT: 95,
                        MetricStatus.GOOD: 100,
                        MetricStatus.FAIR: 110,
                        MetricStatus.POOR: 120
                    }
                }
            }
        }

        # 2. Audit Checklist
        self.audit_checklist = {
            "Quality System": {
                "Documentation": [
                    "Quality manual review",
                    "Process control procedures",
                    "Testing protocols",
                    "Calibration records",
                    "Training records"
                ],
                "Process Control": [
                    "SPC implementation",
                    "Process capability studies",
                    "Equipment maintenance",
                    "Environmental controls",
                    "Material handling"
                ],
                "Testing": [
                    "Incoming inspection",
                    "In-process testing",
                    "Final testing",
                    "Test equipment calibration",
                    "Test data management"
                ]
            },
            "Manufacturing": {
                "Equipment": [
                    "Equipment capability",
                    "Maintenance programs",
                    "Calibration system",
                    "Process monitoring",
                    "Technology level"
                ],
                "Process": [
                    "Production planning",
                    "Workflow optimization",
                    "Capacity utilization",
                    "Inventory management",
                    "Production controls"
                ]
            },
            "Component Specific": {
                "Peltier Modules": [
                    "Temperature differential testing",
                    "Power consumption measurement",
                    "Thermal cycling durability",
                    "Sealing integrity",
                    "Performance consistency"
                ],
                "Solar Cells": [
                    "Efficiency measurement",
                    "UV stability testing",
                    "Environmental testing",
                    "Connection integrity",
                    "Power output consistency"
                ],
                "Supercapacitors": [
                    "Capacity testing",
                    "ESR measurement",
                    "Cycle life testing",
                    "Temperature performance",
                    "Safety testing"
                ]
            }
        }

        # 3. Corrective Action Procedures
        self.corrective_actions = {
            "Quality Issues": {
                "steps": [
                    "Issue identification and documentation",
                    "Root cause analysis using 5-Why",
                    "Containment actions",
                    "Corrective action implementation",
                    "Effectiveness verification"
                ],
                "timeline": "14 days",
                "verification_method": "100% inspection for 3 lots",
                "documentation": [
                    "8D report",
                    "Process change documentation",
                    "Verification data",
                    "Training records"
                ]
            },
            "Delivery Issues": {
                "steps": [
                    "Delay root cause analysis",
                    "Supply chain review",
                    "Logistics optimization",
                    "Buffer stock adjustment",
                    "Performance monitoring"
                ],
                "timeline": "7 days",
                "verification_method": "Daily delivery tracking",
                "documentation": [
                    "Delivery performance report",
                    "Supply chain analysis",
                    "Action plan",
                    "Results verification"
                ]
            },
            "Cost Issues": {
                "steps": [
                    "Cost breakdown analysis",
                    "Value engineering review",
                    "Process optimization",
                    "Material cost review",
                    "Negotiation strategy"
                ],
                "timeline": "30 days",
                "verification_method": "Monthly cost review",
                "documentation": [
                    "Cost analysis report",
                    "Improvement proposals",
                    "Implementation plan",
                    "Results verification"
                ]
            }
        }

        # 4. Scorecard Template
        self.scorecard_template = {
            "header": {
                "Supplier Name": "",
                "Component Category": "",
                "Review Period": "",
                "Overall Score": 0
            },
            "metrics": {
                "Quality": {
                    "weight": 50,
                    "categories": ["Defect Rate", "First Pass Yield", "Component Reliability"]
                },
                "Delivery": {
                    "weight": 30,
                    "categories": ["On-Time Delivery", "Lead Time"]
                },
                "Cost": {
                    "weight": 20,
                    "categories": ["Cost Reduction", "Price Competitiveness"]
                }
            },
            "improvement_plans": {
                "areas": ["Quality", "Delivery", "Cost"],
                "elements": ["Issue", "Action Plan", "Timeline", "Status"]
            }
        }

    def calculate_performance_score(self, metric_values: Dict) -> Dict:
        """Calculate overall performance score based on metrics"""
        scores = {}
        overall_score = 0
        
        for category, metrics in self.metrics.items():
            category_score = 0
            for metric_name, metric_details in metrics.items():
                if metric_name in metric_values:
                    value = metric_values[metric_name]
                    target = metric_details["target"]
                    weight = metric_details["weight"]
                    
                    # Calculate score (0-100)
                    if metric_details["unit"] == "%":
                        score = (value / target) * 100
                    else:
                        score = (target / value) * 100
                        
                    category_score += score * (weight / 100)
                    
            scores[category] = category_score
            overall_score += category_score
            
        return {
            "overall_score": overall_score,
            "category_scores": scores
        }

    def generate_scorecard(self, supplier_name: str, component_category: str, 
                          metric_values: Dict) -> Dict:
        """Generate supplier scorecard"""
        scores = self.calculate_performance_score(metric_values)
        
        scorecard = {
            "header": {
                "Supplier Name": supplier_name,
                "Component Category": component_category,
                "Review Period": f"{datetime.now().strftime('%B %Y')}",
                "Overall Score": scores["overall_score"]
            },
            "performance_metrics": scores["category_scores"],
            "status": self.get_performance_status(scores["overall_score"]),
            "recommendations": self.generate_recommendations(scores["category_scores"])
        }
        
        return scorecard

    def get_performance_status(self, score: float) -> MetricStatus:
        """Determine performance status based on score"""
        if score >= 95:
            return MetricStatus.EXCELLENT
        elif score >= 85:
            return MetricStatus.GOOD
        elif score >= 75:
            return MetricStatus.FAIR
        elif score >= 65:
            return MetricStatus.POOR
        else:
            return MetricStatus.CRITICAL

    def generate_recommendations(self, category_scores: Dict) -> List[str]:
        """Generate improvement recommendations based on scores"""
        recommendations = []
        
        for category, score in category_scores.items():
            if score < 75:
                if category == "Quality":
                    recommendations.append("Implement additional quality controls")
                elif category == "Delivery":
                    recommendations.append("Review supply chain optimization")
                elif category == "Cost":
                    recommendations.append("Conduct value engineering review")
                    
        return recommendations

if __name__ == "__main__":
    # Example usage
    sps = SupplierPerformanceSystem()
    
    # Example metric values
    sample_metrics = {
        "Defect Rate": 0.15,
        "First Pass Yield": 97,
        "Component Reliability": 99.8,
        "On-Time Delivery": 94,
        "Lead Time": 35,
        "Cost Reduction": 4,
        "Price Competitiveness": 105
    }
    
    # Generate scorecard
    scorecard = sps.generate_scorecard(
        "Sample Supplier",
        "Peltier Modules",
        sample_metrics
    )
    
    # Print results
    print("\nSupplier Scorecard:")
    print(f"Supplier: {scorecard['header']['Supplier Name']}")
    print(f"Component: {scorecard['header']['Component Category']}")
    print(f"Overall Score: {scorecard['header']['Overall Score']:.1f}")
    print(f"Status: {scorecard['status'].value}")
    
    print("\nCategory Scores:")
    for category, score in scorecard['performance_metrics'].items():
        print(f"{category}: {score:.1f}")
    
    if scorecard['recommendations']:
        print("\nRecommendations:")
        for rec in scorecard['recommendations']:
            print(f"- {rec}")
