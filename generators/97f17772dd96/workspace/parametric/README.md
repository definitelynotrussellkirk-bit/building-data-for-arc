# Depth-order parametric family

This family keeps the selected nested-frame input grammar and changes only the
color order assigned to positive nesting depths:

- `outer_to_inner` is the exact canonical Racket authority: depth `d` becomes
  color `d + 1`.
- `inner_to_outer` first computes the input-dependent maximum depth `M`, then
  maps depth `d` to `M - d + 2`.

The alternate rule has a real sequential dependency. **A** discovers the nested
frame chain and its maximum depth `M`; **B** uses both each cell's depth and `M`
to choose its output color. Replacing `M` with a fixed value changes the answer
on a two-frame scene.

The first two demonstrations deliberately differ in frame count, offset status,
and square/rectangular geometry. They distinguish either setting without using
those incidental properties. Inputs are identical across settings. The four
query profiles are 14×17, 18×23, 24×27, and a substantive 30×30 three-frame
scene. The adapter supports 2–6 demonstrations and 1–4 queries independently.

Focused tests:

```bash
python3 review.py run python3 -m pytest \
  generators/97f17772dd96/tests/test_parametric_depth_order.py -q
```

Finite rival audit:

```bash
python3 review.py run python3 \
  generators/97f17772dd96/workspace/parametric/audit.py \
  --out generators/97f17772dd96/workspace/parametric/evidence/current/self-audit.json
```
