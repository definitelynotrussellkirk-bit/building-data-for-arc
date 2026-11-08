# Glyph instructions and a stateful cursor

This is an unapproved authoring proposal for official public parent `136b0064`.
The root `reference.rkt` is a general interpreter of the visible instruction
grid; it contains no supplied-grid or answer lookup. `scan=columns` returns
those exact reference bytes. `scan=rows` changes instruction traversal while
keeping the glyph codebook, ink and cursor execution unchanged.

## Rule and original evidence

A full-height yellow-4 divider separates 3×3 instruction slots from a blank
canvas with one gray-5 marker. Read columns left to right and each column top
to bottom for the original rule. Ignore empty slots, including holes within a
column. The four binary masks have the following meanings; 1 denotes the
glyph's single nonzero ink, which is also used for the drawn stroke.

| Mask, top to bottom | Command | Stroke cells | Cursor displacement |
| --- | --- | --- | --- |
| `110 / 101 / 010` | R3 | Three cells to the right | One row down, two columns right |
| `101 / 101 / 111` | L2 | Two cells to the left | One row down, one column left |
| `111 / 010 / 101` | L4 | Four cells to the left | One row down, three columns left |
| `101 / 010 / 010` | D2 | Two cells downward | Two rows down, same column |

Each command starts one row below the previous endpoint, in the same column.
Include that starting cell in the stroke. The last painted cell becomes the
next cursor. Return the entire right-hand canvas, retaining the marker and
trailing blank rows. Repeated commands use the updated cursor, not the initial
marker or a separately reset position.

The supplied three training pairs and one test gold fix these examples but
confound shape and ink. Treating shape as opcode and color as ink is a stated
generalization. Generated demonstrations teach it with remapped colors and
gray glyph ink. The four masks also have distinct pixel counts, so a count
decoder is equivalent on this exact-mask grammar; it is not a wrong rival.

Stage A locates the marker, decodes the actual glyphs and orders their command
records. Stage B consumes those records to update and paint the cursor path.
The causal recipe replaces decoded stroke lengths with one while retaining
ink and direction. The protected replay must show a changed final answer.

## Domain and sampler

The interpreter accepts exact list grids of exact integer colors 0–9, heights
3–30 and total widths 8–30. The divider sits after 1–4 columns of 3×3 slots,
separated by zero rows/columns. The canvas is at least four cells wide. Glyphs
are uniform ink 1–9 except 4; ink 5 on the program side is lawful and does not
create a canvas marker. Empty slots and zero padding are permitted; the program
must be nonempty and every command must fit under the selected scan order.

Generated inputs belong to a narrower matched domain: both scan orders fit.
The first original training input and supplied test input leave the canvas
under row order, so canonical interpretation of an original does not require
the alternative setting to be valid. The Python solver checks the chosen
setting; the generator's `validate_grid` checks both settings.

Three core demonstrations provide a singleton R3 with gray ink, a program with
a hole and a shifted marker, and a program occupying three glyph columns with
a further shifted marker. They teach command-count, hole, color-role, marker
and traversal behavior. Three optional demonstrations extend the fixed prefix.
Four distinct queries include a one-command 3×10 case and a 30×30 case with
21 instructions; the middle queries include holes and longer cursor histories.
Generated profiles use 1–3 glyph columns, remapped inks, varied command orders,
markers and canvas sizes. A local deterministic sampler tries at most 256
command arrangements to find one that fits both settings.
The outer glyph inks in the third demo's odd row differ, so alternating-row
snake reading cannot masquerade as straight row reading in that lesson.

`generate(seed, settings, demos=3, queries=4)` supports exact integer seeds
0 through 2**63−1, 3–6 demonstrations and 1–4 queries independently. Inputs are
identical across settings. The complete four-query bank is privately shuffled
before a query prefix is selected, so changing either count leaves earlier
pairs unchanged. Returned input and output rows are independently owned.

The root input-only API is self-contained:
`generate(seed, sample_index=0, *, difficulty=None, **overrides)`. Its ten
profiles cycle with the sample index, while a local seed stream changes each
sample. `difficulty` is accepted without changing the schedule; unknown
overrides are rejected. The parametric prototype loads this adjacent file by
exact path and exposes `program`, `mirror`, `analyze` and `first_stage`.
`AXES={}` declares that override contract. `self_check` returns an empty list
for valid inputs and findings strings for validation failures, matching the
native base worker's hook convention.

## Reproduce and hand off

From the outer packet, using its prepared Python 3.12 environment and Racket:

```sh
PYTHONDONTWRITEBYTECODE=1 WORK/.venv/bin/python review.py run python3 -m pytest --import-mode=importlib generators/public_eval_136b0064/tests -q
PYTHONDONTWRITEBYTECODE=1 WORK/.venv/bin/python review.py run python3 -m arcpuzzles.review_public_creation preflight public_eval_136b0064 --root . --out ../checks/public_eval_136b0064/preflight
```

Use fresh output paths when rerunning. `checks/PUBLIC_CREATION_TOOLS.md`
documents source-bound protected causal replay and actual single-query public
previews from an authoring preflight. Give a solver only one selected public
file at a time; future queries, directory listings, rules, settings, answers and
presentation permutations remain with the controller.

Python outputs are claims, checked through protected Racket execution. Bounded
semantic and rival checks do not prove unrestricted uniqueness or learning
gain. Owner registration, source review, native qualification and acceptance
remain separate from authoring preflight. No training admission is requested.
