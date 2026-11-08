# Working notes: fd277c567993

## Review c6a4656fd390973b

No prior return was used as a lead; imported associated notes were empty. Baseline generator SHA-256 `b1f45457da12057f5cf1ed4f767692c60391e8e8e18a68b816023fb98d5d2168` completed the battery with 7 green, 2 advisory, and 3 failed stages. Failures were missing rule/axis contract (`lint`), invalid declared degenerates (`defect_lint`), and unhonored advertised overrides (`override`). Profile support was 6/60 exact with 0/20 hard; no semantic contract was declared.

The repair replaced rejection-prone sampling with a connected-shape catalog and 4×4 stencil frame, pinned `RULE_HASH`, made every axis finite and observable, added an independent Python mirror plus rivals/witnesses, and weighted both canonical profiles. The public canonical pairs all fit `skip_occupied_query`, so occupied-query overwrite examples are a required teaching branch.

A first v3.0 schedule used one overwrite every four samples. A new leave-one-out test showed that rotating that sole witness into the query left the four demonstrations ambiguous in every band. The failing log is `checks/cyclic-rotation-red-v3.0.log`. v3.1.0 alternates clear/overwrite, after which 34 focused tests, the full 12-stage battery, and 300 production lessons pass.

Final generator SHA-256: `db1c46f995eb309590cc02c922a0833cfec36396750abbcd250813f2df0114af`.
Canonical authority was not edited. Main remaining limits: normalized connected shapes fit 3×3, offsets are nonnegative in a 4×4 frame, and the finite rival list is not universal induction proof.
## Current reviewer considerations

Source SHA-256: `db1c46f995eb309590cc02c922a0833cfec36396750abbcd250813f2df0114af`.

# Decisions for fd277c567993

## D1 — Preserve the canonical authority; pin its identity

**Choice.** Keep the selected Racket/base authority unchanged and declare `RULE_HASH = "1890aa619f98"`.

**Rationale.** The canonical outputs and rule smoke were already correct. The defects were in the Python input distribution and its metadata, so changing the oracle would have expanded risk without repairing the sampler contract.

**Alternatives rejected.** Editing the Racket rule to clip or skip occupied targets would contradict the selected authority. Replacing the base rule with the archival divergent source was also rejected; authority-sync evidence identifies the selected base as canonical.

**Probe.** Python `rule_mirror` matches all three canonical pairs; final `rule_smoke`, `racket_lint`, and `authority_sync` are green.

**Limit.** The hash binds this review to the current canonical source; a future authority change requires a new review rather than silently retaining the hash.

## D2 — Advertise only controls that are constructively realizable

**Choice.** Replace broad prose/singleton pseudo-axes with seven exact axes: `panel_h`, `panel_w`, `shape_size_ab`, `shape_size_c`, `n_diff`, `palette_kind`, and `offset_relation`. Every finite cross-product is legal, so `INCOMPATIBLE_OVERRIDE_COMBINATIONS` is empty.

**Original rationale.** Unknown. The imported v2.1.0 source advertised controls that were either ignored, band-restricted without declaration, or negative fixtures mixed into the valid domain.

**Alternatives rejected.** Keeping band-specific hidden restrictions would continue to make legal-looking overrides fail. Declaring hundreds of incompatibilities would be harder to audit than building a guaranteed-valid universe. Silently accepting unknown controls was rejected because it produces false provenance.

**Probe.** The final override stage exercises 336 joint cases and accepts all 30,240 draws. Task tests hit domain endpoints in every band and compare observed pixels with requested values.

**Failure modes and limits.** Domains are intentionally finite. Expanding one axis requires proving the whole joint support or explicitly declaring incompatibilities; merely changing the metadata is not sufficient.

## D3 — Use connected 3×3 shape catalogs and a 4×4 stencil frame

**Choice.** Enumerate all normalized four-connected polyominoes of size 3–6 inside 3×3, place them within a 4×4 relative frame, and select 1–4 additions from cells outside the before object.

**Rationale.** This makes geometry constructive: every advertised shape size, panel size, addition count, and clear/overwrite relation can be produced without retries. The extra frame row/column leaves enough lawful background cells for four additions even with a six-cell object.

**Alternatives rejected.** Random walks plus rejection made endpoint combinations fragile. Arbitrary masks risked disconnected objects and underspecified bounding boxes. A larger frame was unnecessary for the current canonical family and would reduce canonical-profile density.

**Probe.** `self_check`, strict-canonical checks, exhaustive override cases, and the independent parser verify connectedness, exact sizes/counts, target bounds, and relation type.

**Limits.** Shapes larger than six, negative offsets above/left of the object's bounding box, multiple objects, and additions outside the 4×4 frame are not sampled. This is the main remaining distribution restriction.

## D4 — Weight canonical profiles without narrowing the declared domain

**Choice.** Keep panel height 5–10 and width 5–9 legal, but heavily weight height/width 5. Use `separator_shared` to recreate canonical palette size 4 and `distinct` for palette size 5.

**Rationale.** The baseline hard band had 0/20 canonical-profile hits. A training generator should retain broader variation while supplying canonical-scale examples in every band.

**Alternatives rejected.** Hard-coding all samples to 5×5 panels would pass the profile gate but destroy useful size variation. Treating separator-shared color as invalid would erase one canonical palette profile.

**Probe.** Final profile floor has 32/60 exact hits—11/20 easy, 10/20 medium, 11/20 hard—and accepts all three canonical inputs. A task test finds both `(5,17,4)` and `(5,17,5)` profiles in every band.

**Limits.** Weighting is deterministic through `GenCtx` but is not a calibrated estimate of a real-world task distribution.

## D5 — Make overwrite semantics unavoidable at lesson level

**Choice.** Alternate `clear` and `overwrite` by sample-index parity when no explicit override is supplied. Explicit `offset_relation` still overrides the schedule.

**Rationale.** All three canonical pairs fit the wrong `skip_occupied_query` rule. The first repair used one overwrite per four samples, which made fixed-position four-demo lessons identifiable but failed when that sole witness was held out as the query. Alternation leaves at least one clear and one overwrite example in the four demonstrations after any one pair is removed from five consecutive samples.

**Alternatives rejected.** Pure random sampling gives only probabilistic lesson coverage. One overwrite per four was insufficient under pair rotation. Making every sample overwrite would refute the shortcut but remove the clear branch and distort the task.

**Probe.** `checks/cyclic-rotation-red-v3.0.log` records the failing leave-one-out test in all three bands. The final 34-test suite checks eight consecutive starts, all five possible query choices, and all bands. The semantic gate sees 289 overwrite witnesses in 600 draws.

**Limits.** This schedule assumes lesson assembly uses nearby sample indices. The 300-lesson production census confirms the actual sampler, while the leave-one-out regression deliberately covers a stronger augmentation policy.

## D6 — Treat semantics as executable data

**Choice.** Add a strict parser, pure Python `rule_mirror`, four rival functions, four witness predicates, explicit witness-to-rival claims, a canonical-shortcut declaration, and `lesson_identifiable`.

**Rationale.** Surface diversity does not ensure that examples teach the intended transformation. The public canonical set's overwrite ambiguity made this concrete rather than hypothetical.

**Alternatives rejected.** Prose-only invariants cannot be gated. Comparing the generator to itself would be circular, so tests use `workspace/reference_probe.py` as an independent parser/mirror. A single “not identity” rival would miss the observed shortcut.

**Probe.** Final semantic gate: 600/600 strict, 3/3 canonical accepted, four witness claims verified, 12/12 lessons identifiable. Large census: 300/300 identifiable over 1,500 unique inputs.

**Limits.** The rival set is finite. It covers copying the query, copying the after panel, absolute rather than translated 8 positions, and skipping occupied query cells; other wrong programs may remain.

## D7 — Keep validation diagnostic and immutable

**Choice.** `self_check` accepts malformed input and returns reasons instead of raising. Grid validation excludes booleans even though Python treats them as integers. Rule/mirror functions avoid mutating their arguments.

**Rationale.** Shared gates and future agents need stable diagnostics on malformed fixtures; permissive Python type behavior can otherwise admit semantically invalid grids.

**Alternatives rejected.** Assertions/exceptions in `self_check` make defect triage noisy. Coercing values would hide data corruption.

**Probe.** Task tests cover malformed grids, boolean outputs, deterministic replay, and input immutability. Final defect lint is clean.

## D8 — Build reusable independent probes

**Choice.** Add `workspace/reference_probe.py` for canonical loading, independent analysis, and mirror execution; add `workspace/audit_contract_probe.py` for exact audit replay.

**Rationale.** Future reviewers should be able to distinguish a generator bug from a test that merely duplicates the generator's own logic. Audit claims also need exact seeds/overrides rather than prose recollection.

**Alternatives rejected.** Inline one-off commands are hard to replay and produced weaker first-pass audit JSON. Shared-repository edits were out of scope.

**Probe.** Both scripts are imported/executed by retained tests or verification commands and are included in the task-local delta.
