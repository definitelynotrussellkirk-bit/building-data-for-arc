# a950d6dbe2e0 parametric authoring

This family keeps the exact selected canonical rule as `mode=full_orbit`: every
upper-left source cell is completed across both full-grid midlines.

The alternative `mode=largest_after_lateral` adds a real sequential dependency:

1. **A:** reflect every source cell across the vertical midline.
2. **Input-dependent intermediate:** recompute the same-color four-connected
   components in that top-half intermediate.
3. **B:** select the largest recomputed component and reflect only it across the
   horizontal midline.

Each constructed scene contains a smaller source component touching the lateral
midline and a larger away-from-midline decoy. A merges the first component with
its mirror, making it the new largest; selecting before A chooses the decoy and
changes the final output. Inputs are matched across settings and use separate
per-index RNG streams. The adapter supports 2–6 demonstrations and 1–4 queries;
query prefixes are stable and query four is a substantive 30×30 case.

Focused checks and bounded self-audit from the packet root:

```bash
python3 review.py run python3 -m pytest \
  generators/a950d6dbe2e0/tests/test_parametric_family.py -q
python3 review.py run python3 \
  generators/a950d6dbe2e0/workspace/parametric/audit_lessons.py \
  --seed-count 32 \
  --out generators/a950d6dbe2e0/workspace/parametric/evidence/current/self-audit.json
```

Native qualification executes both setting programs through protected Racket.
The separate `select_before_lateral.rkt` program is the wrong-order causal
counterfactual. This authoring family is reviewer-ready only after source-bound
manifest and qualification evidence; owner acceptance and training admission
remain separate gates.
