# Working notes: 3e0aef964b9e

## Intended rule and authority

The unique modal background surrounds exactly two foreground colors. Try both role assignments using 8-connected objects and the canonical pixel-corner convex-hull rasterizer. Exactly one target has a positive background gap matching total opposite-color donor count. Erase all donors and fill that gap with donor color. Canonical Racket and pin `cac0ce22f2ed` are unchanged.

## Current v3.1.0 decisions and reversals

Final generator SHA-256: `e4006e39e480a7317b3c58a1598ffa9891d5b0ae69bd9d635b59c9a2d7197dfb`.

The prior v3.0.0 parser and validator remain. Its dense targets only exposed interior holes, letting horizontal row-span completion fit all six canonical records and an actual three-demo lesson while failing its query. Dense profiles now remove one hull-preserving side-boundary cell plus K−1 interior cells. The canonical gap count remains, while row spans disagree. `counterexamples/horizontal-row-span-before.json` retains the old seed-313 lesson and source hashes.

Only `horizontal_row_span` remains a canonical-fitting shortcut (6/6 records, three unique pairs). The four former claims fit only 4/6, 2/6, 4/6 and 4/6 and remain semantic/lesson competitors. The alternate default decoy cycle and sparse-decoy preference restore eight persistent target cells, fixing a measured structural-support gap.

Three demonstrations are required. Two of three profile residues supply dense row-span witnesses, so four consecutive draws retain a witness after any single holdout. The 300-lesson census has 1,200 unique inputs and zero ambiguous production lessons or rotations against five distinct rivals. Fixed-seed enumeration covers three starts × three bands at seed 0: nine overlapping lessons, 36 rotations, eight unique inputs. New tests also inspect six combined profile/hole starts at seeds 0 and 313. These are finite declared-rival results.

## Proposed extension

`workspace/parametric/` contains an unapproved runnable prototype with episode-fixed `donor_policy={move,copy}` and `fill_policy={donor,target}`. Default returns exact canonical Racket. Variants retain object/count/hull selection, changing donor retention or gap color. Four Racket-labeled episodes and a same-input four-output witness retain source/program hashes; each episode's demos refute three alternatives. Twelve prototype tests pass within the 53-test portable suite. No production API, approval or training-admission changes.

## Limits and open findings

Exact axes remain dimensions 13–24, holes 1–6 and decoys 1–2. Construction has finite templates/four placement slots. Sparse templates translate without unrestricted reflection/rotation because raster hull boundaries are direction-sensitive. Arbitrary shapes, 30×30 grids, unknown rivals and all seeds remain unverified.

The old `review-788627da088ff9a4:v0001` audit remains `needs_triage` in the unchanged review index; its source was `5de0d65daa7fb62a227f03bbf2ca3d42ed1aeac7df8cc4699645401c4a9c3ed7`. Later accepted v3.0.0 return `review-f851fb09986ca14c:v0001` addressed those reported issues but did not administratively close the audit. Historical status does not substitute for current measurements. The return's `checks/` preserves failures and final receipts; `DECISIONS.md` explains alternatives and scope.

## Current owner source and evidence limits

Accept3.0.0->3.1.0 hull-preserving side gaps,persistent-marker support and truthful canonical-shortcut declarations. Canonical parser,mirror and Racket unchanged. Horizontal row-span rival fits6/6 appearances of3 unique canonical pairs;new dense witnesses survive every3-demo holdout. Reviewer reports12/12 battery,53 tests(41 canonical/12 prototype),300 lessons/1200 rotations clean;seed0 covers9 lessons/36 rotations with8 unique inputs. Fresh347/96412-file dependency replay repeated53 tests;initial missing-assignment wrapper failure retained. Move/copy donors and donor/target fill yield4 proposed settings,4 episodes/12 rival eliminations and four distinct outputs. Finite13-24 dimensions/templates;no30x30 guarantee. Older5de0d65d connected-donor/malformed-grid audit not explicitly replayed;retain unresolved. Owner checked hashes and public/private structure statically; tests and labels remain reviewer-reported.
## Current reviewer considerations

Source SHA-256: `e4006e39e480a7317b3c58a1598ffa9891d5b0ae69bd9d635b59c9a2d7197dfb`.

# Decisions for 3e0aef964b9e

## D1 — Preserve authority and original reasoning

The supplied v3.0.0 source uses modal background, two foreground roles, 8-connected targets, pixel-corner convex-hull gaps and donor-count matching. Canonical Racket agrees with the inspected labels; rule pin `cac0ce22f2ed` remains. The original pre-v3 simplification rationale is unknown. Prior accepted return `review-f851fb09986ca14c:v0001` and unresolved audit `review-788627da088ff9a4:v0001` were leads, not current measurements.

No canonical rule, base authority, shared parser, mirror, approval or review-index record changes. Altering the reference to fit a rectangular sampler would change the task. Generic successful checks do not resolve the old administrative `needs_triage` status.

## D2 — Develop a small rule extension first

The original-family priority requested parameterization first. The task-local prototype was developed while the baseline was inspected. Donor retention (`move`/`copy`) and gap color (`donor`/`target`) change executed behavior while preserving object roles, count matching and geometry. Cosmetic palette/padding switches would not satisfy this requirement.

Defaults are byte-identical canonical Racket. Selected canonical generation still uses one fixed rule; no production API or approval changes. Parameters are chosen once per seed/episode, not independently per pair, because incoherent hidden rules cannot be inferred from demonstrations.

Four retained episodes, each three demos/one query, refute all three alternative policy settings using demos only. All labels and a four-distinct-output witness execute with Racket. Evidence: `checks/parametric/episodes/private/manifest.json`, its exact rule programs, `final-manifest-check.json`, and 12 focused passing tests. These are finite proposed-policy checks, not production or training approval.

## D3 — Separate real canonical rivals from partial heuristics

Old isolated-donor, rectangle-only, largest-object and lower-color shortcuts fit respectively 4/6, 2/6, 4/6 and 4/6 canonical records. Calling them all-canonical-fitting was false and failed the semantic gate. The six records represent three distinct pairs duplicated across two variants.

Horizontal row-span completion fits all six. Only it belongs in `CANONICAL_SHORTCUTS`; all five remain semantic and lesson competitors. Dropping the partial heuristics entirely would weaken useful generated-lesson checks. A regression iterates the actual declaration and independently verifies every claimed canonical fit.

## D4 — Repair a concrete lesson ambiguity constructively

At old hash `e915f914cbfc3940207d9ccd587d24c987ef24c163a523531930283910a805f9`, seed 313, difficulty None, indices 1–3 all fit row spans, but query 4 differs in ten cells. Actual public Racket checked all four labels. The old lesson hook accepted it because that rival was absent. The task counterexample and `checks/canonical-probe/` retain exact data and source identity.

New dense construction removes one eligible row-edge boundary pixel whose deletion preserves the full raster hull, plus K−1 interior pixels. Intended gaps still total K, the object stays connected, and horizontal gaps are fewer. A finite Python geometry probe checked 62,688 cases across three shapes, eight transforms, legal counts, side cells and interior subsets. Actual Racket checks and strict gates are separate evidence.

Only adding a declaration would leave ambiguous lessons; increasing random witness frequency would still allow witness-free demos; special-casing seed 313 would only fix one reproducer. The constructive condition covers both dense profile residues.

## D5 — Three demonstrations and explicit rotations

The period-three semantic schedule alternates connected/dense, scattered/sparse and mixed/dense profiles. Four consecutive draws contain at least two dense witnesses; holding out one leaves at least one among three demos. The hole/decoy cycle adds period-six structure, so tests check all six starts too.

Production evidence uses the actual sampler, accepted-index metadata, three demos/one query and deterministic seeds. Rotations hold out each labeled pair once, preserving remaining order. The random census covers 100 lessons per band, 1,200 unique inputs and 1,200 rotations. Fixed seed 0 covers three starts × three bands: nine overlapping windows, 36 occurrences and eight unique inputs. These checks cover declared rivals and recipes, not all seeds or control combinations.

The first after battery omitted a schedule attachment and remained a warning/failure despite positive smoke results. Preserve it. A fresh final invocation attaches the source-bound receipt with required rotation policy; do not relabel the earlier aggregate or mix checkpoint settings.

## D6 — Restore canonical scale without changing connectivity

Before defect lint found generated persistent-marker support disjoint from canonical `{0,8}`. Semantic components remain 8-connected even where coverage tooling measures 4-connectivity. Sparse diagonal templates retain small 4-connected scale under the authoritative 8-connected rule.

The old default decoy cycle `(1,2)` becomes `(2,1)`; sparse-decoy preference allows a three-cell one-gap target beside a five-cell decoy, supplying eight persistent target cells and a larger decoy. Weakening coverage or changing semantic connectivity would hide the distribution gap. The new support regression was red before repair and green afterward.

## D7 — Keep exact controls and limits honest

Supported axes remain dimensions 13–24, holes 1–6 and decoys 1–2. Existing type/range/unknown-key validation and reconstruction of observed controls remain. The battery checks advertised controls; independent review also exercised all 36 profile/hole/decoy combinations on alternating 13×24/24×13 grids.

No extension to 30×30 is claimed: extra empty padding adds little relational variety while requiring more verification. Four corner placement slots and finite templates remain restrictions. Arbitrary-blob rejection sampling would create poorly characterized support and unpredictable exact-control cost. Future broadening should target these relational restrictions directly.

## D8 — Preserve asymmetric raster semantics

Sparse templates translate without unrestricted rotation/reflection: the existing pixel-corner ray-casting boundary convention is direction-sensitive. Do not replace this contract with Euclidean symmetry intuition. Dense transformations are checked with the same raster semantics. Equality on canonical data does not establish legality for every sparse transformation.

## D9 — Make the proposed authoring tool reproducible

Shared `wrap_rule` failed in direct repository layout because `scripts.comment_solutions` was absent. The local prototype instead uses public `strip_rule_wrapper` and executes the self-contained lambda with `RacketBridge`; F1 requests a shared fix without making one in this patch.

Exact source bytes identify the prototype, generator, canonical program and helpers. Parser caching keys full ledger bytes, not only file stat; generator loading avoids stale bytecode. A guard rejected a test during a parent source edit. Final evidence binds the frozen generator before and after execution. Public challenges exclude hidden parameters, reference programs and query labels.

## D10 — Preserve failures and solve provenance

Keep the failed before battery, six red teaching tests, intermediate schedule warning, prototype assertion/import/source-guard failures, and expected audit apply failure. Distinguish code repair from rerunning with complete evidence. Exact commands/exits live in `RESULTS.json` and component journals; exit 0 alone is not a semantic pass.

Blind solve finished before source inspection; post-repair solve was prepared from frozen final bytes. Each has one genuine attempted revision and passes three visible examples. Session exposure is `yes` post-repair even though the delegated solver was personally unexposed. Hidden correctness is unknown. The 24 visible-derived symmetry probes are consistency checks, not independent Racket labels. No solve is admitted to training.

## D11 — Audit and return scope

Draw audit targets once, leave their source unchanged, and report source-bound findings separately. `50b436f101bb` includes accepted-domain reference failure, a color-frequency shortcut and ignored axis. `4e6862c442fd` includes a lawful override that defeats a motif-only rival. Neither rival fits its canonical demos; neither is presented as canonical ambiguity.

One supplied-builder ZIP contains the selected task patch and required reports/evidence. Fresh replay uses the original ZIP, declared runtime-closure scope and an independent environment. Existing shared evidence bundling/restoration already solves transport, so no redundant archive tool is added. The runnable parametric authoring tool and independent teaching tests remain reusable by future agents.
