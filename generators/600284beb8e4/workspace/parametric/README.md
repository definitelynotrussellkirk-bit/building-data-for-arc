# Parametric overlap-edge family

`edge_policy=full` preserves the canonical rule byte-for-byte. `near_cue` and
`far_cue` first locate the unique color-1 cue, infer which side of the rectangle
intersection it indicates, then paint the near or opposite intersection edge.
The input bank is matched across settings and supports 2–6 demonstrations plus
1–4 queries; the retained controller-side bank always contains four distinct
queries, ending with a substantive 30×30 scene.

Run focused tests and the bounded adversarial/Racket audit from the repository:

```bash
python3 -m pytest -q generators/600284beb8e4/tests
python3 generators/600284beb8e4/workspace/parametric/audit.py \
  --seeds 96 --protected-racket \
  --out generators/600284beb8e4/workspace/parametric/evidence/adversarial.json
```

The finite rival set is evidence against the named shortcuts, not a proof of
uniqueness against every possible program. Owner qualification and acceptance
remain separate downstream gates.
