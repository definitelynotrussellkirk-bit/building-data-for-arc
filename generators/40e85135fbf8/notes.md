# Working notes: 40e85135fbf8

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## Review review-a5f6eb555eefd673: numeric rank leakage

The selected v3.0.0 baseline always assigned its third palette color (the largest)
to a unilateral gap. Independently ranking each header axis therefore reproduced
all five canonical pairs and all 1,080 ordinary inputs in the retained baseline
probe. Swapping colors 7 and 9 in seed 0/sample 1 preserves the accepted strict
domain but separates literal equality from rank matching in 14 output cells.
The selected Racket authority confirmed this witness; its rule pin remains
`5d3d67439533`.

Version 4 cycles each gap's private color through minimum/middle/maximum and
shuffles the two shared roles independently. It declares general ordinal matching
and row/column ordinal fallbacks as explicit rivals. Six ordered demonstrations
contain two distinct absent ranks for each direction, guaranteeing one nonmaximum
gap per direction. This is needed to refute the directional fallbacks: a proposed
three-demo change and even five demos have concrete counterexamples under the
retained three-scene cycle. The six-demo choice preserves maximum-gap support.

The palette schedule is low/mixed/high/mixed; mixed is the 82 remaining triples
from colors 1–9. All three canonical shapes and the three-color, at-most-one-gap
strict manifold remain. Within a seed, shape and scene are still correlated;
the variation tests do not claim statistical independence.

### Assembly requirements and tooling

The production claim covers **six ordered demonstrations**, using the original
following query. A 300-lesson Racket census found no declared-rival ambiguity,
but 265/2,100 arbitrary single-pair holdouts were ambiguous. Do not treat the
diagnostic rotation result as support for shuffled query selection.

The shared generate/API defaults are three demonstrations and export defaults to
four. Use explicit `--train 6`, or `workspace/generate_checked_lessons.py`, which
requests `EXAMPLES_NEEDED` and checks each actually materialized lesson before
writing JSONL. Existing approval/research flags retain their meaning.
`workspace/probe_palette_roles.py` reports source-bound color/rank support and
ordered rival checks with Python mirror labels, clearly separate from Racket
evidence. Exact reports, failed iterations and replay commands accompany this
review return. This generator review does not admit solve trajectories to training.
## Current reviewer considerations

Source SHA-256: `2460492c695be301ea5c5d270802ed5f26922c21200550ede570e30c55382aa0`.

# Decisions for 40e85135fbf8

Assignment: `review-a5f6eb555eefd673`. Selected baseline generator SHA-256:
`1a094a887f1052685c91f607804a6dbaa004c4e1a2166cf928bbd420fcca34a8`.
Final generator SHA-256:
`2460492c695be301ea5c5d270802ed5f26922c21200550ede570e30c55382aa0`.

## D1 / G1: remove the numeric-rank shortcut

The baseline's private header color was always the maximum of `(1,2,3)` or
`(7,8,9)`. The original rationale for that numeric-role ordering was not recorded;
the prior notes justify header-set gaps but not maximum-only gaps. A rule that
matches each axis's independently sorted color ranks fits all five canonical
pairs and all 1,080 probed baseline inputs (three bands, seeds 0–19, indices 0–17).
All 720 observed baseline gap inputs had the maximum private color. The small
color-swap witness is strict-valid and differs in 14 output cells; actual Racket
verification is retained in `checks/rank-witness-racket-before.json`.

Cycle the private color through all three sorted ranks and independently shuffle
the shared roles. This retains maximum-gap cases while adding minimum/middle gaps.
Reject simply choosing a random private color: it improves pooled coverage but
does not ensure each complete lesson supplies the necessary witness. Reject
always choosing a nonmaximum color: it replaces one avoidable support restriction
with another. Source-bound broad probes and tests observe roles from returned
grids rather than trusting the scheduling formula.

## D2 / G2: six ordered demonstrations

Keep the three-scene canonical/row-gap/column-gap cycle. On successive occurrences
of either gap, the absent rank advances by one modulo three. Six consecutive
inputs therefore contain two gap examples in each direction, at least one of
which is nonmaximum. They refute the original counterparts/multiplicity rivals,
general ordinal matching, and both directional ordinal fallbacks.

Three examples can leave a directional fallback untested, even when general
ordinal matching is refuted. Five are also insufficient for every start in this
schedule: seed 0, demo indices 0–4 have only a maximum-private column gap; the
column-gap query at index 5 has a minimum-private color. The retained analytical
residue audit covers all 27 seed/start classes. Six is minimal for this retained
cycle and full missing-rank support, not a universal lower bound on every possible
generator design. Cost: default task-specific lessons grow from three to six
demonstrations. No additional operations or reference-rule changes were introduced.

The final Racket census materialized 100 lessons per band, six demonstrations and
one following query, starts 0–99, seeds from the documented census SHA-256 recipe.
It found 0/300 production ambiguities, 0 hook warnings and 0 execution/scoring
errors, across 2,100 pairs and 2,093 globally unique inputs. Each exact instance,
accepted index, rejection, seed and source binding is retained in
`checks/lesson-census.json`. This is finite evidence against declared rivals.

## D3: rotations remain unsupported

The same census tried each of seven labelled pairs as the query, preserving the
other pairs' order. It found 265 ambiguous rotations among 2,100 holdouts
(easy 90/700, medium 89/700, hard 86/700). Holding out the only nonmaximum gap in
one direction can remove its distinguishing evidence. The command explicitly
uses `--rotation-policy diagnostic`; the production pass does not conceal the
rotation failure. No claim of shuffled-query support or universal induction is
made. The safe helper retains the actual ordered assembly.

## D4 / G3: broaden palettes while preserving exact controls

Retain `low=(1,2,3)` and `high=(7,8,9)` as exact observable controls. Add `mixed`
for the other 82 triples from colors 1–9. A low/mixed/high/mixed cycle ensures
palette variation within every six-demo lesson and avoids coupling palette kind
to the three-scene cycle. The pool now contains all 84 three-color subsets;
the finite 1,296-input probe observed 74 distinct palettes, not all 84.
Colors 4, 5 and 6 are now covered. Do not infer empirical coverage of every
palette/rank/shape combination from the size of the declared pool.

The stronger direct probe covers three bands, seeds 0–11, sample indices 0–35:
1,296 draws, 1,291 unique inputs and 1,116 overlapping six-demo windows. It found
zero missing directional witnesses, surviving baseline ordinal-rank lessons,
hook warnings, rival execution errors or ambiguous next queries. These broad
probe labels are Python mirror outputs; the separate census and apply records
provide Racket evidence.

## D5: preserve the task's strict domain and authority

Keep the three canonical output shapes `(4,5)`, `(5,4)`, `(6,5)`, exactly three
nonzero colors, at least two shared colors, repeated shared headers, blank input
interiors and at most one unilateral gap. Preserve the distinction between broad
structural `self_check` and narrower `strict_canonical_like`. The authoritative
rule supports a wider domain, but adding dual gaps, new geometry or unrelated
operations is outside this repair. Shape and scene remain coupled within a fixed
seed; variation is not claimed to be independence. Difficulty bands retain the
same semantic rule and grammar.

Keep Racket rule pin `5d3d67439533` and all canonical/archived authority bytes.
No Python mirror is promoted to reference authority. Baseline and final batteries
both run the selected Racket rule and authority synchronization.

## D6 / G4: portable tests and usable generation

The retained task tests could not import the selected generator in the normal
library layout. Replace their legacy namespace and private script imports with
explicit current-tree source discovery and `reviewer_support.find_root`,
`canonical_path`, and `canonical_pairs`. Preserve their semantic assertions;
broaden the palette-count expectation and witness sample length for the new
advertised lesson. Keep the frozen shared/root fixtures untouched. The first
portability revision incorrectly hashed raw rule whitespace and sampled only one
gap per direction; those test failures and their fixes are retained as
intermediate evidence.

The shared CLI/API still default to three demos, and export to four. The selected
task's new checked helper requests `EXAMPLES_NEEDED` and validates every actual
materialized episode before writing JSONL. This catches both short lessons and
any skipped-index assembly that loses a witness. It preserves the existing
approval/research distinction. Generic entry points still require explicit
`--train 6`; fixing their default policy is the priority shared feedback item.

## D7: prior evidence, solve records and audits

Used the imported `local-random-676de6803719` / `GNOTE-004490..004495` notes as a
lead for the existing authority/strict-domain split and original three-scene
schedule. Their historical pass counts were not treated as current measurements.
The selected source hash matches the pinned v3 baseline. No unintegrated patch or
earlier repair ZIP was borrowed.

Blind solve `5573cf8e2aa4` finished before generator inspection, with no earlier
task exposure and 3/3 visible examples passing. The final-source post-repair solve
passed 6/6 visible examples with earlier exposure explicitly disclosed. Neither
solve consulted reference sources during its solve phase; hidden query correctness
remains unknown. Revisions, probes and frozen finish notes are preserved; no
synthetic failed attempt was manufactured.

The two immutable audit draws are findings-only. See `AUDIT.md` for the reproduced
orientation ambiguity in `142a3a64b02a` and missing U-shaped distractor support in
`ad668d162e0a`. Neither audit target was edited.

## Native parametric proposal: equality matrix and largest blocks

The separate `workspace/parametric/` family retains version 4.0.0 and the exact
canonical Racket default. `selection_mode=largest_blocks` constructs the same
cropped header-equality matrix, then keeps every monochromatic connected
component tied for global maximum cell area. The intermediate matrix determines
the candidates consumed by the second step. A protected native counterfactual
replaces it with the original blank interior and records the changed final
answer; qualification and witness evidence remain reviewer-reported until owner
exact-source replay and acceptance.

The proposal expands its own semantic grammar to 2..30 on each input axis,
arbitrary nonzero headers and palettes, separated runs, bilateral private colors
and empty intersections. Canonical production geometry and authority are intact.
Maximum inputs contain 58 header markers and produce 29×29 matrices; the retained
stress evidence measures real matrix content and component competition.

Three constructive demos support the declared 3–6 range, with default three and
four novel queries. A unique 2×7 winner, multiple cross-color area-six ties, and
unit blocks with blank borders teach distinct branches. An initial core failed
its finite cover because foreground cropping and minimum-dimension ranking
survived; the repaired geometry and red/green regression are retained. The core
can be larger than the production examples, reaching 24 cells on one axis, to
combine the distinctions within three demonstrations. The 64-candidate bound
uses only demos; independent streams preserve matched inputs and count prefixes.

Task-local independent Python/Racket rivals, fixtures and a bounded audit are
reusable by future reviewers. A separately frozen bank checks actual emitted
lessons and queries. Equivalent monochromatic connectivity/run-product methods
are disclosed rather than counted as wrong rules. Exact controls, finite scope,
source hashes, before evidence, native qualification, causal replay and public
projection checks are linked from the returned `RESULTS.json`; see the proposal
README for the full rule and replay commands. These results grant no training
admission or automatic approval of the variant.
