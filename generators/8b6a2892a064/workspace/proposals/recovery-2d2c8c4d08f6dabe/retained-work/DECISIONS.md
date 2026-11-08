# Review decisions

## D1 — Canonical repairs preserve valid draws

Assignment review-5514f0db887fe386 concerns task 8b6a2892a064, original training parent f0f8a26d. Version is 4.1.0. The centered turn of odd straight lines, singletons, background 7, clipping behavior, and normalized canonical rule hash 83a9329e575d remain unchanged.

Exact integer seeds, including signed seeds, remain supported. Coercible/noninteger/boolean seeds and negative/noninteger/boolean indices now raise. The baseline reproduced 33 invalid scalar calls. The validator also now enforces a 30-by-30 grid limit; the 31-row counterexample is a retained regression.

The initial version bump changed the keyed RNG stream and caused the inherited diversity test to produce 499 unique inputs where it required more than 500. Rather than weaken that assertion or retune weights, SAMPLING_VERSION=4.0.0 preserves prior valid draws. Three independently obtained baseline input hashes failed before this fix and passed after it. Public-anchor weights, geometry, overrides, and generalized support are unchanged.

## D2 — Exact active authority, preserved archival history

The before battery found two exact active-source text groups with identical normalized semantics. Stock authority-sync changed only /racket_target/target_code in the two permitted base solution files. Canonical text, normalized rule hash, and archival raw_code strings remain unchanged. Recovery snapshots were relocated intact to checks/authority-recovery/. Portable task tests require exact target equality and normalized archival equality; the old raw equality assertion was already false in the supplied baseline.

## D3 — Executable teaching limits

Added identity, horizontal-only, vertical-only, and short-line-skipping rivals plus nonmutating witnesses. EXAMPLES_NEEDED=3 declares an export/audit default, not a guarantee that any three random demonstrations teach every nearby alternative. There is no cyclic schedule declaration and no arbitrary-rotation guarantee.

The final 100-per-band census has 300 lessons, 1,200 Racket-labeled pairs, and 1,049 unique inputs. Two raw materialized lessons and three rotations remain ambiguous. The existing worker already rejects such findings under automatic demonstration policy; explicit-count diagnostic routes can retain them, and missing contracts produce not_declared. The open admission issue is to require nonvacuous executable contracts across routes. Increasing demonstrations until a finite census happens to pass would not establish a general guarantee. A proposed task-local gate instead rejects surviving rivals that disagree on any query. Its CLI uses supplied upstream Racket labels and does not claim to relabel them.

## D4 — Six meaningful proposed rule settings

Parameters: rotate_when in {all,horizontal,vertical}, min_length in {3,5}, fixed once per episode. Default all,3 matches canonical behavior. Object extraction, orientation and length recognition, centered rotation, and compositing remain the reasoning structure. Background and foreground colors remain input-domain choices. Turn direction is rejected because clockwise/counterclockwise centered turns of a straight line are observationally equivalent. Arbitrary thresholds and diagonal modes are unsupported and rejected.

The prototype uses separated zones containing h3, h5, v3, v5, and a singleton, with varied sizes, colors, positions, and edge clipping. This deliberately narrower distribution makes all six settings distinguishable; it is not a replacement for the broader canonical sampler. Input domains do not depend on the setting.

Retained evidence uses three demonstrations and four distinct queries for each setting. All labels and alternative-setting predictions execute the corresponding emitted Racket. Filtering completes before query evaluation. Public payloads and names contain only visible material; hidden settings, references, answers, source hashes, and execution receipts remain private. Sampling is bounded and raises instead of returning clones or shortened episodes.

All six settings use the same seed and seven input draws as a controlled comparison. Each episode has seven distinct inputs; the batch does not have 42 globally unique inputs. Tests cover default parity on all four unique canonical inputs, clipping, selection, independent counts, invalid controls, and public-name stability. These variants are proposed prototypes, not approved production rules.

## D5 — Portable and reusable tools

Task tests use reviewer_support to resolve packet/source identity. Frozen shared fixtures remain unchanged. The prototype test loader compiles explicitly read bytes so cached timestamp bytecode cannot contradict its source hash. The optional task-local memory-safe extractor validates the manifest, hardlinks only protected immutable duplicates, and has 15 synthetic adversarial tests. It is not installed into the shared runtime.

An initial census lost its Racket child under memory pressure and recorded 201 downstream failures. The failure remains retained separately from the successful 300-lesson retry. Unchanged historical files staged out temporarily must be restored byte-for-byte before official packaging; the uploaded ZIP is untouched. Resource exhaustion blocked that restoration, and the runtime was subsequently OOM-killed. The checkpoint recovered source and decisive evidence; see REVIEW.md for exact recovery limits. Compressed evidence carries original-size/hash mappings and restoration instructions.

## D6 — Solves, audit scope, and acceptance

The preliminary second-task solve used visible examples before reference exposure. The later main solve declares earlier exposure yes and reference consultation during the solve no. Hidden query correctness is not claimed where the checker masks it.

The drawn audits are findings-only: 26cfe7595a4a has ignored/inconsistent controls and a representation gap; 735ba14c7162 has false canonical-shortcut assertions, fixed-depth test paths, and scalar gaps. Their sources/approvals remain unchanged. The allocation audit is a bounded cost/quality proposal and preserves draw probabilities.

Acceptance needs attention because canonical lesson ambiguity remains. Passing checks and runnable tools do not establish universal identifiability, new approval, dataset admission, or a measured Qwen gain.
