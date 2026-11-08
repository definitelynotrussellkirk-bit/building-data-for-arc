# Working notes: e3f1bc75d654

## Current rule and authority

Version `5.1.0`; generator SHA-256
`357ce12d945153a3241aabac939c956e66e74dd8d6f29922d8f64c47135b7c0e`.
The background is 0. A lawful scene contains distinct, separated rectangular
frames, exactly one of which has a non-empty, non-solid pattern in its interior.
The selected rule identifies that patterned template, keeps every frame with the
same interior height and width, copies the template's relative pattern into each
kept frame using that frame's color, and erases differently sized frames.

The canonical Racket semantics were not changed. `RULE_HASH = "0ac13a729d1a"`
remains the whitespace-normalized authority hash. The two selected
`target_code` copies were synchronized byte-for-byte to canonical
`program_solution` (exact SHA-256
`cf706900d9a6aef99774a491fcb1ccc49f5b8c2b83ab77623967d993b8263d8d`);
archival `raw_code` remains untouched. Execution parity is retained across both
text forms.

## Input contract and distribution decisions

`seed` and `sample_index` must be exact Python integers (not Boolean, float, or
string), `sample_index` must be non-negative, and `difficulty` is only `None`,
`easy`, `medium`, or `hard`. Every declared integer/color override is also exact
integer-only. This reverses the v5.0.0 behavior that accepted 123 invalid scalar
probes through Python equality/coercion.

The complete canonical linked profiles remain a default-only prior. Even sample
indices are reserved for a generated witness in which the leftmost frame is a
size distractor. Odd indices sample the canonical prior at 60%, retaining a 30%
effective prior across the two-slot schedule. A lesson uses three demonstrations
and one query (`EXAMPLES_NEEDED = 3`, `LESSON_SCHEDULE_PERIOD = 2`); every four
consecutive pairs contain at least two leftmost-distractor witnesses, so holding
out any one pair leaves at least one witness in the demonstrations.

## Strongest measured rival and retained witness

The strongest simple canonical-fitting rival found is **use the leftmost frame's
interior dimensions instead of the patterned template's dimensions**. It fits all
8 usable canonical pairs. On the pre-repair sampler it disagreed with the intended
rule in 295/1000 easy, 314/1000 medium, and 373/1000 hard draws. The exact final
source-bound witness is
`counterexamples/leftmost-frame-shortcut.json` (`seed=1`, `sample_index=0`,
`difficulty=easy`); a focused test replays both predictions. Independent Racket
application is retained under
`checks/counterexamples/e3f1bc75d654-leftmost-frame-shortcut-racket.json`.

The fixed-seed exhaustive schedule receipt covers 6/6 starts across three bands
and 24/24 query rotations with zero ambiguity, hook warnings, or scoring errors.
The production census covers 300/300 lessons, 1200 pairs, and 1200/1200 query
rotations with zero ambiguity or errors and 1200 unique input grids. These are
finite checks against the declared rival, not a proof of universal induction.

## Parametric extension assessment

A proposed, isolated `pattern_orientation` parameter lives under
`workspace/parametric/`: canonical/default `identity` versus proposed
`horizontal_flip`. It preserves the original roles, frame-size selection,
receiver recoloring, and distractor erasure, while changing only the relative
pattern columns. The setting is chosen once per episode; retained asymmetric
inputs make the two settings distinguishable. Verification executed 16 Racket
calls over two four-pair episodes, and all 6 demonstrations separated the two
settings. This prototype is not wired into production generation, approval, or
training metadata.

## Known limits and open findings

The semantic contract names one practical rival plus generic census probes; it
does not enumerate every feature-conditioned hypothesis. Fixed-seed cyclic-start
coverage does not exhaust every seed or random support. The orientation variant
has only bounded prototype evidence and requires a separate maintainer decision.
The post-repair visible-only solve passed all three demonstrations but was
correctly marked as having earlier rule exposure; masked query labels remain
withheld for independent scoring.
## Current reviewer considerations

Source SHA-256: `357ce12d945153a3241aabac939c956e66e74dd8d6f29922d8f64c47135b7c0e`.

# Decisions for e3f1bc75d654

## Scope and evidence boundary

I used the selected packet source and reproduced before-check evidence as the
binding baseline. I did not use an earlier return as a source of truth; retained
associated notes were treated only as leads. The canonical Racket program stayed
the semantic authority throughout. All repairs are limited to the assigned task,
its selected base-solution copies, focused tests, counterexample, and isolated
parametric workspace.

## D1 — Develop one small rule parameter without changing canonical execution

**Choice.** Add a separate prototype parameter
`pattern_orientation ∈ {identity, horizontal_flip}`. `identity` is the exact
canonical default. `horizontal_flip` reflects only the template pattern's
relative interior columns; frame discovery, template selection, exact-size
receiver selection, per-frame recoloring, borders, and distractor erasure are
unchanged. The setting is selected once per episode.

**Rationale.** This is the smallest rule-level variation that preserves the
original family’s object roles and reasoning chain. It changes a meaningful
relational operation rather than a nuisance property such as palette or canvas
size. Retained inputs require an asymmetric pattern so demonstrations actually
distinguish the settings.

**Alternatives rejected.** Vertical/horizontal rotations that swap interior
height and width would entangle the parameter with frame compatibility and
change which receivers are lawful. Palette transformations are not rule
parameters. Randomly selecting an orientation per pair would make a lesson
internally inconsistent.

**Probe and result.** `workspace/parametric/verify.py` instantiated both Racket
programs and executed 16 Racket calls over two four-pair episodes (three
train/one query per setting). All 6 training pairs distinguish both settings.
Evidence: `checks/parametric/orientation-report.json` and
`checks/parametric/materialized/`.

**Limit.** This remains a proposed prototype. It is not wired into production,
selected authority, approval, or training metadata, and its retained evidence is
bounded to two episodes at one seed family.

## D2 — Reject invalid scalar controls at the public boundary

**Prior choice.** Version 5.0.0 relied on equality/coercion in `GenCtx` and local
range checks. Python values such as `9.0 == 9` and string-to-int conversion let
wrong-type call arguments and overrides through.

**New choice.** Require exact integers for `seed`, `sample_index`, and every
integer/color override; reject Boolean, float, and string values; require a
non-negative sample index; accept only `None/easy/medium/hard` for difficulty.
Unknown overrides remain rejected by the declared-axis boundary.

**Evidence.** The before `defect_lint` found 123 accepted invalid-scalar probes.
A focused regression was written first and observed failing, then the boundary
was repaired. The final defect lint and 46 focused tests pass. Evidence:
`checks/before/checks/e3f1bc75d654_before_defect_lint.log`,
`checks/tdd-red-task-tests-v2/`, and `checks/task-tests-final-v2/`.

**Failure mode avoided.** Coercion can make an advertised exact control appear
honored while silently accepting a different API type, and Boolean values can
behave as integers.

## D3 — Synchronize selected authority text, not Racket semantics

**Prior choice.** The selected `target_code` copies were execution-equivalent to
the canonical `program_solution` but differed in exact text. The before authority
gate therefore failed even though both forms solved all canonical pairs.

**New choice.** Copy canonical `program_solution` byte-for-byte into only the two
selected `target_code` fields. Preserve archival `raw_code`. Do not modify the
canonical row or transformation semantics.

**Evidence.** Exact selected source SHA-256 is
`cf706900d9a6aef99774a491fcb1ccc49f5b8c2b83ab77623967d993b8263d8d`;
normalized hash and `RULE_HASH` remain `0ac13a729d1a`. Final authority sync reports
one exact selected group and execution parity for both archival and canonical
forms. Evidence: `checks/authority_sync-final/` and the final battery.

## D4 — Teach the strongest canonical-fitting size-selection rival

**Rival.** “Use the leftmost frame’s interior dimensions as the kept size” fits
all 8 usable canonical pairs. It is stronger than “keep the largest frame” for
this family because the canonical layout accidentally aligns leftmost position
with the intended size while ordinary generated layouts frequently do not.

**Prior choice.** Version 5.0.0 emitted counterexamples only stochastically. Over
1000 draws per band the rival disagreed in 295 easy, 314 medium, and 373 hard
cases, but a short lesson could still omit one.

**New choice.** Reserve every even sample index for a lawful layout whose
leftmost frame is a differently sized distractor. Declare the rival as an
executable semantic competitor and witness. With three demonstrations plus one
query, every four consecutive pairs contain two such witnesses; any query
rotation leaves at least one in the demonstrations.

**Alternatives rejected.** Merely increasing the random witness probability does
not guarantee lesson identifiability. Reordering output frames is impossible
because the rule operates on a spatial scene, not an object list. Hard-coding a
single witness morphology would unnecessarily narrow the distribution.

**Evidence.** The exact retained witness is
`repo/generators/e3f1bc75d654/counterexamples/leftmost-frame-shortcut.json`.
Fixed-seed schedule enumeration covers all 6 start/band combinations and 24 query
rotations. The production census covers 300 lessons, 1200 labelled pairs, 1200
query rotations, and 1200 unique inputs with zero ambiguity, hook warnings, or
scoring errors. Evidence: `checks/schedule-period-s0.summary.json`,
`checks/lesson-census-final-v2.summary.json`, and the compressed full census.

**Limit.** These checks refute the declared rival and generic searched rivals;
they do not prove uniqueness against every possible feature-conditioned rule.

## D5 — Preserve canonical support while adding the deterministic witness

**Choice.** Keep the complete canonical linked-profile prior default-only. Since
even slots are reserved for the witness, sample the prior at 60% on odd slots,
which retains an effective 30% prior across the two-slot schedule.

**Rationale.** The prior preserves official canvas/frame linkage and pattern
morphology. Explicit overrides bypass it so exact controls remain observable.
The effective rate matches the previous intended support while avoiding a
competition between “canonical prior” and “teaching witness” in the same slot.

**Failure modes and limits.** Consecutive samples are intentionally correlated by
schedule role. The fixed-seed schedule receipt proves declared start residues,
not every seed or every undeclared rival. The profile-floor stage remains the
acceptance check for exact/envelope canonical support.

## D6 — Make focused tests portable and source-bound

**Choice.** Replace fixed `__file__.parents[...]` canonical paths with
`reviewer_support.find_root`, `canonical_path`, `canonical_pairs`, and
`load_selected_generator`. Add strict scalar, source authority, semantic rival,
cyclic lesson, parametric, and exact counterexample tests under the assigned task.

**Rationale.** The original focused test passed in the repository layout but
failed in the isolated portable snapshot before reaching new assertions. A task
test must resolve the staged runtime rather than assume source depth.

**Evidence.** The inherited path failure is retained in
`checks/tdd-red-task-tests-v2/`; final portable task tests pass 46/46 in
`checks/task-tests-final-v2/`.

## D7 — Retain a small exact counterexample and independent Racket receipt

**Choice.** Save one minimal source-bound generated disagreement at
`seed=1`, `sample_index=0`, `difficulty=easy`, including the exact input,
intended output, rival output, source hashes, frame facts, and replay command.
Execute the public selected Racket rule on that input and retain its receipt.

**Rationale.** Aggregate rates are useful for distribution assessment but do not
let a future agent inspect or replay the semantic distinction. The exact witness
also guards against a shared Python-mirror error.

**Evidence.** Racket returned a valid output, matched the intended output, differed
from the rival, and executed rule hash `0ac13a729d1a`:
`checks/counterexamples/e3f1bc75d654-leftmost-frame-shortcut-racket.json`.

## D8 — Post-repair solve record

The fresh visible-only solver identifies the patterned template, keeps frames
with the same interior dimensions, transfers relative pattern offsets in each
receiver color, and erases mismatches. It passed all 3 visible demonstrations in
one revision. Because the rule was already seen during generator work, the finish
record honestly declares earlier exposure `yes`; it does not claim blindness or
masked-query correctness.

## D9 — Replace the cosmetic orientation proposal with a causal native family

**Supersedes D1 for current promotion.** The retained horizontal-flip prototype
was a useful earlier probe, but the current MAIN gate explicitly rejects a
collapsing remap-then-paint composition. The native family now uses
`target_basis ∈ {template_interior, pattern_bbox}`. The default materializes the
canonical Racket source byte-for-byte. The alternate first finds the sole
patterned template and derives its minimal pattern bounding box and normalized
crop; those input-dependent dimensions then select a distinct empty receiver,
where the normalized crop is stamped in the receiver color.

**Sequential dependency.** A is pattern/template discovery plus bounding-box
measurement. The intermediate is `(row_min, col_min, row_max, col_max)`, crop
height/width, normalized pattern cells, and the receiver selected by those
dimensions. B selects and paints that receiver. B cannot be chosen before A,
because the target dimensions are not otherwise available. A protected-Racket
wrong-intermediate counterfactual substitutes the template's full interior
dimensions; on the retained 30×30 query this selects the canonical-size frames
and changes the final output.

**Teaching and controls.** Matched inputs include canonical-size receivers, one
unique crop-size target, a transposed same-area decoy, and another distractor.
Two visible demonstrations reject the alternate setting and six executable
nearby shortcuts: full-template dimensions, transposed dimensions, area-only
selection, horizontal crop reflection, union of crop/template targets, and
unnormalized offsets. Query labels are not consulted by the teaching check.
Counts are independent over 2–6 demonstrations and 1–4 queries; the fourth
query is a genuine 30×30 six-frame scene spanning all boundaries and quadrants.

**Evidence.** The reusable task-local `audit.py` passed 18 lesson cases, 300
stress episodes / 2,300 visible pairs, 150 matched-input comparisons, 1,200
sequential public projections, 2 strict public exports, and 66 protected-Racket
evaluations. All six rival programs executed and matched independent Python
predictions before being counted as rejected. The production generator remains
unchanged at SHA-256
`357ce12d945153a3241aabac939c956e66e74dd8d6f29922d8f64c47135b7c0e`.
Native qualification and the source-bound causal witness are the owner handoff;
reviewer `ready` is not acceptance or training admission.
