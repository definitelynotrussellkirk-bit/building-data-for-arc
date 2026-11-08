# Aligned vacancy regions

`adapter.py` is a native parametric adapter for `76aff6297765` / original ARC
`0c9aba6e`. It has two episode-fixed settings:

| selection | Rule |
|---|---|
| `all` | Mark every aligned pair of zero cells with 8. This returns the exact canonical Racket program bytes. |
| `largest` | Form the same joint-zero mask, compute its four-connected components, and retain every component tied for largest cell count. |

The production generator and canonical authority are unchanged. These are
separate parameterized episodes, pending the owner's exact-source acceptance.

## Native use

From the packet's outer directory, after `review.py setup` and a ready Python
environment:

```bash
WORK/.venv/bin/python review.py run python3 -m pytest -q generators/76aff6297765/tests/test_parametric.py
WORK/.venv/bin/python review.py run python3 generators/76aff6297765/workspace/parametric/verify_semantics.py --out ../checks/76aff6297765/new-self-review.json
WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric qualify 76aff6297765 --seed 0 --seed 17 --demos 3 --queries 4 --out ../checks/76aff6297765/new-qualification --summary
```

Choose fresh output paths. The retained inventory must be current before native
qualification. Source edits require a rebuilt inventory and fresh qualification;
the old evidence cannot approve new bytes. The owner then uses the native
acceptance command after integrating the return. No training admission is made.

The direct API is `program(settings)` and
`generate(seed, settings, demos=3, queries=4)`. Counts are independent: 2–6 demos,
1–4 queries; ordinary training uses three demos and four queries. `solve` is a
Python diagnostic mirror, not the output authority. Native qualification checks
every retained label through protected Racket.

## Teaching and causal dependency

The first two demonstrations are constructed, so two-demo requests do not
truncate the production generator's old six-slot curriculum. One uses equal
foreground colors, tied largest components, a smaller diagonal neighbor, and
source-panel zero regions that would mislead selection before intersection.
The other uses distinct colors, a compact largest component, and a smaller
component with a larger bounding box. Their component sizes also reverse a
fixed-threshold explanation: a smaller region is retained in one scene while a
larger region is discarded in the other. Shared scaling, independent dihedral
transforms, and palettes vary these teaching examples. Extra demos and queries
add random topology, component counts, occupancy density, and canvas coverage.

For each episode, both settings receive identical inputs. Setting inference
uses demonstration labels only. `teaching_check` tests the finite named rival
family in `rival_outputs`; it makes no claim about every possible hypothesis.
The independent `verify_semantics.py` tool executes Racket rivals rather than
trusting the Python mirror alone.

The required dependency is: **align and intersect panel zero sets → joint-zero
mask and its connected components → select maximum component size and paint**.
Selecting a largest source-panel component before forming that mask changes
the final output. The retained native causal witness executes both orders on
qualified demonstration inputs. Empty intersections return an all-zero panel;
ties retain all maxima.

## Grammar and size coverage

Generated panels each contain 0 and one foreground color from 1–6 or 9. The two
foreground colors may coincide. All four aligned occupancy states occur. One
or two contiguous full-7 rows divide equal panels. The unchanged canonical
`zip-halves` implementation supports both separator widths.

Four-query episodes include 7×3, 21×23, 29×29, and **30×30** inputs. The largest
has two 14×30 panels and a two-row separator, with at least 100 joint-zero cells
distributed across the canvas. It exercises component selection at full size,
rather than placing a small fixed motif inside a padded canvas. Outputs have
the panel dimensions, up to 14×30. The original production grammar remains
separate and keeps its existing size bounds.

## Private controller data and visible turns

The returned episode is private: it includes the program and query answers.
Keep all four `test` pairs with the controller. For a model-facing turn, use
`reviewer_support.public_challenge_bytes` on the demonstrations and exactly one
query input. Do not expose the remaining query inputs, settings, program, seed,
query answers, ordinal, total query count, or final-turn marker.

Query and demo prefixes are independent of requested counts. At a fixed seed,
setting and demo count, the first visible turn has identical bytes whether one
or four queries were requested. Public IDs are SHA-256 of those exact visible
bytes; changing private metadata cannot change them. The return includes small
public first-turn examples and a private controller index derived from native
qualification outputs.

## Limits

This is finite source-bound execution and teaching evidence. The two teaching
motifs are deliberately structured; the query distribution has broader random
topology. No learned-model score, transfer benefit, unrestricted rotation
curriculum, universal identifiability, or training activation is claimed.
