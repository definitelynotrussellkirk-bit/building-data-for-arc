# Independent whole-change review — 2ca05c7eef24

**Readiness verdict:** The initial review found three Important defects and one Minor compatibility surprise. All four now have scoped corrections, which I inspected; the 14 selected regression cases for those corrections passed on the hashes below. I found no remaining Critical or Important issue in the corrected code. This is readiness for the parent agent's final required battery, actual 729-vote audit, production/rotation census, and fresh replay, not a claim that those separate runs have already passed.

## Scope and source binding

- Assignment: `review-40d2bd8fd0adb4ae`; task: `2ca05c7eef24`.
- Compared the selected task delta from `ad71b19` through checkpoint `04faae860803cb2899d9fe779d2f9ca69332d2f4`; initial reviewed generator SHA-256 was `cedfb31fe522e7c8ff108466e86f44f8670a31afb8fc9bf174fd599f35f550e2`.
- Reviewed the ensuing eight-slot schedule, truthful optional count provenance, and count-domain extension on generator SHA-256 `9d029f8175e0b048a496eaeb6c2dd87b2401fd3c946729b164390a5f446e683e`.
- Inspected the final targeted corrections and ran their selected regressions on generator SHA-256 `eceab1ffd0c9487dc64e28b34b9e724049db31e2530a389f6c28ecfbd1b90b25` and probe SHA-256 `b47e286bed56bb3f37cb94eeb15d06a14ee5a5cc21c9c37d398d283ca283b747`. These hashes were unchanged before/after the selected regression run.
- Read the implementation plan and its cited assignment/semantic contract, the selected generator, task notes/summary, task counterexamples, independent probe, and both focused test files. Inspected the public GenCtx methods relevant to the implementation.
- No source, index, HEAD, reference program, solve file, or other task was modified. All reviewer writes are under `WORK/checks/code-review/`. No subagents were used. No solve-private answers were opened.

File/line references below identify the original checkpoint unless explicitly labeled corrected. Paths are relative to `WORK/repo/generators/2ca05c7eef24/`.

## Strengths

1. **The local voting implementation is direct and correct by inspection.** `generator.py:87-103` first discards zero, requires two nonzero votes, then maximizes `(local_frequency, numeric_color)`. Both lower and higher repeated majorities are covered, so the intended ordering is not reduced to a numeric maximum or minimum rule.
2. **Validation is substantially stronger and its claim is appropriately scoped.** `self_check` checks Python integer colors, rectangular row lists, the exact geometry, and gray only at the two divider columns. Caller metadata does not bypass it. Its documented claim is the visual input domain, not teaching quality. The broader strict-manifold check is separate from the empirical canonical size/palette profile floor.
3. **The controlled constructor has an understandable feasibility argument.** Every foreground cell is chosen once, the initial palette assignments guarantee exact realization, and the three occupancy modes have explicit capacity conditions. The constructor uses public GenCtx methods without mutating private context state. The incompatible-axis errors expose rejected joint requests instead of clipping values.
4. **The full pinned capacity sweep was clean.** The original 1..6 domain had 8,601 accepted and 2,199 structured rejected requests, with no discrepancies across 10,800 combinations. The expanded 1..18 domain had 20,289 accepted and 12,111 structured rejected requests, with no discrepancies across all 32,400 combinations of height, width, count, palette, texture, and difficulty. Both palette aliases were pinned to the same exact value in each case. The later lesson corrections do not change these fully constrained constructor paths.
5. **The schedule refinement preserves the required holdout property.** In `[1,2,3,3,1,1,3,3]`, every four consecutive slots contain two three-color slots. Removing any one query leaves at least one such demonstration. The additional monochrome slot addresses the measured profile-floor miss without removing that structural guarantee. The final constructor verifies all twelve declared rivals on each returned three-color witness, with a finite fallback.
6. **The independent probe is meaningfully independent.** Its Counter-based expectation never calls `generator.apply_rule`. It packs all 729 ordered triples into 18 legal 7-by-20 inputs and checks the 27 padding cells too. Receipt inputs, ordered indices, dimensions, output types, digests, and authority bindings are checked. Dynamic declarations prevent a stale copied rival list from masquerading as coverage. The unsigned-receipt limitation and Python-proxy coverage label are explicit.
7. **The test additions address behavior rather than just implementation shape.** Literal votes, canonical labels, structural rejection, observation of exact controls, retained ambiguity lessons, neutral defaults, and forced bad-layout fallback all test externally meaningful outcomes. The bounded-fallback test forces repeated rejected layouts; it does not merely assert that a retry loop exists.

## Critical

None found.

## Important — reproduced and corrected

### I1. The original motif histogram teaches global rarity as a substitute numeric tie-break

**Location:** `generator.py:182-192`, especially the original `(0,a,a)` motif at line 184; ordinary generation returned without checking global color priorities at line 197.

For three colors `a < b < c`, the seven original motifs contribute global foreground frequencies `a:9, b:6, c:1`. A plausible rival that keeps the true local majority but resolves local frequency ties by the globally least frequent color therefore exactly matches every easy ordinary input. Random clutter can reverse that correlation on a query while demonstrations still fit the rival.

**Exact reproduction:** medium, seed 3, consecutive indices 0..3, hold out index 0 and use indices 1,2,3 as the three demonstrations. The rival fits all three canonical labeled pairs and all three retained demonstrations. The current-at-review lesson hook returned `[]`. At query row 2, column 2, actual Racket returns 7 and the rival returns 4.

**Measured support:** over 40 seeds, indices 0..11, and each of eight four-draw starts, the rival fit 480/480 easy inputs. It produced 65 ambiguous medium rotations and 139 ambiguous hard rotations out of 1,280 rotations in each band. The windows overlap; these are rotation counts, not independent lessons or unique inputs.

**Consequence:** correct labels and a pass against the original eight competitors did not establish the requested teaching property for this additional plausible rule.

**Evidence:** `review-probe-results.json`, `global_rarity_tie-first-ambiguity.json`, `global-rarity-racket.json`, `global_rarity_tie-authority-verification.json`, and `canonical-fit-and-neutral-default.json`.

**Correction inspected:** corrected `generator.py:195-219` changes the same-color pair to `(0,b,b)`, checks completed layouts after clutter, and permits at most 64 attempts before a checked core-only fallback. The four added global rivals are declared at corrected lines 335-360. This retains variable random histograms while supplying explicit counterexamples.

### I2. An arbitrary first-appearance color priority can fit all demonstrations and change the query

**Location:** `generator.py:186-197` and the incomplete original competitor set at lines 307-309.

This rival uses the correct local vote frequency but prefers whichever tied color first appeared in a row-major scan of the input. Randomized placement can accidentally align that priority with the numeric rule in all demonstrations, then change on the query.

**Exact reproduction:** easy, seed 27, consecutive indices 0..3, demonstrations 0,1,2 and query 3. The rival fits all three canonical labeled pairs and all three demonstrations. The original hook returned `[]`. Racket confirms query disagreements at `(0,1)`, `(1,3)`, and `(2,3)`: actual colors 6,7,6 versus rival color 4 at all three positions.

**Measured support:** the same bounded scan found 5 easy, 16 medium, and 17 hard ambiguous rotations out of 1,280 per band.

**Consequence:** the missing distinction affects an ordinary production ordering, not only an unusual override or a hand-constructed out-of-distribution query.

**Evidence:** `first_seen_tie-first-ambiguity.json`, `first-seen-racket.json`, `first_seen_tie-authority-verification.json`, and the shared bounded-probe reports.

**Correction inspected:** first-seen and last-seen priorities are now declared along with both global frequency priorities. A completed three-color draw must refute all twelve alternatives. The row-major fallback begins and ends with the lowest color, so it provides actual scan-priority refutations; the forced-unlucky-layout regression exercises this path.

### I3. Sidecar equality accepted type-corrupted metadata with an invalid stored digest

**Location:** `workspace/probe_vote_support.py:200-201`.

The original scorer compared `meta == current_meta`. Python equates `False` with `0`, and integer-valued floats with integers. It never separately recomputed `metadata_sha256` from the received sidecar.

**Exact reproduction:** prepare a fresh request and a clearly labeled synthetic parser receipt, then change one metadata value while leaving its checksum unchanged: mapping vote `0 -> False`, mapping index `1 -> 1.0`, alphabet entry `0 -> False`, or `triple_count 729 -> 729.0`. All four variants returned `passed: true`, even though the retained and recomputed metadata digests differ.

**Consequence:** the documented strict rejection of altered preparation metadata was false. This finding does not claim that the unsigned receipt can authenticate its producer, nor that the accepted type changes caused a wrong canonical vote label.

**Evidence:** `probe_review.py`, `review-probe-results.json`, and the explicitly named `synthetic-accepted-*.json` parsing reports. These files are synthetic parser evidence only, never Racket evidence.

**Correction inspected:** corrected probe lines 201-208 recompute the received sidecar digest and compare a type-sensitive canonical JSON serialization with the reconstructed metadata. The new tests cover both unchanged and recomputed digests. All eight type-change cases passed in my selected correction run.

## Minor — reproduced and corrected

### M1. Explicitly passing the advertised neutral texture default disabled ordinary teaching

**Location:** `generator.py:265`.

`generate(0,2,difficulty='easy')` and the same call with `texture='default'` produced different distributions even though both observed texture values were `default`. Both had the same 3-by-4 panel geometry and three colors; the explicit-default call switched to two occupied cells per panel, while the ordinary draw had unequal counts and the full teaching core.

The weaker override contract was documented, so this was less severe than an undisclosed lesson guarantee failure. Still, a neutral default option is a reasonable no-op expectation, and the previous generator preserved it.

**Evidence:** `canonical-fit-and-neutral-default.json`.

**Correction inspected:** corrected `generator.py:286-289` removes neutral `texture='default'` from the meaningful-constraint set. Its dedicated regression passed. Exact geometry, count, palette, and nondefault texture requests continue to use the controlled constructor.

## Verification performed by this reviewer

| Check | Source | Result |
|---|---|---|
| All 10,800 pinned h/pw/n1..6/palette/texture/band requests | `cedfb31f...` | 8,601 exact accepted; 2,199 structured rejected; 0 discrepancies |
| Independent rarity and first-appearance rival scan | `cedfb31f...` | Reproduced the counts above and retained exact lessons |
| Canonical rival fit | `9d029f81...`, unchanged authority | Both rivals fit all 3 labeled canonical pairs |
| Public Racket apply of each retained four-pair lesson | Authority `92b2f8e4de94` | All 8 retained labels match; query differences confirmed |
| All 32,400 pinned h/pw/n1..18/palette/texture/band requests | `9d029f81...` | 20,289 exact accepted; 12,111 structured rejected; 0 discrepancies |
| Selected correction regressions | Generator `eceab1ff...`, probe `b47e286b...` | 14 passed, 131 deselected, exit 0, 2.17 seconds |

The two Racket receipts name the later `9d029f81...` generator, whereas their retained inputs were materialized from `cedfb31f...`. The unchanged authority labels those exact input bytes; the compact authority-verification records explicitly distinguish the lesson-source and receipt-source hashes. I do not present those receipts as proof that the later generator reproduced every earlier input.

The selected final run covered retained ambiguity recognition, new global-priority refutation, forced bounded fallback, neutral default behavior, cyclic ordinary rotations, and all eight type-sensitive sidecar cases. See `fix-tests.xml`, `fix-test-source-hashes.json`, and `commands.json`.

## Declined to judge / explicit limits

- No claim of universal rule identifiability. The final constructor explicitly checks twelve rivals; other hypotheses remain outside that finite claim.
- No full final-source battery, 729-case reference run, 300-lesson production census, complete phase enumeration, fresh replay, package integrity, approval, or admission claim. Those are separate parent-owned final gates and must be reported from their actual completed outputs.
- No claim that explicit meaningful override lessons are as diagnostic as ordinary lessons. Their weaker contract is disclosed; exact construction was checked independently.
- No hidden solve scoring or assessment of the two separately assigned audit tasks. Those files and tasks were outside this review.
- No authentication claim for unsigned JSON receipts. The canonical authority cache is keyed by path, modification time, and size; I did not treat a deliberate same-size/same-time file replacement in a long-lived process as a receipt-authentication requirement. The ordinary CLI paths use separate processes. A consumer requiring stronger same-process content freshness would need a stronger cache policy.
- No human-difficulty claim. The bands vary geometry and clutter; the notes correctly avoid presenting them as a measured human difficulty scale.

Subject to the parent-owned final gates and the hashes above, the corrected change is ready to proceed. There is no remaining code-review blocker identified in this review.
