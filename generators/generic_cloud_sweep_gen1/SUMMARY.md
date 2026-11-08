# generic_cloud_sweep_gen1

gen1: cloudy fields swept by an edge bar.

Scene: a dominant background with random cloud blobs in one color, and a
4-colored bar (width 3-6) on the top or bottom edge. Transform: clear all
cloud cells in the bar's column channel (except the bar row), then stamp
the bar every 2 rows marching away from its edge; every 3rd stamp is
green and additionally paints every maximal cloud run in its row green.

Kind: `generic`. Imported version: `1.0.0`.
Approval is derived by the catalog from current code and retained evidence.
