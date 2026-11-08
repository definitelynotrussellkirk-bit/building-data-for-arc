# Native parametric family: repeated pair → selected member

`output_mode=canonical_shape` returns the exact canonical authority unchanged:
find the largest object in each of the three divider-separated panels, identify
the D4 class occurring twice, and output its canonical cyan shape.

`output_mode=selector_member` adds a non-collapsing sequential dependency. First
identify the two largest objects sharing a D4 class. Then the unique singleton
selector (`1` = left member, `2` = right member) chooses within that ordered pair,
and the chosen object's **observed** normalized orientation is output in cyan.
The marker host is deliberately unrelated to the selected panel.

The input sampler is shared across settings. It supports 2–6 demonstrations and
exactly four distinct queries, including a substantive 30×30 case with three
45-cell largest objects. `adapter.py` is the native promotion boundary;
`prototype.py` also exposes bounded finite-rival teaching checks and a causal
wrong-intermediate witness recipe.
