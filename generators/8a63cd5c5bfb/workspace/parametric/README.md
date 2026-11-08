# Rectangle outline with an inferred object color

This opt-in native family preserves task `8a63cd5c5bfb`'s two green corner
markers, implied rectangle and occupied-cell preservation. It leaves the approved
production generator and canonical authority unchanged.

| Episode-fixed `color_source` | Executed transformation |
| --- | --- |
| `cyan` (default) | The exact canonical Racket program; fill empty rectangle edges with 8. |
| `largest_interior` | Mask to the rectangle's strict interior, find same-color 4-connected components, select the unique largest, and fill empty edges with its color. |

The latter has a spatial-selection dependency: the input-derived rectangle decides
which component participates; that component supplies the subsequent border color.
This is contextual selection, not iterative state simulation. A larger outside
object and disconnected repeated-color inside objects make scope and connectivity
matter. Existing border objects are preserved, not erased or recolored.

## Native contract and support

`adapter.py` implements `program(settings)` and
`generate(seed, settings, demos, queries)`. Requests support 2–6 demonstrations
and 1–4 queries independently. Use three demonstrations and four queries normally.
Settings share identical inputs for matching seeds/counts. Separate input streams
keep query prefixes independent of both counts; the same first query is used when
evaluation stops after one answer.

The sampler admits exactly two opposite green corners and a unique largest
interior component. It constructs four 4-separated interior components, a larger
outside decoy crossing the marked boundary with a one-cell interior fragment,
and occupied border distractors. Components are measured after clipping: the
outside portion of a crossing object does not contribute to its size. Shapes,
sizes, colors, orientations, diagonals and component positions vary. Heavy-repeat
scenes make two repeated-color components touch diagonally so 8-connectivity
would merge them and change the answer.

The two mandatory demonstrations place the winner in different positions relative
to both the canvas and the outside strip. One winner is noncyan, the other cyan;
one lesson has a repeated color's combined area exceed the winner and the other
does not. Small decoy colors bracket the winners numerically. These choices fix
concrete color/position shortcuts found in self-review while keeping two demos.
Empty/tied interiors are rejected by the mirror and never sampled. Racket
programs remain total on the admitted grammar.

Default demonstration sizes begin at 12×12, 14×16 and 16×14; additional requested
demonstrations use 18×20, 20×18 and 22×22. Four query sizes are 12×14, 20×22,
24×28 and 30×30. Larger cases grow components and rectangle perimeter. They are
not empty padding. This separate grammar needs 12 cells per side for four
separated components and an outside decoy; the unchanged canonical generator
retains its smaller public inputs.

`height`/`width` keyword arguments support exact authoring-only dimensions 12–30,
supplied together. These are not new production overrides and are not exposed by
native accepted export. The native default already includes a 30×30 fourth query.
Seeds are exact integers in 0..2^63−1; booleans and invalid counts/settings fail.

## Reproduce in this review packet

Run from the outer directory containing `review.py`, with the packet's prepared
Python environment. Payload paths are relative to `WORK/repo`.

```bash
WORK/.venv/bin/python review.py run python3 -m pytest \
  generators/8a63cd5c5bfb/tests/test_parametric.py -q

WORK/.venv/bin/python review.py run python3 \
  generators/8a63cd5c5bfb/workspace/parametric/verify.py \
  --out ../checks/8a63cd5c5bfb/replay

WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric qualify \
  8a63cd5c5bfb --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/8a63cd5c5bfb/qualification-replay --summary
```

Choose fresh output paths. The verifier executes protected Racket and saves
private labels and finite demo-only rival evidence. Native qualification checks
the declared settings independently of the additional shortcut audit.

## Visibility and owner handoff

`public_turn(episode, query_index)` returns only demonstrations and one masked
query. It uses the shared exact-visible-byte projection helper; no setting,
reference program, query answer, total count or future input enters that turn.
The verifier's `controller_public` directory contains all four masked queries
for controller storage/checking; do not pass that directory as one model turn.
Its `public` directory contains single-query first turns. Full labels/programs
remain private.

Reviewer qualification and the causal replay are evidence for owner intake.
The owner must qualify and accept the exact integrated live source before native
export; this return does not perform acceptance or training admission. Finite
rival checks cover only the listed alternative programs and exercised seeds.
