# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1 — path with endpoint terminal arms

- Earlier exposure to this task: none. I had not opened its generator, rule,
  references, notes, or private labels.
- The nonzero cells form a 4-connected tree. Colors 2 and 1 mark two vertices;
  color 5 is the rest of the tree.
- The unique path between the marked vertices becomes color 4 (apart from the
  markers themselves). Branches attached to interior path vertices also become
  4.
- Starting from each marker and walking toward the other marker, the first path
  vertex with an off-path branch is that marker's junction. The complete
  off-path subtree at that junction takes the marker's color: 2 at one end and
  1 at the other.
- This explains markers that are themselves junctions (examples 0, 2, and 3)
  as well as leaf markers whose adjacent path vertex is the junction (examples
  1, 2, and 3). It also distinguishes the interior side branches, which remain
  4.
- I rejected a simple connected-component rule because example 1's gray cells
  are one connected component but receive all three output colors.
- Remaining uncertainty: the visible examples are trees and have exactly one
  marker of each color; the implementation leaves malformed or disconnected
  cases unchanged rather than guessing.
