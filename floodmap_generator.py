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
import base64
from io import BytesIO
import numpy as np
import folium
import rasterio
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
    """For each asset, sample flood depth (band/100) at its exact raster pixel
    across all return periods and all tiffs.
    Returns dict: {asset_label: {rp: depth_m, ...}, ...}"""
    result = {a[2]: {} for a in assets}  # keyed by label
    for path in tiffs:
        with rasterio.open(path) as src:
            max_bands = min(src.count, 6)
            for lat, lon, label, _addr in assets:
                # Check if asset falls within this tiff's bounds
                if not (src.bounds.left <= lon <= src.bounds.right and
                        src.bounds.bottom <= lat <= src.bounds.top):
                    continue
                # Convert lat/lon to pixel row/col
                row, col = src.index(lon, lat)
                row = max(0, min(row, src.height - 1))
                col = max(0, min(col, src.width - 1))
                for i, rp in enumerate(return_periods[:max_bands], start=1):
                    val = float(src.read(i)[row, col]) / 100.0
                    if val > 0:
                        result[label][rp] = val
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

    fmap = folium.Map(location=[center_lat, center_lon], zoom_start=7, tiles="CartoDB Voyager")

    groups = {}
    all_hover_data = {}  # region -> layer_name -> grid data
    for path in tiffs:
        region_id, layers, hover_data = build_layers_for_region(fmap, path)
        groups[f"Region {region_id}"] = layers
        all_hover_data[f"Region {region_id}"] = hover_data

    control = GroupedLayerControl(groups=groups, collapsed=False, exclusive_groups=False)
    control.add_to(fmap)

    # --- Add asset markers with financial damage info ---
    damage_curve = load_damage_curve(DAMAGE_CSV)
    asset_depths = sample_asset_depths(tiffs, ASSETS, RETURN_PERIODS)

    for lat, lon, label, address in ASSETS:
        depths = asset_depths.get(label, {})
        # Build damage table rows
        rows_html = ""
        for rp in RETURN_PERIODS:
            d = depths.get(rp, 0.0)
            if d > 0:
                pct = depth_to_damage_pct(d, damage_curve)
                dmg = BUILDING_VALUE * pct / 100.0
                rows_html += (
                    f'<tr>'
                    f'<td style="padding:2px 6px;">{rp} yr</td>'
                    f'<td style="padding:2px 6px;text-align:right;color:#2166ac;font-weight:600;">{d:.2f} m</td>'
                    f'<td style="padding:2px 6px;text-align:right;">{pct:.1f}%</td>'
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
                    f'</tr>'
                )

        tooltip_html = (
            f'<div style="font-family:Inter,-apple-system,sans-serif;font-size:12px;min-width:280px;">'
            f'<div style="font-size:14px;font-weight:700;color:#1a3a5c;margin-bottom:4px;">{label}</div>'
            f'<div style="color:#555;margin-bottom:6px;">{address}</div>'
            f'<div style="font-size:11px;color:#888;margin-bottom:3px;">'
            f'Building value: £{BUILDING_VALUE:,.0f} (MCM commercial)</div>'
            f'<table style="border-collapse:collapse;width:100%;font-size:11px;">'
            f'<tr style="border-bottom:1px solid #ddd;font-weight:600;color:#333;">'
            f'<td style="padding:3px 6px;">Return Period</td>'
            f'<td style="padding:3px 6px;text-align:right;">Depth</td>'
            f'<td style="padding:3px 6px;text-align:right;">Damage</td>'
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
    asset_coords_json = json.dumps(
        [[lat, lon] for lat, lon, *_ in ASSETS], separators=(',', ':')
    )
    hover_data_js = f"""
    <script>
    var _hoverGrids = {hover_json};
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
        max-width: 260px;
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

            // --- Elevation lookup via Open-Meteo (free, no key) ---
            var _elevCache = {};    // "lat,lng" → elevation (m)
            var _elevPending = {};  // in-flight keys
            var _lastElevKey = '';
            var _elevTimer = null;

            function fetchElevation(lat, lng) {
                // Round to ~11 m precision to limit unique requests
                var rlat = Math.round(lat * 10000) / 10000;
                var rlng = Math.round(lng * 10000) / 10000;
                var key = rlat + ',' + rlng;
                _lastElevKey = key;
                if (_elevCache.hasOwnProperty(key)) return;  // already cached
                if (_elevPending[key]) return;                // request in-flight
                _elevPending[key] = true;
                if (_elevTimer) clearTimeout(_elevTimer);
                _elevTimer = setTimeout(function() {
                    var url = 'https://api.open-meteo.com/v1/elevation?latitude=' + rlat + '&longitude=' + rlng;
                    fetch(url).then(function(r){ return r.json(); }).then(function(d){
                        if (d && d.elevation && d.elevation.length) {
                            _elevCache[key] = d.elevation[0];
                        }
                        delete _elevPending[key];
                        // Update tooltip if cursor still near same spot
                        if (_lastElevKey === key) { updateElevInTooltip(key); }
                    }).catch(function(){ delete _elevPending[key]; });
                }, 150);  // 150ms debounce
            }

            function updateElevInTooltip(key) {
                var el = document.getElementById('ttElev');
                if (el && _elevCache.hasOwnProperty(key)) {
                    el.textContent = _elevCache[key].toFixed(1) + ' m';
                }
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
                // Kick off elevation fetch (debounced + cached)
                fetchElevation(e.latlng.lat, e.latlng.lng);
                // Show cached elevation immediately if available
                var rlat = Math.round(e.latlng.lat * 10000) / 10000;
                var rlng = Math.round(e.latlng.lng * 10000) / 10000;
                var ek = rlat + ',' + rlng;
                if (_elevCache.hasOwnProperty(ek)) {
                    var el = document.getElementById('ttElev');
                    if (el) el.textContent = _elevCache[ek].toFixed(1) + ' m';
                }
                // Check proximity to any asset marker (pixel distance)
                var nearAsset = false;
                var assets = window._assetCoords || [];
                for (var a = 0; a < assets.length; a++) {
                    var pt = mapObj.latLngToContainerPoint(L.latLng(assets[a][0], assets[a][1]));
                    var dx = e.containerPoint.x - pt.x;
                    var dy = e.containerPoint.y - pt.y;
                    if (dx*dx + dy*dy < 900) { nearAsset = true; break; }  // 30px radius
                }
                // Position: left of cursor near asset, right otherwise
                var tw = tooltip.offsetWidth || 260;
                var x, y = e.originalEvent.clientY + 16;
                if (nearAsset) {
                    x = e.originalEvent.clientX - tw - 20;
                    if (x < 0) x = e.originalEvent.clientX + 16;
                } else {
                    x = e.originalEvent.clientX + 16;
                    if (x + tw + 10 > window.innerWidth) x = e.originalEvent.clientX - tw - 16;
                }
                if (y + 150 > window.innerHeight) y = e.originalEvent.clientY - 150;
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

    fmap.save(OUTPUT_HTML)
    print(f"Map saved at: {OUTPUT_HTML}")

    print("Open in browser — regions expanded by default; click names to collapse.")


if __name__ == "__main__":
    try:
        main()
        print("Finished successfully.")
    except Exception:
        import traceback
        traceback.print_exc()
