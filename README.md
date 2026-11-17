# Breathing Life into Your Voice: From Testimony to Action

A standardized Playbook for Community-Led Environmental Justice in South East Los Angeles (SELA).

## Overview

This project replaces traditional "filing a complaint" with **validated testimony**. We combine community voice, sensor data, and visual evidence to create an immutable, algorithmically verified ledger.

## Core Vision

- **Voice (Community):** High-fidelity testimony via the "4 Ws" (Who, What, Where, When)
- **Vision (Technology):** PurpleAir/SCAQMD sensor data + FLIR thermal imaging
- **Action (Ground-Truth Logic):** Algorithmic validation pairing community reports with sensor spikes

## Quick Start

1. **Set up Python environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r scripts/requirements.txt
   ```

2. **Configure API credentials:**
   - PurpleAir API key → `configs/purpleair_config.json`
   - SCAQMD API key → `configs/scaqmd_config.json`
   - Google Sheets ID → `configs/google_sheets_config.json`

3. **Start the data pipeline:**
   ```bash
   python scripts/sela_imap_listener.py
   ```

## Key Components

### Data Acquisition
- **IMAP Listener:** Polls email inbox for booth form submissions
- **Form Parser:** Extracts "4 Ws" from structured email format
- **Unique Indexing:** Each report gets a unique hash ID and timestamp

### Ground-Truth Verification
- **Sensor Query:** Fetch nearest PurpleAir/SCAQMD sensor(s) to report location
- **Statistical Analysis:** Detect spikes > 2.0x standard deviation at report time
- **Verification Status:** Flag as "VERIFIED HOTSPOT" or "UNVERIFIED"

### Immutable Ledger
- **Google Sheets:** Master record of all community testimonies
- **Inspection-Ready Rows:** Each entry is documentation-auditable
- **Transparent Publishing:** All data written automatically for community access

## Environmental Predictive Risk Analyzer & Truck Idling Monitor

A Python-based analytics pipeline and local dashboard for evaluating multi-factor environmental risks and prioritizing truck idling corridors across freight and buffer zones.

### Prerequisites & Installation

Install the required Python packages from the repository root:

```bash
pip install -r requirements.txt
```

### Analyze Truck Idling Hotspots

Run the analyzer with the included sample data and select a time-of-day window. The selected multiplier scales all baseline scores proportionally, preserving the relative corridor ranking.

```bash
python predictive_risk_analyzer_hotspots.py \
  --input data/hotspots.csv \
  --time morning_peak \
  --output truck_idling_hotspots_report.csv
```

Supported time periods are `morning_peak`, `midday`, `evening_peak`, and `night`. Use `--help` to see all command-line options. If `--input` is omitted, the script runs against its built-in sample corridors.

### Launch the Local Dashboard

After generating the report, launch the Streamlit dashboard:

```bash
streamlit run app.py
```

The dashboard reads `truck_idling_hotspots_report.csv` from the current directory and displays the ranked corridors, highlighting the highest-priority hotspot.

## Bilingual Commitment

All materials (staff scripts, signage, community booklets, digital forms) are 100% English/Spanish.

## License

Apache 2.0

**Status:** In Development - MVP Phase
