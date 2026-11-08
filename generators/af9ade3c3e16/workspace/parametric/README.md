# af9ade3c3e16 native parametric family

`finish=frame_only` returns the exact selected canonical Racket bytes: count the
red cells and recolor the corresponding outer-to-inner yellow frame cyan.
`finish=center_cross` performs that same selection, derives the selected frame's
bounding box and strict center row/column, then paints those interior cross cells
9 after the canonical border recolor.

The sampler supports 2–6 demonstrations and 1–4 queries with matched inputs
across settings. Its fourth query is an exact 30×30 nested-frame scene. The
retained `wrong-outer-cross.rkt` keeps the selected border but incorrectly uses
the outermost frame's geometry for stage B.

Run from the packet root:

```bash
python3 review.py task-tests af9ade3c3e16 --phase after --out ../checks/af9ade3c3e16-tests
python3 review.py run python3 generators/af9ade3c3e16/workspace/parametric/audit.py --out generators/af9ade3c3e16/workspace/parametric/evidence/current/bounded-self-audit.json
python3 review.py run python3 -m arcpuzzles parametric qualify af9ade3c3e16 --out ../checks/af9ade3c3e16/qualification --summary
```
