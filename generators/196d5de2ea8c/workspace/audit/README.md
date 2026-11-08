# Assigned audit helper: 089c2bd1f753

This probe searches the selected generator with the portable `reviewer_support`
loader and emits a four-pair medium lesson where the plausible rival “crop the
largest object” fits the first three pairs but disagrees with the fourth.

From the outer packet directory:

```bash
python3 review.py run python3 generators/196d5de2ea8c/workspace/audit/probe_089c2bd1f753.py \
  --out ../checks/audit/089c2bd1f753-largest-object.json
python3 review.py run python3 -m arcpuzzles apply 089c2bd1f753 \
  --input ../checks/audit/089c2bd1f753-counterexample/input.json \
  --out ../checks/audit/089c2bd1f753-counterexample/racket.json
```

The first command is a candidate/rival probe. The second is the authoritative
Racket check; do not treat the Python mirror as a replacement for it.
