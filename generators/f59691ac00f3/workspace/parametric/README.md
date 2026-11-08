# Native parent-choice family

`adapter.py` and `promotion.json` are the current generation entrypoint. They
reuse the exact Racket materializer in `prototype.py`. The canonical generator
and reference authority retain their original bytes. Owner acceptance of the
integrated native source is separate from the review evidence supplied here.

| Contract | Value |
|---|---|
| Episode parameter | `different_parent`: `right` or `left` |
| Canonical default | `right`, byte-for-byte canonical Racket |
| Demonstrations | Independently requested, 2–6; ordinary use: 3 |
| Queries | Independently requested, 1–4; training lessons: 4 |
| Setting-dependent input constraints | None; equal seed/counts give identical inputs |
| Label authority | Exact materialized rule executed through Racket |

Both rules grow a diagonal cellular automaton downward from top-row seeds.
Either missing parent leaves background 7. Equal active parents invert 2↔5;
different active parents copy the selected right or left parent. Each setting
is fixed for the entire episode. A mathematically equivalent color formula is
complement-left for `right`, or complement-right for `left`, retaining both
support gates. Such equivalent programs are valid answers.

## Teaching and input coverage

The native family extends only the task-local input grammar to boards within
3–30 rows and 5–30 columns. Top-row seeds are 2/5; lower input rows are all 7.
The canonical production generator retains its original 3–8 by 5–16 bounds.

The first mandatory demonstration is a dense 16×30 board, containing all four
active parent pairs and reaching depth 14 followed by extinction. The second
is a 12×23 gapped board: some cells have active outer ancestors but an absent
internal ancestor. This teaches the full ancestry gate, defeating a plausible
endpoint-only formula. Optional demonstrations add uniform colors, single
parity support and additional gap profiles.

The four query slots are a 3×5 minimum case, an 11×19 gapped case, a dense
30×30 case and another 30×30 case with gapped, uniform-color or single-parity
support. The last profile cycles across seeds. Train/query RNG streams are
separate; query prefixes remain identical when either requested count changes.
Dimensions and support profiles guarantee distinct inputs without retries.

The dense 30×30 output has 240 active cells, including 210 descendants, and
14 active descendant rows. This is the maximum for top-only width-30 input:
active widths are 30, 28, …, 2. Rows 15–29 necessarily remain background.
There is no claim of 30 active recursion steps. These fixed profile slots
exercise shape, support, color and boundary variation, not every possible
dimension or every legal top-row support mask.

## Runnable checks

Use the packet's prepared Python environment from the outer packet directory:

```bash
WORK/.venv/bin/python review.py task-tests f59691ac00f3 --phase after \
  --out ../checks/f59691ac00f3/new-task-tests

WORK/.venv/bin/python review.py run python3 \
  generators/f59691ac00f3/workspace/parametric/self_audit.py native \
  --seed 0 --demos 2 --queries 4 --out ../checks/f59691ac00f3/new-self-audit.json

WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric qualify \
  f59691ac00f3 --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/f59691ac00f3/new-qualification --summary
```

Output paths must be new. If a task source changes, refresh the task-local
inventory with `arcpuzzles parametric manifest` before qualifying again.

After owner qualification and acceptance, the standard native exporter is:

```bash
python3 -m arcpuzzles parametric export f59691ac00f3 \
  --count 2 --seed 0 --demos 3 --queries 4 --out var/parent-choice-lessons
python3 -m arcpuzzles parametric verify-export var/parent-choice-lessons
```

The generated public container is controller data. Reveal only one query per
model turn, keeping settings, programs, query labels, future inputs and total
counts private. The retained `checks/f59691ac00f3/check_projection.py` uses the
existing native public projector to verify individual views and identical first
turn bytes against a separately generated single-query request. It adds no
training loop or turn controller.

## Current evidence and limits

`self_audit.py original` replays two inherited lessons where a depth-limited rule
fits every demonstration and changes a query. Those original lessons and both
Racket programs remain useful alternative-answer evidence. `self_audit.py native`
checks opposite setting, demonstration-derived depth limit, frozen input
parents, omitted opposite support, endpoint-only support, and an equivalent
complement control. Only these finite rivals and recorded seeds are assessed.

The older `prototype.make_episode` / `prototype.py --out` sampler is retained
for legacy evidence replay. It is not the native lesson-generation route and
its short demonstrations retain the documented depth ambiguity. Its public
writer is repaired: all visible bytes are precomputed, duplicate IDs rejected,
and the full batch sorted by visible hash before any public write.

The row-to-row Racket execution has an input-dependent intermediate: previously
generated parent colors and support decide the next row. The protected witness
shows that substituting original blank parents changes the final answer. A
fully gated top-row closed form is also valid; this witness establishes the
dependency in the reference execution, not a lower bound on all algorithms.

Qualification and reviewer reports do not imply owner acceptance or training
admission. The owner must qualify and accept the exact integrated source.
