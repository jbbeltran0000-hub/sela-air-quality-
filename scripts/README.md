# Python scripts for SELA Air Quality data pipeline

This directory contains the backend Python scripts that power the ground-truth verification system.

## Scripts

- `sela_imap_listener.py` - Polls email inbox for booth form submissions
- `ground_truth_verifier.py` - Queries sensors and detects spikes
- `ledger_writer.py` - Writes verified reports to Google Sheets
- `requirements.txt` - Python dependencies
