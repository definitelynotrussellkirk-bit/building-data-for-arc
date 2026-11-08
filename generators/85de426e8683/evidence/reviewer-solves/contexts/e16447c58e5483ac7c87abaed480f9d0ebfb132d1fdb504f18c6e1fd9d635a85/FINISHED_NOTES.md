# Solve work log

I had not opened this task's generator, Racket rule, private labels, solutions,
or earlier explanations. I only read `solve-blind/challenge.json`.

## Revision 1 — isolated diagonal triples

Hypothesis: color 5 forms several objects. The transformation selects an
8-connected component consisting of exactly three cells in a straight diagonal
line and recolors its middle cell to 4. Horizontal or vertical triples are left
alone, a diagonal component of length five is left alone, and the joined
five-cell zig-zag in training example 3 is left alone because it is one larger
8-connected component rather than two isolated triples. Other colors are
unchanged distractors or pre-existing cells.

Evidence from the visible examples:

- Example 1 has two isolated diagonal triples; both centers become 4.
- Example 2 has a diagonal length five and a separate diagonal length three;
  only the latter changes.
- Example 3 has two isolated diagonal triples, both changed, plus an overlapping
  diagonal cluster of five cells, unchanged.
- Example 4 contrasts isolated diagonal triples against a horizontal triple and
  a vertical triple; only the diagonal centers change.

Implementation probe: find 8-connected components of 5, require exactly three
cells with consecutive rows and constant column step of +1 or -1, then recolor
the middle row's cell. Remaining uncertainty: whether connectivity should be
8-neighbor or an object-specific diagonal connectivity; the visible joined
zig-zag strongly supports 8-neighbor component isolation.
