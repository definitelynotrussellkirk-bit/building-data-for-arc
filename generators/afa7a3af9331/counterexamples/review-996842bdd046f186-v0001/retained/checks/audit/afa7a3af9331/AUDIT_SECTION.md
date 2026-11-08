## afa7a3af9331

**Finding: reproduced shortcut in the sampled lesson support; no generated-label mismatch found.** The unchanged canonical rule independently normalizes both monochrome objects to their own top-left corners, overlays them, preserves exclusive colors, and colors overlap 8. The current sampler always places both objects at row 1 with the same bounding-box height. This lets a simpler rival normalize each object's column while preserving their original relative rows. Every generated object already has the same top row, so the missing independent vertical normalization is invisible on those lessons.

The independent rival is `preserve_relative_rows` in `checks/audit/afa7a3af9331/probe.py`. It uses no seeds, hard-coded shape dimensions, labels, or canonical exceptions. It matched the canonical Racket output on **12/12 ordinary draws**: seeds 1700, 1701 and 1702 for easy, medium and hard respectively, each at sample indices 0..3 with no overrides. It disagreed on **4/4 canonical anchors**, whose objects have separate vertical placements. This is a gap between sampled training support and the canonical task's normalization requirement, not a claim that this rival explains the original task.

**Concrete witness.** Start with `generate(1700, 3, difficulty="easy")`, then move only the right object down by one row without changing canvas dimensions, object shapes, or colors. The selected `self_check` accepts both the original and translated input. Actual public `arcpuzzles apply` execution gives the same canonical output for both:

```json
[[8,8],[7,9],[7,9]]
```

The rival instead produces the following on the translated input:

```json
[[7,7],[8,9],[7,9],[0,9]]
```

The first three easy draws form saved demonstrations that all fit the rival. Its original generated query also fits. The translated query refutes it. Exact inputs, recipe, domain results, actual Racket outputs and rival predictions are in `cases.json`, `racket.json` and `assessment.json` under `checks/audit/afa7a3af9331/`; `shifted_input.json` isolates the witness, and `lesson_public.json` contains the complete three-demonstration challenge with only the translated query input.

**Bounds and existing checks.** The new public Racket probe executed **17/17 inputs successfully**: four canonical anchors, twelve generated draws and one translated witness. All 17 passed the selected generator's domain check, and its Python mirror matched all 17 actual outputs. The combined audit check also passed: **3/3 task tests**, a **600/600 draw census with zero crashes**, **12/12 identifiable lessons**, and **48 diagnostic query rotations with zero reported ambiguities**. Those lesson checks cover the existing `discard_object_colors` rival and generic candidates; they do not test the new row-preserving rival. The gate receipt is `checks/audit/afa7a3af9331/combined/result.json`, with detailed denominators in `combined/checks/afa7a3af9331_audit_semantic_gate.json`.

**Source binding.** The unchanged generator SHA-256 is `4c472e2c1d0dd4ad0a69dd5b4d9f623b147a0b9b3f2eaceb88a850f60851eeef`. The selected rule pin is `a235c2b1bb6c`; the executed callable text SHA-256 is `6dd23b2ffd0d0fb128284e8a31c58e9d40f58aaef6887664e1d489867d43b1a9`. The exact selected canonical `program_solution` text and its separate hash are retained in `cases.json`. Source hashes were rechecked after the probes.

**Suggested follow-up, not implemented here.** Independently vary each operand's vertical offset while preserving two connected objects; include demonstrations that refute relative-row preservation before using such a query, and retain this rival/witness in the task's future tests. The witness is inside the current `self_check` and canonical-rule domain but outside the sampler's aligned-row support. This findings-only audit changes no task source, rule, approval, or admission status. It does not establish a finite generated-query ambiguity, a label bug, or a solver-learning result.
