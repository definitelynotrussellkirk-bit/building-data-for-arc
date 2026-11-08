# Current notes: af840d59f24c — 2.1.1

## Rule and source status

Collect all columns containing zeros, sort left to right, and replace each zero
with its one-indexed global column rank. Preserve every nonzero cell and the grid
shape. The canonical Racket program remains the authority, unchanged in this
return; `RULE_HASH = dbb5a0b9e901`. The Python mirror is diagnostic only.

Current proposed repair source SHA-256:
`d8473b42ac2c72d3ca39b610239caf5d93f1a7d5e50270fdd0f2854ddc332aea`.
Selected baseline `08d52d130454fad7f5911f32affa1ed215c3666c2f7e99e2d3d6715e3514e8a4`
was approved under `review-ae2f760bf63d10e3:v0001`. Its review index listed no
explicit audit findings for this task. Passing this review does not itself
change approval or admit the proposed parametric variants.

## Current generated support

The sole public axis is exact, pixel-observable `scene_profile`:

- `canonical_sparse`: 10 by 10, preserved color 5, four zero columns.
- `wide_many`: 14 by 15, preserved color 9, six to eight zero columns.
- `dense_mixed`: 12 by 16, modal color 8 plus six preserved color-9 cells,
  six zero columns including one full column strictly inside the occupied range.
- `scrambled_order`: 10 by 14, preserved color 6, five zero columns.

Seed and sample index must be actual integers; sample index must be nonnegative.
Negative integer seeds remain valid. Difficulty salts deterministic placement
without changing the profile composition. Unknown keys/values fail explicitly.
The validator describes a broader structural domain than these four geometries;
its accepted inputs are not a claim about generated support.

## Teaching contract and reversals

`EXAMPLES_NEEDED = 4`. Production assembles four demonstrations and one query;
any of the five pairs may be held out, preserving the order of the others.
The old four-profile period was replaced with a ten-position schedule:

`canonical, dense, wide, dense, canonical, canonical, dense, scrambled, dense, canonical`.

Every five consecutive pairs have exactly two canonical and two mixed-color
examples. The old cycle could leave a mixed-color query with four uniform-color
demonstrations: an erase-nonmodal rival survived 3/20 seed-0 rotations. The new
schedule leaves a preservation witness in every supported holdout. A first
repair with less canonical density was rejected after the profile-floor check
measured only 9/60 envelope hits. The final schedule measures 20/60.

The previous fixed construction order/count templates were also reversed.
Two wrong template rivals fit 48/48 baseline generated examples but 0/4 canonical
pairs. Keyed whole-row and occupied-column permutations now reject both templates
and ordinary first-seen/frequency ranks while preserving lawful profile structure.
A later repair keeps full zero columns inside the occupied range, after shared
first/topmost-object rivals exposed remaining ambiguities at three retained
seeds. Both sides must contain changed cells.

Nine distinct lesson rivals are executable: base5-only, ten-by-ten-only,
clamp-after-four, erase-nonmodal, row-local rank, first-seen rank, frequency rank,
and the two old template ranks. The first four fit every canonical pair and need
noncanonical teaching witnesses. Forced single-profile overrides are authoring
controls; arbitrary override-composed lessons do not inherit the schedule guarantee.

## Evidence and tools

Return `review-c0701bd95262eacd` retains exact invocations and hashes in RESULTS:
12/12 strict battery stages green; 116/116 portable task cases passed without
failures, errors or skips. Fixed seed 0 checks all ten starts across three bands:
30 lessons, 150 rotations, 42 unique inputs, no checked ambiguity. The larger
census contains 300 lessons, 1,500 unique inputs and 1,500 rotations, with no
checked ambiguity or materialization/scoring errors. These are finite rival checks.

`workspace/probe_rank_shortcuts.py` independently measures the two template
rivals and preservation, iterates actual declarations, and enumerates the actual
schedule. Final seeds 0, 17, 99173 across None/easy/medium/hard give 168 generated
plus four canonical Racket checks and 600 scoped rotations without ambiguity.
It excludes shared generic rivals; the strict battery/census handle those.
The task-owned reference helper now uses the public selected-source loader and
correct staged dependency root, resolving a retained portable collection failure.

Small reproducible witnesses live in `counterexamples/`; full before/intermediate/
final evidence remains in the return's `checks/`. Earlier failures are retained,
not relabelled as final passes. The complete random-census report records child
exit 0, but its outer exit observation was lost to a tool transport interruption.

## Proposed parametric extension and remaining limits

`workspace/parametric/prototype.py` varies grouping axis (columns/rows) and rank
direction (forward/reverse), fixed once per episode. The canonical default emits
the exact selected Racket text. All settings use the same two sparse profiles,
with both orientations validated. Final build/replay: four episodes, 136 Racket
labels identically re-executed, 12/12 alternative-setting rivals and 60/60
rotation-rival comparisons refuted, 22 focused tests passed. The fixed public
filename leak found during peer review was repaired and covered by a regression.

The variants remain proposed. No evidence here establishes arbitrary-program
identifiability, all-seed coverage, wider geometries/palettes, or model-training
accuracy. The two separately assigned audit findings remain open on their own
unchanged sources. See the return's AUDIT.md, DECISIONS.md and REVIEW.md.

The incomplete unselected strict-scalar proposal atf2315b51 is superseded by accepted source d8473b42ac2c72d3ca39b610239caf5d93f1a7d5e50270fdd0f2854ddc332aea fromreview-c0701bd95262eacd. Old08d52d13 hash is the selected source AT PROPOSAL TIME, not current source. Its missing-negative-index guard and absent full review are resolved by the accepted complete return; no results are transferred to proposed bytes. Original proposal files/manifests remain exact source-bound evidence of this reversal, with no outstanding rebase/approval request. See `evidence/superseded-scalar-proposal/manifest.json`.
## Current reviewer considerations

Source SHA-256: `d8473b42ac2c72d3ca39b610239caf5d93f1a7d5e50270fdd0f2854ddc332aea`.

# Decisions: af840d59f24c

This return starts from selected baseline `08d52d130454fad7f5911f32affa1ed215c3666c2f7e99e2d3d6715e3514e8a4` and ends at `d8473b42ac2c72d3ca39b610239caf5d93f1a7d5e50270fdd0f2854ddc332aea` (version 2.1.1). The canonical Racket program, authority selection, and `RULE_HASH = dbb5a0b9e901` are unchanged. All claims about new behavior use this return's checks, not inherited approval.

## D1 — Develop the original-family extension first

The assignment explicitly prioritized a parametric extension of original ARC family training:575b1a71. A baseline-bound prototype was built and executed before changing the canonical generator. It exposes two small choices: group zero cells by columns or rows, and rank those groups forward or reverse. The default is exactly the selected column/forward rule. Object roles, global grouping, one-indexed spatial ranks, output shape, and nonzero preservation are shared across all settings.

The parameters are fixed once per episode. The sampler uses the same canonical_sparse and scrambled_order profiles for every setting, checks both orientations, and keeps the rank alphabet within 0–9. Transposing inputs only for row settings was rejected because the input distribution would reveal the parameter. The prototype deliberately does not promise the canonical generator's entire four-profile domain for all variants. A shared lawful contrast input yields four different outputs.

Initial evidence is under `checks/parametric/initial/`. Evidence named `checks/parametric/final/` belongs to intermediate source `7438a8b9…`; the final source uses `checks/parametric/final-d8473b42/`. Independent review caught fixed public-file numbering that revealed settings. Numbering now follows seed selection, with a regression. The final build and replay each execute 136 Racket labels; four episodes refute 12/12 alternative-setting rivals and 60/60 rotation-rival comparisons. Variants are proposed, with no approval change.

Instantiated Racket program SHA-256 values (exact text, including the canonical default):

| Setting | SHA-256 |
| --- | --- |
| columns-forward | `cb03ce1f544d8fca4c04b3bed3793b05ab88cef02d7caa86919aaa6e69ccf50f` |
| columns-reverse | `a8a42e2b26d147f893a6a723fbf231c7e8d5f4f2ec8aa12aef408196c05a649c` |
| rows-forward | `1e228b8db443fc64fdaaee361c2d730abe0a9fc9ef982ec95e9463a51df77578` |
| rows-reverse | `1ff0c5e8a8a26d72672a168f06f26380db2bfc7bbc81f7493442a1818116f7f4` |

These hashes are retained in `checks/parametric-agent-report.json` and the final build evidence.

## D2 — Reject coercible stream values before generation

M1: the baseline's generator context accepted bool, float, and string stream values, and negative sample indices. Defect lint emitted 33 warnings, and focused cases reproduced the behavior. Both `generate` and `schedule_profile` now require the actual Python type `int`; `sample_index` must be nonnegative. Negative integer seeds remain valid deterministic keys. The existing difficulty and override contracts remain enforced by `generate`.

Silent coercion was rejected because distinct caller inputs could alias the same stream and malformed indices silently selected a profile. The unselected historical strict-scalar proposal was a lead only; it lacked runtime evidence and still admitted negative sample indices. The selected baseline was tested directly.

## D3 — Break construction templates while preserving lawful structure

M2: baseline construction order and zero-frequency templates encoded rank independently of spatial ordering. Two deliberately wrong template rivals fit 48/48 sampled baseline generated inputs, but 0/4 canonical pairs. Row and occupied-column mutations remained lawful under the validator and actual Racket execution while breaking these templates (`checks/independent-review/baseline_report.json`).

`_vary_layout` applies deterministic keyed permutations to complete rows and occupied columns. It accepts only layouts where ordinary first-seen ranking, frequency ranking, and both old construction-template rivals disagree with the canonical diagnostic mirror. It tries at most 64 candidates, then a deterministic reversed-column fallback that satisfies the same checks. Nonzero cells move with their rows/columns, and each profile's observable contract is preserved. Generated examples need not retain construction order to express the rule.

Merely adding rivals without changing the distribution was rejected: it would report the shortcut without providing better lessons. Unrestricted random grids were also rejected because they would discard reviewed canonical support and the exact public override. The independent final probe found 0/168 matches for either template at seeds 0, 17, and 99173 across all four bands, including None; this is finite support, not universal proof.

## D4 — Compose lessons for every permitted holdout

M3: `erase_nonmodal` ranks zero cells correctly but overwrites all nonzero colors with the modal nonzero color. It fits all four canonical pairs and every uniform-color example. At baseline seed 0, positions 0–4 with position 2 held out, the remaining four demonstrations fail to teach the query's six preserved decoy cells. Across the four baseline schedule starts, 3/20 rotations are ambiguous even though the original lesson hook accepts them.

Four demonstrations plus one query are retained. The query may be any of the five pairs; remaining demonstration order is preserved. Accordingly, rotation is required, not merely diagnostic. The schedule is:

| Position modulo 10 | Profile |
| --- | --- |
| 0 | canonical_sparse |
| 1 | dense_mixed |
| 2 | wide_many |
| 3 | dense_mixed |
| 4 | canonical_sparse |
| 5 | canonical_sparse |
| 6 | dense_mixed |
| 7 | scrambled_order |
| 8 | dense_mixed |
| 9 | canonical_sparse |

Every five consecutive positions contain exactly two canonical profiles, two dense mixed profiles, and one wide/scrambled profile. Removing any query leaves at least one canonical and one mixed example; the mixed example also supplies ranks above four and noncanonical geometry. This schedule covers the four canonical-fitting shortcuts without relying on which pair becomes the query.

The first repair used a shorter dense-heavy schedule. Its explicit rivals passed, but the profile-floor gate measured only 9/60 exact/envelope canonical hits, below 15/60 envelope support. Adding canonical density through the ten-position schedule fixes that concrete failure: final exact/envelope support is 20/60, with 8, 8, and 4 hits over 20 draws in each band. Uniform random profile choice was rejected because it does not guarantee that the preservation witness remains in the demonstrations.

A fixed-seed check enumerates all ten starts and all five holdouts across easy, medium, and hard (30 overlapping lessons, 150 rotations, 42 unique inputs). The larger random census adds 300 lessons and 1,500 unique inputs/rotations, with zero observed ambiguity. Neither count proves all-seed identifiability or excludes all possible rivals. Forced single-profile overrides are for controlled authoring probes; arbitrary override-composed lessons do not inherit the production schedule guarantee.

## D5 — Keep dense separators inside the changed region

M4: the first layout repair could move the full zero column to an outer occupied position. Shared searched rivals that transform only the first/topmost component then survived specific rotated lessons. Three retained seeds/starts in `tests/test_review_regressions.py` reproduce those failures; `checks/second-regressions-before.xml` contains the failing run.

The full zero column must now lie strictly between other zero-containing columns. Both sides contain cells whose rank changes, so a first-component-only transformation cannot account for the whole output. The final strict semantic check and required-rotation census include the shared searched-rival diagnostics. The independent rank probe intentionally has a smaller rival scope and is not substituted for those checks.

## D6 — Preserve the four observable profile choices

| Profile | Generated support | Purpose retained from baseline |
| --- | --- | --- |
| canonical_sparse | 10×10; preserved color 5; four zero columns | Canonical-profile support |
| wide_many | 14×15; preserved color 9; six to eight zero columns | Noncanonical geometry and ranks above four |
| dense_mixed | 12×16; modal 8 plus six preserved color-9 cells; six zero columns, one full | Nonzero preservation and dense global evidence |
| scrambled_order | 10×14; preserved color 6; five zero columns | A second shape/palette and ordering counterexamples |

Difficulty salts layout randomness while preserving semantic profile composition. The exact `scene_profile` override remains deterministic and recoverable from pixels. No extra public override axis is introduced. The validator checks a structural domain broader than these four generated shapes; the public sampler's support and the validator's acceptance set are not interchangeable. The review does not claim arbitrary sizes, palettes, or independently forced override lessons are covered by the measured production curriculum.

## D7 — Repair task-local portable imports

T1: direct focused tests passed, but the portable aggregate initially failed collection with two cached-dependency source mismatches. The task-owned `workspace/reference_probe.py` was prepending `shared/runtime` even inside an isolated snapshot, causing a mixture of source roots when new tests used the public selected-source loader.

The helper now detects a staged root using its runtime manifest and public support module, chooses the correct dependency root, and loads the selected generator through `load_selected_generator`. The default repository path still works. No shared support module or frozen root fixture was modified. The rerun at `checks/task-tests-final2/` executes 116 cases with zero failures/errors/skips. The earlier failed portable receipt is preserved.

## D8 — Preserve evidence and distinguish status

The selected review index had no explicit audits for the main task; its approved decision points to `review-ae2f760bf63d10e3:v0001`. Historical notes were replaced with a concise current account rather than appending contradictory current versions. Earlier decisions remain in the original packet and prior return.

All baseline and intermediate failures in this review are retained. A tool transport interruption lost the outer random-census exit observation; the complete gzip report, SHA mapping, 300-lesson totals, and child exit-0 receipt survived. The outer exit remains null. The later helper change did not alter generator bytes; source-bound test manifests distinguish it from the earlier rank probe.

The blind solve is a separate one-revision 3/3 visible record with no earlier exposure. The final post-repair solve is a one-revision 4/4 visible record with earlier exposure disclosed and no references consulted during that phase. Both private labels are unknown. The earlier exposed solve is retained under its intermediate source hash.

Audit findings on `7e9fd4cf84a9` and `5ccdbe078da6` are not patched here. They remain actionable source-bound reports in `AUDIT.md`, regardless of acceptance of the main repair. No Qwen training was run; the proposed data-quality gate is justified by a concrete ambiguous lesson, not by an asserted model-accuracy increase.
