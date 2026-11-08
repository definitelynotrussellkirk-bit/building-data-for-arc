# public_eval_b99e7126 authoring notes

## Canonical rule

Read the uniform separator lattice as an array of equal square tiles. Exactly
one tile pattern is common and one is rare. The rare tile contains one color
that does not occur in the common tile; the positions of that unique color form
a local mask. The visible rare-tile copies are a subset of one translated copy
of that mask on the macro tile lattice. Complete the translation by replacing
every missing mask position with the complete rare tile. Preserve separators
and all other tiles.

`reference.rkt` is a general implementation and is byte-identical to
`workspace/parametric/canonical.rkt`. It reproduces all three supplied training
pairs and the gold-labelled test pair.

## Episode-fixed extension

`finish_rule=complete_then_highlight_densest_row` first performs canonical
completion, counts completed rare tiles by macro row, selects the unique densest
row, and recolors the rare tile's encoded ink cells in that row with color 9.
Generated inputs deliberately make the visible partial arrangement's densest
row different from the completed mask's densest row. The retained
counterfactual selects from the visible positions, demonstrating that Stage B
must consume Stage A's completed coordinate set.

The sampler supports 2–6 demonstrations and 1–4 queries, keeps inputs matched
between settings, retains four private novel queries, independently permutes
query presentation, and includes a substantive 30×30 case. The 30×30 case uses
a 29×29 seven-tile lattice plus one additional separator row and column; the
parser handles consecutive separator bands by extracting non-separator runs.

## Evidence boundary

The task-local audit executes finite named semantic rivals, protected-Racket
labels, source-stability checks, private-field mutation checks, single-query
public projections, and a source-bound wrong-intermediate witness. It is
bounded reviewer evidence only: owner registration, native qualification,
acceptance, and training admission remain separate and pending.
