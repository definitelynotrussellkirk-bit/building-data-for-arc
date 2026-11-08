# Direction scope — task-local prototype

Status: **prototype / proposed**. The selected generator and canonical rule for
`832404dc8a5c` (`d2acf2cb`, training origin) remain authoritative. This workspace
does not introduce a production parametric API or approve a variant.

## Executed parameter

| Parameter | Values | Original/default |
|---|---|---|
| `direction_scope` | `union`, `rows`, `columns` | `union` |

All settings detect complete pairs of color-4 anchors at opposite grid edges.
`rows` activates anchored rows, `columns` activates anchored columns, and `union`
activates either. On selected cells the rule swaps `0 ↔ 8` and `6 ↔ 7` once;
anchors, other colors, and unselected cells retain their values. At intersections
the union performs one swap. The original setting retains the canonical behavior.

This changes which lanes are transformed while preserving anchor detection,
lane membership, field/marker roles, both reversible palette pairs, and grid
dimensions. It is a directional semantic change, rather than an input reskin.

The setting is chosen once from a deterministic episode seed with `choose_scope`
and then reused for every demonstration and query. An explicit `scope` is an
authoring override for demonstrations of each bounded setting. Input draws use a
separate deterministic stream and exactly the same schedule for every setting.
`load_selected_generator(..., root=find_root(__file__))` supplies the current
selected sampler, and its current digest is recorded, never pinned in tests.

## Inputs and identifiability

The prototype draws lawful 6–13 row by 8–12 column grids. The selected generator
supplies the original dense 0/6 field, paired endpoints of interior anchored
lanes, and 7/8 only inside anchored lanes. These constraints do not depend on the
parameter. The fixed three-demonstration schedule is:

1. Row-only anchors with a 7/8 lane palette.
2. Column-only anchors with a 0/6 lane palette.
3. Mixed row and column anchors with a 7/8 lane palette.

The query uses mixed row and column anchors with a 0/6 lane palette. Both
orientations occur before the query: identity on a nonselected orientation is
deliberate evidence for that direction setting. Each episode is rejected unless
executing **all three parameter settings on all demonstrations** leaves exactly
its chosen setting. `audit_demonstrations` also reports ambiguous inputs honestly;
the tests include a lane-free example where all three settings survive.

This finite check distinguishes declared parameter rivals. It does not prove
uniqueness against every possible program. The schedule is a small authoring
probe, not a calibrated production sampling distribution.

## Execute from the outer extraction directory

Python 3.12+, the packet's included Racket, and the existing runtime dependencies
are required. The focused tests also require pytest. With the review environment
used for this packet, replace `/ABS/PACKET` with the absolute outer directory:

```bash
WORK/.review/venv/bin/python review.py run /ABS/PACKET/WORK/.review/venv/bin/python generators/832404dc8a5c/workspace/parametric/prototype.py --out ../checks/parametric/artifacts --seeds 17 113
WORK/.review/venv/bin/python review.py run /ABS/PACKET/WORK/.review/venv/bin/python -m pytest generators/832404dc8a5c/tests/test_parametric_prototype.py -q
```

The output directory must be new. For the standard packet Python environment,
the equivalent exact command is:

```bash
python3 review.py run python3 generators/832404dc8a5c/workspace/parametric/prototype.py --out ../checks/parametric/artifacts --seeds 17 113
python3 review.py run python3 -m pytest generators/832404dc8a5c/tests/test_parametric_prototype.py -q
```

The wrapper selects the included Racket and runs the payload from `WORK/repo`.
Every emitted example output, witness output and rival prediction comes from
`RacketBridge.eval_text`. The program is materialized as an exact `(rule! callable)`
form; a lexical identity binding implements the host registration wrapper so the
unchanged callable can execute in Racket. There is no Python output mirror.

## Retained evidence and public boundary

The evidence command writes these paths beneath its `--out` directory:

- `public/challenge-*.json`: only demonstration input/output pairs and query
  inputs. Filenames derive solely from already-public content. No hidden seed,
  parameters, code, source hashes, private labels or query answers are included.
- `private/episode-*.json`: seed, fixed parameter, selection origin (seed or
  explicit authoring override), exact program and digest,
  selected sampler identity, input draw overrides, query outputs, and exhaustive
  finite-rival results. These files belong to the controller.
- `private/rules/*.rkt`: exact materialized Racket for every allowed setting.
- `private/witness.json`: one lawful shared input and all three executed outputs,
  including differing-cell counts for every pair of settings.
- `report.json`: source hashes, runtime identity, executed payload command,
  bounded coverage counts, canonical/default comparisons, and limitations.

Default controlled comparisons use seeds 17 and 113 for all three settings.
Three further episodes exercise selection from the seed itself: 11 selects
`union`, 2 selects `rows`, and 16 selects `columns`. Together these provide nine
complete episodes, twenty-seven demonstrations and nine queries, with 152 actual
Racket grid evaluations. The report separately counts distinct public challenges
in case user-supplied comparison seeds overlap these three seed-selected examples.
It also checks all four labeled canonical pairs and twelve selected-sampler draws
against the original canonical Racket. Tests
cover all three directions, both swaps, unchanged anchors/background, single-swap
intersections, reversible behavior, source selection, fixed episode settings,
public/private separation, deterministic reproduction, honest finite ambiguity,
invalid settings/seeds, exactly one parameter draw in both the provided-bridge and
owned-bridge entry paths, and rule execution on a 30×30 grid. The last check is a
rule-domain check only; the episode sampler stays in its declared smaller range.

The retained first failing test predates implementation and fails specifically
because the prototype entrypoint was absent. It does not claim a preexisting
semantic bug in the canonical generator. A second red run shows six failures for
missing seed-selection provenance before that metadata was implemented; both
bridge entry paths are covered. Focused prototype checks are separate
from the canonical repair's battery and task tests. No result grants production
or training admission, and bounded seed evidence is not exhaustive coverage.
