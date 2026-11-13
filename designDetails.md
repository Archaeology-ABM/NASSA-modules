# Design details

## Purpose

Given a raster of costs, the module computes the accumulated cost of travelling from a source cell to every other cell (a cost-distance surface) and the least-cost path from the source to a destination.

## Cost model

Each raster cell holds a cost per unit distance. The cost of moving between two neighbouring cells p and q is

    step cost = distance(p, q) * (cost(p) + cost(q)) / 2

with distance measured between cell centres in patch units (1 for orthogonal and sqrt(2) for diagonal moves). Movement is 8-connected. Cells with `cost < 0` are barriers, and NoData (NaN) cells are converted to `-1` on loading. The world does not wrap, so paths cannot cross the edges.

Costs are isotropic and non-negative, which is what Dijkstra's algorithm requires.

## Implementation 1: patch only

`accumulate-cost` runs Dijkstra's algorithm from a source patch.
- Every patch has an accumulated cost (`acc-cost`, initially 1e30) and a predecessor (`prev`).
- The frontier is a binary min-heap held in two arrays (array extension): costs and patches. When a cheaper route to a patch is found, a new entry is pushed and the old entry stays in the heap. Outdated entries are skipped when popped (lazy deletion).
- Each directed patch-to-patch move is relaxed at most once, so the arrays are sized at 8 entries per patch.
- The search continues until the heap is empty, so the result is the full cost-distance surface. The least-cost path to any destination is read from the `prev` pointers (`path-from-surface`).

## Implementation 2: nw extension

- `build-graph` creates one node per passable patch and one undirected link per pair of neighbouring passable patches. The link `weight` is the step cost. The graph is built once after `setup` and has to be rebuilt only when the cost surface changes.
- `least-cost-path-nw` and `least-cost-nw` use `nw:turtles-on-weighted-path-to` and `nw:weighted-distance-to`.
- `accumulate-cost-nw` queries the weighted distance from the source node to every node and writes the result to the patches. Unreachable patches get 1e30, the same convention as the patch-only method.
- The graph has roughly 4 links per cell with 8-connectivity, so memory use grows quickly with raster size.

## Verification

`compare-methods` runs both methods from the same source and prints the largest absolute difference between the two accumulated-cost surfaces. It should be zero or negligible (floating-point rounding).

## Limitations

- Costs are isotropic. Slope-dependent walking costs, where uphill and downhill differ, would need directed links and a cost function per move.
- Source and destination are set in the `go` procedure and need editing to change.
- Performance has not been benchmarked. In particular, it is not known whether the nw extension reuses the shortest-path tree between the many weighted-distance queries made by `accumulate-cost-nw`.
- Large rasters are limited by NetLogo's memory and speed, as each cell is a patch and, in the nw method, also a turtle with links.
