# Visible-only solve: 57bafcdde8c3

## Information boundary

I read only `WORK/solve-blind/README.md` and
`WORK/solve-blind/challenge.json` as puzzle material. I had no earlier
rule exposure and did not consult any reference solution, generator,
rule file, private answer, canonical data, prior solution notes, audit
data, or `.review` internals. The authorized wrapper commands may handle
private material internally; I do not inspect that material.

## Observations and hypothesis

Each visible training input has two colors. The more frequent color is
unchanged. Some cells of the less frequent color become 8. Every such
cell has another cell of its own color immediately above, below, left,
or right. Foreground cells without these neighbors remain unchanged,
even when touching another foreground cell diagonally.

Hypothesis: identify the most frequent color as background, then recolor
each non-background cell with a same-color cardinal neighbor to 8.
Equivalently, recolor every same-color foreground component of size at
least two under four-neighbor connectivity. Preserve grid dimensions
and all other cells. Read adjacency from the original input so that
recoloring does not change later decisions.

## Visible-only probe

Before writing the solver, I ran an inline Python probe from the packet
root. It read only the visible challenge, computed the predicted changed
coordinate sets, and compared them with the training outputs. Exit code:
0. All changed sets matched exactly, and every observed change was to 8.

| Training example | Background | Foreground | Observed changes | Predicted changes | Diagonal-only foreground cells left unchanged |
| --- | --- | --- | ---: | ---: | ---: |
| 0 | 1 | 0 | 17 | 17 | 12 |
| 1 | 1 | 3 | 30 | 30 | 10 |
| 2 | 7 | 3 | 41 | 41 | 4 |
| 3 | 1 | 0 | 9 | 9 | 10 |

## Solver revisions and verification

Revision 1 implements the first hypothesis above, with no alternate
solver revision or manufactured failure. It uses Python's standard
library, returns a new grid, and does not assume a fixed 13-by-13 shape
or fixed foreground/background colors. The required next verification
is the authorized `review.py blind check` wrapper, followed by
`review.py blind finish` with both exposure declarations set to `no`.

## Limitations

Visible data supports this rule for two-color inputs with a clear
majority background. Inputs with a tied color frequency or several
foreground colors are not demonstrated. The implementation handles
same-color adjacency independently for each non-background color, but
that extension is an inference. The two test outputs are unknown to me;
matching the training examples does not establish private-query
correctness.
