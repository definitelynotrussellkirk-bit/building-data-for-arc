# Working notes: fc41c9b3a565

## 2026-10-06 review repair

Baseline source `fa3afa431032b6678bf9ed2435985e32483d6749b573e637484144d4e5a23396`
failed lint, defect lint, and override contract; canonical-profile support was
0/60 and no semantic contract was declared.

Selected repair:

- pin canonical `RULE_HASH = 735d17bb2ca5`;
- expose only `grid_h`, `grid_w`, and exact `scene_profile` controls;
- reject unknown overrides and make every control observable;
- schedule one exact canonical-morphology anchor every five samples;
- use five-cell 3×3 point-symmetric positives and matched coarse-geometry
  single-axis/asymmetric negatives in ordinary scenes;
- add shared structural analysis, strict profile, oracle mirror, eight witnesses,
  nine rivals, and a four-demo lesson-identifiability hook;
- retain the Racket authority unchanged;
- add `workspace/semantic_probe.py` for cheap replay by future agents.

Final generator SHA-256:
`23dce83c22deae4bd08d1c08552143a1eeca2ac037b04f6467501c41b4d400c1`.
Full after battery: 12/12 green. Large lesson census: 300 materialized lessons,
0 production ambiguities, 0/1,500 rotation ambiguities, and 1,498 unique inputs.

Known limits: finite declared-rival coverage; 2–4 objects; distinct color per
component; general shapes bounded to 3×3; no exhaustive proof over polyominoes or
all possible induction programs.
## Current reviewer considerations

Source SHA-256: `23dce83c22deae4bd08d1c08552143a1eeca2ac037b04f6467501c41b4d400c1`.

# Decisions — `fc41c9b3a565`

## D1: Keep the Racket authority unchanged

**Choice.** Repair only the Python generator and teaching contract. Pin
`RULE_HASH = "735d17bb2ca5"`; do not alter the selected Racket rule.

**Original rationale.** The imported generator did not record one. The before
`rule_smoke`, `racket_lint`, and `authority_sync` stages already passed, and the
canonical program solved all three training pairs plus the held-out canonical
pair.

**Alternatives rejected.** Rewriting the Racket program would add authority risk
without addressing any reproduced defect. Treating the archival raw program as
the selected rule was also unnecessary because both executable sources already
agreed on all canonical pairs.

**Probe.** Full before/after authority stages and the four canonical-pair tests.

**Failure mode / limit.** The Python mirror is not the authority; future changes
must rerun Racket parity rather than infer correctness from `rule_mirror` alone.

## D2: Shrink AXES to exact observable controls

**Choice.** Retain only `grid_h`, `grid_w`, and `scene_profile`. Make all values
finite/exact, route them through keyed context draws, reconstruct them in
`observe_overrides`, reject unknown keys, and declare no incompatible pairs.

**Original rationale.** The imported comments described broad randomized blobs,
but the reason for advertising `n_sym`, `n_asym`, palette controls,
`position_bias`, `density`, and texture aliases was unknown. Measurement showed
that several were ignored, dead, unprobed, or inconsistent with `self_check`.

**Alternatives rejected.** Implementing every old axis would create a much larger
joint support problem and preserve unnecessary palette/texture complexity.
Marking controls diagnostic would silence enforcement while leaving misleading
public API. Keeping negative fixtures in an ordinary texture axis would continue
to emit invalid training inputs.

**Probe.** The official 7,200-draw override matrix plus boundary tests for every
height, width, profile, and difficulty.

**Failure mode / limit.** The smaller API intentionally gives up direct count and
palette controls. Add a control only when it is observable and its full joint
support can be tested.

## D3: Use an exact canonical anchor every fifth sample

**Choice.** Cycle through the three distinct linked canonical morphology
profiles every fifth default sample. Match dimensions and role-tagged normalized
shapes exactly, modulo color and translation.

**Original rationale.** The baseline generated freely but measured 0/60 exact
and 0/60 envelope support. Purely generalized data could move the model away
from the public task manifold.

**Alternatives rejected.** Canonical-only generation would preserve prototype,
size, and reflection shortcuts. A soft dimension-only anchor would satisfy the
profile envelope while still omitting canonical object morphology. A random
low-probability anchor makes small per-band support nondeterministic.

**Probe.** `strict_canonical_like`, four canonical-pair ownership tests, the
60-draw profile floor, and the 600-draw semantic census.

**Failure mode / limit.** Twenty percent is a curriculum choice, not a proven
optimum. The observed strict rate was 21.2% under the shared sampler because its
sample-index schedule is not exactly a contiguous 0–599 sequence.

## D4: Match coarse geometry across opposite labels

**Choice.** Ordinary scenes contain a kept point-symmetric-only five-cell 3×3
object and one or more erased five-cell 3×3 decoys. Decoys include left-right-only,
up-down-only, and fully asymmetric forms.

**Original rationale.** Unknown in the import. The canonical examples alone
allow several simple hypotheses: keep squares/prototypes, keep even-size or
largest objects, or conflate 180-degree symmetry with mirror symmetry.

**Alternatives rejected.** Random polyominoes without role pairing can correlate
size/aspect with the label by chance. Using only a plus or square as positive
would not distinguish 180-degree symmetry from both-axis reflection. Using only
fully asymmetric negatives would not distinguish rotation from single-axis
reflection.

**Probe.** Eight semantic witnesses, nine rivals, `_generated_quality_errors`,
and the matched-geometry regression test over seeds and all bands.

**Failure mode / limit.** General shapes are drawn from a small 3×3 bank. The
lesson demonstrates the predicate, but it does not exhaust the polyomino space.

## D5: Use four role-count profiles

**Choice.** Support 2–4 objects with profiles `(2,1)`, `(3,2)`, `(3,1)`, and
`(4,1)`, where the pair is `(object count, symmetric count)`.

**Original rationale.** The import advertised independent `n_sym` and `n_asym`,
but their implementation and joint legality were unreliable. Canonical inputs
span three- and four-object cases; a two-object case is the cheapest direct
contrast.

**Alternatives rejected.** Independent count axes would require rejecting or
supporting many combinations and larger placement capacity. A single fixed
count would encourage counting/profile memorization and narrow canonical
support.

**Probe.** Exact profile observer tests, all band/profile override combinations,
and distribution/override gates.

**Failure mode / limit.** Profiles do not include all lawful count splits, such
as four objects with two symmetric components. Expansion should add named
profiles rather than silently broadening semantics.

## D6: Keep one color per component and prevent touching

**Choice.** Draw distinct nonzero colors and place each role in a disjoint slot.
Colors may vary freely; component identity remains recoverable by monochrome
4-connectivity.

**Original rationale.** The authority operates on monochrome connected
components. The baseline summary already intended one distinct color per object,
but the exact invariant was not enforced through one shared analyzer.

**Alternatives rejected.** Reusing a color for disconnected components is lawful
under the broad authority but would complicate override observation and teach a
second grouping issue. Allowing same-color contact would merge objects and
change the rule unit. Fixed colors would create role leakage.

**Probe.** Structural analysis, disconnected-color negative test, diversity and
grammar gates.

**Failure mode / limit.** The generator does not teach grouping multiple
disconnected components of one color. That should be a deliberate extension,
not an accidental placement artifact.

## D7: Separate the teaching distribution from the rule domain

**Choice.** `self_check` requires at least one kept and one erased object, while
`rule_mirror` still evaluates all-symmetric or all-asymmetric recombinations
when their underlying objects are structurally lawful.

**Original rationale.** The baseline mixed deliberately invalid negative
fixtures into an advertised ordinary texture domain. At the same time, rejecting
uninformative lessons should not redefine the authority.

**Alternatives rejected.** Making all-symmetric/all-asymmetric samples ordinary
would produce examples with no within-grid contrast. Making the oracle reject
them would incorrectly narrow the rule itself.

**Probe.** Targeted recombination test plus defect lint.

**Failure mode / limit.** The Python analyzer still bounds ordinary object size,
count, and grid size. It is a distribution validator, not a universal ARC parser.

## D8: Make position disagreement deterministic

**Choice.** Place roles in deterministic disjoint slots, rotate/reverse role order,
and horizontally mirror the completed ordinary grid when the left-half rival
still matches the intended output.

**Original rationale.** Unknown. Position is irrelevant to the authority but can
become a shortcut if positives consistently occupy early slots.

**Alternatives rejected.** Pure rejection sampling could be seed-fragile and
harder to reproduce. Random unrestricted placement complicates non-touching
proofs and small-grid support.

**Probe.** Left-half witness in `_generated_quality_errors`, semantic census, and
determinism/global-RNG-purity test.

**Failure mode / limit.** Only one explicit positional rival is modeled. Other
spatial hypotheses (top half, scan order, nearest corner) are not exhaustively
enumerated, though slot reversal and varied layouts reduce their stability.

## D9: Require four demonstrations and test query rotations

**Choice.** Set `EXAMPLES_NEEDED = 4`. Production is four consecutive demos plus
the next pair as query. Retain diagnostic and large-census rotation checks by
holding out every position in the five-pair window.

**Original rationale.** The imported summary claimed generated examples were
broad, but supplied no executable evidence that a lesson identified the rule.
Four examples cover one anchor plus enough ordinary counterexamples across the
five-slot schedule.

**Alternatives rejected.** One or two examples allow prototype/axis hypotheses
to survive. Requiring more than four increases training context cost without a
reproduced need. Treating ordered success as proof of arbitrary rotation would
hide curriculum dependence.

**Probe.** Shared semantic smoke: 12/12 production, 60/60 rotations. Larger
census: 300/300 production and 1,500/1,500 rotations, with no named-rival
ambiguity.

**Failure mode / limit.** These results cover sampled starts and declared
competitors. They do not prove unique induction against undeclared programs.

## D10: Add a cheap task-local semantic probe

**Choice.** Add `workspace/semantic_probe.py` and a portable test for it.

**Original rationale.** Future reviewers otherwise need the full battery to
answer basic questions about strict support, profile coverage, witness firing,
and lesson rotation behavior.

**Alternatives rejected.** A one-off notebook is harder to replay and package.
Embedding all diagnostics in production generation would increase runtime and
couple authoring evidence to normal sampling.

**Probe.** Retained command produced 120 valid grids, 72 ordered lessons, and 360
rotations with zero failures; the task suite imports and exercises the tool.

**Failure mode / limit.** The tool uses the Python mirror for cheap labels. It
must be paired with the shared Racket authority checks before accepting a rule
change.

## 2026-10-25 parametric reviewer build

Added a two-setting native promotion prototype without changing the production
generator or selected authority.  The default `mode=canonical` returns the exact
803-byte canonical program (SHA-256
`735d17bb2ca5d6dd407b4fda51ce0e9942c26af622f60d8deb30fe0f823afbbe`).
The alternative `mode=largest_symmetric_highlight` first applies that canonical
filter, then selects the unique largest component in the filtered intermediate
and recolors it to 9.  A protected-Racket `wrong_order` witness selects the
largest original object before filtering and produces a different final grid.

The adapter supports 2--6 demonstrations and 1--4 queries independently.  Its
matched input banks vary colors, winner rank, geometry, placement and object
count; query slot four is a substantive 30x30 scene with exactly eight objects
and five symmetric survivors.  Bounded self-review over seeds 0--31 covered 64
episodes / 640 labeled pairs with zero recorded failures, eight winner colors,
three winner ranks and 320/320 wrong-order disagreements for the composed
setting.  Target tests passed 73/73 after staging.

Native reviewer qualification used seeds 0 and 17, three demonstrations and four
queries for both settings: 4/4 jobs qualified with 40 protected-Racket
evaluations.  Public projection verification retained 16 one-query views and
the first-turn checker passed 24 private-field invariance mutations.  Evidence
is under `checks/fc41c9b3a565/`; the source inventory is
`workspace/parametric/evidence/manifest.json`.  These are finite reviewer
results, not owner acceptance or training admission.

Known limits: the teaching grammar uses a curated connected-shape bank, distinct
colors per object, and a deliberately unique largest survivor.  It does not
prove identifiability against undeclared programs or correctness over every
possible polyomino arrangement.
