# Proposed marker-order parameter (prototype only)

This workspace tests one episode-level parameter without changing production authority:

- `near_to_far` — canonical/default: stably order markers by increasing minimum edge distance.
- `far_to_near` — proposed alternative: stably order markers by decreasing minimum edge distance.

Both settings keep the same nonzero modal background rule, include zero as a marker, preserve row-major order inside ties, and paint the ordered colors onto output rings from outside inward. The parameter is selected once from the episode seed and shared by two demonstrations and one query. Every retained input uses the production `teaching_combined` grammar and is required to distinguish both settings.

Run the exact Python/Racket evidence check from the packet root:

```bash
python3 review.py run python3 \
  generators/1034300a135f/workspace/parametric/prototype.py \
  --seed 19 \
  --out ../checks/parametric/marker-order-seed19.json \
  --write-public generators/1034300a135f/workspace/parametric/examples
```

The command materializes setting-specific standalone Racket programs under `rules/`, executes both on all retained pairs, checks Python parity, checks canonical-default parity with the selected production generator, and writes public challenges with the parameter and query answer redacted.
