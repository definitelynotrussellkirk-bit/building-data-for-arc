# Exact-pass midpoint cascade family

This task-local prototype keeps the reviewed `fe54bfae4cee` reasoning intact:
equal nonzero endpoints exactly two cells apart fill a zero midpoint.  The only
hidden episode parameter is `passes`:

- `passes=1` is the byte-for-byte canonical Racket program.
- `passes=2` runs that exact pass twice.  Pass 1 creates an input-dependent
  midpoint; pass 2 can use that new cell as an endpoint for a perpendicular
  pair.  Depth-three zig-zag chains distinguish exactly two passes from an
  unbounded closure shortcut.

The deterministic input stream is shared across settings.  It supports 2–6
demonstrations and exactly four distinct queries; query four is a substantive
30×30 scene.  Each scene also contains long-span, diagonal, and blocked-midpoint
near misses.  Public projection exposes demonstration labels and query inputs
only.

From the packet root:

```bash
python3 review.py task-tests fe54bfae4cee --phase after \
  --out ../checks/fe54bfae4cee-task-tests
python3 review.py run python3 -m arcpuzzles parametric manifest fe54bfae4cee \
  --evidence generators/fe54bfae4cee/workspace/parametric/evidence/current \
  --include generators/fe54bfae4cee/tests/test_parametric_midpoint_passes.py \
  --reported-checks 'Focused staged tests, protected Racket parity, finite shortcut audit, public masking and exact 30x30 stress.'
python3 review.py run python3 -m arcpuzzles parametric qualify fe54bfae4cee \
  --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/fe54bfae4cee/qualification --summary
python3 review.py run python3 \
  generators/fe54bfae4cee/workspace/parametric/build_evidence.py \
  --qualification ../checks/fe54bfae4cee/qualification/qualification.json \
  --out ../checks/fe54bfae4cee/review-evidence
python3 WORK/check_public_exports.py \
  WORK/checks/fe54bfae4cee/review-evidence/public --demos 3 --queries 4
```

The retained qualification and causal witness are reviewer evidence only.  The
owner must replay and accept the exact integrated source before the family is a
live parametric API; training admission remains false.
