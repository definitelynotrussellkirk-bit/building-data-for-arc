# Working notes: 675dcb932594, version 2.0.0

## Rule and authority

Find the union of **all shortest cardinal paths with unit step costs** from the
unique color-2 start to the unique color-3 goal through non-5 cells. Change only
qualifying color-0 cells to 8. Preserve walls, both endpoints, other zeros, and
grid dimensions. Colors are semantic constants, not exchangeable paint choices.
The selected Racket rule is the label authority; the Python graph routines are
construction and diagnostic helpers. `RULE_HASH = "1e4fa5a56660"`.

The canonical JSONL and its five labeled pairs are unchanged. The selected
duplicate base-solution `racket_target.target_code` was synchronized by removing
three full-line comments; executable rule behavior is unchanged. Review return
`review-cc66306d919dfef2` retains before/after hashes and execution parity.

## R1: Canonical-fitting shortcuts and the new distribution

The previous version's documented route alternatives did not sufficiently vary
the horizontal/vertical composition of shortest routes. Both rivals that charge
2 for one orientation and 1 for the other fit all five canonical outputs, and
neither was refuted by a 600-draw Python diagnostic of version 1.3.1 (seed 0,
indices 0..199 in each band). The original author's more specific rationale is
unknown. This result is a diagnostic census, not 600 Racket executions.

Even default indices now construct a varied rectangular ring with inward
connectors. Its two shortest routes have the same total length but different
horizontal/vertical move counts; an unused longer corner separates shortest-path
union from reachable-region painting. Translation, reflection, size, connector
depth, and endpoint order vary. Start/goal placement on this family explicitly
refutes the fixed `(1,1)` start and right-column goal shortcuts as well.
Odd indices produce irregular random mazes with guaranteed connected markers;
disconnected zero distractors are allowed. These mazes broaden the topology
beyond the structured teaching family.

The semantic schedule has period 2. Default lessons use four demonstrations and
one query; five consecutive draws contain at least two rich tradeoffs before
sampler rejection/duplicate handling. Holding out any one pair leaves a rich
demonstration. The retained production census uses the actual sampler and checks
all query positions, rather than assuming consecutive requested indices are
always accepted. It found no ambiguity against the 16 distinct declared rivals
in 300 lessons / 1,500 rotations, with 1,446 unique inputs. Enumerating both
semantic starts at seed 0 across all three bands also passed: 6 lessons and 30
rotations. These are finite-rival observations, not universal identifiability.

The final 600-draw diagnostic (the same seed/index/band range) refutes each
weighted rival on 300/600 draws, with 200 distinct inputs in each band. Every
rich draw in the bounded regression sweep refutes all declared competitors.
See `workspace/maze_probe.py` and `counterexamples/step_cost_tradeoff.json`.

## R2: Honest controls, validator, and canonical support

Only `grid_h` and `grid_w` remain public override axes, each an exact Python
integer in 5..24, independent of difficulty. Unknown controls, booleans, strings,
floats, and out-of-range dimensions are rejected. Old inert palette/position
controls and invalid degenerate textures were removed rather than silently
accepted. This API narrowing is intentional and is why the version is 2.0.0.
There are no incompatible combinations of the two advertised axes.

The validator checks the returned pixels: rectangular integer grids, the fixed
0/2/3/5 palette, a complete color-5 perimeter, exactly one endpoint of each kind,
at least one zero, and connected endpoints at distance at least two. Texture
metadata cannot bypass these checks. The strict canonical-like hook additionally
requires a single nonwall component and an unused zero, as in all five canonical
inputs. This is a morphology check, not an exact-shape check.

Half the default indices use a jointly selected actual canonical shape in every
band; the other half explore the broader supported dimensions. The size mixture
has period 4, separately from the period-2 semantic schedule. Rich defaults need
both dimensions at least 6; canonical height 5 remains available on maze draws.
An explicit axis of 5 is honored by falling back to a generic maze, so lessons
with such overrides do **not** inherit the default rich-schedule guarantee.
The public after battery observed 27/60 exact canonical profiles, and its strict
hook accepted 417/600 generated inputs plus all five canonical inputs.

## R3: Small-maze construction regression

The first repair could select the center of a three-cell component as the start,
leaving no goal at distance at least two. Seed 93, index 1, dimensions 5x5 exposed
the failure. The sampler now switches to a neighboring vertex when necessary;
the bipartite cardinal grid guarantees a nonadjacent peer. Four focused cases
cover `None`, easy, medium, and hard. The real failing run is retained in the
review's `checks/small-maze-regression-red.log`.

## Verification and limits

The repair passed all 12 battery stages, the 810-draw exact-override matrix,
188 generator regressions, and three probe tests. The isolated task-test stage
passed all 191 tests without skips. Test code locates canonical data and staged
sources through public `reviewer_support` helpers. Review reports retain exact
commands, source hashes, the original failures, and the final-patch replay.

The rich family still has a recognizable ring-and-connectors topology; an
undeclared specialized rule could exploit it. Random maze draws reduce this
restriction but the finite rival census cannot rule out every alternative.
Difficulty changes generic-maze occupancy, not a demonstrated monotone measure
of solver difficulty. Five-cell overrides and arbitrary lesson sizes are not
covered by the default lesson guarantee. Approval and training admission remain
maintainer decisions; passing diagnostics does not grant either.

The review's unrelated archival-fixture failure is documented in `F1` and
reproduced on the pristine packet. No unresolved task-local gate failure remains.
The two assigned external audits are retained in that review's `AUDIT.md` and do
not alter their target sources. Imported historical notes remain in
`evidence/associated_notes.jsonl` with their original timestamps and provenance.
## Current reviewer considerations

Source SHA-256: `ee5d87667e2d46d94fa721324c5ec3e7478cc9a96062fb4cafbf3c8424100670`.

# Decisions for 675dcb932594

## Objective and starting evidence

The goal was to make generated lessons teach the selected canonical shortest-path
union rule, while repairing the control and validation contract. The baseline
version was 1.3.1, SHA-256
`6ae8af70f7040f53718715605045f065b073e17aba6faf86e5cfd0d74ed20999`.
The final version is 2.0.0, SHA-256
`ee5d87667e2d46d94fa721324c5ec3e7478cc9a96062fb4cafbf3c8424100670`.
Assignment `review-cc66306d919dfef2` and both random audit targets were retained.

The original text mentions a direct path and longer alternate path, and advertises
multiple combinatorial controls. A more detailed original design rationale was
not present, so it is unknown. The before battery independently found four failed
stages, inert controls, exact-size mismatches, invalid degenerate textures, no
semantic contract, and comment-only authority drift (`checks/before/`). The
baseline diagnostic found no separation of either orientation-weighted rival in
600 draws (`checks/semantic-review/baseline-coverage.json`). This motivated a
distribution repair rather than a label-rule change.

## R1: Explicit equal-cost route tradeoffs

**Prior choice:** direct and alternate corridor routes. **New choice:** alternate
a structured teaching family and irregular mazes. Merely having two shortest
routes is insufficient: routes with identical horizontal and vertical counts
also tie under orientation-weighted costs. A correct teaching example needs two
shortest routes whose move-count signatures differ.

For rectangle spans H and W, place an endpoint k cells inward from a corner and
connect it to the adjacent perimeter sides. The routes to the opposite corner
have signatures `(H+k, W-k)` and `(H-k, W+k)` when written as vertical/horizontal
move counts. Both have unit length H+W, while either orientation-weighted cost
favors one. The unused corner path is longer and preserves zeros, separating
shortest-path union from painting every reachable zero. Translation, reflection,
rectangle dimensions and k vary. Endpoint order is chosen so the rich input also
contradicts the canonical start-at-(1,1) and goal-at-right-column assumptions.

The exact 6x6 generated witness, actual Racket output and all five canonical-fitting
rival predictions are in `checks/weighted-witness/` and the source-patch
`counterexamples/step_cost_tradeoff.json`. A no-override emitted witness is also
retained in `checks/final-counterexamples/`. Canonical fit is checked against all
five usable pairs through public helpers, not inferred from appearance.

| Alternative considered | Decision and reason |
| --- | --- |
| Keep the old corridor sampler and add a semantic hook | Rejected: an executable hook cannot manufacture a missing teaching example; the baseline diagnostic actually found zero weighted-cost refutations |
| Use only generic random occupancy | Rejected as the sole source: it does not guarantee a cost-tradeoff example in each bounded lesson |
| Use only a fixed small teaching grid | Rejected: would create a trivial geometric signature and poor diversity |
| Transform one rich topology on every draw | Rejected as the entire distribution; retain it for half the draws and use irregular mazes for breadth |
| Change canonical labels or relax the intended unit-cost rule | Rejected: the canonical outputs and selected rule agree; the defect is teaching coverage |

Sixteen distinct executable rivals cover weighted costs, endpoint assumptions,
single-path selection, shortest-path intersection, diagonal adjacency, endpoint
painting, open/reachable-region painting, identity, a wall-blind rectangle, and
omitting each cardinal direction. Five fit all canonical pairs. The declarations
share callable implementations where appropriate and are dynamically traversed
by the tests and probe. The finite set is a falsifiable check, not a proof that
no other rule explains a lesson.

## Lesson assembly and cyclic starts

`EXAMPLES_NEEDED = 4` is retained. Ordinary assembly is four ordered demonstrations
and one query. The semantic schedule is period 2: tradeoff at even indices, maze
at odd indices. Five consecutive requested draws contain two or three tradeoffs;
any one-pair query rotation leaves at least one. Since production may skip rejected
or duplicate draws, this combinatorial argument is supplemented with actual
production-sampler evidence rather than treated as sufficient by itself.

The required-rotation after battery passed 12 lessons and 60 rotations. The larger
source-bound Racket census passed 100 lessons per band (300 total), 1,500 rotations,
and 1,500 labeled pairs containing 1,446 unique inputs. Its index is 0..99 per
band, with seed `sha256('lesson-census:v1:TASK:BAND:INDEX')[:8]` interpreted as a
uint32; each report retains the actual accepted sample indices. The separate
schedule enumeration uses seed 0 and both starts in each band: six lessons,
30 rotations and nine unique inputs. It enumerates the **declared semantic
period at that fixed seed**, not all seeds or all size-mixture residues.

The size mixture has period 4 and the semantic profile has period 2. This is an
intentional distinction: a semantic schedule need not reproduce exact dimensions
on every cycle. Explicit 5-cell dimensions use generic mazes, so their lessons
are outside the default schedule guarantee. Arbitrary demonstration counts,
multiple-query layouts and undeclared rivals remain unverified.

## R2: Dimensions and canonical morphology

All five canonical shapes are retained as joint shape choices: 5x11, 6x12, 7x11,
8x13 and 7x13. Half the default indices in each difficulty band draw a canonical
shape; the rest use a broader size range up to 24x24. Rich defaults require both
dimensions at least 6, so the 5x11 canonical profile occurs on generic-maze draws.
The joint choice avoids independently combining canonical heights and widths into
pairs absent from the original examples. No canonical grid is copied wholesale.

The old difficulty-specific defaults caused legal endpoint overrides to be
rejected. Default difficulty choices are now separate from the exact override
contract. Both public dimensions accept any Python integer in 5..24 in every
band, including joint corners of the domain. For a dimension of 5, preserve the
requested dimensions and construct a generic maze. Rejecting such controls or
silently enlarging the grid would violate the advertised contract.

The generic maze changes open-cell density by difficulty, but no monotone solver
difficulty claim is made. The dedicated teaching family is present in every band;
hard examples do not sacrifice canonical support merely by being larger.
The public profile floor observed 9/20 exact hits in every band. The custom strict
hook accepts all canonical inputs and checks connected nonwall morphology plus
an unused zero, not size. It accepted 417/600 draws in the semantic battery.

## R2: Controls and lawful domain

| Prior surface | New decision | Why |
| --- | --- | --- |
| Exact `grid_h` / `grid_w` declared 5..24 but clamped or rejected by band/texture | Honor exact bounds across all bands and joint cases | Overrides must be observable and honest |
| Palette, anchor, position and asymmetry controls without consistent effects | Remove them; reject unknown keys | Fixed symbolic colors are not interchangeable, and accepting inert switches misleads callers |
| Invalid degenerate textures mixed into ordinary valid textures | Remove them; reject legacy texture requests | Missing endpoints or corridors do not satisfy this task's ordinary domain |
| Texture metadata could bypass `self_check` | Always validate the returned grid itself | Labels and downstream safety depend on pixels, not claimed intent |
| Loose shape/type and endpoint checks | Validate rectangular integer grid, fixed palette, full wall frame, unique markers, zeros, connectivity and distance >=2 | Prevent malformed or trivial examples without hiding sampler defects |
| No rule hash pin | Pin `1e4fa5a56660` after rechecking canonical parity | Keep teaching claims tied to the actual authority |

The two remaining public axes have no incompatible combinations. `None` means
default selection; booleans, floats and strings are not coerced to dimensions.
This narrows the public API intentionally, so the version is bumped to 2.0.0.
Callers relying on removed legacy controls must stop supplying them. The
strict-canonical hook is narrower than the lawful domain: disconnected zero
distractors are lawful and remain unpainted, though not strict-canonical-like.

## R3: Preserve and fix the actual intermediate failure

The first repair passed 184 tests, then a bounded 5x5 stress probe found seed 93,
index 1 failing in all three named bands. Random start selection landed at the
center of a three-cell component, so every other cell was adjacent and the legal
goal candidate list was empty. Four new cases, including difficulty `None`, first
failed and then passed after selecting a neighboring start when needed. The
cardinal grid has no triangles, so that neighbor has a nonadjacent peer in the
guaranteed component. The fix needs no rejection loop or dimension override.

The initial test failure (128 failed / 56 passed against the original generator),
first green run (184 passed), four-case intermediate red run, and final green run
(188 passed) are retained in separate logs. The first repair's source hash is
`350b62953564a2f6e2cb59c53c5724edc99c6eb90a1499c69d83cb6910a7823a`.
The reusable probe has three additional tests, giving 191 in the isolated task
stage. This history records actual failures; no artificial failed solve was added.

## Authority synchronization without a semantic change

The canonical ledger is untouched. The selected base-solution JSON differed only
by three full-line comments in `racket_target.target_code`. Removing those comments
made the active authorities exactly match and resolved the source divergence.
No archival source or other JSON field changed. The selected normalized hash went
from `182165f83fa7` to the canonical `1e4fa5a56660`; raw text SHA prefixes are a
different hash convention and are labeled separately in
`checks/authority-normalization.json`. Both before and after execution-parity
checks agreed. This is recorded as an authority-text edit, not concealed as
"no Racket file change."

## Reusable tools and evidence boundaries

`workspace/maze_probe.py` uses an independent BFS predecessor DAG to calculate
the output union, number of shortest routes, and possible move-count signatures.
It discovers its own checkout through public helpers, binds reports to source
hashes, refuses output overwrites, records exact sample ranges, and traverses the
actual generator declarations. This helps a future reviewer add rivals without
forgetting to update a copied name list. Its 600-draw run is explicitly Python
diagnostic evidence; Racket receipts and production lesson evidence are separate.

The baseline and final diagnostic both use seed 0, indices 0..199 in easy, medium
and hard. Weighted-cost refutations improve from 0/600 to 300/600. Final per-band
uniqueness is 200/200; profile morphology, exact dimensions and strict acceptance
are separately named measurements. The current ring family remains a possible
new geometric shortcut; random mazes and endpoint variation mitigate that risk
without pretending the finite rival set settles it.

## Environment and shared failures

The default Python could import pytest through the user site, but the isolated
task runner intentionally disables that site. The first task-test attempt failed
preflight before staging any tests. A dedicated venv was provisioned offline from
the already installed package distributions; isolation stayed enabled. Package
versions, hashes and the verified interpreter are retained in
`checks/offline-test-dependencies.json` and `checks/verified-test-environment.json`.
Installed environments and dependency archives are not part of the return.

The broad repository run is reported honestly as failed. A focused rerun with
dependencies available left an unrelated archival golden-digest mismatch and a
shared test's literal comparison of equivalent interpreter paths. The archival
failure was independently reproduced on the untouched original extraction.
The path test passes when the same venv uses its normalized absolute invocation.
These are F1/F2 shared follow-ups, not reasons to rewrite frozen fixtures or
unrelated generators. No full-suite-green claim is made.

## Completion boundaries

Both solve records are finished with one genuine revision and no reference
consultation during solving. The blind episode predates repair-source access;
the post-repair episode truthfully declares earlier exposure. Hidden-query
correctness is unknown. The assigned external audits are findings-only: A1
corroborates an existing open issue; A2 is a new documented-domain coverage gap.
The exact final delta applied to a fresh original extraction after verifying
its isolated Git root, and its public isolated task-test stage passed all 191
tests again. The patch and final generator/solve hashes are bound in
`checks/replay/receipt.json`. Approval and training admission are left to the
maintainer.
