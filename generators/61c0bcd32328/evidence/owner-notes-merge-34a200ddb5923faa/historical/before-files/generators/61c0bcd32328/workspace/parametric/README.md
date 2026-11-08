# Proposed corner-copy direction prototype

This **task-local, unselected prototype** keeps the canonical object extraction,
corner classification, source preservation, translation, and paint order.  It
varies one hidden episode parameter:

- `direction=clockwise` — the original/default rule, returned as the exact
  canonical Racket source.
- `direction=counterclockwise` — copies each corner component to the other
  adjacent corner.

The setting is chosen once for the complete episode.  Each retained episode has
three demonstrations and four distinct query inputs.  The input sampler uses one
corner profile at a time and rejects any grid on which the two settings collapse.
Public challenge files contain only visible demonstrations and query inputs; an
opaque SHA-256 ID is derived from those exact public bytes.

From the packet extraction directory, run the focused tests:

```bash
python3 review.py run python3 -m arcpuzzles check 61c0bcd32328 \
  --stage task_tests --phase after --timeout 180 \
  --out ../checks/green-parametric-task-tests-3
```

Run the exact-Racket materializer/verifier:

```bash
cd WORK
python3 run_with_racket.py python3 \
  generators/61c0bcd32328/workspace/parametric/verify.py \
  --out ../checks/parametric/61c0bcd32328-direction.json
```

The verifier writes private episodes, exact programs, opaque public challenges,
and `evidence/manifest.json` under this directory.  It executes all seven labels
for both settings, checks the opposite-direction rival on every demonstration
and query, replays the default program on all canonical occurrences, and retains
one Racket-backed singleton-corner repair witness.  The finite episodes and
bounded singleton sweep are evidence, not production approval or universal
coverage.
