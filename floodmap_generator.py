"""
Interactive flood-risk map with collapsible per-region layer groups.
- Regions expanded by default; click name to collapse/expand.
- Flood Depth and Risk layers togglable.
"""

__author__ = "Mukharbek Organokov"
__version__ = "2.4.0"

import os
import re
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

# RdYlGn (Reversed) - Most Intuitive
RISK_COLORS = {
#    1:  "#1a9850",  # dark green
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


# === CORE ===
def build_layers_for_region(fmap, tiff_path):
    region_id = clean_region_name(tiff_path)
    overlays = []

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

        for i, rp in enumerate(RETURN_PERIODS[:max_bands], start=1):
            band = src.read(i).astype(float)
            band[band == 0] = np.nan
            band = band / 100.0
            mask = (band > 0) & ~np.isnan(band)
            norm = LogNorm(vmin=max(flood_min, 0.01), vmax=flood_max)
            rgba = np.zeros((*band.shape, 4), dtype=np.uint8)
            rgba[mask] = (cm.Blues(norm(band[mask])) * 255).astype(np.uint8)
            bbox = [[src.bounds.bottom, src.bounds.left], [src.bounds.top, src.bounds.right]]
            layer = folium.raster_layers.ImageOverlay(
                image=rgba,
                bounds=bbox,
                opacity=0.7,
                name=f"Flood Depths → RP {rp} yr",
                show=False,
            )
            layer.add_to(fmap)
            overlays.append(layer)

        if src.count >= RISK_BAND:
            risk = src.read(RISK_BAND).astype(float)
            risk[risk == 0] = np.nan
            risk_rgb = np.zeros((*risk.shape, 3), dtype=np.uint8)
            
            for score, hexcol in RISK_COLORS.items():
                m = (risk == score)
                risk_rgb[m] = (np.array(colors.to_rgb(hexcol)) * 255).astype(np.uint8)
            
            # Create alpha: transparent for risk=1 or NaN, opaque for risk 2-10
            alpha = np.zeros(risk.shape, dtype=float)
            alpha[(risk >= 2) & (risk <= 10)] = 1.0  # Only show risk 2-10
            
            rgba_risk = np.dstack((risk_rgb, (alpha * 255))).astype(np.uint8)
            layer = folium.raster_layers.ImageOverlay(
                image=rgba_risk,
                bounds=[[src.bounds.bottom, src.bounds.left], [src.bounds.top, src.bounds.right]],
                opacity=0.7,
                name="Flood Risk → Score (2–10)",  # Updated name
                show=False,
            )
            layer.add_to(fmap)
            overlays.append(layer)

    return region_id, overlays


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
    for path in tiffs:
        region_id, layers = build_layers_for_region(fmap, path)
        groups[f"Region {region_id}"] = layers

    add_legend(fmap, "Flood Depth (m, log scale)", cmap_name="Blues", vmin=0.01, vmax=5)
    add_discrete_legend(fmap, "Flood Risk Score", RISK_COLORS, valid_values=range(2, 11))

    control = GroupedLayerControl(groups=groups, collapsed=False, exclusive_groups=False)
    control.add_to(fmap)

    # --- Fix collapsible JS ---
    js = """
    <script>
    document.addEventListener('DOMContentLoaded', function() {
        console.log('DOM loaded, waiting for map...');
        
        function setupCollapsible() {
            const layerControl = document.querySelector('.leaflet-control-layers-list');
            if (!layerControl) {
                setTimeout(setupCollapsible, 500);
                return;
            }
            
            console.log('Layer control found!');
            
            const groups = layerControl.querySelectorAll('.leaflet-control-layers-group');
            console.log('Found ' + groups.length + ' groups');
            
            groups.forEach(function(group) {
                if (group.dataset.collapsibleReady) return;
                group.dataset.collapsibleReady = 'true';
                
                const groupName = group.querySelector('.leaflet-control-layers-group-name');
                if (!groupName) return;
                
                const regionText = groupName.textContent.trim();
                console.log('Processing: ' + regionText);
                
                // Find labels but EXCLUDE the one containing the group name
                const groupLabel = group.querySelector('.leaflet-control-layers-group-label');
                const allLabels = Array.from(group.querySelectorAll('label'));
                const checkboxLabels = allLabels.filter(function(label) {
                    return label !== groupLabel;
                });
                
                console.log('Found ' + checkboxLabels.length + ' checkbox labels');
                
                if (checkboxLabels.length === 0) return;
                
                // Create wrapper
                const wrapper = document.createElement('div');
                wrapper.className = 'collapsible-content';
                wrapper.style.display = 'none';
                wrapper.style.paddingLeft = '10px';
                
                // Insert wrapper after the group label
                if (groupLabel.nextSibling) {
                    group.insertBefore(wrapper, groupLabel.nextSibling);
                } else {
                    group.appendChild(wrapper);
                }
                
                // Move checkbox labels into wrapper
                checkboxLabels.forEach(function(label) {
                    wrapper.appendChild(label);
                });
                
                // Style group name (make the group label clickable)
                groupLabel.style.cursor = 'pointer';
                groupLabel.style.fontWeight = 'bold';
                groupLabel.style.userSelect = 'none';
                groupLabel.style.display = 'block';
                groupLabel.style.padding = '5px 0';
                groupLabel.style.marginTop = '8px';
                groupName.textContent = '▸ ' + regionText;
                
                // Add click handler to the group label
                groupLabel.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    
                    if (wrapper.style.display === 'none') {
                        wrapper.style.display = 'block';
                        groupName.textContent = '▾ ' + regionText;
                        console.log('Expanded: ' + regionText);
                    } else {
                        wrapper.style.display = 'none';
                        groupName.textContent = '▸ ' + regionText;
                        console.log('Collapsed: ' + regionText);
                    }
                });
            });
            
            console.log('Collapsible setup complete!');
        }
        
        // Force control to stay open
        setTimeout(function() {
            const control = document.querySelector('.leaflet-control-layers');
            if (control) {
                control.classList.add('leaflet-control-layers-expanded');
                control.style.width = '320px';
            }
            const toggle = document.querySelector('.leaflet-control-layers-toggle');
            if (toggle) {
                toggle.style.display = 'none';
            }
        }, 500);
        
        // Add CSS
        const style = document.createElement('style');
        style.textContent = `
            .leaflet-control-layers {
                width: 320px !important;
            }
            .leaflet-control-layers-list {
                max-height: 70vh;
                overflow-y: auto;
                padding: 10px;
            }
            .leaflet-control-layers-group {
                margin-bottom: 5px;
            }
            .collapsible-content label {
                display: block !important;
                margin: 3px 0 !important;
            }
        `;
        document.head.appendChild(style);
        
        // Start setup
        setTimeout(setupCollapsible, 2500);
    });
    </script>
    """

    fmap.get_root().html.add_child(folium.Element(js))

    fmap.save(OUTPUT_HTML)
    print(f"Map saved at: {OUTPUT_HTML}")

    # Save to root for GitHub Pages
    fmap.save(GITHUB_PAGES_OUTPUT)
    print(f"GitHub Pages version saved at: {GITHUB_PAGES_OUTPUT}")
    print("Ready for deployment!")

    print("Open in browser — regions expanded by default; click names to collapse.")


if __name__ == "__main__":
    try:
        main()
        print("Finished successfully.")
    except Exception:
        import traceback
        traceback.print_exc()
