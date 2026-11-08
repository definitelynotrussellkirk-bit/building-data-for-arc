# Task-local workspace tools

The selected implementation is `../generator.py`. These source-bound tools are retained for future review rounds:

- `reference_probe.py` — independent pixel-level rule reconstruction, generated census, exact-perimeter-only counterexample census, and optional selected-Racket parity.
- `lesson_probe.py` — stages the exact generator, invokes the repository's actual lesson planner/semantic gate, and records lesson-window uniqueness and cyclic-start coverage.
- `shortcut_probe.py` — discovers live `CANONICAL_SHORTCUTS` and `LESSON_COMPETITORS`, checks canonical fit, and saves exact Racket-verified generated counterexamples.
- `audit_probe.py` — retained historical assignment-bound reproducer for the prior review's two adversarial audit targets.

Representative commands from the packet root:

```bash
python3 run_with_racket.py python3 generators/fe0dc9f32b7b/workspace/reference_probe.py \
  --count 150 --racket --out ../checks/final-independent-probe.json

python3 run_with_racket.py python3 generators/fe0dc9f32b7b/workspace/lesson_probe.py \
  --lessons-per-band 100 --census-per-band 150 --timeout 4000 \
  --out ../checks/final-lessons-100-per-band.json

python3 run_with_racket.py python3 generators/fe0dc9f32b7b/workspace/shortcut_probe.py \
  --max-draws 300 --out ../checks/final-shortcut-witness.json
```

`run_with_racket.py` changes the child working directory to `repo`; paths after the wrapper are therefore repository-relative, while evidence outputs use `../checks`.
