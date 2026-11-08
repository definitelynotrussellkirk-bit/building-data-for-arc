# Native diagonal completion: one or two snapshot passes

This separate proposed family preserves production v2.0.0 and its canonical
rule `d45fd86e0516`. `passes=1` returns the exact canonical source bytes in
`canonical.rkt`; `passes=2` executes that same body twice, with the first result
bound as the second pass's input. The parameter is fixed across an episode.

Each pass inspects every 2×2 window of its **original** input, in row-major order.
Two equal nonzero diagonal endpoints trigger filling both other corners only
when both are zero. Both orientations qualify. Writes accumulate into a new
grid; when different eligible windows write the same original zero, the later
window wins. Reads never observe writes from the current pass. A second complete
pass recomputes eligibility on the first result; it is neither an in-place scan
nor a fixed-point fill.

## Domain, counts, and construction

The native grammar is every rectangular list-of-lists grid with exact integer
colors 0..9 and axes 1..30. Blank, one-row/column, blocked, overlapping and
conflicting motifs are lawful. Both settings are total on this grammar; this
explicitly extends the narrower separated-motif production distribution.
Seeds are exact integers 0..2**63−1. Counts are independent: 2–6 demonstrations
and 1–4 queries; ordinary defaults are three demonstrations and four queries.
Unknown settings and coercible scalar values are rejected.

The full six-demo/four-query input bank is constructed before slicing. Separate
seeded streams govern inputs and the private setting; explicit settings use the
same inputs. No rejection loop or request shortening is used. All ten input
grids are distinct. The first two demos are composite 14×20 and 16×23 scenes:
three-wave cascades in perpendicular orientations, immediate and deferred
write conflicts, both diagonal orientations, blockers, unequal endpoints,
axis pairs, full blocks, a singleton, and separated endpoints. Their geometry
is fixed because row-major conflict priority is directional; palette mappings
and safe translations vary across seeds. The deferred conflict is needed to
distinguish reversing only the second pass.

Additional demos use 1×1, 7×9, 20×25 and 30×30 profiles. Queries use 4×7, 15×18,
26×29 and 30×30 profiles. Rectangular mosaics may be transposed or reflected.
The large demo has a 10×10 field of separated local motifs; the large query
has a 7×7 field of wave/conflict motifs with adjacent column boundaries, so
the large pair has distinct geometry and real interactions. Content spans all
quadrants and touches canvas edges. Matching labels are computed after these
orientations and are independently executed during qualification/audit.

## Sequential dependency and alternatives

A performs a complete canonical snapshot pass. Its input-dependent intermediate
grid contains newly filled corners and resolves original-window write conflicts.
B repeats the rule on that grid, so A can enable new eligible windows and new
conflicts. A three-wave fixture distinguishes one, exactly two, and three or
stable passes. Skipping A supplies the original grid to B and changes final
outputs; simply reversing A/B would be meaningless because their operations
are identical. The retained protected-Racket witness uses the valid skip-A
counterfactual. This establishes a finite state dependency, not training gains.

Changing only paint color was rejected because it would not expose that state
dependency. Iteration until stable was considered but exact one/two passes gives
a bounded, teachable neighboring rule and preserves the original task's local
predicate. Finite declared-rival checks cover update schedule, pass count,
orientation, blocker and equality predicates, and scan conflict priority.
They do not establish universal unique induction or uniform sampling of all
lawful grids. Native validation is separate from production approval.

## Reproduce with current packet tools

Run from the outer directory containing `review.py`:

```sh
WORK/.venv/bin/python review.py run python3 -m pytest generators/01bb2cbe1309/tests/test_native_family.py generators/01bb2cbe1309/tests/test_native_audit.py -q
WORK/.venv/bin/python review.py run python3 generators/01bb2cbe1309/workspace/parametric/audit_native.py --out ../checks/01bb2cbe1309/fresh-teaching
WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric qualify 01bb2cbe1309 --demos 6 --queries 4 --out ../checks/01bb2cbe1309/fresh-qualification --summary
```

Choose new output directories. Qualification contains four episodes covering
both settings at seeds 0 and 17, with all four private query labels per episode.
Use the existing `preview-public export` and `verify` commands to derive public
views. The v2 private manifest shuffles the complete query bank with a private
presentation seed and source-index map; each public file contains just one
query, and its ID hashes only visible bytes. Keep private files and directory
listings with the controller and reveal one public file at a time. The saved
source order is a reproducibility schedule, not a forced presentation order.

The adapter loads only its exact adjacent module. Native manifests bind source
and small current evidence. Owner native qualification and fresh acceptance
remain required after integration; reviewer evidence admits no training data.
