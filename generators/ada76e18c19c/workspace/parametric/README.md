# Native row-fill / post-fill color-majority family

`adapter.py` implements the native interface. `mode=all_colors` returns the exact
selected canonical bytes. `mode=filled_majority` first applies the exact-two,
same-color row-span rule; it then counts all surviving nonzero colors and keeps
all cells of the global winner. Equal counts use first row-major appearance.
Disconnected pieces of the winning color are retained. Empty inputs are total.

The native grammar is a separate extension, not a production-generator repair.
It varies colors, placements, sizes and negative rows beyond the narrow official
profiles. Sampled queries require a unique post-fill winner; ties are implemented
and checked separately, not claimed to be taught by the sampled core.

## Generation and teaching

`generate(seed, {"mode": ...}, demos, queries)` accepts exact integer seeds
0..2**63-1, 3..6 demonstrations, and 1..4 queries. Booleans/coercions and unknown
settings fail closed. The full private query bank is independent of the demo
count and returned in stable source order. Shared native preview shuffles that
bank privately before single-query reveal; do not present a directory listing.

Three constructive lessons expose three different negative-row conditions:
three equal cells, a third-color blocker, and mismatched endpoints. They rotate
winner colors and row direction to refute color-ID and scan-order shortcuts.
Two lessons select the union of separated shorter rows rather than the longest
row; the blocked-pair lesson selects one longer row over two short rivals,
refuting qualifying-row frequency. The 22 declared Python policies are fit on demos only. Four
retained earlier lessons expose first/last/min/max-color ambiguities; matching
Racket rivals and repaired distinguishing demonstrations are in the audit.

The four queries use 10x15, 16x19, 23x26 and 30x30 inputs. The largest grid has
signal in every row, endpoints on all four boundaries, and at least 90 nonzero
input cells; filling spreads content throughout the canvas. The canonical
production dimensions remain unchanged.

## Causality

A: exact pair filling. Intermediate: the row-major-tiebroken global color counts
of the filled grid. B: retain the selected color's complete union. The input
color leader can differ from the filled-grid leader; `wrong_order.rkt` chooses
on the original input but masks the correctly filled grid. Native witness
replay verifies a different final answer on an exact qualified pair.

## Reproduce (outer packet directory)

```sh
python3 review.py task-tests ada76e18c19c --phase after --out ../checks/ada76-tests-new
python3 review.py run python3 generators/ada76e18c19c/workspace/parametric/audit.py --seeds 64 --out ../checks/ada76-audit-new.json
python3 review.py run python3 -m arcpuzzles parametric qualify ada76e18c19c --out ../checks/ada76-qualification-new --summary
```

`audit.py` is reusable and refuses to overwrite prior evidence. It reports
Python sweep counts separately from protected-Racket calls, saves exact examples,
and replays the retained teaching regressions. Evidence is bounded, not a proof
of universal identifiability or training benefit. Qualification is not owner
acceptance, and training admission remains false.
