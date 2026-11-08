# Solve work log — 2376352117fc

This is an assistant-authored work summary, not a token-level conversation trace.
Earlier rule exposure: no. Only the preparation output and public challenge were
read; no generator, rule, notes, audit, reference solution or private labels were
opened before or during this solve.

## Revision 1

Hypothesis: use the vector from the single blue (1) marker to the single red (2)
marker to translate all green (3) cells. Paint surviving translated cells cyan
(8) on an otherwise empty grid with the input dimensions. Clip at the grid edge.

Visible evidence, with dimensions measured independently:

| Example | Input | Output | Blue → red displacement | Exact translated-cell match |
| --- | --- | --- | --- | --- |
| 0 | 7 rows × 18 columns | 7 rows × 18 columns | (1, -7) | 6/6 cells |
| 1 | 8 rows × 15 columns | 8 rows × 15 columns | (3, -2) | 5/5 cells |
| 2 | 15 rows × 10 columns | 15 rows × 10 columns | (0, -8) | 2/2 cells |

A Python probe over challenge.json computed marker coordinates, translated green
coordinates, and compared them with the visible cyan coordinates. All three
matched. Example 2 supplies the clipping witness: one of three translated cells
would lie in column -1 and is absent. No program revision or rejected attempted
solution preceded this one; no artificial failure was manufactured.

Queries have known input dimensions 8 × 10 and 13 × 12; their outputs are unknown.
The proposed rule can erase a shape entirely when every translated cell leaves
the grid. Query predictions will be checked for execution only; hidden correctness
remains for independent maintainer scoring.

Official revision-1 visible check completed: 3/3 examples passed; query execution
completed. Hidden-query label is unknown, as required. I stopped with this single
supported revision; the program and work log are retained by the finish command.
