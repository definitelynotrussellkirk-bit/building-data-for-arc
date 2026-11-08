# Working notes: 6098a755202d

## Review 2026-10-02

The canonical Racket program is the semantic authority. It applies Manhattan
Voronoi fill after `remove-duplicates` on the colors of equally near seeds.
Consequently, a tie between two same-color seed cells fills with that color;
only a tie between different colors remains 0. The previous generator sampled
only distinct seed colors, so every generated lesson was also explained by the
weaker rival “any multi-seed tie stays 0.”

Version 3.0.0 replaces dead texture/diagnostic axes with five observable axes:
`grid_h`, `grid_w`, `frame_top`, `frame_left`, and `profile`. Three scheduled
profiles cover a distinct pair, the decisive repeated-color tie, and a distinct
triple. Candidates are rejection-sampled until every seed color owns output
territory; the pair profile includes a cross-color boundary and the repeated
profile includes a cell where the canonical rule disagrees with the seed-count
rival.

`self_check` now recognizes the canonical variable frame offsets instead of
hard-coding `(1,1)`, validates all five canonical inputs, and enforces the
teaching grammar. `rule_mirror`, semantic witnesses/rivals, and
`lesson_identifiable` provide executable contracts. The selected archival
`target_code` and task prose were synchronized to the canonical Racket source.

Replay the shortcut proof with:

```bash
python3 workspace/analyze_shortcut.py
python3 workspace/analyze_shortcut.py --racket
```

The checked witness differs at exactly `(row=2, column=4)`: canonical output 2,
seed-count rival 0.

## Known limits

The curriculum intentionally stays inside one rectangular frame and uses two or
three seeds. It does not claim to define behavior for multiple frames, seeds on
the frame, nonzero cells outside the frame, or more than three seeds. Bottom and
right frame margins remain one cell while top and left vary between one and two,
matching the observed canonical envelope without adding unmotivated geometry.
## Current reviewer considerations

Source SHA-256: `f37f4f1a4a4ae60d2dccf0775041ab0b58d20c099b3fcfb494c8a0992df19a9e`.

# Decisions: 6098a755202d

## Semantic authority

**Choice.** Treat the canonical Racket program as authoritative. Its
`remove-duplicates` operation means a tie is among nearest colors, not nearest
seed cells.

**Original rationale.** Unknown. The old prose said any tied seeds stay zero,
while the executable canonical, archival raw code, and selected target all used
color deduplication. All canonical seeds were distinct, so the inconsistency was
not observable there.

**Alternatives considered.** Preserve the prose and change the Racket program;
keep distinct-color generation and leave the ambiguity unresolved; or teach the
executable semantics explicitly. I chose the last option because repository
rules state that labels are derived through the reference runtime.

**Probe and failure mode.** `workspace/analyze_shortcut.py --racket` checks all
five canonical pairs and a repeated-color witness. Without the witness, the
seed-count rival survives every demonstration. The task prose and selected base
description were updated to prevent text/output contradiction.

## Grid dimensions

**Choice.** `grid_h` is 8..12 and `grid_w` is 9..14, with defaults drawn from a
five-shape schedule observed in the canonical set.

**Original rationale.** The old defaults were approximately 8..10 by 11..13,
but no retained rationale explained the narrower support.

**Alternatives considered.** Fix dimensions to one canonical shape; keep the old
narrow ranges; or broaden to the whole ARC limit. Fixed dimensions underteach
shape variation, the old ranges missed canonical profiles, and full ARC ranges
would add unsupported geometry. The selected envelope accepts all canonical
inputs and gives 38/60 exact-profile hits and 60/60 envelope hits.

**Limit.** Dimensions outside 8..12 by 9..14 are rejected rather than silently
accepted.

## Frame placement

**Choice.** Top and left margins are explicit 1..2 axes. Bottom and right margins
remain exactly one cell.

**Original rationale.** The old generator hard-coded `(1,1,h-2,w-2)`, even
though two canonical examples shift the frame down or right.

**Alternatives considered.** Vary all four margins independently; infer an
arbitrary rectangle anywhere; or model only observed offsets. Fully independent
margins greatly expand the morphology without canonical evidence. The chosen
model accepts all canonical frames while keeping a simple observable contract.

**Failure mode.** A frame touching an outer grid edge, a broken frame, multiple
color-5 structures, or nonzero content outside the frame is rejected.

## Seed count and profile

**Choice.** Use three named profiles: two distinct seeds, three seeds with one
repeated color, and three distinct seeds. Schedule them by `sample_index % 3`.

**Original rationale.** The old generator used two or three seeds, all in
distinct colors, apparently to mirror the demonstrations. That made the
strongest rival rule impossible to falsify.

**Alternatives considered.** Randomly sample profiles; include repeated colors
rarely; or force every individual grid to contain all phenomena. A deterministic
three-example cycle guarantees lesson coverage without overloading a single
scene. The semantic gate observed every profile in every difficulty band and
12/12 identifiable lessons.

**Failure mode.** The repeated-color profile is rejected and redrawn unless it
contains a same-color nearest-seed tie where the intended and rival outputs
differ. The distinct-pair profile is rejected unless it contains a cross-color
tie.

## Palette

**Choice.** Draw from colors `(2,3,4,6,7,8,9)`; reserve 0 for background and 5
for the frame.

**Original rationale.** This matches the old palette and canonical roles.

**Alternatives considered.** Permit color 1 or let frame/background roles vary.
Neither is needed to teach this rule, and role variation would confound the
nearest-color concept with palette-role inference.

**Limit.** The generator does not claim palette-role generalization.

## Placement acceptance criteria

**Choice.** Rejection-sample up to 512 layouts until `self_check` passes, every
seed color owns at least two output cells, and the profile-specific witness is
visible.

**Original rationale.** The old placement loop only sought free cells and could
produce semantically weak examples.

**Alternatives considered.** Construct algebraic seed coordinates for each
profile or accept every random placement. Direct construction is possible but
would reduce geometric diversity; accepting all placements creates invisible
or tiny concepts. The current bounded search succeeded for all 1,080 exhaustive
override probes and all 12,960 official override draws.

**Failure mode.** If no lawful scene is found, generation raises a descriptive
`ValueError`; it never silently returns a malformed grid.

## Overrides

**Choice.** Declare only axes that are both consumed and observable:
`grid_h`, `grid_w`, `frame_top`, `frame_left`, `profile`. Reject unknown keys.

**Original rationale.** The old interface inherited generic axes such as
texture, density, palette size, and position bias; several were dead,
single-valued, aliases, or mixed lawful and negative fixtures.

**Alternatives considered.** Preserve compatibility by accepting ignored axes or
classify many incompatibilities. Silent acceptance made typos look successful
and generated 15,574 baseline findings. Removing unsupported axes yields a
strict, falsifiable contract with no declared incompatibilities.

## Validation and semantic hooks

**Choice.** Provide `_geometry`, `semantic_observables`, `rule_mirror`,
`strict_canonical_like`, `SEMANTIC_RIVALS`, `SEMANTIC_WITNESSES`,
`WITNESS_RIVALS`, `CANONICAL_SHORTCUTS`, and `lesson_identifiable`.

**Original rationale.** No semantic contract existed.

**Alternatives considered.** Rely only on generic lint/self-check or add a
single ad hoc assertion. The complete hook set lets the shared semantic gate
measure strict support, witness frequency, rival disagreement, and lesson-level
identifiability. It passed 600/600 strict draws and 60/60 sampled rival claims.

## Selected authority file

**Choice.** Replace the selected base `target_code` with the exact canonical
program text; leave executable behavior unchanged.

**Original rationale.** The selected text contained one extra explanatory
comment. It was behavior-equivalent but failed exact authority synchronization.

**Alternatives considered.** Keep the beautified copy or modify canonical text.
Exact synchronization avoids two active source identities while preserving the
archival raw code and canonical program.

## Reviewer utility

**Choice.** Add `workspace/analyze_shortcut.py` plus focused subprocess and
semantic tests.

**Original rationale.** No replayable artifact connected the shortcut claim,
canonical pairs, exact witness, Python mirror, and Racket authority.

**Alternatives considered.** Record only prose in the review. The script is more
useful to future agents because it emits machine-readable evidence and can rerun
the reference rule.

**Limit.** Its witness is task-specific by design; it is not a generic ARC
shortcut miner.
