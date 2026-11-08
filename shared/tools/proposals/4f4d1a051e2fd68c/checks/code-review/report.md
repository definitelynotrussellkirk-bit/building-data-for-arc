# Independent code review: d48317a7c7c8

## Verdict

No correctness or contract issue found in the repaired generator or task-local tests. No severity-ranked findings or defect reproducer.

## Reviewed identities

- `repo/generators/d48317a7c7c8/generator.py`: `04a95b8d7c8dedc02acb2277426fa3df55fcb110e995acf700b8f9b64b467cb3`
- `repo/generators/d48317a7c7c8/tests/test_review_regressions.py`: `a00c9d172d9a8ddf25df3875d08a3bd41fde6736dcfc947b22d394c606b444ac`
- `repo/generators/d48317a7c7c8/tests/test_reference_semantics.py`: `80eb6a6d1b3a0bf6e26f69e3e21fe6398157ae392d7d305492842a55cd950b3b`
- `repo/generators/d48317a7c7c8/workspace/probe_review.py`: `fa4ff07817cdb364b7ddf1efe35c456d082a3fb1d30bdfb7ebbc3cc6215cc32d`
- `checks/regressions-before/baseline-generator.py`: `b5b4cb28fb8f4c150ab2c1fe7f5d0e687465eaab2321dc3ad79829e7600706ba`

## Evidence

- Exhaustive guaranteed-fallback sweep: 20,144 cases covering all heights/widths in 8..24, all counts 1..supported capacity, and all eight allowed distractor colors. An independently implemented monochrome four-neighbor component observer found correct dimensions, exact target count, the requested observable distractor color, and at least one changed cap in every case.
- Fallback rivals: all nine declared rivals disagreed with the independent rule on 578 cases (every supported shape at its maximum count, colors 6 and 8). Generator mirror agreed throughout.
- Random constructor: 1,156 cases covering all heights/widths, target count 1 and supported maximum, and colors 6 and 8. All succeeded within the bounded placement routine and passed the independent run detector; ordinary multi-target cases refuted all nine rivals.
- Ordinary API: 48 samples in each of None/easy/medium/hard (192 total), seed 20261008, sample indices 0..47. Every sample had at least two targets and refuted all nine rivals. Repeated identical calls and replay of the observed axes produced identical grids. All four canonical shape anchors and distractor color 6 appeared in each band.
- Packing rejections: all 84 shapes whose documented capacity is below 10 rejected the first count above that capacity with exactly grid_h/grid_w/n_bars in incompatible_axes.
- Both probe reports record identical start/end generator hashes; the generator remained unchanged during these checks.

## Code reasoning

The strict override gate rejects coercible bool/float/string values and undeclared axes while preserving the runtime's documented None-as-unpinned convention. A bounded geometry/count combination is checked against the explicit supported-construction budget before drawing parameters. Unpinned dimensions are selected from shapes supporting the chosen exact count.

The random path checks occupied and protected-cap collisions and same-color cardinal adjacency against prior objects. The internal pattern connections are intentional: the edge singleton is diagonal, the blocked endpoint has a nonyellow blocker, and the bent/overlong components are foils. Every target's claimed available cap remains protected. The color-8 control uses color 6 for the blocker, preserving an actual disagreement with the occupied-cell overwriting rival.

The fallback's core fits inside 8x8 and supplies both independent cap roles whenever n_bars >= 2. Its extra left-column rows contribute floor((h-8)/2) targets; right-hand six-column strips supply at least floor(h/2) targets each. For odd heights the actual number of right-strip rows is ceil(h/2), so the formula underestimates capacity rather than overpromising it. Selecting the better orientation, shuffling spare slots, and reflecting/transposing preserve counts and component separation. The public capacity is a supported-construction bound, not a maximal-packing theorem, and the source states this explicitly.

Task-local tests bind discovery to their own source tree with reviewer_support.find_root(__file__). The semantic probe imports executable rivals from the selected generator and uses a separate run/neighbor-exclusion detector, literal expected cap coordinates, and public canonical application receipts. This review did not independently execute the Racket reference; the parent task owns that validation.

## Scope and limits

Finite probes supplement source reasoning; they do not establish universal identifiability against undeclared rivals. Rich-scene role counts and disjoint protected caps constrain generated support, but those restrictions are explicit and do not invalidate the requested axes or the nine declared rival witnesses. Canonical example/profile overlap does not imply identical input distribution. No generator or test files were edited; reports were written only under WORK/checks/code-review. No audit or draw commands were run, and no solve-directory contents were read.

Detailed machine-readable evidence: fallback-probe.json and random-api-probe.json in this directory.

## Final-source confirmation

The final generator SHA-256 is `7f65ed5ebc7cd917e71a8c6f121bcbdd6d411a6a98bf7c2db5bb5cf69b6717e2`. The source exercised by the independent sweeps above is preserved at `WORK/checks/after/generator.py`, SHA-256 `04a95b8d7c8dedc02acb2277426fa3df55fcb110e995acf700b8f9b64b467cb3`.

A final diff confirms exactly two local identifier renames from `objects` to `components`, including their loop uses: one in `_components` and one in `_prediction`. No imports, constants, branches, expressions, call arguments, data, or other behavior changed. Normalizing precisely that name change makes the complete parsed ASTs identical. This cosmetic lint repair introduces no additional review finding; the existing code-review conclusions carry forward. Large sweeps were not rerun for this confirmation. The parent task is running the final battery, census, and reference tests on the final source identity.
