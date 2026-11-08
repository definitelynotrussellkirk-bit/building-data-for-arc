# Working notes: 8c6fbfbe20d4

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## 2026-10-03 review: neutral-color shortcut

Lead used: retained return `local-random-7b579f7f031c` correctly identified
`erase_unmapped_body` as canonical-equivalent and established the four-profile
schedule. I remeasured the pinned selected baseline rather than treating that
return as current-source evidence.

The stronger shortcut `erase_body_colors_absent_from_headers` also fits every
canonical pair. It maps paired sources, preserves colors named in either sparse
header, and erases only body colors absent from both headers. This is stronger
than erasing every unmapped value because it survives target-colored controls
and unpaired-source controls.

Before repair, the semantic gate's pinned 100-lessons-per-band plan left that
shortcut consistent with all four demonstrations in 40/100 easy, 38/100 medium,
and 10/100 hard lessons. The repair adds the shortcut to the executable
contract and guarantees that the scheduled equal-list profile contains both a
target-colored control and a truly neutral control. Focused regressions and the
task-local `workspace/lesson_probe.py` now bind this teaching invariant.

The selected Racket rule was not changed. A lawful discriminator is retained at
`checks/question-shortcut/`: body color 9 is absent from both headers, the
canonical rule preserves it, and the shortcut erases it.
## Current reviewer considerations

Source SHA-256: `0f15f02d0e60731a11e7b4eaa6922c54c2491b57451060ff63e859098e3d98ae`.

# Distribution decisions: 8c6fbfbe20d4

## Scope and authority

The selected Racket rule remains unchanged and pinned at `RULE_HASH =
27daa6126c50`. The repair is generator-only: version 3.0.0 → 3.1.0. The rule
already solved all canonical examples, is reentrant, and had a green authority
check in the pinned baseline. Editing it would have widened risk without
addressing the observed teaching ambiguity.

The retained return `local-random-7b579f7f031c` was used as a lead, not as
current-source evidence. Its useful finding was that canonical bodies do not
show preservation of unmapped values. I reran the complete before battery and
new shortcut probes against baseline generator SHA-256
`d44403d445ae8d1b4c9420608085ede81a0bf060ed8a2944d51613eb04459223`.

## Structural domain

### Top two rows are ordered sparse lists

**Choice.** Row 0 and row 1 are independent sparse lists. Zeros are skipped;
nonzeros are paired in left-to-right order up to the shorter list length.
Rows 2+ are the body.

**Rationale.** This is the canonical behavior and prevents a same-column
legend shortcut. Independent header columns and gaps are semantically useful,
not cosmetic noise.

**Rejected alternatives.** Equal-length-only lists, same-column pairs, sorting
colors before pairing, and right-aligning unequal lists all fit subsets but are
wrong. They remain executable `LESSON_COMPETITORS` and have dedicated witnesses.

**Probe/failure mode.** `SEMANTIC_WITNESSES` requires independent positions,
crossed color rank, and an extra-target case. Removing those profiles can make
an entire lesson compatible with one of the alternatives even while aggregate
examples remain diverse.

### Shapes

**Choice.** Inputs are 5–12 rows by 5–14 columns; body height is 3–10. Band
ranges grow from easy to hard. Width is chosen large enough for the scheduled
header lengths and usually leaves header gaps.

**Rationale.** These bounds retain canonical-scale examples while varying body
area enough to prevent memorizing one fixed geometry. The rule is row-role
based, so geometric transformations are not generally covariant.

**Rejected alternatives.** D4 augmentation was not enabled: a rotation moves
the semantic header rows, while a reflection reverses list order. Arbitrary
resizing or giant sparse canvases would add cost without a new rule distinction.

**Limitation.** The curriculum does not prove behavior outside these size
bounds. Exact lawful overrides can create a full header row without a gap; the
validator permits that edge intentionally.

### Palette and background

**Choice.** Color 0 is fixed background. Source and target colors are distinct,
nonzero, and disjoint. Body controls may reuse target colors or use colors absent
from both headers.

**Rationale.** A target-colored control distinguishes “only recolor sources”
from “erase everything not in the source list.” A truly neutral control is
needed for the stronger rival that preserves any color mentioned in either
header.

**Rejected alternatives.** Arbitrary palette permutation is unsafe because it
could move 0 into a semantic nonbackground role. Restricting the body to source
colors reproduces the canonical ambiguity rather than teaching preservation.

**Limitation.** ARC has only nine nonzero colors. With four sources and four
targets, only one neutral color remains, so the generator may repeat that color
rather than manufacture more distinct neutral roles.

## Four-profile lesson schedule

`sample_index % 4` selects:

1. `canonical_extra_target` — canonical-like extra target behavior.
2. `equal_gapped_controls` — equal list lengths with independent gaps and body controls.
3. `source_extra_preserved` — a shorter target list and an unpaired source that remains unchanged.
4. `target_extra_controls` — an extra target plus outside-source controls.

**Original rationale.** The retained 3.0.0 design used one deterministic profile
per residue so every four consecutive examples exercised all major branches.
This avoids relying on lucky independent random draws.

**Observed defect.** The old control sampler always made the first control a
target color and chose later controls randomly from target and neutral colors.
A stronger `erase_body_colors_absent_from_headers` rival therefore survived all
four demos in 40/100 easy, 38/100 medium, and 10/100 hard lessons under the
semantic gate's pinned sampler. It survived target controls and the unpaired
source because all those values occur in a header.

**Repair.** The default `equal_gapped_controls` profile now draws at least two
controls. The first is target-colored and the second is guaranteed neutral
(absent from both headers); remaining controls retain the old mixed sampling.
The rival was added to `CANONICAL_SHORTCUTS`, `SEMANTIC_RIVALS`,
`LESSON_COMPETITORS`, and `WITNESS_RIVALS`.

**Why this profile.** Putting the guarantee in one fixed schedule slot is
minimal and deterministic. Requiring a neutral control independently in every
profile would overconstrain the distribution and reduce legitimate canonical-
like examples. A rejection loop at lesson assembly was rejected because it
would hide the teaching invariant outside the generator and complicate replay.
Merely increasing random neutral probability was rejected because it would
still permit complete ambiguous lessons.

**Override behavior.** Explicit `n_unmapped=0` or `1` remains observable and
lawful. Therefore the guarantee is for the default scheduled curriculum, not
for every possible override combination. This preserves the advertised exact
control rather than silently clamping caller input.

## Executable semantic contract

The new rival is implemented once and referenced by the public rival mappings.
`neutral_body_value_is_preserved` fires only when a truly neutral body value is
present and the rival actually disagrees with the intended mirror. This avoids a
frequency-only witness that could claim support without a semantic distinction.

`lesson_identifiable` still requires four demonstrations and checks every
current `LESSON_COMPETITORS` entry. The new
`workspace/lesson_probe.py` iterates those declarations rather than maintaining
a copied rival-name list. Mirror mode is a fast schedule regression; Racket mode
uses `generator_semantic_gate.materialize_lessons` and the production rule
runner.

## Measurements and limits

- Before battery: 12/12 stages green; this established that the repair was not
  prompted by a failing generic gate.
- Focused TDD: the three pinned survivor lessons and missing contract binding
  failed before the change, then 10 focused tests passed after it.
- Final canonical Racket census: 300/300 complete lessons, 100 per band,
  1,500 unique inputs, zero declared competitor survivals. The matching mirror
  census also passed. Sampler:
  `generator_semantic_gate._lesson_plan`, stride 11, four demos plus one query.
- Exact discriminator: canonical Racket output in
  `checks/question-shortcut/racket.json` preserves neutral color 9; executable
  rival output in `checks/question-shortcut/rival.json` erases it.

These measurements establish support in the sampled generator curriculum. They
do not prove that four examples uniquely identify the intended rule among all
possible programs, nor that every lawful override set is pedagogically complete.
