# Working notes: 05409de4bec8

## Final selected repair

- Version: `5.0.0`.
- Final generator SHA-256: `eb5433a5ff10d59419a771cf02ca4378fcbaffdb2835599c86fe160c6fb37fc9`.
- Canonical Racket authority is unchanged at `RULE_HASH = dfbf6efa8173`.
- Prior return used as a lead: `review-60f56bb20c97f41b:v0001`. Its retained `all_pair_lines` ambiguity motivated the rectangle witness; its measurements were not treated as current-source measurements.

## Baseline findings

1. `seed` and `sample_index` accepted booleans, floats, strings, and negative values. The before battery failed `defect_lint` with 33 strict-scalar findings.
2. The generator declared no semantic contract. A four-demo lesson could omit the rectangle exception, allowing `all_pair_lines` to fit the demonstrations while changing a rectangle query.
3. A stronger canonical-fitting shortcut, `single_pair_per_axis`, matches all eight canonical labels. It preserves the rectangle exception but emits only the first exact pair row and first exact pair column for non-rectangles.

## Repair choices

- Reject non-plain and negative scalar arguments.
- Declare executable semantic rivals, witnesses, and `lesson_identifiable`.
- Use a five-slot ordered curriculum: `rectangle_a`, `multi_row`, `rectangle_b`, `multi_col`, `cross_anchor`.
- Keep four demonstrations and one query. Every four consecutive slots contain at least one rectangle witness and one multiple-parallel-line witness, so every one-query rotation refutes both named shortcuts.
- Preserve explicit `scene_family` overrides as exact controls; the schedule guarantee applies to ordinary default generation, not to a caller that deliberately overrides the family.
- Preserve complete public-profile support while making ordinary default support roughly one quarter of draws through two 1/8 rectangle slots plus the always-public cross anchor.

## Parametric prototype

`workspace/parametric/` contains a separate, unapproved `rectangle_policy` prototype with settings `longer` (canonical default) and `both`. The setting is fixed once per episode. Each retained episode has five demonstrations and four distinct rectangle queries; all labels and rival predictions were executed through the bundled Racket bridge.

## Test-scope correction

I initially placed new regressions in the inherited root task test. That file is frozen by this assignment. I restored it byte-for-byte to baseline SHA-256 `380a0e2a11f4216cfd8d62c7c9c6d812bed4492cf6fb0e1c99ba94f9cfce2ea2` and moved all new regressions to `tests/test_review_regressions.py`. The portable aggregate remains blocked because the frozen fixture itself uses a fixed `__file__.parents[...]` canonical-data path; the assignment explicitly forbids repairing that inherited fixture here.

Imported associated notes retain their original evidence and timestamps in `evidence/associated_notes.jsonl`.


## External prototype export correction

- Resolved the retained `external_correction_pending` finding from `evidence/parametric-external-followup-7fe75b0957073e34/manifest.json` in the task-local prototype verifier; the production generator and canonical Racket authority remain unchanged.
- Public bytes and full 64-hex IDs now come from `reviewer_support.public_challenge_bytes` / `public_challenge_id`. The verifier validates both settings first, rejects duplicate visible payloads, preflights every destination, then writes the batch sorted by public ID. Hidden setting order, seed, program, private metadata, and query answers cannot determine public names or creation order; a late collision cannot leave a partial batch; the setting map is private.
- Focused regressions: `18 passed` in `tests/test_parametric_rectangle_policy.py`, including reversed-setting enumeration, private-data invariance, visible-channel sensitivity, duplicate rejection, exact-byte writes, and all-path overwrite preflight before
  any file is created.
- Racket-backed evidence: `WORK/checks/parametric/rectangle-policy-public-writer-v4/` has five demonstrations and four distinct queries for each setting, all labels and rival predictions executed through Racket. Public write order is `f4ef...` then `fbba...`, which is ID order rather than the verifier's private `longer`, `both` iteration order.
- Independent receipt: `WORK/checks/parametric/rectangle-policy-public-writer-v4-independent.json` confirms each filename ID equals SHA-256 of the exact written bytes, payloads contain only visible train/test fields, counts are independently 5+4, all four queries are distinct and disjoint from demonstrations, the current verifier hash matches, and the manifest is complete and exact. The checker is retained as `WORK/checks/parametric/verify_public_evidence.py` for future packet agents.
- The `rectangle_policy = longer | both` extension remains **proposed and unapproved**. Evidence is finite for two retained seeds and one declared rival; no production battery was rerun because selected generator behavior did not change.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-60f56bb20c97f41b:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `badff0c622a568bc992a75b2ab5712c7597fea0eb6c8ae64355a23bdba7d02b7`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

CurrentgeneratorSHA256 eb5433a5ff10d59419a771cf02ca4378fcbaffdb2835599c86fe160c6fb37fc9 explicitly addsall_pair_linesrival, rectanglewitnesses andfive-slot duplicatedrectanglecurriculum. Reported12stagebattery,300lessons/1500rotations andall15seed0starts/75rotations distinguishrectangleexception;focused28mutabletests pass. Resolveonlyearlierrectangle-special-caseambiguity onbadff0c622a568bc992a75b2ab5712c7597fea0eb6c8ae64355a23bdba7d02b7. Frozenportablefixtureblocker remains; no owner rerun or universalclaim.

### Assessment or prior finding

## 05409de4bec8

**Classification: reproduced teaching ambiguity for the rectangle special case.**
Generator SHA-256
`badff0c622a568bc992a75b2ab5712c7597fea0eb6c8ae64355a23bdba7d02b7`;
rule hash `dfbf6efa8173`. The target was not edited.

The intended rule draws full lines through rows and columns containing exactly
two cells of the four-cell target. Rectangle scenes are exceptional: only the
longer axis is drawn. A plausible rival omits only that exception and always
draws every exact-pair row and column. It is identical to the authority on all
non-rectangle patterns and differs on legal unequal-span rectangles.

The fresh probe sampled 900 production-shaped five-pair lessons—300 per band,
four demonstrations and the fifth pair as query. In 74/900 lessons the four
demos were all non-rectangles while the query was a rectangle, so the rival fit
every demonstration and changed the Racket-labelled query. Counts were 27 easy,
22 medium, and 25 hard. Rotating every materialized pair through the query
position produced 354/4,500 ambiguous rotations (111 easy, 122 medium, 121
hard).

The retained representative is easy, seed 730000, sample indices 0..4. The
rival agrees with the supported Racket outputs on all four demonstrations and
differs on the fifth rectangle query. All five inputs return no `self_check`
errors and belong to the documented public/generalized scene domain. The Racket
replay matches the generator's Python mirror for all five pairs.

The full audit battery collected all stages: 11 are green and `semantic_gate`
fails because the source declares no `strict_canonical_like`, semantic witness,
or lesson-identifiability contract. This loud failure is consistent with the
concrete ambiguity rather than being the sole basis for it.

Evidence:

- `checks/audit/05409de4bec8/probe_rectangle_rival.py`
- `checks/audit/05409de4bec8/probe.json`
- `checks/audit/05409de4bec8/probe.stdout.json`
- `checks/audit/05409de4bec8/inputs.json`
- `checks/audit/05409de4bec8/racket.json`
- `checks/audit/05409de4bec8/battery/checks/05409de4bec8_after_semantic_gate.log`
- `checks/audit/05409de4bec8/battery/checks/05409de4bec8_after_battery_summary.json`

Scope: the rival tests one omitted special case under a fixed-seed,
consecutive-index assembly. It does not claim that every lesson is ambiguous or
that other undeclared rivals survive. A repair should add the rival to a semantic
contract and either guarantee a rectangle witness among the four demonstrations
when a rectangle can be queried, or change lesson assembly/resampling so the
special case is taught.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-60f56bb20c97f41b-v0001/audit_assets.json), manifest SHA-256 `3758f271b8722b610f337d07fe4f4f24d597fb2ec3355761708eaa92e668723c`.
<!-- arcpuzzles-current-audit-assessment:end -->
