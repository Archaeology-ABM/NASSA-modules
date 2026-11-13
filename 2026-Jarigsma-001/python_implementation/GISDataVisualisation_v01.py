###############################################################################
# GISDataVisualisation_v01.py
# NASSA module: 2026-Jarigsma-001
# Version: 1.1.0
#
# Original NetLogo module: Amber Esha Jarigsma (2026)
# Python implementation:   João Messias Sousa da Silva (2026)
# Email: joao_messiah@hotmail.com
# ORCID: 0009-0007-4716-3957
#
# References:
#   Boogers & Daems (2022) — SAGAscape: Simulating resource exploitation
#   strategies in Iron Age to Hellenistic communities in Southwest Anatolia.
#   https://doi.org/10.5334/jcaa.90
#
# Replicated NetLogo procedures:
#   load-coordinate-system    -> GISDataVisualisation.__init__
#   import-continuous-raster  -> GISDataVisualisation.read_raster
#   display-continuous-raster -> GISDataVisualisation.show_continuous_with_points
#   import-binary-raster      -> GISDataVisualisation.read_raster
#   display-binary-raster     -> GISDataVisualisation.show_binary_with_points
#   import-categorical-raster -> GISDataVisualisation.read_raster
#   display-categorical-raster-> GISDataVisualisation.show_categorical_raster
#   import-points             -> GISDataVisualisation.read_points
#   display-points            -> GISDataVisualisation.plot_points
#   display-data              -> GISDataVisualisation.display_all
#   reset                     -> (not applicable; create a new instance)
#
# Dependencies:
#   Python    >= 3.9
#   geopandas >= 0.12   https://geopandas.org/
#   matplotlib>= 3.5    https://matplotlib.org/
#   numpy     >= 1.20   https://numpy.org/
#   rasterio  >= 1.3    https://rasterio.readthedocs.io/
###############################################################################

from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from matplotlib.colors import BoundaryNorm, LinearSegmentedColormap, ListedColormap

###############################################################################
# Constants
###############################################################################

### Colour gradient for continuous rasters: green (low) -> pale yellow (mid)
### -> salmon orange (high). RGB values match the hard-coded list in NetLogo's
### display-continuous-raster procedure.
CONTINUOUS_GRADIENT_COLORS = [
    (0 / 255,   104 / 255,  55 / 255),   ### dark green  — low values
    (255 / 255, 255 / 255, 191 / 255),   ### pale yellow — mid values
    (252 / 255, 141 / 255,  89 / 255),   ### salmon      — high values
]

### Colours for binary raster values.
### 0 = background (no feature); 1 = foreground (feature present).
### Matches NetLogo: display-binary-raster assigns white/black.
BINARY_COLOR_0 = "white"
BINARY_COLOR_1 = "black"

### Category-to-colour list for categorical rasters.
### Index position corresponds to category value - 1 (categories are 1-indexed).
### Matches NetLogo: display-categorical-raster, categories 1-5.
CATEGORY_COLORS = ["white", "blue", "red", "green", "yellow"]

### Category boundary values used by BoundaryNorm: one more entry than colours.
CATEGORY_BOUNDARIES = [1, 2, 3, 4, 5, 6]

### Default scatter plot marker area in points^2.
### Equivalent to the NetLogo point-size slider default.
DEFAULT_POINT_SIZE = 8

### Figure dimensions for wide-format maps (continuous and binary rasters).
WIDE_FIGURE_SIZE = (12, 6)

### Figure dimensions for square-format maps (categorical raster).
SQUARE_FIGURE_SIZE = (6, 6)

###############################################################################
# GISDataVisualisation class
###############################################################################


class GISDataVisualisation:
    """
    Python reimplementation of NASSA module 2026-Jarigsma-001:
    "Visualising GIS Rasters and Vector Data in NetLogo" by Amber Esha Jarigsma.

    Loads GIS raster and point-vector datasets and produces matplotlib figures
    that replicate each display procedure from the original NetLogo model.

    All file paths are accepted at instantiation and resolved lazily: data is
    read from disk only when a visualisation method is called. This mirrors the
    NetLogo workflow where import and display are separate button actions.

    Attributes
    ----------
    continuous_raster_path : pathlib.Path
        Path to an .asc (or any GDAL-readable) raster with continuous numeric
        values (e.g. elevation, cost surface).
    binary_raster_path : pathlib.Path
        Path to a raster with binary values (0 = no feature, 1 = feature).
    categorical_raster_path : pathlib.Path
        Path to a raster whose integer values represent discrete land-use or
        land-cover categories (1-indexed).
    points_path : pathlib.Path
        Path to a shapefile (.shp) containing point vector features.
    point_size : int
        Scatter-plot marker area (points^2) used for all point overlays.

    Methods
    -------
    read_raster(path)
        Read any GDAL-compatible raster; return array, extent, and CRS.
    read_points(target_crs)
        Read point shapefile; reproject to target CRS when necessary.
    plot_points(ax, points)
        Scatter-plot point features on an existing matplotlib Axes.
    show_continuous_with_points()
        Display continuous raster overlaid with point vector features.
    show_binary_with_points()
        Display binary raster overlaid with point vector features.
    show_categorical_raster()
        Display categorical raster with discrete colour assignments.
    display_all()
        Run all three display methods in sequence.
    """

    def __init__(
        self,
        continuous_raster_path,
        binary_raster_path,
        categorical_raster_path,
        points_path,
        point_size=DEFAULT_POINT_SIZE,
    ):
        """
        Store file paths and display parameters.

        Replicates NetLogo procedures:
            load-coordinate-system (CRS is inferred from the raster files)
            import-continuous-raster, import-binary-raster,
            import-categorical-raster, import-points

        Parameters
        ----------
        continuous_raster_path : str or pathlib.Path
            Path to a continuous raster file (e.g. Altitude.asc).
        binary_raster_path : str or pathlib.Path
            Path to a binary raster file (e.g. lakesAndRiversRasterized.asc).
        categorical_raster_path : str or pathlib.Path
            Path to a categorical raster file (e.g. categorical_test.asc).
        points_path : str or pathlib.Path
            Path to a point shapefile (e.g. sagascape-sites-EPSG32636.shp).
        point_size : int, optional
            Scatter-plot marker size in points^2 (default: DEFAULT_POINT_SIZE).

        Returns
        -------
        None
        """
        ### Convert all inputs to Path objects so the rest of the class can rely
        ### on Path semantics (/, .name, .exists(), etc.) regardless of whether
        ### the caller passed a string or a Path.
        self.continuous_raster_path = Path(continuous_raster_path)
        self.binary_raster_path = Path(binary_raster_path)
        self.categorical_raster_path = Path(categorical_raster_path)
        self.points_path = Path(points_path)
        self.point_size = point_size

    ###########################################################################

    @staticmethod
    def read_raster(path):
        """
        Read a raster file and return its data array, spatial extent, and CRS.

        Replicates NetLogo procedures:
            import-continuous-raster, import-binary-raster,
            import-categorical-raster

        Uses rasterio rather than the NetLogo GIS extension because rasterio
        supports the same .asc (Esri ASCII grid) format and exposes the same
        metadata (bounds, CRS, NoData value).
        See: https://rasterio.readthedocs.io/en/latest/quickstart.html

        Parameters
        ----------
        path : str or pathlib.Path
            Path to any GDAL-compatible raster (.asc, .tif, etc.).

        Returns
        -------
        data : numpy.ndarray, shape (rows, cols)
            Raster values as a 2-D float array. NoData cells are replaced with
            numpy.nan so that matplotlib renders them as transparent.
        extent : list of float
            Bounding box [left, right, bottom, top] expected by imshow().
        crs : rasterio.crs.CRS or None
            Coordinate reference system; None if the file carries no CRS.
        """
        ### The 'with' block guarantees the file handle is released even if an
        ### exception occurs while reading — important for large rasters.
        with rasterio.open(path) as src:
            ### read(1) reads band 1 as a 2-D array; band indexing is 1-based in
            ### rasterio (following GDAL convention, unlike numpy's 0-based indexing)
            data = src.read(1)
            nodata = src.nodata      ### sentinel value used for missing cells
            bounds = src.bounds      ### BoundingBox(left, bottom, right, top)
            crs = src.crs            ### coordinate reference system

        ### Replace the NoData sentinel with NaN.
        ### np.where is used instead of masked arrays to keep the output as a
        ### plain ndarray, which imshow() accepts without extra unpacking.
        if nodata is not None:
            data = np.where(data == nodata, np.nan, data)

        ### imshow() maps pixel (row, col) to geographic coordinates via 'extent'.
        ### The order [left, right, bottom, top] matches matplotlib's convention,
        ### which differs from rasterio's BoundingBox order (left, bottom, right, top).
        extent = [bounds.left, bounds.right, bounds.bottom, bounds.top]
        return data, extent, crs

    ###########################################################################

    def read_points(self, target_crs):
        """
        Read a point shapefile and reproject to match the raster CRS if needed.

        Replicates NetLogo procedure:
            import-points
            (reprojection corresponds to gis:set-transformation-ds which aligns
            all loaded datasets to a shared spatial envelope)

        Parameters
        ----------
        target_crs : rasterio.crs.CRS or None
            CRS to reproject into (usually taken from read_raster()). If None,
            no reprojection is attempted.

        Returns
        -------
        points : geopandas.GeoDataFrame
            Point features in the target CRS. The geometry column contains
            shapely Point (or MultiPoint) objects.
        """
        ### gpd.read_file() automatically reads all sidecar files (.dbf, .prj,
        ### .shx, .cpg) that accompany a .shp file, including the CRS from .prj.
        points = gpd.read_file(self.points_path)

        ### Reproject only when both CRS values are known and disagree.
        ### Skipping silently avoids crashes when a file lacks a .prj sidecar.
        if (
            points.crs is not None
            and target_crs is not None
            and points.crs != target_crs
        ):
            ### to_crs() uses pyproj under the hood to transform all geometries;
            ### the original GeoDataFrame is not modified (returns a new object).
            points = points.to_crs(target_crs)

        return points

    ###########################################################################

    def plot_points(self, ax, points):
        """
        Scatter-plot point features on an existing matplotlib Axes.

        Replicates NetLogo procedure:
            display-points

        In NetLogo, each point is represented as a turtle agent at the
        corresponding patch. Here, scatter() places a marker at the exact
        geographic coordinate.

        Parameters
        ----------
        ax : matplotlib.axes.Axes
            Axes object to draw onto (must already contain the raster image).
        points : geopandas.GeoDataFrame
            Point features returned by read_points().

        Returns
        -------
        None
        """
        ### tab10 is a 10-colour qualitative palette designed for categorical data.
        ### np.linspace(0,1,10) samples 10 evenly spaced values across [0,1] so
        ### each of the 10 colours maps to a unique feature.
        colors = plt.cm.tab10(np.linspace(0, 1, 10))

        for i, geom in enumerate(points.geometry):
            ### Skip null or empty geometries that may appear after reprojection
            ### or in datasets where some features lack coordinates.
            if geom is None or geom.is_empty:
                continue

            if geom.geom_type == "Point":
                ### zorder=5 renders points above the raster layer (default zorder=1)
                ax.scatter(geom.x, geom.y, s=self.point_size, color=colors[i % 10], zorder=5)

            elif geom.geom_type == "MultiPoint":
                ### MultiPoint stores individual Point objects in the .geoms iterable
                for p in geom.geoms:
                    ax.scatter(p.x, p.y, s=self.point_size, color=colors[i % 10], zorder=5)

    ###########################################################################

    def show_continuous_with_points(self):
        """
        Display a continuous raster as a colour gradient with points overlaid.

        Replicates NetLogo procedures:
            display-continuous-raster, display-points

        The colour gradient (green -> pale yellow -> salmon orange) matches the
        RGB list hard-coded in the NetLogo display-continuous-raster procedure.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        ### Read raster and extract CRS for reprojecting the point layer
        data, extent, crs = self.read_raster(self.continuous_raster_path)
        points = self.read_points(crs)

        ### LinearSegmentedColormap interpolates smoothly between the three
        ### control-point colours, replicating the NetLogo palette gradient.
        ### Named "netlogo_continuous" for traceability in matplotlib colour bar labels.
        cmap = LinearSegmentedColormap.from_list(
            "netlogo_continuous", CONTINUOUS_GRADIENT_COLORS
        )

        fig, ax = plt.subplots(figsize=WIDE_FIGURE_SIZE)

        ### origin="upper" places row 0 at the top of the figure, matching the
        ### raster's north-up orientation (rasterio reads top-to-bottom).
        ax.imshow(data, cmap=cmap, extent=extent, origin="upper")

        ### Overlay point features after the raster so they appear on top
        self.plot_points(ax, points)

        ax.set_title("Continuous raster + points")
        ax.set_axis_off()   ### hide axes ticks and labels for a cleaner map view
        plt.tight_layout()
        plt.show()

    ###########################################################################

    def show_binary_with_points(self):
        """
        Display a binary raster as two discrete colours with points overlaid.

        Replicates NetLogo procedures:
            display-binary-raster, display-points

        Binary value 0 is rendered white (no feature); value 1 is black
        (feature present). This matches the NetLogo display-binary-raster logic.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        data, extent, crs = self.read_raster(self.binary_raster_path)
        points = self.read_points(crs)

        ### ListedColormap assigns a colour directly by integer index:
        ### index 0 -> BINARY_COLOR_0 (white), index 1 -> BINARY_COLOR_1 (black)
        binary_cmap = ListedColormap([BINARY_COLOR_0, BINARY_COLOR_1])

        fig, ax = plt.subplots(figsize=WIDE_FIGURE_SIZE)

        ### vmin=0, vmax=1 clamp the data range to [0, 1] so the two-colour map
        ### applies correctly even when the raster's stored value range differs
        ### slightly (e.g. floating-point .asc files).
        ax.imshow(data, cmap=binary_cmap, extent=extent, origin="upper", vmin=0, vmax=1)

        self.plot_points(ax, points)

        ax.set_title("Binary raster + points")
        ax.set_axis_off()
        plt.tight_layout()
        plt.show()

    ###########################################################################

    def show_categorical_raster(self):
        """
        Display a categorical raster using discrete colour assignments.

        Replicates NetLogo procedure:
            display-categorical-raster

        Categories 1-5 are mapped to white, blue, red, green, and yellow
        respectively, matching the colour assignments in the NetLogo procedure.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        data, extent, _ = self.read_raster(self.categorical_raster_path)

        ### ListedColormap maps each colourmap index to one named colour.
        ### Because categories are 1-indexed, BoundaryNorm is required to shift
        ### the data range [1, 6) onto colourmap indices [0, 5).
        category_cmap = ListedColormap(CATEGORY_COLORS)

        ### BoundaryNorm maps each interval [n, n+1) in CATEGORY_BOUNDARIES to a
        ### colourmap index; the number of intervals must equal cmap.N (= 5).
        ### See: https://matplotlib.org/stable/api/_as_gen/matplotlib.colors.BoundaryNorm.html
        norm = BoundaryNorm(CATEGORY_BOUNDARIES, category_cmap.N)

        fig, ax = plt.subplots(figsize=SQUARE_FIGURE_SIZE)
        ax.imshow(data, cmap=category_cmap, norm=norm, extent=extent, origin="upper")

        ax.set_title("Categorical raster")
        ax.set_axis_off()
        plt.tight_layout()
        plt.show()

    ###########################################################################

    def display_all(self):
        """
        Run all three visualisation methods in sequence.

        Replicates NetLogo procedure:
            display-data

        In NetLogo, display-data checks whether each dataset has been imported
        before drawing it. Here, all four paths are assumed to be valid because
        they were supplied at instantiation.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        ### Execute each display method in the same order as NetLogo's display-data
        self.show_continuous_with_points()
        self.show_binary_with_points()
        self.show_categorical_raster()


###############################################################################
# Script entry point
###############################################################################

if __name__ == "__main__":
    ### Path(__file__).parent resolves to the directory that contains this script,
    ### making all paths relative and portable across machines.
    base_dir = Path(__file__).parent

    ### Instantiate with the SAGAscape sample dataset bundled in python_implementation/
    vis = GISDataVisualisation(
        continuous_raster_path=base_dir / "Altitude.asc",
        binary_raster_path=base_dir / "lakesAndRiversRasterized.asc",
        categorical_raster_path=base_dir / "categorical_test.asc",
        points_path=base_dir / "Points" / "sagascape-sites-EPSG32636.shp",
    )

    ### Run all visualisation methods and display the figures
    vis.display_all()
