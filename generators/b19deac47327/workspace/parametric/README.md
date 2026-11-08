# `b19deac47327` native parametric family

This task-local family keeps the approved production generator unchanged and
adds one episode-fixed parameter:

| `finish_rule` | Executed transformation |
|---|---|
| `project_only` | The exact selected canonical Racket program, byte-for-byte. Each color-1 marker projects the matching border color one cell toward that border. |
| `project_then_bridge` | First run the canonical projection. Then group the newly created interior border-colored seeds by aligned row/column and color, select the unique group with the most seeds, and fill the span between its endpoints. |

The second setting has a real state dependency. **A** is canonical projection;
the input-dependent intermediate is the projected grid and its aligned seed
groups; **B** selects and bridges a group from those new cells. Before A, the
input contains no interior border-colored cells, so B has no eligible group. The
protected-Racket counterfactual in `skip_projection.rkt` skips A and changes the
final output on the retained 30×30 witness.

## Input and lesson contract

- Settings are fixed for the whole episode and never influence input sampling.
- Demonstrations support counts 2–6; ordinary qualification uses two because the
  first two constructive examples already distinguish both declared settings.
- Queries support 1–4 independently. A normal episode stores four distinct
  queries; requesting one reproduces exactly the first query input.
- Query shapes are 13×15, 18×22, 24×27, and 30×30. The 30×30 input contains
  substantive markers spanning both orthogonal boundaries.
- Every scene has three aligned candidate groups: the intended maximum-count
  group, a wider lower-count distractor, and a narrower gapped lower-count
  distractor. The first two demonstrations alternate orientation and winning
  border side.
- The public projection contains demonstrations and exactly one current query
  input. It excludes settings, reference programs, answers, future query inputs,
  seeds, and total-query hints.

`prototype.py` is the single implementation used by the thin `adapter.py`.
`canonical.rkt` is guarded by the selected authority hash. `audit.py` runs a
finite demonstration-only identifiability audit against both declared settings
and nine executable shortcut programs; it does not claim universal uniqueness.

## Reproduction

From the library root with protected Racket configured:

```bash
python3 generators/b19deac47327/workspace/parametric/audit.py \
  --out ../checks/b19deac47327/self-audit.json

python3 -m arcpuzzles parametric qualify b19deac47327 \
  --out ../checks/b19deac47327/qualification --summary
```

Qualification executes every label in protected Racket on seeds 0 and 17, two
demonstrations, and four queries. Reviewer qualification is source-bound evidence,
not owner acceptance or training admission.
