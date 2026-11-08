# Working notes: 5dddd8d6711e

## Review review-190e32a35be1178b, 2026-10-03

Baseline `3.1.0` used equal 3x3 rooms and connected every chamber. Canonical
train example 2 has one row of height-5 rooms with widths 3,5,3,4; the other
examples include isolated chambers. Equal room areas also make area minimization
indistinguishable from minimizing chamber count. The baseline lacked a rule pin,
advertised ignored controls, narrowed declared room controls by difficulty, and
accepted an invalid duplicate marker or crashed on malformed grids.

Version `4.0.0` replaces those restrictions with variable rectangular geometry,
forests/cycles, same-room and unreachable endpoints, wall-9 support, and interior
pigments. All output labels still come from unchanged canonical Racket. The
Python BFS model is used only for semantic diagnostics and constructive placement;
`workspace/maze_probe.py` independently flood-fills and checks it against Racket.

The period-three schedule is `(seed + sample_index) % 3`: witness, canonical
geometry, varied. Witnesses embed a complete 2x3 room graph with pendant forest
attachments, two colored distractors (one on-path and one off-path), and unequal
areas. This separates DFS, descending-order BFS, all-shortest-path union, minimum
room area, and off-path noise preservation. Each rival fits all three original
pairs. Canonical geometry is sampled afresh with random doors/endpoints; no
canonical input or output grids are replayed.

Evidence in the associated return: all 12 after-battery stages green; strict
600/600; all five rivals rejected in 900 overlapping three-demo windows across
three bands, based on 1,800 indexed draws / 1,201 unique generated grids; independent
oracle equals canonical Racket on 1,204 unique inputs including all originals.
These are finite source-bound measurements, not universal induction or model
training results. The return includes exact commands, hashes, failures and audits.

## Boundaries and next work

- Keep 2/3/7/8 semantic roles fixed; arbitrary palette permutation is invalid.
- Tied paths depend on red-start, sorted room-ID BFS. Re-run the reference after
  rotations/reflections or swapping endpoints; tied labels are not equivariant.
- The guarantee covers consecutive three-demo default windows. Re-check shorter,
  shuffled, filtered, independently resampled or overridden episodes.
- The witness motif has a recognizable geometry and fixed relative endpoints;
  randomized canonical/varied slots supply broader layouts. This finite rival
  set does not rule out another motif-conditioned policy.
- Some inputs repeat across difficulty bands. Use input/family hashes for splits;
  do not treat band membership as evidence of disjoint data.
- No earlier task-specific review return was present or used as repair evidence.
## Current reviewer considerations

Source SHA-256: `0814b7b35671edce6464da6ca633fa21812d21d360f9b69993ec98df59076d04`.

# Decisions — 5dddd8d6711e, review-190e32a35be1178b

## Source and evidence boundaries

The assigned baseline is version 3.1.0, SHA-256
`b89467365a197f5cc61581a3c4030722694898a54db9d53e5d63a06099dd929a`.
Its associated-notes file was empty and no task review index was present. No
pending return was treated as measured evidence. The original rationale for
fixed 3x3 rooms and connecting all rooms is only partly documented: the old
source says a spanning tree guarantees a path. Why these restrictions were
retained despite the canonical examples is unknown.

The selected canonical Racket source remains unchanged. Its normalized rule
identifier is `5e8877987e4c`. A task-local Python model supports witnesses; an
independent implementation in `workspace/maze_probe.py` was compared with
actual public Racket outputs. Neither implementation replaces label authority.

## D1 — Variable rooms and explicit canonical geometry support

Canonical input sizes are 9x13, 7x20 and 13x10, all with five colors. One example
has a single chamber row, and room widths/heights vary. The repair supports
1..6 chamber rows/columns, independent rectangular row heights and column widths,
and variable canvas size within 30x30. One schedule slot draws one of the three
canonical geometries while randomizing doors, endpoints and their positions.

Rejected: retaining the 4-pixel lattice or just widening its row/column counts.
That never expresses the height-5 and width-5 chambers or single-row example.
Rejected: replaying canonical grids. Geometry anchors preserve meaningful size
support without copying complete inputs or labels. Every band's 20-draw profile
check has hits: easy 8, medium 5, hard 5. This coarse profile measure is not used
as a substitute for the semantic checks.

## D2 — Connectedness and endpoint cases

The original fully connected spanning tree excludes canonical isolated chambers.
Default mazes now contain forests with optional cycles, and both connected and
unreachable endpoint pairs. A same-room pair is also lawful: two different
marker cells belong to one chamber and the whole chamber is filled. If no graph
path exists, Racket clears all nonwall interiors, including both markers.

Rejected: treating no doors as necessarily invalid, or omitting markers to make
an edge-case texture. Marker-free examples crash the reference selection logic;
no-path examples with both markers are well-defined. These decisions are
separated from their old ambiguous `texture` names.

## D3 — Fixed color roles and nonpath clearing

Only 1 and 9 are sampled as ordinary wall colors; 7 remains a door, 2/3 endpoints,
and 8 the output fill. Interior pigments 4/5/6/8 test that component membership
is geometric rather than color-connected and that nonpath marks are erased.
The witness uses two identical pigments, one on-path and one off-path, to avoid
making pigment identity an answer cue. Other profiles scatter pigments freely.

Rejected: arbitrary global color permutation, which changes this rule's meaning.
The validator admits the rectangular-chamber manifold with closed boundaries
and doors between opposite rooms. The Racket implementation supports additional
irregular components/junctions; that larger space is exercised by oracle
fixtures and is not claimed as generated coverage.

## D4 — Exact controls and observable results

The four supported controls are `rooms_r=1..6`, `rooms_c=1..6`, `wall_color=1|9`
and `n_noise=0..2`. They work in every band and every combination. Observations
are reconstructed from returned pixels, not the RNG's requested values. Invalid
integer types/values and unknown keys raise ValueError. Obsolete `density`,
`position_bias`, `n_distinct_colors`, and diagnostic `texture` controls are
removed rather than silently accepted; this is a version-4 interface change.

Rejected: clamping supplied counts, silently reducing pigment counts, or giving
each difficulty band a different legal override domain. Difficulty changes
sampling weights and cycle rates while retaining the common exact-control domain.

## D5 — Teach the decision within complete lessons

A seed-rotated period-three schedule combines witness, canonical geometry and
varied slots. The witness embeds all seven edges of a 2x3 chamber grid. Forest
attachments enter the cyclic core at most once and therefore add no alternative
core route. Red is in the core's upper-left chamber; green is in its lower-middle
chamber. Sorted BFS, descending BFS, DFS and union-of-shortest-paths select
different chamber sets. Unequal room areas and on/off-path pigments distinguish
two further alternatives.

The five executable rivals all fit every original pair. Default three-example
lessons supply a counterexample to each. The probe uses the actual
`generate(seed,index,difficulty)` calls, all three cyclic starting offsets and
source hashes. It reports 900 overlapping windows, not 900 independent draws:
1,800 indexed calls yield 1,201 unique grids across all bands. Within each band
there are 600 unique grids. All 900 windows reject every declared rival; all
1,204 deduplicated Racket inputs, including originals, agree with the independent
oracle. The battery separately materializes 12 lessons through the real runner.

Rejected: raising a witness's marginal frequency and assuming every lesson
contains one; or coding an unconditional `lesson_identifiable=True` hook. The
hook checks demo-fitting, query-changing rivals. The reusable probe fails
explicitly on crashes, source drift, lost witnesses or mismatches.

## D6 — Residual shortcuts and scope

The guarantee applies to consecutive three-demo default draws. Exact overrides,
shorter lessons, filtering, shuffling and alternate assembly policies need a
new lesson check. The witness is recognizably a 2x3 cyclic core with relative
endpoint constraints; a broader motif-conditioned policy might still survive.
The varied slots supply other topologies/endpoints, but no claim of universal
induction is made. Five explicit rivals are a finite diagnostic family.

Room-ID BFS ties are directional and ordering-dependent. Rotating, reflecting
or swapping endpoints can change which shortest path the reference selects.
Any such augmentation must relabel through Racket. The canonical originals have
unique paths and do not uniquely specify the tie policy themselves.

Cross-band repeated grids are counted, not treated as independent data. Split by
input and provenance/family hashes. We ran no Qwen training or held-out model
benchmark; no downstream accuracy gain or training admission is inferred.

## D7 — Verification and handoff discipline

Retained the 28-failure/8-pass pre-repair regression run, baseline battery failures,
and evidence-export incidents. The initial logger mistakenly precreated the
requested output directory; a later collision recreated its contents during a
run, with the writer unidentified. A completely fresh output collected all
baseline stage evidence successfully. A synthetic probe reproduces evidence
loss on an export-time collision without claiming it identifies that writer.

Selected task tests are run explicitly because the repository suite does not
discover them. New workspace/test files are copied explicitly for portable
verification. The exact final task delta is then applied to a fresh original
packet and focused tests are rerun there, with generator/source hashes retained.
No shared runtime or unrelated generator edits are included.
