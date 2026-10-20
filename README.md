# Modal Shift and Carbon Taxation: An Experimental Economics Study

[![oTree 5/6 Compatible](https://img.shields.io/badge/oTree-5%2F6-blue.svg)](https://otree.org)
[![Python 3.12](https://img.shields.io/badge/python-3.12-brightgreen.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An experimental economics research platform built in **oTree 5/6** and **Python 3.12** evaluating how behavioral framing (Loss vs Gain) impacts urban commuter modal shift under **strictly equivalent economic incentives**.

---

## 1. Project Overview & Research Question

### The Policy Context
A metropolitan transport authority wants to accelerate the modal shift of suburban commuters from private combustion cars to public transit and active mobility (cycling/walking). The authority hesitates between two policy instruments:
1. A **coercive carbon tax** on passenger vehicle fuel.
2. A **positive financial incentive** ("Clean Mobility Pass Voucher") subsidizing public transit passes.

### The Research Question
> **Which policy framing is more effective at driving commuters away from private cars: a financial loss (carbon tax penalty on car use) or an equivalent financial gain (green mobility bonus on public transit)?**

### Experimental Design & Strict Equivalence
- **Design:** Between-subject, vignette-based discrete choice experiment across 8 repeated suburban commuting situations.
- **Treatments:**
  - **Treatment A (Control):** Baseline commute costs (fuel, parking fees, standard public transit fares).
  - **Treatment B (Loss / Carbon Penalty):** The car option includes an explicit red line item:  
    `"Carbon Pollution Surcharge: +€30/month"`. Total car cost increases by €30.
  - **Treatment C (Gain / Green Bonus):** The public transit option includes an explicit green line item:  
    `"Clean Mobility Pass Voucher: −€30/month"`. Total transit cost decreases by €30.

```
       [ Control Condition A ]
Car: Base Cost  |  Transit: Base Fare
Net Advantage = Base Car - Base Transit

       [ Loss Framing B ]                          [ Gain Framing C ]
Car: Base Cost + €30 (Carbon Tax)           Car: Base Cost
Transit: Base Fare                          Transit: Base Fare - €30 (Mobility Voucher)
Net Advantage = Base + €30 - Fare           Net Advantage = Base - (Fare - €30) = Base + €30 - Fare
   ═════════════════════════════════════════════════════════════════════════════════════
          NET FINANCIAL ADVANTAGE IS STRICTLY EQUIVALENT IN B AND C: BOTH +€30 VS CONTROL
```

---

## 2. Repository Structure

```
final_otree_project/
├── settings.py                # oTree configurations & dynamic room loading
├── rooms.json                 # Source of truth for experimental rooms
├── _rooms/                    # Participant label files per room
├── dgp.py                     # Shared Data-Generating Process & persona engine
├── bots_config.json           # Simulation effect size presets (default, null, etc.)
├── intro/                     # Consent, instructions, comprehension check, assignment
├── commute_choice/            # 8 choice scenarios, admin report, custom export
├── survey_demographics/       # Socio-economic, spatial & vehicle ownership survey
├── survey_traits/             # Risk (Dohmen), Time (Falk), NEP-15
├── post_task/                 # Manipulation check, attention check, debrief
├── scripts/
│   ├── manage_rooms.py        # Room management CLI (list, add, remove)
│   ├── generate_links.py      # Link generator (CSV, printable HTML slips, QR codes)
│   ├── run_bots.py            # Automated bot runner with custom presets & export
│   └── simulate_fallback.py   # Pure-Python fallback simulation engine
├── analysis/
│   ├── prepare_data.py        # Wide-to-long cleaning, variable derivation, source tagging
│   ├── run_analysis.py        # Full econometric pipeline (LPM, Logit, Wald tests, plots)
│   ├── analysis.ipynb         # Interactive Jupyter Notebook mirroring pipeline
│   └── analysis.R             # R replication script (fixest/ggplot2)
├── test.py                    # Automated data integrity verification suite
├── app_control_panel.py       # Streamlit control panel dashboard
├── data/
│   ├── bots/                  # Synthetic bot session exports
│   ├── live/                  # Real lab/online human session exports
│   └── processed/             # Cleaned analysis_long.csv & analysis_participant.csv
├── outputs/
│   ├── bots/                  # Regression tables, figures & report for bot data
│   ├── live/                  # Regression tables, figures & report for live data
│   ├── both/                  # Pooled comparative results & parameter recovery
│   └── links/                 # Generated links, printable HTML sheets & QR codes
├── run_dev.sh / .ps1          # Server launcher scripts (Linux/macOS & Windows)
├── run_bots.sh / .ps1         # Bot launcher scripts
├── run_panel.sh / .ps1        # Control panel launcher scripts
├── requirements.txt           # Pinned python dependencies
├── .env.example               # Environment variables template
├── .gitignore                 # Version control exclusions
├── AGENT.md                   # Protocol and rules for AI coding agents
└── README.md                  # Comprehensive project documentation
```

---

## 3. Step-by-Step Installation & Environment Setup

All execution runs inside a dedicated Python virtual environment (`.venv`).

### Prerequisites
- Python 3.12 (or 3.11). *Note: Python 3.12 was selected as modern Python 3.14 breaks older C-extensions in scientific econometrics libraries.*

### Virtual Environment Setup
```bash
# macOS / Linux
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Windows PowerShell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Configuration
Copy the environment template:
```bash
cp .env.example .env
```
Default `.env` settings:
```ini
OTREE_ADMIN_PASSWORD=admin
OTREE_PRODUCTION=0
OTREE_AUTH_LEVEL=STUDY
OTREE_REST_KEY=secret_rest_key_12345
OTREE_BASE_URL=http://localhost:8000
```

---

## 4. Running the Development Server & Admin Access

### Starting the Server
```bash
# Using the helper launcher:
./run_dev.sh 8000

# Or via otree CLI:
otree devserver 8000
```
- Open your browser to: **`http://localhost:8000/`**
- oTree Admin: **`http://localhost:8000/admin`** (Username: `admin`, Password: from `.env`)
- Interactive Demo Sessions: **`http://localhost:8000/demo`**

---

## 5. Experimental Rooms & Player Link Generation

Rooms are defined in `rooms.json` and can be managed via the CLI or the Streamlit control panel.

### Listing Rooms
```bash
python scripts/manage_rooms.py list
```

### Adding a Room
```bash
python scripts/manage_rooms.py add lab_session_2 --display "Room B (40 terminals)" --labels 40 --prefix P --secure
```
*Note: Restart the oTree devserver after adding or removing rooms.*

### Generating Player Links
```bash
# Print formatted table to terminal:
python scripts/generate_links.py --room lab_session --n 30

# Export CSV file to outputs/links/:
python scripts/generate_links.py --room lab_session --n 40 --format csv

# Generate printable participant access slips (HTML):
python scripts/generate_links.py --room lab_session --n 40 --format html

# Generate individual participant QR codes:
python scripts/generate_links.py --room lab_session --n 20 --format qr
```

---

## 6. Synthetic Bot Simulation Engine

You can simulate any number of bots with customized effect sizes:

```bash
# Simulate 150 bots with baseline realistic loss aversion:
python scripts/run_bots.py --n 150 --seed 123 --preset default

# Simulate null effect (zero framing difference):
python scripts/run_bots.py --n 150 --preset null_effects

# Simulate custom effect sizes:
python scripts/run_bots.py --n 180 --beta_B -0.60 --beta_C -0.20 --beta_car_B 0.25
```

### Presets Available in `bots_config.json`:
- `default`: Loss framing ($\beta_B = -0.45$) stronger than Gain framing ($\beta_C = -0.25$).
- `null_effects`: Exactly zero framing differences ($\beta_B = 0.0, \beta_C = 0.0$).
- `gain_stronger`: Green voucher ($\beta_C = -0.50$) outperforms carbon tax ($\beta_B = -0.20$).
- `strong_loss`: Heavy loss aversion ($\beta_B = -0.75, \beta_C = -0.20$).

---

## 7. Automated Testing & Verification

Run automated branch testing:
```bash
# Test single branch conditions (6 participants each)
otree test modal_shift_A 6
otree test modal_shift_B 6
otree test modal_shift_C 6
otree test modal_shift_surveys_first 6

# Test main randomized experiment with 60 participants:
otree test modal_shift 60

# Run Data Integrity Suite on latest export:
python test.py
```

---

## 8. Econometric Analysis Pipeline

The analysis pipeline processes wide and long datasets, estimates Linear Probability Models (LPM) and Logits with **participant-clustered standard errors**, runs Wald tests, heterogeneity analysis, and compiles publication figures.

```bash
# Analyze synthetic bot data:
python analysis/run_analysis.py --source bots

# Analyze live experimental sessions:
python analysis/run_analysis.py --source live

# Pooled comparative analysis & parameter recovery:
python analysis/run_analysis.py --source both
```

All tables (CSV), figures (PNG), and scientific summaries are saved in `outputs/<source>/analysis_report.md`.

---

## 9. Streamlit Interactive Control Panel

To manage the entire lifecycle from a web GUI without terminal commands:

```bash
./run_panel.sh 8501
# Or: streamlit run app_control_panel.py
```
Open **`http://localhost:8501`** to access:
- **Server:** Live status check and quick links.
- **Rooms:** Interactive add/remove room manager.
- **Links:** Direct link tables, printable slips, and QR generator.
- **Bots:** Slider controls for effect sizes and one-click simulation.
- **Analysis:** Interactive econometric model explorer, forest plots, and ZIP bundle downloader.
- **Data:** Live session uploader and dataset inspector.

---

## 10. Hosting Live on the Internet & Participant Link Distribution

To collect real data from participants anywhere over the internet:

### Fast Path: Instant Public HTTPS Link (60 Seconds)
If your devserver is running locally (`./run_dev.sh`), create an instant secure public tunnel:
```bash
./share_live_tunnel.sh
```
This prints a public URL (e.g. `https://bright-falcon-22.loca.lt`). Send participants to:
`https://bright-falcon-22.loca.lt/room/online_open`

### 24/7 Cloud Production Hosting
For permanent cloud hosting without needing your local computer on:
- **Render.com (Free / Low Cost):** Native PostgreSQL database + Web Service running `otree prodserver`.
- **Heroku & oTree Hub (Official Academic Standard):** 1-click cloud deploy with managed PostgreSQL and Redis via [otreehub.com](https://www.otreehub.com).

See [DEPLOYMENT.md](file:///Users/arvind_govindaraj/Downloads/final_otree_project/DEPLOYMENT.md) for complete step-by-step instructions.

---

## 11. Variables & Codebook

| Variable Name | Type | Description |
| :--- | :--- | :--- |
| `participant_code` | String | Unique 8-character oTree participant identifier |
| `treatment` | Factor | Assigned condition (`A`: Control, `B`: Loss, `C`: Gain) |
| `round_number` | Integer | Round sequence (1 to 8) |
| `scenario_id` | Integer | Commuting scenario ID (1 to 8) |
| `distance_km` | Numeric | One-way commute distance (8 to 35 km) |
| `weather` | String | Scenario weather condition (Sunny, Rain, Cloudy, Foggy) |
| `shown_car_total` | Integer | Total monthly car expense shown to participant (€) |
| `shown_transit_total`| Integer | Total monthly public transit fare shown (€) |
| `net_transit_advantage`| Integer| Monthly financial advantage of transit: $Car - Transit$ (€) |
| `choice` | Factor | Mode selected: `car`, `transit`, or `active` |
| `choice_car` | Binary | 1 if private car selected, 0 otherwise |
| `choice_transit` | Binary | 1 if public transit selected, 0 otherwise |
| `choice_active` | Binary | 1 if active mobility selected, 0 otherwise |
| `rt_ms` | Integer | Decision reaction time in milliseconds |
| `age` | Integer | Participant age in years (18–99) |
| `gender` | Factor | Self-reported gender category |
| `education` | Factor | Highest level completed (Secondary to Doctorate) |
| `occupation_csp` | Factor | Socio-professional category (French INSEE CSP) |
| `income_numeric` | Numeric | Monthly household net income bracket midpoint (€) |
| `owns_car` | Binary | 1 if personal/household car owned or leased, 0 otherwise |
| `risk_general` | Integer | Dohmen general risk tolerance scale (0–10) |
| `patience_index` | Numeric | Composite normalized patience score (0.0–1.0) |
| `nep_score` | Numeric | Revised NEP Scale score (1.0–5.0; Dunlap et al., 2000) |
| `manip_seen` | Factor | Manipulation recall check response |
| `attention_passed` | Binary | 1 if instructed-response attention check passed, 0 otherwise |
| `perceived_coerciveness`| Integer| Subjective policy reactance scale (1–7) |

---

## 12. Assumptions

1. **Python Runtime:** Python 3.12 was chosen for the virtual environment. Python 3.14 contains breaking C-API changes that prevent stable installation of pre-compiled wheels for scientific packages (`numpy`, `scipy`, `pyarrow`).
2. **Econometric Stack:** `statsmodels` was implemented as the primary econometric engine rather than `pyfixest`, because `pyfixest` enforces `websockets>=12` and `click>=8` which directly conflict with oTree 5/6 core dependency pins. `statsmodels` delivers clustered standard errors, logit average marginal effects, and Wald tests with complete stability.
3. **Monthly Working Days:** Monthly commuting figures are calibrated on 22 working days per month (44 one-way trips), displayed with small-font per-trip equivalents.
4. **Active Mobility Threshold:** Active mobility (bicycle/walking) is available only for distances $\le 12$ km (Scenarios 1 and 2), reflecting urban commute feasibility.
5. **NEP Reverse Coding:** Even-numbered items on the 15-item Revised NEP Scale (Dunlap et al., 2000) are reverse-coded as $6 - \text{response}$ prior to computing the arithmetic mean score.
6. **Inattention Rate:** In the synthetic bot generator, approximately 5% of participants are modeled as inattentive (random responses, failing the instructed attention check), reflecting standard online participant pools.

---

## 13. Methodological Limitations

- **Stated vs. Revealed Preferences:** Commuters evaluate hypothetical vignettes. While vignettes provide causal internal validity and control over financial equivalence, real-world modal shift may face inertial barriers (habitual routines, transit strikes).
- **Post-Treatment Trait Measurement:** In the main session configuration, trait questionnaires are administered after the choice task. To test for potential task-induced priming, a dedicated session config `modal_shift_surveys_first` is provided to allow empirical comparison.
- **Synthetic Bot Evidence:** Synthetic bot data validates econometric parameter recovery and pipeline integrity; it represents simulated data-generating processes rather than empirical human evidence.

---

## 14. Troubleshooting & Maintenance

- **Port in Use (8000 or 8501):**  
  Run `lsof -i :8000` and `kill -9 <PID>`, or start on an alternate port: `./run_dev.sh 8005`.
- **Database Reset:**  
  If models or fields change, reset the SQLite database cleanly:
  ```bash
  otree resetdb --noinput
  ```
- **Session Label Mismatch:**  
  Ensure participant label files exist in `_rooms/` before creating secure room sessions.
