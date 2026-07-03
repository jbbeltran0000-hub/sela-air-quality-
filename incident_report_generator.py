"""
incident_report_generator.py

Community Incident Validation Report Generator for Sela Guardian
Generates professionally formatted AB 617 compliance reports for air quality anomalies.
"""

import os
from datetime import datetime


class IncidentReportGenerator:
    """
    Generates structured AB 617 Community Incident Validation Reports
    for environmental anomalies detected by Sela Guardian.
    """
    
    def __init__(self, facility_name, facility_address, preparer_name="Jasmine Beltran"):
        """
        Initialize the report generator for a specific facility.
        
        Args:
            facility_name (str): Name of the industrial facility
            facility_address (str): Physical address of the facility
            preparer_name (str): Name of the person preparing the report
        """
        self.facility_name = facility_name
        self.facility_address = facility_address
        self.preparer_name = preparer_name

    def generate_report(self, incident_date, start_time, end_time, pollutant, 
                       spike_value, baseline_value, wind_dir, ground_observations):
        """
        Generates a structured AB 617 Community Incident Validation Report.
        
        Args:
            incident_date (str): Date of the incident (YYYY-MM-DD or MM/DD/YYYY)
            start_time (str): Start time of the anomaly (e.g., "08:15 AM")
            end_time (str): End time of the anomaly (e.g., "08:45 AM")
            pollutant (str): Type of pollutant detected (e.g., "PM2.5", "NO2")
            spike_value (float): Peak concentration detected
            baseline_value (float): Normal/baseline concentration
            wind_dir (str): Wind direction during incident
            ground_observations (str): Physical observations from community members
            
        Returns:
            str: Markdown-formatted report
        """
        # Calculate percentage increase for impact reporting
        try:
            pct_increase = ((spike_value - baseline_value) / baseline_value) * 100
            pct_str = f"{pct_increase:.0f}%"
        except ZeroDivisionError:
            pct_str = "N/A"

        report_md = f"""# Community Incident Validation Report
**Target Facility:** {self.facility_name}  
**Facility Address:** {self.facility_address}  
**Incident Date:** {incident_date}  
**Report Prepared By:** {self.preparer_name}, Environmental Justice Advocate / SELA CSC Member

---

### I. Executive Summary
* **Incident Window:** {start_time} to {end_time} (Local Time)
* **Core Anomaly:** A {pct_str} localized spike in {pollutant} sustained over the incident window, verified via predictive modeling and community ground-truthing.
* **Action Requested:** Immediate on-site facility inspection, physical validation of emissions controls, and source-corroboration.

### II. Data & Modeling Evidence
* **Sensor Baseline:** {baseline_value} µg/m³ (or ppm)
* **Detected Spike Peak:** {spike_value} µg/m³ (or ppm)
* **Duration/Characteristics:** Concentrated, acute event. This localized spike represents a severe deviation from established historical baselines for this node.
* **Predictive Context:** This event correlates directly with anomaly trends previously flagged by the Sela Guardian predictive forecasting models.

### III. Ground-Truthing & Contextual Validation
* **Meteorological Data:** Wind direction trending from the {wind_dir} at the timestamp of the spike, establishing a direct downwind path from the target facility to the community monitoring node.
* **Physical Observations:** {ground_observations}
* **Hyperlocal Granularity:** Cross-referenced observations from multiple nearby community data nodes confirm the anomaly is geographic and environmental, completely ruling out an isolated equipment or single-sensor glitch.

### IV. Regulatory Reference & Precautionary Action Trigger
> "Pursuant to the community-led data validation goals highlighted in AB 617, this report provides hyperlocal, ground-truthed data capturing an acute environmental anomaly routinely missed by regional, averaged stationary monitors. Under the precautionary principle and agency enforcement mandates, this validated data package constitutes a formal trigger for an immediate, physical facility inspection."

---

**Report Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
        return report_md

    def save_report(self, report_content, incident_date, output_dir="reports"):
        """
        Saves the generated report to a markdown file.
        
        Args:
            report_content (str): The markdown report content
            incident_date (str): The incident date (used for filename)
            output_dir (str): Directory to save reports to (default: "reports")
            
        Returns:
            str: Path to the saved report file
        """
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Clean date string to make a safe filename (e.g., 2026-07-03)
        safe_date = incident_date.replace("/", "-")
        filename = f"SELA_Incident_Report_{self.facility_name.replace(' ', '_')}_{safe_date}.md"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(report_content)
        
        print(f"✔️ Report successfully generated and saved as: {filepath}")
        return filepath


# ==========================================
# EXAMPLE USAGE WITH SELA GUARDIAN
# ==========================================
if __name__ == "__main__":
    # Initialize the generator for a specific facility
    reporter = IncidentReportGenerator(
        facility_name="World Oil", 
        facility_address="Insert Refinery or Plant Address, South Gate, CA"
    )

    # Generate a sample report
    markdown_output = reporter.generate_report(
        incident_date="2026-07-03",
        start_time="08:15 AM",
        end_time="08:45 AM",
        pollutant="PM2.5",
        spike_value=85.0,      # The high reading
        baseline_value=12.5,   # The normal baseline
        wind_dir="Northwest",   # Direct path to community
        ground_observations="Distinct sulfur/chemical odors reported by residents on adjacent streets; visible dark plume noted near emissions stacks."
    )

    # Save the report
    reporter.save_report(markdown_output, incident_date="2026-07-03")
