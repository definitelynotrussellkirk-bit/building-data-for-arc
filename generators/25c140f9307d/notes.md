# Working notes: 25c140f9307d

## Current reviewed source

- Generator version: `2.2.0`.
- Generator SHA-256: `54b23214fb0859e439499af592ce8c7b9c3afa4d474d7267f91a8168e1654fb6`.
- Canonical Racket rule hash: `fafb0679bd1e`; canonical program file SHA-256 remains `0600844f7e924d92c384409bd4741b516ff057670e09186d6fed9ed7150d19d0`.
- This review does not grant approval or training admission.

## Repair decision

The prior generator advertised `rect_size` but ignored it, placed its keys close enough to merge into one 8-connected gallery object, and used identical 2×2 tooth shapes. On a representative generated input, the protected canonical rule therefore found no usable one-key-per-hole matching and left holes unfilled.

The repair generates two to four pairwise rotation-distinct four-cell hole/key shapes, separates every 3×3 key object by a full blank row, and makes `rect_size=9..14` and `n_keys=2..4` strict exact controls. Default sizes remain difficulty-aware and may be rectangular. `self_check` now validates the rule-consumed structure while deliberately remaining broad enough to own all four canonical inputs.

## Evidence and limits

- Focused regressions cover key separation, unique shape matching, strict numeric boundaries, deterministic/fresh generation, process-RNG purity, validator rejection of a bridged gallery, and canonical-input ownership.
- Protected Racket filled every hole and preserved every payload color on exact `(size, keys)` boundaries `(9,2)`, `(11,3)`, and `(14,4)`; a separate 32-case census covered eight samples in each difficulty band.
- The generated subfamily uses four fixed tetromino templates and two payload cells per key. The canonical family is broader; no claim is made that this sampler spans all canonical geometry or proves distributional quality.
- Next useful owner action: inspect the repaired lessons visually, then run the normal acceptance/training-admission process if this narrower but rule-faithful distribution is desired.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/25c140f9307d/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-02c4260a98c367b9:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `524e9f948170fd75c7c84e708165d6ebc2da759753f5b0f77f410d3e4ffbb19b`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

This same-batch peer finding binds older524e9f948...source. Accepted54b23214fb0859e439499af592ce8c7b9c3afa4d474d7267f91a8168e1654fb6 separates key galleries and uses distinct rotation-matched tetromino holes/payloads. Reviewer reports3boundary Racket cases and32adversarial cases filling every hole and preserving key payloads. The crop-only shortcut therefore no longer matches those labels. Finite four-shape grammar is retained as a limitation; no fresh owner execution.

### Assessment or prior finding

## 25c140f9307d

**Status:** source-bound finding; unverified until maintainer assessment. No peer source was changed.

Pinned generator `524e9f948170fd75c7c84e708165d6ebc2da759753f5b0f77f410d3e4ffbb19b`, rule hash `fafb0679bd1e`, was probed once at ticket seed prefix `0x13396e1413bf4906` (`1385259392902842630`) with two demonstrations and one query.

A lawful shortcut—crop the bounding box of the largest 4-connected red component and ignore all detached keys—matched the authoritative output on all **3/3 generated pairs**. The same shortcut failed all **4/4 canonical pairs**, differing by 18, 45, 9, and 36 cells. Thus the generated lesson makes detached key payloads non-causal even though key matching is required by the canonical task.

This is a teaching gap: a solver can fit every generated demonstration and answer the generated query without learning the key-to-hole stamping rule. A repair should force key payloads to change the cropped plate in demonstrations and should retain a crop-only rival in lesson/query-rotation checks.

Evidence: `checks/tickets/ticket-de71eebd94842323/episode.jsonl` and `checks/tickets/ticket-de71eebd94842323/analysis.json`.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.
<!-- arcpuzzles-current-audit-assessment:end -->

<!-- parametric-payload-policy-20261024:start -->
## Native parametric payload-policy prototype (2026-10-24)

- **Status:** reviewer-ready native handoff; owner acceptance remains pending and no training data is admitted. The approved canonical generator and canonical authority were not changed.
- **Rule family:** `payload_policy=preserve|swap`. `preserve` returns the exact canonical Racket bytes; `swap` keeps the same plate/hole/key matching and rotation, then exchanges the two oriented key-payload colors before stamping them. Inputs are paired across settings.
- **Counts and stress:** deterministic episodes support 2–6 demonstrations and exactly four distinct queries. Every episode contains one substantive 30×30 input with a 22×22 plate and four detached boundary keys; the Racket output is 22×22.
- **Teaching audit:** on four qualification-shaped episodes, the other declared policy plus crop-only and fill-red shortcuts matched 0 demonstrations and 0 queries. This is a bounded rival check, not a uniqueness proof.
- **Native evidence:** qualification covered both settings at seeds 0 and 17, with 40 protected-Racket evaluations and the requested setting as the sole demonstration survivor. Receipt: `checks/25c140f9307d/qualification/qualification.json`; execution: sibling `execution.json`.
- **Sequential dependency:** A matches and orients a key to a hole; the intermediate is the key identity, rotation, offset and oriented payload targets/colors; B consumes those targets to fill/stamp, optionally swapping colors. `checks/25c140f9307d/dependency.json` records one qualified `swap` case whose protected-Racket skip-A counterfactual changes the final output.
- **Public boundary:** the retained public projection contains only demonstration inputs/outputs and four query inputs. Altering private settings, program and query answers leaves its exact visible bytes and ID unchanged.
- **Checks:** 33/33 target tests and 96/96 focused native framework tests pass. A separate maximum-boundary run (`seed=2^63-1`, six demonstrations, four queries) added 32 protected-Racket evaluations, with each requested policy the sole demonstration survivor. Task-local source inventory: `workspace/parametric/evidence/manifest.json`.
- **Limits / next action:** finite seeds and rivals do not prove universal identifiability or learning benefit. After integrating these exact bytes, the owner must rerun native qualification and protected witness replay, inspect the causal claim, and perform fresh acceptance if satisfied.
<!-- parametric-payload-policy-20261024:end -->
