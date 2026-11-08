# Working notes: b9b63ae52d91

## Current native decision — paired-component row relay

The native `mode` family preserves vertical bytes, retains the horizontal
variant and adds `paired_rows`: classify reflection partners, select the largest
red 4-component (row-major ties), and recolor gray cells in its rows to yellow.
This uses the post-classification topology, not original cyan connectivity.
Production generator/canonical authority remain unchanged. The two-demo finite
cover is built from a bounded matched-input bank; a constructed dense-vs-L
witness repaired a bounding-box shortcut at seed 17. The original public report
leaked its hidden axis; public serialization and the retained example are now
strictly projected, with a hash-named public copy. A sanitized legacy filename
remains an authoring-only compatibility alias, not a model-facing export. Tests cover those regressions and API limits.

Current receipts are in `WORK/checks/b9b63ae52d91/`: 47 scoped tests plus 19
subtests; 32-seed, 480-episode finite audit with 49 protected-Racket evaluations.
Native owner acceptance is pending. Bounds are explicit; no universal uniqueness
or training-admission claim. Author self-review only, no independent reviewer.

## Intended rule and authority

For every cyan (`8`) input cell, inspect the cell in the same column reflected
across the horizontal midline.  Recolor the cyan cell red (`2`) when that
vertical mirror partner is cyan and gray (`5`) otherwise; every black (`0`)
cell remains black.  Odd-height middle-row cyan cells are self-mirrors and are
therefore red.  The selected Racket authority and `RULE_HASH=46194ba2dd2d` were
not changed in this review.

## Current generator design (version 2.1.0)

The generator has two explicit input families.  `linked` preserves one of the
five public 6×6 occupancy patterns under legal row automorphisms and column
permutations.  `generalized` varies height, width, occupancy and the number of
vertical pairs while retaining both paired and asymmetric cyan witnesses.  The
natural prior is now three `linked` choices to six `generalized` choices
(one-third linked); an exact `scene_family` override remains available.

The generator validates `seed` and `sample_index` as non-Boolean, nonnegative
integers before constructing its context.  `strict_canonical_like` reuses the
same lawful-domain analysis as `self_check`.  The declared
`horizontal_mirror` rival changes only the reflection axis; the
`vertical_not_horizontal` witness fires exactly where that rival predicts a
different answer.  `lesson_identifiable` rejects an episode when the horizontal
rival fits every demonstration but changes the query.

## Review decisions and evidence (2026-10-20)

- Baseline defect lint accepted Boolean/float/string/negative scalar controls.
  The focused regression now covers both public scalar arguments and defect
  lint is clean (`checks/focused-defect/`).
- Baseline pinned canonical-profile support was 12/60 (20%).  The small prior
  change raises the final pinned census to 20/60 overall, with support in every
  band (`checks/focused-profile/`).  The linked family remains a minority and
  the 800-draw-per-band diversity test still requires at least 480 generalized
  examples.
- The prior source had no executable semantic contract.  The final focused gate
  reports 600/600 strict inputs, one witness firing in every band, 60/60 checked
  rival claims, 12/12 production lessons identifiable and 72/72 diagnostic
  query rotations unambiguous (`checks/focused-semantic/`).
- The inherited task test used a fixed `parents[1]` root and failed before
  collection in the portable runtime.  It now uses `reviewer_support.find_root`,
  `canonical_path` and `load_selected_generator`.

## Parametric extension (proposed, not canonical)

`workspace/parametric/` contains a runnable two-setting `mirror_axis` prototype:
`vertical` is the canonical default and `horizontal` is the proposed alternate.
The setting is chosen once per episode.  Three demonstrations and the query are
required to distinguish the rival.  Both complete Racket programs are executed
and checked against an independent Python implementation; retained evidence is
under `checks/parametric/`.  Acceptance of the generator repair does not approve
this proposed horizontal-rule curriculum.

## Known limits and open findings

The lawful-domain checker intentionally accepts generalized binary grids beyond
the five public profiles, so it is a rule-domain checker rather than a claim of
exact public-distribution identity.  The horizontal rival is a strong local
competitor but not an exhaustive list of all induction shortcuts.  The
parametric extension has one retained deterministic episode; broader admission
would need multiple seeds, setting balance and downstream policy review.

Imported associated notes retain original evidence/timestamps in
`evidence/associated_notes.jsonl`.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-7719bd275d086941:v0001`. Disposition: **no_issue**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `da62244ece41e9be9555fac8f2313b448d734d07f19732d1d1cbd9723ce02452`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Historical bounded no_issue on da62244e only:5unique canonical inputs/10 occurrences and600 generated samples,6candidate rivals refuted. This did not cover scalar contracts/portable tests/profile-floor balance found by new repair. Current684f08a4 has separate35 tests/12-stage battery and300lessons/1800rotations; no transfer of old verdict to new bytes or universal coverage.

### Assessment or prior finding

## b9b63ae52d91

No issue found after checking all five unique canonical inputs (ten train/test occurrences) and 600 generated samples: 100 each for `linked` and `generalized` across easy, medium, and hard. Every sample passed `self_check`.

I tested plausible rivals for horizontal reflection, 180-degree reflection, “any other cyan in the same column,” “cyan in the opposite half of the same column,” adjacent same-column matching, and treating odd-height axis cyan as solo. Generated witnesses refuted each. In particular, `generate(555, 1, difficulty="medium", scene_family="generalized")` contains an axis cyan at zero-based `(6, 0)` that correctly becomes red 2, ruling out the axis-as-solo shortcut.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-7719bd275d086941-v0001/audit_assets.json), manifest SHA-256 `2aa9871442bc0a04bd3c0808fc86bd0df851f79e734ca5a09d9257a5c283ab12`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `684f08a4cb2e1843c602830e1b3415453b582937416ebb3006cf1acb0fd7cc3e`.

# Decisions for b9b63ae52d91

## D1 — Keep the canonical Racket rule unchanged

**Choice.** Preserve the selected vertical-mirror rule and
`RULE_HASH=46194ba2dd2d`.

**Rationale.** Canonical pairs, rule smoke and authority synchronization passed
at baseline.  The observed defects were generator/test-contract defects, not a
label-authority defect.

**Rejected alternatives.** Rewriting the Racket for style or embedding the
horizontal variant in the production path would create unnecessary authority
risk.  The alternate rule remains isolated under `workspace/parametric/`.

## D2 — Reject invalid scalar controls at the public boundary

**Choice.** Require `seed` and `sample_index` to be non-Boolean, nonnegative
integers before calling `gen_ctx`.

**Original state.** Boolean, float, string and negative values were accepted or
failed indirectly; baseline defect lint reported 33 strict-scalar findings.

**Evidence.** `tests/test_review_repairs.py` exercises both arguments.  See the
red run in `checks/task-tests-red2/` and the green focused/final task-test runs.

**Limit.** Difficulty and axis validation retain their existing explicit
contracts; this change does not attempt to redefine the shared context API.

## D3 — Raise canonical-profile support with the smallest distribution change

**Choice.** Change the natural family list from 3 linked : 7 generalized to
3 linked : 6 generalized (one-third linked), and bump the generator version to
2.1.0.

**Rationale.** Baseline pinned support was 12/60, below the required 25% pooled
envelope floor.  Probe matrices in `checks/probes/profile_ratio_probe_v210*.json`
showed that 3:6 clears the floor while preserving a strong generalized majority.
The final focused census is 20/60 and every band has support.

**Rejected alternatives.** A 4:6 split over-weighted linked scenes and caused an
existing 800-draw generalized-floor regression.  Merely changing the version
while retaining 3:7 would reshuffle pinned samples without materially improving
the prior and was rejected as seed-fitting rather than a distribution repair.
Larger 4:8 or 5:9 lists passed but added no semantic benefit over the simpler 3:6
ratio.

**Failure mode.** This floor is profile-level, not proof that every generated
lesson resembles a public input.  Generalized geometry remains intentional.

## D4 — Declare one executable semantic rival and a lesson gate

**Choice.** Add a left-right `horizontal_mirror` rival, a
`vertical_not_horizontal` witness, a strict lawful-domain hook and
`lesson_identifiable`.

**Rationale.** The alternate axis is a plausible, structurally close shortcut:
it preserves colors and paired-versus-solo classification while changing only
the coordinate relation.  It therefore tests actual reasoning rather than a
trivial constant-output rival.

**Evidence.** `checks/focused-semantic/` verifies the claim on exact generated
inputs and Racket labels: 60/60 sampled rival claims, 12/12 production lessons,
and 72/72 diagnostic rotations.

**Limit.** Passing this finite declared-rival gate does not establish universal
identifiability.

## D5 — Repair the portable test, not the task-test harness

**Choice.** Replace fixed parent-depth and private generator imports with the
public `reviewer_support` helpers in the selected task test.

**Rationale.** The first official task-test attempt stopped before collection
because the copied runtime has a different directory depth.  The packet's own
preflight identified the exact unsupported pattern.

**Evidence.** `checks/task-tests-red/` records the preflight failure;
`checks/task-tests-red2/` then reaches the intended red regressions, and later
runs pass.

## D6 — Prototype `mirror_axis` as a separate episode-level parameter

**Choice.** Provide `vertical` and `horizontal` complete Racket settings under
`workspace/parametric/`; choose one once from the episode seed; require at least
one distinguishing demonstration and a distinguishing query.

**Rationale.** This is a small, lossless parameter that preserves object roles,
palette and reasoning structure.  It changes the rule rather than merely
reskinning colors.  The canonical default remains vertical.

**Evidence.** `checks/parametric/seed-20261020-evidence.json` records accepted
sample indices, exact source hashes, Racket/Python parity, and distinct demo/query
answers.  The public companion omits the query label.

**Rejected alternatives.** Output-color parameters were cosmetic; density and
shape parameters already belong to the generator rather than the rule.  A
per-example axis choice was rejected because it would make demonstrations
internally inconsistent.

**Admission status.** Proposed only.  It is not selected production behavior and
needs broader seed/setting coverage before any training admission.
