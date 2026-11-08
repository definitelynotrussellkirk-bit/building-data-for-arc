# Proposed parametric extension: encoding power

This prototype preserves the canonical marker/bar/repeated-length reasoning and
changes only the final digit encoding. `encoding_power=2` is the exact canonical
Racket program; `encoding_power=1` writes `abs(base) mod 10`. The power is chosen
once per episode. Every retained demonstration and query input is lawful under
the selected generator and gives different Racket outputs for the two settings.

From `WORK/`:

```bash
python3 run_with_racket.py python3 \
  generators/9fe97c2dd8a4/workspace/parametric/prototype.py \
  --seed 17 --difficulty medium --out ../checks/parametric/final-v2
```

The neutral `public-*.json` files contain demonstrations and unlabeled queries
only. `private-*.json`, `program-*.rkt`, `witness.json`, and `receipt.json` retain
the hidden parameter, exact programs, source/runtime hashes, rival outputs, and
limitations. This is a proposed task-local prototype, not a production rule or
training-approval change.
