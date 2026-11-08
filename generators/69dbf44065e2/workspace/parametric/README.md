# Parametric turn-after-down-smear family

The canonical setting (`turn=none`) is the exact selected ARC Racket program.
`turn=left|right` first executes that downward smear, then extends each active
seed from its Stage-A endpoint in the selected horizontal direction through the
Stage-A background.  Stage-A trails therefore determine both Stage-B start rows
and blockers.

Run the bounded adversarial probe from the repository root:

```bash
python3 generators/69dbf44065e2/workspace/parametric/adversarial_probe.py \
  --seeds 64 --racket-seeds 4 \
  --out generators/69dbf44065e2/workspace/parametric/evidence/current/adversarial-probe.json
```

The probe compares the three declared programs and ten plausible bypass rules
on matched inputs, crosses color permutations, exercises count/type boundaries,
checks public-byte privacy, and replays a bounded subset through protected
Racket.  It is finite evidence, not owner acceptance or a proof of uniqueness.
