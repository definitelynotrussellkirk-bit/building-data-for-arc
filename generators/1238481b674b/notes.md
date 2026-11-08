# Current notes: 1238481b674b

## Intended rule and input grammar

The input is a rectangular ARC grid containing only orange `7` and exactly four gray `5` cells. Three gray cells occupy three corners of one axis-aligned square bounding box; the fourth is a strictly interior distractor. The one absent bbox corner selects a triangular outline: paint `8` on the two bbox sides incident to that corner and on the diagonal joining the other two corners. Paint only former `7` cells, preserving all four gray markers.

The selected Racket authority remains unchanged at rule hash `cbabe9d66374`. On final generator SHA-256 `907a296f355d90e454437e2c4e74b50d8d40f0541194fff99d3b847b2503a311`, rule smoke and authority synchronization pass. The archival `raw_code` carrier remains role-stated as divergent text but has execution parity; no shared-source repair is required by this review.

## Distribution and teaching choices

The four-slot schedule retains canonical anchors, translated clockwise/counterclockwise distractors, and expanded near-missing cases. Valid-output generation was intentionally left unchanged. The final profile-floor probe found 17 exact canonical-profile hits in 60 draws: easy 4/20, medium 5/20, hard 8/20, with zero crashes.

`CANONICAL_SHORTCUTS` now contains the strongest observed canonical-fitting rival: `nearest_distractor_corner`. It chooses the bbox corner nearest the interior gray marker as the triangle apex. This fits all 4 labeled canonical pairs because every canonical distractor is near the true missing corner, but it fails when a clockwise/counterclockwise distractor is closer to another corner. The generator emits such cases, and witness `distractor_is_not_orientation_cue` plus the four-slot lesson schedule refute the rival.

The prior declarations `erase_interior_gray` and `solid_triangle` remain useful semantic rivals but were removed from `CANONICAL_SHORTCUTS`: they matched 0/4 and 1/4 canonical pairs respectively and therefore were false canonical-shortcut claims.

## API and validation decision

`generate` and `schedule_profile` now require exact Python integers for `seed` and `sample_index`, reject `bool`, float, string, and `None`, and reject negative sample indices. This reverses the previous coercive behavior (`int(sample_index)`) that produced 33 strict-scalar warnings. Valid calls and generated grids are unchanged, so `VERSION` remains `3.0.0` to avoid needless deterministic resampling.

## Verification and retained evidence

- Before source `d1a81b757d30fa61f1a87b2f2c8959d16156985e3a5ccfaf32c022cc66860cbd`: battery 10/12 green; `defect_lint` and `semantic_gate` failed.
- Final source `907a296f355d90e454437e2c4e74b50d8d40f0541194fff99d3b847b2503a311`: battery 12/12 green.
- Focused portable regressions: 24/24 passed under the protected-Racket wrapper.
- Lesson census: 300/300 materialized, 1,500 query rotations, 516 unique inputs, zero declared-rival ambiguities or scoring/materialization errors.
- Exact shortcut counterexample: `counterexamples/review-cf9c41ca8d4a7c2c/nearest-distractor-corner.json`; protected Racket and the Python mirror agree and both differ from the rival.

## Known limitation / open maintainer action

The immutable retained fixture `tests/test_generator_1238481b674b.py` still imports legacy `scripts.*` modules and derives canonical data from a fixed parent depth. The required staged `task_tests` command therefore stops in preflight before pytest (exit code 2). Packet rules prohibit rewriting that frozen fixture. New tests live in `tests/test_review_repairs.py` and pass directly, but aggregate staged task-test completion remains blocked until the maintainer migrates the retained fixture.

## Historical-note reversal

Associated note `GNOTE-003731` described a checkout with shared-source divergence and required an intake-side authority patch. Independent before and after batteries in this packet both passed `authority_sync`; the final report records exact synchronization plus execution parity. Treat that older limitation as superseded for the current source snapshot, while retaining it as historical provenance.
## Current reviewer considerations

Source SHA-256: `907a296f355d90e454437e2c4e74b50d8d40f0541194fff99d3b847b2503a311`.

# Decisions for 1238481b674b

## D1 — Preserve the input/output law and Racket authority

**Choice:** Keep the orange/gray grammar, missing-corner triangle rule, all valid generated outputs, and Racket rule hash `cbabe9d66374` unchanged.

**Original rationale:** The canonical data and current generator already agree on four gray cells, three square corners plus one interior distractor, with the missing corner selecting two incident sides and the opposite diagonal.

**Alternatives considered:** Rewrite the Racket rule; simplify to three markers; treat the distractor as removable noise. These were rejected because authority sync/rule smoke already passed and the simpler grammars erase a canonical teaching requirement.

**Probes/evidence:** All four canonical pairs pass `self_check`, strict-canonical checks, Python mirror, and protected-Racket execution. Final battery authority stages are green.

**Failure modes/limits:** This decision covers the declared generator domain, not malformed grids with other palettes or marker counts.

## D2 — Reject coercible call identities

**Choice:** Require `type(seed) is int`, `type(sample_index) is int`, and `sample_index >= 0` in both `generate` and `schedule_profile`.

**Original state:** `int(sample_index)` and downstream context handling silently accepted booleans, floats, and strings. The baseline defect lint produced 33 warnings across easy/default/hard probes.

**Alternatives considered:** Continue coercion; validate only `generate`; allow negative indices as Python modulo aliases. These were rejected because distinct API inputs would collapse to the same deterministic sample identity and helper/entry-point behavior would diverge.

**Probe:** Tests were written first and failed on the baseline, then passed after the minimal helper was added. Final defect lint reports zero flags.

**Limit:** Difficulty validation remains the existing finite-value check; no unrelated API refactor was introduced.

## D3 — Declare only a real canonical shortcut

**Choice:** Remove `erase_interior_gray` and `solid_triangle` from `CANONICAL_SHORTCUTS`, retain them as ordinary semantic rivals, and declare `nearest_distractor_corner` instead.

**Original rationale/status:** The old names represented plausible errors, but the semantic gate showed they did not fit all canonical demonstrations (0/4 and 1/4). Calling them canonical shortcuts was factually wrong.

**Selected rival:** Choose the bbox corner closest in Manhattan distance to the interior gray marker and draw the triangle from that corner. Because every canonical distractor is at local `(1,1)` near the genuinely missing corner, this rule fits all 4 labeled canonical pairs.

**Alternatives considered:** Set `CANONICAL_SHORTCUTS = {}`; use an 8×8-only overfit; use a fixed missing corner. Empty metadata would avoid a false claim but miss the strongest real ambiguity. Size-only overfit is less structurally plausible, and fixed corners fail canonical examples.

**Separating probe:** A generated 10×10 case with missing top-left and a clockwise distractor near top-right makes the rival select top-right. Protected Racket and `rule_mirror` agree on the top-left triangle and disagree with the rival. Exact record: `checks/shortcut-witness/counterexample.json`.

**Failure modes/limits:** Manhattan ties can occur for the smallest rotated geometry; the explicit witness uses side length 6, where the nearest corner is unique. The claim is finite and executable, not a proof that no other shortcut fits the canon.

## D4 — Keep and expose the existing four-slot teaching schedule

**Choice:** Keep canonical anchor, translated clockwise, translated counterclockwise, and expanded near-missing slots. Add the nearest-corner rival to `LESSON_COMPETITORS` and the corresponding witness rather than changing generation.

**Rationale:** The generator already emits the exact counterfactuals needed to separate distractor location from missing-corner orientation. Changing the sampler would perturb valid deterministic outputs without improving coverage.

**Probe:** The final semantic gate reports all profiles represented in each band. The independent census materialized 100 lessons per band and rotated each of 5 pairs through the query position: 300 lessons, 1,500 rotations, zero declared-rival ambiguities.

**Limits:** No `LESSON_SCHEDULE_PERIOD` is declared, so this review did not claim exhaustive fixed-seed period coverage. The census only rules out declared competitors on sampled production lessons; universal induction remains unknown.

## D5 — Keep VERSION at 3.0.0

**Choice:** Do not bump `VERSION`.

**Rationale:** The patch changes invalid-input rejection and semantic metadata/tests, not any valid generated grid. A version bump would unnecessarily reseed every valid sample through `gen_ctx` and turn a contract repair into a distribution change.

**Alternative:** Bump to 3.0.1. Rejected to preserve deterministic valid-output identity.

## D6 — Do not modify the frozen legacy fixture

**Choice:** Leave `tests/test_generator_1238481b674b.py` byte-identical (SHA-256 `3b4e2e348f8b09bcec580d4abd8b2a3b03b61a2476b3f51d61b91145879eebd9`) and add `test_review_repairs.py`.

**Rationale:** DUTIES explicitly marks the baseline root test file as a frozen fixture and assigns its migration to the maintainer.

**Probe:** Required staged task tests fail preflight on the frozen file's fixed-depth canonical path before pytest. The new portable suite, run directly through the protected-Racket wrapper, passes 24/24.

**Limit:** The aggregate task-test gate remains blocked even though the new tests are green; this is reported as a blocker, not reclassified as a pass.

## D7 — Supersede, do not delete, stale authority history

**Choice:** Preserve associated historical notes but state in current `notes.md` that GNOTE-003731 is superseded for this source snapshot.

**Rationale:** Historical provenance is useful, but the pinned baseline and final source both independently passed `authority_sync`; repeating the old limitation as current would be misleading.

**Evidence:** Before and after authority-sync receipts, plus final 12/12 battery.

## D8 — Prior-review use

I used prior returns `review-cea4804a0e6548b7:v0001` and `review-dffcfb3105e6c47f:v0002` only as leads for the portable-fixture and shortcut-metadata defects. I reproduced both on the pinned baseline before patching. Their claims were not treated as measurements of current bytes.


## Review review-1d7501933dd1aee2 — parametric extension

- The pinned production generator remains version `3.0.0`, SHA-256 `907a296f355d90e454437e2c4e74b50d8d40f0541194fff99d3b847b2503a311`; canonical/default Racket hash `cbabe9d66374` and authority are unchanged. New before and after strict batteries are both 12/12 green.
- A separate **proposed prototype** under `workspace/parametric/` adds one episode-level `render_mode` parameter: canonical `outline` versus `solid` triangle fill. The mode is selected once from seed parity and shared across four demonstrations (indices 0–3) and query 4. Both labels are executed by complete Racket programs; all 10 retained pairs distinguish the two settings. Evidence: `checks/parametric/render-mode-evidence.json`.
- New focused prototype tests pass 5/5; combined public-API focused tests pass 29/29. The aggregate staged `task_tests` remains blocked at portable preflight by the immutable legacy fixture `test_generator_1238481b674b.py`; that file remains byte-identical and maintainer migration is still open.
- Production lesson evidence uses four ordered demonstrations plus one query. A 100-per-band census materialized 300/300 lessons and all 1,500 query rotations with zero ambiguities against declared rivals and zero errors. This is finite declared-rival evidence, not universal induction.
- The prototype is not selected authority or approved training data. Integration would require separate review/versioning; no catalog, base, canonical, or production generator path was changed.


## Current public prototype identifiers

Public filenames now derive only from visible demonstrations and query inputs. The original source/report is retained under `workspace/parametric/evidence/reviewer-original/` and `reviewer-reported/`; the corrected Racket-backed export is in `owner-current/`. Focused naming/writer checks passed; the source-bound owner receipt records the exact group count. This correction does not approve the prototype or rerun its full repair battery.
