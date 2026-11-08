# Working notes: f44596002946

## Baseline findings

The imported `2.2.0` generator implemented the core connection rule correctly,
but its public and training-data contracts were substantially weaker than its
metadata claimed.

- Nine axes were declared, but only `grid_h`, `grid_w`, and `n_colors` were
  actually drawn. Two singleton axes were non-controls, aliases were not
  observable, unknown keys were accepted, and the override audit produced
  7,501 findings across 98,460 draws / 1,094 cases.
- Canonical-profile support was effectively absent: 0/60 exact-profile draws
  and only 3/60 coarse-envelope draws.
- Random pair placement allowed one color's endpoint to lie on another color's
  completed segment. A pinned census measured this ambiguity in 7.8% of easy,
  26.2% of medium, and 49.4% of hard draws; at least one such case appeared in
  22.0%, 73.4%, and 94.0% of four-example lessons respectively.
- Crossing exposure was accidental rather than curricular. A four-example easy
  lesson contained any crossing only 31.8% of the time, and no schedule ensured
  both numeric overwrite directions.
- `self_check` only required one connectable pair, so it did not protect the
  full lesson grammar or the claimed axes. No task-linked semantic contract was
  declared.

## Selected design

Collapse the public contract to one categorical `scene_profile` axis whose
value is recoverable from the grid itself. Schedule four branch-complete
profiles in a fixed cycle, while using keyed randomness for colors and geometry:

1. `canonical_mixed`: three noncrossing aligned pairs with both orientations.
2. `cross_horizontal_high`: one interior H/V crossing where the horizontal
   color is numerically higher.
3. `cross_vertical_high`: the symmetric crossing where vertical wins.
4. `precondition_decoys`: one valid pair, one separated 45-degree diagonal pair,
   and one gapped aligned triple; only the valid pair transforms.

Difficulty changes the keyed layout stream but not the semantic curriculum or
canonical shape envelope. This avoids dishonest claims that easy/medium/hard
represent different rules while preventing byte-identical bands.

## Alternatives considered

### Keep independent dimensions, palette, count, density, and texture axes

Rejected. Their Cartesian product contained aliases, impossible combinations,
and values not recoverable from the returned grid. It also could not guarantee
that a four-demo training episode contained the rule-disambiguating branches.

### Preserve broad random scenes and merely reject endpoint collisions

Rejected as insufficient. It repairs one ambiguity but leaves crossing order
and negative preconditions to chance, so many episodes still support shortcuts
such as “vertical always wins,” “connect diagonal pairs,” or “connect any
aligned color with at least two cells.”

### Modify the canonical Racket rule

Rejected. The selected authority, task-local source, grammar gate, Racket
linter, execution parity, and Python mirror agree. The defect was in input
distribution and contract honesty, not the rule.

## Failure modes now guarded

- unknown or misspelled overrides;
- unobservable public-axis values;
- endpoint-on-segment overwrites;
- identity examples;
- missing crossing direction;
- diagonal-pair overgeneralization;
- aligned-triple overgeneralization;
- full-row/full-column filling;
- connecting only one pair;
- byte-identical difficulty bands;
- a four-demo lesson on which any declared rival still fits.

## Known limitations

- The generator intentionally stays at canonical scale and uses at most three
  nonbackground colors. It is optimized for clean rule identification rather
  than maximal geometric breadth.
- The negative alignment witness is a separated 45-degree diagonal. Other
  non-cardinal offsets are legal under the rule but are not separate profiles.
- Crossing profiles contain one H/V intersection. Multiple-crossing networks
  are excluded because they add overwrite-chain complexity absent from the
  canonical examples.
- `scene_profile` is the only override by design; future axes should be added
  only with exact grid-derived observation and a complete episode-level
  counterexample schedule.

## Reproducible local audit

Run:

```bash
PYTHONPATH=shared/runtime python3 generators/f44596002946/workspace/profile_audit.py \
  --seeds 100 --out generators/f44596002946/workspace/profile_audit.json
```

The report checks profile coverage, observer fidelity, endpoint safety,
self-check acceptance, uniqueness, canonical signatures, and whole-lesson
rival refutation.
## Current reviewer considerations

Source SHA-256: `5969542bb1466afceb896685f46ee5dd226d34d1ae97344b57a3cf4c245b44a6`.

# Decisions: f44596002946

## D1 — Replace nine weak axes with one observable scene profile

**Original choice and rationale:** The baseline advertised independent grid,
palette, count, density, position, and texture controls, apparently to maximize
combinatorial variety. Several had no implementation, were aliases, or had only
one possible value; the original rationale was otherwise not recorded.

**Decision:** Expose only `scene_profile`, with four complete semantic scene
types. Recover its exact value from the returned grid.

**Alternatives considered:** Repair every existing axis; keep aliases for
backward compatibility; expose separate shape, color-count, crossing, and
decoy axes.

**Why selected:** Independent axes create a large invalid or semantically weak
Cartesian product and do not guarantee a useful four-demo lesson. One complete
profile axis is exact, replayable, and testable.

**Probe/evidence:** Baseline override audit: 7,501 findings. Repaired strict
override audit: 450 draws / 5 cases / 3 bands, zero findings, unknown key
rejected.

**Failure mode/limitation:** Fewer user knobs. Any future axis must be exactly
observable and must preserve a complete lesson schedule.

## D2 — Use a four-slot deterministic curriculum

**Original choice and rationale:** Each color pair was sampled independently;
crossings and orientation mixtures emerged stochastically. This favored broad
randomness but did not account for episode-level teaching value.

**Decision:** Cycle through `canonical_mixed`, `cross_horizontal_high`,
`cross_vertical_high`, and `precondition_decoys`. Any consecutive four examples
cover all profiles.

**Alternatives considered:** Weighted random profiles; rejection-sample each
whole lesson until branch coverage appears; increase `EXAMPLES_NEEDED`.

**Why selected:** A residue schedule is deterministic, cheap, and invariant to
the lesson's starting sample index. Four examples are enough to cover all
identified competitors without increasing training sequence length.

**Probe/evidence:** Every scheduled four-demo lesson is identifiable in tests;
semantic gate measured 12/12 identifiable lessons across easy/medium/hard.

**Failure mode/limitation:** The profile order is predictable. Geometry and
colors remain keyed-random, so examples do not repeat.

## D3 — Match canonical shape/palette signatures exactly

**Original choice and rationale:** The baseline widened grids by difficulty
(6×7 through 16×18) and varied one to six colors, likely to increase surface
variety.

**Decision:** Restrict generated signatures to `(8,10,4)`, `(9,9,3)`, and
`(7,11,4)`, the signatures present in the retained canonical task.

**Alternatives considered:** Keep the broad shape ranges; use only the single
most common canonical shape; add canonical shapes as a minority prior.

**Why selected:** The baseline produced 0/60 exact-profile examples. This task
needs semantic branch coverage more than extrapolation to much larger line
networks. Exact signatures reduce distribution shift while three shapes still
avoid shape locking.

**Probe/evidence:** Profile support improved from 0/60 exact and 3/60 envelope
to 60/60 for both. Diversity remains 100% over 300 battery pairs and 1,200
local-census pairs.

**Failure mode/limitation:** It does not train large multi-line networks. Those
should be a separate profile family after evidence that they improve transfer.

## D4 — Forbid endpoint-on-segment intersections

**Original choice and rationale:** The baseline prevented marker-marker
collisions but explicitly allowed line crossings. It did not distinguish clean
interior crossings from one line passing through another pair's endpoint.

**Decision:** Permit only interior/interior crossings and reject any endpoint
on another connectable segment.

**Alternatives considered:** Let ascending paint order resolve endpoint cases;
keep them only in hard mode; create a dedicated endpoint-overwrite profile.

**Why selected:** Endpoint cases visually erase or overwrite an input marker in
the output, conflating “connect pairs” with “modify another pair's evidence.”
They were common rather than exceptional: 7.8%/26.2%/49.4% per draw and
22.0%/73.4%/94.0% per four-example lesson from easy to hard.

**Probe/evidence:** Regression test scans 480 default draws. The local audit
scans another 1,200. No endpoint risk remains.

**Failure mode/limitation:** The authoritative rule can execute endpoint cases,
but this generator intentionally excludes them from training.

## D5 — Teach both numeric crossing winners explicitly

**Original choice and rationale:** Colors were random and crossings accidental;
ascending paint order was documented, but no episode guaranteed evidence for
it.

**Decision:** Include one profile where horizontal has the higher color and one
where vertical has the higher color.

**Alternatives considered:** A single crossing profile with random color order;
multiple crossings in one grid; describe precedence only in metadata.

**Why selected:** One random crossing can leave an orientation-based shortcut
alive. The paired profiles isolate the actual rule: numeric color order, not
orientation.

**Probe/evidence:** The semantic gate verified 60/60 rival-disagreement checks
for both `horizontal_higher_color_wins` and `vertical_higher_color_wins`.

**Failure mode/limitation:** Each profile has one crossing. It does not teach
long overwrite chains.

## D6 — Add diagonal-pair and aligned-triple negative examples

**Original choice and rationale:** Ordinary generation created only exactly-two
aligned pairs, so the preconditions were never falsified by generated data.
The source listed degenerate textures, but they were not ordinary lesson
members and were not a coherent semantic curriculum.

**Decision:** Put a separated 45-degree pair and a gapped aligned triple beside
one valid pair in `precondition_decoys`. The true rule changes only the valid
pair.

**Alternatives considered:** Separate profiles for every invalid cardinality;
empty/identity-only examples; rely on canonical written text.

**Why selected:** One nonidentity grid teaches both negative branches without
wasting an example on a fully unchanged output. It directly refutes two
canonical-compatible shortcuts.

**Probe/evidence:** Canonical shortcut audit verified generated
counterexamples for `connect_diagonal_pairs` and
`connect_any_aligned_color_with_at_least_two_cells`.

**Failure mode/limitation:** The diagonal witness is 45 degrees only, and the
cardinality witness is exactly three cells.

## D7 — Keep difficulty semantic-neutral but layout-distinct

**Original choice and rationale:** Difficulty changed dimensions and color
counts. After canonical calibration, those broad ranges were no longer
appropriate.

**Decision:** Use the same four semantic profiles in every band, but salt keyed
layout randomness by band.

**Alternatives considered:** Ignore difficulty; invent easy/medium/hard profile
subsets; make hard mode larger.

**Why selected:** The first repaired draft correctly kept semantics constant
but produced byte-identical bands; defect lint caught this. Band-specific keyed
streams preserve diversity without claiming a different rule.

**Probe/evidence:** A test requires three distinct band layouts for every
profile. Final defect lint is green.

**Failure mode/limitation:** “Hard” does not mean a more complex rule instance;
it is an independent layout stream.

## D8 — Add strict structural and lesson-level contracts

**Original choice and rationale:** The baseline checker merely looked for one
paintable pair, likely as a minimal crash guard.

**Decision:** Validate ARC grid type, canonical signatures, allowed per-color
structures, visible gaps, nonidentity behavior, endpoint safety, exact profile
observation, canonical parity, witness claims, and whole-lesson rival
refutation.

**Alternatives considered:** Add only local assertions; depend entirely on the
shared battery; validate outputs rather than inputs.

**Why selected:** Model quality depends on what a complete lesson identifies,
not just whether each input executes. The task-local hooks make that claim
machine-checkable.

**Probe/evidence:** Strict census 600/600, canonical acceptance 4/4, witnesses
6/6, rival claims 6/6, lessons 12/12, and 15 pytest cases all pass.

**Failure mode/limitation:** Rival sets are authored, not exhaustive. New
plausible shortcuts should be added as named competitors.

## D9 — Leave canonical Racket unchanged

**Original choice and rationale:** The authority processes colors in ascending
order and connects only exactly-two row/column pairs. It already matches all
canonical examples.

**Decision:** No rule patch.

**Alternatives considered:** Special-case endpoint collisions; change crossing
precedence; broaden diagonal behavior.

**Why selected:** Grammar, Racket lint, authority sync, execution parity, and
Python mirror parity all pass. Changing the authority would alter a correct
rule to compensate for bad input generation.

**Failure mode/limitation:** The authority remains broader than the selected
training manifold; `self_check` defines the intended generated subset.
