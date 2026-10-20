"""
Streamlit Control Panel for Modal Shift & Carbon Taxation Experiment.
Interactive research management interface covering:
1. Server status and oTree admin access
2. Room management & participant label generator
3. Link generator (CSV, printable HTML, QR codes)
4. Bot simulation engine with configurable effect sizes & presets
5. Econometric analysis execution & interactive reporting (live, bots, both)
6. Data repository & session export uploader
"""

import os
import sys
import json
import zipfile
import subprocess
from pathlib import Path
import pandas as pd
import requests
import streamlit as st

# Configure page layout and aesthetics
st.set_page_config(
    page_title="Modal Shift & Carbon Tax: Experiment Control Panel",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))
import dgp
from scripts.manage_rooms import load_rooms, save_rooms
from scripts.generate_links import get_room_labels

# CSS styles
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1e3a8a;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #64748b;
        margin-bottom: 1.5rem;
    }
    .status-badge-ok {
        background-color: #d1fae5;
        color: #065f46;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
    }
    .status-badge-fail {
        background-color: #fee2e2;
        color: #991b1b;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
    }
    .metric-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        padding: 15px;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">Modal Shift and Carbon Taxation</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Experimental Economics Management, Bot Simulation & Econometrics Dashboard</div>', unsafe_allow_html=True)

# Sidebar
st.sidebar.title("Navigation")
base_url = st.sidebar.text_input("oTree Base URL", os.getenv("OTREE_BASE_URL", "http://localhost:8000"))

# Check server status
server_online = False
try:
    r = requests.get(base_url, timeout=1.5)
    server_online = (r.status_code == 200)
except Exception:
    server_online = False

if server_online:
    st.sidebar.markdown('Server Status: <span class="status-badge-ok">ONLINE</span>', unsafe_allow_html=True)
else:
    st.sidebar.markdown('Server Status: <span class="status-badge-fail">OFFLINE</span>', unsafe_allow_html=True)

st.sidebar.markdown(f"[Open oTree Admin]({base_url}/admin)")
st.sidebar.markdown(f"[Open Demo Sessions]({base_url}/demo)")
st.sidebar.markdown("---")
st.sidebar.info("Tip: Start the devserver using `./run_dev.sh` or `otree devserver`.")

# Main Tabs
tabs = st.tabs(["🖥️ Server", "🏢 Rooms", "🔗 Links", "🤖 Bots & Simulation", "📊 Econometric Analysis", "📁 Data Management"])

# -----------------------------------------------------------------------------
# TAB 1: SERVER
# -----------------------------------------------------------------------------
with tabs[0]:
    st.subheader("oTree Experimental Server Status")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Base URL", base_url)
    with col2:
        st.metric("Server Status", "Active (Online)" if server_online else "Not Detected (Offline)")
    with col3:
        st.metric("Admin Password", "Configured (from .env)")

    st.markdown("### Server Quick Actions")
    st.write("To launch or restart the oTree server:")
    st.code("./run_dev.sh", language="bash")
    st.write("Or on Windows PowerShell:")
    st.code(".\\run_dev.ps1", language="powershell")

    st.markdown("### Direct Links")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.link_button("Go to Admin Interface", f"{base_url}/admin")
    with c2:
        st.link_button("View Demo Configurations", f"{base_url}/demo")
    with c3:
        st.link_button("View Rooms Portal", f"{base_url}/rooms")

# -----------------------------------------------------------------------------
# TAB 2: ROOMS
# -----------------------------------------------------------------------------
with tabs[1]:
    st.subheader("Manage Experimental Rooms (rooms.json)")
    rooms = load_rooms()

    room_rows = []
    for r in rooms:
        lfile = r.get('participant_label_file', 'Open (No labels)')
        lcount = 0
        if 'participant_label_file' in r:
            lp = PROJECT_ROOT / r['participant_label_file']
            if lp.exists():
                with open(lp, 'r') as f:
                    lcount = len([x.strip() for x in f if x.strip()])
        room_rows.append({
            "Room Name": r['name'],
            "Display Name": r.get('display_name', ''),
            "Label File": lfile,
            "Participant Count": lcount
        })

    st.dataframe(pd.DataFrame(room_rows), use_container_width=True)

    st.warning("⚠️ Any modifications to rooms require restarting the oTree server.")

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("#### Add New Room")
        with st.form("add_room_form"):
            new_name = st.text_input("Internal Room Name (e.g. lab_session_2)", "")
            new_disp = st.text_input("Display Title", "")
            new_count = st.number_input("Number of Participant Labels", min_value=0, max_value=200, value=30)
            new_prefix = st.text_input("Label Prefix", "P")
            submitted = st.form_submit_button("Add Room")
            if submitted and new_name:
                cmd = [sys.executable, str(PROJECT_ROOT / 'scripts' / 'manage_rooms.py'), 'add', new_name, '--display', new_disp, '--labels', str(new_count), '--prefix', new_prefix]
                res = subprocess.run(cmd, capture_output=True, text=True)
                if res.returncode == 0:
                    st.success(f"Room '{new_name}' created successfully. Please restart oTree server.")
                    st.experimental_rerun()
                else:
                    st.error(res.stderr or res.stdout)

    with col_b:
        st.markdown("#### Remove Room")
        with st.form("remove_room_form"):
            room_to_remove = st.selectbox("Select Room to Remove", [r['name'] for r in rooms if r['name'] not in ('lab_session', 'online_open')])
            remove_submitted = st.form_submit_button("Delete Selected Room")
            if remove_submitted and room_to_remove:
                cmd = [sys.executable, str(PROJECT_ROOT / 'scripts' / 'manage_rooms.py'), 'remove', room_to_remove]
                res = subprocess.run(cmd, capture_output=True, text=True)
                if res.returncode == 0:
                    st.success(f"Room '{room_to_remove}' deleted.")
                    st.experimental_rerun()
                else:
                    st.error(res.stderr or res.stdout)

# -----------------------------------------------------------------------------
# TAB 3: LINKS
# -----------------------------------------------------------------------------
with tabs[2]:
    st.subheader("Participant Access Links & QR Generator")
    room_names = [r['name'] for r in rooms]
    selected_room = st.selectbox("Choose Room", room_names, index=0)
    n_links = st.slider("Number of Player Links", min_value=1, max_value=100, value=30)

    room_wide_url = f"{base_url}/room/{selected_room}/"
    st.markdown(f"**Room-wide Access URL:** [{room_wide_url}]({room_wide_url})")

    labels = get_room_labels(selected_room, n_links)
    links_data = []
    for lbl in labels:
        p_url = f"{base_url}/room/{selected_room}/?participant_label={lbl}"
        links_data.append({"Label": lbl, "URL": p_url})

    df_links = pd.DataFrame(links_data)
    st.dataframe(df_links, use_container_width=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        csv_bytes = df_links.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Links (CSV)", data=csv_bytes, file_name=f"{selected_room}_links.csv", mime="text/csv")
    with col2:
        # Run generate_links for HTML
        html_path = PROJECT_ROOT / 'outputs' / 'links' / f"{selected_room}_links.html"
        subprocess.run([sys.executable, str(PROJECT_ROOT / 'scripts' / 'generate_links.py'), '--room', selected_room, '--n', str(n_links), '--format', 'html'], capture_output=True)
        if html_path.exists():
            with open(html_path, 'r', encoding='utf-8') as f:
                st.download_button("🖨️ Download Printable HTML Slips", data=f.read(), file_name=f"{selected_room}_slips.html", mime="text/html")
    with col3:
        if st.button("Generate QR Code Pack"):
            subprocess.run([sys.executable, str(PROJECT_ROOT / 'scripts' / 'generate_links.py'), '--room', selected_room, '--n', str(min(10, n_links)), '--format', 'qr'], capture_output=True)
            st.success("QR Codes generated in outputs/links/qr_" + selected_room)

# -----------------------------------------------------------------------------
# TAB 4: BOTS & SIMULATION
# -----------------------------------------------------------------------------
with tabs[3]:
    st.subheader("Synthetic Bot Simulation & Parameter Injection")
    st.markdown("Inject known treatment framing effects and generate simulated participants.")

    cfg = dgp.load_bots_config()
    presets_dict = {
        "default": "Baseline: Loss (-0.45) > Gain (-0.25)",
        "null_effects": "Null Hypothesis: Zero framing effects (0.00)",
        "gain_stronger": "Bonus Dominance: Gain (-0.50) > Loss (-0.20)",
        "strong_loss": "Strong Loss Aversion: Loss (-0.75) > Gain (-0.20)"
    }

    c1, c2, c3 = st.columns(3)
    with c1:
        n_sim_bots = st.number_input("Number of Bots to Simulate", min_value=6, max_value=600, value=150, step=6)
    with c2:
        sim_preset = st.selectbox("Behavioral Preset", list(presets_dict.keys()), format_func=lambda x: presets_dict[x])
    with c3:
        sim_seed = st.number_input("Simulation Seed", min_value=1, max_value=99999, value=123)

    st.markdown("#### Effect Size Customization (Overrides)")
    p_cols = st.columns(4)
    with p_cols[0]:
        beta_b = st.slider("beta_B: Loss Framing (Carbon Tax)", min_value=-1.2, max_value=0.2, value=-0.45, step=0.05)
    with p_cols[1]:
        beta_c = st.slider("beta_C: Gain Framing (Clean Voucher)", min_value=-1.2, max_value=0.2, value=-0.25, step=0.05)
    with p_cols[2]:
        beta_nep_c = st.slider("NEP × Voucher Interaction", min_value=-0.5, max_value=0.2, value=-0.15, step=0.05)
    with p_cols[3]:
        beta_car_b = st.slider("Car Ownership × Tax Reactance", min_value=-0.2, max_value=0.6, value=0.15, step=0.05)

    if st.button("🚀 Run Bot Simulation", type="primary"):
        with st.spinner(f"Simulating {n_sim_bots} participants and running oTree tests..."):
            cmd = [
                sys.executable,
                str(PROJECT_ROOT / 'scripts' / 'run_bots.py'),
                '--n', str(n_sim_bots),
                '--preset', sim_preset,
                '--seed', str(sim_seed),
                '--beta_B', str(beta_b),
                '--beta_C', str(beta_c),
                '--beta_nep_C', str(beta_nep_c),
                '--beta_car_B', str(beta_car_b)
            ]
            res = subprocess.run(cmd, capture_output=True, text=True)
            st.text_area("Execution Log", res.stdout if res.returncode == 0 else (res.stderr + "\n" + res.stdout), height=200)

            latest_export = PROJECT_ROOT / 'data' / 'bots' / 'latest' / 'commute_choice_custom.csv'
            if latest_export.exists():
                df_prev = pd.read_csv(latest_export)
                st.success(f"Simulation completed: {len(df_prev)} choice rounds generated for {df_prev['participant_code'].nunique()} participants.")
                st.dataframe(df_prev.head(10), use_container_width=True)

# -----------------------------------------------------------------------------
# TAB 5: ECONOMETRIC ANALYSIS
# -----------------------------------------------------------------------------
with tabs[4]:
    st.subheader("Econometric Estimation & Hypothesis Testing")
    an_source = st.radio("Select Target Data Source", ["bots", "live", "both"], horizontal=True, index=0)

    if st.button("📊 Run Econometric Analysis", type="primary"):
        with st.spinner(f"Estimating LPM, Logit, Wald Tests, and generating publication figures for '{an_source}'..."):
            cmd = [sys.executable, str(PROJECT_ROOT / 'analysis' / 'run_analysis.py'), '--source', an_source]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode != 0:
                st.error("Analysis failed. Stderr:\n" + res.stderr)
            else:
                st.success("Econometric models estimated and publication figures compiled.")

    out_folder = PROJECT_ROOT / 'outputs' / an_source
    if out_folder.exists() and (out_folder / 'analysis_report.md').exists():
        st.markdown("### Executive Econometric Report")
        with open(out_folder / 'analysis_report.md', 'r', encoding='utf-8') as f:
            report_text = f.read()

        # Display report without raw markdown images to embed properly
        st.markdown(report_text.split("---")[0])

        # Main regression table
        reg_table_path = out_folder / 'table_main_regression.csv'
        if reg_table_path.exists():
            st.markdown("#### Primary Regression Results (Participant-Clustered SEs)")
            st.dataframe(pd.read_csv(reg_table_path), use_container_width=True)

        # Figures
        f_cols1 = st.columns(2)
        with f_cols1[0]:
            p1 = out_folder / 'car_share_by_treatment.png'
            if p1.exists():
                st.image(str(p1), caption="Private Car Share by Policy Framing (95% CI)")
        with f_cols1[1]:
            p2 = out_folder / 'coefficients_forest_plot.png'
            if p2.exists():
                st.image(str(p2), caption="Econometric Coefficient Estimates (Forest Plot)")

        f_cols2 = st.columns(2)
        with f_cols2[0]:
            p3 = out_folder / 'traits_distribution.png'
            if p3.exists():
                st.image(str(p3), caption="Participant Traits Distributions")
        with f_cols2[1]:
            p4 = out_folder / 'parameter_recovery_plot.png'
            if p4.exists():
                st.image(str(p4), caption="Parameter Recovery: Injected vs Estimated Effects")

        # Zip download
        zip_path = out_folder / f"{an_source}_results_bundle.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            for file in out_folder.iterdir():
                if file.name != zip_path.name:
                    zf.write(file, arcname=file.name)

        with open(zip_path, 'rb') as f:
            st.download_button("📦 Download Complete Analysis Bundle (Zip)", data=f.read(), file_name=f"{an_source}_results.zip", mime="application/zip")

# -----------------------------------------------------------------------------
# TAB 6: DATA REPOSITORY
# -----------------------------------------------------------------------------
with tabs[5]:
    st.subheader("Data Repository & Live Session Uploader")
    st.markdown("Upload raw CSV exports downloaded from the oTree Admin `Data` tab to incorporate real session participants.")

    uploaded_file = st.file_uploader("Upload oTree CSV Export (all_apps_wide.csv or custom export)", type=['csv'])
    if uploaded_file is not None:
        save_dest = PROJECT_ROOT / 'data' / 'live' / 'uploaded_sessions'
        save_dest.mkdir(parents=True, exist_ok=True)
        target_csv = save_dest / uploaded_file.name
        with open(target_csv, 'wb') as f:
            f.write(uploaded_file.getbuffer())
        st.success(f"File uploaded to {target_csv}. Re-run data preparation to analyze.")

    st.markdown("### Processed Datasets Preview")
    proc_long = PROJECT_ROOT / 'data' / 'processed' / 'analysis_long.csv'
    proc_part = PROJECT_ROOT / 'data' / 'processed' / 'analysis_participant.csv'

    if proc_long.exists():
        df_l = pd.read_csv(proc_long)
        st.write(f"**Long Dataset (`analysis_long.csv`):** {len(df_l)} rows, {df_l['participant_code'].nunique()} participants")
        st.dataframe(df_l.head(15), use_container_width=True)

    if proc_part.exists():
        df_p = pd.read_csv(proc_part)
        st.write(f"**Participant Dataset (`analysis_participant.csv`):** {len(df_p)} participants")
        st.dataframe(df_p.head(15), use_container_width=True)
