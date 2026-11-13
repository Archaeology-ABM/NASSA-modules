# Changelog

All notable changes to this module are documented in this file.

## [1.0.0] - 2026-11-13

### Added
- Patch-only Dijkstra with a binary-heap frontier (`accumulate-cost`), producing a full cost-distance surface and predecessor pointers.
- nw-extension version: one-off graph construction from the raster (`build-graph`), least-cost path (`least-cost-path-nw`), path cost (`least-cost-nw`) and cost surface (`accumulate-cost-nw`).
- `compare-methods` procedure to check that both methods give the same accumulated costs.
- Handling of NoData (NaN) and negative cost values as barriers.
