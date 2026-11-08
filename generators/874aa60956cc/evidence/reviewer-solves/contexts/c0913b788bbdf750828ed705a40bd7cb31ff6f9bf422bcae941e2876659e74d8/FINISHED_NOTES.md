# Solve work log

## Prior exposure

Before this solve I had read only the packet-level workflow and the visible examples printed by `python3 review.py blind prepare`. I did **not** inspect this task's generator, Racket rule, reference solution, private labels, audit records, or the assigned repair generator.

## Revision 1 — diagnostic baseline

- **Program:** untouched template raising `NotImplementedError`.
- **Command:** `python3 review.py blind check --intent diagnostic_probe --note 'Harness baseline before implementation: template raises NotImplementedError; expected execution failure.'`
- **Observed:** execution error, 0/3 visible examples. This established the checker path before implementation.

## Revision 2 — rectangle-border hypothesis

### Observations

- In every training example, a nonzero color occurring exactly twice marks opposite corners of an axis-aligned rectangle. The output adds that rectangle's perimeter.
- Colors occurring once or more than twice do not generate a rectangle; their original cells remain unless another generated border overwrites them.
- Border conflicts are resolved by processing candidate colors in the row-major order of their **first input occurrence**. Later candidates overwrite earlier ones. This explains all visible intersections:
  - train 0 first occurrences are 3, 7, 6, so 6 overwrites both 3 and 7;
  - train 1 candidate first occurrences are 4, 3, 2, so 2 overwrites both;
  - train 2 first occurrences are 7, 1, 6, 9, so 6 overwrites 7 and 1.

### Implementation

1. Scan the original grid and store nonzero positions by color.
2. Select colors with exactly two positions.
3. Sort them by first row-major position.
4. Copy the input, then draw each inclusive rectangle perimeter in that order.
5. Preserve all untouched cells.

### Alternatives rejected

- Sorting by color, rectangle size, or second occurrence fails the visible overlap cases.
- Giving original seed cells unconditional priority fails where an original point is overwritten by a later rectangle.
- Filling interiors fails because outputs add only borders.

### Remaining uncertainty

The examples do not show a candidate color whose two points share a row or column. The implementation treats that as a degenerate rectangle (a line), which is the natural inclusive-perimeter extension. It also excludes background color 0 even if it happened to occur exactly twice.
