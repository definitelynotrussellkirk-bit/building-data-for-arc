# Working notes — 06da3d8c94fe

## 2026-10-11/12 — assignment `review-a6a14d66a9d41a60`

Baseline generator version `3.1.0`, SHA-256 `42dadaad6a7c89f0a698adab0a46aa8694bbe82d5608a791c02d6f7dfbfbb175`; final version `4.0.0`, SHA-256 `5f22a70fcdb2d1eda1c899c5f4d3a3886685523b8da19064e27814dc6c4dd6ca`. Canonical Racket rule hash `b01bd9f14dbe` is unchanged. Imported associated notes were empty, so no prior return was used as evidence.

## Intended rule

The input has five equal-width panels separated by four full-height color-5 columns. Panels 1 and 2 are interpreted as nonzero masks. Panel 3 equals exactly one of their union, intersection, or XOR masks. Infer that unique operation and apply it to panels 4 and 5; output occupied cells as color 2 and all other cells as 0.

## Baseline findings

The baseline correctly moved away from an older wrong-task motif sampler, but its comments and Python mirror asserted a nonexistent “no match → XOR” authority fallback. The selected canonical authority instead requires exactly one matching operation and errors when none matches. Accordingly, the advertised `fallback_xor` texture generated invalid demonstrations. `identical_query` could make the query uninformative or empty, exact axes were band-restricted despite broader declarations, unknown/scalar controls were not validated, `RULE_HASH` was missing, the canonical 4×24 / `{0,2,5}` profile was never sampled, and no executable semantic lesson contract existed.

The strongest canonical shortcut is `never_union`: the two canonical demonstrations exercise XOR and intersection, so a solver can assume those exhaust the task and substitute XOR whenever a union demonstration appears. It fits all canonical demonstrations and changes the canonical query. The exact retained counterexample is `counterexamples/never_union-shortcut.json`.

## Current design

- Removed production textures and every malformed/fallback branch. A valid grid always has exactly one inferred operation.
- Exposed only three exact controls: `panel_w` 3–5, `grid_h` 4–10, and `kind` in `{union, intersection, xor}`. Unknown controls, bools, non-integral scalars, negative sample indices, and unknown difficulty values reject loudly.
- Constructed both demonstration and query pairs with overlap, left-only, and right-only evidence, making union, intersection, and XOR pairwise distinct and non-empty.
- Even sample indices use the canonical 4×24, three-color profile; odd indices explore the full size domain with difficulty-weighted defaults. Exact overrides remain legal in every band.
- `kind = sample_index mod 3`; with `EXAMPLES_NEEDED = 5`, every six-example lesson contains each operation exactly twice. Every cyclic query holdout therefore leaves at least one example of every operation in the demonstrations.
- Added a pure Python mirror, strict validator, exact observer, three branch witnesses, four executable rivals (`always_union`, `always_intersection`, `always_xor`, `never_union`), and `lesson_identifiable`.
- Added an independent oracle (`workspace/reference_probe.py`), a reusable shortcut/rotation probe (`workspace/probe_shortcuts.py`), 135 portable regression tests, and a source-bound exact counterexample.

## Final evidence

The complete after battery, run with required query-rotation identifiability, is 12/12 green on the final generator hash: `checks/after/result.json`. Portable selected task tests are 135/135: `checks/task-tests/result.json`. Profile support is 30/60 exact canonical hits: 9/20 easy, 13/20 medium, and 8/20 hard in the final battery. The override matrix accepted 5,850/5,850 draws with zero findings. Rule smoke checked 120/120 Python–Racket cases. The semantic smoke accepted 600/600 strict grids, all canonical pairs, all branch witnesses and rival claims, 12/12 lessons, and 72/72 query rotations.

The larger production census materialized 300 lessons / 1,800 labeled pairs, with 1,429 unique inputs, zero materialization/scoring errors, zero production ambiguities, and zero ambiguities across 1,800 query rotations. The final visible-only solve passed 5/5 examples on its first revision and honestly records earlier rule exposure; the earlier blind task passed 3/3 before any source inspection.

## Limits and open findings

The representation retains fixed divider color 5 and output color 2; panel input colors vary only on broad-profile draws. The domain is bounded to heights 4–10 and panel widths 3–5. Structured canonical-profile pairs use simple connected length-four bars; broader draws supply denser random masks. Identifiability claims are finite and only cover the declared rivals plus the explicit `never_union` canonical shortcut, not every possible program. Training approval remains a maintainer decision; this review does not change catalog approval.

## Decision reversals

The prior `fallback_xor` choice was removed because it contradicted the selected authority rather than exercising a lawful edge case. The prior `identical_query` negative texture was removed from production because it reduced query discrimination. The prior three-random-demo policy was replaced by a deterministic six-position operation schedule so complete lessons and every query rotation have guaranteed branch support.
## Current reviewer considerations

Source SHA-256: `5f22a70fcdb2d1eda1c899c5f4d3a3886685523b8da19064e27814dc6c4dd6ca`.

# Decisions — generator `06da3d8c94fe`

All selected-source decisions below bind to final generator SHA-256 `5f22a70fcdb2d1eda1c899c5f4d3a3886685523b8da19064e27814dc6c4dd6ca`, version `4.0.0`, and unchanged canonical rule hash `b01bd9f14dbe`. Baseline SHA-256 was `42dadaad6a7c89f0a698adab0a46aa8694bbe82d5608a791c02d6f7dfbfbb175`. Associated notes were empty; the only known baseline rationale is what its source comments stated.

## D1 — Preserve and pin the selected Racket authority

**Choice.** Keep the canonical rule and canonical examples unchanged; set `RULE_HASH = "b01bd9f14dbe"` and require exact Python–Racket parity on lawful inputs.

**Prior choice / rationale.** The baseline omitted `RULE_HASH` and described a “no matching operation → XOR” fallback. That description came from its own mirror/comments, not from the selected authority.

**Rationale.** Canonical examples consistently express a five-panel operation-inference task. The defect was the generator’s domain description and sampler, not the authority. Direct inspection and `arcpuzzles apply` show that malformed no-match demonstrations are not lawful fallback cases.

**Alternatives rejected.** Changing Racket to accept malformed demonstrations would redefine a sound canonical task around a sampler bug. Keeping an approximate mirror would conceal authority drift.

**Probes.** Full battery `authority_sync` and `rule_smoke`; 120/120 mirror cases; canonical tests; exact Racket counterexample output in `checks/shortcut-racket/racket.json`.

**Limits.** The Python mirror is support code, not authority. Training approval remains unchanged.

## D2 — Remove malformed and non-teaching production textures

**Choice.** Delete the public `texture` axis, `fallback_xor`, and `identical_query` production branches. Every generated board must identify exactly one operation and give three distinct, non-empty query candidates.

**Prior choice / rationale.** Baseline comments called the two textures “degenerates”: one deliberately made panel 3 match no operation; the other copied/recolored panel 4 into panel 5. The apparent aim was edge-case breadth.

**Rationale.** `fallback_xor` contradicted the authority and failed the generator’s own validator. `identical_query` could erase the very distinction the learner is supposed to apply. Neither is a lawful positive training axis.

**Alternatives rejected.** Preserving them as ordinary exact overrides would advertise invalid or uninformative examples. Keeping them as silently ignored aliases would perpetuate a false contract. They can still be constructed externally as explicitly labeled negative tests if needed.

**Probes.** Baseline override report; TDD failures in `checks/tdd-red.log`; final invalid-control tests; lint and defect lint with zero findings.

**Limits.** The repaired sampler intentionally does not train error behavior for malformed demonstrations.

## D3 — Make the public control surface small, exact, observable, and strict

**Choice.** Expose only `panel_w` 3–5, `grid_h` 4–10, and `kind` in `{union, intersection, xor}`. Reject unknown axes, bools, non-integral scalars, negative sample indices, and unknown difficulty values. Recover all three controls from returned pixels with `observe_overrides`.

**Prior choice / rationale.** The baseline advertised the same size/kind controls plus `texture`, but band-specific draws made part of each declared range unreachable and it accepted weakly typed/unknown input paths.

**Rationale.** An exact axis is useful only when every legal value works across the stated domain and downstream tooling can observe the realized value. Strict request validation turns typos and coercions into local errors rather than silent distribution changes.

**Alternatives rejected.** Band-specific legal ranges were rejected because they make the same exact request inconsistently valid. A larger speculative surface was rejected because no additional axis was needed to teach the rule.

**Probes.** 5,850/5,850 accepted override draws with zero findings; 135 task tests, including boundaries, combinations, unknown controls, scalar types, replay, and observer equality.

**Limits.** Panel colors and profile type are intentional sampler choices, not exact public axes.

## D4 — Construct operation-separating mask pairs instead of relying on rejection luck

**Choice.** Every demonstration pair and query pair contains overlap, left-only, and right-only occupied cells. Canonical-profile draws use connected subset/superset bars; broad draws seed the three required states and then add random occupancy.

**Prior choice / rationale.** The baseline sampled independent masks and retried until the requested demonstration operation was unique and the selected query output was non-empty.

**Rationale.** The three witness states make union, intersection, and XOR pairwise distinct by construction. Applying the same requirement to panels 4–5 means the query answer genuinely depends on the inferred operation. Construction is easier to reason about and test than probabilistic rejection.

**Alternatives rejected.** Pure rejection sampling can become slow or distributionally opaque, especially at small sizes/densities. Only constraining the demonstration would leave ambiguous queries. Fully deterministic fixed masks would reduce diversity.

**Probes.** `self_check`; independent oracle tests; all-operation candidate-distinctness tests; rule smoke; diversity and distribution gates.

**Limits.** Canonical-profile geometry is deliberately simple. Broad-profile masks provide the less regular cases.

## D5 — Guarantee branch coverage at the complete-lesson level

**Choice.** Set `kind = KINDS[sample_index % 3]` by default and `EXAMPLES_NEEDED = 5`. A materialized lesson has six labeled pairs, so every operation occurs exactly twice. Declare the six-position profile/kind schedule explicitly.

**Prior choice / rationale.** The baseline drew kind randomly and said “3 demos with 3 different ops,” but no mechanism guaranteed that statement.

**Rationale.** The strongest canonical shortcut, `never_union`, survives because the canonical demonstrations omit union. Branch coverage must be guaranteed for each assembled lesson, not merely likely over the corpus. Two occurrences per operation also make every cyclic query holdout leave one demonstration of each branch.

**Alternatives rejected.** Three random demonstrations have a substantial chance of missing or duplicating operations. A three-position deterministic lesson would cover all operations in production order but fail some arbitrary query rotations because holding one branch out removes it from demonstrations. Rejection-resampling complete lessons would be more complex than a direct schedule.

**Probes.** `workspace/probe_shortcuts.py`; 18/18 cyclic holdouts across representative windows; required semantic-gate rotations 72/72; 1,800/1,800 census rotations.

**Limits.** The guarantee applies to consecutive sampler indices and one query per six-pair lesson. A downstream assembler that skips/reorders draws outside this contract must recheck identifiability.

## D6 — Alternate canonical-profile anchors with broader examples

**Choice.** Even sample indices default to height 4, panel width 4, and palette `{0,2,5}` (whole input shape 4×24); odd indices draw height 4–10 and panel width 3–5 with difficulty-weighted options and varied panel colors.

**Prior choice / rationale.** The baseline used height 5–8 and panel width 3–5, with difficulty-specific subranges; it never emitted the canonical 4×24 profile.

**Rationale.** The strict profile floor requires recurrent support near canonical geometry/palette. Alternating profiles gives a deterministic minimum while retaining size/color diversity. Difficulty changes broad defaults without narrowing exact legality.

**Alternatives rejected.** Sampling canonical geometry only probabilistically could miss a small acceptance window. Making every draw canonical would overfit representation and lose useful breadth. Treating profile as an exact axis would expose an unnecessary internal curriculum control.

**Probes.** Profile floor: 30/60 exact hits, 10/20 in each band; diversity and distribution gates; exact-size tests.

**Limits.** Half of default draws are canonical-profile by design, so the distribution is not uniform over sizes.

## D7 — Encode the strongest plausible shortcut as executable evidence

**Choice.** Declare `never_union` alongside fixed-operation rivals; retain a lawful generated union counterexample and a reusable shortcut probe.

**Prior choice / rationale.** The baseline discussed “always union/xor” informally but had no executable semantic declarations and did not identify the omission-specific canonical shortcut.

**Rationale.** `never_union` fits both canonical demonstrations and changes the canonical query, making it more targeted than an always-fixed operation. A named callable lets the semantic gate, census, task tests, and future agents score the same hypothesis consistently.

**Alternatives rejected.** A prose-only warning is not regression-proof. Treating “always XOR” as the strongest rival misses that a solver can correctly handle intersection while still assuming union is impossible.

**Probes.** `checks/shortcut-probe.json`; `counterexamples/never_union-shortcut.json`; Racket application evidence; test-first red/green logs; census and semantic gate.

**Limits.** Four declared rivals are not an exhaustive hypothesis class.

## D8 — Separate independent oracle logic from production implementation

**Choice.** Keep `rule_mirror` in the generator for shared tooling, and add `workspace/reference_probe.py` with separately written panel parsing, operation inference, and outputs for tests/probes.

**Prior choice / rationale.** The baseline had only `_mirror`, which duplicated its own mistaken fallback interpretation.

**Rationale.** Tests that call the same helper as production can prove internal consistency while preserving the same bug. The independent oracle catches parser/inference/rival mistakes and is especially important for the retained counterexample.

**Alternatives rejected.** Comparing only against canonical pairs gives too few structures. Importing private runner functions would make tests nonportable and conflate Python support code with Racket authority.

**Probes.** 135 portable tests; counterexample checks; Racket rule smoke and direct `apply` evidence.

**Limits.** Independence is by separate implementation, not formal verification.

## D9 — Validate the whole lawful manifold, not only the selected answer

**Choice.** `self_check` verifies shape, dividers, palette legality, literal panel-3 mask, unique demonstration operation, pairwise-distinct/non-empty candidates for both pairs, and declared dimensions. `strict_canonical_like` uses the same lawful manifold.

**Prior choice / rationale.** The baseline checked shape/dividers, unique demo match, and only the effective query’s non-emptiness.

**Rationale.** A query where two wrong operations coincide can still have a correct label but teach a shortcut. Validating all candidate operations makes semantic discrimination a per-grid invariant rather than a corpus-level hope.

**Alternatives rejected.** A loose canonical validator plus stricter production validator was unnecessary because all canonical inputs satisfy the full lawful contract. Checking only output non-emptiness would not establish operation identifiability.

**Probes.** Canonical acceptance; mutation tests; self-check stage; semantic gate; lesson census.

**Limits.** It validates structural/declared semantics, not every possible human interpretation of the task.

## D10 — Preserve deterministic replay and fresh mutable returns

**Choice.** Use only keyed `gen_ctx` draws/local RNGs, validate seed/index types, and return newly allocated grids. Version changed to `4.0.0` because draw semantics changed materially.

**Prior choice / rationale.** The baseline already used `gen_ctx`, but request validation and the final construction/schedule differed.

**Rationale.** Every evidence item, exact counterexample, lesson window, and source-bound report must be replayable. Freshness prevents a caller’s mutation from contaminating later draws.

**Alternatives rejected.** Module-global RNG, caches, or silent request normalization would make replay and parallel generation unreliable.

**Probes.** Determinism/freshness/global-RNG tests; A-B-A replays in shared checks; source hashes in every retained report.

**Limits.** Changing version, draw labels, or draw order intentionally changes generated instances and requires new evidence.

## D11 — Keep focused tests and a future-agent diagnostic tool

**Choice.** Add 135 portable tests, `workspace/probe_shortcuts.py`, `workspace/reference_probe.py`, and the exact counterexample JSON.

**Rationale.** The shared battery proves integration properties but cannot encode all task-specific decisions. The probe gives future reviewers a cheap answer to the assignment’s central question and audits every cyclic holdout without reconstructing the reasoning.

**Alternatives rejected.** Relying only on the battery would leave the canonical shortcut implicit. Relying only on task tests would omit Racket execution, profile/override matrices, and production lesson materialization.

**Probes.** `checks/task-tests/result.json` (135/135), `checks/shortcut-probe.json`, and full battery `checks/after/result.json` (12/12).

**Limits.** The probe is finite and task-specific; it should not be promoted as a universal shortcut detector without the declarative branch interface proposed in feedback F1.
