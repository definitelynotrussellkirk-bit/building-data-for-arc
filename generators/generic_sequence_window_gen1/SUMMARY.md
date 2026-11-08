# generic_sequence_window_gen1

gen1: shape progressions + gray-bracket window, two shape families.

Scene: n=3-5 shapes march along one axis with constant gap and affine
sizes, anchored on a shared top/bottom line, colored by a 2-3 color
cycle. Families: PERIODIC TOWERS (constant width, unit rows tiled i+base
times, optional cap row) and GROWING ARMS (t-like: spine column full
height, full rows at fixed anchor-distances, width and height +1 per
step). Two gray corner brackets frame the bbox (or a row-crop of it) of
the NEXT element (or the one BEFORE the first); output = its content.
Vertical variants transpose the whole scene. Scenes resample until the
detector's output equals the intended construction.

Kind: `generic`. Imported version: `1.0.0`.
Approval is derived by the catalog from current code and retained evidence.
