# Blind solve work log

## Exposure and scope

I had no earlier exposure to the Racket rule or any reference solution. During
this solve I read only the public `challenge.json`, the public solve-directory
`README.md`, the initial `solution.py` stub, and this work-log template. An
attempt to read a packet-root `README.md` found no such file. I did not open
generator implementations, canonical data, audit records, private labels,
hidden review metadata, or earlier solution explanations. The parent provided
the target identifier, the permitted paths, and the `review.py` entrypoint
commands, but no hidden transformation information.

There are three labeled training pairs and two query inputs without outputs.
All query results below are predictions. No query correctness is observable.

## Observations and competing hypotheses

Every displayed input has a background of 7 and a full bottom row of 8. The
bottom row is unchanged in all three training outputs. The foreground consists
of two separated objects. Each training object occupies four cells in an L
shape, includes two colors, and remains one object under orthogonal adjacency
when colors are ignored. Shape, individual cell colors, and column positions
are preserved. Every foreground cell moves upward by exactly four rows.

A direct Python analysis of the public labeled pairs extracted orthogonally
connected components, matched them by their leftmost column, and compared
their complete colored coordinate lists. It found:

| Training pair | Left object cells / upward shift | Right object cells / upward shift | Colored shape preserved |
| --- | --- | --- | --- |
| 0 | 4 / 4 | 4 / 4 | Yes, both objects |
| 1 | 4 / 4 | 4 / 4 | Yes, both objects |
| 2 | 4 / 4 | 4 / 4 | Yes, both objects |

The leading hypothesis is that each connected object rises by its own cell
count. This connects the observed distance to an object property and naturally
extends to the six-cell bars in query 0. I selected it as an inference, not as
a uniquely established rule.

An equally fitting simple alternative is a fixed upward shift of four rows.
The training data do not distinguish those two rules. They also do not
distinguish cell count from some other shape measurements on these particular
L shapes, or from rules involving the shared color counts. Splitting an object
by color would give two cells per piece, which would not explain a direct
per-piece cell-count shift of four; this supports grouping adjacent colors into
one foreground object, but does not prove the distance rule.

Both training objects always have the same size, so the data cannot establish
whether different-sized objects would move independently. Orthogonal versus
diagonal connectivity is also not distinguished by the visible shapes.

## Revision 1: rise by connected-object cell count

This is the only implemented solve attempt. The initial stub raised
`NotImplementedError`; there were no failed candidate implementations.

The implementation copies the grid, treats colors other than 7 and 8 as
foreground, groups those cells by orthogonal adjacency regardless of color,
clears their original positions to 7, and redraws each component after moving
it upward by its number of cells. All original foreground positions are
cleared before any object is drawn. This preserves the floor, shapes, and
colors in the displayed examples and avoids erasing a newly drawn object when
handling a later component. The input is not modified.

The empty-grid case returns an empty grid. Ragged rows are rejected. An object
whose inferred translation would extend above the grid raises a clear error,
rather than acquiring an accidental wraparound from negative Python indices.
No supplied input has that issue. There is no evidence here for a top-edge
clipping rule, arbitrary recoloring, or handling overlapping translated objects.

### Public-data probes and results before the official check

Two inline `python3` probes were run from the packet root. The first loaded
only `WORK/solve-blind/challenge.json`, extracted components and measured the
training displacements listed above. It also compared the leading hypothesis
against the fixed-four alternative on the public query inputs:

| Query / object | Cell count | Input top row | Predicted top, cell-count rule | Predicted top, fixed-four rule |
| --- | --- | --- | --- | --- |
| 0 / left bar | 6 | 6 | 0 | 2 |
| 0 / right bar | 6 | 7 | 1 | 3 |
| 1 / left L | 4 | 9 | 5 | 5 |
| 1 / right L | 4 | 8 | 4 | 4 |

The second probe loaded the implementation with
`runpy.run_path('WORK/solve-blind/solution.py')['solve']` and called it on every
public input. It compared training predictions with their supplied outputs
and checked query execution, dimensions, color counts, bottom-row preservation,
and input immutability. Observed results:

- Exact training matches: **3 of 3**.
- Public query executions: **2 of 2**, with no exceptions.
- All five input grids remained unchanged.
- Both query predictions retain dimensions, total color counts, and the floor.
- Query 0 predicts the six 2 cells on row 0, columns 1 through 6, and the six 4
  cells on row 1, columns 9 through 14.
- Query 1 predicts 2 at (4, 6), (5, 6), (5, 7), (5, 8), and 4 at (5, 1),
  (6, 1), (6, 2), (6, 3). Coordinates are zero-based.

These checks verify implementation and visible agreement, not hidden query
correctness. They do not resolve the competing explanations.

### Required check and finish

After writing this revision and log, run the authorized check from the packet
root. The check result is retained by the review entrypoint; this log does not
pre-claim its outcome:

```sh
python3 review.py blind check --intent solve --note 'Revision 1: each orthogonally connected multicolor foreground object rises by its cell count; local checks match all 3 labeled pairs and execute both public queries, but fixed-four movement remains a visible-data alternative.'
```

If the official visible checks and executions agree with the local results,
finish this one-attempt episode with:

```sh
python3 review.py blind finish --earlier-exposure no --reference-consulted no --reason 'The single object-cell-count lift implementation matches all 3 visible training examples and executes both public query inputs. The displayed training data cannot distinguish a size-dependent lift from a fixed four-row lift; no hidden outputs or references were consulted, so further revisions would lack new evidence.'
```

The stopping rationale is finite visible evidence and a working, explicit
hypothesis. Confidence is high in the observed four-row training translation
and in the implementation of the selected rule; confidence is lower in the
unseen six-cell extrapolation. Private query correctness remains unknown.
