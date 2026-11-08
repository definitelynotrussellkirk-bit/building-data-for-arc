# 00ed2544a15e

For every horizontal or vertical pair of red (`2`) cells, paint the strictly
interior cells cyan (`8`) only when the original inclusive segment contains
exactly those two reds and otherwise only black (`0`). A third red or any other
color blocks that span; unrelated cells are unchanged.

Version `3.0.0` uses a constructive three-profile curriculum
(`h_chain`, `v_chain`, `cross`). Every ordinary example contains clear
horizontal and vertical connections, a color-blocked aligned pair, an isolated
red, and a chain/shared-endpoint case. Thus each example refutes identity,
horizontal-only, vertical-only, ignore-blockers, and simple-pairs-only rivals.

Declared exact controls are `grid_h=8..12`, `grid_w=9..13`, and
`profile=h_chain|v_chain|cross`; all legal joint combinations are constructive
and observable. The canonical authority is pinned by
`RULE_HASH = "92ea0e00d9a5"`.

Kind: `per_puzzle`. Imported/reviewed version: `3.0.0`.
Approval is derived by the catalog from current code and retained evidence.
