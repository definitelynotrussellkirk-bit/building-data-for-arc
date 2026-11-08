# Solve work log

## Prior exposure

Before this visible-only solve I had already reviewed this task's generator and authority as part of the assigned repair, so this is **not blind**. During the solve phase itself I did not reopen the generator, Racket source, reference answers, private query labels, or earlier solution explanations; I used only the prepared visible examples.

## Revision 1

Hypothesis from the visible examples: the single red `2` on an edge selects the mirror axis. A top-row marker selects its column; a left-column marker selects its row. Keep the original gray `5` cells and add orange `7` at their reflected coordinates.

Two visible cases resolve boundary details. Train example 1 has reflected coordinates already occupied by gray cells; those cells remain `5`, so painting is restricted to empty targets. Train example 4 has a source whose reflected column falls outside the grid; no wrapped or clipped cell appears, so out-of-bounds targets are skipped. The implementation therefore gathers the original `5` cells, reflects each across the selected axis, and writes `7` only when the target is in bounds and currently `0`.

Alternative rules rejected by the visible examples: always overwrite the mirror target, modulo-wrap off-grid reflections, use a fixed vertical axis, or use a fixed horizontal axis.
