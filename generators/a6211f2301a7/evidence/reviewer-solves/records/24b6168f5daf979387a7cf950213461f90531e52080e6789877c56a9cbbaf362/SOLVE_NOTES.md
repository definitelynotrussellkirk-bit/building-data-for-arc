# Blind solve: a6211f2301a7

I had no earlier exposure to this task's rule. I read only the preparation
output and public challenge. No generator, reference program, private label,
canonical record, or prior solution explanation was opened.

## Hypothesis and visible probes

The nonzero bounding box is 2 x 3 in training example 0; its output is 3 x 2.
The crop `[[2,0,3],[0,0,1]]` becomes `[[0,2],[0,0],[1,3]]` after a clockwise
quarter-turn. Example 1 has a 4 x 2 crop and a 2 x 4 output. Example 2 has a
2 x 3 crop and a 3 x 2 output. A visible-data-only Python probe enumerated
all four rotations of each nonzero crop. Only one clockwise quarter-turn
matched each of the three visible outputs.

Cropping alone, counterclockwise rotation, and a half-turn did not match.
Colors and internal zero cells are preserved; empty margins are removed.
The implementation uses that direct rule. Empty input foreground is outside
the visible evidence and returns an empty list defensively.

An independent collaborator was restricted to the same two public files to
check the hypothesis; its conclusion will be recorded before finishing.

## Revision 1

First genuine solve attempt: nonzero bounding box, then 90 degrees clockwise.
No deliberate wrong attempt or fabricated revision was created. Masked query
answers and output dimensions remain unknown; only the tool may score them
later. The checker below measures visible examples and execution only.
