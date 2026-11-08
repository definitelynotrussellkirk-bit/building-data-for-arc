# Working notes: 0c5e8548d3be

Version 3.0.0 is a teaching-distribution rewrite. The Racket authority was left
unchanged. The public surface was reduced to exact `grid_h`, `shape_size`, and
`relation_profile` controls; all are recoverable from returned pixels.

The strongest canonical-compatible shortcut is reflection-inclusive (dihedral)
equivalence. Every generated sample now includes a chiral shape and its mirror,
which the intended rotation-only rule separates. All four panels have the same
cell count, eliminating the baseline count shortcut. Input color 8 is reserved.

Final evidence: 12/12 battery stages green, 38/38 task tests green, and 300
source-bound lessons / 1,500 rotated query holdouts with zero ambiguity. See
`workspace/reference_probe.py` for the independent geometry oracle used by the
regression tests.
## Current reviewer considerations

Source SHA-256: `4824a4c03d62f79d3f7279e2df43f393b23e092e5c46e390006686b321ea91e9`.

# Design decisions for `0c5e8548d3be`

## D1. Preserve the selected Racket authority

**Original rationale:** unknown. The selected rule already matched all canonical
pairs and passed execution, purity, grammar, and authority synchronization.

**Decision:** leave every Racket/canonical authority byte unchanged and pin the
Python generator with `RULE_HASH = "c0e3bdee7bdc"`.

**Alternatives:** rewrite the rule for style or replace it with the Python
mirror. Both add source-role risk without correcting a behavioral defect.

**Probe:** before/final rule-smoke, grammar, Racket-lint, authority-sync, and the
independent apply witness under `checks/question/`.

**Limit:** the Python mirror is test support, not label authority.

## D2. Replace broad nominal controls with three exact observable axes

**Original rationale:** the old axes appeared intended to provide combinatorial
variation. In practice several were aliases, singletons, dead under some
textures, or silently accepted invalid values.

**Decision:** expose only `grid_h` (5–8), `shape_size` (4–12), and
`relation_profile` (0=2+2, 1=3+1, 2=2+1+1). `observe_overrides` reconstructs all
three from returned pixels.

**Alternatives:** repair every legacy axis, expose no controls, or publish a large
incompatibility matrix. The first two retain semantic noise or reduce targeted
testing; the third adds complexity without teaching value.

**Probe:** exhaustive boundary/joint override tests plus the shared override
gate. All legal combinations are constructive; unknown and invalid values fail
closed.

**Limit:** object position and palette order remain nuisance randomness rather
than exact public axes.

## D3. Use a validated finite shape catalogue

**Original rationale:** random growth was flexible but made exact size/chirality
and all-combination guarantees hard to prove.

**Decision:** provide two connected 5×5-bounded shapes for each size 4–12. The
primary is four-way chiral; the secondary belongs to another dihedral class.
Import-time validation checks coverage, size, connectivity, chirality, orbit
size, and bounds.

**Alternatives:** rejection-sample polyominoes or solve shapes dynamically.
Those obscure termination and override guarantees. A single shape per size
cannot create the needed semantic contrasts.

**Probe:** import-time assertions, all size boundaries in task tests, and 240
default-sample independent geometry checks.

**Limit:** the catalogue is finite; it provides orientation and placement
variation, not exhaustive polyomino morphology.

## D4. Make cell count useless

**Original rationale:** the old implementation made relation classes have
different counts, likely to keep classes visually distinct.

**Decision:** all four panels in every ordinary example have the same cell
count, while containing two or three rotation classes.

**Alternatives:** merely include occasional equal-count negatives or vary counts
within a class. Occasional evidence leaves many lessons shortcut-solvable;
varying counts within a class contradicts shape equivalence.

**Probe:** `cell_count_equivalence` disagrees with every generated demonstration
in focused tests and the source-bound census.

**Limit:** equal counts are intentionally overrepresented; natural ARC tasks may
mix counts.

## D5. Put a chiral shape beside its mirror in every sample

**Original rationale:** the canonical examples do not distinguish rotations from
reflections.

**Decision:** each relation profile includes at least one mirror-only pair. The
intended output separates it, while a dihedral/reflection rival merges it.

**Alternatives:** rely on one special schedule slot or add a prose warning only.
Neither guarantees that every assembled lesson refutes the rival.

**Probe:** independent mirror-only predicates, exact Racket witness
`checks/question/reflection_witness.json`, and 1,500 rotated query holdouts with
zero ambiguity.

**Limit:** chirality is always pedagogically explicit, which is diagnostic but
not frequency-calibrated.

## D6. Retain canonical support through a 3-of-4 schedule

**Original rationale:** broad generation had low official-profile support.

**Decision:** three slots per four-sample cycle use height 5, canonical palette
`{2,3,4,6}`, and canonical class partitions. The fourth slot broadens height,
palette, and 3+1 relations. Difficulty changes size/height schedules but not
validity.

**Alternatives:** make all samples exact canonical clones or broaden every slot.
The first encourages template memorization; the second weakens distribution
anchoring.

**Probe:** exact 9/12 strict samples per band in focused tests and final profile
floor green in every band.

**Limit:** strict support is structurally linked rather than a statistical model
of canonical frequency.

## D7. Reserve color 8 and make color irrelevant

**Original rationale:** legacy sampling could use any nonzero color even though
8 denotes positive relations in the output.

**Decision:** generated inputs use four distinct colors from
`{1,2,3,4,5,6,7,9}`. Equivalent panels deliberately have different colors.

**Alternatives:** allow 8 as nuisance or reuse colors across panels. Both create
avoidable ambiguity in a compact teaching task.

**Probe:** targeted color-8 mutation, distinct-color assertions, and the
`same_panel_color` rival.

**Limit:** monochrome/repeated-color panel sets are outside the teaching domain,
although the Racket rule itself ignores colors.

## D8. Declare the finite 13-state output codomain

**Original rationale:** generic diversity lint interpreted low unique-output
ratio as possible poison.

**Decision:** declare `EXPECTED_OUTPUT_CODOMAIN = 13`, derived from 3 labeled 2+2
partitions, 4 labeled 3+1 partitions, and 6 labeled 2+1+1 partitions.

**Alternatives:** fabricate unsupported partitions or suppress the lint. Neither
is honest.

**Probe:** a test enumerates generated outputs across bands/seeds and covers all
13; final lint and defect lint are green.

**Limit:** output diversity is intrinsically finite even though input diversity
is high.

## D9. Keep validation broader than override inversion

**Original rationale:** canonical panels have unequal counts, while generated
`shape_size` overrides require equal counts to be observable.

**Decision:** `self_check` validates the rule domain independently. It invokes
`observe_overrides` only when metadata explicitly requests at least one declared
axis.

**Alternatives:** reject canonical unequal-count examples or infer axes whenever
any metadata is present. Both were observed failures.

**Probe:** all five canonical pairs with unrelated/empty metadata, exact override
round-trips, and the preserved intermediate 11/12 battery failure.

**Limit:** `observe_overrides` intentionally rejects lawful canonical inputs that
are outside the generated equal-size subdomain; `self_check` does not.

## D10. Build independent reusable review tooling

**Decision:** add `workspace/reference_probe.py` for canonical loading,
normalization, rotations/reflections, independent rivals, and observable facts;
add 38 portable task tests around it.

**Alternative:** test production helpers against themselves. That can preserve a
shared bug undetected.

**Probe:** the independent oracle matches all canonical labels and every sampled
Racket output checked by the shared gates.

**Limit:** finite rivals do not prove unique human interpretation beyond the
declared task domain.
