# Task notes: 57488f2a7c15

## Scope and authority

Version 2.0.0, generator SHA-256 `695c31b0bf2506cde10a9f240b78d59f1bb5efd85038186bc9f532d4305eeaa7`. Canonical Racket `2b970065d6a3` and its ledger are unchanged. The operation overlays the transpose: every nonzero cell is reflected across the main diagonal.

The old independent coordinate sampler could put different nonzero colors at both ends of a transpose orbit. Easy seed 1 / index 1, no overrides, has 9 at (0,1) and 8 at (1,0); actual Racket swaps them, so no label can both preserve sources and complete symmetry. An independently rerun 30,000-draw baseline census found 5,251 conflicting draws, all validator-accepted. This repeats a lead from bundled prior review `review-9a173d367793b6e0:v0001`; current measurements are independently bound to baseline SHA `525a5770fbca7fc5cee98cc5037f313dcf62d77ed87f854f91cd9b150d57657d`.

## Input distribution

Choose distinct unordered off-diagonal orbits before placing colors. An occupied orbit is either incomplete or an equal-color pair; diagonal cells are selected separately. Default training scenes have at least two distinct colors and at least one incomplete orbit. These choices teach color preservation and a nontrivial transformation; lawful monochrome and already-complete fixed points are outside this selected training manifold. Domain tests separately retain lawful fixed-point behavior.

| Exact axis | Range / interpretation |
| --- | --- |
| `side` | 4..16, square dimensions |
| `n_cells` | 2..12 actual nonzero pixels |
| `n_distinct_colors` | 2..9 actual nonzero colors |
| `n_diagonal` | 0..3 occupied diagonal positions |
| `n_pairs` | 0..3 completed equal-color transpose orbits |
| `source_triangle` | lower / upper / mixed incomplete sources; complete pairs do not set orientation |

For M incomplete orbits, P pairs and D diagonal cells: occupied pixels=M+2P+D; independent color groups=M+P+D; occupied orbits fit side*(side-1)/2. Mixed requires at least two incomplete sources. Shared diagonal-color context requires a repeated color group, attached to an incomplete source. Feasible combinations are chosen before random sampling. `observe_overrides` derives exact results from pixels; incompatible requests raise `IncompatibleOverrides` with `incompatible_axes`. Unknown keys and noninteger integer-controls are rejected; None means unspecified. Explicit axes take precedence over the implicit teaching profile, so overrides may displace its witnesses.

Canonical sides 5/6/7 and four/five occupied-cell profiles have positive weight in every band. Hard also favors larger/more occupied grids. Final canonical exact-profile hits: easy 11/20, medium 7/20, hard 4/20. The broader 600/600 strict count refers to this documented training domain, not exact canonical profiles.

## Teaching schedule and limitations

`EXAMPLES_NEEDED=5`; period 18. Every five consecutive ordinary profiles contains incomplete sources in both directions and shared, unique and absent diagonal-color contexts. Over one cycle each lower/context and upper/context combination occurs once and each mixed/context combination four times. All nine joint profiles therefore remain present with independent joint frequencies. Shared-color witnesses place the shared diagonal color on an incomplete source. Eleven distinct rivals and eight explicit witnesses bind these choices; eight rival shortcuts fit all five canonical pairs.

Final source-bound Racket-labelled census: 100 lessons per band, lesson indices 0..99, five demos plus one query, no overrides. All 300 ordered lessons refute all 11 declared rivals; their 1,800 inputs are globally unique. Arbitrary holdouts produce 300 ambiguous rotations out of 1,800 and are diagnostic only. Five is the conservative declared count, not a proven minimum: prefix reanalysis found 147/300 ambiguous three-demo lessons and 0/300 ambiguous four-demo lessons (all rivals refuted in each four-demo prefix). No new labels were computed for that reanalysis.

Public generate defaults to three demonstrations and export defaults to four; these consumers ignore the declaration. Request five explicitly to use the reviewed contract. No four-demo failure is claimed. Shuffled/nonconsecutive examples, arbitrary rotations, and schedule-displacing overrides require their own checks. Finite rivals do not establish universal induction.

## Final verification and retained failures

Final battery: all 12 stages green. Explicit isolated task tests: 155 passed, zero failures/errors/skips. Conflict census: 0/30,000 violations, seeds 0..9999 with index=seed and no overrides in each band; 10,000 unique per band, 21,847 globally unique. Exact override battery: 69,570 attempts, 65,970 accepted, 3,600 explicitly incompatible, no findings/warnings. Repository suite: 359 passed, three optional torch skips.

The review return preserves the before battery, 19 baseline domain-test failures, two intermediate test receipts, the initial provenance-check error and a refused evidence overwrite. The 142-test intermediate pass and earlier zero-conflict report belong to predecessor SHA `1eeda46fe9d082b75511b8266f9588a72bf08e9ba083dabeb05c9ac29c8b5bb4`; final receipts use the SHA at the top of this note. An isolated-environment pytest import issue was fixed with an explicit venv, without shared-code changes.

Reusable probes and commands are in `workspace/README.md`. Root return reports contain exact seeds, source/runtime identities, original logs, solves and audits. No hidden-score or model-training improvement is claimed.
## Current reviewer considerations

Source SHA-256: `695c31b0bf2506cde10a9f240b78d59f1bb5efd85038186bc9f532d4305eeaa7`.

# Decisions — 57488f2a7c15

Final generator: version 2.0.0, SHA-256 `695c31b0bf2506cde10a9f240b78d59f1bb5efd85038186bc9f532d4305eeaa7`. The canonical Racket authority and ledger are unchanged. Findings G1/G2/G3 and integration limit I1 use the IDs in `REVIEW.md`.

## 1. Diagnose the domain before changing labels (G1)

The bundled `evidence/review_index.json` contains an unverified textual lead from return `review-9a173d367793b6e0:v0001`, pinned to baseline source SHA-256 `525a5770fbca7fc5cee98cc5037f313dcf62d77ed87f854f91cd9b150d57657d`. The earlier archive's complete checksum was not supplied in that index and the archive was not opened. Every numerical claim in this return was independently remeasured against the supplied baseline; the prior text was a lead, not accepted evidence.

The first easy witness (`seed=1`, `sample_index=1`, no overrides) contains 9 at (0,1) and 8 at (1,0). Actual Racket execution swaps them, so source preservation and main-diagonal symmetry cannot both hold. The census found 5,251/30,000 such draws, including 5,461 conflicting orbits. A preserve-originals interpretation leaves the pair asymmetric; changing overlay order merely chooses a different failure. I therefore repaired the input domain rather than redefining a sound canonical rule. `checks/conflicts-before.json` retains exact inputs, Racket outputs and hashes.

## 2. Construct compatible orbits instead of retrying

Each unordered off-diagonal pair of positions is selected once. It receives one source or a completed same-color pair; diagonal positions are sampled separately. This makes unequal occupied transpose partners impossible by construction while retaining legitimate equal-color pairs and diagonal cells. A rejection-only patch would be smaller but would obscure the induced distribution and could loop under difficult joint overrides. Restricting every draw to a single triangle would avoid conflicts but fail to teach copying in both directions.

Validation checks rectangular shape, square dimensions, exact integer colors 0..9, the supported counts and palette, compatible transpose partners, and at least one incomplete orbit. It handles malformed inputs without unsafe indexing. The law tests independently exercise actual Racket source preservation, output symmetry and idempotence; the expected results are not obtained from the generator's own mirror.

## 3. Make six input controls exact and observable (G2)

| Axis | Meaning / supported explicit range | Reason and constraint |
| --- | --- | --- |
| `side` | Square side 4..16 | Retains compact canonical-like tasks while permitting larger puzzles |
| `n_cells` | Total occupied input cells 2..12 | Counts actual pixels, including diagonal cells and both cells of complete pairs |
| `n_distinct_colors` | Distinct nonzero colors 2..9 | Guarantees the requested palette is realized; includes canonical five nonzero colors |
| `n_diagonal` | Occupied diagonal cells 0..3 | Supports absent, shared-color, and unique-color diagonal contexts |
| `n_pairs` | Already occupied equal-color transpose pairs 0..3 | Retains lawful compatible overlaps rather than banning them |
| `source_triangle` | lower / upper / mixed | Describes incomplete sources only; completed pairs do not change this observation |

With M incomplete orbits, P complete pairs, D diagonal cells, and K colors, occupied count is `M+2P+D`; available independent color groups number `M+P+D`; and `M+P <= side*(side-1)/2`. Require M>=1 (M>=2 for mixed). Shared diagonal-color mode requires a repeated color group, so K must leave that degree of freedom. Feasible configurations are enumerated first; each weighted choice restricts the remaining feasible set. No requested count is silently clipped.

`observe_overrides` reconstructs every axis from the grid. Unknown controls and wrong scalar types are rejected; Boolean, floating-point and string values are not coerced into integers. Incompatible combinations raise `IncompatibleOverrides` carrying `incompatible_axes`. `None` means unspecified. Explicit overrides take precedence over the implicit teaching profile; fallback may relax that profile but never a requested axis. The teaching guarantee therefore applies only to ordinary no-override lessons.

The earlier intent behind several dead controls and texture modes is unknown; the source and before checks showed they were not reliable exact controls. I removed those advertisements rather than preserving misleading knobs. Version 2.0.0 signals this intentional interface/distribution change. The final override battery evaluated 773 cases × 3 bands × 30 seeds = 69,570 draws, with 65,970 lawful acceptances and 3,600 structured incompatible requests, zero findings and zero warnings.

## 4. Preserve canonical support in every difficulty band

All five canonical pairs are validator-accepted. Sides 5/6/7 and four/five occupied-cell profiles retain positive weight in every band; hard also favors larger scenes. Color allocation attains every chosen distinct-color count. The final exact profile counts were easy 11/20, medium 7/20, hard 4/20, versus no hard support before. Exact profile matches are a support check, not a claim that the samples reproduce the full canonical distribution.

Default lessons intentionally use at least two colors and at least one new copied cell, so they teach color preservation and a visible transformation. Monochrome inputs and already-complete symmetric fixed points can be perfectly lawful under Racket; these are excluded from the chosen training manifold, not reclassified as mathematical rule violations. Law tests retain compatible fixed-point examples separately. I did not ban arbitrary line or diagonal geometry simply to improve a generic lint metric.

## 5. Teach direction and context without coupling them (G3)

The five canonical examples all have lower-only incomplete sources. Eight plausible restricted rules still fit all canonical pairs, including rules whose behavior depends on whether diagonal colors are shared with off-diagonal sources, unique to the diagonal, or absent. Merely mixing upper/lower inputs somewhere in a dataset is insufficient: each lesson must contain the needed refuting examples.

The final schedule has 18 profiles. In each six-position block, position 0 is lower-only, position 3 upper-only, and other positions mixed. Diagonal contexts cycle so every consecutive five-demo window includes shared, unique and absent contexts, with copying in both directions. Over the full cycle all nine triangle/context combinations occur: each lower/context and upper/context combination once, each mixed/context combination four times. Thus neither variable reveals the other in the full-period profile frequencies. A shared-color profile forces its diagonal color onto an incomplete source, not merely an already-complete pair.

The executable contract declares 11 distinct rivals and eight verified semantic witnesses. The shared census materialized 300 lessons, 100 per band, with actual Racket labels and 1,800 globally unique pairs. Every declared rival was refuted in each ordered five-demo lesson. `schedule_contract.py` separately checks every cyclic start at the profile level and explicitly reports zero generated grids/Racket labels; 13 realization regressions connect profiles to 138 actual grids across 23 indices, two seeds and three bands. The profile proof is supplementary to the source-bound label census.

## 6. State assembly limits rather than claiming rotation safety (I1)

Arbitrary query rotations remove a sole context witness in 300/1,800 measured holdouts. With the selected lower-only support, universal six-pair rotation safety against three disjoint context-specific rivals cannot be achieved: each context needs at least two upper-source witnesses to survive every holdout, consuming all six slots and leaving no lower-only example. A synthetic rejected 12-profile proposal is preserved as a schedule diagnostic; it was never presented as an accidental model solve failure or a measured deployment candidate. An earlier provisional 30-profile implementation and its intermediate test evidence are explicitly source-bound.

Five ordered demonstrations are the conservative declared contract, not an established minimum. The final saved-label prefix diagnostic found 147/300 ambiguous three-demo lessons and 0/300 ambiguous four-demo lessons, with all 11 rivals refuted in each four-demo prefix; no four-demo failure is claimed. Public generation defaults to three and export defaults to four; they currently ignore `EXAMPLES_NEEDED`. Explicit `--train 5` / `n_train=5` is required for both. F2 proposes the shared consumer change; it was outside this task's allowed source edits. The retained short-prefix diagnostic reuses saved Racket labels to make this risk concrete without claiming a new generator/API run. Shuffling, arbitrary rotations, nonconsecutive samples, and schedule-displacing overrides need their own identifiability checks.

## 7. Preserve useful failures and honest evidence scope

Baseline battery and focused-test failures are retained. The first census probe exposed a distinction between raw rule-source and wrapped-callable hashes; its failed provenance record remains beside the corrected source-bound census. Nine intermediate tests initially demanded literal error-message text even though the structured incompatibility field existed; correcting the assertion preserved the requested feasibility behavior. The intermediate all-green 142-test run uses predecessor SHA `1eeda46fe9d082b75511b8266f9588a72bf08e9ba083dabeb05c9ac29c8b5bb4`, while the final isolated stage executes all 155 tests on the final hash.

The isolated test runner deliberately hides user-site packages. Initially this hid pytest and caused the explicit task stage plus three repository harness tests to fail. A fresh venv with explicit already-installed test dependencies resolved the environment issue; shared code was not changed. The final repository suite is 359 passed and three optional torch skips. Commands and all real failures remain in `RESULTS.json` and `checks/`.

Both required solves contain one genuine revision, their actual visible feedback, frozen notes, and honest exposure declarations. No intentional negative was manufactured. Both hidden scores remain unknown. Audit-only targets were unchanged, and their findings distinguish an actual generated query counterexample from a constructed input outside an emitter's image. Passing these bounded checks does not authorize training admission or establish measured Qwen3.5-9B improvement.

## 8. Exact delta handoff

The provided packager produced source patch SHA-256 `cf6a97ea7539169f18ea03309ba15c8e87d8efad8afae44acd154d5887e3c118`. The reusable replay tool extracted the original upload into `/workspace/scratch/1a6175758ecb/fresh-replay`, initialized and verified that exact Git root, checked and applied the patch, installed its own bundled Racket and isolated test environment, and passed all 155 task tests again. All 11 patched files match the final working files byte-for-byte; the canonical ledger and audit targets remain unchanged. The final solve uses the same generator SHA. Full command, runtime and hash evidence is in `checks/fresh-replay.json` and `checks/handoff-summary.json`. Lossless compressed evidence was also restored and hash-verified in that fresh copy.
