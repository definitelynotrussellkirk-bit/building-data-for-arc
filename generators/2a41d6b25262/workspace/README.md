# Workspace probes for 2a41d6b25262

The selected implementation is `../generator.py`; files here are review tools,
not alternate selected generators.

## `reference_probe.py`

Independent canonical reader and Python statement of the normalized-template
XOR rule. It deliberately does not import production mirror helpers when
computing expected outputs. Task-local tests use it for canonical acceptance,
shape signatures, role order, and oracle comparisons.

## `cyclic_lesson_probe.py`

Complements the shared production lesson census by rotating every member of a
five-pair lesson into the query position. It discovers competitors dynamically
from `LESSON_COMPETITORS`, records replay seeds/sample indices/profiles/input
hashes, verifies canonical shortcut fit, and emits JSON.

Full review command from the packet root:

```bash
python3 run_with_racket.py python3 \
  generators/2a41d6b25262/workspace/cyclic_lesson_probe.py \
  --generator generators/2a41d6b25262/generator.py \
  --per-band 100 --out ../checks/cyclic-lesson-final.json
```

The retained final report covers 100 lessons per band and all 1,500 cyclic
query rotations. Its finite named-rival result is not a universal induction
proof; authoritative Racket parity and the production sampler are checked by
the task tests, battery, and shared lesson census.
