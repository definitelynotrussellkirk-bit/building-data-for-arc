# `1b39c0e8ebc7` vector-direction family

This task-local family exposes one episode-fixed parameter:

- `vector_direction=forward` — exact canonical 8→9 displacement;
- `vector_direction=reverse` — the same translate/intersect operation with the
  9→8 displacement.

Inputs are matched across settings. Every scene contains forward hits,
reverse-only hits, unmatched color-3 sources, and unmatched color-4 targets.
The first two demonstrations already distinguish both settings; 2–6 demos are
supported and every episode contains four distinct queries. The final query is a
substantive 30×30 scene with content on all four boundaries and in all quadrants.

Focused checks:

```bash
python3 -m pytest -q \
  generators/1b39c0e8ebc7/tests/test_generator_1b39c0e8ebc7.py \
  generators/1b39c0e8ebc7/tests/test_parametric_vector_direction.py
python3 generators/1b39c0e8ebc7/workspace/parametric/adversarial_probe.py \
  --seeds 32 --demos 2 --out /tmp/vector-direction-probe.json
python3 generators/1b39c0e8ebc7/workspace/parametric/sampler_stress.py \
  --seeds 32 --out /tmp/vector-direction-stress.json
```

Protected Racket qualification/preflight remains the label authority. These
files are reviewer-ready source, not owner acceptance or training admission.
