# Native `target_basis` family

This task-local native adapter preserves the selected canonical generator and
its exact default Racket program. One setting is chosen once per episode:

- `target_basis=template_interior` — exact canonical behavior. Find the sole
  patterned template, retain all frames with the same interior dimensions, and
  stamp the template pattern at its original relative offsets.
- `target_basis=pattern_bbox` — composed alternate behavior. First derive the
  template pattern's minimal bounding box and normalized crop. Then use those
  input-dependent crop dimensions to select a different empty frame and stamp
  the normalized crop in that frame's color.

The alternate has a real A→intermediate→B dependency: the receiving frame is not
known until the pattern bounding box has been measured. A protected-Racket
counterfactual that substitutes the template interior dimensions selects the
canonical-size frames instead and changes the final output.

The sampler supports 2–6 demonstrations and 1–4 queries independently. Native
qualification uses three demonstrations and four queries. Inputs are matched
across settings for the same seed. The fourth query is a substantive 30×30
scene with six separated frames, boundary contacts, all-quadrant occupancy, a
unique crop-sized target, and a transposed same-area decoy. Public exports hide
settings, programs, future queries, and query answers; sequential turns reveal
one query input at a time.

From the packet outer directory:

```bash
python3 review.py run python3 \
  generators/e3f1bc75d654/workspace/parametric/audit.py \
  --out generators/e3f1bc75d654/workspace/parametric/evidence/current/self_audit.json \
  --public-dir generators/e3f1bc75d654/workspace/parametric/evidence/current/public \
  --case-out ../checks/e3f1bc75d654/audited-causal-case.json \
  --stress-seeds 50

python3 review.py run python3 -m arcpuzzles parametric qualify e3f1bc75d654 \
  --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/e3f1bc75d654/qualification --summary
```

The self-audit is finite: it tests both settings and six authored nearby rivals;
it does not prove universal identifiability, owner acceptance, or training
admission.
