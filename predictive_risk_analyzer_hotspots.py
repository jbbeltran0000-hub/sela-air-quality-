"""
predictive_risk_analyzer.py

Environmental Predictive Risk Analyzer
with Truck Idling Hotspot Prediction
"""

import argparse
import csv
from dataclasses import dataclass
from typing import Dict, List


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
        # Each shift applies one shared positive scaling factor, preserving the
        # relative ordering of corridors.
        self.time_multipliers = {
            "morning_peak": 1.30,  # 06:00-10:00
            "midday": 1.00,        # 10:00-15:00
            "evening_peak": 1.25,  # 15:00-19:00
            "night": 0.80,         # 19:00-06:00
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

    def predict_truck_idling_hotspots(
        self, locations: List[Dict], time_period: str = "midday"
    ) -> List[Dict]:
        """Score and rank hotspots using the selected shift multiplier."""
        if time_period not in self.time_multipliers:
            valid_periods = ", ".join(self.time_multipliers)
            raise ValueError(
                f"Unknown time period {time_period!r}. Choose from: {valid_periods}."
            )

        multiplier = self.time_multipliers[time_period]
        hotspots = []

        for loc in locations:
            base_score = (
                float(loc["truck_count"]) * 0.40
                + float(loc["complaints"]) * 0.25
                + float(loc["industrial_score"]) * 0.20
                + float(loc["aqi_impact"]) * 0.15
            )
            hotspot_score = base_score * multiplier

            hotspots.append({
                "location": loc["location"],
                "time_period": time_period,
                "multiplier_applied": multiplier,
                "hotspot_score": round(hotspot_score, 2),
            })

        # The same positive multiplier is applied to every baseline score, so
        # this ranking is identical to the ranking by baseline score.
        hotspots.sort(key=lambda item: item["hotspot_score"], reverse=True)
        return hotspots

    def export_hotspots_to_csv(
        self,
        hotspots: List[Dict],
        filename: str = "truck_idling_hotspots_report.csv",
    ) -> None:
        """Export calculated hotspot rankings to a structured CSV file."""
        fieldnames = [
            "location", "time_period", "multiplier_applied", "hotspot_score"
        ]
        with open(filename, mode="w", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(hotspots)
        print(f"\n[Export Success] Hotspot report saved to '{filename}'")


def load_locations_from_csv(filepath: str) -> List[Dict]:
    """Load and validate location records from a user-provided CSV file."""
    required_fields = {
        "location", "truck_count", "complaints", "industrial_score", "aqi_impact"
    }
    locations = []

    with open(filepath, mode="r", newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        if reader.fieldnames is None:
            raise ValueError("CSV file is empty or has no header row.")

        missing_fields = required_fields - set(reader.fieldnames)
        if missing_fields:
            raise ValueError(
                "CSV is missing required column(s): " + ", ".join(sorted(missing_fields))
            )

        for row_number, row in enumerate(reader, start=2):
            try:
                for field in ("truck_count", "complaints", "industrial_score", "aqi_impact"):
                    row[field] = float(row[field])
                if not row["location"] or not row["location"].strip():
                    raise ValueError("location must not be empty")
            except (TypeError, ValueError) as error:
                raise ValueError(f"Invalid data on CSV row {row_number}: {error}") from error
            locations.append(row)

    if not locations:
        raise ValueError("CSV contains no location records.")
    print(f"[Data Loaded] Imported {len(locations)} locations from '{filepath}'")
    return locations


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Environmental Predictive Risk & Truck Idling Hotspot Analyzer"
    )
    parser.add_argument(
        "-i", "--input",
        help=(
            "Path to a CSV containing location, truck_count, complaints, "
            "industrial_score, and aqi_impact columns"
        ),
    )
    parser.add_argument(
        "-t", "--time",
        choices=["morning_peak", "midday", "evening_peak", "night"],
        default="morning_peak",
        help="Shift window for the multiplier (default: morning_peak)",
    )
    parser.add_argument(
        "-o", "--output",
        default="truck_idling_hotspots_report.csv",
        help="Filename for the exported CSV report",
    )
    args = parser.parse_args()

    if args.input:
        try:
            locations_data = load_locations_from_csv(args.input)
        except (OSError, ValueError, csv.Error) as error:
            parser.error(f"could not load input CSV: {error}")
    else:
        print("[Notice] No input CSV provided. Using built-in sample corridor data.")
        locations_data = [
            {
                "location": "Firestone Blvd & Alameda St",
                "truck_count": 95,
                "complaints": 30,
                "industrial_score": 85,
                "aqi_impact": 78,
            },
            {
                "location": "Santa Fe Ave Corridor",
                "truck_count": 80,
                "complaints": 20,
                "industrial_score": 75,
                "aqi_impact": 65,
            },
            {
                "location": "South Gate Residential Buffer Zone",
                "truck_count": 45,
                "complaints": 40,
                "industrial_score": 50,
                "aqi_impact": 55,
            },
        ]

    analyzer = PredictiveRiskAnalyzer()
    formatted_period_name = args.time.replace("_", " ").title()
    print(f"\nPredicted Truck Idling Hotspots ({formatted_period_name})")
    print("-" * 65)

    ranked_hotspots = analyzer.predict_truck_idling_hotspots(
        locations_data, time_period=args.time
    )
    for hotspot in ranked_hotspots:
        print(hotspot)

    try:
        analyzer.export_hotspots_to_csv(ranked_hotspots, filename=args.output)
    except OSError as error:
        parser.error(f"could not write output CSV: {error}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
