# fd277c567993

Three equal panels are separated by two full color-5 columns. Panel A contains one connected monochrome object; panel B repeats that object and adds 1–4 color-8 cells; panel C contains a different query object. The rule transfers the added 8-cells by their offsets from A's bounding-box top-left to C's bounding-box top-left, overwriting query cells at target positions.

The v3.1.0 sampler constructively covers panel sizes 5–10 × 5–9, connected object sizes 3–6, 1–4 additions, canonical palette sizes 4 and 5, and both clear and occupied-query overwrite cases. Default samples alternate clear/overwrite so any one of five consecutive pairs may be held out as the query without removing all overwrite witnesses.

Kind: `per_puzzle`. Selected version: `3.1.0`. Canonical rule hash: `1890aa619f98`.
Approval remains a catalog decision; passing review checks does not admit training data.
