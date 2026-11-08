# One or two rounds of orthogonal closure

This is an opt-in proposed family for `699479899861` (canonical bank task M47).
The production generator and canonical authority are unchanged. Reviewer
qualification and causal replay are preparation for owner acceptance; this
workspace does not activate training or count as native acceptance.

## Rule and parameter

`closure_rounds` is exactly the integer `1` or `2`, fixed for the whole episode.
The default `1` returns the selected canonical Racket source byte-for-byte from
`canonical.rkt`. Its SHA-256 is
`0fe01d258c1d0b1af66581419afe1708cd7070127941a85c9d9e344851a68338`.

| Setting | Transformation |
| --- | --- |
| `{"closure_rounds":1}` | Find every 4-connected red (`2`) component. Recolor and fill its bounding box green (`3`). |
| `{"closure_rounds":2}` | Perform that first pass, then discover 4-connected green components in its resulting grid and fill each resulting component's bounding box green. Stop after this second pass. |

All objects for a pass come from that pass's input snapshot. Updating the
components after each individual fill would be a different rule. On a connected
component the set of occupied rows and columns has no gaps, so the canonical
row/column Cartesian product equals its bounding box. Cells outside the painted
boxes retain their original colors.

### Why the intermediate matters

**A:** Execute red-component closure. **Intermediate:** The first-pass grid and
its newly connected green components. **B:** Recompute those green components
and fill their boxes simultaneously. Two red objects that were separate can
have touching first-pass boxes; their merged green component then has a larger
second-pass box. B therefore depends on A's actual result. Reusing the original
red components misses new green cells. This is an updated-state dependency,
with a retained protected-Racket counterfactual, rather than a color remapping.

The chain motif also keeps a third object separate at the first snapshot. The
second fill makes it touch, so a **third** pass would change the answer again.
This distinguishes exactly two passes from convergence.

## Sampled grammar and teaching

The two settings share identical inputs for the same seed/split/index. Separate
local SHA-256-derived random streams make inputs independent of both the hidden
rule and requested demonstration/query counts. Longer requests preserve each
split's prefix. No retries or silent shortened episodes are used.

Every input has zero background, no initial green, eight to ten red components,
and one to three decorative cells outside all reachable closure boxes. Four
separated regions provide:

1. A three-component chain where passes one, two, and three differ.
2. An independent merging pair, distinguishing all-component behavior from
   first-only or largest-only handling.
3. A diagonal-contact pair, distinguishing 4-connectivity from 8-connectivity
   in both discovery stages.
4. One to three independent L, plus, U, zigzag, or T shapes, varying component
   count, topology, dimensions, and position.

The first two demonstrations orient the chain in opposite row orders. This
constructively rejects both ascending and descending live-update scans, keeping
the two-demo minimum. Within those two examples horizontal reflections remain
random; subsequent demonstrations and all queries use all eight dihedral
transforms, including transposition. Independent shape dimensions and local
reflections continue to vary. The rule itself commutes with every such transform.

The minimum teaching canvas is deliberately larger and denser than the original
canonical inputs so the two-example prefix can carry these distinctions. This
separate sampler extends production's 2–4 small-component distribution; it does
not advertise new production overrides or alter the production validator.
It retains recognizable component separation, bounding-box closure, recoloring,
decoration preservation, and the canonical default's exact semantics.

| Split | Base shapes, before optional transposition |
| --- | --- |
| Demonstrations | 16×17, 18×20, 21×23, 24×27, 28×26, 29×30 |
| Queries | 17×19, 22×25, 30×30, 27×29 |

Every unordered shape is distinct, so no demonstration/query inputs can be
duplicates within an episode, even after transposition. The 30×30 profile fills
its four regions with scaled content and contacts all four boundaries; it is
not a small example placed on an empty larger canvas. The API accepts no custom
dimension override. These are sampled profiles, not every dimension in 1–30.

## Interfaces and checks

`prototype.py` exports `program(settings)`,
`generate(seed, settings, demos=3, queries=4)`, `mirror(grid, settings)`,
`components(grid, color, connectivity=4)`, `closure(grid, color=2)`,
`transform(grid, code)`, and `analyze(grid)`.

- Seeds are exact integers from `0` through `2**63-1`.
- Demonstration counts are independently `2..6`; query counts are `1..4`.
- Booleans, floats, unknown settings, and out-of-range requests fail explicitly.
- Grids are rectangular lists with exact integer colors `0..9`, bounded `1..30`.
- `generate` returns private `train`, `test`, and exact `program_solution`.
  Python labels are claims; native qualification independently executes them.
- `adapter.py` loads this adjacent prototype by exact path, avoiding a shared
  cached module name from a different family.

`rivals.py` contains independent Python predictions and standalone executable
Racket programs. The finite audit checks opposite pass count, stale original
components, three passes, convergence, 8-connectivity in either stage, global
filling, first/largest selection, fixed canonical extents, retained red, erased
decorations, skipped first pass, and both live-update scan orders. A rival
surviving demonstrations is an ambiguity only if it changes a query answer.
Equivalent one-pass rivals may survive and agree on every query.

From the **outer packet directory**, with its checked Python/Racket setup:

```bash
WORK/.venv/bin/python review.py task-tests 699479899861 \
  --phase after --out ../checks/699479899861/task-tests-new

WORK/.venv/bin/python review.py run python3 \
  generators/699479899861/workspace/parametric/audit.py \
  --out ../checks/699479899861/self-review-new
```

The audit checks 80 requests over seeds 0–19 and demo counts 2/6, then protected
Racket labels and all rivals for both settings on seeds 0/17, demo counts 2/6,
and four queries. It records source stability, exact programs/runtime identity,
sampler coverage, rival disagreement locations, and a causal case. This is
bounded finite evidence, not a proof of uniqueness against all hypotheses.

## Native inventory, qualification, and owner handoff

Current scoped evidence belongs in `evidence/current/`. The native inventory
includes both new test sources explicitly. After all executable sources and
tests are final:

```bash
WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric manifest 699479899861 \
  --evidence generators/699479899861/workspace/parametric/evidence/current \
  --include generators/699479899861/tests/test_parametric_generator.py \
  --include generators/699479899861/tests/test_parametric_projection.py \
  --reported-checks 'Replace with actual source-current checks and limitations'

WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric qualify 699479899861 \
  --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/699479899861/qualification --summary
```

Existing output directories are refused. Replacing an existing inventory requires
its exact hash via the native `--replace SHA256` guard. Native qualification
requires demonstrations alone to distinguish both declared setting programs,
executes every label, and binds the exact source/contract/runtime closure.
Source edits require fresh relevant checks, inventory, and qualification.

Use `arcpuzzles.review_witness template --match-case` with the audit's retained
causal case, then `build`, as described in the packet's `PARAMETRIC-RULES.md`.
The native helper fills bindings and replays both exact programs. Interpretations
of intermediate values remain reviewer-authored. After integration, the owner
must run the native qualification and fresh acceptance path on the exact live
source. Reviewer `ready` or `reviewer_replayed` does not replace that step.

## One-query public views for future agents

The reusable task-local exporter consumes a genuine qualification and its sibling
execution receipt. It reuses the native source/receipt validation and existing
public-byte serializer. It supports the four-query qualified episodes:

```bash
WORK/.venv/bin/python review.py run python3 \
  generators/699479899861/workspace/parametric/export_qualified.py export \
  --qualification ../checks/699479899861/qualification/qualification.json \
  --out ../checks/699479899861/sequential-public

WORK/.venv/bin/python review.py run python3 \
  generators/699479899861/workspace/parametric/export_qualified.py verify \
  --bundle ../checks/699479899861/sequential-public
```

Each `public/<visible-sha256>.json` contains only the demonstrations plus one
query input. Its name hashes its exact visible bytes. Public files are written
in hash order. Settings, seeds, programs, query answers, episode/query order,
and complete receipts remain under `private/`. The first view is identical to
the same episode's single-query projection. Changing hidden metadata, answers,
or future inputs cannot alter a current public view or its filename.

Give the model **one selected public file per turn**. The whole directory and
private manifest remain controller data; do not expose their file count or
future views. This utility does not implement a controller or training loop.
Its verification checks serialized bytes and current source-bound receipts;
it does not replay Racket or independently authenticate maliciously rewritten
receipts. It rejects stale source, mismatched receipts, invalid/duplicate inputs,
duplicate visible views, existing destinations, and modified public inventories.
