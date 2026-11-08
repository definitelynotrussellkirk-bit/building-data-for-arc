# Diamond-center relay family

`composition=fill_centers` is the exact canonical Racket program. The
alternative `connect_equal_centers` first identifies every blank center whose
four diagonal neighbors share one nonzero color, fills those derived centers,
then connects horizontally or vertically aligned equal-color derived centers
through zero cells. The connection step therefore consumes the
input-dependent center anchors produced by the canonical step.

The demo and query streams are independent and prefix-stable. They support
2–6 demonstrations and 1–4 queries; the fourth query is a substantive 30×30
scene with seven authored relay pairs plus positive and negative controls.
Every input distinguishes the two settings. Run:

```sh
python3 generators/ee5295e1813b/workspace/parametric/audit.py \
  --out generators/ee5295e1813b/workspace/parametric/evidence/self-audit.json
```

`wrong-intermediate.rkt` is the protected-Racket witness ablation: it shifts
every derived center down one row before constructing connections.
