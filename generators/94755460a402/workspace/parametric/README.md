# Command-source variants for 94755460a402

This native family keeps frame selection, strict-interior extraction, cropping,
and geometric transformation from the canonical task. It varies one fixed rule:

- `header` (default): read the transformation code from input cell `(0,1)`;
  `canonical.rkt` is byte-for-byte the selected canonical authority.
- `selected_marker`: first select and crop the first selector-colored frame, then
  read the cropped motif's top-left cell as the transformation code.

The alternative has a real causal dependency: **A** selects and crops the frame;
the input-dependent intermediate is the selected motif marker; **B** chooses and
applies the geometric transform from that marker. The header is a distractor.
Skipping A and using the header changes the result on the constructive lesson.

Inputs are matched across settings and deterministic by `(seed, split, index)`.
The first two demonstrations distinguish the declared settings and finite
shortcut set. The family supports 2–6 demonstrations and exactly four distinct
queries. Query four is an exact 30×30 four-frame scene with substantive content
and contacts on all four boundaries. Public helpers expose demonstration labels
and one query input at a time, with no settings, program, future answers, or
query-count hints. Python labels are claims until protected native qualification
replays the returned Racket program.

From the packet outer directory:

```bash
python3 review.py run python3 -m pytest -q \
  generators/94755460a402/tests/test_parametric_command_source.py
python3 review.py run python3 generators/94755460a402/workspace/parametric/audit.py \
  --seed 0 --seed 17 --racket \
  --out generators/94755460a402/workspace/parametric/evidence/current/audit.json
python3 review.py run python3 -m arcpuzzles parametric qualify 94755460a402 \
  --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/94755460a402/qualification --summary
```

The audit is bounded to the declared programs, finite rivals, and named seeds; it
does not claim universal uniqueness, owner acceptance, learning gain, or training
admission.
