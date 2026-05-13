# Epidemic Network
*by Marek Vlach and João Messias Sousa da Silva*

Experimental environment for testing of large array of theoretical conditions for development epidemic event within various quantitative, spatial and connectedness (network structure) aspects.

## License

MIT

## Further information

![Interface screenshot](netlogo_implementation/documentation/Epidemic_Network_Model_v1%20interface.png)

See full list of documentation resources in [`documentation`](documentation/tableOfContents.md).

## Python implementation

Python reimplementation of the NetLogo model as a self-contained `EpidemicModel` class.
The implementation replicates the full simulation logic (cluster generation, population
setup, distance-stratified social network, SEIRD disease progression) and provides two
visualisation functions (`plot_model`, `plot_histograms`) matching the original NetLogo
interface and histogram monitors.

**Dependencies:** Python >= 3.9, numpy >= 1.20, networkx >= 2.0, matplotlib >= 3.0

**Notebook:** [`python_implementation/demonstration.ipynb`](python_implementation/demonstration.ipynb)

**Implementation documentation:** [`python_implementation/documentation/tableOfContents.md`](python_implementation/documentation/tableOfContents.md)
