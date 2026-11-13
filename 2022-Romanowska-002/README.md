# Out of Africa - Conditional isotropic diffusion
*by Iza Romanowska, Colin D Wren, and Stefani A Cabtree* (NASSA submission :rocket:)

*Python implementation by João Messias Sousa da Silva*

A reimplementation of the classical study by Young and Bettinger (1992) investigating the possible drivers behind the Out of Africa dispersal of modern humans.

## License

<a rel="license" href="http://creativecommons.org/licenses/by-sa/4.0/"><img alt="Creative Commons License" style="border-width:0" src="https://i.creativecommons.org/l/by-sa/4.0/88x31.png" /></a><br />This work is licensed under a <a rel="license" href="http://creativecommons.org/licenses/by-sa/4.0/">Creative Commons Attribution-ShareAlike 4.0 International License</a>.

## References

Romanowska, I., Wren, C., Crabtree, S. 2021. Agent-Based Modeling for Archaeology: Simulating the Complexity of Societies. Santa Fe, NM: SFI Press. [https://www.sfipress.org/books/agent-based-modeling-archaeology](https://www.sfipress.org/books/agent-based-modeling-archaeology)

## Further information

A generalisation of a demic diffusion model, where a number of agents (turtles) are initialised at a given region in a given map, and then reproduce themselves at each time step with a certain probability and only if there is a free adjacent grid cell (patch). A reimplementation of the classical study by Young and Bettinger (1992) investigating the possible drivers behind the Out of Africa dispersal of modern humans. The module code is an adaptation of the content of "ch1_Y&Bdispersal.nlogo" in the public repository associated to Romanowska, Wren, & Crabtree 2021 (https://github.com/SantaFeInstitute/ABMA/blob/master/ch1).

![Interface screenshot](netlogo_implementation/documentation/Out%20of%20Africa%20dispersal%20-%20Conditional%20isotropic%20diffusion%20interface.png)

See full list of documentation resources in [`documentation`](documentation/tableOfContents.md).

## Python implementation

`python_implementation/2022_romanowska_002_v01.py` reproduces the NetLogo procedures `setup`, `go`, `reproduce-population`, `try-to-reproduce` and `reproduce-at`. Rules checked against the NetLogo source:

- all initial agents are created on the point (`inputX`, `inputY`) with an integer random colour `0-139`;
- each agent reproduces with probability `pop_growth` into a random free `neighbors4` patch that is not white (sea); the hatchling colour is the parent colour + 0.1;
- the world wraps horizontally only (as in the `.nlogo` settings).

Colours: the base map and the agents are drawn with the official NetLogo palette (`data/netlogo_palette_7.0.4.csv`, extracted with `extract-rgb`). Agents are drawn as 2x2-patch squares (NetLogo `size 2`, patch size 1).

Defaults (as in the NetLogo interface): 20 agents, start point (361, 176), initial radius 2, `pop_growth` 0.30, world 600 x 351 patches (the size of the example map `worldAboveSeaLevelElevation.png`).

### Dependencies

Python >= 3.9, `numpy`, `matplotlib`, `Pillow`:

```bash
pip install numpy matplotlib Pillow
```

### Run

```bash
python python_implementation/2022_romanowska_002_v01.py --scenario external_image --ticks 200
```

A walk-through is available in [`python_implementation/demonstration.ipynb`](python_implementation/demonstration.ipynb).

### Known limitations

- The random number generator differs from NetLogo's, so runs are statistically but not agent-by-agent identical.
- For images other than the example map, base-map colours are matched to the nearest palette colour (NetLogo's own `import-pcolors` rule was not reverse-engineered); land/sea classification is unaffected.

See [`python_implementation/documentation/tableOfContents.md`](python_implementation/documentation/tableOfContents.md) for the list of Python resources.
