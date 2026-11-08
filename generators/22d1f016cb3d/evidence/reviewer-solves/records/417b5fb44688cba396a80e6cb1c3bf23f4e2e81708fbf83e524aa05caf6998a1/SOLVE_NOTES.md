# Exposed solve work log

This is a human-readable work log, not a token-level model trace. I had already reviewed the generator/rule before this required exposed solve, so earlier rule exposure is **yes**. During this solve lane I used only the visible challenge presentation and did not consult generator source, Racket source, reference solutions, private labels, or earlier solution explanations.

## Visible-example inference

All examples preserve shape and every non-5 cell. The rectangular examples show three roles for a 5-cell: corners become 1, strict rectangle interiors become 2, and non-corner perimeter cells become 4. The hollow frame is decisive: straight frame segments become 4 even though their component-bounding-box status differs from a filled rectangle. The cross-like example makes the local rule explicit.

Hypothesis: classify each 5-cell by whether it has a 5 on both horizontal sides and whether it has a 5 on both vertical sides. Both opposing pairs -> 2; neither pair -> 1; exactly one pair -> 4. Grid exterior counts as absent. Preserve all non-5 values.

## Revision 1

Implemented the direct local-neighbor rule with no component extraction or bounding boxes. This should handle filled rectangles, hollow frames, crosses, thin bars, border-touching shapes, and multiple components uniformly. I stopped after the visible examples passed because the three demonstrations jointly distinguish corners/ends, straight segments, junction interiors, and preservation behavior; no failed natural revision occurred.
