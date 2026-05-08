import os
import yaml
import glob
import streamlit as st

# Set page config
st.set_page_config(page_title="IMERG Dry Spell Dashboard", layout="wide")

# Load Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(BASE_DIR, "config.yaml"), "r") as f:
    config = yaml.safe_load(f)

PLOTS_DIR = config["output_dir"]

st.title("🛰️ IMERG Weekly Dry Spell Analysis")
st.markdown("This dashboard updates automatically as raw data gets fetched and processed in the background.")

# Fetch processed files
plot_files = sorted(glob.glob(os.path.join(PLOTS_DIR, "*.png")))

if not plot_files:
    st.warning(f"No plot outputs found in `{PLOTS_DIR}`. Please run `python processor.py` first.")
else:
    # Build a clean dropdown selection by translating the file names
    labels = {}
    for fpath in plot_files:
        fname = os.path.basename(fpath)
        # Parse: "dryspell_01_Mar_to_07_Mar_2026.png" -> "01 Mar to 07 Mar 2026"
        clean_name = fname.replace("dryspell_", "").replace(".png", "").replace("_", " ").replace("to", "–")
        labels[clean_name] = fpath

    # User Select
    selected_label = st.select_slider(
        "Select Week:",
        options=list(labels.keys()),
        value=list(labels.keys())[-1] # Default to the latest week
    )

    # Render Image
    img_path = labels[selected_label]
    st.image(img_path, use_column_width=True)
    st.caption(f"Showing calculated statistics for: **{selected_label}** |  Plot file: `{os.path.basename(img_path)}`")