# Native parametric family for `4b326abc33f4`

`assignment_mode=local` is the exact canonical Racket program. It finds hollow
color-5 frames in canonical bbox order, reads each frame's single midpoint side
seed, and fills that frame with its own color.

`assignment_mode=cyclic_next` keeps the same input grammar and performs a real
composed dependency:

1. **A:** detect and canonically order the frames, then extract their side-seed
   colors;
2. **Intermediate:** the input-dependent ordered seed-color sequence;
3. **B:** rotate that sequence left and fill each frame with its successor's
   color, wrapping the final frame to the first.

Inputs are sampled independently of the private setting. The minimum two-demo
lesson uses three- and four-frame scenes with mixed seed sides, nonmonotone color
orders, and geometry that distinguishes canonical cyclic adjacency from global
left-to-right, center-row, area, color-rank, wrong-direction, partial-three-frame,
and side-conditional alternatives. Four query profiles include boundary contact,
order confounds, 24x24 coverage, and a substantive four-quadrant 30x30 scene.

Useful commands from `WORK/repo`:

```sh
python3 -m pytest -q generators/4b326abc33f4/tests
python3 generators/4b326abc33f4/workspace/parametric/audit.py \
  --seeds 256 \
  --out generators/4b326abc33f4/workspace/parametric/evidence/adversarial-audit.json
```

The audit is finite Python evidence. The packet's protected-Racket preflight,
causal-witness builder, public projection verifier, owner acceptance, and training
admission are separate gates.
