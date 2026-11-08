# Working notes: 88ce0ac7322b

## Final review state (2026-10-05)

- Final generator SHA-256: `1428762df7b65c25e42e190c652cb3c38dd135d955592b2726cb0fcfe0e52a67`.
- Canonical Racket rule unchanged; normalized hash `53d8281899b9`.
- Baseline battery: 6 green, 1 advisory, 5 failed.
- First repair battery: 10 green, 2 failed (palette drift and 15% profile floor).
- Final battery: 12/12 green.
- Final portable tests: 49/49.
- Final census: 300 lessons, 1,200 rotations, 0 ambiguities.

The original axis surface appeared inherited and had no retained task-specific
rationale. The selected repair removes dead/redundant controls rather than
trying to preserve them cosmetically. Mixed examples use only payload colors 1
and 2 because a second foreground color is the minimum needed to distinguish
occupancy from red-count/modal/raw-sum shortcuts while remaining close to the
canonical palette.

See root `REVIEW.md` and `DECISIONS.md` for full evidence and limitations, and
`workspace/rival_probe.py` for the retained source-bound cyclic-start probe.
## Current reviewer considerations

Source SHA-256: `1428762df7b65c25e42e190c652cb3c38dd135d955592b2726cb0fcfe0e52a67`.

# Decisions — 88ce0ac7322b

## D1. Keep the Racket authority unchanged

**Decision.** Pin `RULE_HASH = 53d8281899b9` and repair only the input
curriculum. The public rule already sorts complete separator-delimited tiles by
nonzero occupancy, and rule smoke plus authority sync showed no behavioral
defect.

**Original rationale.** No rationale was recorded for leaving `RULE_HASH`
unpinned; the baseline appears to predate the current authority contract.

**Alternative considered.** Rewrite the rule or synchronize an archival bank
copy. Rejected: selected canonical execution already passed, and archival
divergence is reported by authority sync without affecting selected parity.

**Probe/failure mode.** Rule smoke, canonical examples, and the independent
Python mirror check selected behavior. A future selected-rule edit must update
the pin atomically.

## D2. Use the complete 3×3 tile-strip grammar

**Decision.** Accept exactly three rows, 3–5 complete 3×3 tiles, full color-9
separator columns, payload colors 0–8, tile occupancies 1–8, pairwise-distinct
occupancies, and an initially unsorted order.

**Original rationale.** The baseline hard-coded 4–5 tiles and rejected all public
3-tile inputs. No task-specific justification was documented.

**Alternatives considered.** (a) Preserve 4–5 tiles and add a special canonical
exception; rejected because validator semantics would depend on provenance.
(b) Permit arbitrary tile sizes or separator colors; rejected because neither
appears in the public task and would broaden the induction problem without
supporting evidence.

**Probe/failure mode.** Targeted tests reject ragged grids, bad separators,
payload 9s, occupancy ties, empty/full tiles, non-ARC cells, and identity order.
The grammar intentionally excludes tied keys, so tie-breaking is not taught.

## D3. Replace the inherited axis surface with two exact controls

**Decision.** Advertise only `profile` and `order_pattern`. Both are recoverable
from pixels by `observe_overrides`, accepted in every band, and exhaustively
crossed by the shared override gate.

**Original rationale.** The baseline's `grid_h`, `grid_w`, `palette_kind`,
`tile_count`, `palette_size`, `position_bias`, `n_distinct_colors`, `density`, and
`texture` fields looked like inherited metadata. Most were ignored, fixed,
diagnostic-only, or internally contradictory; no rationale was retained.

**Alternatives considered.** Repair every old axis. Rejected because several
were not meaningful independent dimensions of this task (`grid_h` is
necessarily 3; `grid_w` is derived from tile count; `density` duplicates
occupancy). Marking them all diagnostic would preserve clutter without training
value.

**Probe/failure mode.** Final override evidence covers 1,800 draws, 20 cases and
three bands with zero findings or warnings; an unknown key raises `ValueError`.

## D4. Anchor the canonical profile explicitly

**Decision.** `canonical3` emits exactly three red/color-2 tiles, reproducing the
public 3×11/palette-3 input profile. It occupies two residues of the five-residue
schedule.

**Original rationale.** Baseline defaults generated only 4–5 tiles, producing
0/60 exact-profile hits.

**Alternatives considered.** A one-in-four anchor was the first repair. It was
semantically adequate but the pinned profile-floor sample hit only 9/60 (15%),
under the 25% clean-verdict threshold. A two-in-five schedule gives measured
20/60 support while preserving mixed witnesses in every lesson.

**Probe/failure mode.** Final profile-floor counts are 6/20 easy, 7/20 medium,
and 7/20 hard. Overweighting canonical anchors further would reduce the number
of color-invariance counterexamples.

## D5. Use the minimum mixed palette that breaks canonical shortcuts

**Decision.** Mixed examples use payload colors 1 and 2 only, plus background 0
and separator 9. Core occupancies are selected from `(4,5|6,7|8)`: occupancy 4
is all 2, the middle count is balanced between 1 and 2, and the largest count is
all 1.

**Original rationale.** The first repair used many distinct/high colors to make
wrong keys disagree clearly. It worked semantically but defect lint measured a
generated palette around 9 versus canonical 3 and flagged wrong-task drift.

**Alternatives considered.** (a) Stay monochrome: impossible to distinguish
occupancy from color-2 count, modal count, or raw sum. (b) Keep six or more
payload colors: unnecessary and distributionally far from canonical. (c) Use
one additional payload color: selected; it is the minimal extension.

**Probe/failure mode.** In intended occupancy order the three rival key
sequences are non-monotone, so stable sorting cannot accidentally reproduce the
right answer. Tests cross all profiles, order patterns, and bands. A remaining
limitation is that the curriculum does not explore arbitrary palettes.

## D6. Schedule for both production order and query rotation

**Decision.** Use profile residues
`canonical3, mixed3, canonical3, mixed4, mixed5`; change order pattern every five
samples across `reverse, rotate, zigzag`. `EXAMPLES_NEEDED = 3`, so lessons have
three demos and one query. Every cyclic four-pair window has at least two mixed
profiles; after holding any pair out, at least one mixed witness remains.

**Original rationale.** The baseline had no semantic schedule. The first repair
used one canonical plus three mixed residues; it passed identifiability but not
the profile-rate gate.

**Alternatives considered.** Randomly resample until a witness appears; rejected
because it makes failures seed-dependent and harder to audit. An ordered-only
policy was also rejected because downstream assembly permits query rotation.

**Probe/failure mode.** The small semantic gate checked 48 rotations; the local
probe exhausted 15 starts × 3 bands × 4 query positions; the source-bound census
scored 1,200 rotations. All were identifiable against declared rivals.

## D7. Declare executable rivals instead of prose-only warnings

**Decision.** Register `color_2_count`, `dominant_color_count`, and
`raw_color_sum` under `CANONICAL_SHORTCUTS`, `SEMANTIC_RIVALS`, and
`LESSON_COMPETITORS`; bind them to a mixed-palette witness and enforce them in
`lesson_identifiable`.

**Original rationale.** None existed in the baseline, so the semantic gate could
only return `NO_CONTRACT` even though the canonical examples were shortcut-rich.

**Alternatives considered.** Mention shortcuts only in notes; rejected because
nothing executable would prevent regression. Add a very large hypothesis
library; deferred because each rival should be task-lawful, interpretable, and
cheap enough for per-lesson checks.

**Probe/failure mode.** Each rival fits all three canonical pairs and disagrees
on every exact mixed profile/order case. The finite set cannot exclude an
unimagined rule, so claims are explicitly bounded.

## D8. Retain a source-bound future-agent probe

**Decision.** Add `workspace/rival_probe.py`, tested through the portable task
runtime. It dynamically imports the selected generator declarations, reads
canonical data through `reviewer_support`, uses an independent expected-output
implementation, checks all joint overrides, and exhausts cyclic starts and
query rotations.

**Alternative considered.** Rely only on the shared 300-lesson census. Rejected
as the sole local aid because it samples production starts rather than
exhausting this small deterministic schedule and is more expensive during
iteration.

**Probe/failure mode.** The retained tool does not invoke Racket and therefore is
not authority evidence by itself. Its output is paired with rule smoke,
authority sync, and the shared Racket-labeled census.

<!-- arcpuzzles-trainer-ambiguity:start -->
## Current trainer ambiguity follow-up

Claude supplied 1 exact canonical lesson(s) with a proposed alternative rule. Retained privately with source hashes and all stored queries: `evidence/trainer-ambiguity-current/current.json`. These are **open describer flags**, not confirmed wrong labels or failed current parametric qualifications. Check whether the proposed rival fits every demonstration and changes any stored query; distinguish source revisions before repairing. Approval and training state are unchanged.
<!-- arcpuzzles-trainer-ambiguity:end -->
