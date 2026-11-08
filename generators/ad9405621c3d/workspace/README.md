# Workspace for `ad9405621c3d`

The selected implementation is `../generator.py`. These source-bound tools are retained for replay and future reviews.

## `reference_probe.py`

Independent endpoint parsing and U,D,L,R BFS; it does not import path helpers from the selected generator. It checks canonical parity, generator validity/determinism/diversity, the declared outer-two-ring shortcut, topology-profile counts, and optional real Racket parity.

From `repo/`:

```bash
PYTHONPATH=shared/runtime python3 generators/ad9405621c3d/workspace/reference_probe.py \
  --per-band 200 --racket \
  --out ../checks/ad9405621c3d_reference_probe.json
```

## `lesson_probe.py`

Materializes at least 100 lessons per band with four consecutive demonstrations and one query, using source-bound deterministic seeds. It records the exact sampler, source hashes, dimensions/colors/profiles, unique-input and input-output counts, rival disagreements, identifiability, and optional sampled Racket parity.

From `repo/`:

```bash
PYTHONPATH=shared/runtime python3 generators/ad9405621c3d/workspace/lesson_probe.py \
  --lessons-per-band 100 --racket-sample 64 \
  --out ../checks/ad9405621c3d_lesson_probe.json
```

Both reports are finite audits, not universal proofs. Re-run them whenever `generator.py` or either probe changes; compare the source hashes embedded in the output before reusing claims.
