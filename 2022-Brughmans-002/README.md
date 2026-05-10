# Importing a Roman Transport network

*by Tom Brughmans* (NASSA submission :rocket:)  
*Python implementation by João Messias Sousa da Silva*

## Further information

By Tom Brughmans  
First version: Summer 2018  
This version created 01/09/2018  
NetLogo version used: 6.0.1  
Extension used: nw (pre-packaged with Netlogo 6.0.1)  
https://ccl.northwestern.edu/netlogo/6.0-BETA1/docs/nw.html 

Tutorial document available as a PDF in the [netlogo_implemention folder](netlogo_implementation/Netlogo_Roman-transport_v0.1.pdf)

Cite this tutorial as:
Brughmans, T. (2018). Importing a Roman Transport network with Netlogo, Tutorial, https://archaeologicalnetworks.wordpress.com/resources/#transport  .


This tutorial provides an introduction to finding and assembling pre-existing code to quickly create complex models. It uses code and data linked to the https://projectmercury.eu pages. We will create a Roman transport network by reusing existing code that draws on the open access ORBIS dataset (http://orbis.stanford.edu/), we will create alternative network structures by reusing existing code, and we will explore the impact these different network structures have in light of simple economic processes. This tutorial will reveal the importance of not reinventing the wheel, of searching for appropriate existing code and letting your model-building be inspired by others’ previous work.

See full list of documentation resources in [`documentation`](documentation/tableOfContents.md).

## Python implementation

A Python reimplementation of this module is available in [`python_implementation/`](python_implementation/romanTransportNetwork_v01.py), providing the same distance analysis and visualisation procedures as the original NetLogo model via the `RomanTransportNetwork` class.

**Dependencies:** Python >= 3.9, networkx >= 2.0, matplotlib >= 3.0, numpy >= 1.20

[`demonstration.ipynb`](python_implementation/demonstration.ipynb): Jupyter Notebook demonstrating how to load the ORBIS network, run all four distance analyses, and produce all six visualisations replicating the NetLogo procedures.

See [`python_implementation/documentation`](python_implementation/documentation/tableOfContents.md) for the full list of resources.
