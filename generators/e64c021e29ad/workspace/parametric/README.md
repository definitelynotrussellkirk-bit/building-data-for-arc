# `e64c021e29ad` native parametric family

The default setting, `{"sweep_mode":"all"}`, returns the selected canonical
Racket source byte-for-byte: every color-5..9 object is swept to the border in
the direction encoded by its adjacent 1..4 cell.

The nearby alternative, `{"sweep_mode":"first_hit_relay"}`, adds a genuine
input-dependent relay:

1. Trace the singleton color-9 probe along its own coded ray to the **first**
   color-5..8 object.
2. Carry that object's identity and adjacent direction code forward.
3. Paint the probe path in 9 and sweep only the selected object in its own
   direction and color.

The target, color, and second-stage direction cannot be chosen before the trace.
`last_hit.rkt` is the bounded wrong-intermediate counterfactual used by the
protected causal witness; it deliberately chooses the farther ray hit.

Inputs are matched across settings. The API supports 2–6 demonstrations and
1–4 queries; the stored controller-side lesson has four distinct queries, with
query 4 a substantive 30×30 case. Public challenge bytes omit settings, programs,
and query answers, and the first revealed query is byte-identical to single-query
use.

Run the task tests and authoring evidence from the packet root:

```sh
python3 review.py run python3 -m pytest -q generators/e64c021e29ad/tests/test_parametric.py
python3 review.py run python3 generators/e64c021e29ad/workspace/parametric/verify.py \
  --out generators/e64c021e29ad/workspace/parametric/evidence/current
```

Then create the source inventory and run native qualification exactly as described
in `repo/docs/parametric-promotion.md`. Authoring evidence and qualification are
finite checks; owner acceptance remains a separate exact-source decision.
