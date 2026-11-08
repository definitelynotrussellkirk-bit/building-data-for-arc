# Solve work log

## Prior exposure declaration

Before this solve I had inspected this task's generator and Racket-authority metadata while repairing it, so this is an **exposed** solve. During the solve phase itself I used only `solve/challenge.json`, my own Python, and checker feedback; I did not reopen the generator, Racket source, reference solutions, or private labels.

## Revision 1 — whole-glyph compass placement

Across the three visible demonstrations, each input contains nine solid 3×3 nonzero tiles scattered on a zero background. Eight have gray `5` cells plus one signal color; one is all gray. The output is always a gray 9×9 canvas partitioned into nine 3×3 macro-cells.

Hypothesis: the local geometry of the signal-colored cells is itself a compass cue. A top-left corner glyph goes in the top-left macro-cell, a top-edge glyph in top-middle, and so on through the eight perimeter positions. The all-gray tile maps to the already-gray center. Input position and signal color vary and therefore do not select the destination.

Implementation: scan for every all-nonzero 3×3 window, map its non-`5` coordinate set to one of eight perimeter macro-cells, and copy the entire source tile there. Leave the center gray. This also handles inputs where two tiles belong to the same connected component, because detection is based on exact solid 3×3 windows rather than connected components.

Local visible-example probe: applied `solve` to all three training inputs from `challenge.json`; all three outputs matched exactly. No alternative survived all demonstrations: reading-order placement changes across examples, and color-to-slot mapping is inconsistent.

Remaining uncertainty before checker: whether a test input creates a spurious solid 3×3 window where two tiles touch. The visible family appears constructed to preserve exactly nine solid windows; the implementation fails closed if that count changes.
