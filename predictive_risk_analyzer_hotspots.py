
"""
predictive_risk_analyzer.py

Environmental Predictive Risk Analyzer
with Truck Idling Hotspot Prediction
"""

from dataclasses import dataclass
from typing import List, Dict


@dataclass
class RiskFactors:
    air_quality: float
    traffic: float
    industrial_activity: float
    noise: float
    community_reports: float


class PredictiveRiskAnalyzer:
    def __init__(self):
        self.weights = {
            "air_quality": 0.35,
            "traffic": 0.20,
            "industrial_activity": 0.25,
            "noise": 0.10,
            "community_reports": 0.10,
        }

    def calculate_risk(self, factors: RiskFactors):
        score = (
            factors.air_quality * self.weights["air_quality"]
            + factors.traffic * self.weights["traffic"]
            + factors.industrial_activity * self.weights["industrial_activity"]
            + factors.noise * self.weights["noise"]
            + factors.community_reports * self.weights["community_reports"]
        )

        if score < 30:
            level = "LOW"
        elif score < 60:
            level = "MODERATE"
        elif score < 80:
            level = "HIGH"
        else:
            level = "CRITICAL"

        return {"risk_score": round(score, 2), "risk_level": level}

    def predict_truck_idling_hotspots(self, locations: List[Dict]):
        """
        Predict potential truck idling hotspots.

        Each location should contain:
        {
            "location": "Firestone Blvd & Alameda",
            "truck_count": 90,
            "complaints": 25,
            "industrial_score": 80,
            "aqi_impact": 70
        }
        """

        hotspots = []

        for loc in locations:
            hotspot_score = (
                loc["truck_count"] * 0.40
                + loc["complaints"] * 0.25
                + loc["industrial_score"] * 0.20
                + loc["aqi_impact"] * 0.15
            )

            hotspots.append({
                "location": loc["location"],
                "hotspot_score": round(hotspot_score, 2)
            })

        hotspots.sort(key=lambda x: x["hotspot_score"], reverse=True)

        return hotspots


if __name__ == "__main__":
    analyzer = PredictiveRiskAnalyzer()

    sample_locations = [
        {
            "location": "Firestone Blvd & Alameda St",
            "truck_count": 95,
            "complaints": 30,
            "industrial_score": 85,
            "aqi_impact": 78
        },
        {
            "location": "Santa Fe Ave Corridor",
            "truck_count": 80,
            "complaints": 20,
            "industrial_score": 75,
            "aqi_impact": 65
        },
        {
            "location": "South Gate Residential Buffer Zone",
            "truck_count": 45,
            "complaints": 40,
            "industrial_score": 50,
            "aqi_impact": 55
        }
    ]

    print("Predicted Truck Idling Hotspots")
    print("--------------------------------")
    for hotspot in analyzer.predict_truck_idling_hotspots(sample_locations):
        print(hotspot)
