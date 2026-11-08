# Boolean result component policy

`component_policy=all` returns the exact canonical Racket source, byte for byte.
`largest` first computes the normalized, legend-selected Boolean mask, then
keeps its largest **4-connected** component by cell count. Ties use bounding-box
minimum row, minimum column, then row-major component discovery. Paint only that
component's cells on a fresh cropped cyan grid; an empty result is `[[0]]`.
The default production generator, canonical authority and approvals are unchanged.

## API and grammar

`adapter.program(settings)` and `adapter.generate(seed, settings, demos, queries)`
are the native interface. Settings contain exactly `component_policy: all|largest`.
Seeds are exact integers 0 through 2^63−1; demonstrations are 3–6 and queries 1–4.
Three demonstrations are needed to expose all three independent legend entries
(3=union, 4=intersection, 6=XOR); qualification uses three and four queries.
Requests outside those bounds, including booleans, raise `ValueError`.

Inputs have two independently placed connected shapes in colors 1 and 2, one
corner control, and black background. The separate parametric sampler extends
the input canvas to 8–30 rows and 11–30 columns. Connected growth includes
partial overlap and subset cases; separate private connecting corridors can
produce disconnected intersections, diagonal contacts, ties and irregular pieces.
Horizontal/vertical layouts and independent placement vary nuisance geometry.
The fourth private query has a substantive 30×30 canvas with full-span structures.
Equal masks and empty results are legal under the preserved canonical semantics.
This remains a bounded synthetic grammar, not all polyominoes or every ARC task.

## Teaching and causal structure

The same seed/count request has identical inputs under both settings. A bounded
candidate selector chooses demonstrations against both settings before producing
any query. It rejects a lesson unless its demonstrations refute all declared
finite rivals: the other setting, fixed operations, all five incorrect legend
permutations, absolute alignment and (for largest) smallest/first piece,
bounding-box area, diagonal connectivity and reverse positional ties.
This is finite identifiability, not proof against arbitrary programs.

A is independent normalization and the control-selected Boolean operation. Its
input-dependent intermediate is the resulting cell mask and connected pieces.
B ranks those newly computed pieces and crops the winner. Choosing an original
operand first cannot determine the correct result. The source-bound witness
changes A's operation to union while keeping B, and executes both programs.

## Run from a reviewer packet

```bash
WORK/.venv/bin/python review.py run python -m pytest \
  generators/fb7f02aa9ab0/tests/test_parametric.py -q -p no:cacheprovider
WORK/.venv/bin/python review.py run python \
  generators/fb7f02aa9ab0/workspace/parametric/verify.py --out var/fb7-verification
WORK/.venv/bin/python review.py run python -m arcpuzzles parametric qualify \
  fb7f02aa9ab0 --demos 3 --queries 4 --seed 0 --seed 17 \
  --out ../checks/fb7f02aa9ab0/qualification --summary
```

Choose a new output directory for each run. The verifier uses this checkout's
protected Racket and retains private full episodes, rival outcomes, size stress,
and public **single-current-query** files with IDs derived only from visible bytes.
Four query inputs/answers remain controller-side; first-turn public content is
identical to a one-query request. Use the existing consumer for later turns.

The native manifest and qualification bind exact source; this return is prepared
for owner integration and fresh native acceptance, not self-approved or admitted
to training. Run the manifest helper after source/evidence changes and requalify.
