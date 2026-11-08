# Native projection edge-mode family

Status: **reviewer-ready and natively qualified; exact-source owner acceptance pending**.
Training admission remains disabled.

The episode-fixed parameter is `edge_mode`:

- `near` — canonical/default. Copy every aligned colored source to the nearest
  edge of the cyan region's input-derived bounding box.
- `far` — copy the source to the opposite bounding-box edge.

Both settings retain the original object roles, colors, source preservation,
alignment test, diagonal-ignore behavior, and collision-free declared domain.
`near` returns the canonical Racket program byte-for-byte.

The native adapter supports 2–6 demonstrations and 1–4 private queries with
prefix-stable, setting-neutral inputs. Qualification exercises three
 demonstrations and four distinct queries at seeds 0 and 17. Query shapes are
12×15, 18×20, 24×27, and 30×30; the 30×30 scene contains substantive geometry
rather than padding. Public turns reveal one query at a time and omit settings,
programs, answers, future inputs, and total-count hints.

From the outer packet directory:

```bash
# Focused adapter contract
python3 review.py run python3 -m pytest -q \
  generators/064e439acd2d/tests/test_native_parametric_edge_mode.py

# Protected-Racket finite-rival and boundary audit
python3 review.py run python3 \
  generators/064e439acd2d/workspace/parametric/self_audit.py \
  --seed 0 --seed 17 \
  --out generators/064e439acd2d/workspace/parametric/evidence/current/self-audit.json

# Native qualification
python3 review.py run python3 -m arcpuzzles parametric qualify 064e439acd2d \
  --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/064e439acd2d/qualification --summary

# Recheck the bound causal witness
python3 review.py run python3 -m arcpuzzles.review_witness check \
  --qualification ../checks/064e439acd2d/qualification/qualification.json \
  --witness ../checks/064e439acd2d/causal/witness.json \
  --out ../checks/064e439acd2d/causal/check.json
```

The finite self-audit compares both declared settings and eight executable
shortcuts. After two demonstrations, only the selected setting survives among
that retained family. This is not a universal uniqueness proof.

The required sequential dependency is real and input-dependent: Step A derives
the cyan bounding box and classifies each source side; Step B uses those derived
coordinates plus `edge_mode` to choose the target edge. The protected witness
shifts the derived `cmin` one column inward and changes four final cells.

Key artifacts:

- `adapter.py` — native adapter boundary.
- `promotion.json` — declared parameter/count contract.
- `canonical.rkt` — byte-exact canonical default.
- `self_audit.py` — reusable protected-Racket audit.
- `evidence/manifest.json` — exact source/evidence inventory.
- `../../../../../checks/064e439acd2d/qualification/qualification.json` — reviewer qualification.
- `../../../../../checks/064e439acd2d/causal/witness.json` — bound causal witness.
