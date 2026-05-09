import os
import glob
import yaml
import warnings
import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.ticker as mticker
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
from pathlib import Path

warnings.filterwarnings("ignore")

# Load configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(BASE_DIR, "config.yaml"), "r") as f:
    config = yaml.safe_load(f)

# Helper configurations
WHITE_BROWN = mcolors.LinearSegmentedColormap.from_list(
    "white_brown",
    ["#FFFFFF", "#F5DEB3", "#C68642", "#8B4513", "#3B1A08"],
    N=256
)

PANEL_SPECS = [
    ("3-Day Dry Spell\n(current week)",         3,  3),
    ("7-Day Dry Spell\n(season to date)",        7,  6),
    ("10-Day Dry Spell\n(season to date)",       10, 4),
]

def load_imerg(data_path: str, start_date: str) -> xr.DataArray:
    path = Path(data_path)
    if path.is_dir():
        files = sorted(glob.glob(str(path / "*.nc")) + glob.glob(str(path / "*.nc4")))
        if not files:
            raise FileNotFoundError(f"No .nc/.nc4 files found in {data_path}")
        ds = xr.open_mfdataset(files, combine="by_coords", parallel=False)
    elif path.is_file():
        ds = xr.open_dataset(str(path))
    else:
        raise FileNotFoundError(f"DATA_PATH not found: {data_path}")

    # Auto-detect precipitation variable
    keywords = ["precip", "rain", "precipitation", "cal", "hq", "irmerge"]
    candidates = [v for v in ds.data_vars if any(k in v.lower() for k in keywords)]
    var = candidates[0] if candidates else list(ds.data_vars)[0]
    da = ds[var]

    # Normalize dimensions
    rename_map = {}
    for dim in list(da.dims):
        dl = dim.lower()
        if "time" in dl and dim != "time":
            rename_map[dim] = "time"
        elif dl in ("latitude", "y") and dim != "lat":
            rename_map[dim] = "lat"
        elif dl in ("longitude", "x") and dim != "lon":
            rename_map[dim] = "lon"
    if rename_map:
        da = da.rename(rename_map)

    da = da.sortby("lat").sortby("lon")

    # Resample to daily
    times = pd.DatetimeIndex(da.time.values)
    if len(times) > 1:
        delta = (times[1] - times[0]).total_seconds()
        if delta < 86_400:
            da = da.resample(time="1D").sum(skipna=True)

    da = da.sel(time=slice(start_date, None))
    if da.sizes["time"] == 0:
        raise ValueError(f"No data found on or after {start_date}.")

    if config["bbox"] is not None:
        lon_min, lon_max, lat_min, lat_max = config["bbox"]
        da = da.sel(lon=slice(lon_min, lon_max), lat=slice(lat_min, lat_max))
        if da.sizes["lat"] == 0 or da.sizes["lon"] == 0:
            raise ValueError(f"Spatial clip to BBOX returned an empty array.")

    return da.transpose("time", "lat", "lon")

def count_dry_spells(arr: np.ndarray, min_length: int, threshold: float = 1.0) -> np.ndarray:
    if arr.ndim != 3:
        raise ValueError(f"Expected 3-D (time, lat, lon), got {arr.shape}")
    dry = np.where(np.isfinite(arr), arr < threshold, False)
    T = arr.shape[0]
    current = np.zeros(arr.shape[1:], dtype=np.int16)
    count = np.zeros(arr.shape[1:], dtype=np.int16)

    for t in range(T):
        current = np.where(dry[t], current + 1, 0)
        just_hit = (current == min_length)
        count = np.where(just_hit, count + 1, count)
        current = np.where(just_hit, 0, current)
    return count.astype(float)

def get_arr_slice(da: xr.DataArray, start: pd.Timestamp, end: pd.Timestamp):
    subset = da.sel(time=slice(start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")))
    return subset.values if subset.sizes["time"] > 0 else None

def get_weeks(da: xr.DataArray, week_start: str = "Mon") -> list:
    anchor = "W-SUN" if week_start == "Mon" else "W-SAT"
    times = pd.DatetimeIndex(da.time.values)
    week_ends = pd.date_range(times.min(), times.max() + pd.Timedelta(days=7), freq=anchor)
    weeks = []
    for wend in week_ends:
        wstart = wend - pd.Timedelta(days=6)
        days_in_week = times[(times >= wstart) & (times <= wend)]
        if len(days_in_week) < 3:
            continue
        label = f"{wstart.strftime('%d %b')} – {wend.strftime('%d %b %Y')}"
        weeks.append((label, wend))
    return weeks

def make_cmap_norm(vmax: int):
    vmax = max(vmax, 1)
    levels = np.arange(0, vmax + 2)
    colors = ["#FFFFFF"] + [mcolors.to_hex(WHITE_BROWN(i / vmax)) for i in range(1, len(levels) - 1)]
    cmap = mcolors.ListedColormap(colors)
    norm = mcolors.BoundaryNorm(levels, cmap.N)
    return cmap, norm, levels

def plot_week(week_label: str, arrays: list, lats: np.ndarray, lons: np.ndarray, output_dir: str) -> str:
    proj = ccrs.PlateCarree()
    fig, axes = plt.subplots(1, 3, figsize=(20, 7), subplot_kw={"projection": proj}, constrained_layout=True)
    fig.suptitle(f"IMERG Dry Spell Events  ·  Week: {week_label}", fontsize=14, fontweight="bold")

    lon2d, lat2d = np.meshgrid(lons, lats)
    lon_min, lon_max, lat_min, lat_max = config["bbox"]

    for ax, data, (title, _spell_len, vmax) in zip(axes, arrays, PANEL_SPECS):
        cmap, norm, levels = make_cmap_norm(vmax)
        masked = np.ma.masked_invalid(data)

        mesh = ax.pcolormesh(lon2d, lat2d, masked, cmap=cmap, norm=norm, transform=proj, shading="nearest", zorder=1)
        ax.add_feature(cfeature.OCEAN, facecolor="#d6ecf7", zorder=0)
        ax.add_feature(cfeature.LAND, facecolor="#f5f5f0", zorder=0)
        ax.add_feature(cfeature.COASTLINE, linewidth=0.9, zorder=3)
        ax.add_feature(cfeature.BORDERS, linewidth=0.6, linestyle="--", edgecolor="#444444", zorder=3)
        ax.add_feature(cfeature.LAKES, facecolor="#d6ecf7", linewidth=0.4, zorder=2)
        ax.add_feature(cfeature.RIVERS, edgecolor="#6baed6", linewidth=0.4, zorder=2)

        gl = ax.gridlines(crs=proj, draw_labels=True, linewidth=0.4, color="gray", alpha=0.5, linestyle="--")
        gl.top_labels = gl.right_labels = False
        gl.xformatter, gl.yformatter = LONGITUDE_FORMATTER, LATITUDE_FORMATTER
        gl.xlocator = mticker.FixedLocator(np.arange(-6, 5, 2))
        gl.ylocator = mticker.FixedLocator(np.arange(2, 14, 2))
        gl.xlabel_style = gl.ylabel_style = {"size": 7}

        ax.set_extent([lon_min, lon_max, lat_min, lat_max], crs=proj)
        ax.set_title(title, fontsize=11, fontweight="bold", pad=8)

        cbar = fig.colorbar(mesh, ax=ax, orientation="horizontal", pad=0.04, fraction=0.046, aspect=28, ticks=levels[:-1] + 0.5)
        cbar.ax.set_xticklabels([str(int(v)) for v in levels[:-1]], fontsize=8)
        cbar.set_label("Number of Dry Spell Events", fontsize=9, labelpad=4)
        cbar.outline.set_linewidth(0.5)

    os.makedirs(output_dir, exist_ok=True)
    safe = week_label.replace(" ", "_").replace("–", "to").replace("/", "-")
    fpath = os.path.join(output_dir, f"dryspell_{safe}.png")
    fig.savefig(fpath, dpi=config["dpi"], bbox_inches="tight")
    plt.close(fig)
    return fpath

def run_processor():
    """Main execution block triggered by scheduler or manual CLI run"""
    # Load central configuration
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(BASE_DIR, "config.yaml"), "r") as f:
        config = yaml.safe_load(f)

    # DYNAMIC PATH OVERRIDE: Check if running on GitHub Actions
    if os.environ.get("GITHUB_ACTIONS") == "true":
        data_path = os.path.abspath(os.path.join(BASE_DIR, "../data/raw"))
        output_dir = os.path.abspath(os.path.join(BASE_DIR, "../data/plots"))
    else:
        data_path = config["data_path"]
        output_dir = config["output_dir"]

    print("\n[1/3] Loading climate dataset...")
    da = load_imerg(data_path, config["start_date"])
    lats, lons = da.lat.values, da.lon.values
    season_t0 = pd.Timestamp(str(da.time.values[0])[:10])

    print("\n[2/3] Identifying weekly periods...")
    weeks = get_weeks(da, config["week_start"])
    print(f"Found {len(weeks)} complete week(s) to process.")

    print("\n[3/3] Commencing dry spell counts & exporting plots...")
    saved_plots = []
    for i, (label, wend) in enumerate(weeks, 1):
        wstart = wend - pd.Timedelta(days=6)
        
        arr_week = get_arr_slice(da, wstart, wend)
        if arr_week is None:
            continue
            
        map_3day = count_dry_spells(arr_week, min_length=3, threshold=config["threshold"])
        arr_season = get_arr_slice(da, season_t0, wend)
        map_7day = count_dry_spells(arr_season, min_length=7, threshold=config["threshold"]) if arr_season is not None else np.zeros_like(map_3day)
        map_10day = count_dry_spells(arr_season, min_length=10, threshold=config["threshold"]) if arr_season is not None else np.zeros_like(map_3day)

        # Uses the dynamically defined output_dir
        fpath = plot_week(label, [map_3day, map_7day, map_10day], lats, lons, output_dir)
        saved_plots.append(fpath)
        print(f"  [{i}/{len(weeks)}] Saved: {os.path.basename(fpath)}")
    
    print("\nProcessing Cycle Completed Successfully!")
    return saved_plots

if __name__ == "__main__":
    run_processor()
