#!/usr/bin/env python3
"""
Ground Truth Verifier
Queries PurpleAir and SCAQMD APIs to verify community reports against sensor data.

Logic:
1. Read queued reports from verification_queue.jsonl
2. For each report, fetch the nearest sensor(s) within 2 km
3. Check for statistical spikes (> 2.0x standard deviation) at report time ± 15 min
4. Flag as VERIFIED_HOTSPOT or UNVERIFIED
5. Write results to the immutable Ledger (Google Sheets)

Usage:
    python ground_truth_verifier.py --run-once
    python ground_truth_verifier.py --continuous --interval 60
"""

import os
import json
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import requests
from loguru import logger
import dotenv
from haversine import haversine, Unit

dotenv.load_dotenv()

logger.add("logs/ground_truth_verifier.log", rotation="500 MB")


class GroundTruthVerifier:
    """Verifies community reports against sensor data."""

    def __init__(
        self,
        purpleair_api_key: str = os.getenv("PURPLEAIR_API_KEY"),
        scaqmd_api_key: str = os.getenv("SCAQMD_API_KEY"),
        max_distance_km: float = float(os.getenv("VERIFICATION_MAX_DISTANCE_KM", "2.0")),
        spike_threshold: float = float(os.getenv("VERIFICATION_SPIKE_THRESHOLD", "2.0")),
        time_window_minutes: int = int(os.getenv("VERIFICATION_TIME_WINDOW_MINUTES", "15")),
    ):
        """
        Initialize Ground Truth Verifier.
        
        Args:
            purpleair_api_key: PurpleAir API key
            scaqmd_api_key: SCAQMD API key
            max_distance_km: Maximum distance to search for sensors
            spike_threshold: Multiplier for standard deviation (e.g., 2.0 = 2x SD)
            time_window_minutes: Time window around report to check sensors
        """
        self.purpleair_api_key = purpleair_api_key
        self.scaqmd_api_key = scaqmd_api_key
        self.max_distance_km = max_distance_km
        self.spike_threshold = spike_threshold
        self.time_window_minutes = time_window_minutes
        self.purpleair_base_url = "https://api.purpleair.com/v1"
        self.scaqmd_base_url = "https://www.aqmd.gov/api"

    def parse_location(self, location_str: str) -> Optional[Tuple[float, float]]:
        """
        Parse location string to lat/lon coordinates.
        Supports: "34.0195,-118.2437" or geocoded location names.
        
        For MVP, we'll support numeric coordinates only.
        Full implementation would use geopy.geocoders.Nominatim
        """
        try:
            parts = location_str.split(",")
            if len(parts) == 2:
                lat = float(parts[0].strip())
                lon = float(parts[1].strip())
                if -90 <= lat <= 90 and -180 <= lon <= 180:
                    return (lat, lon)
        except ValueError:
            pass
        
        logger.warning(f"Could not parse location: {location_str}")
        return None

    def fetch_purpleair_sensors(self, lat: float, lon: float) -> List[Dict]:
        """
        Fetch nearby PurpleAir sensors within max_distance_km.
        
        Returns list of sensor dicts with keys: sensor_id, lat, lon, pm2_5, name
        """
        try:
            # PurpleAir API v1: Get sensors near a location
            params = {
                "api_key": self.purpleair_api_key,
                "nwlng": lon - 0.05,  # Bounding box (approximate)
                "nwlat": lat + 0.05,
                "selng": lon + 0.05,
                "selat": lat - 0.05,
                "fields": "sensor_index,name,latitude,longitude,pm2.5"
            }
            
            response = requests.get(
                f"{self.purpleair_base_url}/sensors",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            sensors = []
            
            if "data" in data:
                for sensor_data in data["data"]:
                    sensor = {
                        "sensor_id": sensor_data[0],
                        "name": sensor_data[1],
                        "lat": sensor_data[2],
                        "lon": sensor_data[3],
                        "pm2_5": sensor_data[4],
                        "source": "purpleair"
                    }
                    
                    # Calculate distance
                    distance = haversine(
                        (lat, lon),
                        (sensor["lat"], sensor["lon"]),
                        unit=Unit.KILOMETERS
                    )
                    
                    if distance <= self.max_distance_km:
                        sensor["distance_km"] = distance
                        sensors.append(sensor)
            
            logger.info(f"Found {len(sensors)} PurpleAir sensors within {self.max_distance_km} km")
            return sorted(sensors, key=lambda x: x["distance_km"])
        
        except Exception as e:
            logger.error(f"Failed to fetch PurpleAir sensors: {e}")
            return []

    def fetch_scaqmd_sensors(self, lat: float, lon: float) -> List[Dict]:
        """
        Fetch nearby SCAQMD (official) monitors within max_distance_km.
        
        Returns list of sensor dicts.
        """
        try:
            # SCAQMD API: Get air quality data
            params = {
                "key": self.scaqmd_api_key,
                "latitude": lat,
                "longitude": lon,
                "distance": self.max_distance_km
            }
            
            response = requests.get(
                f"{self.scaqmd_base_url}/aqmd_monitors",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            sensors = []
            
            if "Stations" in data:
                for station in data["Stations"]:
                    sensor = {
                        "sensor_id": station.get("StationId"),
                        "name": station.get("StationName"),
                        "lat": station.get("Latitude"),
                        "lon": station.get("Longitude"),
                        "pm2_5": station.get("PM25", None),
                        "source": "scaqmd"
                    }
                    
                    distance = haversine(
                        (lat, lon),
                        (sensor["lat"], sensor["lon"]),
                        unit=Unit.KILOMETERS
                    )
                    
                    if distance <= self.max_distance_km:
                        sensor["distance_km"] = distance
                        sensors.append(sensor)
            
            logger.info(f"Found {len(sensors)} SCAQMD sensors within {self.max_distance_km} km")
            return sorted(sensors, key=lambda x: x["distance_km"])
        
        except Exception as e:
            logger.error(f"Failed to fetch SCAQMD sensors: {e}")
            return []

    def check_sensor_spike(self, sensor: Dict, report_time: str) -> bool:
        """
        Check if sensor detected a spike at report time ± time_window.
        
        For MVP: Compare against historical 7-day median (simple baseline).
        Full implementation would fetch historical data and calculate SD.
        """
        try:
            # Parse report time
            report_dt = datetime.fromisoformat(report_time)
            window_start = report_dt - timedelta(minutes=self.time_window_minutes)
            window_end = report_dt + timedelta(minutes=self.time_window_minutes)
            
            # Get sensor's current reading
            current_pm25 = sensor.get("pm2_5")
            
            if current_pm25 is None:
                logger.warning(f"No PM2.5 data for sensor {sensor['sensor_id']}")
                return False
            
            # For MVP: Assume 7-day median baseline = 20 µg/m³
            # Full implementation queries historical data
            baseline_pm25 = 20.0
            spike_threshold_value = baseline_pm25 * self.spike_threshold
            
            is_spike = current_pm25 > spike_threshold_value
            
            logger.info(
                f"Sensor {sensor['sensor_id']}: {current_pm25} µg/m³ "
                f"(threshold: {spike_threshold_value}, spike: {is_spike})"
            )
            
            return is_spike
        
        except Exception as e:
            logger.error(f"Failed to check sensor spike: {e}")
            return False

    def verify_report(self, report: Dict) -> Dict:
        """
        Verify a single report against sensor data.
        
        Returns updated report with verification status and matched sensors.
        """
        logger.info(f"Verifying report {report['_id']}: {report['what']} @ {report['where']}")
        
        # Parse location
        coords = self.parse_location(report["where"])
        if not coords:
            report["status"] = "UNVERIFIED"
            report["verification_reason"] = "Could not parse location"
            logger.warning(f"Report {report['_id']}: Could not parse location")
            return report
        
        lat, lon = coords
        
        # Fetch nearby sensors
        purpleair_sensors = self.fetch_purpleair_sensors(lat, lon)
        scaqmd_sensors = self.fetch_scaqmd_sensors(lat, lon)
        all_sensors = purpleair_sensors + scaqmd_sensors
        
        if not all_sensors:
            report["status"] = "UNVERIFIED"
            report["verification_reason"] = f"No sensors within {self.max_distance_km} km"
            logger.warning(f"Report {report['_id']}: No nearby sensors")
            return report
        
        # Check for spikes
        matched_sensors = []
        for sensor in all_sensors:
            if self.check_sensor_spike(sensor, report["when"]):
                matched_sensors.append({
                    "sensor_id": sensor["sensor_id"],
                    "name": sensor["name"],
                    "distance_km": sensor["distance_km"],
                    "source": sensor["source"],
                    "pm2_5": sensor["pm2_5"]
                })
        
        # Determine verification status
        if matched_sensors:
            report["status"] = "VERIFIED_HOTSPOT"
            report["matched_sensors"] = matched_sensors
            report["verification_reason"] = f"Matched {len(matched_sensors)} sensor(s)"
            logger.info(f"Report {report['_id']}: VERIFIED")
        else:
            report["status"] = "UNVERIFIED"
            report["verification_reason"] = "No sensor spikes detected at report time"
            logger.info(f"Report {report['_id']}: UNVERIFIED")
        
        report["verified_at"] = datetime.utcnow().isoformat()
        return report

    def process_queue(self) -> List[Dict]:
        """
        Read verification queue and process all pending reports.
        
        Returns list of verified reports.
        """
        verified_reports = []
        
        try:
            queue_file = "data/verification_queue.jsonl"
            if not os.path.exists(queue_file):
                logger.info("No verification queue found")
                return verified_reports
            
            # Read and process queue
            with open(queue_file, "r") as f:
                for line in f:
                    try:
                        report = json.loads(line)
                        if report.get("status") == "PENDING_VERIFICATION":
                            verified_report = self.verify_report(report)
                            verified_reports.append(verified_report)
                    except json.JSONDecodeError:
                        logger.error(f"Invalid JSON in queue: {line}")
                        continue
            
            logger.info(f"Verified {len(verified_reports)} reports")
            
            # Clear queue (move to archive)
            if verified_reports:
                os.rename(queue_file, queue_file.replace("queue", "archive"))
            
            return verified_reports
        
        except Exception as e:
            logger.error(f"Failed to process queue: {e}")
            return verified_reports

    def run_once(self):
        """Run verification once and exit."""
        verified_reports = self.process_queue()
        if verified_reports:
            logger.info(f"Processed {len(verified_reports)} reports")
            # Next: Write to Ledger (handled by ledger_writer.py)
            return verified_reports
        return []

    def run_continuous(self, interval_seconds: int = 60):
        """Run continuous verification loop."""
        import time
        
        logger.info(f"Starting continuous verification (interval: {interval_seconds}s)")
        try:
            while True:
                self.process_queue()
                logger.debug(f"Sleeping for {interval_seconds} seconds...")
                time.sleep(interval_seconds)
        except KeyboardInterrupt:
            logger.info("Verification interrupted by user.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ground Truth Verifier")
    parser.add_argument(
        "--run-once",
        action="store_true",
        help="Run verification once and exit"
    )
    parser.add_argument(
        "--continuous",
        action="store_true",
        help="Run continuous verification loop"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Verification interval in seconds (default: 60)"
    )
    
    args = parser.parse_args()
    
    verifier = GroundTruthVerifier()
    
    if args.run_once:
        verifier.run_once()
    elif args.continuous:
        verifier.run_continuous(interval_seconds=args.interval)
    else:
        # Default: run once
        verifier.run_once()
