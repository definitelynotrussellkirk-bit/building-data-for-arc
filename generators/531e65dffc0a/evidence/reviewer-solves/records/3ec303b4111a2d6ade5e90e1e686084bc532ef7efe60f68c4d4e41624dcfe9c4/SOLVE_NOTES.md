# Post-repair visible-only solve work log

This is an assistant-authored work log, not a captured token-level trace.
The reviewer previously inspected this task's generator and Racket rule during
the repair, so earlier rule exposure is **yes**. After preparing this final
episode, I consulted only `solve/challenge.json`, my own Python and the visible
check feedback. I did not consult generator code, the reference rule, earlier
solution explanations or private query answers during the solve.

The unattempted preparation for an intermediate generator was archived under
`checks/prior-solve/v2-prepared-before-v21/`. It is not a solve of this version.
The current preparation reports seed 653293859 and final generator SHA-256
`704565e2cac3d04a427b95e0550d6461d948626144a5eb9598968a60554d1e58`.

## Revision 1 — rotation stamps

I inspected the three visible training pairs and both query inputs by printing
their nonzero coordinates, grouped by color, using Python's standard JSON
reader. The observations included:

- The first example has a six-cell color-7 prototype and one marker of each
  color 2, 3, 4 and 5. Its output contains only color 7 and background.
- In the second example, the prototype occupies (4,1), (4,2), (5,2). Marker 2
  at (3,7) produces (3,7), (3,8), (4,8), preserving the prototype's orientation.
- Marker 3 at (2,3) in that same example produces (2,4), (3,3), (3,4), the
  clockwise quarter-turn of the prototype in its bounding box.
- Marker 4 at the right edge produces a clipped copy. The third example also
  provides a marker-5 copy that is clipped at the right edge.

The implemented hypothesis is to extract the non-marker prototype, normalize
its bounding box, and stamp it at marker positions. Marker colors 2/3/4/5 select
zero/one/two/three clockwise quarter-turns. Use a fresh background grid, clip
individual pixels at the boundary, and merge overlapping copies in the
prototype color. This standalone Python does not import task or reference code.

This revision will be submitted with `--intent solve`. No intentionally wrong
revision was created. Alternatives such as moving a clipped copy inward or
keeping the original prototype are checked against the visible examples,
rather than installed as fabricated failed attempts. Two file-edit tool calls
were rejected for patch formatting before any file was changed or any solver
check was run; those were not solution revisions.

Remaining uncertainty before the check: these examples do not establish
behavior for multiple competing prototypes, ties, or unseen marker meanings.
Query correctness is withheld by the solve protocol.
