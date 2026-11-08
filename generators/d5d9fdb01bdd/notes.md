# Working notes: d5d9fdb01bdd

## 2026-10-03 repair

The selected `2.0.0` sampler emitted dense four-color rectangles with all four
bbox corners forced.  That distribution rejected every canonical input and made
several advertised controls ineffective.  The authority itself was correct and
was not changed.

Version `3.0.0` restores the demonstrated family: sparse one/two-color
canonical-scale paths, internal zeros, variable placement, and lawful
one-to-three-color generalization.  `self_check` now accepts every canonical
input, public overrides are exact over their full domains, and `RULE_HASH` is
pinned to `1b9c6046c883`.

Two executable rivals are retained:

- `transpose_only_tall_or_square`: fits all four canonical pairs because every
  canonical tight crop has `height >= width`; it leaves a wide crop untransposed.
- `largest_component_only`: fits connected examples but drops disconnected
  content before crop/transpose.

The schedule uses one canonical anchor plus two wide/disconnected witnesses per
three examples.  This redundancy matters: an earlier draft used one witness for
each rival, but a three-of-four query rotation could hide the sole witness and
leave a shortcut alive.  The current schedule passes every query rotation in the
retained `workspace/lesson_probe.py`.

Limitations: declared-rival checks are finite and do not prove universal
induction.  The generalized family intentionally stays within small sparse
patterns (bbox sides `2..5`, five to ten occupied cells); it does not claim that
large dense crops are pedagogically equivalent to the canonical task.
## Current reviewer considerations

Source SHA-256: `f55ef20f6783321f1ac6162c01d67a41727d981247d9cc6144a6e5235d07c68b`.

# Decisions: d5d9fdb01bdd

## D1 — Keep the Racket authority unchanged

**Observation.** The baseline `rule_smoke` and authority checks passed, and the
canonical program is exactly “crop all nonzero content, then transpose.” The
failure was the input distribution and contract, not the rule.

**Decision.** Keep the canonical/Racket source byte-for-byte unchanged, pin
`RULE_HASH = "1b9c6046c883"`, and supply a pure Python `rule_mirror` only for
tests and semantic probes.

**Alternative rejected.** Changing the authority to match the old dense
rectangles would have rewritten the task rather than repaired its generator.

**Probe.** Four canonical inputs are accepted and the Python mirror matches all
four canonical outputs; shared Racket `rule_smoke`, `racket_lint`, and
`authority_sync` pass.

## D2 — Replace dense rectangles with sparse path-like content

**Baseline rationale.** No retained note explained why `2.0.0` forced all four
bbox corners, four colors, and roughly 50% rectangular fill; original rationale
is therefore **unknown**. Those choices contradicted every canonical example.

**Decision.** Use small sparse templates with internal zeros, one-cell outer
padding, variable placement, and one to three nonzero colors. Canonical anchors
use a 4×3 six-cell path matching the demonstrated morphology. Generalized
witnesses use 3×4 or 4×5 sparse shapes.

**Bounds.** Canvas `5..11 × 6..12`; tight bbox sides `2..5`; occupied cells
`5..10`; nonzero colors `1..3`.

**Alternatives rejected.** Random Bernoulli fill retained the same dense-object
shortcut and produced unstable component counts. Arbitrary polyomino growth was
more general but made exact color and semantic-witness guarantees harder to
inspect. Small named templates keep the lesson auditable while flips, placement,
palette, dimensions, and difficulty draws supply diversity.

**Failure modes.** Template families can overfit shape identity. The rule does
not depend on template identity, and the output/canvas/palette variation plus
wide/disconnected counterexamples reduce that risk, but finite templates remain
a documented limit.

## D3 — Expose only exact, observable controls

**Decision.** Public axes are:

- `grid_h`: integer `5..11`;
- `grid_w`: integer `6..12`;
- `n_distinct_colors`: integer `1..3`.

Unknown keys and invalid difficulties fail loudly. All boundary cross-products
are constructive; no incompatibility declarations are needed.

**Alternative rejected.** The baseline exposed position/density/texture-style
controls that were dead, silently narrowed by band, or not recoverable from an
output. Keeping them would preserve a misleading API.

**Probe.** The focused regression checks every low/high cross-product in all
three bands. The shared override stage exercised 9,990 accepted draws and 111
cases with zero failures. The retained lesson probe independently checks 24
joint boundary cases.

## D4 — Make canonical support explicit but not exclusive

**Decision.** `strict_canonical_like` recognizes the four canonical outer-size
profiles, canonical crop dimensions `(3,3)`, `(4,2)`, `(4,3)`, five/six occupied
cells, and one/two nonzero colors. One of every three scheduled samples is a
canonical-scale anchor, yielding a measured strict fraction around one third.

**Alternative rejected.** Sampling only exact canonical profiles would pass
coverage while teaching no orientation generalization. Sampling almost no
canonical examples would repeat the baseline profile-floor failure.

**Probe.** Shared profile floor measured 27/60 exact-profile and 35/60 envelope
hits; semantic gate measured 197/600 strict samples (32.8%).

## D5 — Teach against the strongest plausible rivals

**Canonical shortcut.** Every canonical tight crop has `height >= width`, so a
solver can fit all four demonstrations by transposing only tall/square crops and
leaving wide crops unchanged.

**Second rival.** A solver can process only the largest connected component;
this fits three of four canonical pairs and is a natural object-centric shortcut.

**Decision.** Declare both as executable rivals and pair them with executable
witnesses:

- wide crop that must still be transposed;
- disconnected content whose complete union must be cropped/transposed.

**Probe.** `checks/shortcut/counterexample.json` records a Racket-checked exact
wide witness. Shared semantic gate verified 60/60 rival claims per rival, and the
300-lesson census refuted every declared rival in every lesson.

## D6 — Redundant schedule instead of one witness per role

**Rejected draft.** The first repair schedule was `tall connected`, `square
disconnected`, `wide connected`. It passed fixed three-demo windows, but the new
query-rotation regression failed: when the disconnected example became the
query, `largest_component_only` fit every remaining demonstration.

**Decision.** Use `canonical_anchor`, `wide_disconnected_a`, and
`wide_disconnected_b`. Two of every three examples independently refute both
rivals. Any three examples selected from four consecutive samples still contain
a wide/disconnected witness.

**Evidence.** The failure is preserved in
`checks/red-query-rotation-test.log`; the repaired result is in
`checks/green-query-rotation-test.log`. The retained probe checked 1,200 query
rotations across 300 4-example windows with zero failures.

## D7 — Retain a source-bound reviewer tool

**Decision.** Add `workspace/lesson_probe.py` and its regression test. It reads
rivals/witnesses from the selected generator rather than copying a name list,
hashes the imported source, tests consecutive cyclic starts and every query
rotation, checks exact joint overrides, and emits first concrete
counterexamples.

**Why not rely only on shared census.** The shared census correctly documents
that it does not rotate every pair into the query position. Witness frequency
alone did not catch the failed draft schedule.

**Limits.** The probe checks declared rivals plus exact axis boundaries. It does
not enumerate all possible human shortcuts or establish universal induction.
Global duplicates across independent lessons are reported; an 85% minimum
unique-input fraction is required rather than falsely demanding collision-free
random sampling.
