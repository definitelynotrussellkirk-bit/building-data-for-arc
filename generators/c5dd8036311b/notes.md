# Current notes: c5dd8036311b — version 2.1.0

## Rule and domain

A single full-width horizontal bar contains color 1 and marker colors 2/8 on a zero background. Above each marker, grow a stem of color 1 with a same-color tip: four added cells for color 2, three for color 8. The input bar remains unchanged. These are fixed color-coded roles, so palette permutations are not interchangeable-rule tests.

The generated domain is H=8..30, W=6..30; one bar, at least one row below, sufficient upward headroom, and 1..8 markers from 15 declared count profiles. This is a deliberately narrow upward-bar family. Multiple bars, arbitrary obstacles, palette substitutions, other orientations, and clipped tips are outside the generator domain. A defensive Python rule mirror handles some broader cases, but that does not enlarge the declared domain.

## Repaired findings and reversed decisions

G1: The imported distribution capped total markers at four, omitted red-majority mixed scenes, and gave the medium band no exact canonical dimension/color profile. Original motivation was not recorded. Preserve all 11 old profiles, add teaching_5, teaching_7, six_mixed and balanced_8, and mix canonical geometry with broad/large geometry. Final pinned profile result is 32/60 exact and 33/60 envelope hits, with exact support in every band (11/11/10).

G2: Random independent examples could leave a plausible endpoint-omission rule consistent with every demonstration but wrong on the query. Default lessons now use an alternating teaching/variation schedule, period 24. Every four consecutive draws have four distinct marker-count profiles and two teaching witnesses. Three demonstrations therefore retain at least one complete witness under any one-query rotation. This protects against the five declared rivals only; it is not universal induction.

G3: Reject booleans/floats for seed/index and negative indices; keep every literal Python integer seed valid. The first repair incorrectly restricted seeds to uint32 and broke the 48-bit seeds used by semantic checks. The failing after battery and four positive wide/signed-seed regressions are retained; the cap was removed. Keyed GenCtx randomness also removes the old linear seed/index alias.

G4: The selected base solution's target_code differed from canonical authority only in whitespace. It now equals canonical text exactly; canonical source/labels and archival raw_code are unchanged. Rule hash remains fd929da87d08.

The inherited mutable tests were migrated to reviewer_support portable helpers and observable contracts. Fixed private enumeration/version and disjoint-height expectations were removed. No frozen root/shared tests were changed.

## Current evidence and limits

Final generator SHA-256: 8c8516063ea26db20c415a47d8d48bf346bb100c64e419d30f3988effc3ccb04.
Final strict battery: 12/12 green; strict membership 600/600. Production census: 100 lessons per band, 300 total, 1,200 labeled pairs, 1,186 unique inputs, zero declared-rival ambiguity in ordered production or 1,200 holdouts. Schedule census: all 24 starts at seed 0 across three bands, 72 overlapping lessons, 288 pairs/rotations, 81 unique inputs, zero ambiguity. All use three demonstrations and one query. Forced public_N overrides reproduce exact public inputs and are inspection controls, not promises of distinct repeated examples.

counterexamples/five-shortcuts.json retains an accepted 9×8 witness and exact Racket outputs. workspace/probe_shortcuts.py rechecks the actual shortcut declarations, canonical fit, and three authoritative witnesses through the public API. The final isolated task-test stage passes 163 tests. The global repository suite still reports 17 failures; its separate triage found no selected-task failure.

## Proposed parameter extension

workspace/parametric varies height_8 and height_2 independently over 2..5, with default (3,4), one setting per episode, both symbols in every pair, and real instantiated Racket labels. V2 evidence crosses two identical input replicas with all 16 settings: 32 episodes, 128 labeled pairs on 8 unique inputs, 128 holdouts, 1,920 alternative-setting comparisons, no ambiguity. An intentional missing-symbol negative control yields three ambiguities.

V1 public filenames and setting-specific seeds disclosed the setting; retained failing tests prompted opaque random IDs, shuffled public export order, and identical input seeds across settings. The deterministic make_episode(seed) API still requires keeping seeds private. The extension is proposed, not approved for training, and is separate from the canonical repair.

## Current owner source and evidence limits

Accepted2.1.0 broadened canonical/large geometry, fifteen count profiles and period24 alternating complete witnesses against five declared rivals. Signed and arbitrary-width integer seeds remain supported after correcting an introduced uint32 restriction. Canonical Racket unchanged; selected base target_code synchronized in whitespace only, tokens/all other JSON and archival raw_code preserved. Reviewer12/12 strict battery,163 portable task tests also in fresh dependency-closure replay (all14 changed paths exact). Canonical floor0/60 to32/60 (11,11,10 per band),600/600 strict support and5 canonical inputs. Production300 lessons/1200 rotations clean (1186 unique inputs); all24 starts at seed0 in three bands72 lessons/288 rotations (81 unique inputs). Teaching/count correlations and finite rival limits remain. Two heights2..5 yield16 proposed settings; crossed shared input replicas, random opaque delivery IDs and shuffled public order repair original filename/input-fingerprint leakage.32 episodes/128 holdouts,23 focused prototype/privacy tests, exact default source. Separate root suite1002 pass/17 fail/3 skip/18 subtests stays failed; unchanged shared/test source comparisons do not prove a baseline pass. No owner full battery, production parameter API, variant approval or training admission.
## Current reviewer considerations

Source SHA-256: `8c8516063ea26db20c415a47d8d48bf346bb100c64e419d30f3988effc3ccb04`.

# Decisions and boundaries

Assignment `review-d3e11e1dcfcb4756`, task `c5dd8036311b`, original ARC family `training:72a961c9`. The assignment and both drawn audit targets are unchanged. Parametric exploration began before the canonical repair. The initial blind solve preceded opening the repair implementation/reference.

## D1 — Preserve the canonical operation and narrow input family

The operation is independent upward growth above color-coded markers in one horizontal bar. Color 2 denotes four added cells and color 8 denotes three; stem color is 1, background 0, and the tip keeps the marker color. The original input is preserved. A single local operation is a legitimate rule; adding extra unrelated steps would change the reasoning pattern.

Keep full-width bars, zero background, one bar, sufficient headroom and at least one row below. Broaden geometry to H=8..30 and W=6..30 and marker count to 1..8 within the declared profiles. Reject multiple bars, stray pixels, arbitrary obstacle fields and color substitutions. The canonical color roles are fixed, so random palette swaps would change the rule. Larger grids stress scale while preserving the same operation. Rotations, horizontal growth and obstacles were rejected as unmotivated canonical changes. The original author's justification for narrower dimensions and profiles was not recorded; observed consequences, rather than an invented rationale, motivate this repair.

The selected base JSON's target_code and canonical source were whitespace-normalized equal before editing. The target now equals canonical source bytes exactly. Archival raw_code and the canonical ledger are preserved. This resolves authority synchronization without changing intended outputs.

## D2 — Separate geometry coverage from difficulty labels

The old medium heights were 11/12, excluding all canonical shape profiles, and the pinned 60-draw probe found no exact hits. All bands now use a 50% canonical-geometry lane, 20% broad band-specific geometry, 20% large rectangles with H=21..30, and 10% exact 30×30 grids. Single-color canonical shapes are 9×6 or 10×7; mixed shapes are 9×9, 9×11 or 13×10. Placement, edge, colors and bar position remain randomized where allowed.

This mixture deliberately balances canonical support with broader support. Always canonical-size grids would conceal scale sensitivity; disjoint height bands would recreate the old zero-support defect; uniform all-size sampling would make exact canonical profiles too rare in small pinned samples. Final measured support is 32/60 exact, 33/60 envelope, with exact hits 11/20 easy, 11/20 medium, 10/20 hard. Those are measurements, not population probabilities. Difficulty names are sampling bands, not validated human difficulty scores.

## D3 — Teach a complete family of concrete rivals

The eleven original marker-count profiles are retained. Four new profiles add total counts five, six, seven and eight: teaching_5=(3 of 2,2 of 8), six_mixed=(4,2), teaching_7=(4,3), balanced_8=(4,4). Three are teaching profiles; the other twelve are variation profiles. Default teaching scenes include an adjacent marker pair at a randomly chosen edge, more than four markers, more than two of one color, and a strict color-2 majority with color 8 present. These properties jointly distinguish five actual executable rivals:

- ignore boundary markers;
- ignore adjacent markers;
- process only the first four markers from left to right;
- process at most two markers of each color;
- let a minority color-8 marker grow four cells when color 2 is more numerous.

All five fit all five usable canonical pairs, and the final authoritative probe validates three disagreement witnesses. The retained early baseline probe has a different fifth candidate, mixed_minority_taller, which swaps both heights under the majority condition. That earlier candidate is not silently identified with the final one-color-only callable.

The original generator's four-marker cap made the first-four shortcut observationally indistinguishable across its emitted count profiles. Independently, a real baseline production lesson at seed 1729/easy/start 4 let endpoint omission fit all three demos while disagreeing on the query; this was verified via public Racket application. That is a teaching defect even though individual labels are correct.

## D4 — Schedule complete lessons and protect query rotations

Set EXAMPLES_NEEDED=3. Default exported lesson policy is three demonstrations plus one query. Alternation depends on `(seed + sample_index) % 2`; profiles cycle within the three teaching or twelve variation classes, giving declared period 24. Every four consecutive indices contain two distinct teaching profiles and two distinct variation profiles. Their marker multisets are all different, so the production sampler cannot discard one as a duplicate of another within that window. Whichever of the four pairs is held out, at least one full teaching witness remains among the demonstrations.

An earlier random profile selection within each lane was rejected because a production deduplication step could skip a repeated input and undermine the intended four-draw structure. A retained failing uniqueness regression motivated deterministic profile cycling; geometry remains keyed and random. Purely ordered curricula were not chosen: arbitrary one-query rotations are explicitly required and checked. Always-dense scenes were also rejected; variation profiles preserve sparse, single-color and balanced scenes.

Final evidence: 300 production lessons (100 per band), 1,200 pair appearances on 1,186 unique input grids, zero ambiguity/errors/warnings for ordered lessons and all 1,200 rotations. The separate period census uses seed 0, starts 0..23 in every band, 72 overlapping lessons/288 pairs/288 rotations, and 81 unique inputs. Its reporting modulus 6 is not the declared period. All saved lessons accepted four consecutive requested indices without rejection skips. Exact per-lesson seeds and sample indices are retained in the full source-bound reports. These finite checks test five unique rivals exposed through fifteen namespace bindings, plus reported generic bounded probes; they do not prove universal identifiability or all-seed coverage.

Forced public_N overrides retain the exact canonical input and are inspection controls. Repeating one such override can produce duplicate inputs; a forced-override multi-example lesson is not covered by the default distinct-window guarantee. The semantic hook checks available color roles and rivals on actual demonstrations/query, rather than approving labels solely from a named profile.

## D5 — Validate scalar types without narrowing valid seeds

Reject bool and non-int seed/index values and negative sample indices. The imported generator accepted invalid scalars and used a linear combined seed that created cross-(seed,index) aliases. The repair uses shared GenCtx keyed randomness.

A first repair mistakenly imposed uint32 seed bounds. The strict battery then exposed valid 48-bit pinned seeds (e.g. 153800779826655) crashing profile/semantic probes. This was our introduced regression. Four focused signed/wide-integer cases reproduced it; the final source permits any literal Python int seed, including negative and arbitrary-width integers, while keeping index nonnegative. The failed battery, intermediate source, RED log and final GREEN remain retained. Shared census schedule_seed has its own uint32 control contract; that does not constrain the generator API's seed input.

## D6 — Portable and meaningful tests

The 118 inherited task tests were mutable and tied to private enumeration/import paths, exact old version, disjoint height bands and an overstrong uniqueness count. They now use reviewer_support.find_root/canonical_path/canonical_pairs and portable module loading. Retained observable checks include canonical behavior, broad mirror/Racket behavior, clipping behavior of the mirror, first-bar selection, input immutability and malformed inputs. Twenty-two new regressions cover scalar contracts, aliasing, geometry, declarations, missing teaching witnesses, distinct four-draw profiles and large/dense cases. The 23 parametric tests separately exercise actual rules and public exports. The public isolated stage executes all 163, with no import diagnostic errors or skips.

No shared/root frozen test or implementation was edited. The root suite remains failed (17 failures) and has its own source comparison/environment triage. No historical pass is inferred. Further unrelated runtime changes would exceed the assigned repair boundary; the actionable diagnosis is returned instead.

## D7 — Proposed two-height extension

Choose two small literal rule parameters, height_8 and height_2 in {2,3,4,5}, default (3,4), with one pair held fixed per episode. These preserve the color-coded conditional reasoning and make the numerical mapping a demonstration-inferred task parameter. Equal and reversed heights are allowed; tying height to numeric color rank would introduce a shortcut. Do not parameterize palette, orientation, stem color, clipping, or multiple operations in this proposal.

Every pair contains both marker colors; input generation reserves headroom for the largest possible height and is independent of the chosen setting. Each setting materializes an exact Racket program using the protected bridge, with no Python-label fallback. The default program equals the canonical source byte for byte and matches 5/5 canonical labels. The final suite's 16 settings yield distinct outputs on a shared witness; 32 episodes and 128 holdouts produce 1,920 alternative-setting comparisons with zero ambiguity. A deliberately absent-symbol teaching negative produces three ambiguous holdouts. It is labelled intentional, not a natural solver failure.

## D8 — Repair exporter information leaks before proposing use

V1 sequential filenames revealed the sorted setting (32/32 observed cases), and different input seeds per setting enabled seed lookup. The public challenge JSON itself was masked, but delivery metadata still leaked the answer-defining setting. Three real failing privacy tests were retained before changing the exporter.

V2 crosses the same two input seeds, 0 and 1, with all 16 settings. Hence 128 labeled pairs intentionally use only eight unique input grids. Each export gets independently random 128-bit IDs and an independently shuffled write/index order. Only public/ is learner-visible; settings, seeds, program sources, mappings and query labels remain private. A repeated export retains content with fresh identities. All 23 focused tests pass, and the artifact audit verifies 125 retained hashes, all 32 public projections and five source bindings. The deterministic make_episode(seed) API remains deterministic and can disclose the setting if a seed is exposed/enumerated; the stronger guarantee is scoped to the crossed evidence exporter.

This is a proposed prototype. A successful canonical repair or bounded parameter check does not grant variant approval or training admission. Generalization to more shapes/seeds/settings is unmeasured. V1 is retained as explicitly superseded, not erased.

## D9 — Preserve failures and deliver a replayable delta

All actual failing iterations, intermediate generator snapshots, baseline counterexamples, original v1 exports, privacy RED, root-suite failures and solve bookkeeping failures are retained. Large superseded evidence is losslessly compressed with original-path/size/SHA maps and restoration instructions. Public solves retain only permitted visible feedback; private query correctness remains unknown. The final solve declares prior exposure and binds the final generator hash.

The final handoff uses the public delta builder and a fresh original-packet runtime-closure replay. That extraction is intentionally partial; the replay receipt records its coverage and verifies every changed path/hash. Focused tests run in the new checkout separately from static patch application. Receipt and command details belong in RESULTS.json and checks/replay/. No full environment, duplicate repository or installed dependency tree is transported.
