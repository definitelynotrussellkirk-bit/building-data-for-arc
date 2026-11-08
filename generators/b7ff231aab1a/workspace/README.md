# Review workspace

`reference_probe.py` independently computes the intended area-ranked output and
the canonical-compatible reading-order rival directly from pixels. It can also
materialize the stable adversarial witness used in this review:

```bash
PYTHONPATH=../../shared/runtime python3 reference_probe.py \
  --seed 20261007 --sample-index 0 --out witness.json
```

To analyze an existing grid, pass either a raw JSON grid or an object containing
an `input` field with `--input PATH`. The tool never invokes or imports the
Racket oracle; use `arcpuzzles apply` separately when authoritative output is
required.
