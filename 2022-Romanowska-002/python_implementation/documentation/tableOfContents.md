# Python implementation - Table of contents

Files in `python_implementation/` of the module **Out of Africa - Conditional isotropic diffusion** (`2022-Romanowska-002`).

- [`2022_romanowska_002_v01.py`](../2022_romanowska_002_v01.py): main script (classes `Turtle` and `OutOfAfricaModel`, plotting, command line entry point).
- [`demonstration.ipynb`](../demonstration.ipynb): notebook that sets the inputs, runs the model and plots the result.
- [`worldAboveSeaLevelElevation.png`](../worldAboveSeaLevelElevation.png): example input map (600 x 351 px; white = sea).
- [`data/netlogo_palette_7.0.4.csv`](../data/netlogo_palette_7.0.4.csv): NetLogo palette (`extract-rgb`, NetLogo 7.0.4) used to draw patches and agents.
- [`data/import_pcolors_lookup_worldAboveSeaLevelElevation.csv`](../data/import_pcolors_lookup_worldAboveSeaLevelElevation.csv): RGB to `pcolor` table produced by NetLogo `import-pcolors` for the example map.
- [`data/netlogo_reference/`](../data/netlogo_reference/): NetLogo 7.0.4 output used for validation (`pcolors.txt`, agents at ticks 0, 60 and 200; seed 12345, 20 agents, start (361, 176), `pop_growth` 0.30).
