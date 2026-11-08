# Public-example solve work log

This is a reviewer-authored model work log: a concise record of hypotheses, experiments, decisions, and uncertainties. It is not a token trace or a transcript of hidden internal reasoning.

## Scope and exposure

This solver episode was dispatched fresh with no task-rule history. The overall reviewer had earlier exposure, so finalization must record `--earlier-exposure yes`. During this episode I read only the prepared public examples, `WORK/solve/README.md`, `WORK/solve/challenge.json`, and public solve artifacts. I did not consult generator source, a Racket rule, a reference solution, private query labels, prior solve notes, or sibling task metadata.

The task contains three labeled training examples and two unlabeled queries. Training shapes are respectively 10 x 11, 12 x 12, and 12 x 12 for both input and output. Query input shapes are 11 x 24 and 10 x 11; their true output shapes and correctness are unknown.

## Hypotheses and public experiment

Initial hypothesis: count the blue (1) cells in the top row to obtain a one-based descending size rank. Find green (3) components using orthogonal connectivity. Recolor the component at that rank red (2), retaining all other cells and the grid dimensions.

I also evaluated two plausible alternatives in a public-data measurement script: using all blue cells as the rank and connecting green cells diagonally. These were actual diagnostic comparisons, not submitted solver revisions or intentionally failing checks. The measurements are saved in `public_observations.json`.

| Example | Top-row blue count | All blue count | Orthogonal component sizes, descending | Recolored size | Proposed selection matches |
| --- | ---: | ---: | --- | ---: | --- |
| Train 0 | 2 | 4 | 6, 5, 2, 1 | 5 | Yes |
| Train 1 | 3 | 3 | 16, 14, 10, 3 | 10 | Yes |
| Train 2 | 2 | 4 | 4, 3, 2, 1, 1 | 3 | Yes |

The all-blue rank and diagonal-connectivity alternatives each disagree with training examples 0 and 2. In those examples, a small green component diagonally touches the recolored component but remains green, supporting orthogonal connectivity. The blue cells away from the top row remain present without increasing the observed rank. In example 1, the three top-row blue cells are separated, supporting a cell count rather than a count of a single contiguous run.

For query 0, the observed top-row count is 1 and the orthogonal green component size list is [11]. For query 1, the count is 2 and the size list is [6, 5, 2, 1, 1]. These are input-derived measurements only; no query labels were accessed.

## Actual implementation revision 1

Implemented the top-row rank / orthogonal green component hypothesis in `solution.py`. The function creates a copy, finds the components, sorts them by descending size, and recolors the selected component. The equal-size fallback is row-major order. If the count is outside the component range, it leaves the copy unchanged. Those fallback decisions are not established by the visible labels, and neither affects the observed selected ranks.

There has been one genuine implementation revision. No intentionally incorrect solver was written and no negative checker result has been invented. The next official check will test this implementation against all available visible labels and execute it on the unlabeled queries.

## Remaining uncertainty

Only three labeled cases are available. Behavior at a selected-rank tie, with no top-row marker, or with a marker count larger than the number of components is not determined by these labels. The visible labels support a top-row count; equivalent alternatives such as the count in the uppermost row containing blue cells cannot be separated by this small sample. Both query outputs remain masked, so execution and visible training success cannot establish their correctness.
