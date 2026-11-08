# Post-repair visible-only solve work log

## Access and exposure declaration

This episode began by running the public `review.py solve prepare` workflow
from `/workspace/scratch/2c750d06c63d/round4` with its own
`WORK/.venv/bin/python3`. The source hash printed by prepare was
`b132d7379dbffedb658594771b419d949fd817319fc8b3687e5c1bc04585d595`, which
matches the hash supplied for receipt comparison. I did not open the source.

The parent task reports earlier generator work in this session, so the final
declaration must be `--earlier-exposure yes`. This record does not claim blind
status. During this solve I have read only the outer `START-HERE.md`, the newly
prepared `WORK/solve/README.md` and public `challenge.json`, and my own work.
An initial filename-only documentation search also listed names of baseline
documents; I did not open those documents. I have not consulted generator
source, canonical data, Racket rules, reference solutions, private query labels,
task notes, repair reports, prior solution explanations, or other agents'
material. The intended finish declaration is `--reference-consulted no`.

Public workflow commands and independent public-grid probe commands are recorded
with exact argument vectors, working directory, exit status, and output paths in
`WORK/checks/post-solve-commands.json`. The public runtime may print provenance
hashes; those receipts are not reference answer consultation.

## Initial observations before any authored solution

The three visible training examples preserve grid dimensions and all gray (5)
and red (2) cells. The observed changes are black (0) to cyan (8). Examples 1 and
2 also preserve preexisting cyan (8) and maroon (9).

Example 0 divides into vertical non-gray compartments. The middle compartment
contains two red cells and all its black cells become cyan. The zero-red and
one-red compartments stay unchanged. This alone suggests selection by a red
cell count, but does not distinguish an exact count from a threshold or maximum.

In example 1, the long outer path has two red cells and is filled. An inner
L-shaped region has two adjacent red cells and is also filled. Other regions
with one, three, four, or five red cells remain unchanged. This suggests an exact
count of two red cells, not selection of the maximum red count, a minimum of
two, or two separate red objects. The outer path touches the grid boundary, so
being enclosed away from an edge is not required.

The non-gray colors appear to participate in connectivity. For example, the
outer path in example 2 runs through maroon near its top-left red cell and cyan
under its top-right red cell. If either color were treated as a wall, the path
would not contain those two red cells in one region. Existing nonzero cells
should be preserved rather than repainted.

The candidate region definition is four-neighbor connectivity through all
cells except gray. There are diagonal contacts between regions in the more
complex examples; eight-neighbor connectivity may incorrectly join filled and
unfilled parts. I will measure both component definitions on only the public
grids before authoring the first solution.

## Probe 1: public component descriptions

`WORK/solve/public_probe.py` reads only `WORK/solve/challenge.json`. It reports
four-neighbor and eight-neighbor non-gray components, red counts, edge contact,
and the color changes in visible training outputs. For public test inputs it
reports input features only. This is exploratory feature analysis, not a
submitted solution or an attempted failed revision.

The probe completed with exit code 0. Its output is retained in
`WORK/checks/post-solve-visible-probe.log`. The measurements were:

| Visible example | Four-neighbor red counts | Filled components and changed black-cell counts |
| --- | --- | --- |
| Train 0 | 0, 2, 1 | the two-red component: 38 |
| Train 1 | 2, 4, 5, 2, 1, 3 | the two two-red components: 36 and 7 |
| Train 2 | 2, 3, 4, 5, 2, 1 | the two two-red components: 36 and 7 |

There were no changes in other components, and every measured change was
`0->8`. Four-neighbor connectivity separates the components consistently. With
eight neighbors, both complex examples merge an outer filled component with a
four-red unfilled component, yielding six red cells and a mixture of changed
and unchanged zeros. Eight neighbors also merge the filled inner region with
the one-red unfilled region, producing a three-red region with mixed changes.
This rules out the eight-neighbor version of this component-count hypothesis
on the visible examples. No submitted eight-neighbor solution was created.

The public query inputs have four-neighbor two-red regions as well. The first
query has one such region with eight black cells. The second query has two,
with 48 and 13 black cells. Applying the hypothesis therefore predicts eight
and 61 recolorings respectively; these are predictions from public inputs,
not private-answer correctness claims. The second query's components also
include the same one-, three-, four-, and five-red unfilled roles seen in the
visible examples, but at a different shape and size.

## Actual solution revision 1

I authored `WORK/solve/solution.py` after the public component probe. It performs
a four-neighbor flood fill over cells of any color except gray (5). For each
region it counts red (2) cells. If and only if that count is exactly two, it
changes the region's black (0) cells to cyan (8). It preserves all other cells
and returns the original dimensions. The code does not read any files, import
other solutions, use example identities, or consult expected query outputs.

This is the first and only authored solution revision so far. The alternatives
above were considered and compared as observations before implementation; they
are not fabricated failed attempts. I will run the public check with intent
`solve` because the full component rule now explains all three visible outputs
and has a concrete generalization to both public query inputs.

Planned check note: "Revision 1: Four-neighbor components of all non-gray cells;
recolor only zeros in components with exactly two red cells. Public component
counts support exact cell counting and reject diagonal connectivity."
