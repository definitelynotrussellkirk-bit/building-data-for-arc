# Keyed rotation and first-hit size

Native adapter for the separate parameter family of `66387591ebe6`.
The production generator and selected canonical program remain unchanged.

| Private episode setting | Rule |
|---|---|
| `{"turn_source":"key"}` | Exact canonical bytes: keep the top-left key and color-9 pivot; rotate every other foreground cell by `key - 1` clockwise quarter-turns. |
| `{"turn_source":"hit_size"}` | Key 1/2/3/4 sends a north/east/south/west ray from the pivot. Bind the first same-color four-connected component hit, then rotate all payload by `(size - 1) mod 4`. With no hit, leave the input unchanged. |

The ray/component is an input-dependent intermediate. Its size is needed before
the rotation can be chosen; it is not an episode constant or a color remap.

## Use and reproduce

From the packet's outer directory, with its Python environment and Racket setup:

```bash
WORK/.venv/bin/python review.py run python3 \
  generators/66387591ebe6/workspace/parametric/audit_native.py \
  --seed 23 --demos 5 --out ../checks/66387591ebe6/new-audit

WORK/.venv/bin/python review.py run python3 -m pytest -q \
  generators/66387591ebe6/tests/test_native_parametric.py

WORK/.venv/bin/python review.py task-tests 66387591ebe6 \
  --phase after --out ../checks/66387591ebe6/new-staged-tests

WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric qualify \
  66387591ebe6 --demos 5 --queries 4 \
  --out ../checks/66387591ebe6/new-qualification --summary
```

Use a fresh output directory. Pass `--demos 5` explicitly because the shared
qualification CLI defaults to three, below this family's teaching minimum.
Owner acceptance of the exact integrated bytes remains a separate step.

`native.program(settings)` and `native.generate(seed, settings, demos=5,
queries=4)` are the adapter API. The latter returns only `train`, `test` and
`program_solution`; all labels are executed by protected Racket. The sampler
also exposes `sample_inputs(seed, demos=5, queries=4)`. Seeds are exact integers
from zero through `2**63-1`, demos 5–6 and queries 1–4. Booleans and coerced
strings/floats are rejected. Task-local modules load by exact adjacent path.

## Teaching, sizes and matched inputs

Five mandatory demonstrations cover all four keys, all four selected-size
rotation residues, wraparound beyond four cells, and the no-hit branch:

| Demo | Size | Key | First-hit component size | Alternate turns |
|---|---|---|---|---|
| 1 | 9×9 | 1 | 2 | 1 |
| 2 | 9×9 | 2 | 1 | 0 |
| 3 | 13×13 | 3 | 4 | 3 |
| 4 | 15×15 | 4 | none | 0 |
| 5 | 17×17 | 1 | 7 | 2 |

An optional sixth 19×19 demo has key 2 and a six-cell first hit. The same key
and hit color occur with different outcomes, and the same dimensions require
different rotations. These choices defeat key, color and canvas-size lookup
shortcuts. The selected component has disconnected same-color, diagonal
same-color, differently colored adjacent, and farther-ray distractors.

Queries are 9×9, 17×17, 23×23 and 30×30. The last uses a long first-hit ray,
a seven-cell target and colored structures spanning a 29×29 rotation-safe
square. Those structures rotate and touch the safe region's boundaries; they
are substantive content, not empty padding. An integer pivot in a 30×30 grid
cannot center a 30×30 square under all quarter-turns. Every payload cell stays
in bounds and avoids the key/pivot under all four rotations.

One seeded palette and separate deterministic scene streams are independent
of settings and requested counts. Both settings receive identical inputs.
Increasing demo or query count preserves both existing prefixes. These are
structured square curriculum profiles with staircase targets and a three-sided
frame aligned with the key, not a sampler of every legal shape, size, component
count or independently varied cue layout. Production's narrow connected-object
9/11-scale sampler is not changed by the extension.

## Public projection

Only demonstration pairs and current query input belong in the model prompt.
The audit writes hash-named public JSON using the existing canonical visible
byte helper. Its private report maps full controller challenges and first-turn
views; give the model the first-turn view, then reveal each later query through
the existing consumer. The full four-query challenge remains controller-side.
Settings, seed, programs and query answers do not affect visible-byte identities.
One-query generation has exactly the same first-turn bytes as four-query use.
Private evidence folder names are not prompt identifiers.

## Evidence and limits

`evidence/repaired-seed0/` and `repaired-seed17/` contain the current protected
Racket audit: two settings, five demos and four queries each. Each run made
208 protected evaluations. Thirteen canonical and thirty composed-rule rivals
were eliminated from demos. Three lookup families were checked per setting;
only the correct canonical key-to-turn mapping survived and agreed on queries.
The audit replays all labels independently and checks matched inputs and public
projection. Finite rivals do not prove uniqueness against arbitrary rules.

`evidence/teaching-before/` preserves executed failures of the initial draft:
distinct demo dimensions permitted size lookup; its original no-hit key fallback
permitted a constant-three-turn interpretation. The current same-size demos and
no-hit/no-action semantics repair those findings. Three original ambiguous
lessons remain in `evidence/alternative-solutions/`, separate from repaired labels.
`evidence/final-seed0/` is historical **failed** evidence of the initial atomic
identity-rule wrapper error; the name does not denote the final source.

Five demonstrations are an explicit teaching cost, above the usual three.
The unchanged production key-1 omission remains an unresolved production audit;
mandatory key-1 examples address the new family only. Native qualification,
reviewer-ready status, exact-source owner acceptance, and training admission
remain distinct.
