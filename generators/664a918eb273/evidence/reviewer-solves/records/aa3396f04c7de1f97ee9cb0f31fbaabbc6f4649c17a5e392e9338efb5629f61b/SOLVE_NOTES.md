# Visible-example solve work log

This is a reviewer-authored summary of observable experiments and implementation
decisions, not a captured model conversation, token-level trace, or log-probability record.

## Exposure declaration

Earlier rule exposure: **yes**. Before this solve episode I inspected the Racket
rule and generator while repairing the assigned task. This is not a blind solve.
During the episode I used only `challenge.json`, the Python solution, and the
visible-only probe/check feedback. I did not reopen the generator, reference
rule, reference solutions, previous solution explanations, or private labels.

## Visible evidence and hypotheses

The three demonstrations preserve path shapes and colors, join pieces in their
left-to-right input order, retain the original height, and trim the right edge.
The large demonstration contains two disconnected pieces of color 1, so a color
cannot stand in for an object identifier. Its left margin also remains present.

An intentionally incorrect horizontal-only compaction rule was tested as an
**intentional teaching negative**, not as an accidental failed solver revision.
`visible_probe.py` compares it with the endpoint-joining proposal on each visible
training pair. Horizontal-only compaction fails all three; the endpoint proposal
matches all three. Full measured outcomes are in `visible_probe.json`.

## Revision 1

Implemented eight-neighbor component extraction, four-neighbor endpoint degree,
left-to-right ordering, and translation of each later entry to the cell directly
right of the prior exit. Preserve the first piece, height, and individual cell
colors. Refuse clipping/overlap rather than silently returning a damaged grid.

The source is independent Python with no generator/reference imports. The
checker below is the first submitted solution revision; there are no concealed
failed revisions. Further edits are warranted only by observed failures.
