# Working notes: ecd1f88fc6d3

## 2026-10-01 review (`review-080665b9e70e6cd0`)

Canonical authority was left unchanged. Its normalized rule hash is `16da73149c81`.

Baseline defects reproduced:

- no `RULE_HASH`, no `self_check`, and no semantic contract;
- declared `density`, `texture`, `direction`, `emitter_color`, and `palette_size` controls were dead, unobservable, or invalid in combinations;
- negative fixtures were included in the ordinary texture domain;
- only `1/60` pinned draws matched an exact canonical `(height, width, palette-size)` profile, and hard had zero profile support;
- strict override audit found 8,583 findings and accepted unknown keys.

Version 4 replaces the broad random emitter cloud with four explicit profiles:

1. `canonical_small`: right + down emitters, default `7x7`, palette size 5;
2. `canonical_medium`: up + left emitters, default `8x8`, palette size 5;
3. `canonical_distractor`: up + left emitters plus a color on an active ray and an isolated code, default `9x9`, palette size 7;
4. `direction_sweep`: one emitter in each direction.

The six-residue schedule
`small, medium, distractor, sweep, small, distractor`
retains the first three exact canonical profiles and guarantees that every three consecutive demonstrations contains the distractor profile.

Executable support added:

- strict unknown-difficulty and unknown-override rejection;
- honest axes limited to `grid_h`, `grid_w`, and recoverable `scene_profile`;
- `observe_overrides`, `self_check`, `strict_canonical_like`, and an independent Python `rule_mirror`;
- eight semantic witnesses, four rival solvers, four shortcut checks, and lesson identifiability;
- focused regression tests, including all canonical pairs, boundary override cross-products, distractor behavior, rival counterexamples, determinism, and sliding lesson windows.

Final evidence: 24 focused tests pass and the inherited after battery is 12/12 green. Exact-profile support is `54/60`; semantic strict support is `600/600`; all 12 materialized lessons are identifiable; the override matrix accepts all 3,960 valid draws and rejects unknown keys.

Remaining intentional limits: the curriculum stays close to the public 7–9 grid manifold and does not synthesize crossing active rays, whose row-major overwrite precedence is an implementation detail not demonstrated by the canonical examples.


## 2026-10-02 review (`review-201ae2dcbb09941c`)

Version 4's full battery independently passed 12/12, but the new normalization probe found only one geometry per fixed-size profile over 80 seeds. A code-blind seed-to-adjacent-marker rival fit all three public pairs and all 360 default-band draws. The new test-first regressions initially produced 14 failures.

Version 5 randomizes individual nonintersecting emitter positions with a bounded constructive sampler, not fixed-template fallback. The scheduled distractor keeps its seven-color signature while placing an inactive code 4 beside a seed, outside active rays and with no seed to its left. This guarantees an authority-zero cell that the code-blind rival paints. The validator now enforces the noncrossing promise, and known None overrides mean absence.

Measured after repair: 76/77/80/80 normalized fixed-7×7 layouts across 80 seeds per profile; code-blind rival agreement 0/80 on distractors. Forty task tests pass, including the predecessor's 24 unchanged tests. The after battery is 12/12 green; 120/120 Racket mirror applications agree, 600/600 strict inputs, 9/9 witness types, 5/5 declared rival claims, 12/12 identifiable lessons, and 3,960 valid override draws. A separate local stress test passes 3,600 draws including 900 distractor refutations and 144 deterministic replays. All task tests and the Racket witness probe also pass in an explicitly copied relocated runtime.

Reusable tools live in workspace/: probe_distribution.py, audit_probe.py, verify_portable.py and stress_generation.py. The return includes before/after logs, exact witness grids and failed test/probe/suite attempts. Top-level suite packaging/import problems are documented in FEEDBACK_TO_CODEX.md, not fixed outside this assignment's scope.

A source-frozen fresh solve used visible examples only during the solve phase; earlier rule exposure is yes. Its deliberate code-blind teaching-negative revision passes 2/3 visible examples; its final program passes 3/3. Hidden-query correctness is withheld; no blind-solve or training-admission claim is made.

Remaining limits: canonical 7–9 profile manifold, distinct active seed colors, no intersecting active rays, fixed inactive code identity and finite declared rival family. Canonical authority is unchanged (16da73149c81). See the compact workspace handoff before extending the domain.
## Current reviewer considerations

Source SHA-256: `5122f13d30c5c417a05b17375c96d6d18e77967db3ea9cdf9b9486d56390bf2b`.

# Distribution decisions and rejected alternatives

Assignment: `review-201ae2dcbb09941c`; task: `ecd1f88fc6d3`.

## 1. Preserve authority; fix the generator

The public rule and labels agree under independent Racket evaluation. The strongest reproduced problem was insufficient input support, not an incorrect authority. Changing the numeric direction semantics would move the target rather than fix the shortcut. The authority and canonical examples therefore remain unchanged. Evidence: all public-pair checks and exact rival witnesses in `checks/probe-after.json`.

## 2. Keep four profiles, the six-residue schedule and three-demo lesson length

The predecessor notes explicitly explain this choice: retain the canonical dimension/palette/direction signatures and ensure a distractor occurs in each consecutive length-three window. The sequence is small, medium, distractor, sweep, small, distractor. We retain that rationale, not an invented one. The metadata now says six-residue schedule rather than modulo four. Removing the schedule in favor of independent random profile selection would sometimes create nondiscriminating lessons; increasing demonstration count would change the teaching contract unnecessarily. Tests check sliding windows and the battery materializes 12 identifiable lessons. Profile overrides or caller-reordered demonstrations can bypass the guarantee and must be checked separately.

## 3. Randomize emitter positions, not merely palette and global translation

Version 4's concrete implementation used fixed emitter templates. Beyond its explicit emphasis on canonical closeness, the original reason for those exact coordinates is unknown. The normalized fixed-size probe shows why retaining them is not sufficient: one layout per profile over 80 seeds despite a green ordinary diversity check.

Version 5 enumerates valid positions for each profile's directions, randomly orders placement, and constructs disjoint full rays. This expands positional and length variation while keeping counts and palette observable. A free emitter cloud was rejected because it would reintroduce accidental activation, palette drift and hard-to-observe profile overrides. A hidden fixed-template fallback was rejected because it would conceal sampling failures and recreate structural concentration. Sampling retries are bounded at 128; exhaustion raises a clear error. No exhaustion occurred in the 3,600-draw cross-product or 3,960-draw override audit. This does not prove an all-seed bound or uniform sampling. Greedy placement can bias the layout distribution.

## 4. Keep active rays nonintersecting and enforce that promise

The predecessor explicitly excludes intersecting active rays because the canonical demonstrations do not teach overwrite precedence. We keep this domain boundary and add missing validation. The authority does have a deterministic row-major ordering; correctness on that wider domain is not needed to justify exposing it to learners. Adding crossings would mix a new instructional problem into this repair. Merely allowing the validator to accept them would falsely describe the generator's domain. A hand-constructed crossing case fails the new test against version 4 and is rejected by version 5. Passing this validator is not a proof that a scene was generated.

## 5. Make direction-code values causally necessary

The strongest concrete rival found starts a ray from any seed 5..9 through any cardinally adjacent marker 1..4, ignoring the marker's value. It fits all public examples and all 360 default-band predecessor draws. Palette shuffling, extra easy rays and ordinary marker-preservation distractors do not refute it.

Every new distractor scene therefore has an inactive code 4 adjacent to a seed, outside all active rays, with no seed immediately to its left. The authority leaves that cell zero; the rival necessarily paints a positive value there. This is a constructive distinguishing condition, not a probabilistic hope. “Isolated” in inherited descriptions is to be understood as nontriggering, not necessarily geometrically disconnected. We also retain a colored distractor downstream of an active code, so both “preserve input markers” and “stop at obstacles” remain false.

Using code 4 is deliberate: the distractor profile's active directions are up and left, so that unused code preserves the original seven-color profile. Randomizing the inactive code without constraints could alter the palette, activate an unintended ray or stop matching the observable profile. Holding this inactive code fixed is itself residual structure. A solver that reads values only to special-case code 4 may survive; no claim of universal rival elimination is made. A later, separately validated profile could diversify inactive codes without weakening three-demo identifiability.

## 6. Keep seed colors 5..9 distinct; preserve palette and grid bounds

Direction codes 1..4 are semantic, not nuisance colors; a generic whole-palette permutation is invalid. Distinct active seed colors and the 7..9 dimension bounds come from the predecessor's explicit canonical-profile choices. The original mathematical reason to exclude all repeated seed colors is unknown. We retain these limits to keep exact profile signatures and isolate this repair. New active rays may be as short as seed plus code; the distractor layout reserves a longer ray to place its downstream colored marker. Testing covers all four profiles and every dimension boundary. Repeated active colors, grids beyond nine, negative cases, crossings and zero-emitter examples remain future domain extensions rather than unsupported knobs.

Difficulty strings remain legal deterministic streams, not a measured monotonic ranking of cognitive difficulty. No new easy/medium/hard performance claim is introduced.

## 7. Treat known `None` overrides as absent, but reject unknown names

Shared generation context treats a known override set to `None` as unspecified. The predecessor's local profile/dimension selection could instead change the default or reject it. We normalize known `None` values before local interpretation, preserving strict rejection for unknown names even when their values are `None`. Explicit wrong types, invalid dimensions and unknown profiles remain errors. Dedicated regression tests cover absent-versus-None equivalence. Relaxing all validation was rejected because it would hide misspelled axes.

## 8. Keep review tools local and test both layouts

Only the assigned generator home is writable for source changes. Shared runtime mapping and suite packaging defects were not opportunistically patched. Native and relocated imports differ; the new probe makes that difference explicit. The relocated verifier records the actual directory and matching source hash and copies new tests intentionally rather than claiming that the ordinary catalog already includes them. Root detection assumes either the supplied native layout or the declared exported runtime; unsupported layouts fail rather than silently loading a neighboring repository.

## 9. Preserve failures and solve provenance

Tests were added before the repair and their predecessor failures are retained. A native namespace error, import-stripping failure and installed-package failures remain in the evidence. The solve came after generator freeze and deliberately avoided reopening any reference. Prior exposure is recorded as yes. The first wrong solver is explicitly an intentional teaching negative; the second is a reviewer-authored program, not a captured model conversation or token trace. Finite visible-example success does not disclose the withheld query labels, and no training-admission decision is claimed.
