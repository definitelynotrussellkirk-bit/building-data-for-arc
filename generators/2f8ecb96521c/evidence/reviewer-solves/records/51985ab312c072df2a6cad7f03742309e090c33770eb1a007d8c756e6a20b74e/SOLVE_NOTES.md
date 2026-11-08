# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Exposure and scope

I had no earlier rule exposure. I read only this directory's README.md,
challenge.json, initial solution.py, and initial SOLVE_NOTES.md before solving.
I have not consulted generators, Racket, reference solutions, private labels,
catalogs, prior explanations, or audit evidence.

## Revision 1: component size determines interior color

Observed actual shapes (rows x columns): training 0 is 10 x 13 in/out;
training 1 is 10 x 11 in/out; training 2 and 3 are 10 x 10 in/out.
Both masked queries are 10 x 10 inputs with unknown outputs.

Each training input has two separated solid yellow rectangles. Coordinates are
zero-based and bounds inclusive:

* Train 0: rows 0..3, columns 9..11 = 4 x 3, area 12, interior becomes 1;
  rows 5..8, columns 6..9 = 4 x 4, area 16, interior becomes 2.
* Train 1: rows 0..4, columns 3..5 = 5 x 3, area 15, interior becomes 2;
  rows 0..3, columns 7..9 = 4 x 3, area 12, interior becomes 1.
* Train 2: rows 0..2, columns 2..5 = 3 x 4, area 12, interior becomes 1;
  rows 4..8, columns 3..7 = 5 x 5, area 25, interior becomes 2.
* Train 3: rows 3..7, columns 1..5 = 5 x 5, area 25, interior becomes 2;
  rows 4..7, columns 7..9 = 4 x 3, area 12, interior becomes 1.

Hypothesis: preserve the background and a one-cell yellow border around each
rectangle. Color the smaller rectangle's strict interior blue (1), and the
larger rectangle's strict interior red (2). Implementation finds 4-connected
yellow components, sorts by area, and uses increasing ranks for interior color.
Only the two-component case is supported by the examples.

Alternatives: blue might specifically mean a 3 x 4 rectangle or area 12,
rather than relatively smaller. Visible data cannot distinguish these from
size ranking: all four small rectangles have area 12. Position and scan order
are contradicted by training 1 and 3, where the red rectangle appears first.
Orientation cannot alone determine color because training 1 has both rectangles
vertical. Interior area ranking is also consistent and equivalent here.

Masked-input inspection only: query 0 has 4 x 3 (area 12) and 4 x 4 (area 16)
rectangles; query 1 has 4 x 3 (area 12) and 5 x 3 (area 15) rectangles. Thus the
area-12 alternative and relative-size hypothesis predict the same outputs for
these inputs, but their actual labels are unavailable. Equal-area ties and
inputs with more than two components remain untested and unidentifiable here.

The initial placeholder was replaced by this first substantive hypothesis.
No artificial failing revision was created.

### Planned public check

From /workspace/scratch/4bbe6d6743f0/arc-review:

`/workspace/scratch/4bbe6d6743f0/arc-review/WORK/.venv/bin/python review.py blind check --intent solve --note 'Smaller yellow rectangle gets blue interior; larger gets red; retain one-cell yellow borders'`
