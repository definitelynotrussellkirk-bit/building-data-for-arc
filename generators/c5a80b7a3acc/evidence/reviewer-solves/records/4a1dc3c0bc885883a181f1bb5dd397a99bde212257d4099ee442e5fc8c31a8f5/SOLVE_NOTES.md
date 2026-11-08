# Visible-only solve notes

I read only `solve/challenge.json` for puzzle information and `solve/README.md`
for the permitted workflow. I have not consulted the generator, reference rule,
private query labels, reports, or previous solutions. The finish command will
record earlier exposure as yes conservatively for coordinator exposure; I was
not given a rule in this solve.

## Inferred hypothesis

Extract all cells of color 2 and all cells of color 3. Normalize each shape
independently by moving its upper-left bounding-box corner to the origin.
If the input contains color 7, take the intersection of the normalized cell
sets. Otherwise take their symmetric difference. Ignore color 9. Render the
selected cells as 8 on zero, tightly crop the selected result, and return
`[[0]]` if no cells remain.

Examples 1 and 4 contain 7, and the aligned intersections match their cropped
outputs. Examples 2 and 5 have no 7, and their aligned symmetric differences
match the full three-by-three outputs. Example 3 has identical normalized
shapes and no 7, explaining its empty result. The differing red and green
bounding-box widths in examples 2 and 5 support alignment at the upper-left
corner rather than scaling or centering. No role for 9 is needed to explain
the visible examples.

## Revision 1

Implemented the above single hypothesis using coordinate sets. This is the
first candidate; no hypothesis sweep or private-answer inspection was used.
The intended check is the prescribed visible-example and query-execution
check. Masked query correctness will remain unknown to this solver.

## Provenance reset

The first managed execution of this candidate passed 5/5 visible examples and
completed execution, but finish encountered an existing frozen notes file.
The coordinator reported public records carried over from a previous episode,
archived that directory, and prepared a clean episode with the same challenge.
I restored only my own solution and notes, with no hypothesis or code change.
The repeated managed check is solely for clean provenance, not a solver
correctness failure. I did not inspect prior artifacts or private labels.


Coordinator execution note: Public carryover artifacts reappeared between separate tool calls. All such records were archived. The coordinator ran clean preparation, this unchanged isolated-solver candidate, and finish in one uninterrupted sequence. This is a provenance repair, not a new hypothesis or an incorrect solver attempt. Masked correctness remains unknown.
