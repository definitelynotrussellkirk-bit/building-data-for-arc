# Working notes: 31e43af4bcfa

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## Review review-2273c0fb1442d34d: v3.1.0

The prior `local-random-c3add34452e0` notes were used as leads, particularly the
three-profile schedule and tie-lawfulness decisions. Measurements were rerun on
the pinned v3.0.0 source, SHA-256
`6583017df54ddca89da225416dd2daa3ebca59dddcc2c5b35439b450e02b80ce`.

G1: Old ordering rivals missed canonical-fitting capped-area-3, perimeter, and
8-connectivity shortcuts. Rescoring 300 retained Racket-labeled baseline lessons
with the expanded rivals found 77 ambiguous production lessons and 453 ambiguous
single-query rotations out of 1,200. The original three rivals alone found zero
production ambiguities but 212 rotation ambiguities.

G2: Each distinct-rank scene now includes a square-4 preceding an L-3 spatially,
with diagonal contact but no shared cell or edge. Both have perimeter 8 and
bounding-box area 4, so correct area ranking disagrees with reading order,
capped-area-3, perimeter, and bounding-box ranking. Diagonal contact exposes
the 8-connected extraction shortcut. K=3 adds a singleton; K=4 adds a singleton
and domino. Other profiles keep their earlier tie sizes 2, 3, and 4 and D4
orientation variety. Canonical dimension anchors, all exact dimension/count
combinations, and the Racket rule remain unchanged.

G3: Five demonstrations plus one query give six consecutive samples, two per
profile. Any single holdout retains all profiles among the five demonstrations.
This costs two additional demonstrations relative to v3.0.0. It is a guarantee
about the scheduled witnesses and declared rivals, not all conceivable rules.
The official final census covers 200 lessons per easy/medium/hard band: 600
lessons, 3,600 distinct inputs, and 3,600 rotations, with zero ambiguity, scoring
errors, materialization errors, or hook warnings. Accepted indices and source
hashes are retained in the return's checks/lesson-census-after.json.

G4: Exact integer overrides now use the public draw_int_strict helper. Floats,
numeric strings, and booleans raise TypeError; valid integer domains and the
runtime's None convention are retained. Tests use public reviewer_support
helpers in both the library and staged runtime.

The reusable workspace/probe_curriculum.py checks all 1,260 joint band/count/
height/width/profile cases and every holdout of ordinary cyclic windows. Its
outputs are explicitly Python-mirror diagnostics, with Racket authority checked
separately. Canonical-shortcut declarations include only the three rivals that
fit every canonical labeled pair; all seven rivals remain lesson competitors.

Limits: generated component areas remain 1..4; the validator accepts some larger
components. The capped-area-4 rival cannot be distinguished anywhere in this
generated support, although a lawful area-5/area-6 counterexample exists. The
distinct-rank profile intentionally concentrates on the square/L witness, so it
does not cover every distinct-area inventory. The validator is a structural
Racket-input check, not a universal guarantee of ARC-sized output for arbitrary
hand-built bodies. No full-grid D4 or arbitrary 0/1 color renaming is claimed.
No generator approval or model-trajectory training admission is asserted here.
## Current reviewer considerations

Source SHA-256: `957ffcfc3550177532091e46ea8717bb63b583b9a7871a8360ec2f1e2f58d1d0`.

# Decisions for 31e43af4bcfa

## Baseline and authority

The immutable assignment selected v3.0.0, source SHA-256
`6583017df54ddca89da225416dd2daa3ebca59dddcc2c5b35439b450e02b80ce`.
I used associated notes from `local-random-c3add34452e0` as leads: accept
equal-area components, preserve row/column tie order, retain directional roles,
and inspect all cyclic schedule starts after changing demonstration count.
Those inherited results were not treated as measurements of this packet.

The canonical rule and all canonical data bytes are unchanged. There was no
need to alter authority: the reproduced failures concerned teaching coverage,
declared rivals, and exact controls. Version 3.1.0 deliberately changes keyed
random streams; seed identity is always paired with source/version identity.

## D1: Preserve the input grammar and control domains

Keep background 0, body-object color 1, a left-prefix palette of distinct colors
2..9, K in 2..4, total heights 5..9, and widths 7..13. The original rationale is
available in the source/summary and canonical examples: geometry and palette
have different roles, and disconnected body objects map one-to-one to palette
entries. No evidence justified widening or silently changing those roles.

Exact controls still override weighted defaults in every band. Canonical-size
anchors at sample residues 0 and 4 modulo 8 are retained. All 105 K/height/width
settings were exercised at each of three profile positions in four bands:
1,260 cases, seed 17, zero failures. That is finite construction evidence, not
a claim that every random seed has been enumerated. The existing after battery
also passed its profile floor and override checks.

## D2: Make actual cell count observable

The earlier distinct-rank pair put an object of size K ahead of a singleton.
That distinguishes reading order but does not reliably distinguish area from
coarser ranks, perimeter, or bounding-box size. Capped area at three matches all
three canonical labeled pairs; baseline seed 11, indices 0..2, also leaves it
unrefuted, then query index 3 exposes the error. The exact four inputs and
Racket corroboration are retained in `checks/adversarial-before/` and
`checks/witnesses/`.

New choice: a square of area 4 and an L of area 3, both bounded by 2×2 boxes,
with square first in spatial reading order. Both have perimeter 8. Correct
ranking puts the L first; reading order, perimeter, bounding-box area, and
capped-area-3 put the square first. K=3 adds area 1; K=4 adds areas 1 and 2.
All palette colors remain distinct, making order changes visible.

Alternative rejected: merely add rival names and rely on ordinary sampling.
That would turn some lessons into rejections without guaranteeing a usable
teaching example, especially at K=2. Another rejected alternative was requiring
larger grids: the witness fits the existing minimum 5×7 and every legal control
combination, avoiding an unnecessary API restriction.

The new anchor is intentionally concentrated, rather than claiming broad
shape-size coverage. The two tie profiles still sample equal sizes 2, 3, and 4,
with geometrically distinct D4 variants and varied placements. No full-grid
geometric augmentation is declared: palette-row and reading-order roles are
directional.

## D3: Teach connectivity in the same witness

Force diagonal contact between the square and L while retaining `_can_place`'s
existing prohibition on overlap and orthogonal contact. This makes four versus
eight connectivity observable without adding another profile or increasing the
declared grid domain. An 8-connected rival merges the pieces, assigns the
matching palette prefix, and emits a real differing output. It does not raise
an exception to masquerade as a refuted prediction.

The minimum setting with K=4 is constructible; the exhaustive control probe
also tested it in all four bands. Baseline seed 19, indices 0..2, teaches no
connectivity distinction before the query at index 3; the retained inputs and
actual Racket outputs preserve that counterexample.

## D4: Keep the three-profile structure, use five demonstrations

Profiles remain distinct_rank, row_tie_cross_order, same_row_column_tie. The old
reason for three demos was that every consecutive triple contains one of each.
However, among four pairs, holding out the sole row-tie example removes its
witness. The original declared rivals measured 212 ambiguous rotations out of
1,200 baseline rotations; expanded rivals measured 453.

Five demos plus one query form six consecutive pairs, with two of every
profile. Every single-pair holdout leaves each profile represented. This is the
smallest fixed length that guarantees two occurrences of every profile in this
unchanged period-three design; it is not a proof that no more efficient design
with combined tie witnesses could be built.

Alternative: keep three demonstrations and restrict downstream use to ordered
production lessons. That would avoid two extra examples but would retain a
known query-rotation limitation. Alternative: redesign all profiles to combine
every tie branch in fewer examples. That is awkward at K=2 and would change
more of the established distribution. The conservative five-demo choice costs
two extra demonstrations; exact token cost was not benchmarked.

Official final coverage: 200 Racket-labeled lessons per easy/medium/hard band,
five demos and one query, all six single-query holdouts, 600 lessons and 3,600
distinct inputs. There were no production or rotation ambiguities against the
seven named rivals. A separate Python probe covers all 24 combined schedule/
anchor starts for seeds 0..1 in four bands: 192 overlapping windows and 1,152
holdouts. Counts are not independent trials or universal induction proofs.

## D5: Separate rival roles honestly

All seven rivals are lesson competitors: reading-order-only, size/left/top,
reversed ties, capped-area-three, perimeter, bounding-box area, and eight
connectivity. Only capped-area-three, perimeter, and eight connectivity fit
every usable canonical labeled pair and therefore remain CANONICAL_SHORTCUTS.
The other rivals are still useful because new generated lessons must supply
their own teaching evidence. A canonical-fit matrix and actual named-witness
refutations are retained by the reusable probe; names are read dynamically.

## D6: Reject noninteger exact controls and make tests portable

Legacy draw_int coerced 2.9 to 2 and numeric strings to integers. Use the already
available draw_int_strict primitive for the three integer axes; floats, strings,
and booleans now raise TypeError. Valid values retain draw provenance and exact
observability. None keeps the public runtime's existing no-override convention.
No shared primitive was changed.

The retained task tests' scripts.canonical_profile_gate import failed directly
in this library. Replace it with public canonical_pairs(root=find_root(...))
and load source from the identified library or staged runtime. The root frozen
fixture remains untouched. All 47 staged tests, including the frozen fixture,
pass with no skips. Initial regression and environment failures are preserved.

## D7: Reusable tool, bounded evidence, remaining limitations

The new `workspace/probe_curriculum.py` checks canonical fits, legal joint
controls, deterministic fresh results, witness refutations, complete cyclic
lessons, and all single-query holdouts. It records source hashes and exact
failure cases and refuses to overwrite evidence. Its label basis is explicitly
the Python mirror, distinct from the public Racket census and apply receipts.

Generated component areas remain at most 4. Capped-area-4 agrees everywhere on
this support; a validator-accepted area-5/area-6 example with different rankings
is retained and Racket-checked as a **validator-only** limit. Expanding shape
support is future work and would need placement, lesson, and output-size checks.
In particular, self_check's structural input grammar can accept hand-built
large components whose packed output exceeds standard ARC dimensions. No such
large output is generated by this repair. Arbitrary relabelings involving 0 or
1, arbitrary rotations of the entire task, undeclared rivals, multiple held-out
pairs, and trajectory training admission are not certified.

The two other task audits are findings-only as assigned. Their source files
were left unchanged; the retained Racket execution failures remain actionable
follow-up evidence, not blockers invented for the selected repair.
