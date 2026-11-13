# DijkstraLCP
*by Philip Verhagen*

Least-cost paths and cost-distance surfaces over a raster with Dijkstra's algorithm in NetLogo. The same problem is solved in two ways: directly on patches, using a binary-heap frontier, and with the nw extension, using a graph built once from the raster. Both methods give the same accumulated costs, so they can be compared or swapped depending on raster size.

## License

MIT

## References

Dijkstra, E. W. (1959). A note on two problems in connexion with graphs. *Numerische Mathematik*, 1, 269-271.

## Further information

The cost of a move between two neighbouring cells is the distance between their centres multiplied by the mean of the two cell costs, so diagonal moves cost sqrt(2) times as much as orthogonal ones. Cells with a negative or missing cost are barriers. Costs are isotropic: moving from A to B costs the same as moving from B to A.

Contents: `documentation/` has the design notes, and `netlogo_implementation/` holds the model (`DijkstraLCP.nlogo`), its instructions, an example input folder and an output folder. See `netlogo_implementation/documentation/instructions.md` to run the model.

This piece of code was largely developed using Claude Sonnet 5.5. The code was only tested on a single test cost surface, and will be less suited for use with larger datasets.
