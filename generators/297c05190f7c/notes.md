# Working notes: 297c05190f7c

Imported associated notes retain original evidence/timestamps in
`evidence/associated_notes.jsonl`.

## Review 2026-10-02 — round 1, assignment review-95f5097f68aaf5c1

The 2.0.0 baseline passed the full battery, but an independent geometry probe
found a semantic coverage gap. At minimum 8x9 overrides, all 900 sampled
baseline attempts (seed 0..99, three difficulties, three profiles) were
consistent with both of these rivals:

1. complete only components whose bounding box lies near an outer corner;
2. complete only components whose maximum bounding-box extent is at most 3.

Both rivals also fit every canonical pair. Version 2.1.0 scatters objects in
`canonical_pair` and `component_split`; `expanded` guarantees an interior L and
one irregular 4x4 bounding box. Exact source hashes, denominators, and first
counterexamples are retained in `checks/distribution-before.json` and
`checks/distribution-after.json`.

## Review 2026-10-02 — round 2

A broader independent candidate miner exposed a second distributional bias in
2.1.0. Five rules still fit all three canonical pairs and all 900 sampled 2.1.0
attempts (300 unique inputs): complete only components that are thin, acyclic,
hole-free, at most 5/6 dense in their bounding box, or at most eight cells.
The common cause was that every changing component in the sampled curriculum
belonged to the same sparse, tree-like shape family.

Version 2.2.0 replaces the expanded profile's sparse 4x4 template with fixed
near-solid 4x4 templates containing an enclosed hole. Under every allowed D4
transform the selected component is nonrectangular, has more than eight cells,
has density greater than 5/6, contains a full 2x2 block, contains a 4-neighbor
cycle, and contains an enclosed background hole. Five executable rivals and one
composite semantic witness were added. In the paired source-hashed audit, the
five surviving shortcuts changed from 0/900 disagreements on 2.1.0 to 300/900
each on 2.2.0, and no candidate in the ten-rule library survived the final
sample. See `checks/shortcut-miner-before.json` and
`checks/shortcut-miner-after.json`.

The Racket authority, canonical rows, public axes, profile schedule, and
`RULE_HASH` were not changed.

## Review 2026-10-02 — round 3

A wider executable search over 127 candidate rules found 60 canonical-fitting
survivors in version 2.2.0. The apparent diversity reduced to two missing
boundaries: changing objects were never simultaneously sparse, deep, and
elongated, and same-color groups remained easy to recognize by equality,
diagonal contact, or large separation.

Version 2.3.0 adds three attributable counterexample families without changing
the rule or public axes:

1. `canonical_pair` schedules a sparse 6x8/8x6 L with fill gain 35 and a
   missing box cell at Manhattan distance 5;
2. `component_split` includes a 2x8/8x2 irregular object;
3. `expanded` uses a 23-cell near-solid holed 5x5 object and a close,
   non-diagonal, unequal same-color companion.

Eight named rivals were promoted into the selected source and independent
miner: one-step Manhattan fill, fill-gain-at-most-four,
density-at-least-five-ninths, aspect-at-most-three-halves,
area-at-most-sixteen, component-size-at-most-fifteen,
extent-at-most-three-or-square, and a conditional largest-per-color rule. All
eight fit the canonical pairs and survived all 900 sampled 2.2.0 attempts. The
same source-hashed controls refute all eight in 2.3.0; a separate 127-candidate,
300-grid balanced search reports zero survivors.

The first full battery exposed one useful overcorrection: every candidate
2.3.0 grid initially had a largest component of at least nine cells, while the
canonical median is four. A failing regression was added before the fix.
`canonical_pair` now alternates the large sparse object with a seven-cell 3x5
L. The small branch keeps the key one-step, density, gain, aspect, and extent
counterexamples, restores canonical-size reachability, and preserves every
sliding three-profile lesson. The strict defect lint is clean after this repair.

The Racket authority, canonical examples, selected rule, profile names,
override axes, schedule, and `RULE_HASH` remain unchanged.
## Current reviewer considerations

Source SHA-256: `c750a60ea8f1d6f1033a5df1108e91dc12fa38f95dde7261fcd4a22adb146c62`.

# Decisions for 297c05190f7c

## D1 — Preserve the rule authority and public interface

**Choice.** Keep the canonical Racket program, canonical data, base solution,
`RULE_HASH`, profile names, public axes, component definition, and period-three
schedule.

**Why.** Every authoritative stage was already green. Both review rounds found
teaching-distribution ambiguity, not a mismatch in rule execution.

**Alternatives rejected.** Changing the rule or adding an axis would not address
an observed authority defect and would create avoidable integration risk.

## D2 — Put a non-corner object in every profile

**Choice.** The 2.1.0 repair uses deterministic non-overlapping anchors so every
profile has a nonrectangular component outside the public-corner region.
`expanded` also has a genuinely interior L.

**Why.** The original generator and all canonical pairs admitted a
corner-components-only rule. Refuting location dependence in every profile is
clearer than making it a rare exception.

**Alternatives rejected.** Unconstrained random placement could miss the
lesson; adding only a rival without changing generation would correctly fail
the gate but would not repair the curriculum.

## D3 — Add scheduled 4x4 support rather than enlarge every profile

**Choice.** Keep `canonical_pair` and `component_split` close to public scale,
while `expanded` contains one irregular component spanning a 4x4 box.

**Why.** This is sufficient to refute extent-at-most-3 without reducing the
strict-canonical fraction. The period-three curriculum guarantees exposure.

**Alternatives rejected.** Enlarging every profile would move the entire
curriculum away from the public examples. Random shape growth would make
minimum-size feasibility and semantic attribution less reliable.

## D4 — Retain repeated-color and connectivity lessons

**Choice.** Keep the same-color diagonal split in `component_split` and two
distant same-color corner components in `expanded`.

**Why.** Shape-family repairs must not weaken the core distinction between
same-color 4-components, a single box per color, and 8-connected color groups.

**Alternative rejected.** Giving every expanded object a distinct color would
simplify placement but weaken the per-component lesson.

## D5 — Make location and extent hypotheses executable

**Choice.** Keep `corner_components_only` and `bbox_extent_at_most_three` as
named rivals/canonical shortcuts with explicit witnesses.

**Why.** Executable competitors turn a prose intention into a sampled output
disagreement against the authoritative rule.

**Alternative rejected.** Mere geometry-presence counters are insufficient; a
large or interior component must be nonrectangular so the rival actually
produces a different complete grid.

## D6 — Retain independent, source-hashed probes

**Choice.** Keep exact 2.0.0 and 2.1.0 sources and make review probes import only
the public `generate` entry point. The probes independently reconstruct
components, intended outputs, candidate outputs, denominators, and first
counterexamples.

**Why.** Reusing `_analyze`, `rule_mirror`, or generator rival functions could
allow a shared bug to self-confirm. Source identity and exact sampling controls
are necessary for a meaningful before/after claim.

**Limitation accepted.** These are finite boundary-distribution audits, not
exhaustive proofs over every seed. The full battery separately covers default
bands, diversity, grammar, overrides, and authority.

## D7 — Use test-first, portable task-local verification

**Choice.** Add tests before implementing each review tool/behavior, preserve
red and green logs, and run the selected test file through a disposable runtime.

**Why.** The red runs show that the tests detect the absent feature, and the
portable runner avoids relying on an unrecorded installed checkout.

**Evidence.** Round two records 4 failed/20 passed before implementation and
24 passed afterward in `checks/prior-rounds/tdd/round2-topology-red.log` and
`checks/prior-rounds/tdd/round2-focused-green.log`.

## D8 — Enumerate property-filter rivals before another manual tweak

**Choice.** Build a ten-candidate shortcut miner rather than guessing one more
shape. The library covers location, edge contact, extent, rank by size, rank by
color, thickness, graph cycles, enclosed holes, bounding-box density, and
component cardinality.

**Why.** The first review fixed two hand-selected rivals yet left five closely
related filters untouched. Enumerating a small hypothesis family made the
shared sparse-shape bias visible before editing generation again.

**Alternative rejected.** Continuing with one-off visual inspection would
repeat the same failure mode and provide no reusable search surface for future
agents.

## D9 — Cross five shape boundaries with one near-solid holed component

**Choice.** Replace the sparse large template with two fixed 4x4 near-solid
shapes containing one or two enclosed interior holes. The selected shape has
14 or 15 cells, density above 5/6, a full 2x2 block, at least one 4-neighbor
cycle, an enclosed hole, and extent 4 under every D4 transform.

**Why.** One scheduled object simultaneously refutes thin-only, acyclic-only,
hole-free-only, low-density-only, small-component-only, and the previously
known extent-limited rule while preserving easy causal attribution.

**Alternatives rejected.** A ring can supply a hole and cycle but need not cross
the full-2x2 or density thresholds. A thick notched shape can cross thickness
and density but need not contain a hole. Random dense masks make connectivity
and D4 invariants harder to guarantee.

## D10 — Use one composite witness but five separate rivals

**Choice.** `shape_topology_density_invariance` fires only when one component
crosses all five new boundaries; its claim lists all five executable rivals
separately.

**Why.** A composite witness keeps the curriculum condition attributable, while
separate rival outputs ensure no individual hypothesis is hidden by an
aggregate score. The semantic gate reports 60/60 disagreements for each rival.

**Alternative rejected.** Five duplicate witnesses would add noise without
increasing generated support because all five properties intentionally co-occur
on the same expanded object.

## D11 — Preserve schedule and axes instead of adding a new profile

**Choice.** Upgrade the existing `expanded` profile rather than adding a fourth
profile or a new public shape-complexity axis.

**Why.** Every three-example lesson window already includes `expanded`; changing
the profile count would alter scheduling and potentially the public object-count
axis for no semantic gain.

## D12 — Define completion as zero survivors in the declared library

**Choice.** The round-two acceptance criterion is: all ten candidates fit the
canonical pairs, none survive the final sampled curriculum, focused tests pass,
and the authoritative battery remains green.

**Why.** This criterion is source-bound, reproducible, and stronger than merely
asserting that the new shape “looks different.” It does not claim that the
finite library exhausts every possible shortcut.

# Round-three decisions

## D13 — Search a parameterized rival family before adding another shape

**Choice.** Broaden shortcut discovery from ten hand-written candidates to 127
executable rules spanning fill distance, gain, component size, box area, extent,
density, aspect ratio, color predicates, scene ranking, per-color conditionals,
row/column closure, and cavity filling.

**Why.** Adding another visually unusual object without first identifying the
remaining equivalence class would repeat the failure mode from rounds one and
two. The broad report showed that 60 survivors collapsed into a few common
boundaries, allowing three targeted scene changes instead of dozens of special
cases.

**Alternative rejected.** Random-mask fuzzing can increase visual diversity but
makes it difficult to attribute which semantic distinction eliminated a rival.
Pure visual inspection also cannot demonstrate that a complete executable rule
fits every canonical pair.

## D14 — Promote eight representatives, retain the broader search as evidence

**Choice.** Put eight clear, named rivals into selected generator code and the
independent task-local miner; keep the 127-rule search report as review evidence.

**Why.** The eight representatives cover each root cause with readable semantics
and stable tests. Threshold variants such as gain≤5, gain≤6, and gain≤7 are not
independent teaching requirements once a stronger high-gain witness exists.
Keeping all 127 in production code would obscure the curriculum and increase
maintenance cost without adding a distinct boundary.

## D15 — Use a sparse 6x8 L for fill depth, density, gain, and area

**Choice.** The large `canonical_pair` branch uses an L occupying the top row and
one side of a 6x8 box: 13 cells, area 48, fill gain 35, density 13/48, and maximum
missing-cell Manhattan distance 5.

**Why.** One object simultaneously and transparently crosses the four missing
scalar boundaries and the “extent≤3 or square” hybrid. D4 transforms preserve
all properties. Its cells form an unmistakably connected object, avoiding
ambiguity about segmentation.

**Alternatives rejected.** A random sparse polyomino would need repeated
connectivity checks and could accidentally raise density or shorten fill depth.
A hollow ring is deep but dense and square. A long 2-row L is elongated but all
missing cells are one step from the object.

## D16 — Keep aspect ratio attributable with a separate 2x8 object

**Choice.** `component_split` pairs its canonical diagonal-split motif with a
2x8/8x2 L.

**Why.** The 6x8 deep object has aspect 4:3 and therefore cannot refute an
aspect≤3:2 shortcut. A 2x8 L gives a direct aspect witness while retaining the
existing per-color and 4-versus-8-connectivity lesson in the same profile.

**Alternative rejected.** Making the sparse object both deep and extremely
elongated would require a still larger box, pressure minimum dimensions, and
worsen canonical-scale drift.

## D17 — Defeat conditional per-color grouping with a close unequal pair

**Choice.** In `expanded`, the dense 23-cell 5x5 object shares its color with a
three-cell incomplete L placed at Manhattan distance 2 or 3. The pair is
non-diagonal and differs in both size and fill gain.

**Why.** Earlier same-color pairs were either equal-size diagonal motifs or far
corner objects. A rival could safely process all objects only in those easy
cases and otherwise select the largest per color. The new pair removes every
condition in that shortcut while preserving non-overlapping boxes.

**Alternatives rejected.** Merely changing the second object's size leaves the
“far” condition intact. Moving equal objects closer leaves the equal-size
condition intact. Overlapping boxes would introduce output conflict semantics
not supported by the authority.

## D18 — Raise the dense witness to 23 cells instead of adding a fourth profile

**Choice.** Replace the round-two 4x4 near-solid object with a 5x5 object missing
two internal cells.

**Why.** It preserves the full-2x2, cycle, hole, and high-density evidence while
crossing both area 16 and component size 15. Reusing `expanded` keeps the public
profile count, object-count observability, and period-three schedule unchanged.

**Alternative rejected.** A fourth profile would require a longer lesson window
or weaken the guarantee that every three demonstrations collectively refute all
named competitors.

## D19 — Treat the battery's scale warning as a real regression

**Choice.** Stop after the first candidate battery failed `defect_lint`; add a
regression and restore a canonical-scale branch instead of suppressing or
reclassifying the warning.

**Why.** Canonical maximum component size has median four, while the candidate
range was `[9,23]`. The new seven-cell branch brings the generated lower envelope
close enough to the public examples and improves curriculum continuity. The
warning exposed an actual side effect of adversarial hardening: extreme examples
had displaced ordinary ones.

**Alternative rejected.** Increasing the detector tolerance or recording the
warning as “expected” would preserve a known support gap. Shrinking every new
object would reopen the very shortcuts the round was meant to close.

## D20 — Use a scheduled 3x5 seven-cell L as the compact branch

**Choice.** Every alternate `canonical_pair` occurrence uses a 3x5/5x3 L of
seven cells. The branch is determined from `sample_index`; it is not a new
public override axis.

**Why.** Seven cells are within the battery's canonical-coverage tolerance, yet
the 15-cell box has gain eight, density 7/15, aspect 5:3, maximum extent five,
and missing cells more than one step from the object. It therefore preserves
the key one-step, density, gain, aspect, and extent discriminators. The other
two profiles retain the area>16, size>15, and same-color grouping witnesses, so
every sliding three-profile window remains identifiable.

**Alternatives rejected.** A 2x4 or 3x3 object is closer to canonical size but
cannot jointly cross the density, aspect, gain, and extent boundaries. Making
the compact/large choice random could leave a small finite audit with no compact
sample; the period-six deterministic alternation guarantees coverage.

## D21 — Preserve the period-three public schedule

**Choice.** The compact/large alternation is internal to `canonical_pair`; the
observable profile sequence remains `canonical_pair`, `component_split`,
`expanded`.

**Why.** The object-count-based `scene_profile` axis remains exactly observable,
and every three consecutive scheduled demonstrations still includes all three
semantic roles. No consumer needs a new axis or longer lesson.

## D22 — Separate paired evidence from broad evidence

**Choice.** Use the 18-rule miner for exact before/after claims under identical
900-attempt controls. Report the 127-rule search separately as a wider baseline
census and a 300-grid final stress test.

**Why.** This avoids implying that unequal broad sample sets form a paired
experiment. The exact causal claim—eight promoted rivals change from 0/900 to
positive disagreements—is supported by identical source-hashed controls. The
broader search supports discovery and residual-risk assessment.

## D23 — Define round-three completion conservatively

**Choice.** Completion requires: 39/39 focused tests, clean strict defect lint,
all 12 authoritative battery stages green, no survivor in the paired declared
library, no survivor in the final broad balanced search, a valid visible-only
solve record, and a package that passes the repository's static full-return
validator.

**Why.** No individual signal is enough. Tests alone can mirror implementation;
a miner alone can miss contract regressions; a green battery can miss a novel
shortcut; and a valid ZIP does not establish semantics. The combined criterion
provides independent checks without claiming exhaustive proof.

# 2026-10-25 native parametric review — post-fill retention

- The canonical `retention=all` setting remains byte-exact to the authority program; the ordinary generator was not changed.
- The added `largest_postfill_component` setting first fills every original component bounding box, then recomputes same-color four-connectivity on that filled intermediate and retains every maximum-area post-fill component.
- Matched lessons include same-color source components that merge only after filling, plus scenes where an unmerged object wins. This refutes pre-fill size/bbox ranking, per-color totals, always-merged, alternate-setting, and smallest-post-fill shortcuts at the declared two-demo minimum.
- The family materializes six demonstrations and four queries before prefix slicing, supports independent `demos=2..6` and `queries=1..4`, and retains a substantive 30x30 query.
- Bounded evidence: 39/39 inherited task tests, 5/5 family tests, six audit jobs with 108 protected-Racket evaluations, four authoring-preflight jobs with 32 protected-Racket evaluations, a wrong-order witness changing 44 cells, and 16 strict one-query public projections.
- Finite rival checks are not a universal uniqueness proof. Owner exact-source qualification, acceptance, and any training admission remain separate.
