# Native parametric family: legend recolor and column selection

This family keeps the approved `a53fa114c4a9` program byte-for-byte as its
`explicit_mask` default.  Both settings read the same three-row legend/mask
header and recolor the body before producing a cropped output.

- `explicit_mask`: retain every column marked with color 1 in row 2.
- `merged_component`: after recoloring, find the largest monochromatic
  4-connected component and retain only marked columns that intersect it.

The sampler maps two alternating source colors to one target color.  Their
checkerboard rectangle is disconnected before recoloring and a single largest
component afterward.  A smaller solid decoy is the raw-body winner.  This
creates a visible, protected causal test: replacing the recolored intermediate
with the raw body selects different columns and changes the final crop.

`audit.py` is a reusable bounded verifier for protected Racket execution,
matched inputs, prefix stability, the raw-body counterfactual, and the 30×30
stress case.  Its result is evidence, not owner acceptance or training
admission.
