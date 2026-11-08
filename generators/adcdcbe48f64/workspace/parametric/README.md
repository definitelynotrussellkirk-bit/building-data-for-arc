# Episode-level tile-count prototype

This isolated prototype preserves the original task's object role and spatial
reasoning: copy the entire input horizontally, alternating original and
left-right mirror, beginning with the original. It varies one small rule
parameter exactly once per episode:

| Parameter | Allowed value | Meaning |
|---|---:|---|
| `tile_count` | `5` | Canonical default: `g | mirror(g) | g | mirror(g) | g`. |
| `tile_count` | `3` | Proposed nearby rule: `g | mirror(g) | g`. |

The input grammar does not depend on the parameter. Both settings remain within
ARC's 30-column bound because production inputs are at most six columns wide.
The canonical setting returns the selected authority text byte-for-byte. The
alternative changes only the output count literal; tile order, mirror axis,
starting orientation, palette, and input roles remain invariant.

Each complete episode contains three demonstrations and one query. A deterministic
task-bound hash selects the count before any inputs are drawn and the count is
held fixed for all four pairs. Every pair distinguishes 3 from 5 by output width,
so demonstrations cannot leave the declared parameter rival alive. Public
challenge files omit the setting, Racket source, and query answer. Private files
retain those values, exact programs and hashes, alternative predictions, source
hashes, and replay seeds.

From the outer packet directory:

```bash
python3 review.py run python3 generators/adcdcbe48f64/workspace/parametric/tile_count.py \
  --seed-start 71 --out ../checks/parametric/tile-count-v1
python3 review.py run python3 -m pytest -q \
  generators/adcdcbe48f64/tests/test_parametric_tile_count.py
```

Use a new output path for each evidence run; the builder refuses to overwrite.
All labels are produced by the included real Racket bridge and compared with an
independent Python implementation. The retained report also executes the default
five-tile rule on every labeled canonical pair.

This is a proposed, bounded prototype. It does not alter the selected production
generator, canonical rule hash, catalog approval, or public parametric API. Two
settings and two retained episodes do not prove universal identifiability,
solver benefit, or training admission.
