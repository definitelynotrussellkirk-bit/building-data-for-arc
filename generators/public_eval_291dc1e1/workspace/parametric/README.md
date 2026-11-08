# Border-directed bar packing

This is an unapproved authoring family for the exact public parent `291dc1e1`.
The canonical program reads bars in the order indicated by the `0` corner and
the `1` and `2` border strips. The `1` strip determines the fast scan direction;
the `2` strip determines the order of tracks. After removing those strips,
extract filled four-connected non-`8` rectangles, keep horizontal bars as drawn,
rotate vertical bars counterclockwise, and center the resulting two-row bars in
a vertical stack. Repeated bars and interior `0`, `1`, and `2` cells are retained.

| Setting | Behavior |
| --- | --- |
| `stack_order=forward` | Preserve the border-defined component sequence; exact root reference bytes. |
| `stack_order=reverse` | Reverse that complete sequence before placing the normalized bars. |

Both settings receive identical inputs for the same seed and counts. The
parameter is fixed for an episode. It changes sequence order, not the orientation
of individual bars. Stage A extracts, normalizes, and orders the input objects;
stage B consumes their sequence and maximum length to construct the centered
stack. The `layout-order` binding is the causal intervention point.

## Supported inputs and teaching

Inputs are rectangular lists of exact integers `0..9`, with dimensions `5..30`.
The origin is the top-left or top-right corner. Border semantics `0/1/2` and
background `8` are fixed. There are `1..15` filled rectangular bars of thickness
two and even length `2..28`; components may touch a removed border or an
unmarked canvas edge. Outputs have dimensions at most `30×28`. Bottom origins,
odd lengths, hollow or connected composite shapes, and alternate border colors
are outside this grammar.

The family supports **3–6 demonstrations and 1–4 queries**. The first three
scenes cover horizontal/right, vertical/left, and vertical/right readings, with
patterned squares, asymmetric long bars, staggered positions, interior border
colors, and repeated objects. Patterned squares and horizontal right-start
orientation are explicitly taught extensions: their corresponding objects in
the supplied public pairs are monochrome. The four query scenes cover both
axes and both top corners, including a substantive `30×30` boundary scene.
Finite rival checks support the chosen minimum; they cannot establish uniqueness
against every possible program.

Generation uses local independent random streams. The complete four-query bank
is shuffled before prefix selection. Increasing demonstration or query counts
preserves existing prefixes. Caller-owned grids do not alias another result.

## Run from the outer packet directory

Use Python 3.12+ with the packet dependencies and its freshly installed bundled
Racket runtime. All payload commands below execute in `WORK/repo`.

```sh
PYTHONDONTWRITEBYTECODE=1 WORK/.venv/bin/python review.py run python3 -m pytest --import-mode=importlib generators/public_eval_291dc1e1/tests -q
PYTHONDONTWRITEBYTECODE=1 WORK/.venv/bin/python review.py run python3 -m arcpuzzles.review_public_creation preflight public_eval_291dc1e1 --root . --out ../checks/public_eval_291dc1e1/preflight
```

The native preflight executes every original training and supplied gold query,
then three demonstrations and **four queries** at seeds `17` and `43` for both
settings. Use a fresh output directory after source changes. For direct private
authoring, load `adapter.py` and call
`generate(17, {"stack_order": "reverse"}, demos=3, queries=4)`; its returned
answers, program, setting, and future query inputs stay with the controller.
The bridge in `WORK/checks/public_creation_tools.py` builds source-bound causal
evidence and one-query public projections from the native preflight.

The adapter reads only its adjacent declared resources. `sampler.py` is an exact
copy of root `generator.py`, and `canonical.rkt` exactly matches root
`reference.rkt`. Focused tests cover authoring behavior; source approval,
registration, native owner qualification, acceptance, and training admission are
separate steps.
