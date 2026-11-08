# Blind derivation notes

Exposure before freezing: **no**. Reference material consulted before freezing:
**no**.

The visible examples contain one compact multicolor component with a color-5
anchor, one or more color-6 target cells, and occasionally an isolated extra
5. The output copies the complete anchored component around every 6, aligning
the component's anchor 5 with the target and clipping at grid boundaries. The
isolated 5 is ignored because its component has no non-5 motif content.

The implementation finds components among nonzero, non-6 cells under
Chebyshev distance at most two, selects the component containing color 5 with
the most non-5 cells, records offsets from its anchor, and stamps those offsets
at every 6. It passed all three visible examples during the original blind
phase.
