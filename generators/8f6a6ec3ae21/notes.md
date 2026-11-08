# Working notes: 8f6a6ec3ae21

## 2026-10-04 review `review-3b5936d24ac678b2`

Baseline source hash:
`5ce16d39670288cd8ed38d2eef1ef59cd94024b1282983128713fa3ad68af857`.
No prior return was used as a lead.

The baseline battery completed with 7 green, 2 advisory, and 3 failed stages.
It lacked `RULE_HASH`, had dead/singleton axes and unlawful ordinary textures,
accepted unknown overrides, rejected values advertised as legal, and provided no
semantic contract. Easy had no canonical-profile hit in 20 samples.

The repair narrowed the API to six exact observable controls, made all 1,080
joint combinations constructive, added canonical dimension anchors, required
gapped selector sets, and inserted alternating wrong-role border decoys. The
decoys specifically refute `any_nonzero_axes`, which fits every canonical pair.
Four named rivals and four witnesses are executable; `lesson_identifiable`
checks complete demo/query bundles.

Test-driven record: the focused suite first produced 35 failures and 11 passes
against the baseline. After implementation and one schedule correction, all 46
passed. Final generator hash:
`a30551fabf7d39bc1056441e22e0a9153c2457be1f5d488d9307f5eee57e6475`.

Final evidence:

- after battery: 12/12 green;
- override gate: 18,090/18,090 accepted, zero findings;
- semantic gate: strict 600/600, four witnesses 600/600, 12/12 sampled lessons;
- profile gate: 16/60 exact, with support in every band;
- local probe: all 1,080 joint overrides plus 100 defaults per band;
- lesson census: 300 lessons, 900 rotations, zero ambiguities, 898 unique inputs;
- fresh exposed solve: first revision passed all three visible examples.

Known limit: the default sampler deliberately emits exactly one wrong-role decoy
per example. This makes every demonstration individually diagnostic but narrows
the default decoy-count distribution; exact overrides still cover zero and both.
Finite named-rival success is not a proof of universal rule identifiability.

Imported associated notes retain original evidence/timestamps in
`evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `a30551fabf7d39bc1056441e22e0a9153c2457be1f5d488d9307f5eee57e6475`.

# Decisions for `8f6a6ec3ae21`

## D1 — Preserve the canonical Racket authority

**Choice.** Keep the selected Racket rule unchanged and pin
`RULE_HASH = "ca6d5269f15c"` in the generator.

**Rationale.** Canonical input/output pairs and the baseline `rule_smoke` already
agreed with the intended row-selector × column-selector rule. The defect was in
sampling, contracts, and teaching support, not output semantics.

**Alternatives rejected.** Rewriting or “simplifying” the Racket would add an
unnecessary second change and risk authority drift. The final battery confirmed
execution parity without source edits.

**Evidence and limit.** `checks/after/checks/8f6a6ec3ae21_after_authority_sync.json`.
One archival raw-code source remains textually divergent, but execution parity
passed; it was not modified.

## D2 — Replace the imported axis list with six exact observable controls

**Choice.** Advertise only `grid_h`, `grid_w`, `n_marks_1`, `n_marks_2`,
`n_row_decoys`, and `n_col_decoys`.

**Original rationale.** Unknown. The imported baseline listed palette, density,
position, color-count, and texture axes, but several were singleton, ignored, or
not visible in the generated pixels.

**Rationale.** An axis is useful only when an override has an exact observable
effect. The six retained controls can be recovered from a grid by
`observe_overrides` and are independently checked.

**Alternatives rejected.** Keeping decorative metadata axes as “diagnostic” would
preserve a misleading public surface. Adding palette controls was rejected
because the canonical role colors 1 and 2 and output color 8 are part of this
specific task.

**Failure modes and tests.** Unknown names, bools/floats/strings, and out-of-range
values must fail loudly. All 1,080 legal joint combinations must construct.
Evidence: `checks/semantic-probe.json`, the override battery report, and focused
tests.

## D3 — Use dimensions 6–10 by 7–12 with canonical anchors

**Choice.** Legal dimensions are height 6–10 and width 7–12. Every third default
sample is scheduled onto one of the three canonical dimension/palette profiles;
other draws use the full domain with difficulty weighting.

**Rationale.** Height 6 is the smallest size that can hold four gapped row
selectors plus a disjoint left-border decoy; width 7 is the analogous minimum
for columns. The upper bounds broaden scale without creating large, mostly empty
boards. Canonical anchors prevent a band from drifting away from observed data.

**Alternatives rejected.** The baseline advertised smaller values that its easy
path rejected. A canonical-only sampler would overfit dimensions; a uniform-only
sampler did not guarantee per-band profile support.

**Measured result.** The profile gate found 16/60 exact hits: easy 6/20, medium
5/20, hard 5/20. The local 100-per-band probe found 48, 40, and 39 canonical
profile hits.

## D4 — Use 2–4 gapped selectors on each axis

**Choice.** Each correct marker set contains 2–4 coordinates and must contain at
least one gap.

**Rationale.** Two markers are the minimum useful Cartesian-product example.
Counts through four vary output cardinality while remaining constructive at the
minimum dimensions. Gaps make the `bounding_box_fill` shortcut disagree on every
default sample.

**Alternatives rejected.** One selector gives weak evidence for a product rule.
Contiguous-only sets make a filled rectangle observationally plausible. Counts
above four would force larger minimum boards or crowd optional decoys.

**Failure modes and tests.** `self_check` rejects too few/many or contiguous
selectors. The `gapped_axes` witness and `bounding_box_fill` rival are executable.

## D5 — Add role-swapped border decoys

**Choice.** Permit 0–1 color-1 decoys on the top border and 0–1 color-2 decoys on
the left border. In the default schedule, exactly one of the two is present and
its side alternates by sample index.

**Rationale.** All three canonical pairs are also solved by a shortcut that treats
any nonzero top-border mark as a selected column and any nonzero left-border mark
as a selected row. A wrong-role marker creates the cheapest lawful
counterexample: the official rule ignores it while the shortcut paints extra
cells. Alternating sides prevents a one-sided exception rule.

**Alternatives rejected.** Interior noise changes the canonical structural
contract and tests a different skill. Randomly omitting all decoys can assemble a
lesson that never refutes the canonical shortcut. Always placing decoys on only
one border invites a side-specific shortcut.

**Known restriction.** Exactly one decoy per default example is a teaching
schedule, not the full legal distribution. Exact overrides and the exhaustive
probe cover zero and two-decoy cases, but production defaults do not sample them.

## D6 — Clear all input markers in the output

**Choice.** The mirror and rivals explicitly model a blank output except for 8 at
correct intersections.

**Rationale.** This is required by canonical outputs and distinguishes the rule
from “copy input, then add intersections.”

**Alternative rejected.** Preserving input markers is a plausible but wrong
shortcut, represented by `preserve_markers` and the `clear_markers` witness.

## D7 — Require two demonstrations and make each individually instructive

**Choice.** Set `EXAMPLES_NEEDED = 2`, but ensure every default example refutes
all four named rivals.

**Rationale.** Two demos are enough for variation in decoy side, dimensions, and
marker counts. Making each example independently diagnostic makes lesson
assembly and query rotation robust rather than relying on a lucky pair.

**Alternatives rejected.** One demonstration gives less variation. Three or more
increase context cost without improving the measured declared-rival result. A
schedule where only one special sample carries the negative would be fragile
under query rotation.

**Measured result.** 300 materialized lessons and 900 held-out rotations had zero
declared-rival ambiguity; `checks/lesson-census.json` records seeds, starts,
outputs, and source hashes.

## D8 — Add executable semantics instead of prose-only claims

**Choice.** Implement `strict_canonical_like`, `rule_mirror`,
`observe_overrides`, four witnesses, four rivals, `CANONICAL_SHORTCUTS`, and
`lesson_identifiable`.

**Rationale.** These hooks let the battery and census falsify distribution and
teaching claims. The local probe iterates declarations rather than maintaining a
second hard-coded rival list.

**Alternatives rejected.** A comment saying the examples are “diverse” cannot
catch a dead axis or an ambiguity. Comparing only to canonical pairs misses a
shortcut that fits all canonical labels.

**Limits.** Named rivals are not an exhaustive program search. A pass means the
measured lessons reject those hypotheses, not that induction is unique in an
absolute sense.

## D9 — Test public behavior first

**Choice.** Add 46 portable regressions covering authority metadata, canonical
pairs, exact overrides, invalid inputs, deterministic distribution, semantic
negatives, lesson rotation, destructive mutations, malformed grids, and Python
hash-seed independence.

**Rationale.** The first test run against the baseline produced 35 failures and
11 passes, proving the tests exercised missing behavior. The final staged run
passed 46/46.

**Alternative rejected.** Depending only on the general battery would leave
selected task tests undiscovered and would not make the intended API examples
readable to future agents.
