# Solve work log

## Exposure

Before this solve I had not opened the task's generator, canonical rule, private
labels, reference solutions, audit evidence, or any earlier solution explanation.
I used only the visible grids printed by `review.py blind prepare` and the public
`challenge.json`.

## Revision 1 — paired key and candidate panels

The full-height color-9 columns split every input into five panels with widths
3, 4, 3, 4, and a wider clue area.  The first and third panels each contain a
3×3 colored key; the following 4-column panel is its candidate answer.  In every
training example, the far-right clue contains an exact translated copy of one
key in that key's own color, sometimes interleaved with pixels of another color.
The output is the 4×4 candidate immediately following the reproduced key.

I checked this manually across all five examples: examples 0 and 4 reproduce the
left key and select the first candidate; examples 1–3 reproduce the right key and
select the second candidate.  The implementation therefore splits on full 9
columns, normalizes each key's same-color coordinates, compares them with the
same color in the clue, and crops the uniquely selected candidate to four rows.

Remaining uncertainty: the visible lesson always gives exactly one matching key
and candidate foreground spanning four rows.  The program rejects malformed or
ambiguous layouts rather than guessing.
