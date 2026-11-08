# Current notes: `a287e878de99`

## Intended rule

On a zero background, retain exactly those gray/color-5 cells with one orthogonal gray neighbor. Erase interior, branch/junction, cycle-only, and isolated gray cells. The selected canonical Racket authority is unchanged and pinned by `RULE_HASH = "d7cc9d995b63"`.

## Current generator

Version `3.0.0`; final reviewed generator SHA-256 `7094d09bf5e92160593b8bfd0eb298a778d925fe779eb9f2688504f32954396a`.

Advertised observable axes:

- `grid_h` 7..15;
- `grid_w` 8..17;
- `component_count` 2..5;
- `scene_pattern` = `path|branch|cycle|singleton`.

All legal joint overrides are constructive. Unknown or invalid controls fail loudly. Default path slots are 7×8 canonical anchors with two simple paths of sizes 2 and 5; other slots vary by difficulty.

## Teaching schedule and semantic contract

Four demonstrations are required. Consecutive indices cycle through path, branch, cycle, and singleton profiles. The schedule is designed so arbitrary query rotation of a five-pair bundle remains identifiable against the declared rivals:

- `two_extrema_per_component`;
- `nonbranching_components_only`;
- `degree_at_most_one`.

The exact strongest-rival witness is `counterexamples/two_extrema_branch_singleton.json`. A reusable cyclic-start/rotation probe is `workspace/probe_curriculum.py`.

## Validation boundary

Accepted lesson inputs are rectangular 7..15 × 8..17 zero/gray grids with at most five components, at least one degree-one cell, and at least one gray cell that must be erased. A one-component lesson must have at least five gray cells; shorter isolated motifs are excluded as under-informative even though the abstract rule can label them.

## Evidence summary

- focused task tests: 12 passed;
- final battery: 12/12 green, no advisory/failure;
- strict support: 600/600; canonical accepted: 3/3;
- profile floor: exact support in every difficulty, 18/60 total;
- lesson census: 300/300 materialized, 1,500 pairs, 1,495 unique inputs, zero declared-rival ambiguity in production or all 1,500 query rotations;
- post-repair visible solve: 4/4 demonstrations passed.

See `REVIEW.md`, `DECISIONS.md`, and `checks/` in the review return for source-bound details.

## Known limits

The semantic result is finite and relative to declared rivals. Fixed profile order is intentional, though geometry and placement are randomized. The backtracking node guard has passed the exhaustive advertised override product but must be rechecked if templates or ranges change.
## Current reviewer considerations

Source SHA-256: `7094d09bf5e92160593b8bfd0eb298a778d925fe779eb9f2688504f32954396a`.

# Decisions for `a287e878de99`

## Binding interpretation

The canonical transformation is local and color-specific for this task: on a zero background, retain a gray/color-5 cell exactly when it has one orthogonal gray neighbor; turn all other cells into zero. I did not alter the Racket authority or canonical ledger. `rule_mirror` is an independent Python transcription used for generator assertions and task tests, while final counterexample labels were also checked through the canonical Racket runner.

## Reversed baseline choices

### 1. Simple paths only → topology-complete teaching support

**Prior choice:** ordinary generation used only separated nonbranching paths. The likely rationale was ease of construction and a direct visual match to the canonical examples.

**Problem:** this made the intended local predicate observationally equivalent to stronger component-level shortcuts: “keep two endpoints/extrema per component” and “solve only simple path components.” It also did not distinguish `degree == 1` from `degree <= 1` because isolated cells were absent.

**New choice:** retain canonical path anchors but schedule four scene profiles: `path`, `branch`, `cycle`, and `singleton`. Branch and cyclic-with-tail components refute component-level endpoint shortcuts; isolated cells refute `degree <= 1`. Branch and cycle scenes deliberately include an isolated component as well, so a rotated four-demo lesson still contains enough evidence when the nominal singleton profile is held out.

**Rejected alternatives:**

- Merely lengthening or bending paths: still leaves every component with exactly two endpoints and does not distinguish the component shortcut.
- Adding only branches: refutes “two endpoints” but does not independently establish that isolated cells must be erased.
- Adding only isolated cells: refutes `degree <= 1` but leaves the strongest component-level shortcut intact.
- Randomly hoping rare counterexamples appear: does not guarantee teachability in each exported lesson.

## Lesson assembly

`EXAMPLES_NEEDED = 4`. `schedule_profile` cycles through all four profiles by `sample_index % 4`, so every consecutive four-example window contains one of each profile. Production lessons are ordered consecutive draws, but downstream assembly may rotate which of five labelled pairs is the query; therefore the contract is written to support arbitrary single-query rotation rather than relying on one privileged query position.

Evidence:

- the focused test checks 16 cyclic starts per band;
- `workspace/probe_curriculum.py` checks all five query positions for those starts (240 rotations total);
- the source-bound census materialized 300 lessons and checked all 1,500 query rotations with zero declared-rival ambiguity.

This is not a universal induction proof. It is a finite check against the three named rivals over the production sampler and retained lesson bundles.

## Canonical-profile support

Every scheduled path slot with no overrides is a 7×8 canonical anchor containing two separated simple paths of sizes 2 and 5. This choice preserves a substantial, exact canonical-size/palette footprint while the other three slots supply semantic counterexamples. The profile-floor gate measured exact support in all bands: 8/20 easy, 5/20 medium, and 5/20 hard.

I rejected making every profile canonical-sized because that would unnecessarily reduce geometric diversity and make five-component override construction more crowded. I also rejected making path anchors stochastic in shape/count because profile-floor support should be guaranteed, not left to chance.

## Advertised controls

The public axes are only:

- `grid_h`: 7..15;
- `grid_w`: 8..17;
- `component_count`: 2..5;
- `scene_pattern`: `path|branch|cycle|singleton`.

All four are observable from the returned grid. Unknown controls and invalid values fail loudly. There are no declared incompatible combinations: a deterministic backtracking placer realizes the full Cartesian product, including each topology with five separated components on the minimum 7×8 canvas. The public override gate exhaustively checked the declared product; the retained fast probe checks a 128-case boundary matrix.

I removed the old fake or alias axes instead of preserving compatibility with controls that did not correspond to observable variation. A smaller honest API is preferable to a large silent one.

## Geometry and placement

Shapes are compact templates with all rotations/reflections available. The placer sorts harder/larger components first, shuffles deterministic candidate lists from the keyed layout RNG, enforces non-overlap plus one orthogonal-cell separation, and backtracks. This makes tight global overrides constructive rather than retry-dependent.

The cycle profile uses a 2×2 cycle with a two-cell tail. A pure 2×2 cycle would have no surviving cells and would violate the lesson requirement that each input contain both preserved and erased gray cells. The tail supplies exactly one degree-one witness while retaining a genuine cycle and a degree-three junction.

## Validation boundary

`self_check` and `strict_canonical_like` share structural validation: rectangular 7..15 × 8..17 grids, colors only 0/5, at most five components, at least one degree-one cell, and at least one erased gray cell. A one-component scene must contain at least five gray cells. This last boundary rejects a generic four-cell line that is lawful for the abstract rule but too weak as a standalone lesson and is outside the generator's production grammar.

I rejected allowing identity pairs, pair-only scenes, singleton-only scenes, pure cycles, blank grids, wrong colors, and ragged grids. Each is covered by `mutation_fixtures` and focused tests.

## Semantic contract

The declared plausible rivals are:

1. `two_extrema_per_component`: retain at most two representatives per component;
2. `nonbranching_components_only`: retain endpoints only for ordinary simple paths;
3. `degree_at_most_one`: retain isolated cells as well as endpoints.

All three fit all canonical demonstrations. Executable witnesses bind branching, cyclic, and isolated-cell topology to the rivals they must refute. `lesson_identifiable` first verifies lawful labels and then rejects a lesson only when a competitor matches every demonstration but changes the query answer.

The exact retained strongest-rival witness is `counterexamples/two_extrema_branch_singleton.json`, labelled by canonical Racket evidence at `checks/counterexample-a287e878de99/racket.json`.

## Color choice

The generator remains fixed to canonical foreground color 5 and background 0. I did not add color-role permutations because the selected Racket task is color-specific and there was no need to broaden palette semantics to repair the topology/teaching defect.

## Determinism and diversity

All draws flow through the keyed generator context. Repeating the same call returns identical pixels. Across 64 defaults per band, the focused tests require all four scenes, at least eight shapes, and at least 60 unique grids. The larger census observed 1,495 unique normalized inputs among 1,500 pairs.

## Known limits

- Finite declared-rival tests do not rule out every human or program-synthesized shortcut.
- The production schedule is intentionally periodic, although the geometry is not; a learner could notice profile order if sample indices were exposed externally.
- Backtracking has a 300,000-node guard. The exhaustive public override gate found no legal combination that reaches it, but future template additions must recheck the full product.
- `self_check` validates teaching grammar, not every mathematically lawful input to the Racket rule.
