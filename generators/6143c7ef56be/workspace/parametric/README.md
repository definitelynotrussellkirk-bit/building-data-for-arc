# Proposed `route_marker` parametric family

This task-local prototype preserves the canonical program exactly when
`route_marker=none`. The alternatives choose the unique `nearest` or `farthest`
quadrant marker by Manhattan distance to its collapsed-block destination, then
use that selected record to draw a vertical-then-horizontal route into the 2x2.
Inputs are sampled independently of the private setting, and demonstrations are
constructed to refute both the retained outer-corner shortcut and a fixed-TL
route shortcut.

Generate compact protected-Racket evidence from the packet root:

```bash
python3 review.py run python3 \
  generators/6143c7ef56be/workspace/parametric/prototype.py \
  --seed 37 --demos 3 --queries 4 \
  --out ../checks/parametric/6143c7ef56be-route-marker
```

Then create the native source inventory and qualification with the commands in
`repo/docs/parametric-promotion.md`. This remains proposed until native
qualification and owner acceptance bind the exact integrated source.
