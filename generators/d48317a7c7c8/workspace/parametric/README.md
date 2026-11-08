# Target-length parametric prototype

This proposed family preserves the canonical connected-component reasoning and
changes one meaningful episode-fixed rule parameter:

- `target_length=3` — the exact canonical rule, byte for byte.
- `target_length=4` — cap only straight monochrome yellow components of length 4.

Every component is still found with 4-connectivity, bent or merged shapes remain
distractors, and each open endpoint is capped independently with gray `8`.
Inputs are sampled independently from the private setting. Two demonstrations
are sufficient to distinguish both settings; the retained evidence uses three
demonstrations and four distinct queries, ending with a substantive 30×30 scene.

The native promotion surface is `adapter.py` plus `promotion.json`. The adapter
supports 2–6 demonstrations and 1–4 queries; ordinary use should request four
queries for sequential reveal. `prototype.py` creates compact Racket-backed
public/private evidence and verifies the finite rival from demonstrations only.

From the packet root:

```bash
python3 review.py run python3 \
  generators/d48317a7c7c8/workspace/parametric/prototype.py \
  --base-seed 20261024 \
  --out ../checks/parametric/d48317a7c7c8-target-length-v1

python3 review.py run python3 -m pytest -q \
  generators/d48317a7c7c8/tests/test_parametric_target_length.py \
  --basetemp /tmp/d483-parametric-tests
```

Public files contain labeled demonstrations and query inputs only. They are written
as exact `reviewer_support.public_challenge_bytes`, and their opaque filenames use
`challenge-<full-SHA-256>.json` for those exact visible bytes. Private files retain
settings, exact Racket source, all query labels, hashes, and teaching checks.
This bounded prototype is not qualification, acceptance, or training admission.
