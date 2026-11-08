# Proposed docking-distance parameter

This is an **unapproved task-local prototype**. It leaves the selected canonical
generator and authority unchanged.

`docking_distance` is chosen once per episode from `{1, 2}`. Distance `1` is
the byte-exact canonical rule: each equal-color marker pair becomes cardinally
adjacent. Distance `2` preserves the same pieces, marker-equality tree, outward
port inference, transitive placement, colors, and final crop, but leaves one
background cell between paired marker cells.

From the packet extraction root, generate retained Racket-backed evidence with:

```bash
PATH="$PWD/WORK/.review/racket-runtime/racket/bin:$PATH" \
python3 review.py run python3 \
  generators/54628ce9692d/workspace/parametric/prototype.py \
  --seeds 0 1 \
  --out ../checks/parametric/docking-distance-v1
```

Seeds `0` and `1` cover distances `2` and `1`, respectively. The private
evidence retains exact Racket text, source hashes, canonical replay, selected
and rival outputs, and query labels. Public files retain demonstration labels
but omit the hidden parameter, Racket source, rival outputs, and query answer.

Limits: this is finite evidence over the selected generator's five published
morphology families. It does not establish that distance `2` is collision-free
for arbitrary novel piece shapes, does not prove universal identifiability, and
does not confer production or training approval.
