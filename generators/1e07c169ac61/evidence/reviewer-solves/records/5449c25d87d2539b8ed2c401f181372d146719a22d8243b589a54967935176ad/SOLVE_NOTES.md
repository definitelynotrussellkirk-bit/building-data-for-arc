# Visible-only solve work log

Assignment: review-0a7960b3204c9f47. Task: 1e07c169ac61.

## Evidence boundary

I read only the prepared WORK/solve-blind/README.md and challenge.json,
listed that solver-facing directory, and created my own code and experiments.
I have not opened generator or Racket source, canonical data, reference answers,
task/audit notes, private review state, or previous solutions. No external
service or additional agent was used. Earlier rule exposure: no.
Reference consulted: no.

## Initial hypothesis and manual checks

Every visible input and output has one colour-9 cell in the same position.
The shape, colour multiset, and number of foreground cells are preserved.
The candidate operation is a clockwise quarter turn of every foreground cell
around that 9, with zeros remaining the background on the original canvas.
With row coordinates increasing downwards, the relative map is
(dr, dc) -> (dc, -dr). Thus the absolute map is
(r, c) -> (pivot_row + c - pivot_col, pivot_col - r + pivot_row).

Examples traced before coding:

- Train 0: pivot (4,6); (5,2) becomes (0,5), (6,2) becomes (0,4).
- Train 1: pivot (4,2); 4 at (5,2) becomes (4,1), and 4 at (6,4)
  becomes (6,0). This distinguishes a rotation from a simple translation.
- Train 2: pivot (4,4); isolated 7 at (5,1) becomes (1,3), and 7 at
  (3,5) becomes (5,5). Disconnected pixels follow the same map.
- Train 3: pivot (7,4); 2 at (4,1) becomes (4,7), and 3 at (7,2)
  becomes (5,4), preserving individual colours.

## Probe and implementation, revision 1

I wrote a visible-only probe comparing the eight square symmetries about
colour 9, with exact colour-aware coordinate-set comparison against each
visible output. This checks direction and reflection alternatives without
consulting hidden outputs. The probe exited 0: clockwise_90 matched 4/4,
and each of the other seven alternatives matched 0/4. These are hypothesis
comparisons, not submitted solver revisions or invented failure episodes.

I will submit revision 1 to the public checker with the intent note:
"Rotate all nonzero cells clockwise about the unique 9; all four manual
traces and the eight-transform visible probe support this map."

The implementation finds the unique 9 and rotates all nonzero cells with
the coordinate map above, including the stationary pivot. It returns a fresh
same-sized grid. The visible data does not establish behaviour for multiple
or missing pivots, nonzero backgrounds, or foreground that rotates outside
the canvas; the implementation rejects these malformed or unsupported cases
rather than guessing a clipping or resizing rule.

No failed solver revision has occurred. The initial edit was overwritten
before any execution to ensure the prepared placeholder could not remain as
a second solve definition. This was an untested file-write correction, not a
hypothesis revision or a checker failure.

## Commands and remaining uncertainty

All probe, check and finish commands run from the packet root and are captured
by WORK/checks/blind/visible-rotation/record_command.py. Exact arguments,
working directory, exit code, stdout and stderr are saved alongside that
script in command-receipts.jsonl and per-command logs.

There are four labelled examples and two unlabelled queries. Visible fit can
support this simple rule but cannot certify hidden correctness. Query outputs
and checker/finish results will be recorded after execution.
