# af373b71d67d

A zero-background grid contains one connected color-3 motif and one hollow
rectangular frame in a single nonzero color other than 3. Erase the source
motif, rotate its normalized shape 90 degrees clockwise, and stamp it beginning
at `(frame_top + 1, frame_left + 1)`. Stamp cells are authoritative: when the
rotated motif reaches a frame edge, color 3 replaces that border cell.

The selected sampler uses deterministic constructive layouts on grids from
8–16 rows by 10–18 columns, cycles eight legal frame colors, and alternates
roomy-anchor and frame-overwrite teaching profiles. The validator also accepts
the canonical two-cell motif; production motifs are restricted to connected
3–5-cell shapes with four distinct quarter-turn orientations so every sampled
board exposes clockwise direction.

Kind: `per_puzzle`. Selected version: `2.1.0`. Canonical rule hash:
`7364b3464a5f`.

Approval is derived by the catalog from current code and retained evidence.
