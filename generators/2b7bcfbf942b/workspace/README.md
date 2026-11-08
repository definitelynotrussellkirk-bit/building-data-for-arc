# Workspace tools for 2b7bcfbf942b

The selected implementation is `../generator.py`; files here are qualification
and replay tools, not alternate generators.

## `reference_probe.py`

Independent same-color component parsing and bounding-box geometry, a Python
oracle transliterated independently from the generator implementation, the
`complete_frames_only` and `canonical_bbox_sizes_only` rivals, exact witness
inputs, deterministic distribution auditing, and optional real-Racket parity.

Example from `repo/`:

```bash
PYTHONPATH=shared/runtime:src python3 generators/2b7bcfbf942b/workspace/reference_probe.py --count 120 --racket --out ../checks/reference-probe.json
```

## `lesson_probe.py`

Stages a portable selected-task runtime, reads the final generator's declared
competitors and witnesses dynamically, runs one persistent Racket bridge, and
assembles 3-demo/1-query lessons.  It reports source hashes, exact sampler,
axis domains, unique-input counts, witness coverage, rival disagreements, and
lesson identifiability.

Example from the packet root:

```bash
python3 run_with_racket.py python3 generators/2b7bcfbf942b/workspace/lesson_probe.py --per-band 100 --demos 3 --out ../checks/lesson-probe.json
```
