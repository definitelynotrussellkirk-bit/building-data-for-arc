# Feedback to Codex

## F1: Require a nonvacuous lesson contract at admission (highest priority)

Affected paths: repo/src/arcpuzzles/worker.py::lesson_check, approval/admission policy, and dataset export routes. The existing worker already tests declared rivals for each query and rejects findings when demonstration_policy.automatic is true. Reuse that mechanism. The missing requirement is that an admitted generator must provide a meaningful executable contract, with the same obligation on explicit-count/diagnostic routes. The supplied approved main generator had no contract; the before semantic stage reported NO_CONTRACT.

The repair adds four executable nearby rivals. A 300-lesson census then finds two raw materialized lesson windows where skip_short_lines fits every demonstration but disagrees on the query. Automatic production with the repaired declarations can reject such lessons; an explicit-count diagnostic route can still return a diagnostic verdict, so admission must distinguish these states. Do not count diagnostic_unsupported, not_declared, or an unexecuted contract as a semantic pass.

Included task-local tool: generators/8b6a2892a064/workspace/lesson_gate/gate.py, with nine focused tests and a README. It freezes demo-consistent rivals, checks every query, rejects missing/duplicate/malformed data, records exact source and upstream-receipt hashes, and expressly does not reexecute labels. It passes the retained 3-demo/4-query production episode and rejects the retained real ambiguous lesson. Evidence: checks/four-query-gate.json, checks/ambiguous-episode-gate.json, and checks/lesson-census-brief.json. It is optional tooling, not a shared-runtime patch or new training approval.

Cheapest acceptance probe: run those two retained episodes through the gate. Also reject an empty declaration and require distinct inputs. Any Qwen quality benefit remains an experiment, not a claimed model result.

## F2: Resource-aware packet extraction

Affected entrypoint: full packet extraction/verification. This request has 105,426 ZIP members and 1,747,257,654 uncompressed bytes. A full normal-disk extraction encountered ENOSPC; memory pressure also interrupted Racket work. An unchanged full-history packet can dominate resources needed to review one task.

Included optional utility: generators/8b6a2892a064/workspace/packet_tools/memory_safe_extract.py, README and 15 synthetic adversarial tests. It verifies original manifest bytes; rejects traversal, duplicate entries, symlinks, hash mismatches, missing files and illegal directory payloads; hardlinks exact immutable duplicates; isolates declared editable tasks and shared data; provides verify and detach. It is not constant-memory: central-directory, manifest, and hash indexes scale with file count, and hardlinks do not eliminate all path inode costs. Consider integrating this supported extraction mode, plus disk/inode/available-memory preflight, rather than asking future reviewers to reconstruct these safeguards.

This review used stock extraction, then exact-byte immutable deduplication and temporary staging of historical evidence to run checks. Original files must be restored and verified before a valid return can be built. The uploaded archive is unchanged. No full runtime, duplicate repository, or dependencies belong in the return.

## F4: Fail cleanly after a Racket child dies

Affected tool: Racket bridge recovery and census materialization. The first retained census materialized 99/300 lessons, then recorded a dead Racket child followed by repeated __pg_rule undefined errors; 201 lessons failed materialization. The environment reported OOM events. This is distinct from the two semantic ambiguities in the successful 300-lesson retry.

Evidence: checks/lesson-census.json.gz and checks/lesson-census-console.log. Proposed bounded test: kill the child after one successful rule load, then make one more request. Either rehydrate the exact selected rule before continuing, or stop with a single infrastructure failure and an explicit unattempted remainder. Repeating thousands of missing-binding calls obscures the initiating failure. This is a shared-tool proposal; no bridge implementation was edited.

## F5: Keep supported authority-sync recovery outside forbidden source paths

The stock authority-sync command legitimately repaired two assigned active target_code strings and preserved raw_code. It also left recovery files under repo/var/review/authority-sync and a repo/REVIEW/.lock. The return scanner rejects new paths there. Recovery was moved intact into checks/authority-recovery/ and the unlocked lock file into checks/authority-review.lock. Have the command use a return-compatible evidence directory or advertise that required relocation. Also prefer portable reviewer_support fixtures and exact-byte compilation for task-local tests.


## F6: Make long reviews resilient to workspace loss

The private review process eventually exited 137 under shared memory pressure. A small checkpoint ZIP preserved the final generator, prototype, complete before/after battery evidence, census, solves and audits, but later task-test logs and the random audit seed had not yet been copied. The return includes explicit recovery provenance and never fills those gaps with invented evidence. Future packet tooling should checkpoint assignment contracts immediately and retain source changes, command receipts and completed evidence outside the execution runtime at bounded intervals. The included finish_return.py reconstructs the full workspace from the original ZIP plus scoped reviewed overlay, verifies original baselines, and invokes the unchanged stock return builder. Its synthetic guard tests do not substitute for a completed real-archive return/replay.


## F3: Randomized allocation and data-quality audit — prioritize source-bound teaching evidence alongside original-family parameterization

**Reproduction and scope.** I used `random.Random(int(seed, 16)).sample(sorted(manifest["generators"]), 3)` with audit seed `7eddf4041ed941716d0920e4b429c0ef52ab9f9a183d5a91f729c23f17543be6`. The sampled IDs, in draw order, were **`86fdc171c075`, `079291c08c15`, `be02b305dd1e`**. Inspection was read-only and selective within the supplied ZIP; no generator execution, corpus-wide check, model job, or policy change occurred. All paths below are ZIP-relative.

### Actual allocation differs from dataset weighting

`WORK/PACKET-MANIFEST.json` contains **3,941 generators, 1,571 approved generators, a 250-ID normal authoring pool, and a 252-ID main-pool union**. All 250 normal IDs are approved original training-task families currently lacking qualifying parametric evidence. The priority metadata separately records 555 original families needing repair and parameters, 1,767 other unapproved families, and 198 current prototypes; these are authoring classifications, not quality measurements.

The public-evaluation focus probability is exactly specified as `1/10`. Its 120 anchors contain only **one mapped task**, `evaluation:5545f144`, with `generic_waypoint_route_gen1` and `generic_waypoint_route_gen2`. The remaining **119 anchors use `inspired_extension` on the normal-priority target**. `WORK/repo/src/arcpuzzles/review_full_draw.py`, `main_selection_for_seed`, implements this fallback. Thus, under the intended uniform-seed interpretation, approximately **99.9167% of selected main IDs remain in the 250-ID normal pool**, although **10% of assignments still receive an evaluation reasoning focus**. Only about **0.0833%** select a directly related waypoint generator. This distinction matters when interpreting “10% evaluation coverage.”

Dataset sampling is separate. `WORK/repo/catalog/puzzles.jsonl` has `mix_weight=1.0` on 3,925 records and `0.0` on 16; **every one of the 1,571 approved records has weight 1.0**. Default weighted export therefore gives equal *attempt* weight to eligible IDs in this snapshot, subject to filters and subsequent rejection/deduplication. The sampled frame generator has weight 1.0 but is **unapproved**, so its positive weight does not admit it to default export. `catalog.py` enforces approval and `datasets.py` applies the eligible-pool weights.

Representation is uneven by design: the normal authoring pool is entirely training-origin; the approved catalog contains 1,113 bank-source records, 448 training-source records, and 10 custom-source records. Augmented tags overlap these categories. **All three random catalog rows are bank-tagged; no identified ARC-GEN or RE-ARC example was inspected. A bank tag does not establish exhaustive upstream provenance, so this audit supports no recommendation to increase or decrease those external sources.**

### Sampled evidence and concrete coverage limits

| ID | Observation grounded in retained source/evidence | Allocation implication |
|---|---|---|
| `86fdc171c075` | Current `generator.py` v1.1.1 constructs strictly nested rectangular frames. It declares eight axes, including constant controls and an unused `palette_kind`; band-local size draws contradict the global advertised bounds. Its exact-source `evidence/review_index.json` retains an accepted audit: `generate(0,0,typo=1)` was accepted, easy `grid_h=18` rejected, and `palette_kind="warm"` ignored. These are **inherited, reviewer-reported reproductions**, supported by current source inspection. Ordinary nesting makes “fill the inner frame interior” answer-equivalent to intersection on generated inputs; it provides no evidence for distinguishing more general intersection reasoning. No parametric prototype, lesson-rival contract, or four-query receipt was present in the sampled home. | Repairing observable controls and clarifying the lawful geometry can prevent wasted review and labeling. More samples from the same nested construction would not establish broader reasoning coverage. The record remains outside default approved export. |
| `079291c08c15` | Current v4.0.0 enforces two distinct-shape objects, complete disjoint translated footprints, and exact size overrides. Retained associated notes report baseline linked-lawfulness **292/900 despite green generic defect/distribution gates**, improving to **900/900** after repair; reported override findings fell from **360 across 2,610 draws** to **0 across 810 draws**. The source rejects identical normalized shapes to defeat a color-swap-in-place shortcut, and task tests contain targeted third-object, clipping, overlap, and same-shape negatives. `EXAMPLES_NEEDED=4` exists, but the source declares no lesson-rival hook and the sampled home contains no parametric or four-query receipt. | Existing approval and per-input semantic checks are useful foundations. A small, source-bound four-query lesson qualification is a better next marginal investment than assuming per-input validity proves lesson identifiability. |
| `be02b305dd1e` | Current v3.1.0 has twelve exact scene profiles, a four-demo schedule, explicit solid-fill and smallest-magenta rivals, and a hook checking ordering/layout/template-size evidence. Current notes report repair of **33 invalid-call acceptances**, a concrete ordering ambiguity at `seed=232922564183033`, medium, indices 33–37, and a final **300-lesson / 1,500-rotation census with no measured ambiguities**, with **1,498 unique inputs among 1,500 pairs**. These results are retained reviewer claims, not fresh execution here. Its approval explicitly says `reviewer_reported`. A retained source-bound solve summary demonstrates **four demos and two queries**, with per-query hook verdicts. The census was one-query based; neither establishes four-query execution. The notes report an aggregate-battery stall despite individually passing stages, including defect lint in 11 seconds. | This is the strongest sampled candidate for inexpensive four-query qualification: useful teaching contracts already exist. Preserve its finite rival-set limitation and reuse intact source-bound evidence instead of repeating an interrupted full battery by default. |

**Staleness warning grounded in this sample:** `shared/data/derived/generator_catalog.jsonl` describes versions 1.1.0, 3.0.0, and 2.0.0 respectively, while current sampled sources are 1.1.1, 4.0.0, and 3.1.0. Its lint warnings, “locked axes,” and diversity figures should not be treated as current measurements or used directly to set new weights. The current notes/tests are more relevant, but inherited numbers still require their stated verification status.

The selected task’s baseline, `8b6a2892a064` v4.0.0, is consistent with the current original-family priority: the manifest traces it to training task `f0f8a26d` and records prototype status `missing`. Its baseline source samples four exact public inputs plus eight generalized blueprints repeated three times in the choice list: **4/28 raw profile-choice mass is on exact public inputs**. This is a source-derived sampling fact, not an observed rejection rate; more queries increase the importance of accepted-input indices and deduplication. Baseline notes retain Racket-lint A012/A008 warnings attributed to the legacy wrapper and loop variable `kc`, despite reported execution parity. Any current prototype results belong in the separate, newly measured review evidence.

### Concrete alternative and bounded trial

**Proposal for a future allocation comparison; preserve the current policy now.** Keep the **10% evaluation-focus lane**. Compare the existing 90% original-family lane with an alternative allocating **60% of total assignments to approved original-family parameters, 20% to exact-source unresolved semantic/override defects, and 10% to approved families lacking four-query qualification**. The sample supports these additional work categories, but is too small to establish an optimal percentage.

**Cost estimate, not a measured speedup:** with four demonstrations, an episode containing four queries requires eight labels, versus twenty labels for four separately labeled four-demo/one-query episodes. Under equal per-input labeling cost and reusable demos, this is **60% fewer labels for four query targets**. Compared with one four-demo/one-query episode, label work rises from five to eight while query targets rise from one to four. Shared demonstrations also correlate the resulting targets; they do not create four independent tasks. Actual savings depend on rejection, deduplication, process overhead, and lesson validation.

A bounded proposed pilot is **20 assignments: ten current-policy controls and ten alternative allocations**. In each arm retain one evaluation-focus case; use nine original-family controls versus six original-family, two unresolved-defect, and one four-query-qualification cases. Cap exploratory qualification at **60 reviewer-minutes per case and 500 newly Racket-labeled inputs across the pilot**, using existing receipts first and at most two fixed seeds per band/setting. Record source hashes, accepted/rejected indices, unique lawful query targets, per-query declared-rival results, reviewer time, and Racket CPU time separately.

**Stopping rule:** quarantine a setting on the first confirmed label mismatch or demo-consistent rival that changes a query answer; stop at the time/label cap rather than adding volume. Retain the alternative only if its observed qualified unique-query yield per reviewer-hour improves by a prespecified **20%** without higher invalid/ambiguous acceptance or worse labeling cost per qualified query. That threshold is a proposed decision rule, not a statistical claim. Otherwise retain current allocation and diagnose the limiting category. No model-quality or broad source-quality conclusion follows from this pilot alone.

### Evidence identities

SHA-256 values below were computed directly from ZIP member bytes:

| ZIP-relative path | SHA-256 |
|---|---|
| `WORK/PACKET-MANIFEST.json` | `d6455f690c4ca33908aed3eada89e50d2dcac36352ad1bdde82b0f0f3d70cf12` |
| `WORK/repo/src/arcpuzzles/review_full_draw.py` | `ecd5853119409a1f28780b18ad6bdc1fb62ef7efd6af8de2e23d2855bfaaefc4` |
| `WORK/repo/catalog/puzzles.jsonl` | `bee6b7a6995a6bd2a2df930a3db5863e5a19ed110ec21b84bf5e5e41ae42ec2d` |
| `WORK/repo/src/arcpuzzles/catalog.py` | `789779b4d20976d253ef6a20892f8c0064e25d3790fbe2d4aa5b14982bdbfdbe` |
| `WORK/repo/src/arcpuzzles/datasets.py` | `b26a88742792672593bf04da0ed1c6ca5b8f4b77b742f6d8663bb7fd1102792d` |
| `WORK/repo/shared/data/derived/generator_catalog.jsonl` | `dad563db7a6ecd747e7594d1945965d0cd893e028219dc348547ec636d43a17d` |
| `WORK/repo/generators/86fdc171c075/generator.py` | `0ac8c3ccf3e1687c26519f50b4ca347587233d0042336a18ae3b6a7e9fe49fe3` |
| `WORK/repo/generators/86fdc171c075/evidence/review_index.json` | `da339e13ff7c469a2c389255f815de39d62eefa3e48c4820b46cd58f2d476a4b` |
| `WORK/repo/generators/079291c08c15/generator.py` | `829127effec54e6acb88e0ebfa853ad8bc4a82339eae3bb3287f6f30b5d190a3` |
| `WORK/repo/generators/079291c08c15/evidence/associated_notes.jsonl` | `0254ab1bd7cdccced7abb8ef8cca25a2f797bbcb301504642e276aa895e65ffc` |
| `WORK/repo/generators/079291c08c15/tests/test_generator_079291c08c15.py` | `a7fe2fb1b53613c0d00d28408ddce5b1928a7523a603baa34d555df9d83c1702` |
| `WORK/repo/generators/be02b305dd1e/generator.py` | `b70ae4e93b362406f3233b4de9d019f8a51ec3c98f176ee35b70b368839e12ee` |
| `WORK/repo/generators/be02b305dd1e/notes.md` | `0d313d8c3d740da2aca8eaf38dc58ffb2ad06f94cd4240214b7f510251ae04bd` |
| `WORK/repo/generators/be02b305dd1e/tests/test_generator_be02b305dd1e.py` | `5150c2029d66e62946698690ac70b03a0010b5f6bbdf6175116bf7a4191cab71` |
| `WORK/repo/REVIEW/approvals/99c1254dff6ab9b4f927925d5835e59c9de7541c0562e734a315cec0563b4961.json` | `a71a61d7e19e3e15e80b9dd4c6e668da788904305cdec2ae72a201a5dcf53667` |
| `WORK/repo/generators/be02b305dd1e/evidence/reviewer-solves/contexts/32537ac462815e7eae8773a77b01b711d63e760802236e54949b5fc5d309fa44/summary.json` | `32537ac462815e7eae8773a77b01b711d63e760802236e54949b5fc5d309fa44` |
| `WORK/repo/generators/8b6a2892a064/generator.py` | `7b70d101c08c1389680591f2d5f203ad54067525ea783199e4e4b8d6e59b4c4b` |
| `WORK/repo/generators/8b6a2892a064/evidence/associated_notes.jsonl` | `7ec54f2a6881bcb062be86be3018cb1854c63a45ee4ca0e42c77be705a8e24ce` |
