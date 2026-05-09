import os
import yaml
import glob
import streamlit as st

# Set page config for a professional GIS Portal experience
st.set_page_config(
    page_title="GMet-Style IMERG Dry Spell Portal",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS to mimic the premium, clean layout of the GMet Atlas
st.markdown("""
    <style>
        /* Main page adjustments */
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2rem;
        }
        /* Top Header Styling */
        .gmet-header {
            background-color: #1a252c;
            padding: 1.5rem;
            border-radius: 8px;
            margin-bottom: 1.5rem;
            color: #ffffff;
            border-left: 5px solid #009688;
        }
        /* Card aesthetics for spatial outputs */
        .map-card {
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 1rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        }
    </style>
""", unsafe_allow_html=True)

# Load Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(BASE_DIR, "config.yaml"), "r") as f:
    config = yaml.safe_load(f)

# Path Override for Streamlit Cloud
LOCAL_PLOTS_DIR = config["output_dir"]
RELATIVE_PLOTS_DIR = os.path.abspath(os.path.join(BASE_DIR, "../data/plots"))

if os.path.exists(RELATIVE_PLOTS_DIR):
    PLOTS_DIR = RELATIVE_PLOTS_DIR
else:
    PLOTS_DIR = LOCAL_PLOTS_DIR

# ---------------------------------------------------------
# 1. PREMIUM HEADER (GMet Atlas Style)
# ---------------------------------------------------------
st.markdown(f"""
    <div class="gmet-header">
        <h2 style='margin:0; font-weight:700; font-size:24px;'>🛰️ CLIMATE MONITORING PLATFORM — WEST AFRICA</h2>
        <p style='margin:5px 0 0 0; font-size:14px; color:#a0aec0; letter-spacing: 0.5px;'>
            HIGH-RESOLUTION IMERG SATELLITE PRECIPITATION ANALYSIS • METEO GHANA COMPATIBLE
        </p>
    </div>
""", unsafe_allow_html=True)

# Fetch processed files
plot_files = sorted(glob.glob(os.path.join(PLOTS_DIR, "*.png")))

if not plot_files:
    st.warning(f"⚠️ No plot outputs found in `{PLOTS_DIR}`. The automated cloud pipeline is currently pulling initial satellite granules.")
else:
    # Build clean dropdown selection
    labels = {}
    for fpath in plot_files:
        fname = os.path.basename(fpath)
        clean_name = fname.replace("dryspell_", "").replace(".png", "").replace("_", " ").replace("to", "–")
        labels[clean_name] = fpath

    options_list = list(labels.keys())

    # ---------------------------------------------------------
    # 2. COMPACT PARAMETER SELECTORS (Side-by-Side)
    # ---------------------------------------------------------
    col_ctrl1, col_ctrl2, col_ctrl3 = st.columns([2, 1, 1])
    
    with col_ctrl1:
        # We use a drop-down selectbox similar to GMet variable selection
        selected_label = st.selectbox(
            "📅 Target Observation Week",
            options=options_list,
            index=len(options_list) - 1
        )
        
    with col_ctrl2:
        st.selectbox(
            "🔧 Precipitation Threshold",
            options=[f"{config['threshold']} mm/day"],
            disabled=True,
            help="Configured in pipeline yaml"
        )
        
    with col_ctrl3:
        st.selectbox(
            "🛰️ Sensor Dataset",
            options=[config["short_name"]],
            disabled=True,
            help="NASA GPM IMERG Early Run V07"
        )

    st.markdown("---")

    # ---------------------------------------------------------
    # 3. SPATIAL MAP CONTAINER
    # ---------------------------------------------------------
    img_path = labels[selected_label]
    
    # Render with a clean, shaded background card
    st.markdown("### 🗺️ Dry Spell Event Distribution")
    with st.container(border=True):
        st.image(img_path, use_container_width=True)

    # ---------------------------------------------------------
    # 4. DATA METADATA TABS (GMet Style Information Panel)
    # ---------------------------------------------------------
    st.markdown("<br>", unsafe_allow_html=True)
    tab_info, tab_sys = st.tabs(["📊 Dataset Metadata", "⚙️ System Infrastructure"])
    
    with tab_info:
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Spatial Resolution", "0.1° (~10 km)")
        col_m2.metric("Observed Region", "West Africa (Sub-Sahelian)")
        col_m3.metric("Calibration Climatology", "NASA Land-Atmospheric Normal")
        
    with tab_sys:
        st.markdown(f"""
        * **Platform Pipeline:** Fully automated GitHub Actions Runner (`ubuntu-latest`)
        * **Processing Libraries:** `xarray`, `dask`, `cartopy`, `earthaccess`
        * **Latest Remote Execution:** Successful auto-commit to `data/plots/`
        * **Active File Name:** `{os.path.basename(img_path)}`
        """)
