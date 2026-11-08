# Blind solve notes

This is a concise work log of observations, hypotheses, and executed probes. It is not a token trace. Puzzle information came only from `solve-blind/challenge.json`; no reference, generator, rule source, private query result, prior solution, or prior notes were consulted.

## Observations

- There are three visible input/output pairs and two query inputs without outputs.
- Each visible output is the tight bounding rectangle of all nonzero input cells: 6 by 6, 6 by 6, and 5 by 5.
- Zeros within that rectangle remain zero. Original nonzero colors disappear; differently colored touching cells form one occupied shape.
- The exposed cells have value 1. Interior cells have value 2, with a central 3 in the third example. This suggests successive layers measured from the background.

## Hypothesis and visible-only probe

Hypothesis: crop to the bounding rectangle of all nonzero cells, then replace every nonzero cell with its shortest orthogonal distance to a zero cell, including the background just outside the crop.

Executed an inline `python3 -` probe that loaded only the challenge JSON and compared multi-source distance transforms against all three visible outputs. It tested orthogonal adjacency and eight-neighbor adjacency separately. Exit code: 0.

- Orthogonal adjacency matched all three visible examples exactly.
- Eight-neighbor adjacency disagreed in 4, 3, and 2 cells respectively. In the third example it gave the central cell 2 instead of the observed 3.

This probe distinguishes the two distance metrics; it was not a submitted solver attempt. There was no reason to add special behavior for individual input colors or separate connected components.

## Solver revisions and episode checks

Revision 1 implements the orthogonal distance rule with a padded zero frame and breadth-first propagation from every background cell. An all-zero input returns an empty crop; this case is absent from the visible examples.

Attempt 1 used the following command from the packet root:

```sh
python3 solve_episode.py blind check --intent solve --note 'Revision 1: crop all nonzero cells and label orthogonal distance to background; the visible-only metric probe matched all three training examples and rejected diagonal distance.'
```

Exit code: 0. Feedback reported revision 1, `execution_status: completed`, `visible_passed: 3`, `visible_total: 3`, and `reported_label: unknown`. No hidden correctness was revealed or inferred. This was the only solver revision and the only episode check; all attempt records were retained.

## Stopping decision

The single rule explains every visible output, including cropping, mixed input colors, zeros inside the crop, and the depth-3 cell. The alternative diagonal metric was directly contradicted by visible examples. The implementation then passed all three visible examples through the episode harness. With no remaining visible mismatch or execution failure, further revisions would have no evidence-based purpose. Hidden correctness remains unknown.

Finishing with `--earlier-exposure no --reference-consulted no` accurately describes this solve.
