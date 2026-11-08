# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1 — harness diagnostic

- Earlier reference exposure: none. I have not opened any generator, canonical rule,
  private label, or prior solution explanation for task `71982ba2b59e`.
- Command: `python3 solve_episode.py blind check --intent diagnostic_probe ...`
- Observation: the prepared `NotImplementedError` stub produced an execution error,
  confirming the visible-example checker is exercising `solve(grid)`.

## Revision 2 — object relation matrix

### Observations

Each output is square, with side length equal to the number of 4-connected,
single-colour non-background objects in the input. Ordering the objects by their
topmost row and then leftmost column makes the diagonal equal to the object
colours in all three demonstrations:

- example 0: object colours `2, 6, 2, 6`;
- example 1: object colours `6, 5, 6, 5, 5`;
- example 2: object colours `2, 1, 1, 1`.

The symmetric off-diagonal entries have a consistent interpretation:

- `8` when the two component shapes are congruent after rotation/reflection;
- otherwise `6` when the two objects have the same colour;
- otherwise `0`.

Examples supporting this include the vertical and horizontal 3-cell lines in
example 0 (`8`), the two rotated T tetrominoes in example 1 (`8`), and the two
2×2 squares of different colours in example 2 (`8`). Same-colour but
non-congruent pairs are `6` throughout.

### Remaining ambiguity and choice

No demonstration pair is simultaneously the same colour and the same shape,
while both test inputs contain such a pair. I choose shape-match precedence
(`8` before `6`) because `8` consistently denotes the stronger geometric
relation, independent of colour; colour equality is used only when shape
congruence does not already explain the pair.

### Implementation plan

1. Extract 4-neighbour connected components, requiring equal nonzero colour.
2. Sort components by `(minimum row, minimum column)`.
3. Canonicalize each shape over all rotations and reflections after translating
   coordinates to the origin.
4. Fill the diagonal with source colours and off-diagonal cells using the
   precedence above.

### Visible check and query predictions

The visible checker completed all 3/3 demonstrations successfully. The solver
predicts:

- query 0: `[[8,8,6,8],[8,2,0,8],[6,0,8,6],[8,8,6,8]]`;
- query 1: `[[8,6,8,0,8],[6,8,0,0,6],[8,0,5,0,8],[0,0,0,2,0],[8,6,8,0,8]]`.

I am stopping because the rule accounts for every visible relation and the only
remaining uncertainty is the explicitly documented precedence when both
relations hold; masked-query feedback is intentionally unavailable.
