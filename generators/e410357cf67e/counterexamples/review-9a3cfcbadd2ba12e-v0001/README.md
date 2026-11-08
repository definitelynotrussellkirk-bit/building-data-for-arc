# Retained counterexamples for review-9a3cfcbadd2ba12e

- `counterexamples.json` retains two canonical inputs that the pre-repair validator rejected (corner/straight and non-corner/straight), plus one final-source active-wall case that distinguishes the canonical rule from the canonical-fitting `ignore_walls` shortcut.
- `pre-repair-ambiguous-lesson.json` retains an old-source five-pair lesson where the first four demonstrations fit `ignore_walls` and the fifth query differs. Its old generator hash and authoritative Racket rule hash are embedded.

Replay final-source witnesses from the packet root with:

```sh
PYTHONPATH=repo/shared/runtime:repo/src \
python3 repo/generators/e410357cf67e/counterexamples/review-9a3cfcbadd2ba12e-v0001/reproduce.py
```
