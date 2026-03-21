"""
Interactive flood-risk map with collapsible per-region layer groups.
- Regions expanded by default; click name to collapse/expand.
- Flood Depth and Risk layers togglable.
"""

__author__ = "Mukharbek Organokov"
__version__ = "2.4.0"

import os
import re
import csv
import json
import math
import glob
import base64
import requests as _requests
from io import BytesIO
import numpy as np
import folium
import rasterio
from rasterio.transform import rowcol
from pyproj import Transformer
from folium.plugins import GroupedLayerControl
import matplotlib.pyplot as plt
from matplotlib import cm, colors
from matplotlib.colors import LogNorm

# === CONFIG ===
INPUT_DIR = "data"
OUTPUT_BASE = "data/output"
os.makedirs(OUTPUT_BASE, exist_ok=True)

OUTPUT_HTML = "public/combined_flood_risk_map.html"

RETURN_PERIODS = [10, 20, 50, 100, 200, 500]
RISK_BAND = 8
HOVER_DOWNSAMPLE = 6  # Downsample raster by this factor for hover data grids

# Asset locations (lat, lon, label, address)
ASSETS = [
    (52.2979, -2.0745, "Asset A", "4 Woden Court, Saxon Business Park, Hanbury Road, Bromsgrove, B60 4AD"),
    (53.2621, -1.3464, "Asset B", "Prospect House, Colliery Close, Chesterfield, S43 3QE"),
    (54.2339, -2.7179, "Asset C", "Units 5-7, Moss End Business Village, Crooklands, Milnthorpe, LA7 7NU"),
    (53.4314, -2.3190, "Asset D", "183 Cross Street, Sale, M33 7JG"),
    (52.3792,  0.7358, "Asset E", "Station Road, Barnham, Thetford, IP24 2PD"),
]
BUILDING_VALUE = 1_000_000  # £ commercial building replacement cost
DAMAGE_CSV = "public/data/flood_damage_csv.txt"
EXTRAPOLATED_RPS = [1, 2, 5]  # short return periods estimated via log-linear fit
MAPBOX_TOKEN = os.environ.get("MAPBOX_TOKEN", "")
OS_API_KEY = os.environ.get("OS_API_KEY", "")

# EA LIDAR DTM 1m elevation data (EPSG:27700 British National Grid)
LIDAR_DIR = os.path.join(INPUT_DIR, "lidar")

# RdYlGn (Reversed) - Most Intuitive
RISK_COLORS = {
    1:  "#1a9850",  # dark green
    2:  "#66bd63",  # green
    3:  "#a6d96a",  # light green
    4:  "#d9ef8b",  # yellow-green
    5:  "#fee08b",  # yellow
    6:  "#fdae61",  # light orange
    7:  "#f46d43",  # orange
    8:  "#d73027",  # red-orange
    9:  "#a50026",  # dark red
    10: "#67001f",  # very dark red
}

# Viridis - Colorblind Friendly
# RISK_COLORS = {
# #    1:  "#440154",  # purple
#     2:  "#482878",  # dark blue-purple
#     3:  "#3e4989",  # blue
#     4:  "#31688e",  # teal-blue
#     5:  "#26828e",  # teal
#     6:  "#1f9e89",  # green-teal
#     7:  "#35b779",  # green
#     8:  "#6ece58",  # yellow-green
#     9:  "#b5de2b",  # yellow
#     10: "#fde725",  # bright yellow
# }

# RISK_COLORS = {
# #    1:  "#0d0887",  # dark blue
#     2:  "#41049d",  # purple
#     3:  "#6a00a8",  # violet
#     4:  "#8f0da4",  # magenta
#     5:  "#b12a90",  # pink-magenta
#     6:  "#cc4778",  # pink
#     7:  "#e16462",  # coral
#     8:  "#f2844b",  # orange
#     9:  "#fca636",  # yellow-orange
#     10: "#fcce25",  # yellow
# }

# Spectral (Reversed) - High Contrast
# RISK_COLORS = {
# #    1:  "#2b83ba",  # blue
#     2:  "#5aae61",  # green
#     3:  "#9dd84a",  # light green
#     4:  "#d7ee8e",  # pale yellow
#     5:  "#ffffbf",  # cream
#     6:  "#fee090",  # pale orange
#     7:  "#fdae61",  # orange
#     8:  "#f46d43",  # red-orange
#     9:  "#d73027",  # red
#     10: "#a50026",  # dark red
# }

# Turbo - Maximum Contrast
# RISK_COLORS = {
#     2:  "#30123b",  # dark blue
#     3:  "#4662d7",  # blue
#     4:  "#36a1f9",  # cyan
#     5:  "#13c8fe",  # light cyan
#     6:  "#1ae4b6",  # turquoise
#     7:  "#72f566",  # green
#     8:  "#c7ef34",  # yellow-green
#     9:  "#f1ca3a",  # yellow
#     10: "#fe9b2d",  # orange
# }

# Inferno - Dramatic & Professional
# RISK_COLORS = {
#     2:  "#08051d",  # nearly black
#     3:  "#280b53",  # dark purple
#     4:  "#4f0d4a",  # purple
#     5:  "#7b1a3f",  # magenta
#     6:  "#a92e2e",  # dark red
#     7:  "#d24742",  # red
#     8:  "#ed6925",  # orange
#     9:  "#fb9b06",  # yellow-orange
#     10: "#f5d746",  # yellow
# }

# # Earth Tones - Natural & Calm
# RISK_COLORS = {
#     2:  "#543005",  # dark brown
#     3:  "#8c510a",  # brown
#     4:  "#bf812d",  # tan-brown
#     5:  "#dfc27d",  # tan
#     6:  "#f6e8c3",  # cream
#     7:  "#f5c5ab",  # peach
#     8:  "#e88471",  # coral
#     9:  "#c7522a",  # red-orange
#     10: "#8c2d04",  # dark red-brown
# }

# === HELPERS ===
def clean_region_name(filename: str) -> str:
    base = os.path.basename(filename)
    m = re.search(r"xll\.(-?\d+)\.yll\.(-?\d+)", base)
    if m:
        x, y = m.groups()
        return f"x{x}y{y}"
    return os.path.splitext(base)[0]

def load_damage_curve(csv_path):
    """Load the depth-to-damage-% curve from CSV.
    Returns sorted list of (depth_m, commercial_pct) tuples."""
    curve = []
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            depth = float(row["depth_m"])
            pct = float(row["mcm_commercial_pct"])  # MCM commercial model
            curve.append((depth, pct))
    curve.sort(key=lambda x: x[0])
    return curve


def depth_to_damage_pct(depth_m, curve):
    """Linearly interpolate damage % for a given depth using the damage curve."""
    if depth_m <= 0 or np.isnan(depth_m):
        return 0.0
    if depth_m <= curve[0][0]:
        return curve[0][1]
    if depth_m >= curve[-1][0]:
        return curve[-1][1]
    for i in range(len(curve) - 1):
        d0, p0 = curve[i]
        d1, p1 = curve[i + 1]
        if d0 <= depth_m <= d1:
            t = (depth_m - d0) / (d1 - d0) if d1 != d0 else 0
            return p0 + t * (p1 - p0)
    return curve[-1][1]


def sample_asset_depths(tiffs, assets, return_periods):
    """For each asset, sample a ~50 m radius grid of raster pixels to compute:
      - mean flood depth (of flooded pixels only)
      - flood coverage % (fraction of footprint pixels that are wet)
    Returns dict: {label: {rp: (mean_depth_m, coverage_pct), ...}, ...}
    """
    RADIUS_M = 50  # approximate building footprint radius
    result = {a[2]: {} for a in assets}
    for path in tiffs:
        with rasterio.open(path) as src:
            max_bands = min(src.count, 6)
            res_x, res_y = src.res  # degrees per pixel
            for lat, lon, label, _addr in assets:
                if not (src.bounds.left <= lon <= src.bounds.right and
                        src.bounds.bottom <= lat <= src.bounds.top):
                    continue
                # Convert radius to pixel offsets
                m_per_deg_lon = 111320 * math.cos(math.radians(lat))
                m_per_deg_lat = 111320
                r_cols = max(1, int(round(RADIUS_M / (res_x * m_per_deg_lon))))
                r_rows = max(1, int(round(RADIUS_M / (abs(res_y) * m_per_deg_lat))))

                c_row, c_col = src.index(lon, lat)
                c_row = max(0, min(c_row, src.height - 1))
                c_col = max(0, min(c_col, src.width - 1))

                row_lo = max(0, c_row - r_rows)
                row_hi = min(src.height, c_row + r_rows + 1)
                col_lo = max(0, c_col - r_cols)
                col_hi = min(src.width, c_col + r_cols + 1)

                for i, rp in enumerate(return_periods[:max_bands], start=1):
                    patch = src.read(i, window=rasterio.windows.Window.from_slices(
                        (row_lo, row_hi), (col_lo, col_hi)
                    )).astype(float) / 100.0  # cm → m
                    total_px = patch.size
                    wet_px = int(np.count_nonzero(patch > 0))
                    if wet_px > 0:
                        mean_depth = float(patch[patch > 0].mean())
                        coverage = wet_px / total_px * 100.0
                        # Keep the higher coverage if asset spans multiple tiffs
                        prev = result[label].get(rp)
                        if prev is None or coverage > prev[1]:
                            result[label][rp] = (mean_depth, coverage)
    return result


def extrapolate_short_rps(asset_depths, known_rps, extrap_rps):
    """Fit depth = a + b*ln(RP) and coverage = a + b*ln(RP) on the known
    return-period data and extrapolate to shorter return periods.

    Returns dict: {label: {rp: (est_depth_m, est_coverage_pct), ...}, ...}
    Only populates entries where >= 2 known data points exist.
    Negative extrapolations are clamped to 0.
    """
    result = {}
    for label, depths in asset_depths.items():
        result[label] = {}
        rps, ds, covs = [], [], []
        for rp in known_rps:
            entry = depths.get(rp)
            if entry and entry[0] > 0:
                rps.append(rp)
                ds.append(entry[0])
                covs.append(entry[1])
        if len(rps) < 2:
            continue
        log_rps = np.log(rps)
        # Fit depth
        b_d, a_d = np.polyfit(log_rps, ds, 1)
        # Fit coverage
        b_c, a_c = np.polyfit(log_rps, covs, 1)
        for rp in extrap_rps:
            est_d = max(0.0, a_d + b_d * np.log(rp))
            est_c = max(0.0, min(100.0, a_c + b_c * np.log(rp)))
            if est_d > 0:
                result[label][rp] = (est_d, est_c)
    return result


def add_legend(map_obj, title, cmap_name=None, vmin=0, vmax=1):
    cmap = plt.get_cmap(cmap_name, 256)
    gradient_img = (cmap(np.linspace(0, 1, 256))[:, :3] * 255).astype(np.uint8)
    with BytesIO() as buffer:
        plt.imsave(buffer, gradient_img[np.newaxis, :, :], format="png")
        buffer.seek(0)
        b64 = base64.b64encode(buffer.read()).decode("utf-8")
    html = f"""
    <div style="position: fixed; bottom: 50px; left: 50px; width: 220px;
                z-index:9999; background:white; padding:10px; border-radius:12px;
                box-shadow:0 1px 4px rgba(0,0,0,.3)">
      <b>{title}</b><br>
      <img src="data:image/png;base64,{b64}" style="width:190px;height:20px;"><br>
      <small>{vmin:.2f} – {vmax:.2f}</small>
    </div>
    """
    map_obj.get_root().html.add_child(folium.Element(html))


def add_discrete_legend(map_obj, title, colors_dict, valid_values=None, top=10, left=10):
    keys = sorted(valid_values) if valid_values is not None else sorted(colors_dict.keys())
    items = "".join(
        f'<div style="display:flex;align-items:center;margin:2px 0;">'
        f'<span style="display:inline-block;width:14px;height:14px;background:{colors_dict[k]};'
        f'border:1px solid #555;margin-right:8px;"></span>{k}</div>'
        for k in keys
    )
    html = f"""
    <div style="position: fixed; top: {top}px; left: {left}px;
                z-index:9999; background:white; padding:10px 12px; border-radius:12px;
                box-shadow:0 1px 4px rgba(0,0,0,.3); font-size:12px;">
      <div style="font-weight:700; margin-bottom:6px;">{title}</div>
      {items}
    </div>
    """
    map_obj.get_root().html.add_child(folium.Element(html))


def downsample_band_mean(band, factor):
    """Downsample a 2D array by computing the mean of valid (finite & >0)
    pixels within each block.  Best for continuous data like flood depth.
    Returns a 2D list of rounded floats (None for empty blocks)."""
    rows, cols = band.shape
    out_rows = rows // factor
    out_cols = cols // factor
    result = []
    for r in range(out_rows):
        row_out = []
        for c in range(out_cols):
            block = band[r*factor:(r+1)*factor, c*factor:(c+1)*factor]
            valid = block[np.isfinite(block) & (block > 0)]
            if valid.size == 0:
                row_out.append(None)
            else:
                row_out.append(round(float(np.mean(valid)), 3))
        result.append(row_out)
    return result


def downsample_band_mode(band, factor):
    """Downsample a 2D array by computing the mode (most frequent value)
    within each block. Best for categorical / discrete data like risk scores.
    Returns a 2D list of int values (None for NaN-only blocks)."""
    rows, cols = band.shape
    out_rows = rows // factor
    out_cols = cols // factor
    result = []
    for r in range(out_rows):
        row_out = []
        for c in range(out_cols):
            block = band[r*factor:(r+1)*factor, c*factor:(c+1)*factor]
            valid = block[np.isfinite(block) & (block > 0)]
            if valid.size == 0:
                row_out.append(None)
            else:
                # Find mode: most frequent integer value
                rounded = np.round(valid).astype(int)
                vals, counts = np.unique(rounded, return_counts=True)
                row_out.append(int(vals[np.argmax(counts)]))
        result.append(row_out)
    return result


# === LIDAR ELEVATION ===
class LidarElevation:
    """Load EA LIDAR DTM 1m tiles and provide fast elevation lookup at WGS84 coords."""

    def __init__(self, lidar_dir):
        self.tiles = []  # list of (bounds_bng, rasterio DatasetReader)
        self.to_bng = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)
        tif_paths = sorted(glob.glob(os.path.join(lidar_dir, "*_DTM_1m.tif")))
        for p in tif_paths:
            ds = rasterio.open(p)
            self.tiles.append((ds.bounds, ds))
        print(f"  📐 Loaded {len(self.tiles)} LIDAR DTM tiles from {lidar_dir}")

    def close(self):
        for _, ds in self.tiles:
            ds.close()

    def get_elevation(self, lat, lon):
        """Return ground elevation (m AOD) at WGS84 lat/lon, or None if outside coverage."""
        x, y = self.to_bng.transform(lon, lat)  # always_xy: (lon,lat) → (easting,northing)
        for bounds, ds in self.tiles:
            if bounds.left <= x <= bounds.right and bounds.bottom <= y <= bounds.top:
                r, c = rowcol(ds.transform, x, y)
                r = max(0, min(r, ds.height - 1))
                c = max(0, min(c, ds.width - 1))
                val = float(ds.read(1, window=rasterio.windows.Window(c, r, 1, 1))[0, 0])
                if val > -1e30:  # not nodata
                    return round(val, 2)
        return None

    def build_elevation_grid(self, south, west, north, east, rows, cols):
        """Build a 2D elevation grid (list of lists) matching hover grid dimensions.
        Uses vectorised sampling for speed."""
        lats = np.linspace(north, south, rows)   # top→bottom
        lons = np.linspace(west, east, cols)      # left→right
        lon_grid, lat_grid = np.meshgrid(lons, lats)
        xs, ys = self.to_bng.transform(lon_grid.ravel(), lat_grid.ravel())
        xs = np.array(xs)
        ys = np.array(ys)
        elev = np.full(rows * cols, np.nan)

        for bounds, ds in self.tiles:
            mask = (xs >= bounds.left) & (xs <= bounds.right) & \
                   (ys >= bounds.bottom) & (ys <= bounds.top)
            if not mask.any():
                continue
            rs, cs = rowcol(ds.transform, xs[mask], ys[mask])
            rs = np.clip(np.array(rs), 0, ds.height - 1)
            cs = np.clip(np.array(cs), 0, ds.width - 1)
            # Read a window covering all needed pixels in this tile
            r_min, r_max = int(rs.min()), int(rs.max())
            c_min, c_max = int(cs.min()), int(cs.max())
            window = rasterio.windows.Window(c_min, r_min, c_max - c_min + 1, r_max - r_min + 1)
            data = ds.read(1, window=window)
            local_r = rs - r_min
            local_c = cs - c_min
            vals = data[local_r.astype(int), local_c.astype(int)]
            valid = vals > -1e30
            idx = np.where(mask)[0]
            elev[idx[valid]] = vals[valid]

        # Convert to 2D list, rounding to 1 decimal
        elev_2d = elev.reshape(rows, cols)
        result = []
        for r in range(rows):
            row_out = []
            for c in range(cols):
                v = elev_2d[r, c]
                if np.isfinite(v):
                    row_out.append(round(float(v), 1))
                else:
                    row_out.append(None)
            result.append(row_out)
        return result


# === CORE ===
def build_layers_for_region(fmap, tiff_path):
    region_id = clean_region_name(tiff_path)
    overlays = []
    hover_data = {}  # {layer_name: {bounds, rows, cols, grid}}

    with rasterio.open(tiff_path) as src:
        flood_min, flood_max = np.inf, 0.0
        max_bands = min(src.count, 6)
        for i in range(1, max_bands + 1):
            b = src.read(i).astype(float) / 100.0
            v = b[b > 0]
            if v.size:
                flood_min = min(flood_min, float(np.nanmin(v)))
                flood_max = max(flood_max, float(np.nanmax(v)))
        if not np.isfinite(flood_min):
            flood_min, flood_max = 0.01, 0.02

        bbox = [[src.bounds.bottom, src.bounds.left], [src.bounds.top, src.bounds.right]]

        for i, rp in enumerate(RETURN_PERIODS[:max_bands], start=1):
            band = src.read(i).astype(float)
            band[band == 0] = np.nan
            band = band / 100.0
            mask = (band > 0) & ~np.isnan(band)
            norm = LogNorm(vmin=max(flood_min, 0.01), vmax=flood_max)
            rgba = np.zeros((*band.shape, 4), dtype=np.uint8)
            rgba[mask] = (cm.Blues(norm(band[mask])) * 255).astype(np.uint8)
            layer_name = f"Flood Depths \u2192 RP {rp} yr"
            layer = folium.raster_layers.ImageOverlay(
                image=rgba,
                bounds=bbox,
                opacity=0.7,
                name=layer_name,
                show=False,
            )
            layer.add_to(fmap)
            overlays.append(layer)

            # Build hover grid for this band (block-mean for accuracy)
            small = downsample_band_mean(band, HOVER_DOWNSAMPLE)
            hover_data[layer_name] = {
                "bounds": bbox,
                "rows": len(small),
                "cols": len(small[0]) if small else 0,
                "grid": small,
                "unit": "m",
                "label": f"Flood Depth (RP {rp} yr)",
            }

        if src.count >= RISK_BAND:
            risk = src.read(RISK_BAND).astype(float)
            risk[risk == 0] = np.nan

            # Use discrete RISK_COLORS for each integer score 2-10
            # Round to nearest int so float raster values (e.g. 2.0, 3.0) match dict keys
            risk_rounded = np.round(risk)
            rgba_risk = np.zeros((*risk.shape, 4), dtype=np.uint8)
            for score, hex_color in RISK_COLORS.items():
                r_c = int(hex_color[1:3], 16)
                g_c = int(hex_color[3:5], 16)
                b_c = int(hex_color[5:7], 16)
                mask_score = (risk_rounded == score) & ~np.isnan(risk)
                rgba_risk[mask_score] = [r_c, g_c, b_c, 255]
            risk_layer_name = "Flood Risk \u2192 Score (1\u201310)"
            layer = folium.raster_layers.ImageOverlay(
                image=rgba_risk,
                bounds=[[src.bounds.bottom, src.bounds.left], [src.bounds.top, src.bounds.right]],
                opacity=0.7,
                name=risk_layer_name,
                show=False,
            )
            layer.add_to(fmap)
            overlays.append(layer)

            # Build hover grid for risk (integer values, block-mode for accuracy)
            risk_for_hover = src.read(RISK_BAND).astype(float)
            risk_for_hover[risk_for_hover == 0] = np.nan
            small_risk = downsample_band_mode(risk_for_hover, HOVER_DOWNSAMPLE)
            hover_data[risk_layer_name] = {
                "bounds": bbox,
                "rows": len(small_risk),
                "cols": len(small_risk[0]) if small_risk else 0,
                "grid": small_risk,
                "unit": "",
                "label": "Flood Risk Score",
            }

    return region_id, overlays, hover_data


# === MAIN ===
def main():
    print("🚀 Starting main() ...")
    tiffs = [os.path.join(INPUT_DIR, f) for f in os.listdir(INPUT_DIR) if f.endswith(".tif")]
    if not tiffs:
        print("❌ No TIFFs found.")
        return

    with rasterio.open(tiffs[0]) as src:
        center_lat = (src.bounds.top + src.bounds.bottom) / 2
        center_lon = (src.bounds.left + src.bounds.right) / 2

    fmap = folium.Map(location=[center_lat, center_lon], zoom_start=7, tiles=None)

    # --- Basemap tile layers ---
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png",
        attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
        name="_basemap_street",
        max_zoom=20,
        subdomains="abcd",
    ).add_to(fmap)

    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}",
        attr='&copy; Esri, HERE, Garmin, OpenStreetMap contributors',
        name="_basemap_topo",
        max_zoom=19,
    ).add_to(fmap)

    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr='&copy; Esri, Maxar, Earthstar Geographics',
        name="_basemap_satellite",
        max_zoom=21,
        max_native_zoom=18,
    ).add_to(fmap)

    folium.TileLayer(
        tiles="https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png",
        attr='&copy; <a href="https://opentopomap.org">OpenTopoMap</a> (<a href="https://creativecommons.org/licenses/by-sa/3.0/">CC-BY-SA</a>)',
        name="_basemap_terrain",
        max_zoom=20,
        max_native_zoom=17,
    ).add_to(fmap)

    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/Elevation/World_Hillshade/MapServer/tile/{z}/{y}/{x}",
        attr='&copy; Esri, USGS',
        name="_basemap_hillshade",
        max_zoom=23,
        max_native_zoom=16,
    ).add_to(fmap)

    folium.TileLayer(
        tiles="https://api.mapbox.com/styles/v1/mapbox/outdoors-v12/tiles/{z}/{x}/{y}?access_token=__MAPBOX_TOKEN__",
        attr='&copy; <a href="https://www.mapbox.com/">Mapbox</a> &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
        name="_basemap_mapbox",
        max_zoom=22,
        tile_size=512,
        zoom_offset=-1,
    ).add_to(fmap)

    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
        name="_basemap_dark",
        max_zoom=20,
        subdomains="abcd",
    ).add_to(fmap)

    # Ordnance Survey Outdoor — detailed UK topographic map (free tier: zoom ≤16)
    folium.TileLayer(
        tiles="https://api.os.uk/maps/raster/v1/zxy/Outdoor_3857/{z}/{x}/{y}.png?key=__OS_API_KEY__",
        attr='&copy; <a href="https://www.ordnancesurvey.co.uk/">Ordnance Survey</a> Crown copyright',
        name="_basemap_os_outdoor",
        max_zoom=16,
    ).add_to(fmap)

    # Google Maps Road
    folium.TileLayer(
        tiles="https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
        attr='&copy; <a href="https://www.google.com/maps">Google</a>',
        name="_basemap_google",
        max_zoom=22,
    ).add_to(fmap)

    # Google Satellite
    folium.TileLayer(
        tiles="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
        attr='&copy; <a href="https://www.google.com/maps">Google</a>',
        name="_basemap_google_sat",
        max_zoom=22,
    ).add_to(fmap)

    # Hybrid labels overlay (paired with satellite imagery layer for hybrid mode)
    # CartoDB Voyager Only Labels — roads, places, water, POIs
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/rastertiles/voyager_only_labels/{z}/{x}/{y}{r}.png",
        attr='&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> &copy; <a href="https://carto.com/">CARTO</a>',
        name="_basemap_hybrid_labels",
        max_zoom=21,
        subdomains="abcd",
    ).add_to(fmap)

    folium.TileLayer(
        tiles="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        name="_basemap_osm",
        max_zoom=19,
    ).add_to(fmap)

    groups = {}
    all_hover_data = {}  # region -> layer_name -> grid data
    for path in tiffs:
        region_id, layers, hover_data = build_layers_for_region(fmap, path)
        groups[f"Region {region_id}"] = layers
        all_hover_data[f"Region {region_id}"] = hover_data

    control = GroupedLayerControl(groups=groups, collapsed=False, exclusive_groups=False)
    control.add_to(fmap)

    # --- Load LIDAR DTM for 1m elevation data ---
    lidar = None
    if os.path.isdir(LIDAR_DIR):
        lidar = LidarElevation(LIDAR_DIR)

    # --- Build elevation hover grids from LIDAR (independent 20 m resolution) ---
    ELEV_CELL_M = 20  # elevation hover grid cell size in metres
    elev_hover_grids = []
    if lidar and lidar.tiles:
        for region_name, layers_dict in all_hover_data.items():
            ref = next(iter(layers_dict.values()))
            south, west = ref["bounds"][0]
            north, east = ref["bounds"][1]
            # Compute rows/cols from geographic extent at 20 m spacing
            lat_m = (north - south) * 111320
            lon_m = (east - west) * 111320 * math.cos(math.radians((north + south) / 2))
            elev_rows = max(1, int(lat_m / ELEV_CELL_M))
            elev_cols = max(1, int(lon_m / ELEV_CELL_M))
            print(f"  🏔️  Building elevation grid for {region_name} ({elev_rows}x{elev_cols} @ {ELEV_CELL_M}m)...")
            elev_grid = lidar.build_elevation_grid(south, west, north, east, elev_rows, elev_cols)
            elev_hover_grids.append({
                "bounds": ref["bounds"],
                "rows": elev_rows,
                "cols": elev_cols,
                "grid": elev_grid,
            })

    # --- Add asset markers with financial damage info ---
    damage_curve = load_damage_curve(DAMAGE_CSV)
    asset_depths = sample_asset_depths(tiffs, ASSETS, RETURN_PERIODS)
    extrap_depths = extrapolate_short_rps(asset_depths, RETURN_PERIODS, EXTRAPOLATED_RPS)

    for lat, lon, label, address in ASSETS:
        depths = asset_depths.get(label, {})
        extrap = extrap_depths.get(label, {})
        # Lookup LIDAR elevation for this asset, fallback to Open-Meteo API
        asset_elev = lidar.get_elevation(lat, lon) if lidar else None
        if asset_elev is None:
            try:
                url = f"https://api.open-meteo.com/v1/elevation?latitude={lat}&longitude={lon}"
                data = _requests.get(url, timeout=5).json()
                asset_elev = data["elevation"][0]
                print(f"    ↳ {label}: Open-Meteo elevation = {asset_elev:.1f} m")
            except Exception as exc:
                print(f"    ↳ {label}: Open-Meteo elevation failed: {exc}")
        asset_elev_str = f"{asset_elev:.1f} m AOD" if asset_elev is not None else "N/A"
        # Build damage table rows — extrapolated short RPs first, then measured
        rows_html = ""
        # Style constants
        EST = 'font-style:italic;color:#7b7b7b;'  # extrapolated rows
        EST_D = 'font-style:italic;color:#5a9bd5;'  # extrapolated depth
        EST_DMG = 'font-style:italic;color:#d4796b;'  # extrapolated £

        # --- Extrapolated rows (RP 1, 2, 5) — only include rows with data ---
        extrap_rows = ""
        for rp in EXTRAPOLATED_RPS:
            entry = extrap.get(rp)
            if entry and entry[0] > 0:
                d, cov = entry
                pct = depth_to_damage_pct(d, damage_curve)
                adj_pct = pct * cov / 100.0
                dmg = BUILDING_VALUE * adj_pct / 100.0
                extrap_rows += (
                    f'<tr style="{EST}">'
                    f'<td style="padding:2px 6px;">{rp} yr *</td>'
                    f'<td style="padding:2px 6px;text-align:right;{EST_D}">{d:.3f} m</td>'
                    f'<td style="padding:2px 6px;text-align:right;">{pct:.1f}%</td>'
                    f'<td style="padding:2px 6px;text-align:right;">{cov:.0f}%</td>'
                    f'<td style="padding:2px 6px;text-align:right;{EST_DMG}">£{dmg:,.0f}</td>'
                    f'</tr>'
                )

        # Add extrapolated rows + separator only if there are any
        if extrap_rows:
            rows_html += extrap_rows
            rows_html += (
                '<tr><td colspan="5" style="padding:0;">'
                '<hr style="border:none;border-top:1px dashed #ccc;margin:2px 0;">'
                '</td></tr>'
            )

        # --- Measured rows (RP 10–500) ---
        for rp in RETURN_PERIODS:
            entry = depths.get(rp)  # (mean_depth_m, coverage_pct) or None
            if entry and entry[0] > 0:
                d, cov = entry
                pct = depth_to_damage_pct(d, damage_curve)
                # Adjust damage by flood coverage fraction
                adj_pct = pct * cov / 100.0
                dmg = BUILDING_VALUE * adj_pct / 100.0
                rows_html += (
                    f'<tr>'
                    f'<td style="padding:2px 6px;">{rp} yr</td>'
                    f'<td style="padding:2px 6px;text-align:right;color:#2166ac;font-weight:600;">{d:.2f} m</td>'
                    f'<td style="padding:2px 6px;text-align:right;">{pct:.1f}%</td>'
                    f'<td style="padding:2px 6px;text-align:right;">{cov:.0f}%</td>'
                    f'<td style="padding:2px 6px;text-align:right;color:#c0392b;font-weight:700;">£{dmg:,.0f}</td>'
                    f'</tr>'
                )
            else:
                rows_html += (
                    f'<tr>'
                    f'<td style="padding:2px 6px;">{rp} yr</td>'
                    f'<td style="padding:2px 6px;text-align:right;color:#999;">—</td>'
                    f'<td style="padding:2px 6px;text-align:right;color:#999;">—</td>'
                    f'<td style="padding:2px 6px;text-align:right;color:#999;">—</td>'
                    f'<td style="padding:2px 6px;text-align:right;color:#999;">—</td>'
                    f'</tr>'
                )

        tooltip_html = (
            f'<div style="font-family:Inter,-apple-system,sans-serif;font-size:12px;min-width:320px;">'
            f'<div style="font-size:14px;font-weight:700;color:#1a3a5c;margin-bottom:4px;">{label}</div>'
            f'<div style="color:#555;margin-bottom:4px;">{address}</div>'
            f'<div style="font-size:11px;color:#666;margin-bottom:4px;">'
            f'&#9650; Elevation: <b>{asset_elev_str}</b>&nbsp;&nbsp;|&nbsp;&nbsp;'
            f'Building value: £{BUILDING_VALUE:,.0f} (MCM commercial)</div>'
            f'<table style="border-collapse:collapse;width:100%;font-size:11px;">'
            f'<tr style="border-bottom:1px solid #ddd;font-weight:600;color:#333;">'
            f'<td style="padding:3px 6px;">Return Period</td>'
            f'<td style="padding:3px 6px;text-align:right;">Depth</td>'
            f'<td style="padding:3px 6px;text-align:right;">Damage</td>'
            f'<td style="padding:3px 6px;text-align:right;">Fraction</td>'
            f'<td style="padding:3px 6px;text-align:right;">£ Impact</td>'
            f'</tr>'
            f'{rows_html}'
            f'</table>'
            f'</div>'
        )

        folium.CircleMarker(
            location=[lat, lon],
            radius=8,
            color="#c0392b",
            weight=2,
            fill=True,
            fill_color="#e74c3c",
            fill_opacity=0.9,
            tooltip=folium.Tooltip(tooltip_html, sticky=True),
        ).add_to(fmap)

    # --- Collect region bounds for fly-to-region ---
    region_bounds = {}
    for path in tiffs:
        rid = clean_region_name(path)
        with rasterio.open(path) as src:
            region_bounds[f"Region {rid}"] = [
                [src.bounds.bottom, src.bounds.left],
                [src.bounds.top, src.bounds.right],
            ]
    region_bounds_json = json.dumps(region_bounds, separators=(',', ':'))

    # --- Build flat hover lookup: list of {bounds, rows, cols, grid, unit, label} ---
    # Flatten all regions' layers into a single list for simpler JS lookup
    flat_hover = []
    for region_name, layers in all_hover_data.items():
        for layer_name, ld in layers.items():
            flat_hover.append(ld)

    hover_json = json.dumps(flat_hover, separators=(',', ':'))
    elev_grids_json = json.dumps(elev_hover_grids, separators=(',', ':'))
    asset_coords_json = json.dumps(
        [[lat, lon] for lat, lon, *_ in ASSETS], separators=(',', ':')
    )
    hover_data_js = f"""
    <script>
    var _hoverGrids = {hover_json};
    var _elevGrids = {elev_grids_json};
    var _assetCoords = {asset_coords_json};
    </script>
    """
    fmap.get_root().html.add_child(folium.Element(hover_data_js))

    # --- Hover tooltip JS ---
    # Simple approach: on mousemove, scan ALL grids for a non-null value at cursor.
    # No need to detect which layer is active — if there's data, show it.
    hover_tooltip_js = """
    <style>
    #floodTooltip {
        position: fixed;
        z-index: 99999;
        pointer-events: none;
        background: rgba(255,255,255,0.95);
        border: 1px solid #2166ac;
        border-radius: 6px;
        padding: 8px 12px;
        font-size: 13px;
        font-family: 'Inter', -apple-system, sans-serif;
        box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        display: none;
        max-width: 400px;
        line-height: 1.5;
    }
    #floodTooltip .tt-row { display: flex; justify-content: space-between; align-items: baseline; gap: 12px; }
    #floodTooltip .tt-label { color: #555; font-size: 11px; white-space: nowrap; }
    #floodTooltip .tt-value { color: #2166ac; font-weight: 700; font-size: 14px; }
    #floodTooltip .tt-coords { color: #999; font-size: 10px; margin-top: 4px; border-top: 1px solid #eee; padding-top: 3px; }
    </style>
    <div id="floodTooltip"></div>
    <script>
    (function() {
        function setupHoverTooltip() {
            // Find Leaflet map object
            var mapObj = null;
            for (var key in window) {
                try { if (window[key] instanceof L.Map) { mapObj = window[key]; break; } } catch(e) {}
            }
            if (!mapObj) {
                setTimeout(setupHoverTooltip, 500);
                return;
            }

            var tooltip = document.getElementById('floodTooltip');
            var grids = window._hoverGrids;
            if (!grids || grids.length === 0) { console.warn('No hover grids'); return; }

            // --- Elevation lookup from pre-computed LIDAR DTM 1m grids ---
            var _elevGrids = window._elevGrids || [];

            function lookupElevation(lat, lng) {
                for (var i = 0; i < _elevGrids.length; i++) {
                    var g = _elevGrids[i];
                    var south = g.bounds[0][0], west = g.bounds[0][1];
                    var north = g.bounds[1][0], east = g.bounds[1][1];
                    if (lat < south || lat > north || lng < west || lng > east) continue;
                    var row = Math.floor((north - lat) / (north - south) * g.rows);
                    var col = Math.floor((lng - west) / (east - west) * g.cols);
                    row = Math.max(0, Math.min(row, g.rows - 1));
                    col = Math.max(0, Math.min(col, g.cols - 1));
                    var val = g.grid[row][col];
                    if (val !== null) return val;
                }
                return null;
            }

            function lookupAll(lat, lng) {
                var results = [];
                for (var i = 0; i < grids.length; i++) {
                    var g = grids[i];
                    var south = g.bounds[0][0], west = g.bounds[0][1];
                    var north = g.bounds[1][0], east = g.bounds[1][1];
                    if (lat < south || lat > north || lng < west || lng > east) continue;

                    var row = Math.floor((north - lat) / (north - south) * g.rows);
                    var col = Math.floor((lng - west) / (east - west) * g.cols);
                    row = Math.max(0, Math.min(row, g.rows - 1));
                    col = Math.max(0, Math.min(col, g.cols - 1));

                    var val = g.grid[row][col];
                    if (val !== null) {
                        results.push({ value: val, unit: g.unit, label: g.label });
                    }
                }
                return results;
            }

            // Deduplicate: keep unique labels, prefer first occurrence
            function dedup(results) {
                var seen = {};
                var out = [];
                for (var i = 0; i < results.length; i++) {
                    if (!seen[results[i].label]) {
                        seen[results[i].label] = true;
                        out.push(results[i]);
                    }
                }
                return out;
            }

            mapObj.on('mousemove', function(e) {
                var results = dedup(lookupAll(e.latlng.lat, e.latlng.lng));
                if (results.length === 0) {
                    tooltip.style.display = 'none';
                    return;
                }
                var html = '';
                var rc = window._riskColors || {};
                for (var i = 0; i < results.length; i++) {
                    var r = results[i];
                    var valStr, style;
                    if (r.unit) {
                        valStr = r.value.toFixed(2) + ' ' + r.unit;
                        style = '';
                    } else {
                        var score = Math.round(r.value);
                        valStr = score.toString();
                        var c = rc[score] || rc[String(score)] || '#d73027';
                        style = ' style="color:' + c + '"';
                    }
                    html += '<div class="tt-row"><span class="tt-label">' + r.label + '</span>'
                          + '<span class="tt-value"' + style + '>' + valStr + '</span></div>';
                }
                html += '<div class="tt-coords">' + e.latlng.lat.toFixed(5) + ', ' + e.latlng.lng.toFixed(5)
                      + '&nbsp;&nbsp;&#9650; <span id="ttElev">…</span>'
                      + '</div>';
                tooltip.innerHTML = html;
                tooltip.style.display = 'block';
                // Instant elevation from pre-computed LIDAR grid
                var elev = lookupElevation(e.latlng.lat, e.latlng.lng);
                var el = document.getElementById('ttElev');
                if (el) {
                    if (elev !== null) {
                        el.textContent = elev.toFixed(1) + ' m';
                    } else {
                        el.textContent = '…';
                        // Fallback: Open-Meteo API for areas without LIDAR
                        var _elevCache = window._elevCache || (window._elevCache = {});
                        var cacheKey = e.latlng.lat.toFixed(3) + ',' + e.latlng.lng.toFixed(3);
                        if (_elevCache[cacheKey] !== undefined) {
                            el.textContent = (_elevCache[cacheKey] !== null) ? _elevCache[cacheKey].toFixed(1) + ' m' : '—';
                        } else {
                            _elevCache[cacheKey] = null;
                            fetch('https://api.open-meteo.com/v1/elevation?latitude='
                                + e.latlng.lat.toFixed(4) + '&longitude=' + e.latlng.lng.toFixed(4))
                                .then(function(r){ return r.json(); })
                                .then(function(d){
                                    if (d && d.elevation && d.elevation[0] != null) {
                                        _elevCache[cacheKey] = d.elevation[0];
                                        var cur = document.getElementById('ttElev');
                                        if (cur) cur.textContent = d.elevation[0].toFixed(1) + ' m';
                                    }
                                }).catch(function(){});
                        }
                    }
                }
                // Hide flood tooltip near asset markers (asset tooltip already shows depth/damage)
                var nearAsset = false;
                var assets = window._assetCoords || [];
                for (var a = 0; a < assets.length; a++) {
                    var pt = mapObj.latLngToContainerPoint(L.latLng(assets[a][0], assets[a][1]));
                    var dx = e.containerPoint.x - pt.x;
                    var dy = e.containerPoint.y - pt.y;
                    if (dx*dx + dy*dy < 900) { nearAsset = true; break; }  // 30px radius
                }
                if (nearAsset) {
                    tooltip.style.display = 'none';
                    return;
                }
                // Position to the right of cursor, flip left if near edge
                var tw = tooltip.offsetWidth || 400;
                var th = tooltip.offsetHeight || 150;
                var x = e.originalEvent.clientX + 16;
                var y = e.originalEvent.clientY + 16;
                if (x + tw + 10 > window.innerWidth) x = e.originalEvent.clientX - tw - 16;
                if (y + th + 10 > window.innerHeight) y = e.originalEvent.clientY - th - 16;
                tooltip.style.left = x + 'px';
                tooltip.style.top = y + 'px';
            });

            mapObj.on('mouseout', function() {
                tooltip.style.display = 'none';
            });

            console.log('Hover tooltip ready! (' + grids.length + ' grids)');
        }
        // Wait for map to init
        if (document.readyState === 'complete') { setTimeout(setupHoverTooltip, 1000); }
        else { window.addEventListener('load', function() { setTimeout(setupHoverTooltip, 1000); }); }
    })();
    </script>
    """
    fmap.get_root().html.add_child(folium.Element(hover_tooltip_js))

    # --- Restyle the GroupedLayerControl + collapsible regions ---
    risk_colors_json = json.dumps(RISK_COLORS, separators=(',', ':'))

    # Build discrete risk legend items HTML
    risk_legend_items = "\n      ".join(
        f'<div class="rl-item"><span class="rl-swatch" style="background:{color}"></span>{score}</div>'
        for score, color in sorted(RISK_COLORS.items())
    )

    js = f"""
    <style>
    /* Modern restyled layer control */
    .leaflet-control-layers {{
        border: none !important;
        border-radius: 10px !important;
        box-shadow: 0 4px 20px rgba(0,0,0,0.12) !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
        font-size: 13px !important;
        min-width: 260px;
        max-width: 300px;
        background: #fff !important;
    }}

    /* Custom panel */
    #layerPanel {{
        position: absolute;
        top: 10px;
        right: 10px;
        z-index: 1000;
        background: #fff;
        border-radius: 10px;
        box-shadow: 0 4px 24px rgba(0,0,0,0.15);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        font-size: 13px;
        width: 280px;
        max-height: 85vh;
        display: flex;
        flex-direction: column;
        overflow: hidden;
        transition: width 0.2s;
    }}
    .leaflet-control-layers-list {{
        max-height: 70vh;
        overflow-y: auto;
        padding: 8px 4px;
    }}

    /* Region group headers */
    .leaflet-control-layers-group-label {{
        display: flex !important;
        align-items: center;
        cursor: pointer;
        padding: 8px 10px;
        margin: 2px 0;
        border-radius: 8px;
        background: #f0f6ff;
        border: 1px solid #d0e3f7;
        font-weight: 700 !important;
        font-size: 13px !important;
        color: #1a3a5c !important;
        user-select: none;
        transition: background 0.15s;
    }}
    .leaflet-control-layers-group-label:hover {{
        background: #dceaf8;
    }}
    .leaflet-control-layers-group-name {{
        flex: 1;
    }}

    /* Chevron indicator */
    .leaflet-control-layers-group-label .group-chevron {{
        font-size: 10px;
        color: #6b8db5;
        transition: transform 0.2s;
        margin-left: 8px;
    }}
    .leaflet-control-layers-group-label.expanded .group-chevron {{
        transform: rotate(90deg);
    }}

    /* Collapsible layer list */
    .group-layers-wrap {{
        overflow: hidden;
        max-height: 0;
        transition: max-height 0.25s ease;
        padding-left: 6px;
    }}
    .group-layers-wrap.open {{
        max-height: 500px;
    }}

    /* Individual layer labels */
    .leaflet-control-layers-group label:not(.leaflet-control-layers-group-label) {{
        display: flex !important;
        align-items: center;
        padding: 5px 8px;
        margin: 1px 0;
        border-radius: 6px;
        cursor: pointer;
        transition: background 0.1s;
        font-size: 12px !important;
    }}
    .leaflet-control-layers-group label:not(.leaflet-control-layers-group-label):hover {{
        background: #f5f7fa;
    }}
    .leaflet-control-layers-group label:not(.leaflet-control-layers-group-label) input {{
        accent-color: #2166ac;
        width: 15px;
        height: 15px;
        margin-right: 8px;
    }}

    /* Color swatches */
    .layer-swatch {{
        display: inline-block;
        width: 14px;
        height: 14px;
        border-radius: 3px;
        margin-right: 8px;
        flex-shrink: 0;
        border: 1px solid rgba(0,0,0,0.1);
    }}

    /* Hide toggle button, keep expanded */
    .leaflet-control-layers-toggle {{
        display: none !important;
    }}
    .leaflet-control-layers {{
        display: block !important;
    }}
    .leaflet-control-layers-expanded {{
        display: block !important;
    }}
    </style>

    <script>
    var _riskColors = {risk_colors_json};
    var _regionBounds = {region_bounds_json};
    </script>

    <script>
    (function() {{
        var rpSwatches = ['#c6dbef','#9ecae1','#6baed6','#4292c6','#2171b5','#084594'];
        var riskColors = window._riskColors || {{}};

        function setupLayerControl() {{
            var control = document.querySelector('.leaflet-control-layers-list');
            if (!control) {{ setTimeout(setupLayerControl, 500); return; }}

            // Find Leaflet map object for fly-to
            var mapObj = null;
            for (var key in window) {{
                try {{ if (window[key] instanceof L.Map) {{ mapObj = window[key]; break; }} }} catch(e) {{}}
            }}

            // Force the control to stay expanded
            var wrapper = document.querySelector('.leaflet-control-layers');
            if (wrapper) wrapper.classList.add('leaflet-control-layers-expanded');

            var groups = control.querySelectorAll('.leaflet-control-layers-group');
            if (groups.length === 0) {{ setTimeout(setupLayerControl, 500); return; }}

            groups.forEach(function(group) {{
                var groupLabel = group.querySelector('.leaflet-control-layers-group-label');
                if (!groupLabel || groupLabel.dataset.enhanced) return;
                groupLabel.dataset.enhanced = 'true';

                // Add chevron
                var chevron = document.createElement('span');
                chevron.className = 'group-chevron';
                chevron.textContent = '\u25B6'; // ▶
                groupLabel.appendChild(chevron);

                // Wrap layer labels in a collapsible container
                var allLabels = Array.from(group.querySelectorAll('label'));
                var layerLabels = allLabels.filter(function(l) {{ return l !== groupLabel; }});

                var wrap = document.createElement('div');
                wrap.className = 'group-layers-wrap';
                // Insert after groupLabel
                if (groupLabel.nextSibling) {{
                    group.insertBefore(wrap, groupLabel.nextSibling);
                }} else {{
                    group.appendChild(wrap);
                }}

                layerLabels.forEach(function(label, idx) {{
                    wrap.appendChild(label);
                    // Add color swatches to layer labels
                    var span = label.querySelector('span');
                    var text = span ? span.textContent.trim() : '';
                    var swatch = document.createElement('span');
                    swatch.className = 'layer-swatch';

                    if (text.indexOf('Depth') !== -1) {{
                        swatch.style.background = rpSwatches[Math.min(idx, rpSwatches.length - 1)];
                    }} else if (text.indexOf('Risk') !== -1) {{
                        // Build a mini gradient from RISK_COLORS
                        var cols = Object.values(riskColors);
                        if (cols.length >= 3) {{
                            swatch.style.background = 'linear-gradient(90deg, ' + cols[0] + ', ' + cols[Math.floor(cols.length/2)] + ', ' + cols[cols.length-1] + ')';
                        }}
                    }}

                    var input = label.querySelector('input');
                    if (input && input.nextSibling) {{
                        label.insertBefore(swatch, input.nextSibling);
                    }}
                }});

                // Click to toggle + fly to region
                groupLabel.addEventListener('click', function(e) {{
                    e.preventDefault();
                    e.stopPropagation();
                    var isOpen = wrap.classList.contains('open');
                    if (isOpen) {{
                        wrap.classList.remove('open');
                        groupLabel.classList.remove('expanded');
                    }} else {{
                        wrap.classList.add('open');
                        groupLabel.classList.add('expanded');
                        // Fly to region bounds
                        if (mapObj && _regionBounds) {{
                            var nameSpan = groupLabel.querySelector('.leaflet-control-layers-group-name');
                            var regionName = nameSpan ? nameSpan.textContent.trim() : '';
                            var bounds = _regionBounds[regionName];
                            if (bounds) {{
                                mapObj.flyToBounds(bounds, {{ padding: [30, 30], maxZoom: 12, duration: 0.8 }});
                            }}
                        }}
                    }}
                }});
            }});

            console.log('Layer control enhanced with ' + groups.length + ' collapsible groups');
        }}

        if (document.readyState === 'complete') {{ setTimeout(setupLayerControl, 1500); }}
        else {{ window.addEventListener('load', function() {{ setTimeout(setupLayerControl, 1500); }}); }}
    }})();
    </script>

    <!-- Discrete Risk Score Legend (top-left, hidden by default) -->
    <style>
    #riskLegend {{
        position: fixed;
        top: 12px;
        left: 12px;
        z-index: 10000;
        background: rgba(255,255,255,0.95);
        border-radius: 10px;
        padding: 10px 14px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.18);
        font-family: 'Inter', -apple-system, sans-serif;
        font-size: 12px;
        display: none;
        line-height: 1.6;
    }}
    #riskLegend b {{ color: #1a3a5c; font-size: 13px; }}
    .rl-item {{ display: flex; align-items: center; gap: 8px; }}
    .rl-swatch {{ width: 18px; height: 14px; border-radius: 3px; border: 1px solid rgba(0,0,0,0.1); }}
    </style>
    <div id="riskLegend">
      <b>Flood Risk Score</b>
      {risk_legend_items}
    </div>

    <script>
    (function() {{
        function setupRiskLegendToggle() {{
            var legend = document.getElementById('riskLegend');
            if (!legend) return;
            var labels = document.querySelectorAll('.leaflet-control-layers-group label');
            labels.forEach(function(label) {{
                // Check ALL spans (the first may be a color swatch with no text)
                var spans = label.querySelectorAll('span');
                var hasRisk = false;
                spans.forEach(function(s) {{
                    if (s.textContent.trim().indexOf('Risk') !== -1) hasRisk = true;
                }});
                if (hasRisk) {{
                    var cb = label.querySelector('input[type="checkbox"]');
                    if (cb) {{
                        cb.addEventListener('change', function() {{
                            legend.style.display = cb.checked ? 'block' : 'none';
                        }});
                    }}
                }}
            }});
        }}
        if (document.readyState === 'complete') {{ setTimeout(setupRiskLegendToggle, 2000); }}
        else {{ window.addEventListener('load', function() {{ setTimeout(setupRiskLegendToggle, 2000); }}); }}
    }})();
    </script>
    """

    fmap.get_root().html.add_child(folium.Element(js))

    # --- Basemap switcher JS (called from parent frame) ---
    basemap_js = """
    <script>
    (function() {
        var _basemapLayers = {};
        var _activeBasemap = null;
        var _mapObj = null;

        // Map URL fragments to basemap keys (order matters — more specific first)
        var _urlToKey = [
            ['voyager_only_labels', 'hybrid_labels'],
            ['rastertiles/voyager', 'street'],
            ['World_Topo_Map', 'topo'],
            ['World_Imagery', 'satellite'],
            ['opentopomap.org', 'terrain'],
            ['World_Hillshade', 'hillshade'],
            ['dark_all', 'dark'],
            ['api.os.uk', 'os_outdoor'],
            ['lyrs=m', 'google'],
            ['lyrs=s', 'google_sat'],
            ['api.mapbox.com', 'mapbox'],
            ['tile.openstreetmap.org', 'osm']
        ];

        // Hybrid uses two layers: satellite base + labels overlay
        var _hybridKeys = ['satellite', 'hybrid_labels'];

        // Max zoom per basemap (clamp map zoom when switching)
        var _basemapMaxZoom = {
            street: 20, osm: 19, mapbox: 22, os_outdoor: 16,
            google: 22, google_sat: 22,
            topo: 19, satellite: 21, hybrid: 21, terrain: 17,
            hillshade: 16, dark: 20
        };
        var _defaultMaxZoom = 22;

        function initBasemaps() {
            // Find the Leaflet map object
            var mapDivs = document.querySelectorAll('.folium-map');
            if (!mapDivs.length) return;
            var mapId = mapDivs[0].id;
            _mapObj = window[mapId];
            if (!_mapObj) return;

            // Inject Mapbox token at runtime (passed from parent or URL param)
            var mbToken = '';
            try { mbToken = new URLSearchParams(window.location.search).get('mbtoken') || ''; } catch(e){}
            if (!mbToken) { try { mbToken = window.parent._mapboxToken || ''; } catch(e){} }

            // Inject OS API key at runtime
            var osKey = '';
            try { osKey = window.parent._osApiKey || ''; } catch(e){}

            // Collect basemap tile layers by matching URL patterns
            _mapObj.eachLayer(function(layer) {
                if (layer._url) {
                    // Replace placeholder with real token
                    if (mbToken && layer._url.indexOf('__MAPBOX_TOKEN__') !== -1) {
                        layer.setUrl(layer._url.replace('__MAPBOX_TOKEN__', mbToken));
                    }
                    if (osKey && layer._url.indexOf('__OS_API_KEY__') !== -1) {
                        layer.setUrl(layer._url.replace('__OS_API_KEY__', osKey));
                    }
                    for (var i = 0; i < _urlToKey.length; i++) {
                        if (layer._url.indexOf(_urlToKey[i][0]) !== -1) {
                            var key = _urlToKey[i][1];
                            _basemapLayers[key] = layer;
                            // Remove all except 'street' (default)
                            if (key !== 'street') {
                                _mapObj.removeLayer(layer);
                            } else {
                                _activeBasemap = key;
                            }
                            break;
                        }
                    }
                }
            });
        }

        window.switchBasemap = function(name) {
            if (!_mapObj) return;
            // Remove current basemap layer(s)
            if (_activeBasemap === 'hybrid') {
                // Hybrid = satellite + labels
                for (var h = 0; h < _hybridKeys.length; h++) {
                    if (_basemapLayers[_hybridKeys[h]]) _mapObj.removeLayer(_basemapLayers[_hybridKeys[h]]);
                }
            } else if (_activeBasemap && _basemapLayers[_activeBasemap]) {
                _mapObj.removeLayer(_basemapLayers[_activeBasemap]);
            }
            // Add new basemap layer(s)
            if (name === 'hybrid') {
                for (var h = 0; h < _hybridKeys.length; h++) {
                    if (_basemapLayers[_hybridKeys[h]]) {
                        _basemapLayers[_hybridKeys[h]].addTo(_mapObj);
                        _basemapLayers[_hybridKeys[h]].bringToBack();
                    }
                }
            } else if (_basemapLayers[name]) {
                _basemapLayers[name].addTo(_mapObj);
                _basemapLayers[name].bringToBack();
            }
            _activeBasemap = name;
            // Clamp map zoom to this basemap's max tile level
            var mz = _basemapMaxZoom[name] || _defaultMaxZoom;
            _mapObj.setMaxZoom(mz);
            if (_mapObj.getZoom() > mz) _mapObj.setZoom(mz);
        };

        window.getActiveBasemap = function() {
            return _activeBasemap;
        };

        if (document.readyState === 'complete') { setTimeout(initBasemaps, 500); }
        else { window.addEventListener('load', function() { setTimeout(initBasemaps, 500); }); }
    })();
    </script>
    """
    fmap.get_root().html.add_child(folium.Element(basemap_js))

    fmap.save(OUTPUT_HTML)
    if lidar:
        lidar.close()
    print(f"Map saved at: {OUTPUT_HTML}")

    print("Open in browser — regions expanded by default; click names to collapse.")


if __name__ == "__main__":
    try:
        main()
        print("Finished successfully.")
    except Exception:
        import traceback
        traceback.print_exc()
