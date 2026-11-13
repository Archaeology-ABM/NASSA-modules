## 1.2.0
- Addition of a Python implementation (`python_implementation/`) by João Messias Sousa da Silva, following Workflow B of the NASSA guide.
  - Reproduces the NetLogo rules: all initial agents start on (inputX, inputY) with integer random colours (0-139); hatchlings get colour + 0.1; reproduction into a free non-white `neighbors4` patch with probability `pop_growth`; world wraps horizontally only.
  - Base-map colours and agent colours use the official NetLogo palette (extracted with `extract-rgb`, NetLogo 7.0.4); base map identical to NetLogo's `import-pcolors` for the example image.
  - Validated against NetLogo 7.0.4 (20 agents, start (361, 176), pop_growth 0.30): same tick-0 map and agents; population and extent at ticks 60 and 200 within the spread of 20 random seeds (see `python_implementation/data/netlogo_reference/`).
- Updated `README.md` and documentation with the Python implementation.
## 1.1.0
- Adaptation to schema v1.0.0.
## 1.0.2
- Adapted NASSA.yml to NASSA-schema v.0.5.1 (SPDX license format).
## 1.0.1
- Adapted NASSA.yml to NASSA-schema v.0.5 (no relative paths).
## 1.0.0
- Creation of the module.