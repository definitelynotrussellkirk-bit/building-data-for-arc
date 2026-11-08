# Working notes: 040bfb038c65

## Current rule and source identity

The selected rule is unchanged in meaning: find the 4-connected yellow (`4`) objects, quotient their shapes by D4 rotation/reflection, and recolor the unique D4 class cyan (`8`). The final generator is version `3.0.0`, SHA-256 `c7bc4573dc3efe33da4b079eacdd52588f67b7294ca53df9c66efdf100a1615e`, with canonical `RULE_HASH = "80d289c11e33"`.

The selected authority file was synchronized so `racket_target.target_code` is exactly `racket_target.raw_code`; this is an exact-text/authority repair, not a semantic Racket-rule change. Current authority-file SHA-256: `1a72856f242fcd4ec566c17daabac91a2cf89f8086c00b0752adf8858c588601`.

## Prior open finding used as a lead

Used retained return `review-a9c2c4e2a4816f8c:v0001` only as a lead. Its source-bound finding `A040-F1` showed that the old version `2.0.1` could emit three demonstrations on which “recolor the largest yellow object, row-major on ties” fit, followed by a smaller-oddball query on which it failed. The current source was measured independently before repair.

## Reversed choices

The prior generator independently sampled object-size relations and relied on rejection sampling. It also advertised combinations that were not consistently constructible or observable, included invalid degenerate textures, omitted `RULE_HASH`, and declared no executable lesson/rival contract.

The replacement is constructive:

- Four independent 3×3 corner regions guarantee separated objects on every advertised `7..14 × 9..16` grid.
- Two or three majority objects plus one oddball are built from finite free-polyomino catalogs of sizes 3–5.
- Exact controls are limited to the fully constructive cross-product: `grid_h`, `grid_w`, `n_majority=2..3`, and `texture=smaller_odd|same_size_odd|larger_odd`.
- A deterministic three-slot schedule emits smaller, equal, then larger oddballs. Equal-size examples place the oddball after a majority in row-major order, so the largest-object tie-break is also refuted.
- Ordinary dimensions are strongly anchored to canonical 7×9/10 profiles while still sampling both declared endpoints.
- `strict_canonical_like`, `SEMANTIC_RIVALS`, `SEMANTIC_WITNESSES`, `WITNESS_RIVALS`, `CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, and `lesson_identifiable` now make the teaching claim executable.

## Current evidence

- Focused task regressions: `123 passed`; every advertised override cross-product round-trips in every band.
- Formal after battery: 11/12 stages green. The sole nonzero stage is the strict follow-up warning that a declared finite schedule must be exhaustively enumerated outside the smoke battery.
- Required schedule census: 9/9 fixed-seed start-residue lessons, 36/36 query rotations, zero ambiguities/errors/warnings.
- Production census: 300/300 lessons (100 per band), 1,200 unique inputs and 1,200 query rotations, zero declared-rival ambiguities/errors.
- Reusable probe: `workspace/probe_curriculum.py`; 9 lessons/36 rotations green and canonical largest-rival fit confirmed 3/3.
- Minimal replayable witness: `counterexamples/largest-object-shortcut-v3.json`.
- Exposed visible-only post-repair solve passed all 3 demonstrations in one revision without consulting the reference during solving.

## Known limits and open questions

The four-corner placement grammar is intentionally narrower than arbitrary free placement. The semantic evidence is finite and only excludes declared/tested rivals; it is not a proof of unique induction against every imaginable hypothesis. The exhaustive schedule census covers every residue and rotation at seed 0 across all bands, while the broader 300-lesson census samples many seeds but does not enumerate the entire generator state space. Position-based or more exotic undeclared shortcuts remain an open adversarial-testing area.
## Current reviewer considerations

Source SHA-256: `c7bc4573dc3efe33da4b079eacdd52588f67b7294ca53df9c66efdf100a1615e`.

# Decisions: 040bfb038c65

## D1 — Treat lesson identifiability as the primary defect

**Original choice:** sample each grid independently and hope a lesson contains a useful size counterexample.

**Why changed:** retained return `review-a9c2c4e2a4816f8c:v0001` reproduced a three-demo lesson where the largest-object rival survived and changed the query. I independently reproduced the baseline failures and kept that prior return only as a lead.

**Alternatives considered:**

- Keep independent draws and reject/resample whole lessons: rejected because the per-grid generator has no reliable lesson-level transaction and probabilistic repair makes replay/coverage harder.
- Add only a witness hook: rejected because naming a defect does not ensure every exported lesson teaches against it.
- Deterministically schedule semantic profiles: selected because every window and rotation can be exhaustively checked.

**Failure mode guarded:** a correct label set that underdetermines the intended rule.

## D2 — Use a three-phase size-relation schedule

**Choice:** `smaller_odd`, `same_size_odd`, `larger_odd`, indexed by `sample_index mod 3`.

**Rationale:** smaller oddballs refute strict-largest; equal-size oddballs placed after a majority refute row-major tie-breaking; larger oddballs retain natural variation and prevent “always smallest” from becoming the intended lesson.

**Probe:** `checks/schedule-census-final.json` enumerates all three starts in all three bands and every query position: 9/9 lessons, 36/36 rotations, zero ambiguity/errors.

**Limit:** this schedule addresses the declared largest-object family, not every conceivable hypothesis.

## D3 — Replace rejection placement with four constructive regions

**Original choice:** random shapes and placements with retries.

**Choice:** four disjoint 3×3 corner regions, each with internal orientation/offset variation.

**Rationale:** every advertised grid dimension supports four separated regions, so all exact-control combinations are constructive. This removes stochastic collision failures and makes validator assumptions transparent.

**Rejected alternative:** arbitrary interior placement with escalating retry limits; it would reintroduce non-total exact controls.

**Limit:** position support is narrower than arbitrary free placement.

## D4 — Narrow the exact public object-count domain

**Original advertised surface:** included combinations not guaranteed to fit or round-trip.

**Choice:** `n_majority=2..3`, producing 3 or 4 total objects.

**Rationale:** four constructive regions guarantee the entire cross-product on the minimum 7×9 grid and match the canonical object-count style. Supporting four majority objects would require five regions or a different geometry.

**Test:** every endpoint/control combination in every difficulty band round-trips through `observe_overrides`.

## D5 — Keep broad dimensions, but anchor ordinary sampling to canonical profiles

**Choice:** exact `grid_h=7..14`, `grid_w=9..16`; defaults weight height 7 and widths 9/10 heavily while retaining all endpoints.

**Rationale:** the first repair accidentally advertised a broad range without ordinary draws reaching it. A failing test in `checks/tdd-red-axis-span.log` forced the correction. This keeps canonical support strong without making wider dimensions override-only.

**Alternative rejected:** narrow the declared dimensions to 7×9/10; unnecessary because the constructive layout works throughout the larger range.

## D6 — Enumerate free polyominoes instead of maintaining hand lists

**Choice:** deterministically enumerate D4-free polyominoes of sizes 3–5 that fit 3×3, then choose distinct majority/oddball classes.

**Rationale:** a finite generated catalog is easier to audit for D4 distinctness and supports orientation variation without duplicated hand-coded shapes.

**Failure mode guarded:** accidentally selecting two transformed copies as “different” classes.

## D7 — Make the semantic contract executable

**Choice:** add `strict_canonical_like`, a Python `rule_mirror`, named rival/witness mappings, canonical shortcuts, lesson competitors, and `lesson_identifiable`.

**Rationale:** prose claims were not machine-checkable. The formal semantic gate can now verify strict support, canonical acceptance, witness firing, rival validity, and lesson/query behavior.

**Limit:** the Python mirror is a test oracle, not the authority; Racket remains authoritative and is bound through rule smoke/censuses.

## D8 — Retain a minimal counterexample and a fast probe

**Choice:** add `counterexamples/largest-object-shortcut-v3.json` and `workspace/probe_curriculum.py`.

**Rationale:** future reviewers should be able to replay the exact disagreement and recheck every schedule residue in seconds rather than reconstructing a historical audit.

**Tests:** both artifacts are loaded, hash-checked, and replayed by the 123-test task suite.

## D9 — Synchronize authority text without changing rule meaning

**Original condition:** selected `target_code` and `raw_code` differed textually while executing the same rule.

**Choice:** set selected `target_code` exactly to `raw_code`.

**Rationale:** authority synchronization was a blocking formal stage. The semantic rule and `RULE_HASH` remain unchanged; rule smoke, Racket lint and authority sync are green.

## D10 — Preserve the strict battery warning rather than game it

**Choice:** keep `LESSON_SCHEDULE_PERIOD=3` declared, accept the smoke battery’s nonzero follow-up warning, and run the required exhaustive census.

**Rejected alternative:** hide/remove the schedule declaration merely to make the aggregate battery green.

**Evidence:** `checks/after/result.json` records the warning; `checks/schedule-census-final.json` discharges it with zero findings.

## D11 — Replay the returned patch, not merely the working tree

**Choice:** build a preliminary return, extract the original uploaded packet into a new directory, run `git apply --check`, apply exactly `patches/source.patch`, and rerun the complete task-local regression suite plus the curriculum probe.

**Rationale:** this detects hidden dependencies on unreturned working files, accidental patch omissions, stale solve-source bytes, and path/mode mistakes that ordinary in-place testing cannot detect.

**Evidence:** `checks/final-replay/summary.json` binds the original packet, replay input return, source patch, six changed paths, final source hashes, solve hash, **123/123** tests, and the 9-lesson/36-rotation probe. The final repack may add only review documents/evidence; acceptance identity is the retained `source_patch_sha256`.

## D12 — Add a native sequential parametric family without changing the canonical rule

**Choice:** keep `target=outsider` byte-for-byte equal to the canonical Racket program and add `target=farthest_partner`. The alternate first finds the unique D4-shape singleton, retains its bounding-box anchor, then recolors the repeated-class object farthest from that input-dependent anchor. Inputs are sampled independently of the setting and shared exactly across paired settings.

**Why this is non-cosmetic:** step B cannot select its target until step A supplies the oddball anchor. A protected-Racket `skip_a` counterfactual that always chooses the bottom-right object changes the final output on retained 7x9 and 30x30 cases.

**Episode contract:** 2–6 demonstrations, exactly four distinct queries, and a boundary-spanning 30x30 fourth query. A reusable finite audit checks seeds 0 and 17 at 2/3/6 demonstrations against largest-object, fixed-corner, nearest/farthest-partner, and canonical-outsider rivals as applicable; it also checks that settings, programs, query labels, and future queries are absent from the first public turn.

**Native evidence:** adapter SHA-256 `aae81a313d6ed856630c24ff9dc99f986c95a5dd4f11662bab628599167523e4`; promotion SHA-256 `e73bc5a22853b943d4d1136469f69b72dfa9e2cdfdde12ba0574179d327d361c`; manifest SHA-256 `1c9b4e1249e0f89f4b5b9f3edaca477e67235f19cc83b547a92765d02ed174c2`; native qualification SHA-256 `79e2792257117ef85f6bfe56606fb57260dffe1e3a28bf622ffacb9baacf684c`; causal witness SHA-256 `71686bdffc9166119199fd22276f23d33216fc1eb6955086f1d2d16bd04150c6`. The complete task-local suite is 127/127 green.

**Limits and next action:** finite rivals and bounded witnesses do not prove unique induction or universal algorithmic depth. Reviewer status is `ready`, not accepted. After integrating the exact returned source, the owner must rerun native qualification, protected witness replay, and fresh acceptance before any use or training admission.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/040bfb038c65/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->
