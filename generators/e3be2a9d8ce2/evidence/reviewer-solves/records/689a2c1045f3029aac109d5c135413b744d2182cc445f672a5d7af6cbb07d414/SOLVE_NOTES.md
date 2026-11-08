# Solve work log

## Exposure disclosure

I had already inspected this generator's rule and implementation during the assigned repair before the packet required the post-repair solve. I therefore record `earlier-exposure=yes`. During this solve I did not reopen the generator, Racket rule, reference solutions, private labels, or prior solution notes; I used only the prepared visible challenge and the check command.

## Hypothesis

Every nonzero input cell is an emitter. It keeps its color and draws two same-color arms: a vertical arm from the emitter to whichever of the top or bottom border is closer, plus a horizontal arm to whichever of the left or right border is closer. Exact center ties go down and right. All visible examples are consistent with this: top-left seeds make up/left L-shapes, bottom-left seeds make down/left L-shapes, and top-right seeds make up/right L-shapes.

## Implementation

`solution.py` collects emitters in row-major order, creates a zero grid of the same dimensions, and paints the selected inclusive row/column ranges. I used the integer comparisons `2*r < h-1` and `2*c < w-1`; equality therefore selects bottom/right. First paint wins only as a deterministic safeguard for overlapping rays. The shown examples appear deliberately disjoint.

## Alternatives considered

A tempting weaker rule is to extend every seed merely one cell in each direction, because several seeds sit one cell from a border. Example 1 refutes that: the two color-1 emitters at row 2 extend all the way to the top and their nearest side borders. Another alternative is choosing a direction from color or quadrant; the examples instead support independent nearest-edge choices on each axis.

## Remaining uncertainty

The examples do not visibly exercise an exact center tie or overlapping ray footprints. I use the previously disclosed tie convention only as an implementation choice and deterministic row-major first-paint behavior for overlap. The generated examples otherwise strongly determine the nearest-edge L-ray rule.
