# Proposed arm-turn parameter (isolated prototype)

This prototype keeps the canonical creature detection, tail direction, whole-object
wall translation, background, and tail transport. It varies one hidden rule
parameter once per episode:

- `arm_turn = half_turn` — canonical/default: opposite arm colors swap.
- `arm_turn = preserve` — the moved body keeps its arm-color orientation.

Every generated creature has four distinct arm colors, so each labelled
 demonstration distinguishes these two settings before the query. The public
challenge files omit the hidden setting and query answer. The retained evidence
contains exact Racket text and hashes, Racket-derived labels, seeds, source hashes,
rival outputs, and a direct parity check between the default prototype and the
selected canonical Racket authority.

Run from the outer extraction directory:

```bash
python3 review.py run python3 \
  generators/0d1deab2505c/workspace/parametric/prototype.py \
  --out ../checks/parametric/arm-turn
```

The output directory must be new. This is a proposed, task-local prototype; it
does not modify the production generator API or approve a new canonical rule.
