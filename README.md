# Breathing Life into Your Voice: From Testimony to Action

A standardized Playbook for Community-Led Environmental Justice in South East Los Angeles (SELA).

## Overview

This project replaces traditional "filing a complaint" with **validated testimony**. We combine community voice, sensor data, and visual evidence to create an immutable, algorithmically verified "Ground-Truth Ledger" of air quality hotspots in SELA.

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

## Bilingual Commitment

All materials (staff scripts, signage, community booklets, digital forms) are 100% English/Spanish.

## License

Apache 2.0

**Status:** In Development - MVP Phase
