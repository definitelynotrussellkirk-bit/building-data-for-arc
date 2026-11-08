# Current account: 2b83f40cf6d9

## Intended rule and authority

`RULE_HASH = cbbc66a297e5` is pinned to the selected canonical Racket authority.
For every nonzero color that appears exactly twice, colors are processed by
first row-major appearance. Starting at the first marker, move one row toward
the second marker and then one column toward it, painting each visited cell;
repeat until the second marker is reached. Aligned pairs therefore become
straight segments. This review changed no Racket or canonical data.

## Ordinary input contract

Version `2.0.0` generates rectangular `7..18` by `8..20` grids with background
0, two or three distinct nonzero colors, exactly two isolated marker cells per
color, and no 4-adjacent markers. The only advertised exact axes are `grid_h`,
`grid_w`, and `n_colors`; unknown, non-integer, and out-of-range overrides reject
rather than being ignored. Pair placement is constructive with backtracking, so
all declared boundary combinations are supported.

Difficulty bands weight different parts of the full declared ranges but do not
narrow them. With no overrides, every third sample is anchored to one of the
five exact canonical shape/palette profiles. Axis values are still drawn through
keyed context calls, preserving provenance. The anchor period is 3 rather than 4
so it is not phase-locked to the semantic layout schedule.

## Teaching contract

The five canonical demonstrations contain only diagonal pairs, so the strongest
retained canonical-fitting rival is `diagonal_pairs_only`: apply the intended
rule to diagonal pairs but leave row- or column-aligned pairs unconnected. The
four-position layout schedule is
`diagonal, one_aligned, diagonal, all_aligned`. Lessons use three demonstrations
and one query; every four-sample window and every query rotation contains an
aligned demonstration that refutes the rival. The aligned counterexample is in
`counterexamples/current-aligned-rival/`.

## Validation and evidence

`self_check` validates shape, dimensions, ARC integer colors, the exact 2–3 color
multiplicity contract, and marker isolation. The task-local tests bind the rule
hash and canonical oracle, prove the canonical rival fit, exercise override
boundaries and invalid controls, reproduce the former one-color validator bug,
and check profile support, keyed provenance, schedule rotations, and joint
support between the profile and semantic schedules.

Final source SHA-256:
`4ca15e7a48171953ca72ee9527dfcba7d62624a33ed71bbf9ce90085008586d6`.
The final battery is 12/12 green and the focused suite is 38/38 passing. Wider
finite checks found no ambiguity against the declared rival in 300 production
lessons, 1,200 query rotations, or all 48 rotations of the four schedule starts
at seed 0.

## Known limits

The semantic evidence is finite and covers the declared canonical-fitting rival;
it is not a proof of unique induction against every conceivable rule. The fixed
schedule enumeration uses one seed, while the larger random census samples but
does not exhaust all seeds. Inputs outside the ordinary 2–3-pair isolated-marker
domain are rejected or unspecified rather than generalized.

## Current scoped audit assessment

See `evidence/current-audit-assessment.json` for explicit source-bound dispositions. These are finite reviewer-reported checks; no owner rerun or universal qualification.
## Current reviewer considerations

Source SHA-256: `4ca15e7a48171953ca72ee9527dfcba7d62624a33ed71bbf9ce90085008586d6`.

# Decisions for `2b83f40cf6d9`

Final generator SHA-256:
`4ca15e7a48171953ca72ee9527dfcba7d62624a33ed71bbf9ce90085008586d6`.
The original rationale for most imported version `1.2.1` choices was not present
in its concise notes, so those rationales are recorded as unknown rather than
reconstructed.

## D1 — Keep the canonical rule unchanged and pin it

**Prior choice/rationale:** The generator depended on the selected Racket rule but
did not declare `RULE_HASH`; the rationale for omitting the binding is unknown.

**New choice:** Keep the authority bytes unchanged and declare
`RULE_HASH = "cbbc66a297e5"`. Add an independent Python oracle used only by tests and
semantic hooks.

**Alternatives rejected:** Rewriting the Racket rule, changing path ordering, or
normalizing aligned pairs away. None was justified: all five canonical outputs
already match the selected authority, and rule-smoke/authority-sync were green.

**Probe/evidence:** The focused test applies the Python oracle to all five
canonical pairs and checks exact outputs. Final `rule_smoke`, `racket_lint`, and
`authority_sync` are green in `checks/after-final-source/`.

**Failure mode/limit:** The Python oracle is a mirror, not a replacement authority;
its agreement is tested on canonical pairs and generated semantic witnesses.

## D2 — Declare only observable exact axes

**Prior choice/rationale:** The imported generator advertised dimensions, number
of pairs/colors, and texture-like controls, but several were not consumed or were
silently bypassed. Difficulty bands changed the legal dimension range, and
unknown keys were swallowed. The original rationale is unknown.

**New choice:** Advertise only `grid_h=7..18`, `grid_w=8..20`, and
`n_colors=2..3`. Validate keys, exact integer type (excluding booleans), and full
bounds before generation. Difficulty affects weights only; it never changes the
contract. Every explicit axis value is routed through the generation context and
verified afterward with `observe_overrides`.

**Alternatives rejected:**

- Retain `texture` or similar nominal axes: no independent, stable observable was
  defined, so keeping them would preserve a fake control.
- Declare many incompatibilities: constructive placement makes every Cartesian
  boundary combination feasible, so incompatibilities would hide rather than
  solve the defect.
- Clamp or ignore invalid values: this makes experiments non-replayable and was
  the reproduced baseline failure.

**Probe/evidence:** Boundary combinations are parametrized across no difficulty
and all three named bands. The final override checker ran 21,240/21,240 draws with
zero finding/warning and rejected its unknown-key probe.

**Failure mode/limit:** The declared axes describe ordinary inputs, not arbitrary
hand-authored grids outside the validator domain.

## D3 — Enforce the ordinary 2–3-color domain in `self_check`

**Prior choice/rationale:** The imported validator mainly checked pair counts and
accepted a grid containing only one color twice. This contradicted the summary;
the rationale is unknown.

**New choice:** Validate nonempty rectangular shape, dimensions, exact ARC integer
cells 0..9, two or three nonzero colors, exactly two cells per color, and no
4-adjacent marker cells. Return diagnostics rather than raising on malformed
inputs.

**Alternatives rejected:** Treat one-color cases as a hidden extended domain or
weaken the summary to match. Canonical examples and the imported description both
state 2–3 colors, and a weaker domain would dilute lesson semantics without any
canonical support.

**Probe/evidence:** `checks/task-tests-red2/` records the reproduced one-color
failure before the fix. Final focused tests cover one color, adjacent markers,
booleans, ragged rows, and `None`; final semantic gate reports 600/600 strict hits.

**Failure mode/limit:** The validator intentionally rejects possible generalized
variants, such as one or four colors, rather than claiming the rule cannot be
mathematically applied to them.

## D4 — Use constructive backtracking for isolated marker pairs

**Prior choice/rationale:** Several baseline branches generated special textures
or degenerate cases that could bypass requested dimensions. The rationale for
those branches is unknown.

**New choice:** Build each pair from cached aligned/diagonal candidate lists and
use complete backtracking under a 4-neighbor blocked set. This directly realizes
the requested grid and color count while preserving marker isolation.

**Alternatives rejected:** Unbounded random retry, post-hoc deletion, or special
small-grid branches. Those approaches can become seed-dependent, obscure exact
controls, or recreate endpoint overwrite defects like audit A1.

**Probe/evidence:** All declared corners (7×8 through 18×20, 2 or 3 colors) pass
in every band. The default-distribution test checks deterministic replay and both
color counts over 96 samples per band setting.

**Failure mode/limit:** Candidate enumeration is cached and acceptable at current
small ranges; materially larger grids or many more pairs would require a more
scalable placement strategy.

## D5 — Weight the full domain and anchor canonical support

**Prior choice/rationale:** Difficulty-specific draws favored certain sizes but
also narrowed exact override bounds. After the first repair, random weighting
alone produced no exact canonical profile in medium or hard during the pinned
20-draw census. The original intended distribution rationale is unknown.

**New choice:** Keep the full range legal in every band, use difficulty-specific
weights for ordinary draws, and—only when no override is supplied—anchor every
third sample to one of the five exact canonical `(height, width, n_colors)`
profiles. Axis draws remain named context choices for provenance.

**Alternatives rejected:**

- Rely on chance: source `026ab95f…` failed with exact support only 3/60 and none
  in medium/hard.
- Force all samples into the canonical envelope: this would unnecessarily shrink
  input diversity.
- Anchor every fourth sample: source `348ae0b7…` passed the battery but was
  phase-locked to the four-step semantic schedule, so canonical profiles only
  received diagonal layouts.
- Let explicit overrides participate in the anchor: this could override the
  caller and break exact-control provenance.

**Probe/evidence:** `checks/task-tests-red3/` and `red4/` record the missing support
and envelope-rate failures. `red5/` records the phase-lock failure. The final
period-3 anchor yields 23/60 exact and 24/60 envelope hits, exact support in every
band, named provenance, and all semantic residues in the joint-support test.

**Failure mode/limit:** A deterministic anchor is visible in sample-index
statistics. Period 3 was chosen to be coprime with the period-4 semantic schedule,
not to claim randomness.

## D6 — Teach the strongest canonical-fitting rival explicitly

**Prior choice/rationale:** The imported generator had no executable semantic
rival or lesson-identifiability contract. All five canonical pairs happen to have
both row and column displacement, so a solver could infer “ignore aligned pairs.”
No prior rationale for this omission was recorded.

**New choice:** Declare `diagonal_pairs_only` in `SEMANTIC_RIVALS`,
`LESSON_COMPETITORS`, and `CANONICAL_SHORTCUTS`; declare `aligned_pair` as its
witness. Use the layout schedule
`diagonal, one_aligned, diagonal, all_aligned`, with three demonstrations and one
query. `lesson_identifiable` validates labels and requires an aligned
counterexample among the demos.

**Alternatives rejected:**

- Random aligned-pair frequency alone: a nonzero global witness rate does not
  guarantee every complete lesson refutes the rival.
- Two demonstrations: a four-pair, three-demo window makes every held-out query
  rotation retain an aligned witness; fewer demos cannot guarantee that for this
  schedule.
- Put the witness only in queries: correct labels would still leave training
  demonstrations ambiguous.
- Invent many rivals: only the strongest source-supported plausible shortcut is
  declared; finite tests should not masquerade as universal induction.

**Probe/evidence:** The source-bound canonical test proves the rival fits 5/5
canonical pairs. The exact 7×8 counterexample is retained under
`counterexamples/current-aligned-rival/`. The final semantic gate found 298/600
aligned witnesses, 12/12 identifiable lessons, and 48/48 clean rotations. The
larger census found 0 ambiguity in 300 lessons and 1,200 rotations; fixed schedule
enumeration covered every start residue and 48 rotations at seed 0.

**Failure mode/limit:** These results cover declared rivals and tested transforms.
An undeclared hypothesis may still fit; this is documented as unknown.

## D7 — Preserve real failures and separate audit-only work

**Prior choice/rationale:** Not applicable; this is a review-process decision.

**Choice:** Retain all red focused-test runs and failed/interrupted batteries.
Keep A1 (`a74527c8b210`) and A2 (`4650a2421296`) as findings-only audits with
exact current-source reproducers and Racket outputs, and do not alter those tasks.

**Alternatives rejected:** Delete failed evidence after reaching green, or patch
unassigned targets. Either would make the reasoning unauditable or violate scope.

**Probe/evidence:** Failure directories are under `checks/task-tests-red*`,
`checks/after/`, and `checks/after-final/`; audit evidence is under
`checks/audit/<task>/`.

**Failure mode/limit:** Audit findings establish the exact reproduced cases, not
complete characterization of those generators.

## D8 — Stop after source-bound final checks and a fresh visible-only solve

**Choice:** Stop when the final source had 12/12 battery stages green, 38/38
focused tests, clean required rotations, clean large/fixed schedule censuses, an
exact Racket-checked rival counterexample, and a new solve episode bound to the
same hash. The post-repair solve declared earlier exposure `yes` and did not
consult references during solving.

**Reason:** Further changes would add unrequested behavior and risk weakening the
now-measured contract. The unresolved limitation—finite rival coverage—is
fundamental to the scope of the evidence, not a failing check that can honestly
be “fixed” by adding arbitrary hypotheses.
