# Row-run traversal: native parametric adapter

This is a separate proposed family for `be5d9fa6fec1`. The selected production
generator and its canonical rule are unchanged. Owner qualification and acceptance
on the integrated source remain required before using the accepted export API.

## Episode rules

`step_mode` is fixed for every demonstration and query in an episode:

| Setting | Rule |
|---|---|
| `fixed3` (default) | Segment maximal consecutive identical rows; recolor nonzero cells in runs 0, 3, 6, … to 2. The program is the exact canonical source. |
| `height_plus_one` | Start at run 0. Recolor its nonzero cells, then advance by the current run's height plus one. Read the newly reached run's height before advancing again. Stop past the final run. |

Segmentation and run heights come from the original input. Painting does not
resegment the grid. The adaptive rule's current run index is an evolving state;
it determines which input-derived height controls the next destination.

The API supports **2–6 demonstrations and 1–4 queries independently**. Ordinary
native qualification uses three demonstrations and four queries. Both settings
use exactly the same inputs for a given seed and counts. Increasing either count
preserves the existing demonstration/query prefixes. Seeds are exact integers
from 0 through `2**63-1`; booleans, invalid settings and out-of-range counts fail.

## Input and teaching support

Inputs contain nonempty monochromatic 0/1 or 0/8 row patterns, repeated for
1–3 physical rows. Adjacent patterns can have the same foreground color and
different pixels. A nonadjacent A–B–A repeat distinguishes maximal runs from
globally unique patterns. The first two demonstrations construct heights
`[2,1,1,3,1,1,1,1]` and `[1,2,3,1,2,1,1,1]`; the patterns vary by seed.

The four query profiles are **8×3, 17×9, 25×19, and 30×30**, with 6, 10, 14,
and 16 maximal runs. The large profile distributes content across the full width
with varied row density and run heights. This broader grammar belongs to the
parametric family; it is not a new production `profile_id` override.

`teaching_report(train, settings)` fits 17 canonical-setting or 18 adaptive-setting
rivals using demonstration labels only. They include fixed periods, physical-row
counting, color-kind grouping, a frozen first-height stride, local height modulus,
missing `+1`, selected-pattern reuse, color-only painting and early stopping.
Independent regression tests additionally check grouping all globally identical
patterns together. These are finite tests, not a uniqueness proof.

## Run and reproduce

From the packet's outer directory, using the Python environment selected by
`review.py python-check`:

```bash
python3 review.py run python3 -m pytest -q \
  generators/be5d9fa6fec1/tests/test_parametric.py \
  generators/be5d9fa6fec1/tests/test_parametric_adversarial.py

python3 review.py run python3 \
  generators/be5d9fa6fec1/workspace/parametric/probe.py \
  --out ../checks/be5d9fa6fec1/replay-self-audit

python3 review.py run python3 -m arcpuzzles parametric qualify be5d9fa6fec1 \
  --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/be5d9fa6fec1/replay-qualification --summary
```

The probe runs both settings on seeds 0 and 17 at the minimum and maximum
demonstration counts, always with four queries. It executes all 64 labels through
protected Racket, checks demonstration-only rival elimination, input matching,
unique inputs, private-field invariance and single-query first-turn equivalence.
Choose a new output path for each run. Source/evidence inventory is produced by
the repository's `parametric manifest` helper, not by this probe.

## Public projection

`generate` returns private controller data and Python label claims; qualification
independently checks the claims against Racket. `write_batch` is a byte projection,
not label certification. The probe calls it only after successful Racket checks.

- `public/` contains masked four-query bundles for the controller. Filenames hash
  the exact visible JSON bytes; batch records are sorted by those IDs and duplicate
  visible episodes are rejected.
- `turns/` contains one-query actor surfaces from `visible_turn`. Each includes
  demonstrations and just the currently revealed input, without future inputs,
  total-count hints, settings, seeds, programs or query answers. Its name also
  hashes only its exact visible bytes.
- `private.json` maps the public/turn IDs to complete controller-side episodes.

Give the model the current `visible_turn` surface; keep the whole four-query bundle
with the controller. The first turn has exactly the same bytes as a single-query
request with the same seed, setting and demonstration count. No training controller
or training-admission policy is added here.
