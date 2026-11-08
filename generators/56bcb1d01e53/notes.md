# Working notes: `56bcb1d01e53`

## Current rule model

The selected authority first obtains 8-connected foreground components and
repeatedly joins pairs separated by one cardinal background cell. Each resulting
monochrome cluster is completed from its bounds:

- square bounds use quarter-turn rotational closure, including half-integer
  centers for even squares;
- rectangular bounds use horizontal/vertical reflection in an odd box centered
  at the rounded cluster center;
- supported odd squares fill their center under either the cardinal-support
  branch or the authority's larger diagonal-plus-midpoint branch.

The authority remains the canonical Racket rule pinned by
`RULE_HASH = a66a93e7a5d4`; no canonical data or Racket rule changed.

## Review lead and independently reproduced defects

The retained audit
`counterexamples/review-15a8b14353eb3e0a-v0001/retained/checks/audit/56bcb1d01e53/`
was used only as a lead. This review reproduced the relevant behavior against
source `7c7978cf0cd1f1f3842837e34539120bfb5c65a880b21053c1da05485437612d`
and found three source-bound gaps plus one validator defect:

1. No generated example exercised the 7x7 diagonal center-support branch, so a
   `cardinal_center_only` rival survived.
2. Generated square icons did not distinguish quarter-turn closure from full D4
   closure, so a `square_dihedral_closure` rival survived all canonical pairs.
3. The validator and Python mirror accepted modal background 0 even though the
   Racket prelude's `mode` ignores literal zero; that is a semantic domain
   mismatch, not merely an object-extraction sentinel collision.
4. `generate` coerced non-integral and negative `sample_index` values instead of
   failing closed. The baseline defect-lint stage emitted 33 strict-scalar
   warnings.

## Canonical repair — version 3.1.0

The two-slot schedule remains intact:

1. `canonical_core` cycles through all five canonical dimension/palette
   signatures.
2. `teaching_mix` now contains four icons that jointly exercise six branches:
   bridge merge, rectangular expansion, even-square completion, cardinal center
   fill, diagonal center fill, and rotation rather than full D4 closure.

The new `diag7_chiral` icon is a lawful 7x7 chiral square formed from two raw
8-components joined by one cardinal bridge. The canonical output fills its
center through diagonal support but does not paint four reflection-only cells.
It therefore supplies executable counterexamples to both
`cardinal_center_only` and `square_dihedral_closure` without changing the
canonical authority or the lesson size.

Six executable witnesses are paired with six rivals:

- `bridge_merge` -> `no_bridge_merge`
- `rectangular_expansion` -> `square_rotation_only`
- `even_square` -> `odd_squares_only`
- `center_completion` -> `no_center_fill`
- `diagonal_center_completion` -> `cardinal_center_only`
- `rotation_not_dihedral` -> `square_dihedral_closure`

`seed` is now required to be a real Python integer. `sample_index` is required
to be a real nonnegative Python integer. Modal background 0 is rejected by the
public mirror and validator with an explanation matching the Racket `mode`
semantics. The sole exact public override remains observable
`background=1..9`.

## Proposed parametric extension

`workspace/parametric/prototype.py` is a separate authoring prototype, not part
of production generation or approval. It chooses one episode-level parameter:

- `square_closure = "rotation"` (default, exact canonical Racket program)
- `square_closure = "dihedral"` (nearby full-D4 square variant)

The parameter is fixed across two demonstrations and one query. All labels are
produced by the protected Racket bridge. Public episode files omit the hidden
mode and query answers; evaluator-only files retain them. Materialized seeds 0
and 1 each leave exactly the selected mode after the demonstrations. This is
bounded evidence over one isolated chiral-square family, not universal support
for parametric production.

## Final-source measurements

Final generator SHA-256:
`ba299a70b42692962aaf335beca33f9609875fc7287a50c1bdaa6004164c8a0a`.

- Portable task-local tests: 92 passed.
- After battery: 11/12 stages green. The only red stage is the shared semantic
  gate's `declared_period_not_enumerated` follow-up condition; every substantive
  in-gate check passed (311/600 strict-profile hits, 5/5 canonical inputs,
  6/6 witnesses, 6/6 rival claims, 12/12 lessons, 0/48 diagnostic rotation
  ambiguities).
- Required fixed-seed schedule census: 6/6 residue/band lessons and 24/24 query
  rotations identifiable, zero errors or ambiguities.
- Expanded production census, split by band to avoid a monolithic shell cap:
  300/300 lessons, 1,200 unique inputs, and 1,200/1,200 required query rotations;
  all six rivals were refuted in every lesson and no materialization or scoring
  error occurred.
- Racket authority/parity, defect lint, distribution, profile floor, overrides,
  grammar, Racket lint, and authority synchronization all passed on final source.
- Parametric evidence: two complete Racket-derived episodes, canonical default
  unchanged, and focused prototype tests included in the 92-test total.

## Limits

The production sampler still uses a finite template family, one distinct color
per logical icon, three demonstrations plus one query, and six declared rivals.
The finite census does not prove unique induction against undeclared hypotheses,
all seeds, same-color separated icons, or every authority-lawful geometry. The
D4 variant remains proposed only; it is not selected, approved, or admitted for
training by this return.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-15a8b14353eb3e0a:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `7c7978cf0cd1f1f3842837e34539120bfb5c65a880b21053c1da05485437612d`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

All three parts addressed on accepted source ba299a70b42692962aaf335beca33f9609875fc7287a50c1bdaa6004164c8a0a based on reviewer-reported repair evidence from review-b1567e168170bc61:v0001: the chiral 7x7 template teaches diagonal-supported centers and rotation versus D4 closure, both executable rivals/witnesses are declared, and validator/mirror/observer consistently reject the already excluded zero background. Tests and independent probe are generators/56bcb1d01e53/tests/test_generator.py and generators/56bcb1d01e53/workspace/reference_probe.py. The returned 92-test pass, six fixed-seed lessons/24 rotations and 300 band-split lessons/1200 rotations support the repaired scope. No owner rerun; the 11/12 unbound aggregate remains separate and does not close unrelated findings.

### Assessment or prior finding

## 56bcb1d01e53

Evidence directory: `checks/audit/56bcb1d01e53/`.

Assigned and observed generator SHA-256: `7c7978cf0cd1f1f3842837e34539120bfb5c65a880b21053c1da05485437612d`.
Selected Racket rule: `a66a93e7a5d4`. Audit target source was not changed. These are three unresolved P2 findings. They do not identify a wrong label in the generator's current nonzero-background emitted inputs; they limit its teaching coverage and validator guarantees.

### A1 — No generated input teaches the canonical diagonal-center branch (P2)

The five templates in `generator.py` at `_TEMPLATES` (line 104) generate logical boxes of 4×5, 5×4, 5×5, or 6×6. Packing keeps them separate. The 7×7 diagonal-support center branch in `_apply_rule` (line 280) therefore has zero generated support. Matching the canonical 22×22 canvas and five-color profile does not recover this semantic coverage.

A concrete rival preserves bridge grouping, square rotation, rectangular reflection, and cardinal-supported center filling, but omits diagonal-supported center filling. It matches all 40 sampled production inputs (ten schedule positions in each of four difficulty bands) and every pair of the retained seed-11 four-pair lesson. All four held-out rotations pass the existing lesson hook while this rival survives.

This is a canonical failure, not only an extrapolation to a larger invented shape. Canonical test pair index 1 contains four 7×7 icons. Actual selected-rule Racket execution paints color 6 at zero-based row 5, column 14; the rival leaves background 8. All five stored canonical labels were independently confirmed against Racket in this audit.

Evidence: `checks/audit/56bcb1d01e53/audit_probe.py`, `checks/audit/56bcb1d01e53/audit-evidence.json` (`canonical`, `production_census`, `rotations`), and `checks/audit/56bcb1d01e53/audit-probe.command.json`.

Recommended repair: introduce a diagonal-supported 7×7 center witness and an explicit `cardinal_center_only` rival. Preserve the existing query-rotation guarantee against the expanded rival set. Extend the canonical-support observable to distinguish this branch from dimension/palette similarity.

### A2 — Full reflection symmetry remains indistinguishable from square rotation (P2)

The natural `square_dihedral_closure` rival adds horizontal, vertical, and diagonal reflections to each square's quarter-turn rotation partners. It keeps the bridge, rectangle, and center branches intact. It fits all five canonical labels and all 160 template/orientation/origin-parity cases (five templates × eight dihedral orientations × four origin parities).

This agreement covers the emitted square templates by construction: their completed shapes are already reflection-symmetric. The rectangular branch is unchanged, and packing separation plus unique icon colors prevents cross-icon interactions. Thus further seeds from this source do not distinguish the two rules.

A 7×7 input with a chiral 5×5 icon at origin (1,1) is accepted by `self_check`. The canonical Racket program adds only cell (2,5), changing background 1 to color 2. The executed D4 rival also adds (1,4), (2,1), (4,5), and (5,2). The Python rival and executed Racket rival agree exactly on this witness. Both complete programs and all inputs/outputs are retained.

Evidence: `checks/audit/56bcb1d01e53/child_d4_probe.py`, `checks/audit/56bcb1d01e53/child-d4-evidence.json` (160 checks and all five canonical fits), `checks/audit/56bcb1d01e53/minimal_witness_probe.py`, `checks/audit/56bcb1d01e53/minimal-witness-evidence.json` (`d4_witness`), `checks/audit/56bcb1d01e53/canonical-rule.rkt`, `checks/audit/56bcb1d01e53/rival-d4-rule.rkt`, and `checks/audit/56bcb1d01e53/minimal-witness-probe.command.json`. The child performed only Python checks; the separate minimal-witness receipt records the subsequent real Racket execution explicitly.

Recommended repair: include a chiral square witness in the normal teaching schedule and declare the D4 rival. Retain the witness even though both rules fit the original demonstrations: its purpose is precisely to distinguish their lawful extensions.

### A3 — Validator admits a background it explicitly excludes from generation (P2)

`generate` rejects `background=0`, but `_grid_facts` / `self_check` (line 475 onward) accepts a zero strict-majority background. `observe_overrides` returns `{"background": 0}` for such an accepted grid, and `rule_mirror` silently returns an answer that disagrees with the selected Racket rule.

The minimal 7×7 witness is the A2 input with background changed from 1 to 0. `self_check` returns `[]`. The selected Racket output and Python mirror differ at five cells: (1,2), (2,5), (3,3), (4,1), and (5,4). A second current-production mutation, seed 17 / index 1 / background 4 with colors 0 and 4 swapped, is also accepted and differs at 38 cells on its 18×22 canvas.

The existing generator comments and notes attribute the restriction to the object-extraction sentinel. The first semantic divergence is actually earlier: the runtime prelude's `mode(g)` excludes literal color 0 by default (definition at line 107). The Python `_background` includes it. The Racket rule's object extractor receives an explicit binary foreground mask, so the supplied sentinel explanation does not describe this cause accurately.

Evidence: `checks/audit/56bcb1d01e53/minimal-witness-evidence.json` (`zero_witness`), `checks/audit/56bcb1d01e53/audit-evidence.json` (`zero_background_witness`), the selected canonical rule, and `shared/runtime/arc_repl/racket_prelude/arc-prelude.rkt`.

Recommended repair: make the validator enforce the declared nonzero-background domain, and have the public mirror reject inputs outside that domain or implement the actual Racket background semantics. Correct the explanatory comments. This finding does not imply current default generation emits zero-background inputs.

### Execution and limits

This audit executed 12 applications of the selected Racket rule: five canonical pairs, four production pairs, the larger zero-background mutation, and two minimal witnesses. One additional Racket application executed the explicitly separate D4 rival. Forty generated inputs were checked in Python; the template rival probe checked 160 cases. No full audit battery or runtime sweep was run. The retained public production challenge contains only training input/output pairs and an unlabeled test input.

Run from `WORK`, using its independent environment:

```sh
.venv/bin/python run_with_racket.py /absolute/path/to/WORK/.venv/bin/python ../checks/audit/56bcb1d01e53/audit_probe.py
.venv/bin/python run_with_racket.py /absolute/path/to/WORK/.venv/bin/python ../checks/audit/56bcb1d01e53/minimal_witness_probe.py
```

The exact executed interpreter, arguments, working directory, exit code, and log hash are in the two command receipts. Both commands exited zero; their assertions confirm the reported findings and source identity. `checks/audit/56bcb1d01e53/verification.json` binds the final evidence files and checks the public projection.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-15a8b14353eb3e0a-v0001/audit_assets.json), manifest SHA-256 `c112143791d480986d1a29d083131a89448cde5fa991df4193566ea0437ffb8a`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `ba299a70b42692962aaf335beca33f9609875fc7287a50c1bdaa6004164c8a0a`.

# Decisions

## D1 — Preserve the canonical Racket authority

**Choice.** Keep the selected Racket program and `RULE_HASH = a66a93e7a5d4`
unchanged. Repair the generator's input curriculum, mirrors, validators, rivals,
and tests instead.

**Rationale.** The reproduced failures were missing teaching witnesses and a
Python-side domain mismatch, not wrong canonical labels. All five canonical
examples were accepted, and the authority/rule-smoke stages were green before
and after.

**Alternatives rejected.** Expanding the Racket rule to full D4 closure would
silently redefine the task. Editing canonical rows to fit the Python mirror
would invert authority. Both were rejected.

**Probe/evidence.** `checks/before/checks/56bcb1d01e53_before_rule_smoke.json`,
`checks/after/checks/56bcb1d01e53_after_rule_smoke.json`, and the unchanged rule hash in the portable
runtime manifest.

**Failure mode/limit.** An undiscovered authority bug would not be repaired by
this choice; current evidence only establishes consistency with the pinned rule.

## D2 — Use one chiral 7x7 witness to close two semantic gaps

**Choice.** Add `_DIAGONAL7_CHIRAL` to `teaching_mix`. Its geometry creates a
bridge-joined logical icon, diagonal-only center support, and a visible difference
between quarter-turn and full-dihedral closure.

**Rationale.** The baseline generated no diagonal-center witness and no chiral
square. Consequently `cardinal_center_only` and `square_dihedral_closure` could
survive. A single lawful icon supplies both missing distinctions without changing
the canonical rule or growing the demonstration count.

**Alternatives considered.** Separate diagonal and chirality templates would be
more redundant but would consume more schedule capacity. Randomly searching for
rare witnesses would make coverage probabilistic. A fixed compact teaching icon
was chosen because its witness status is executable and deterministic.

**Probe/evidence.** Focused tests in `tests/test_generator.py`, independent logic
in `workspace/reference_probe.py`, and six witness/rival records in
`checks/after/checks/56bcb1d01e53_after_semantic_gate.json`.

**Failure mode/limit.** Repeating one chiral form can itself become a cue. The
canonical-core half of the schedule and broad censuses mitigate but do not prove
absence of such a shortcut.

## D3 — Keep the two-slot, three-demo curriculum

**Choice.** Preserve `LESSON_SCHEDULE_PERIOD = 2`, alternating `canonical_core`
and `teaching_mix`, with three demonstrations and one query. Expand the teaching
contract from four to six rivals rather than increasing lesson length.

**Rationale.** The existing interface and downstream data assumptions stay stable.
The repaired teaching bundle refutes all six declared rivals for every required
query placement in the retained censuses.

**Alternatives rejected.** Adding demonstrations would increase token cost for
Qwen3.5-9B and alter the established lesson contract. Using only teaching_mix
would narrow canonical profile support. Random witness selection could create
unidentifiable windows.

**Probe/evidence.** `checks/schedule-period-s0.summary.json` exhausts the declared
fixed-seed period; the three `lesson-census-*.summary.json` files cover 300 wider
production lessons and 1,200 query placements.

**Failure mode/limit.** The fixed-seed period census does not exhaust all seeds,
and the larger random census does not prove all possible schedule windows.

## D4 — Fail closed on call scalars

**Choice.** Require `type(seed) is int`; require `type(sample_index) is int` and
`sample_index >= 0`. Do not coerce with `int(...)`.

**Rationale.** The baseline accepted booleans, floats, strings, and negative
indices, yielding 33 strict-scalar warnings across difficulty contexts. Silent
coercion creates accidental collisions and makes replay metadata dishonest.

**Alternatives rejected.** Accepting `numbers.Integral` would still admit booleans
unless special-cased. Coercion was rejected because `1.75 -> 1` and string parsing
hide invalid caller behavior.

**Probe/evidence.** `checks/before/checks/56bcb1d01e53_before_defect_lint.log`,
new parameterized regressions, and green final defect lint.

**Failure mode/limit.** NumPy integer scalars are intentionally rejected by this
strict public contract; callers must convert explicitly.

## D5 — Exclude literal-zero backgrounds for the correct reason

**Choice.** Keep the observable background axis at `1..9` and reject a modal
background of 0 in `self_check`, `rule_mirror`, and override observation.

**Rationale.** The Racket prelude's `mode` ignores literal zero, so Python's
ordinary `Counter.most_common` background can disagree with authority. The old
explanation that zero was merely an object-extraction sentinel was incomplete.

**Alternatives rejected.** Reimplementing Racket `mode` in the generator would
make some zero-heavy grids use a different nonzero background but would expand the
public domain beyond tested canonical assumptions. Changing the Racket prelude is
outside task-local scope.

**Probe/evidence.** The focused zero-background witness in
`tests/test_generator.py` and corrected task notes.

**Failure mode/limit.** This intentionally excludes potentially meaningful
zero-background variants; they would require a separately specified authority.

## D6 — Parameterize square closure only in a separate prototype

**Choice.** Add proposed parameter `square_closure={rotation,dihedral}`, default
`rotation`, under `workspace/parametric/`. Choose it once per episode; execute
both exact programs through protected Racket. Do not route production `generate`
through the prototype.

**Rationale.** Rotation versus full D4 is a nearby, meaningful rule change that
preserves object extraction, bounds, closure reasoning, and center completion.
The chiral witness makes the modes distinguishable. The default program is
byte-identical to canonical.

**Alternatives rejected.** Varying output color, canvas size, or template weights
would be cosmetic rather than a rule parameter. Parameterizing bridge distance
would entangle object identity and require a broader redesign.

**Probe/evidence.** `checks/parametric/square-closure/manifest.json`, two exact
Racket files, two public/private episodes, and focused tests in
`tests/test_parametric.py`.

**Failure mode/limit.** Evidence covers seeds 0 and 1 and one isolated square
family, not all seeds or the full production curriculum. The variant remains
unapproved.

## D7 — Require query-rotation identifiability in the retained census

**Choice.** Treat all legal query placements as required for the selected task's
retained schedule and wider census, even though the semantic smoke labels them
diagnostic by default.

**Rationale.** A correct per-grid label is insufficient if a plausible rival fits
all demonstrations and differs on the held-out query. The audit of
`0ae0d5780419` independently reproduced exactly this failure: 12/12 ordinary
lessons passed but 27/60 alternate placements were ambiguous.

**Alternatives considered.** Fixing query order and documenting it can be valid
for intentionally ordered curricula. Here every placement passed cheaply, so the
stronger contract was retained.

**Probe/evidence.** 24/24 fixed-period and 1,200/1,200 expanded query placements.

**Failure mode/limit.** Requiring rotations globally would false-positive on a
curriculum whose ordering itself carries an intentional teaching role; this is why
the recommendation in `QUESTION_ANSWER.md` is conditional on legal export policy.

## D8 — Split the large census by band and retain full reports losslessly

**Choice.** After two monolithic 300-lesson invocations exceeded the surrounding
shell execution cap, run unchanged 100-lesson censuses separately for easy,
medium, and hard. Compress the three full JSON reports deterministically for the
return budget while retaining direct summaries and logs.

**Rationale.** Splitting changes neither source nor per-band seed recipe and yields
complete source-bound evidence instead of discarding a long run. Gzip is lossless,
and original sizes/hashes/restoration commands are recorded.

**Alternatives rejected.** Reporting only the partial monolithic attempts would
not establish the requested coverage. Deleting the full reports would remove exact
instances. Increasing the outer shell cap was not reliable in this environment.

**Probe/evidence.** `checks/lesson-census-final*.log`, three band summaries, and
`checks/evidence-compression-manifest.json`.

**Failure mode/limit.** The three reports are separate rather than one atomic
controller receipt; their source hashes and identical settings must be checked
together.

## D9 — Treat the aggregate semantic warning as a tooling reconciliation issue

**Choice.** Report the final battery honestly as 11/12 with exit 1, then satisfy
the prescribed schedule obligation with a new exact census instead of suppressing
the warning or modifying shared code.

**Rationale.** The warning says only that the aggregate command did not enumerate
the declared period. The follow-up did enumerate it with zero ambiguity/errors.
Conflating those facts would either hide a red command or mislabel valid source as
semantically broken.

**Alternative rejected.** Removing `LESSON_SCHEDULE_PERIOD` to make the warning
disappear would destroy useful metadata. Editing the shared runner was outside the
allowed patch scope.

**Probe/evidence.** Compare `checks/after/checks/56bcb1d01e53_after_battery_summary.json` with
`checks/schedule-period-s0.summary.json`. Shared improvement is F1.

## D10 — Keep audits findings-only

**Choice.** Do not edit `0ae0d5780419` or `af9ade3c3e16`; retain source-bound
findings under their exact headings in `AUDIT.md`.

**Rationale.** The assignment requested adversarial reviews, not repairs, and the
patch scope permits only the selected task.

**Failure mode/limit.** Both audit findings remain open until their owners repair
and reverify them.
