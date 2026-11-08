# Gray bridges, then smallest green component

This task-local family adds `gray_role = inert | bridge`. It is opt-in and needs
owner qualification/acceptance on the integrated source. The production
`generator.py`, its canonical Racket authority, and its approval are unchanged.

| Setting | Meaning |
|---|---|
| `inert` (default) | Exact canonical program bytes: paint the unique smallest green 4-connected component yellow; gray is unchanged. |
| `bridge` | Convert gray to green, recompute green components and their areas, then paint the unique smallest resulting component yellow. |

The prototype grammar expands beyond production's isolated-gray/corner-zone
grammar. Each gray connected path joins at least two green components. There is
a unique smallest component both before and after joining, with at least two
resulting components. Irregular polyominoes fill separated rectangular regions
throughout the canvas. Shapes can touch the canvas boundary. Nonjoining objects
are separated even diagonally; these samples do not teach 4 versus 8 connectivity.
The accepted sampler is intentionally not an unrestricted arbitrary-grid sampler.

## Teaching and sizes

`generate(seed, settings, demos=3, queries=4)` supports **3–6 demonstrations** and
**1–4 queries**, with exact integer arguments and seeds in `0..2**63-1`.
Three demonstrations teach (1) a changed winner after a merge, including gray's
contribution to area, (2) a winning merged object, and (3) an untouched winner.
Two demonstrations are deliberately unsupported: the three branch witnesses
avoid restricting query support or quietly leaving a plausible branch shortcut.
The ordinary lesson has three demonstrations and four novel queries.

The second demonstration constructs a six-cell thin merged object (perimeter 14)
and a compact seven-cell object (perimeter 12). This repairs a demonstrated
minimum-perimeter shortcut without adding a fourth demonstration. The first
demonstration also separates bounding-box size from occupied-cell count.
The finite checks include first/last/largest, fixed-size-two, bounding-box area,
perimeter, bridged-only/unbridged-only, and the other parameter setting; bridge
mode additionally checks original-anchor, gray-excluded area, wrong-order, and
gray-always-green predictions. They are lower bounds on teaching quality, not a
proof of unique inference against arbitrary programs.

The sampler chooses the first three demonstrations independently of requested
counts, query inputs, and settings. It retries geometry at most 64 times to reject
residual finite shortcuts in **both** settings. Each setting uses the same input
stream; only labels differ. Extra demonstrations and queries have separate stable
streams, so a one-query request and a four-query request have identical first turns.

Default demo sizes start at 9×10, 12×14, 18×20. The four query sizes are 12×16,
20×23, 26×22, 30×30. At 30×30 there are 16 original green components, with several
gray joins and substantial interior content. `sample_input(seed,index,height,width)`
also supports exact height/width 8–30 for boundary probes. **These are prototype
controls; no production size override has been added or validated.**

## Run and retain source-bound evidence

From the outer packet directory, after `review.py setup`, use its own environment:

```bash
WORK/.venv/bin/python review.py run python3 -m pytest \
  generators/d93294819fca/tests/test_gray_bridge.py -q

WORK/.venv/bin/python review.py run python3 \
  generators/d93294819fca/workspace/parametric/audit.py check \
  --out ../checks/d93294819fca/audit-new
```

The audit executes the real rule and finite rivals through protected Racket,
compares them to the independent Python implementations, exercises size/count
boundaries, and writes exact public bytes alongside separate private evidence.
It also reports a bounded 32-seed sampling check; that sampling count is not a
claim that every one of those episodes was executed in Racket.

To replay the repaired historical perimeter finding, add
`--perimeter-before ../checks/d93294819fca/perimeter-before.json` when that retained
fixture is available. It contains private authoring inputs, labels, and old source
identity. The reusable audit can run without that historical fixture.

After focused checks, retain small receipts in `evidence/current/` and generate
the inventory with the existing native helper (do not hand-edit its hashes):

```bash
WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric manifest d93294819fca \
  --evidence generators/d93294819fca/workspace/parametric/evidence/current \
  --include generators/d93294819fca/tests/test_gray_bridge.py \
  --reported-checks 'Use the actual current audit and focused test results'

WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric qualify d93294819fca \
  --out ../checks/d93294819fca/qualification

WORK/.venv/bin/python review.py run python3 \
  generators/d93294819fca/workspace/parametric/audit.py witness \
  --qualification ../checks/d93294819fca/qualification/qualification.json \
  --out ../checks/d93294819fca/sequential-witness.json
```

Existing output paths are refused. A fresh inventory over an existing manifest
requires the native helper's exact `--replace SHA256` guard. Qualification must
be rerun after any bound source change. The owner then uses the native acceptance
command on the exact integrated bytes; this return does not manufacture acceptance.

## Controller projection

Saved `examples/public/<public_id>.json` files are controller-side bundles with
all four masked query inputs. Do not present that whole bundle as one model turn.
Call `visible_turn(episode,i)` to present the demonstrations and exactly one query
input. It supplies no settings, seed, answers, future input, query count or final
turn hint. The existing consumer owns answer/reveal timing; this prototype does
not add a training loop or turn controller.

`write_batch` hashes the exact `reviewer_support.public_challenge_bytes` written,
sorts public IDs, rejects duplicate visible episodes before creating output, and
keeps settings/programs/query answers in `private/`. Changing private metadata
or query labels alone cannot change the public bytes or filenames.

## Causal witness

A converts gray bridges to green; its intermediate is the merged component
membership and areas. B selects the smallest component using that intermediate.
The witness executes both the qualified program and a wrong-order program that
selects the original minimum before gray conversion. Both convert gray; they
paint different target cells. `audit.py witness` copies the native qualification's
source binding and checks it against current source before recording the case.

No measured training gain, universal identifiability, or training admission is
claimed. Any production or prototype approval remains a separate owner action.
