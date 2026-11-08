# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Visible-only analysis and revision 1

Earlier exposure: I had not opened this task's generator, canonical rule,
reference solution, private labels, notes, or audit evidence. I used only the
prepared visible challenge and my own parsing scripts.

I first identified the blue/orange separator rows and columns and treated each
rectangle as a room. The output length is always the number of rooms minus one,
and the visible 8 is at index `i` exactly when the selected orange horizontal
link joins row-major rooms `i` and `i+1` (examples: 0–1, 17–18, and 8–9).

I compared all orange-linked horizontal pairs by overlaying their interiors in
room-local top-left coordinates. The selected pair has the largest number of
coordinates occupied by a red/green cell in both rooms. Two visible ties need
secondary evidence: same-color overlaps distinguish example 0; equal room shape
distinguishes example 2. Example 1 is already unique on occupied overlap (3 vs
at most 2). I therefore implemented the lexicographic score
`(occupied overlap, same-color overlap, equal-shape flag)`, with earliest
row-major position only as a final deterministic tie-break.

Visible test predictions before checker feedback: query 0 selects boundary 0
(overlaps 3, 1, 0); query 1 selects boundary 1 (overlaps 3, 2, 1). Remaining
uncertainty: the intended comparison may phrase the secondary tie-break more
semantically than this finite-example rule, but the primary overlap mechanism
and output indexing are strongly supported by every visible pair.
