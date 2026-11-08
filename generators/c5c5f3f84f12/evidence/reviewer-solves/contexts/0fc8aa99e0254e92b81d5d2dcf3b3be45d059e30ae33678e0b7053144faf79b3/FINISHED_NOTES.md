# Solve work log

## Exposure declaration before solving

I had already reviewed this task's generator and authority before this required post-repair solve, so earlier rule exposure is **yes**. During both solve records I did not consult the generator, Racket rule, reference solutions, or private labels; I used the visible challenge and local solve feedback. The first completed record is preserved under `checks/prior-solve/attempt-1-execution-error/` rather than erased.

## Visible-example hypothesis

Each input contains one red(2) object, one blue(1) corner singleton, and one differently colored corner singleton. Across the four visible examples, the blue corner—not the other singleton—orders the transformation: top-left leaves the red shape unchanged, top-right rotates it 90 degrees clockwise, bottom-right rotates it 180 degrees, and bottom-left rotates it 270 degrees clockwise. The output is the red object's normalized bounding box recolored cyan(8).

## Failed revision retained

The first standalone implementation encoded that rule correctly but passed a generator expression into `_normalize`. `_normalize` called `min` twice, so the first call consumed the iterator and the second raised on an empty sequence. The harness reported `execution_status: error`, 0/4 visible, which identified an implementation defect rather than a rule-hypothesis failure.

## Corrective revision

The only semantic-neutral change is to materialize `cells = list(cells)` once at the start of `_normalize`. The solver then extracts the blue corner and red cells, normalizes coordinates, applies the corresponding clockwise quarter turns, crops the result, and writes color 8. The non-blue corner singleton is deliberately ignored.

## Remaining uncertainty

The visible examples cover all four control corners and distinguish the colored distractor from the blue control. Private-query correctness remains withheld by design.
