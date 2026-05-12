# Python Implementation — Table of Contents
**NASSA module 2026-Jarigsma-001**

## Code

| File | Description |
|------|-------------|
| [GISDataVisualisation_v01.py](../GISDataVisualisation_v01.py) | Main Python module — `GISDataVisualisation` class replicating all NetLogo import and display procedures |
| [demonstration.ipynb](../demonstration.ipynb) | Jupyter notebook demonstrating the module step-by-step using the SAGAscape sample dataset |

## Data files

| File | Description |
|------|-------------|
| [Altitude.asc](../Altitude.asc) | Continuous raster — elevation model in UTM zone 36N (EPSG:32636), 200 × 200 grid |
| [lakesAndRiversRasterized.asc](../lakesAndRiversRasterized.asc) | Binary raster — lakes and rivers presence/absence mask (0 = absent, 1 = present) |
| [categorical_test.asc](../categorical_test.asc) | Categorical raster — land-use/land-cover classes (integer values 1–5), 200 × 200 grid |
| [Points/sagascape-sites-EPSG32636.shp](../Points/sagascape-sites-EPSG32636.shp) | Point shapefile — SAGAscape archaeological site locations in UTM zone 36N |

## Output images

These figures are produced by running `demonstration.ipynb`.

| File | Description |
|------|-------------|
| plot_continuous_with_points.png | Elevation gradient map with SAGAscape site overlays |
| plot_binary_with_points.png | Lakes-and-rivers binary mask with SAGAscape site overlays |
| plot_categorical.png | Categorical land-use/land-cover raster |
