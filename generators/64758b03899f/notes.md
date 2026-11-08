# Working notes — 64758b03899f

## 2026-10-07 — assignment `review-c10f4bfcab3749ee`

Imported generator 2.0.1 was replaced by generator 3.0.0. Canonical semantic authority is unchanged: extract all color-5 cells, normalize them by the top-left of their bounding box, clear the input, and stamp those offsets at every nonzero non-5 anchor using the anchor's own color. `RULE_HASH = "daa4a7279074"` pins that authority.

### Baseline findings

The pinned source fixed one four-cell mask at one location, fixed three anchor locations, and varied little beyond dimensions and three colors. Several declared axes were singleton or aliases, the required `RULE_HASH` was missing, and the summary incorrectly said the source mask remained in the output. The interrupted before battery retained lint failure plus passing self-check/rule-smoke evidence under `checks/before/`; it did not complete and is not reported as a finished baseline battery.

The strongest plausible shortcut is **normalize from the first row-major color-5 cell**, not from the bounding-box top-left. It fits all five canonical pairs because each canonical mask contains normalized `(0,0)`. A hollow-origin mask separates it. The exact final-source witness is `counterexamples/first-mask-cell-origin.json`; canonical Racket output is retained at `checks/selected-counterexample-racket-v2.json` and differs from the shortcut in eight cells.

### Current sampler decisions

- Exact observable axes are `grid_h` 9..13, `grid_w` 12..18, `mask_family` over eight connected families, and `n_anchors` 2..3. Unknown, mistyped, or out-of-domain overrides reject.
- Four mask families reproduce the canonical structural families. Three additional families omit normalized `(0,0)` and directly refute first-cell-origin normalization; one additional hook broadens geometry while preserving the canonical law.
- Constructive placement chooses a non-origin source bounding box, isolated anchors, in-bounds footprints, no source/footprint overlap, and no footprint/footprint overlap. Anchor colors are distinct members of `{1,2,3,4,6,7,8,9}`.
- The four-slot schedule is `canonical_two`, `hollow_origin`, `canonical_three`, `hollow_broad`. The initial candidate had only one guaranteed hollow-origin slot. Its semantic smoke check passed ordered production lessons but found 2 ambiguous query rotations out of 60. The final schedule guarantees two hollow-origin slots per period, so every five-pair lesson still has at least one such witness after any one pair is held out.
- `EXAMPLES_NEEDED = 4`, `LESSON_SCHEDULE_PERIOD = 4`, and `MIN_STRICT_FRAC = 1.0`. Production lessons use four demonstrations and one query. Query rotation is supported for the declared six rivals, not merely treated as diagnostic.

### Semantic contract and tests

Declared rivals cover marker-only output, bounding-box fill, first-anchor-only stamping, keeping the source mask, first-mask-cell origin, and stamping in color 5. Each has a named witness and executable counterrule. `lesson_identifiable` rejects malformed labels and any lesson whose four demonstrations leave a declared rival viable.

Task-local tests cover canonical acceptance and an independent Python reference, exact overrides in every difficulty band, invalid overrides, deterministic distribution coverage, cyclic schedule coverage, every query holdout, all declared rivals, destructive mutations, and replay of the retained exact counterexample. These tests are supplemental to the canonical Racket checks, not an alternate authority.

### Racket-source synchronization

The selected bank file had canonical `raw_code` but a `target_code` differing only by one explanatory comment. Defect lint classified that as unsynchronized rule-source divergence even though sampled behavior matched. `target_code` and its status were synchronized to the canonical `program_solution`; the executable rule, canonical row, rule hash, and outputs did not change.

### Measured final evidence

Final generator SHA-256: `74c55295d20f82a9faddb7011f2e11b92b8846e55d81a9b0b208339fe77aa5a8`.

- Required-rotation semantic gate: strict 600/600; ordered lessons 12/12 identifiable; rotations 60/60 identifiable; no warnings or errors. See `checks/focused-semantic-rotations/`.
- Large lesson census: 300/300 lessons, 1,500 pairs, 1,500 unique inputs, 0 production ambiguities, and 0/1,500 ambiguous rotations across easy/medium/hard. See `checks/lesson-census.json`.
- Declared-period census: all 12 band × start-residue lessons and all 60 query rotations passed at fixed seed 0. See `checks/lesson-census-period.json`.
- Focused task suite currently has 25 tests. The source-bound staged result and final battery are recorded in the root review documents.

### Limits and open scope

The generator intentionally excludes clipped stamps, overlapping source/stamps, overlapping stamp footprints, duplicate anchor colors, multiple mask components, arbitrary masks outside the eight declared families, anchor counts outside 2..3, and dimensions outside 9..13 × 12..18. Difficulty changes the default broad size distribution but does not narrow legal overrides. The finite rival set and sampled censuses do not prove unique induction against every imaginable hypothesis or measure downstream model accuracy. Catalog approval remains false and was not modified.
## Current reviewer considerations

Source SHA-256: `74c55295d20f82a9faddb7011f2e11b92b8846e55d81a9b0b208339fe77aa5a8`.

# Decisions — 64758b03899f

Assignment `review-c10f4bfcab3749ee`; selected implementation version 3.0.0. “Original rationale” below distinguishes source comments from reviewer inference. The imported notes contained no substantive design history beyond a description of the fixed layout.

## D1. Preserve the canonical transformation; synchronize only the duplicate bank text

**Original rationale:** The canonical examples, written solution, and executable program all implement one rule: normalize every color-5 cell by the mask bounding-box top-left, clear the input, and stamp the normalized offsets at every nonzero non-5 anchor in that anchor's color. The imported generator's prose mostly described that rule, although it incorrectly said the source mask remained.

**Choice:** Keep canonical `program_solution` and rule hash `daa4a7279074` unchanged. Add the required `RULE_HASH` pin and an independent Python mirror used only for tests/contracts. The selected bank's `raw_code` already equaled canonical, but its `target_code` contained one extra comment. Because after-policy defect lint treats behavior-equivalent source divergence as blocking, synchronize `target_code` byte-for-byte to canonical and mark its canonicalization status accordingly.

**Alternatives rejected:** Change the authority to keep the source mask, clip a different way, or treat anchors as centers. All contradict canonical outputs. Ignore the bank warning as cosmetic. This would leave a required after gate red and two textual authorities for future tools.

**Probes:** Canonical 5/5 pairs match the independent mirror; rule smoke, Racket lint, authority sync, and defect lint pass. `arcpuzzles apply` on the retained shortcut witness matches the mirror.

**Limits/failure modes:** Synchronizing duplicate text is not new semantic evidence. Catalog approval remains false. A future canonical rule change must update `RULE_HASH`, mirrors, and tests together rather than silently relying on this pin.

## D2. Replace fake axes with four exact, pixel-observable controls

**Original rationale:** Unknown. Version 2.0.1 declared eight axes, but `palette_size`, `position_bias`, and `n_distinct_colors` were singleton values, `texture` aliased palette behavior/degenerates, and the generated scene remained essentially fixed. Baseline lint explicitly rejected the missing rule hash and warned about collapsed/unprobed axes.

**Choice:** Advertise only `grid_h`, `grid_w`, `mask_family`, and `n_anchors`. Their legal domains are 9..13, 12..18, eight named families, and 2..3. Every override is exact and reconstructed from pixels by `observe_overrides`. Unknown names, booleans-as-ints, mistyped values, and out-of-range values reject.

**Alternatives rejected:** Retain diagnostic singleton axes; keep a generic “texture” axis; use soft targets that the sampler may ignore. These add apparent dimensionality without controlled interventions.

**Probes:** Every axis is forced in every difficulty band; invalid override tests; repository override gate; distribution test reconstructs the requested values. Final source-bound tests contain 25 passes.

**Limits/failure modes:** The four axes intentionally do not expose source position, anchor colors, or profile as user controls. Those remain keyed randomness. `None` is treated as no override through the established generator context.

## D3. Cover canonical geometry and the missing origin distinction

**Original rationale:** The old source hard-coded a single four-cell shape that did not represent the four distinct canonical training shapes. No retained rationale explained that restriction.

**Choice:** Include the four canonical families (`diag4`, `tee4`, `corner3`, `cup5`), one broader origin-filled hook, and three connected hollow-origin families. The hollow families have a valid bounding box whose `(0,0)` cell is empty. This is the minimal structural distinction needed to separate bounding-box normalization from first-row-major-cell normalization.

**Alternatives rejected:** Arbitrary random polyomino enumeration. It broadens support but complicates observability and validation without evidence that every shape is useful. Only canonical families. This preserves the strongest canonical-fitting shortcut. Rectangles only. This also makes bounding-box-fill indistinguishable.

**Probes:** The semantic gate identifies `use_first_mask_cell_as_origin` as fitting 5/5 canonical pairs and records the hollow-origin witness as satisfying that ambiguity. Final semantic sample fires that witness 302/600 times; all 60 checked rival claims disagree with canonical output on witness-bearing inputs. Exact witness and eight differing cells are retained in the task counterexample.

**Limits/failure modes:** Support is eight families, not all connected masks. The validator deliberately rejects other lawful-to-the-Racket-rule masks because the generator contract is narrower than the full rule domain. This finite family choice is a curriculum boundary, not a claim of necessity.

## D4. Use constructive disjoint placement

**Original rationale:** The imported source chose fixed locations where its one shape happened to fit. It had no general collision policy because source, anchors, and projected stamps did not vary independently.

**Choice:** Enumerate feasible non-border source origins, shuffle deterministically, enumerate legal anchors whose entire projected shape fits, and backtrack to select 2 or 3 anchors. Require source/stamp disjointness, stamp/stamp disjointness, isolated anchors, and no anchor inside another stamp. Raise if a documented axis combination cannot be constructed instead of silently shortening the requested structure.

**Alternatives rejected:** Rejection sampling with a retry cap, which can bias or sporadically fail; clipping projected stamps, which creates a separate edge-case lesson; allowing overlaps, which can make label effects order-dependent or erase evidence.

**Probes:** 600/600 strict semantic draws, repository self-check/dist/diversity/profile gates, deterministic replay tests, destructive mutation tests, and exact override sweeps.

**Limits/failure modes:** The sampler does not teach clipping, overlap precedence, or source/target collisions even though the canonical Racket program has defined behavior for some such grids. Anchors are isolated for clean object interpretation.

## D5. Use distinct anchor colors and bounded anchor count

**Original rationale:** Version 2.0.1 always emitted three distinct colors. Canonical examples contain two or three anchors, also in distinct colors.

**Choice:** Emit exactly two or three anchors, each with a different color from `{1,2,3,4,6,7,8,9}`. Scheduled profiles ensure colors 1 and 9 appear across a four-slot lesson while other colors remain keyed samples.

**Alternatives rejected:** One anchor, which cannot refute first-anchor-only behavior; duplicate anchor colors, which reduce visual separability without adding a needed semantic branch; arbitrary many anchors, which move away from canonical density and increase placement pressure.

**Probes:** Canonical-profile test, palette coverage across 96 draws per band, multiple-anchor witness 600/600, and first-anchor rival disagreement 60/60 where checked.

**Limits/failure modes:** Color roles are interchangeable for anchors under the rule, but explicit color-permutation metamorphisms were not separately enumerated. Numeric-rank shortcuts are weakened by broad color use but not exhaustively modeled.

## D6. Preserve canonical size/palette profiles while broadening defaults

**Original rationale:** The imported dimensions were 9..12 by 10..14 and did not reliably hit all canonical profiles. The canonical task uses 9..11 rows, 13..16 columns, and palette sizes 4 or 5.

**Choice:** Legal dimensions are 9..13 by 12..18. Scheduled canonical-two and canonical-three profiles draw exact canonical size/anchor-count combinations; the hollow-origin profile uses canonical sizes; hollow-broad uses difficulty-weighted ranges. Every band still permits every exact override.

**Alternatives rejected:** Replay canonical layouts; this teaches position shortcuts. Uniformly draw the full rectangle with no canonical component; the profile-floor gate and curriculum density can become weak. Narrow dimensions by difficulty; this breaks cross-band exact controls.

**Probes:** Profile-floor passes; task tests require at least one exact canonical size/palette profile per band and broad family/origin/palette coverage. Distribution, diversity, and grammar gates pass in the final battery.

**Limits/failure modes:** The schedule weights are design choices, not optimized by downstream training. Difficulty affects defaults, not a guaranteed monotone complexity order.

## D7. Guarantee teaching support under arbitrary one-query holdout

**Original rationale:** Unknown. The original generator declared no lesson schedule, rivals, witnesses, or identifiability hook.

**Initial choice and reversal:** The first 3.0.0 candidate used profiles `canonical_two`, `hollow_origin`, `canonical_three`, `broad`, so every four ordered demonstrations contained one guaranteed hollow-origin witness. Ordered production lessons passed 12/12, but the semantic smoke report found 2/60 ambiguous query rotations: holding out the only hollow pair could leave `use_first_mask_cell_as_origin` viable.

**Final choice:** Replace the fourth profile with `hollow_broad`, yielding two guaranteed hollow-origin slots per four-period. Every five consecutive pairs therefore contain at least two; after any single query holdout, four demonstrations retain at least one. Keep four demonstrations and one query, period four, and require the lesson hook to refute all declared rivals.

**Alternatives rejected:** Treat rotations as unsupported/diagnostic only. Production assembly could then be safe, but the small deterministic schedule made full rotation support inexpensive. Increase to five demonstrations, which raises lesson cost unnecessarily. Resample only failing lessons, which obscures schedule guarantees and replay.

**Probes:** A regression first failed on the old schedule at easy/start 8/query index 1. After the change: required-rotation semantic gate 60/60; large census 300/300 production and 1,500/1,500 rotations; all 12 band × schedule-start lessons and 60/60 rotations in period enumeration.

**Limits/failure modes:** Guarantees are against six declared rivals and the finite schedule contract. They do not prove identifiability against every hypothesis, and the 300-lesson census samples seeds rather than exhausting them.

## D8. Declare executable rivals and witnesses

**Original rationale:** None retained.

**Choice:** Declare marker-only, bounding-box-fill, first-anchor-only, keep-source, first-mask-cell-origin, and mask-color counterrules. Pair them with witnesses for multiple mask cells, nonrectangularity, multiple anchors, source removal, hollow origin, and anchor recoloring. `lesson_identifiable` checks labels with the Python mirror and rejects any declared rival surviving all demonstrations, whether or not it agrees on the query.

**Alternatives rejected:** Rely solely on generic identity/rotation shortcuts; they miss the canonical-fitting origin error. Declare names without executable outputs; that gives no reproducible evidence. Claim universal uniqueness from the finite set; not justified.

**Probes:** Every named rival differs on a focused generated input; semantic gate verifies 60 authoritative disagreements per witness/rival claim with no oracle errors; canonical ambiguity audit finds only the intended first-cell-origin shortcut among declared rivals.

**Limits/failure modes:** The Python mirror is supplemental. The canonical Racket rule remains label authority. Future plausible rivals should be added with exact witnesses and schedule analysis rather than inferred from a green finite census.

## D9. Retain small, source-bound evidence instead of prose-only claims

**Original rationale:** The selected task had no focused tests or counterexamples.

**Choice:** Add task-local portable tests, an input-only Racket replay file, and a full JSON counterexample bound to generator/rule hashes. Keep the initial lint and semantic-rotation failures as evidence of the repaired defects. Use shared `lesson-census` rather than inventing a duplicate private evaluator.

**Alternatives rejected:** Only describe the shortcut; future agents could not replay it. Add a task-local general census tool; shared tooling already records source manifests, exact lessons, rivals, and rotations.

**Limits/failure modes:** Check reports can be large. The return retains decisive reports and prunes duplicate staged runtimes before packaging; exact commands and exit states remain in `RESULTS.json`.
