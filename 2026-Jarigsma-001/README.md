# Visualising GIS Rasters and Vector Data in NetLogo
*by Amber Esha Jarigsma; Python implementation by João Messias Sousa da Silva*

This module provides a generic and reusable framework for importing and visualising GIS data in NetLogo. It is designed to illustrate how different types of spatial data can be loaded, interpreted and displayed within a NetLogo environment.

The module supports:
- **Continuous rasters** (e.g. elevation, cost surfaces), visualised using colour gradients  
- **Binary rasters** (e.g. land/water masks), visualised using discrete colour assignments  
- **Categorical rasters** (e.g. land-use or land-cover classes), visualised using category-specific colours  
- **Point vector data** (e.g. site locations), visualised as turtle agents positioned from GIS coordinates  

## Python implementation

The Python reimplementation provides a `GISDataVisualisation` class that replicates all import and display procedures from the original NetLogo model using `rasterio`, `geopandas`, and `matplotlib`.

**Dependencies:** Python >= 3.9, geopandas >= 0.12, matplotlib >= 3.5, numpy >= 1.20, rasterio >= 1.3

**Demonstration notebook:** [python_implementation/demonstration.ipynb](python_implementation/demonstration.ipynb)

**Implementation documentation:** [python_implementation/documentation/tableOfContents.md](python_implementation/documentation/tableOfContents.md)

## License
**MIT** 

## References
Boogers, S., & Daems, D. (2022). SAGAscape: Simulating resource exploitation strategies in Iron Age to Hellenistic communities in Southwest Anatolia. Journal of Computer Applications in Archaeology, 5(1), 169–187. https://doi.org/10.5334/jcaa.90

## Further information
This module is implemented in NetLogo and Python and is intended as a general-purpose example of GIS raster and vector visualisation for agent-based modelling. Users are expected to replace placeholder file paths with their own GIS datasets and to adapt colour schemes and display logic as required for their specific research questions.
