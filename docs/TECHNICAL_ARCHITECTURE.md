# Part 3: Technical Architecture (The Engine)

## 3.1 Data Acquisition (The SELA IMAP Interface)

**Code:** Python (via Google Colab or standalone)  
**Function:** Automated script that queries an email inbox (IMAP) to fetch new reports submitted from the booth's web form.  
**Instruction:** Organize reports with a simple, unique hash `_id` and timestamp.

### Data Flow

```
[Booth Tablet Form] 
    ↓ (submits via SMTP)
[Gmail Inbox: SELA_Reports]
    ↓ (IMAP listener polls every 30s)
[Python: sela_imap_listener.py]
    ↓ (parses 4Ws from email body)
[Local Queue: data/verification_queue.jsonl]
    ↓ (one JSON per line)
[Python: ground_truth_verifier.py] (next stage)
```

### Expected Email Format

Booth form submissions arrive as plain text emails:

```
WHAT: Odor
WHERE: South Gate High School, South Gate CA
WHEN: 2024-06-07T14:30:00
WHO: Diesel truck idling near parking lot
```

### Report Object (After Parsing)

```json
{
  "_id": "a7f3d2c9e1b4a5f6",
  "timestamp": "2024-06-07T14:35:42.123456Z",
  "status": "PENDING_VERIFICATION",
  "what": "Odor",
  "where": "South Gate High School, South Gate CA",
  "when": "2024-06-07T14:30:00",
  "who": "Diesel truck idling near parking lot"
}
```

---

## 3.2 The Ground-Truth Verification Logic (The Script)

**Code:** Python (querying PurpleAir/SCAQMD APIs)  
**The Logic:**

1. **Fetch nearest sensor(s)** to the report's location (using geolocation)
2. **Check for statistical spikes** (e.g., **> 2.0x standard deviation**) at the *exact time* of the resident's report
3. **If both match,** flag the report as **status: 'VERIFIED_HOTSPOT'** in the immutable Ledger
4. **If no match,** flag as **'UNVERIFIED'** (still logged for pattern analysis)

### Verification Algorithm

```python
def verify_report(report: Dict) -> Dict:
    """
    Verify report against sensor data.
    
    Returns:
        report dict with updated status and sensor references
    """
    # Parse location from WHERE field
    lat, lon = geocode(report['where'])
    
    # Query PurpleAir API for nearest sensor within 2 km
    sensor = find_nearest_sensor(lat, lon, max_distance_km=2.0)
    
    if not sensor:
        report['status'] = 'UNVERIFIED'
        report['verification_reason'] = 'No sensor nearby'
        return report
    
    # Fetch sensor data ±15 minutes from report time
    sensor_data = query_sensor_history(
        sensor_id=sensor['id'],
        start_time=report['when'] - 15min,
        end_time=report['when'] + 15min
    )
    
    # Calculate baseline mean and standard deviation
    mean = np.mean(sensor_data['pm25'])
    std = np.std(sensor_data['pm25'])
    
    # Check for spike at exact report time
    spike_value = query_sensor_at_time(sensor_id=sensor['id'], time=report['when'])
    
    # Verify: spike > 2.0x standard deviation from mean
    if spike_value > (mean + 2.0 * std):
        report['status'] = 'VERIFIED_HOTSPOT'
        report['sensor_id'] = sensor['id']
        report['spike_value'] = spike_value
        report['baseline_mean'] = mean
        report['spike_factor'] = spike_value / (mean + std)
        return report
    else:
        report['status'] = 'UNVERIFIED'
        report['verification_reason'] = 'No sensor spike detected'
        return report
```

### Sensor Integration

#### PurpleAir API
- **Endpoint:** `https://api.purpleair.com/v1/sensors`
- **Data:** Real-time PM2.5 from crowdsourced sensors throughout SELA
- **Query:** Location + time range
- **Authentication:** API key (free tier available)

#### SCAQMD (South Coast Air Quality Management District)
- **Endpoint:** SCAQMD's public data portal
- **Data:** Official regulatory PM2.5, O3, NO2 measurements
- **Query:** Station ID + date range
- **Authentication:** Public (no key required)

---

## 3.3 The SELA Ledger (Database Management)

**Tool:** Google Sheets  
**Function:** This is our master, unchangeable record of all community testimonies. Every row is inspection-ready.  
**Instruction:** All data from the script (verified or not) is automatically written to this shared Ledger for transparency.

### Ledger Schema (Google Sheets Columns)

| Column | Type | Example | Purpose |
|--------|------|---------|---------|
| `_id` | Text | `a7f3d2c9e1b4a5f6` | Unique report identifier (hash) |
| `timestamp_submitted` | DateTime | `2024-06-07T14:35:42Z` | When report was processed |
| `timestamp_report` | DateTime | `2024-06-07T14:30:00Z` | When resident observed issue |
| `what` | Text | `Odor` | Type of observation |
| `where` | Text | `South Gate HS, South Gate CA` | Location of observation |
| `when` | DateTime | `2024-06-07T14:30:00Z` | Time of observation |
| `who` | Text | `Diesel truck idling` | Source description |
| `status` | Text | `VERIFIED_HOTSPOT` | Verification result |
| `sensor_id` | Text | `purpleair_12345` | Sensor that verified |
| `spike_value` | Number | `45.3` | Sensor PM2.5 reading |
| `baseline_mean` | Number | `18.2` | Sensor baseline average |
| `spike_factor` | Number | `2.47` | Multiplier over baseline |
| `latitude` | Number | `33.9651` | Report latitude |
| `longitude` | Number | `-118.2065` | Report longitude |
| `health_impact` | Text | `Pediatric Asthma Hospitalization Zone` | Dr. London overlay |
| `enforcement_status` | Text | `Pending` | Agency action status |

### Integration with Google Sheets API

```python
def write_to_ledger(verified_report: Dict, sheet_id: str):
    """
    Write verified report to Google Sheets ledger.
    
    Args:
        verified_report: Report dict with verification results
        sheet_id: Google Sheets ID (stored in .env)
    """
    service = build('sheets', 'v4', credentials=credentials)
    
    # Append row to sheet
    values = [
        [
            verified_report['_id'],
            verified_report['timestamp'],
            verified_report['when'],
            verified_report['what'],
            verified_report['where'],
            verified_report['who'],
            verified_report['status'],
            verified_report.get('sensor_id', ''),
            verified_report.get('spike_value', ''),
            verified_report.get('baseline_mean', ''),
            verified_report.get('spike_factor', ''),
        ]
    ]
    
    body = {'values': values}
    service.spreadsheets().values().append(
        spreadsheetId=sheet_id,
        range='Ledger!A:K',
        valueInputOption='RAW',
        body=body
    ).execute()
```

### Transparency & Immutability

- **Read-Only for Community:** Ledger is shared as read-only Google Sheet with all SELA residents
- **Write-Only from Scripts:** Only automated backend scripts can append rows
- **Audit Trail:** Timestamp every entry; never delete/edit rows
- **Public Export:** Monthly export to CSV for media, health advocates, agencies

---

## 3.4 System Architecture (Full Pipeline)

```
┌─────────────────────────────────────────────────────────────┐
│                    SELA Air Quality System                   │
└─────────────────────────────────────────────────────────────┘

BOOTH EXPERIENCE (Community Data Entry)
┌────────────────────────────────────┐
│  Station 2: Tablet Form            │
│  "4 Ws" Voice Clinic               │
│  [WHAT][WHERE][WHEN][WHO]          │
└────────┬───────────────────────────┘
         │ (email submission)
         ↓
┌────────────────────────────────────┐
│  Gmail: SELA_Reports Inbox         │
│  (receives form submissions)        │
└────────┬───────────────────────────┘
         │
BACKEND DATA PIPELINE
         ↓
┌────────────────────────────────────┐
│  Python: sela_imap_listener.py     │
│  (polls IMAP every 30s)            │
│  (parses 4Ws from email)           │
│  (generates unique _id hash)       │
└────────┬───────────────────────────┘
         │ (writes JSON lines)
         ↓
┌────────────────────────────────────┐
│  File: data/verification_queue.jsonl│
│  (queued reports awaiting verify)  │
└────────┬───────────────────────────┘
         │
         ↓
┌────────────────────────────────────┐
│  Python: ground_truth_verifier.py  │
│  (fetches nearest sensor)          │
│  (queries PurpleAir/SCAQMD API)    │
│  (detects spike > 2.0x SD)         │
│  (sets status VERIFIED or UNVERIFIED)
└────────┬───────────────────────────┘
         │ (writes verified report)
         ↓
┌────────────────────────────────────┐
│  Python: ledger_writer.py          │
│  (appends row to Google Sheet)     │
│  (immutable timestamp)             │
└────────┬───────────────────────────┘
         │
LEDGER & VISUALIZATION
         ↓
┌────────────────────────────────────┐
│  Google Sheets: SELA Ledger        │
│  (master record of all reports)    │
│  (read-only for community)         │
└────────┬───────────────────────────┘
         │
         ├─→ Station 3: Live Pulse Map (WebSocket feed)
         ├─→ CARB Dashboard (monthly export)
         └─→ Dr. London Health Overlay (spatial join)
```

---

## 3.5 Deployment Options

### Option A: Google Colab (Recommended for MVP)
- No server infrastructure required
- Free tier: 12-hour runtime (run in scheduled 3-hour blocks)
- Easy credential management
- Ideal for community events (start script 30 min before booth opens)

### Option B: Raspberry Pi (Recommended for Pilot)
- Low cost (~$50)
- Runs Python 24/7 for continuous polling
- Fits in booth setup (portable)
- Local WiFi connectivity

### Option C: AWS Lambda (Recommended for Scale)
- Serverless: triggered on IMAP email arrival
- Pay-per-execution (very cheap)
- Scales automatically with report volume
- Requires AWS account setup

---

## Next Steps

1. **Set up Gmail account** for SELA_Reports inbox
2. **Create Google Sheet** with Ledger schema
3. **Get API keys** for PurpleAir and SCAQMD
4. **Deploy Python scripts** (Colab or Raspberry Pi)
5. **Test end-to-end** with sample reports before booth event
