# Breathing Life into Your Voice: From Testimony to Action
## A Standardized Playbook for Community-Led Environmental Justice in South East Los Angeles (SELA)

---

## Executive Summary

This playbook is a **scalable, replicable, and sustainable system** for converting community testimony about air quality into verified data that drives agency enforcement.

**The Core Innovation:** We don't replace regulatory agencies. We provide them with community-verified data so fast, so credible, and so medically contextualized that they *must* act.

**Three Pillars:**
1. **Voice (Community):** Structured testimony via 4 Ws (What, Where, When, Who)
2. **Vision (Technology):** Real-time sensor data + thermal imaging verification
3. **Action (Ground-Truth Logic):** Algorithmic pairing of voice + vision = immutable ledger

**Timeline:** 6-week MVP pilot (1-2 community events per week) → 3-year scale to 10+ LA neighborhoods

---

## Part 1: Strategic Vision & Core Principles

### The Problem: The Silence Gap

Residents in South East Los Angeles have stopped reporting air quality problems. Not because the air is clean. Because reporting doesn't work:

- **Traditional cycle:** Report → No feedback → Assume nothing happened → Stop reporting
- **Result in SELA:** 38% reduction in air quality complaints over 5 years
- **Cost:** Invisible pollution + invisible health crisis (highest pediatric asthma rates in CA)

### Our Solution: Validated Testimony

We replace "filing a complaint" with **"providing data."**

**The resident becomes a sensor.** Their observation gets:
1. **Structured** (4 Ws: What, Where, When, Who)
2. **Verified** (paired with sensor data)
3. **Published** (immutable ledger)
4. **Acted upon** (CARB enforcement triggered)

### Why This Works

- **For communities:** Voice validated in real-time = immediate proof of impact
- **For agencies:** No more complaints, just data = faster triage + enforcement
- **For health:** Overlay with Dr. London's pediatric asthma research = undeniable health trigger
- **For the next generation:** Silence broken → Voice becomes action → Action becomes change

---

## Part 2: The Booth Experience

### Three-Station Design

#### Station 1: FLIR Visual Proof (See the toxicity)
- **What:** Thermal imaging shows heat signatures (exhaust plumes, industrial emissions)
- **Why:** Sensors measure air. Cameras see emissions. Together = full picture.
- **Staff:** 1-2 bilingual staff members
- **Time per person:** 2-3 minutes
- **Goal:** Hook residents to transition to Station 2

#### Station 2: 4Ws Voice Clinic (Tell your story)
- **What:** Emoji-based tablet form capturing What/Where/When/Who
- **Why:** Structured data is analyzable. But emojis keep it human.
- **Staff:** 1-2 bilingual staff members
- **Time per person:** 30 seconds
- **Goal:** Capture 50-100 reports per 3-hour shift

#### Station 3: Live Pulse Map (Watch it verify)
- **What:** Large monitor showing real-time verification of reports
- **Why:** Closes the loop immediately. Resident sees their data being processed.
- **Staff:** 1 staff member
- **Time per person:** 1-2 minutes (watching)
- **Goal:** Build trust + generate social media content

### Bilingual Commitment

All staff scripts, signage, forms, and materials are **100% English/Spanish.** No exceptions.

### Materials Checklist

**Hardware:**
- [ ] FLIR thermal camera + tripod
- [ ] 2× iPad/tablets (WiFi-enabled)
- [ ] 1× Large monitor (42"-55") for live map
- [ ] Extension cords, power strips, WiFi hotspot
- [ ] Styluses for tablet accessibility

**Signage & Collateral:**
- [ ] Retractable banner (36" × 80"): "USE YOUR VOICE / USA TU VOZ"
- [ ] Station labels (bilingual)
- [ ] QR codes linking to public ledger
- [ ] Printed consent forms (bilingual)
- [ ] Community booklets: "Your Voice, Our Air" (8-page)
- [ ] Resource flyers (health clinics, CARB contact info)

**Staffing:**
- [ ] 6-9 bilingual staff (2-3 per station, 3-hour shifts)
- [ ] Staff t-shirts: "DE LA VOZ A LA ACCIÓN"
- [ ] Staff ID badges
- [ ] Training scripts (provided in STAFF_TRAINING.md)

### Success Metrics (3-Hour Shift)

| Metric | Target | Notes |
|--------|--------|-------|
| Booth foot traffic | 150-250 | Event-dependent |
| Forms submitted | 50-100 | 30-sec avg |
| Verified hotspots | 8-15 | ~15-20% rate |
| Bilingual interactions | 80%+ | Staffing ratio |
| Resident satisfaction | 90%+ | Post-event survey |
| Social media engagement | 500+ impressions | Photos + quotes |

---

## Part 3: Technical Architecture

### The Data Pipeline

```
Booth Tablet Form
    ↓ (SMTP)
Gmail: SELA_Reports Inbox
    ↓ (IMAP polling every 30s)
sela_imap_listener.py
    ↓ (parses 4Ws, generates hash ID)
data/verification_queue.jsonl
    ↓ (JSON lines queue)
ground_truth_verifier.py
    ↓ (queries PurpleAir/SCAQMD APIs)
Verification Algorithm:
  - Fetch nearest sensor(s)
  - Check for spike > 2.0x SD
  - Set status: VERIFIED or UNVERIFIED
    ↓
ledger_writer.py
    ↓ (appends to Google Sheet)
SELA Ledger (Google Sheets)
    ↓ (read-only for community)
Public Feed, CARB Dashboard, Health Overlay
```

### Report Object Schema

```json
{
  "_id": "a7f3d2c9e1b4a5f6",
  "timestamp": "2024-06-07T14:35:42Z",
  "when": "2024-06-07T14:30:00Z",
  "what": "Odor",
  "where": "South Gate High School, South Gate CA",
  "who": "Diesel truck idling",
  "status": "VERIFIED_HOTSPOT",
  "sensor_id": "purpleair_12345",
  "spike_value": 45.3,
  "baseline_mean": 18.2,
  "spike_factor": 2.47,
  "latitude": 33.9651,
  "longitude": -118.2065
}
```

### Verification Logic

**Pseudocode:**
```
FOR each report:
  1. Parse location → geocode to lat/lon
  2. Query PurpleAir API → find nearest sensor within 2 km
  3. Fetch sensor history ±15 min from report time
  4. Calculate mean + std dev of historical data
  5. Check sensor value at exact report time
  6. IF spike_value > (mean + 2.0 * std_dev):
       status = "VERIFIED_HOTSPOT"
     ELSE:
       status = "UNVERIFIED"
  7. Write to Google Sheets ledger
```

**Threshold:** > 2.0x standard deviation (conservative but defensible)

**Time window:** ±15 minutes from report time (accounts for sensor averaging)

### API Integration

**PurpleAir:**
- Free tier: 300 API calls/day
- Data: Real-time PM2.5 from crowdsourced sensors
- Coverage: Excellent in SELA (30+ sensors)
- Authentication: Simple API key

**SCAQMD:**
- Public portal: No authentication required
- Data: Official PM2.5, O3, NO2 measurements
- Coverage: Fewer stations but regulatory-grade
- Use for cross-validation of spikes

### Google Sheets Ledger

**Purpose:** Immutable, transparent record of all reports

**Columns:**
- `_id`: Unique hash
- `timestamp_submitted`: When processed
- `what/where/when/who`: 4 Ws
- `status`: VERIFIED_HOTSPOT / UNVERIFIED
- `sensor_id`: Which sensor confirmed
- `spike_value`: PM2.5 reading
- `baseline_mean`: Sensor average
- `spike_factor`: Multiplier over baseline
- `health_impact`: Dr. London overlay

**Sharing:** Read-only link to all SELA residents

### Deployment Options

**Option A: Google Colab (MVP)**
- Free tier: 12-hour runtime per session
- Run 30 min before → 4 hours after booth event
- Ideal for testing, low infrastructure
- No server needed

**Option B: Raspberry Pi (Pilot)**
- Cost: ~$50
- Runs 24/7 continuous polling
- Fits in booth
- Local WiFi connectivity

**Option C: AWS Lambda (Scale)**
- Serverless: Triggered on email arrival
- Pay-per-execution (very cheap)
- Auto-scales
- Requires AWS account

**Recommended for MVP:** Option A (Google Colab)

---

## Part 4: Agency Integration & CARB Pitch

### Strategic Positioning

We are NOT:
- Replacing regulatory agencies
- Claiming superior science
- Asking for enforcement power

We ARE:
- Providing community-verified data
- Making agency investigation faster + more targeted
- Closing the feedback loop

### The CARB Pitch (6-Slide Deck)

**Slide 1:** Problem statement (reporting fatigue in SELA)  
**Slide 2:** Our solution (voice + vision + verification)  
**Slide 3:** Data pipeline (real example with verified hotspot)  
**Slide 4:** Medical validation (overlay with Dr. London's research)  
**Slide 5:** Why CARB benefits (faster enforcement, less investigation waste)  
**Slide 6:** The ask (technical liaison for integration)

### The Close

> *"We have the data engine. We have community trust. We have medical validation. What we need is integration with your systems. A technical liaison. That's it. This closes the feedback loop. Your enforcement gets better. Our community gets healthier. Let's do this."*

### Year 1-3 Roadmap

**Months 1-6 (Pilot):**
- 5 community events
- 500-1000 verified hotspots
- CARB liaison assigned
- API integration testing

**Months 7-18 (Scale):**
- 15 community events
- 2000+ verified hotspots
- Live CARB data feed
- 50-100 enforcement actions

**Months 19-36 (Integration):**
- Ongoing community events
- 3000+ verified hotspots
- 200+ enforcement actions
- 15-20% PM2.5 reduction in SELA
- **Model exported to other LA neighborhoods**

---

## Part 5: Operational Playbook

### Pre-Event (2 weeks before)

- [ ] Secure event location (community center, farmer's market, park)
- [ ] Recruit + train staff (6-9 bilingual volunteers)
- [ ] Test all equipment (FLIR, tablets, WiFi, monitor)
- [ ] Set up email inbox (SELA_Reports@gmail.com)
- [ ] Configure API keys (PurpleAir, SCAQMD, Google Sheets)
- [ ] Create/test Python scripts locally
- [ ] Print signage + consent forms + booklets
- [ ] Coordinate with local health advocates + community leaders
- [ ] Create social media campaign (#UseYourVoice)

### Event Day (3 hours)

**T-30 min:** Arrive early, set up stations, test equipment, brief staff

**T-0:** Booth opens. Start Python IMAP listener.

**T-0 to T+180 min:** 
- Station 1: 2 staff rotating 1-2 min engagements
- Station 2: 2 staff rotating 30-sec form submissions
- Station 3: 1 staff monitoring live map feed
- Photo/video documentation

**T+180 min:** Booth closes. Collect feedback. Thank volunteers.

**T+180 to T+240 min:** 
- Let Python scripts run (catch last batch of reports)
- Review verified hotspots in real-time
- Generate social media post

### Post-Event (1 week after)

- [ ] Publish verified hotspots on public ledger
- [ ] Create social media gallery
- [ ] Thank volunteers + send feedback survey
- [ ] Compile metrics for next event
- [ ] Reach out to CARB liaison (if applicable)
- [ ] Share data with health advocates

---

## Part 6: Scaling & Sustainability

### Next Event Cycle
- Same booth experience, different neighborhood
- Rotate staff to build distributed capacity
- Increase goal: 100+ verified hotspots per event
- Build community ownership

### Resident-Led Operations (Year 2+)
- Train 2-3 SELA residents as booth coordinators
- Community members run their own events
- Ecosystem becomes self-sustaining

### Funding Model
- Phase 1: Grant funding (environmental justice orgs, foundations)
- Phase 2: Government contract (CARB pays for data feed)
- Phase 3: Hybrid (grants + agency funding + community contributions)

### Expansion to Other Neighborhoods
- Blueprint published on GitHub (this repo)
- Training materials available
- Toolkit ready for replication
- Goal: 5 LA neighborhoods by Year 3

---

## Appendix: Quick Reference

### Critical Documents
- [VISION.md](docs/VISION.md) – Strategic why
- [BOOTH_EXPERIENCE.md](docs/BOOTH_EXPERIENCE.md) – Operational how
- [TECHNICAL_ARCHITECTURE.md](docs/TECHNICAL_ARCHITECTURE.md) – System design
- [AGENCY_INTEGRATION.md](docs/AGENCY_INTEGRATION.md) – CARB strategy
- [STAFF_TRAINING.md](docs/STAFF_TRAINING.md) – Bilingual scripts

### Key Contacts
- **PurpleAir API:** https://develop.purpleair.com/
- **SCAQMD Data:** https://www.aqmd.gov/
- **Dr. Rima Habre (USC):** Pediatric air quality research
- **CARB Environmental Justice:** carb-ej@arb.ca.gov

### Metrics Dashboard
- [Public Ledger](https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID) (read-only)
- Monthly stats: Verified hotspots, enforcement actions, air quality trends

---

**This playbook belongs to the SELA community. Modify it. Own it. Scale it.**

**De la voz a la acción.**  
**From Voice to Action.**
