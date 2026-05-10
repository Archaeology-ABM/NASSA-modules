Importing a Roman Transport network
# Documentation – Python implementation
## Table of contents

- [`romanTransportNetwork_v01.py`](../romanTransportNetwork_v01.py): Main module file implementing the `RomanTransportNetwork` class.

- [`demonstration.ipynb`](../demonstration.ipynb): Jupyter Notebook demonstrating how to load the ORBIS network, run all four distance analyses, and produce all six visualisations replicating the NetLogo procedures.

- Data files:
  - [`orbis.graphml`](../orbis.graphml): ORBIS directed transport network (nodes = settlements, edges = routes with km, days, expense, and route-type attributes).
  - [`orbis_edges_0514.csv`](../orbis_edges_0514.csv): Edge list with route attributes.
  - [`orbis_nodes_0514.csv`](../orbis_nodes_0514.csv): Node list with settlement attributes.
  - [`settlements.csv`](../settlements.csv): Settlement reference data.

- Output examples:
  - [`plot_network.png`](plot_network.png): Transport network coloured by route type (roads grey, sea routes sky blue, rivers white).
  - [`plot_provinces.png`](plot_provinces.png): Settlements coloured by Roman province.
  - [`plot_distance_unweighted.png`](plot_distance_unweighted.png): Greyscale distance map by hop count.
  - [`plot_distance_km.png`](plot_distance_km.png): Greyscale distance map by kilometres.
  - [`plot_distance_days.png`](plot_distance_days.png): Greyscale distance map by travel days.
  - [`plot_distance_expense.png`](plot_distance_expense.png): Greyscale distance map by cost.
