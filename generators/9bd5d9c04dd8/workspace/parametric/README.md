# Native selection-mode family

This task-local adapter exposes one episode-fixed rule parameter while preserving
the selected generator's input grammar:

| Parameter | Values | Canonical/default |
| --- | --- | --- |
| `selection_mode` | `most`, `fewest` color-1 cells | `most` |

Both settings enumerate orthogonally isolated, fully nonzero 3×3 tiles, count
color-1 cells, choose one extremum, and return that tile. `canonical.rkt` is the
exact selected canonical program. `fewest.rkt` changes only the strict extremum
direction. Every generated scene gives candidate tiles distinct color-1 counts,
so labels distinguish the settings without changing the inputs.

## Native contract

`adapter.py` exports:

- `program(settings)`: exact retained Racket source for the setting;
- `generate(seed, settings, demos, queries)`: deterministic `train`, `test`, and
  `program_solution` records.

The family accepts 2–6 demonstrations and 1–4 queries. Demo and query streams are
independent, all episode inputs are distinct, and input sampling is independent
of the hidden setting. Qualification uses 3 demonstrations and all 4 queries.
The fourth query is a substantive 30×30 scene with at least eight isolated
candidate tiles plus non-candidate distractors.

Python outputs are claims only. Native qualification re-executes every label with
the protected bundled Racket runtime. The focused tests additionally compare both
programs with the independent Python mirror and reject a fixed "first candidate"
bypass.

From the outer extraction directory:

```bash
python3 review.py run python3 -m pytest -q \
  generators/9bd5d9c04dd8/tests/test_parametric_selection_mode.py

python3 review.py run python3 -m arcpuzzles parametric qualify 9bd5d9c04dd8 \
  --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/9bd5d9c04dd8/qualification --summary
```

This prototype is proposed/ready for owner review; it does not self-approve,
accept, or admit the family to training.
