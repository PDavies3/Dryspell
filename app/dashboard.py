import os
import yaml
import glob
import streamlit as st

st.set_page_config(
    page_title="Dry Spell Monitor — West Africa",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background: #f5f7f2; }
[data-testid="stHeader"] { background: transparent; }
section.main > div { padding-top: 1rem; padding-bottom: 2rem; }

.hero {
    border-radius: 28px;
    overflow: hidden;
    position: relative;
    height: 170px;
    margin-bottom: 1rem;
}
.hero img {
    width: 100%; height: 100%;
    object-fit: cover; object-position: center 60%;
    display: block;
}
.hero-overlay {
    position: absolute; inset: 0;
    background: rgba(10,30,10,0.52);
    display: flex; flex-direction: column;
    justify-content: flex-end;
    padding: 1.25rem 1.5rem;
}
.hero-top {
    display: flex; align-items: flex-start;
    justify-content: space-between;
}
.hero-title { font-size: 16px; font-weight: 600; color: #fff; line-height: 1.3; }
.hero-sub { font-size: 11px; color: rgba(255,255,255,0.65); margin-top: 3px; }
.hero-pills { display: flex; gap: 6px; flex-shrink: 0; }
.hpill {
    font-size: 10px; padding: 3px 9px; border-radius: 99px;
}
.hpill-live {
    background: rgba(234,243,222,0.25); color: #C0DD97;
    border: 0.5px solid rgba(192,221,151,0.4);
}
.hpill-warn {
    background: rgba(250,238,218,0.2); color: #FAC775;
    border: 0.5px solid rgba(250,199,117,0.4);
}

.met-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0,1fr));
    gap: 8px; margin-bottom: 1.1rem;
}
.met {
    background: #eef2e8; border-radius: 18px;
    padding: 0.8rem 0.9rem;
}
.met-lbl { font-size: 10.5px; color: #5a6b50; margin-bottom: 4px; }
.met-val { font-size: 21px; font-weight: 600; color: #1e3212; line-height: 1; }
.met-unit { font-size: 10px; color: #7a8f6e; margin-top: 3px; }

.notice {
    border-radius: 18px; background: #FAEEDA;
    padding: 0.7rem 1rem; margin-bottom: 1.1rem;
    display: flex; gap: 10px; align-items: flex-start;
}
.notice img {
    width: 40px; height: 40px; border-radius: 12px;
    object-fit: cover; flex-shrink: 0;
}
.notice-body { font-size: 12px; color: #633806; line-height: 1.55; }
.notice-body strong { font-weight: 600; color: #412402; display: block; margin-bottom: 2px; }

.map-section {
    border-radius: 24px; overflow: hidden;
    margin-bottom: 1.1rem; background: #eef2e8;
}
.map-bar {
    display: flex; align-items: center;
    justify-content: space-between;
    padding: 0.75rem 1.1rem;
}
.map-bar-l {
    font-size: 12.5px; font-weight: 500; color: #1e3212;
    display: flex; align-items: center; gap: 6px;
}
.map-img-wrap {
    height: 195px; background: #dde8d0;
    display: flex; align-items: center;
    justify-content: center; position: relative; overflow: hidden;
}
.map-img-wrap img { width: 100%; height: 100%; object-fit: cover; opacity: 0.92; }
.map-placeholder-label {
    position: absolute; font-size: 11.5px;
    color: rgba(255,255,255,0.9);
    background: rgba(30,60,20,0.5);
    padding: 4px 14px; border-radius: 99px;
}
.leg {
    display: flex; align-items: center;
    gap: 10px; padding: 0.65rem 1.1rem; flex-wrap: wrap;
}
.leg-lbl { font-size: 10.5px; color: #5a6b50; }
.leg-items { display: flex; gap: 8px; flex-wrap: wrap; }
.leg-item {
    display: flex; align-items: center;
    gap: 4px; font-size: 10.5px; color: #5a6b50;
}
.dot { width: 8px; height: 8px; border-radius: 50%; }

.two-col {
    display: grid;
    grid-template-columns: repeat(2, minmax(0,1fr));
    gap: 10px; margin-bottom: 1.1rem;
}
.panel { background: #eef2e8; border-radius: 24px; padding: 1rem 1.1rem; }
.panel-head { display: flex; align-items: center; gap: 8px; margin-bottom: 0.85rem; }
.panel-head img { width: 28px; height: 28px; border-radius: 8px; object-fit: cover; }
.panel-head-txt { font-size: 12.5px; font-weight: 500; color: #1e3212; }

.crop-row {
    display: flex; align-items: center; gap: 7px;
    padding: 4.5px 0;
    border-bottom: 0.5px solid rgba(90,107,80,0.18);
}
.crop-row:last-child { border-bottom: none; }
.cname { font-size: 11.5px; color: #5a6b50; width: 62px; flex-shrink: 0; }
.bbar { flex: 1; height: 5px; background: #d8e4cc; border-radius: 99px; overflow: hidden; }
.bfill { height: 5px; border-radius: 99px; }
.rtag { font-size: 10px; padding: 2px 7px; border-radius: 99px; white-space: nowrap; }
.r-hi { background: #FCEBEB; color: #A32D2D; }
.r-md { background: #FAEEDA; color: #854F0B; }
.r-lo { background: #EAF3DE; color: #27500A; }

.adv-item {
    display: flex; gap: 9px; align-items: flex-start;
    padding: 5.5px 0;
    border-bottom: 0.5px solid rgba(90,107,80,0.18);
}
.adv-item:last-child { border-bottom: none; }
.adv-img { width: 34px; height: 34px; border-radius: 10px; object-fit: cover; flex-shrink: 0; }
.adv-txt { font-size: 11.5px; color: #5a6b50; line-height: 1.5; }
.adv-txt strong { font-weight: 500; color: #1e3212; display: block; margin-bottom: 1px; }

.ftr {
    display: flex; align-items: center;
    justify-content: space-between;
    flex-wrap: wrap; gap: 4px; padding: 0 0.2rem;
}
.ftr-l { font-size: 10.5px; color: #7a8f6e; display: flex; align-items: center; gap: 5px; }
.pulse { width: 6px; height: 6px; border-radius: 50%; background: #3B6D11; flex-shrink: 0; display: inline-block; }
.ftr-r { font-size: 10.5px; color: #9aaa8e; }

div[data-testid="stSelectbox"] > div { border-radius: 12px !important; }
</style>
""", unsafe_allow_html=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(BASE_DIR, "config.yaml")
if os.path.exists(config_path):
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
else:
    config = {
        "output_dir": os.path.join(BASE_DIR, "data/plots"),
        "threshold": 1.0,
        "short_name": "IMERG Early V07"
    }

RELATIVE_PLOTS_DIR = os.path.abspath(os.path.join(BASE_DIR, "../data/plots"))
PLOTS_DIR = RELATIVE_PLOTS_DIR if os.path.exists(RELATIVE_PLOTS_DIR) else config["output_dir"]

HERO_IMG = "https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=900&q=80"
NOTICE_IMG = "https://images.unsplash.com/photo-1464226184884-fa280b87c399?w=80&q=70"
SAT_IMG = "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=900&q=75"
MAIZE_IMG = "https://images.unsplash.com/photo-1556075798-4825dfaaf498?w=80&q=70"
FIELD_IMG = "https://images.unsplash.com/photo-1625246333195-78d9c38ad449?w=80&q=70"
IRR_IMG = "https://images.unsplash.com/photo-1586771107445-d3ca888129ff?w=80&q=70"
MULCH_IMG = "https://images.unsplash.com/photo-1416879595882-3373a0480b5b?w=80&q=70"
FCST_IMG = "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=80&q=70"

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="hero">
  <img src="{HERO_IMG}" alt="West African farmland" />
  <div class="hero-overlay">
    <div class="hero-top">
      <div>
        <div class="hero-title">Dry spell monitor — West Africa</div>
        <div class="hero-sub">NASA GPM IMERG Early Run V07 · 0.1° · near real-time</div>
      </div>
      <div class="hero-pills">
        <span class="hpill hpill-live">&#x25CF; Live</span>
        <span class="hpill hpill-warn">Dry season</span>
      </div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Metrics ───────────────────────────────────────────────────────────────────
plot_files = sorted(glob.glob(os.path.join(PLOTS_DIR, "*.png")))
n_files = len(plot_files)
coverage = 64

st.markdown(f"""
<div class="met-grid">
  <div class="met">
    <div class="met-lbl">Dry days</div>
    <div class="met-val">11</div>
    <div class="met-unit">consecutive</div>
  </div>
  <div class="met">
    <div class="met-lbl">Threshold</div>
    <div class="met-val">{config['threshold']}</div>
    <div class="met-unit">mm / day</div>
  </div>
  <div class="met">
    <div class="met-lbl">Coverage</div>
    <div class="met-val">{coverage}%</div>
    <div class="met-unit">of region</div>
  </div>
  <div class="met">
    <div class="met-lbl">Maps loaded</div>
    <div class="met-val" style="font-size:15px;padding-top:4px;">{n_files}</div>
    <div class="met-unit">output files</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Advisory notice ───────────────────────────────────────────────────────────
st.markdown(f"""
<div class="notice">
  <img src="{NOTICE_IMG}" alt="dry farmland" />
  <div class="notice-body">
    <strong>Drought advisory active</strong>
    Prolonged dry spell detected across northern sectors — 8–12 consecutive dry days.
    Supplemental irrigation recommended for maize and sorghum at critical growth stage.
  </div>
</div>
""", unsafe_allow_html=True)

# ── Controls ──────────────────────────────────────────────────────────────────
if plot_files:
    labels = {}
    for fpath in plot_files:
        fname = os.path.basename(fpath)
        clean = fname.replace("dryspell_", "").replace(".png", "").replace("_", " ").replace("to", "–")
        labels[clean] = fpath
    options_list = list(labels.keys())
else:
    labels = {"No outputs found": None}
    options_list = list(labels.keys())

col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    selected_label = st.selectbox("Observation week", options_list, index=len(options_list) - 1)
with col2:
    st.selectbox("Threshold", [f"{config['threshold']} mm/day"], disabled=True)
with col3:
    st.selectbox("Dataset", [config["short_name"]], disabled=True)

# ── Map ───────────────────────────────────────────────────────────────────────
img_path = labels.get(selected_label)

if img_path and os.path.exists(img_path):
    st.markdown(f"""
    <div class="map-section">
      <div class="map-bar">
        <div class="map-bar-l">&#9632; Distribution · {selected_label}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.image(img_path, use_container_width=True)
else:
    st.markdown(f"""
    <div class="map-section">
      <div class="map-bar">
        <div class="map-bar-l">&#9632; Distribution · {selected_label}</div>
      </div>
      <div class="map-img-wrap">
        <img src="{SAT_IMG}" alt="satellite view placeholder" />
        <span class="map-placeholder-label">Satellite map output renders here</span>
      </div>
      <div class="leg">
        <span class="leg-lbl">Dry days:</span>
        <div class="leg-items">
          <div class="leg-item"><div class="dot" style="background:#C0DD97"></div>1–3</div>
          <div class="leg-item"><div class="dot" style="background:#639922"></div>4–6</div>
          <div class="leg-item"><div class="dot" style="background:#3B6D11"></div>7–9</div>
          <div class="leg-item"><div class="dot" style="background:#EF9F27"></div>10–12</div>
          <div class="leg-item"><div class="dot" style="background:#E24B4A"></div>13+</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

# ── Bottom panels ─────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="two-col">
  <div class="panel">
    <div class="panel-head">
      <img src="{MAIZE_IMG}" alt="maize" />
      <span class="panel-head-txt">Crop stress risk</span>
    </div>
    <div class="crop-row">
      <span class="cname">Maize</span>
      <div class="bbar"><div class="bfill" style="width:82%;background:#E24B4A"></div></div>
      <span class="rtag r-hi">High</span>
    </div>
    <div class="crop-row">
      <span class="cname">Sorghum</span>
      <div class="bbar"><div class="bfill" style="width:60%;background:#EF9F27"></div></div>
      <span class="rtag r-md">Moderate</span>
    </div>
    <div class="crop-row">
      <span class="cname">Millet</span>
      <div class="bbar"><div class="bfill" style="width:38%;background:#EF9F27"></div></div>
      <span class="rtag r-md">Moderate</span>
    </div>
    <div class="crop-row">
      <span class="cname">Groundnut</span>
      <div class="bbar"><div class="bfill" style="width:20%;background:#639922"></div></div>
      <span class="rtag r-lo">Low</span>
    </div>
    <div class="crop-row">
      <span class="cname">Cassava</span>
      <div class="bbar"><div class="bfill" style="width:12%;background:#97C459"></div></div>
      <span class="rtag r-lo">Low</span>
    </div>
  </div>

  <div class="panel">
    <div class="panel-head">
      <img src="{FIELD_IMG}" alt="field advisor" />
      <span class="panel-head-txt">Field advisories</span>
    </div>
    <div class="adv-item">
      <img class="adv-img" src="{IRR_IMG}" alt="irrigation" />
      <div class="adv-txt"><strong>Irrigation alert</strong>Begin supplemental irrigation for maize — critical growth stage.</div>
    </div>
    <div class="adv-item">
      <img class="adv-img" src="{MULCH_IMG}" alt="mulching" />
      <div class="adv-txt"><strong>Mulching</strong>Apply organic mulch to retain soil moisture in dry zones.</div>
    </div>
    <div class="adv-item">
      <img class="adv-img" src="{FCST_IMG}" alt="forecast" />
      <div class="adv-txt"><strong>5-day outlook</strong>No rainfall forecast — reassess if spell exceeds 14 days.</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
active_file = os.path.basename(img_path) if img_path else "—"
st.markdown(f"""
<div class="ftr">
  <div class="ftr-l">
    <span class="pulse"></span>
    GitHub Actions pipeline &middot; xarray + cartopy &middot; auto-commit active &middot; {active_file}
  </div>
  <div class="ftr-r">0.1° · Sub-Sahelian West Africa</div>
</div>
""", unsafe_allow_html=True)
