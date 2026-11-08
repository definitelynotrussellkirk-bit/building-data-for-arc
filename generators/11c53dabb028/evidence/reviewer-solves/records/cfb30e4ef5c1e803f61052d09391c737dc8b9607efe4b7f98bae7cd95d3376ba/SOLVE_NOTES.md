# Visible-only blind solve notes

## Exposure and sources

I had no earlier exposure to the rule or solution. I read only the public
`solve-blind/README.md` and `solve-blind/challenge.json`, and performed my own
Python calculation on the visible training examples. I have not opened a
generator, Racket rule, canonical/reference solution, private label, private
review material, task notes, audit evidence, or previous solution explanation.

## Observations

- All five visible training outputs have twice the input height and twice its
  width. Their four input-sized quadrants are identical.
- Within an input-sized output quadrant, every input nonzero cell becomes zero,
  and every input zero cell becomes a single nonzero color.
- The chosen output color equals the first nonzero input value in row-major
  order in all five examples: 8, 3, 5, 5, and 5 respectively.
- Choosing the most common nonzero input color is inconsistent with the visible
  examples: example 1 has nonzero majority color 2 but output color 3; example 4
  has nonzero majority color 1 but output color 5.

## Hypothesis

Scan from top to bottom and left to right to find the first nonzero color.
Create a tile with that color at every input zero and zero at every input
nonzero. Repeat the entire tile twice horizontally and twice vertically.

The visible examples support this hypothesis, but they do not prove unique
behavior for every possible input. The implementation defaults the selected
color to zero for an all-zero input; no visible example establishes that case.

## Experiments and actual revision history

1. Before creating `solution.py`, I ran a Python calculation of the proposed
   transformation against each public training output. Exact matches were
   5/5, and cell mismatch counts were 0, 0, 0, 0, and 0. Input/output dimensions
   were 2x2/4x4, 4x6/8x12, 3x6/6x12, 4x4/8x8, and 10x7/20x14.
2. The same calculation recorded the first nonzero color, most common nonzero
   color, and actual nonzero output colors, supporting the observations above.
3. I confirmed that both public test entries contain only an input; their
   expected outputs are unavailable. I did not evaluate query correctness.
4. I wrote the first and only solver revision implementing the hypothesis.
   There have been no failed solver revisions or failed official checks before
   this note. The official visible-only check is the next action; its exact
   feedback and frozen revision are recorded by the review command.

If the official visible-only check confirms this revision, I intend to stop
because all available labeled examples are explained by the same simple rule.
Private query correctness must remain unknown during this blind solve.
