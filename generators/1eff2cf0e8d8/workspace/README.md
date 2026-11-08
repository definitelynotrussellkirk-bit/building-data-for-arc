# Task workspace

The selected implementation is `../generator.py`. This directory contains reusable, non-selected evidence tools.

## `lesson_probe.py`

A source-bound large-lesson audit. It:

- loads the exact selected generator and verifies an optional SHA-256 pin;
- builds an explicit canonical `GeneratorBundle`, then uses the repository's real `runner.run_one` sampler and Racket bridge;
- reads semantic rivals, shortcuts, and witnesses dynamically from the generator;
- verifies every declared canonical shortcut against every usable canonical pair;
- tests all cyclic four-demo starts, counts unique inputs and sampler shifts, and checks Python/Racket parity;
- records domain limits and avoids claiming universal induction.

From the packet root, after `setup_racket.py`:

```bash
python3 run_with_racket.py python3 \
  generators/1eff2cf0e8d8/workspace/lesson_probe.py \
  --lessons-per-band 100 \
  --expected-generator-sha256 44ee3ba40b5e3f5b0fa7326e0931208e8f2e205c7150ea507f220f151fe081bb \
  --out ../checks/1eff2cf0e8d8_lesson_probe.json
```

The wrapper changes into `repo/`, so paths after `python3` are repository-relative and the output uses `../checks/` to land at packet root.
