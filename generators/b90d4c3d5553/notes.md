# Working notes — b90d4c3d5553

## 2026-09-27 — assignment review-76f88ee4a481ad51

Reviewer: GPT-6 Astra Pro. Imported generator 1.3.0; revised sampler 2.0.0. Canonical and archival rule bytes, rule hash `a9a48a6b2948`, shared check tools and admission metadata are unchanged.

The initial full battery failed canonical self-check and override consistency. Both tripods were hard-coded upright and the source always left of the target. All three canonical inputs were rejected. Easy/medium counts ignored overrides; declared domains disagreed with accepted band domains. The motif excluded self-mirrors, and the validator filtered out the very cases it purported to check.

Implemented independently oriented frames; constructive disjoint placement; exact finite-orbit pair/noise/axis sampling; exterior distractors; strict pixel validation; observed overrides; and a declared `self_mirror` witness against a `distinct_pairs_only` rival. A sparse/broad mixture uses a 50/50 profile draw and keeps every domain available in each band. The initial 1/3 sparse mixture produced a profile-floor advisory; retained evidence records that iteration rather than hiding it. The mixture is not claimed optimal for a trained model.

The exact hand witness is `workspace/reference_probe.py:witness_input()`. Its intended and distinct-pairs outputs differ only at (4,10), using zero-based row,column. A default generated example exists at seed 0/index 0 with four axis markers. Final crossed sampling observed axis counterexamples in 3,284/8,000 draws and all 64 orientation pairs. The old panel had none and one orientation pair.

111 task tests pass with one Racket-dependent skip. The repository root suite separately has 96 passes and 28 Racket-dependent skips. Independent stress covers 68,160 forced combinations with no errors. These are supplementary checks, not Racket execution. The reference parity command deliberately exits nonzero when the runtime is missing. Package installation and direct runtime download attempts failed in the review environment. The source-layout reference-probe error and early distinct-cardinality aggregation mistake are documented in the return reports and corrected in the delivered tools.

Remaining limits: fixed role colors, unit cardinal bases, at least one off-axis pair, full nonoverlapping padded neighborhoods, no clipped/overwritten targets, bounded counts, correlated cross-band draws, no model-training outcome, and no per-lesson witness-coverage guarantee. Obtain real canonical parity and a green required reference battery before promotion. The runtime-present path of the new parity helper has not executed here. See root return reports for exact before/after stage results and source hashes.
## Current reviewer considerations

Source SHA-256: `a4f68c547c944080dd10ae786c25d4b64f297311d373522ba4cfb6501a62046c`.

# Decisions — b90d4c3d5553

Review: GPT-6 Astra Pro; assignment `review-76f88ee4a481ad51`.
The original notes and associated evidence contain no substantive design history. “Original rationale” below means an actual source comment or an explicitly identified inference, not a reconstructed conversation. The selected implementation is version 2.0.0. All choices are task-local; shared checkers and admission records are unchanged.

## 1. Preserve the executable rule and color roles

**Original rationale:** the source identifies two coordinate tripods and mirror-partner filtering. The canonical program explicitly uses colors 2/3/4, 5/6/7 and 8 and the predicate `(u,v) -> (-u,v)` within radius three. Its three supplied examples agree with that reading. There is no evidence supporting a different rule.

**Choice:** preserve canonical and archival Racket bytes and rule hash `a9a48a6b2948`. Keep background 0 and the seven literal nonzero roles. `generate` returns an input only. The Python geometry oracle and semantic rival are supplemental checking tools, not a label-production fallback. No approval change.

**Alternatives:** changing the rule to distinct off-axis pairs would agree with the examples but contradict the executable membership predicate at u=0. Color-permutation augmentation would require remapping the literal-role rule and would be a different distribution/authority contract; not done.

**Probe and limitation:** independent geometry matches all three retained outputs. A hand witness and generated self-mirror cases separate the rival. Actual Racket execution could not run because the runtime is absent and attempted downloads failed. One canonical code comment calls the reflection “across x axis”; the expression negates u, which is reflection across the local y-axis. Documentation explains this; the comment was not used to justify changing authority bytes.

## 2. Independently orient the source and target

**Original rationale:** unknown. `_put_frame`, `_global` and `_find_frame` all hard-code east/south, despite the canonical examples using different source/target bases.

**Choice:** eight cardinal orthogonal bases per frame, independently sampled with keyed draws. Explicit overrides `source_orientation` and `target_orientation` each span 0..7. A unique colored origin and its two adjacent role markers determine coordinates. No color-independent “left object is source” inference.

**Alternatives:** rotating the entire old image would tie the two frames together and never teach a relative basis change. Four rotations omit reflected bases. Both rejected in favor of the complete 8 x 8 product.

**Probes:** all 64 forced pairs, all 64 seen in the unforced audit, global D4 metamorphic tests, and all three canonical inputs accepted. The small legacy alias lint warns on its cohort; a complete Cartesian intervention proves these axes are not aliases. Do not collapse them to appease that warning.

**Limits:** unit, perpendicular, cardinal bases only. Sheared, scaled, nonadjacent or duplicate frames are not supported. Global transforms are checked semantically; not every transformed rectangle is an advertised h/w override.

## 3. Dimensions and frame placement

**Original rationale:** version 1.3.0 comments say size/position variation was intended to remove a formerly fixed 12x18 shape. The original nevertheless forced source-left/target-right. A second comment explains separating the target to avoid silently losing noise under a paint guard. Metadata said h=10..16 and w=14..24, while individual bands accepted smaller inconsistent domains.

**Choice:** h=10..24 and w=14..24 in every band. Choose feasible source centers and then a target from the exact finite set whose Chebyshev center distance is at least seven. Both radius-three squares fit and are disjoint. All feasible relative directions are available; either frame can be left or above. Geometry tuples are cached in bounded LRU caches; generated grids and randomness are never cached.

**Alternatives:** rejection placement with a retry cap can fail or bias small canvases; fixed halves retain a positional shortcut; allowing square overlap complicates copy collisions and can obscure the selected semantic distinction. The finite construction avoids these issues.

**Probes:** all 165 sizes crossed with all 64 orientation pairs at maximum motif/distractor counts (10,560 cases); smallest-canvas count sweep; cross-process hash-seed repeatability and cache-clear/call-order tests. 164 of the 165 shapes occurred in the final unforced panel, and all 165 were explicitly exercised. Sampling is source-uniform followed by conditional target-uniform, NOT uniform over every ordered center pair.

**Limits:** no clipped or overlapping frames. Minimum area is 140, and two disjoint 7x7 squares leave 42 exterior cells, more than the four required distractors. Full margins and disjointness mean every selected source marker maps to free in-bounds target background. Boundary-adjacent copied pixels are allowed.

## 4. Exact pairs, noise and axis markers

**Original rationale:** the old comment requires at least one pair so something copies, and says noise should have no partner. The implementation samples u from nonzero values and caps both rejection loops at 200. Easy/default counts bypass override draws. A final paint guard silently skips collisions.

**Choice:** explicit domains pairs=1..6, unpaired noise=0..4, axis=0..5 in every band. Enumerate positive-u reflection orbits. Sample pair orbits without replacement; select noise from different remaining orbits, choosing a free side; separately sample the five free u=0 cells. The free side (-1,0) opposite color 3 is valid singleton noise. Counts are exact and recoverable from pixels. Unexpected constructive collisions raise rather than shorten the motif.

**Alternatives:** keep noise >=1 in the validator, exclude axis cells, or preserve a capped loop. These would retain contradictory override promises or never falsify the canonical-fitting distinct-pair rival. Allowing zero off-axis pairs/all-axis-only/no-copy inputs is lawful under a broad reading of the rule but deferred to keep the established nontrivial-pair task family.

**Probes:** all 57,600 count/orientation products on 10x14 (6 pair counts x 5 noise counts x 6 axis counts x 5 distractor counts x 64 bases); assert the independent observed counts equal requested counts and the changed-cell count equals `2*n_pairs+n_axis`. Five is the exact number of free u=0 positions within [-3,3] after reserving origin and +v marker. There are twenty pairable off-axis orbits, so even six pairs leave ample distinct orbits for four noise cells.

**Limits:** these checks are Python-side, not Racket authority evidence; the staged runtime probe is retained for completion. Max counts remain a deliberate bounded curriculum, not a claim to generate every legal rule input.

## 5. Exterior distractors

**Original rationale:** the old invariant excludes them, while the old validator silently ignores all radius violations before checking radius. No other rationale retained.

**Choice:** 0..4 color-8 distractors outside both padded squares, preserved in the input. When there are at least two and a suitable pair exists, preferentially plant an exterior mirrored pair. This can distinguish local radius-limited selection from unbounded symmetry filtering. Exact distractor count is observed independently.

**Alternatives:** no distractors leaves radius selection unchallenged; arbitrary grid noise could corrupt tripods or target destinations. Controlled exterior placement preserves interpretability without such corruption.

**Probes:** exact-count stress and an unbounded rival. The latter is scored only where every target projection stays in bounds: final audit 1,200 disagreements among 6,872 defined cases; 1,128 undefined projections are separately counted, NOT silently counted as wins. A distant marker is not by itself a guarantee that a total rival output differs.

## 6. Sparse/broad mixture and difficulty

**Original rationale:** easy uses 2 pairs/1 noise, default and medium use 3/2, hard uses 4..5/2..3. h/w also change with band. Historical optimization evidence is absent.

**Choice:** a keyed 50/50 choice between a sparse core and broad component. Core count choices retain the full domain and add 100 extra copies of each anchor: h=12, w=18, pairs=2, noise=1, axis=0, distractors=0. It favors a canonical-sized/density neighborhood but does not replay canonical layouts or constrain orientations. Broad uses the full domains; easy adds weight to lower pair/noise counts and hard to higher counts. Explicit overrides always win unchanged.

**Iteration:** the first candidate used one-third core/two-thirds broad. The profile check reported 12/60 matches (20%, advisory) while semantic branches were covered. The final choice is a conservative equal allocation to sparse and broader inputs, not a seed-specific repair and not an experimentally optimized training curriculum. The earlier candidate and receipts remain under `checks/after/`.

**Alternatives:** uniform-only rich sampling risks making small canonical-like examples atypical; mostly canonical-shaped samples retain shortcuts; strict count ordering by difficulty conflicts with broad override support and informative easy counterexamples. No need to pretend difficulty monotonically orders every generated instance.

**Limits:** mixture weights and anchors are design choices. No model was trained, no downstream accuracy gain measured, and no per-lesson witness-coverage guarantee was added. `None` and medium are intentionally equivalent; crossed band samples can coincide. The audit reports union-distinct input counts and explicitly says its 8,000 draws are correlated across bands.

## 7. Validation, metadata and bounded tools

**Original rationale:** validate a recognizable motif. The original only finds upright tripods, ignores extra role colors and unexpected palette values, and discards axis/out-of-radius cells before testing those cases. It has no pixel-level override observer and ignores unknown override names.

**Choice:** strict palette, exactly one of each frame color, orthogonal frame recognition, margins/separation, empty initial target neighborhood, and explicit observed-count limits. Reject malformed grids diagnostically. Unknown axes, booleans and noninteger values reject rather than disappear; a None override retains GenCtx's established “absent” meaning. Add exact `observe_overrides` and semantic witness/rival hooks.

**Probes:** destructive mutations, canonical acceptance, all count products, invalid override tests, repository override gate, and semantic witness consistency. The new hooks intentionally make the semantic gate FAIL when it cannot authoritatively check the claimed disagreement: no “green” from missing Racket.

**Tools built:** independent geometry/reference probe with real-Racket-only parity mode; Cartesian stress tool; one-command qualification driver with command/exit/time receipts and separate task/root suites. Original early audit cardinalities summed band-level distinct counts; the final audit fixes this to set unions, and final before/after reports use that corrected code. A first source-layout Racket attempt failed importing `scripts`; the final tool checks runtime availability first and stages via `prepare_runtime`. Its runtime-present path still needs execution.

**Review boundary:** author self-review, not an independent second reviewer. No optional unrelated-generator audit was drawn. No changes outside the assigned task were made to solve warning or dependency failures.
