# Blind visible-only solve work log

This is an agent work log, not a token-level transcript. I have not opened any generator, Racket rule, reference solution, canonical task data, previous solution explanation, or audit evidence. Preparation handles references automatically and reveals only public examples. Earlier rule exposure: no. Reference consulted during solve: no.

## Visible observations and initial hypothesis

- Train example 0: Input 12 rows × 11 columns. Output 3 rows × 3 columns. The output crops the seven-cell orange (7) object at the top-right. The two separate green (3) objects have 5 and 6 cells, so grouping solely by color would select the wrong color. A maroon (9) object also has 7 cells. The shown choice is the first tied object in row-major traversal. The yellow square has 4 cells.
- Train example 1: Input 12 rows × 12 columns. Output 2 rows × 4 columns. The output crops the six-cell green (3) object, larger than the five-cell maroon (9), four-cell orange (7), three-cell blue (1), and two-cell gray (5) objects.
- Train example 2: Input 12 rows × 11 columns. Output 4 rows × 3 columns. The output crops the seven-cell red (2) object, larger than the six-cell orange (7) and five-cell cyan (8) objects.
- Test query 0: Input 10 rows × 13 columns. Output unknown. There are two disconnected red (2) objects of 4 and 5 cells, plus tied six-cell cyan (8) and gray (5) objects. My proposed tie handling chooses the cyan component because its first occupied cell precedes the gray component in row-major order.
- Test query 1: Input 11 rows × 13 columns. Output unknown. The cyan object has 7 cells; the green rectangle has 6; the red object has 5.

The simplest shared explanation is to find same-color orthogonally connected nonzero objects, choose the one with the greatest occupied cell count, and crop it to its bounding box without changing its color or orientation. Zero fills unoccupied positions within that box. The examples do not distinguish 4-connectivity from 8-connectivity on all possible inputs. One visible tie supports row-major ordering but also admits other tie rules, such as minimum bounding-box area. Those alternatives remain uncertain. I chose row-major order as a straightforward consistent rule.

## Revision 1

Implemented a standard-library flood fill for four-neighbor monochromatic components, maximum cell-count selection, strict-greater replacement to retain the first tie, and an isolated component crop. No deliberate negative attempt was manufactured. The next public check tests all three visible examples and execution on the masked queries; it cannot determine hidden query correctness.
