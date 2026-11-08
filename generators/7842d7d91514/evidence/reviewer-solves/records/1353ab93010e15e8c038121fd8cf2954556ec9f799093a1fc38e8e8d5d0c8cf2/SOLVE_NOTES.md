# Solve work log

Earlier exposure: yes. Before this source-bound solve I had inspected and repaired the selected generator and its rule authority, so I already knew the intended task family. I did not consult those sources, reference outputs, private query labels, or earlier solve notes while implementing this solve; I used only `challenge.json` and the visible examples above.

## Revision 1

Hypothesis from the visible examples: the single four-connected color-5 component is a template. Each four-connected color-2 component is compared after translation normalization while preserving its orientation. A candidate with exactly the same occupied offsets is recolored 4; every other candidate is recolored 1. Background and the color-5 template remain unchanged. Rotations/reflections are deliberately not accepted: visible train examples contain same-sized differently oriented candidates that become 1.

Implementation/probe: parse color-5 and color-2 four-connected components independently, normalize each by subtracting its minimum row and column, compare the resulting coordinate sets, and recolor whole candidate components. I kept validation for the visible invariant of exactly one color-5 template.

Alternatives considered and rejected from visible evidence: matching only component size, accepting rotations/reflections, recoloring all candidates alike, and comparing bounding boxes. Each conflicts with at least one visible pair. Remaining uncertainty is limited to unseen malformed inputs outside the demonstrated grammar; the prepared queries follow that grammar.
