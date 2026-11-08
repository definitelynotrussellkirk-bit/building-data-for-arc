# Keyed-ray route family

`route_mode=straight` is the exact canonical Racket program.  The alternative
`clockwise_elbow` first casts the keyed magenta ray to its blocker/wall endpoint,
then turns clockwise from that computed endpoint and continues to the next
blocker/wall.  The second leg therefore consumes the first leg's input-dependent
endpoint rather than a fixed frame location.

The demo and query streams are independent and prefix-stable.  They support
2–6 demonstrations and 1–4 queries; the fourth query is a substantive 30×30
four-frame scene.  Every input distinguishes the two settings.  Run:

```sh
python3 generators/7d09ccad28c8/workspace/parametric/audit.py \
  --out generators/7d09ccad28c8/workspace/parametric/evidence/self-audit.json
```

`wrong-intermediate.rkt` is the protected-Racket witness ablation: it turns at
the emitter instead of the endpoint produced by the first leg.
