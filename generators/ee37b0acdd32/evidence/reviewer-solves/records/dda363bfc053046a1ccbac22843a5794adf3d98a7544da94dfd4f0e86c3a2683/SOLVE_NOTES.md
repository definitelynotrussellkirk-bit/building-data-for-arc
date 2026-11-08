# Blind visible-only solve work log

This is an assistant-authored work log, not a token-level conversation capture.

## Scope and source binding

- Assignment: `review-50e2310958c213c4`; blind task: `ee37b0acdd32`.
- Prepared generator SHA-256 reported by the public prepare command:
  `1cf46183d36979212fc84956fecef9801427d54d7072f54559edf358a6953747`.
- Public challenge SHA-256 reported by preparation:
  `f754c3815c10d1bd2005c0918d1da8908376630cc0dd375d46f06ac7f0238585`.
- Instance SHA-256: `9ae24b3d16c307dfef4b5e74ae02fb6c9d44307cc513680a6ab0b8a517f1f090`.
- Seed: `2025702175`; difficulty: `medium`; 3 visible examples and 2 masked queries.
- I read only the public `START-HERE.md`, `WORK/RETURN-GUIDE.md`, the official
  preparation output, and `WORK/solve-blind/README.md` / `challenge.json`.
  I used my own Python experiments. Generator and rule source, reference
  solutions, canonical data, historical notes, private labels, and other
  rounds' solve logic were not consulted.
- Earlier rule exposure: **no**. I do not recognize this task from prior work.
  Reference consulted during solve: **no**.
- An independent review was delegated with access restricted to the same public
  README and challenge; its purpose is to assess visible-rule ambiguity.

## Public presentation and observations

No arrays are copied here; the public README contains the dimension-prefixed
arrays. The actual dimensions are:

| Pair | Input | Output |
| --- | --- | --- |
| Train 0 | 10 rows × 11 columns | 10 rows × 11 columns |
| Train 1 | 10 rows × 13 columns | 10 rows × 13 columns |
| Train 2 | 8 rows × 10 columns | 8 rows × 10 columns |
| Query 0 | 10 rows × 11 columns | unknown |
| Query 1 | 10 rows × 13 columns | unknown |

All three visible outputs retain a subset of the nonzero input cells, recolor
those cells 8, and make all remaining cells 0. Each input has a single 1 and a
single 2, both retained. Four-cell monochrome blocks along the route between
them are retained in full, even where a pixel path could take a shorter route.

Train 0 retains the singleton 4 at (6, 5) that connects two blocks, while
removing the separate singleton 4 at (4, 6) and the side branch 7 at (7, 3).
Thus color identity or minimum component size alone does not determine retention.
Train 1 removes the two vertically adjacent 5 cells on the right of the 7 block.
Those two cells form a pixel-level loop with two cells of the block, but a single
leaf when monochrome regions are the graph nodes.

## Hypothesis and exploratory probes

The proposed rule is to make one node per orthogonally connected monochrome
nonzero region, connect nodes that touch along an edge, retain the route from
the region of color 1 to the region of color 2, and recolor every cell in retained
regions to 8. Zero is background. Distinct regions of the same color remain
separate nodes.

`visible_probe.py` reads only the public challenge. Its retained detailed report
is `WORK/checks/blind-visible-probes.json`. The actual logged experiment is in
`WORK/checks/blind-04-visible-probe.log`; command metadata is in
`WORK/checks/blind-commands.json`.

The following comparisons were exploratory rivals, not submitted revisions and
not accidental failed solve attempts. Counts are exact cell mismatches against
the visible expected outputs:

| Hypothesis | Train 0 | Train 1 | Train 2 |
| --- | ---: | ---: | ---: |
| Region route between 1 and 2 | 0 | 0 | 0 |
| Recolor every nonzero cell | 2 | 3 | 1 |
| One shortest pixel route | 4 | 7 | 4 |
| Repeatedly remove unprotected pixel leaves | 0 | 2 | 0 |
| Keep regions of size at least four, plus 1 and 2 | 1 | 0 | 0 |

The region-route rule predicts 11 retained cells for query 0 and 18 for query 1.
These are predictions only. Query output arrays remain unknown.

## Submitted attempt 1

I wrote one genuine solution revision, `solution.py`, implementing the region
graph and breadth-first route search. It uses no task-specific source imports,
example lookup tables, or private data. Complete monochrome regions on the
selected route become 8; all other output cells become 0.

At this point the official visible-only check has not yet run. The next action
is `python3 review.py blind check --intent solve --note ...`. Every actual
submitted revision will be checked and retained. No failure has been invented.

## Remaining ambiguity

The visible component graphs, including the query inputs, have tree structure;
there is a unique route between the marker regions. The examples do not decide
how to treat a graph with multiple routes: shortest region path, union of simple
paths, and protected-node leaf pruning agree on the observed trees but can
diverge on cycles. The implementation chooses a deterministic shortest region
path in that unobserved case. This extrapolation is not claimed to be established.

All visible backbone regions have four cells, so alternative rules that combine
block recognition with connector handling remain conceivable. The route rule
is preferred because it explains the retained singleton connector and removed
two-cell side branch with one connectivity criterion. Cases with multiple marker
regions, no marker, or disconnected markers are not established by the examples;
the implementation raises a clear error for those cases.

## Check status and stopping decision

Pending the first official check. Private-query correctness is withheld by the
workflow and will not be claimed here.
