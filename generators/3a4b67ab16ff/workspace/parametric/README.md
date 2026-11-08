# Layer-order rule prototype

This task-local authoring prototype preserves the canonical joint-bounding-box
reasoning: restore the gray rectangle, intersect each non-gray color's joint
bbox with it, and fill the clipped rectangle. It varies one hidden parameter
once per episode:

- `layer_order=ascending` is the canonical/default behavior. Its materialized
  Racket source is byte-for-byte the registered canonical program.
- `layer_order=descending` reverses only the final numeric color iteration, so
  the lower color wins where clipped rectangles overlap.

Inputs do not encode the setting. Every episode uses one fixed value across
three demonstrations and four distinct queries. All examples contain a
lawful two-color overlap; the demonstrations reject the other declared value,
and each private query answer differs under that rival. Every selected and
rival output is executed by the included Racket bridge. Public files are named
from, and contain, only the exact visible demonstration/input bytes; settings,
seeds, programs, rival outputs, and query answers remain private. The writer
precomputes the complete batch, rejects duplicate visible payloads before any
public write, and emits public files in visible-ID order rather than private
setting/seed order.

From the packet root, retain one episode for each setting with:

```bash
python3 review.py run python3 \
  generators/3a4b67ab16ff/workspace/parametric/prototype.py \
  --out ../checks/parametric/3a4b67ab16ff-layer-order-final \
  --seed-start 1 --train 3 --test 4
```

This evidence is a bounded proposal, not production approval or training
admission. It covers the two declared order values on controlled two-color
overlap scenes; it does not claim identifiability against arbitrary programs.
