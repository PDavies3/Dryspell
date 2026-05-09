import os
import yaml
import glob
import streamlit as st

# Set page config for a professional wide layout with a custom page icon
st.set_page_config(
    page_title="IMERG Dry Spell Monitor",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
# SIDEBAR DESIGN
# ---------------------------------------------------------
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/satellite.png", width=80)
    st.title("IMERG Monitor")
    st.markdown("---")
    
    st.subheader("⚙️ Pipeline Configuration")
    st.markdown(f"**Threshold:** `{config['threshold']} mm/day`")
    st.markdown(f"**Week Start:** `{config['week_start']}`")
    st.markdown(f"**Season Start:** `{config['start_date']}`")
    
    st.markdown("---")
    st.markdown(
        "💡 *This system monitors dry spell patterns across West Africa. "
        "Data is updated automatically every day at 03:00 UTC via NASA GPM IMERG.*"
    )

# ---------------------------------------------------------
# MAIN DASHBOARD DESIGN
# ---------------------------------------------------------
st.title("🛰️ IMERG Weekly Dry Spell Analysis")
st.caption("Automated High-Resolution Satellite Precipitation Monitoring")
st.markdown("---")

# Fetch processed files
plot_files = sorted(glob.glob(os.path.join(PLOTS_DIR, "*.png")))

if not plot_files:
    st.warning(f"⚠️ No plot outputs found in `{PLOTS_DIR}`. The automated pipeline is setting up your first run.")
else:
    # Build clean dropdown selection
    labels = {}
    for fpath in plot_files:
        fname = os.path.basename(fpath)
        clean_name = fname.replace("dryspell_", "").replace(".png", "").replace("_", " ").replace("to", "–")
        labels[clean_name] = fpath

    options_list = list(labels.keys())

    # Row 1: Key Performance Indicators / Metadata Cards
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Total Analyzed Weeks", value=len(options_list))
    with col2:
        st.metric(label="Active Dataset", value=config["short_name"])
    with col3:
        # Show the most recently processed week name
        st.metric(label="Latest Update", value=options_list[-1].split("–")[-1].strip())

    st.markdown("### 🗺️ Dry Spell Spatial Maps")

    # Row 2: Select Week Control (Conditional rendering)
    if len(options_list) == 1:
        selected_label = options_list[0]
        st.info(f"📅 **Showing data for:** {selected_label} *(The slider will automatically appear once the next week of data is compiled)*")
    else:
        selected_label = st.select_slider(
            "Slide to change weekly viewing period:",
            options=options_list,
            value=options_list[-1]
        )

    # Row 3: Render Image inside a clean, modern container
    img_path = labels[selected_label]
    
    # Render with a beautiful card-like aesthetic
    with st.container(border=True):
        st.image(img_path, use_container_width=True)
        
    # Styled caption box
    st.info(
        f"📋 **Active Plot:** `dryspell_{selected_label.replace(' ', '_').replace('–', 'to')}.png` | "
        f"**Calculated Period:** {selected_label}"
    )
