# Native parametric crop family

The default `crop_policy=fixed_color_9` is the selected canonical program
byte-for-byte: crop the inclusive bounding box of every color-9 marker.

The alternative `crop_policy=selector_parity` is deliberately sequential.
Step A counts the color-2 selector cells and records their parity. Odd selects
color 5; even selects color 9. Step B then finds that selected color's marker
bbox and copies the complete rectangle. The target bbox cannot be chosen until
Step A has produced the input-dependent parity intermediate.

The first two demonstrations use selector counts 1 and 2, so fixed-color-5 and
fixed-color-9 bypasses cannot fit both. Inputs are matched across settings,
demonstration and query streams are independently prefix-stable, and the fourth
query is a substantive 30×30 boundary case. Candidate colors are always present
with distinct bboxes and distinct crop outputs.

`wrong-selector.rkt` reverses the parity mapping for the protected-Racket causal
witness. It is an ablation only, not an admitted setting. `prototype.py` and its
older evidence remain historical; `adapter.py`, `family.py`, the three Racket
files, and `promotion.json` are the native candidate source.
