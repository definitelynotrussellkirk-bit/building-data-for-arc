# Visible-only solve notes

This is a human work log based only on the displayed training pairs and masked queries. I had already seen the task rule during generator repair, so this is **not blind**; I did not reopen or consult the generator, Racket source, reference solutions, or private labels during this solve episode.

## Hypothesis before revision 1

Each nonzero object is a maximal contiguous horizontal run of one color. The output preserves exactly one cell per run: the geometrical middle cell. Runs of length 1 remain unchanged; length 3 keeps offset 1; length 5 keeps offset 2. Every other cell becomes background 0, and the grid shape is unchanged.

Visible checks:

- Train 0: color 6 at columns 3..5 keeps column 4; color 8 at 3..7 keeps 5; color 3 at 1..3 keeps 2; singleton 7 stays at 7.
- Train 1: the two length-5 runs keep their third cells; the length-3 run keeps its second; singleton 4 remains.
- Train 2: length-3 runs keep their second cells and the length-5 run keeps its third.

Implementation plan: scan each row left to right, detect each maximal same-color nonzero run, and write its cell at `start + length // 2` into an otherwise zero grid. The visible examples use odd lengths, so this is a unique center.
