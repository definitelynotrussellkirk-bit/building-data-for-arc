# Workspace

`reference_probe.py` is the reusable independent probe for generator `77871cecd343`. It intentionally does not import the generator's semantic helpers for its oracle or rivals.

From the packet root, run:

```sh
python3 run_with_racket.py python3 generators/77871cecd343/workspace/reference_probe.py \
  --count 250 --racket --out ../checks/custom/77871cecd343-probe-v21.json
```

The probe checks:

- all canonical inputs pass `self_check` and match an independent Python reflection oracle;
- both declared rivals fit all canonical pairs;
- deterministic validity, support, and exact-input diversity over each difficulty band;
- centered-cross and retired quadrant-offset rivals disagree with the intended rule on generated cases;
- each source quadrant receives all nine joint cross-offset pairs;
- selected generated/canonical inputs agree with the live Racket authority.

The exact centered-cross counterexample used in the review is returned by `witness_input()`. The selected implementation remains `../generator.py`; workspace probes are evidence only and are never label authority.
