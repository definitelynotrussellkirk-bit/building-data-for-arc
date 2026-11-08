# Native mirror / post-mirror component selection

The canonical `all_components` setting returns the exact selected Racket source:
mirror the input left-to-right as `[reverse(row), row]`, then vertically stack
`[flip(strip), strip, flip(strip)]`. `largest_mirrored` constructs that strip,
keeps its largest monochromatic four-connected component (row-major discovery
breaks ties), and performs the same vertical stack. It retains original strip
coordinates rather than cropping or recentering the selected object.

## Why the intermediate matters

A component touching the source's left boundary merges with its reflected copy
at the strip seam. An off-seam component instead yields two separate copies.
Consequently the largest original component need not be the largest mirrored
component. The second demo constructively reverses this ranking: sizes 5 > 3
before mirroring versus 6 > 5 afterward. `wrong_order.rkt` selects on the input
before mirroring; the protected native witness uses that exact distinguishing
qualified demo. Duplicate off-seam maxima must select only the first copy.

## Teaching and request contract

`generate(seed, settings, demos, queries)` supports 3–6 demos, 1–4 prefix-stable
queries, exact integer seeds 0..2**63-1, and `settings={"mode":...}`. Inputs are
matched across settings. Color, shape extent, dimensions and placement vary.
The first two demos expose seam merging, size ranking, mirror order and ties.
A third contrasts a dense rectangle against a larger-bbox L with diagonal
satellites. Its winning rectangle sits above the other objects, so selecting
the lowest component cannot mimic size selection. It rules out eight-neighbor connectivity. An executed regression
shows that the eight-neighbor rule fits the first two demos but fails a query;
therefore 2-demo requests are deliberately unsupported.

The generated core uses binary inputs (0 plus one variable foreground color),
including a 3x2 query from the original domain. The separate native family also
uses larger inputs. The output is always `3h x 2w`, so inputs are limited to
`h<=10,w<=15`: **30x30 is an output stress case, not an input claim**. Its 10x15
input has a full connected frame and separate interior distractors. Its selected
output spreads signal across all 30 rows and all four borders, without padding.
The production generator and canonical approval are unchanged.

## Reproduction (outer packet directory)

```sh
python3 review.py task-tests 1a259ef9a7e7 --phase after --out ../checks/mirror-tests-new
python3 review.py run python3 generators/1a259ef9a7e7/workspace/parametric/audit.py --seeds 64 --out ../checks/mirror-audit-new.json
python3 review.py run python3 -m arcpuzzles parametric qualify 1a259ef9a7e7 --out ../checks/mirror-qualification-new --summary
```

`audit.py` pins sources, checks 25 finite policies on demonstrations only, and
counts its Python sweep separately from protected-Racket executions. It retains
four complete labeled episodes, executed rivals and the three-demo regression.
The existing native `preview-public` writer privately shuffles the full query
bank and emits hash-named single-query views. `public_turn` strips nested private
metadata; it does not replace the controller's presentation shuffle. Never show
future-query files or the private bundle listing to the learner.

Qualification and finite audits do not prove universal identifiability, owner
acceptance or training benefit. Exact-source owner acceptance remains pending;
training admission remains false.
