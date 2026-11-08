# Native template completion and gain selection

`completion_policy=all_copies` preserves canonical.rkt exactly, including its
coverage-ranked greedy handling of every non-template colored cell.
`largest_gain` first executes that canonical rule, measures newly filled original-
zero cells per resulting 8-connected nonzero component, and recolors the unique
largest-gain component cyan (8). A tie or no gain leaves the canonical result.
The winning component includes its old partial cells, not only newly added cells.

The constructive family uses 2–3 disjoint-color templates, 5 or 12 partial
placements, varied marker poses and palettes, and both single- and multi-cell
monochrome partials. Shapes include solid and missing-corner 2×2 through 5×5
patterns. Literal labels and all eight transformed hand cases are checked with
protected Racket. The ordinary canvas is 22–25 by 24–29, the compact query is
16×17, and the stress query is 30×30 with dense content in all four quadrants
and complete templates touching opposing corners. This is a separate native
grammar; the approved production generator is unchanged.

Demonstration 1 makes a larger original partial win by gaining more cells.
Demonstration 2 makes a smaller completed object win over a larger template.
Nearby executable rivals test ignoring multicolor-template fragments that are
themselves monochrome, reversing greedy coverage ranking, selecting by total or
original size, selecting first/last, and recoloring only new cells. Their finite
elimination is not universal uniqueness.

`generate(seed, settings, demos, queries)` accepts independent 2–6 and 1–4 counts.
The complete four-query bank is shuffled on a separate private presentation RNG
before slicing. Cached internal episodes are always deep-copied before return.
`public_view` exposes only demonstrations and the current query input. Public
file names hash only visible bytes; directory listings remain controller-private.

From the outer packet directory:
```sh
python3 review.py run python3 generators/f06819f26831/workspace/parametric/audit.py --out generators/f06819f26831/workspace/parametric/evidence/new-audit --seeds 20
python3 review.py task-tests f06819f26831 --phase after --out ../checks/new-tests
```
The reusable audit separates repeated-prefix requests, unique inputs and real
Racket calls, refuses existing output directories, retains private labels and
rejects execution errors rather than counting them as rival elimination.
The inherited production finding that matching-color blobs are NOT inert remains
open; this family models their actual semantics rather than changing production.
Native qualification and a causal witness do not grant owner acceptance or
training admission.
