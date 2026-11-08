# 3adf11522bf5

**Selected generator:** v3.0.0
**Canonical rule pin:** `a18583a5c8f2`

The input is a rectangular zero-background grid containing exactly one obstacle
color from 2–9. For every zero cell, compute the largest all-zero square whose
top-left corner is that cell. Paint color 1 on the union of every globally
largest square. Also paint every all-zero square of side at least 2 whose entire
footprint is disjoint from that fixed maximal union. Preserve all obstacles.

The sampler exposes exact observable controls for height, width, obstacle color,
and scene profile. Every declared value is legal in every difficulty band. A
20-slot shape schedule gives each band broad support while placing a 10×10,
two-color canonical profile in 5/20 slots. The semantic schedule emits a
`canonical2` scene once per four samples and a `teaching` scene otherwise.
Teaching scenes force all of these counterexamples:

- a disjoint smaller square, refuting “paint only globally largest squares”;
- an overlapping smaller-square fringe, refuting “paint every square cell”;
- tied largest squares, refuting “paint only the first largest square”;
- non-5 obstacle colors, refuting the strongest canonical-fitting color-5 shortcut.

`self_check` and `strict_canonical_like` enforce the sampled manifold, while
`rule_mirror`, executable rivals/witnesses, and `lesson_identifiable` provide a
reusable semantic contract. See `workspace/reference_probe.py`,
`workspace/curriculum_probe.py`, and `tests/test_generator.py`.

The selected Racket program was not semantically changed. Its selected base
`target_code` was synchronized byte-for-byte to the existing canonical source;
the minified `raw_code` remains archival.
