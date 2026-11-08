# Blind solve work log

## Exposure and scope

I started from the supplied unimplemented `solution.py` and blank work-log
template. I have had no earlier exposure to this task's Racket rule, generator,
reference solution, private labels, or prior solution explanations. During this
solve I read only the public `challenge.json`, public `README.md`, and the
supplied solution/work-log templates as task evidence. All reasoning below is
based on the three labeled training examples and my own experiments. The two
query outputs are masked and cannot be validated here.

## Initial observations and hypothesis

All three examples preserve the dimensions, exterior background, rectangular
color-7 frame, and any color-7 cells inside the frame. Only interior zero cells
change. The other nonzero cells behave as colored seeds.

My initial hypothesis is to color every interior zero with the nearest seed by
Manhattan distance, breaking equal-distance ties by the smaller numeric color.
Interior color-7 cells remain unchanged but do not obstruct distance. The frame
is the bounding rectangle of the color-7 cells.

Useful discriminators in the public examples (zero-based coordinates):

- Training 0, cell (1,7): seed 9 at (3,6) and seed 2 at (4,7) are both distance
  3 away in Manhattan distance, and the output is 2. Euclidean and Chebyshev
  distance would favor 9 here.
- Training 1, cell (4,3): colors 1 and 4 are both distance 1 away, and the
  output is 1. This also argues against always choosing the later seed in
  row-major order.
- Training 2, cell (3,2): color 3 at (6,2) has Manhattan distance 3, while
  color 2 at (3,6) has distance 4. The intervening 7 at (4,2) would make an
  obstacle-aware path to color 3 length 5, but the output is 3.
- Training 2, cell (4,3): colors 3 and 8 have equal Manhattan distance 3,
  and the output is 3. This also argues against always choosing the first
  seed in row-major order.

## Supplied-template baseline

Before replacing the supplied `NotImplementedError` template, I will run the
public check to confirm the execution/visible-example gate detects the missing
implementation. This is a baseline of the untouched stub, not a rejected
transformation hypothesis.

Command:

```sh
python3 solve_episode.py blind check --intent solve --note 'Baseline of the supplied unimplemented template before implementing the visible Manhattan-distance hypothesis.'
```

Observed result: checker revision 1 reported `execution_status: error`,
`visible_passed: 0`, `visible_total: 3`, and `reported_label: bad`. The checker
command itself exited 0. The supplied stub has no implementation, so this is the
expected missing-function baseline; it does not reject the distance hypothesis.

## Visible-only hypothesis probes

I wrote `visible_probes.py` to compare six concrete alternatives using only the
three public labeled training examples. The script reads `challenge.json` and
writes `visible_probes.json`; it does not score the masked queries.

Command:

```sh
python3 solve-blind/visible_probes.py
```

Observed result (command exit 0):

| Distance and tie rule | Exact visible examples | Wrong cells by example |
| --- | --- | --- |
| Manhattan, smaller color | 3/3 | 0, 0, 0 |
| Squared Euclidean, smaller color | 1/3 | 5, 0, 1 |
| Chebyshev, smaller color | 0/3 | 5, 2, 4 |
| Shortest path around color-7 cells, smaller color | 2/3 | 0, 0, 1 |
| Manhattan, first seed in row-major order | 1/3 | 11, 0, 4 |
| Manhattan, last seed in row-major order | 2/3 | 0, 1, 0 |

The four discriminator cells listed above produced the expected distinctions.
These rejected alternatives were probe models, not revisions of `solution.py`.
The initial Manhattan/smaller-color hypothesis needed no change.

## Implementation revision 1

I replaced the stub with a direct implementation of the supported rule. It
copies the input, identifies the color-7 bounding rectangle, gathers its
interior nonzero/non-7 seeds, and fills only interior zero cells by minimizing
`(Manhattan distance, seed color)`. All existing nonzero cells and exterior
cells are preserved. There are no lookups of task examples or query-specific
branches in the solver.

The next official check tests this actual implementation on all visible
examples and checks execution. Its query correctness feedback remains masked.

Command:

```sh
python3 solve_episode.py blind check --intent solve --note 'Implement Manhattan-nearest seed filling inside the 7 frame, with smaller-color ties and nonblocking preserved 7 cells; visible-only probes reject distance and tie alternatives.'
```

Observed result: checker revision 2 exited 0 and reported
`execution_status: completed`, `visible_passed: 3`, `visible_total: 3`, and
`reported_label: unknown`. The program hash was
`60034d407c21a426c633321c951d5c74b4fd00808649d2f813bcd3e74f729a3d`.
The unknown label is not evidence of private-query correctness. I made no
further solution changes after this check.

## Stopping decision

The implemented rule matches all three visible examples, and the retained
probes resolve the concrete distance, obstacle, and tie-break alternatives I
considered. I therefore stop rather than add unsupported special cases. The
unseen queries remain unverified; passing the examples cannot prove them
correct. No Racket rule, generator implementation, reference solution, private
label, canonical data, or prior task explanation was consulted.

Finish command:

```sh
python3 solve_episode.py blind finish --earlier-exposure no --reference-consulted no --reason 'The implemented nearest-seed rule matches all 3 visible examples and the visible discriminator probes; masked-query correctness remains unknown.'
```

Evidence retained in this directory: `solution.py`, this work log,
`visible_probes.py`, and `visible_probes.json`, in addition to the official
check/finish records created by the harness.
