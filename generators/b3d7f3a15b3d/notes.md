# Current working notes: b3d7f3a15b3d

## 2026-10-23 review-b248ec296d74f803 — proposed prototype public-ID correction

The production generator remains byte-identical at SHA-256
`e1d8f2ffd5cf0a2329ca1c3cede73a2333a5cc6afbdc906bc143015a210b4ce5`;
the canonical `RULE_HASH=032c15e97118` and its Racket text are unchanged. This
review changes only the separate task-local parameter prototype, its focused
tests, and current notes. It grants no variant approval or training admission.

The prior prototype wrote public challenges under setting-order names such as
`episode-00/public.json`. The corrected writer derives each public ID from the
exact bytes returned by `reviewer_support.public_challenge_bytes`, verifies the
matching `public_challenge_id`, sorts batches by that ID, and writes
`public/<sha256>.json`. Seeds, settings, programs and query answers remain under
`private/<sha256>/`; changing any of them without changing visible bytes leaves
the public ID unchanged. Duplicate visible payloads are rejected before output,
and all private JSON/rule bytes are precomputed before any directory is created,
preventing a malformed later record from leaving a partial batch.

Prototype SHA-256: `456c43d556501946422edde7f820123e60fb13d4cd837877bb7eb026f735a7a2`. Focused-test SHA-256:
`b6d5f883aa8a669e1328d0659a0a57c581f12799de33cf4211103963551ca3ad`. The six-setting Racket-backed run uses three
identifying demonstrations and four distinct queries per setting, preserves
8/8 retained canonical pairs for default `both/2`, and writes six sorted opaque
public IDs. The retained external follow-up manifest remains unchanged as the
historical source-bound report that motivated this correction; its old
`external_correction_pending` status describes the older prototype bytes, not an
approval record for these new bytes.

## 2026-10-23 review-58c6359b7db58ccc — proposed v3.1.0 repair

Generator SHA-256: `e1d8f2ffd5cf0a2329ca1c3cede73a2333a5cc6afbdc906bc143015a210b4ce5`.
The prior approved/reviewed v3.0.0 source was `3d840b93077aaf640b9f596ce1a41298424d35edcdb3e2e78d96ee6dc4029a27`. Existing approval and
audit-index records remain tied to those older bytes and are not auto-refreshed
or closed by this repair. The retained `needs_triage` index entry remains as
issued; this review does not adjudicate its disposition.

### Rule and ownership

The fixed canonical rule uses zero-separated4×4 framed cells with2×2 interiors.
At each local interior offset, each non-common color fills between its original
anchors independently along cell rows and columns when at least two exist.
Newly painted cells are not anchors for another pass. The selected Racket
`RULE_HASH=032c15e97118` and exact program text remain unchanged.

Retain the four observed profiles3×3/p5,4×4/p5,5×4/p6,5×5/p7 and the sole
observable `scene_profile` control. Generated scenes retain a unique modal
common interior color, uniform frames, distinct color/offset channels, multiple
changing colors, and real horizontal and vertical fills. Difficulty varies
presentation; it is not calibrated human/model difficulty.

### New decisions and reproduced defect

The prior sampler supplied only sparse accidental witnesses against repeated
propagation, and its lesson competitor list omitted that canonical-fitting
rival. Baseline seed15/default, indices0–2 demonstrations and query3, is an
accepted ambiguous lesson; actual Racket labels and a smaller lawful witness
are in `counterexamples/single_pass_ambiguity.json`. Repetition fits all8
retained canonical occurrences (4unique inputs), so existing finite canonical
checks could not settle the distinction.

New choice: two guaranteed single-pass witnesses every three samples, with the
previous random constructor retained in residue2. A gapped span plus a separated
singleton distinguishes one pass from repeated filling. Four profile roles
cross three semantic roles, giving `LESSON_SCHEDULE_PERIOD=12`; every profile
occurs in witness/free roles. Any three consecutive demonstrations retain a
witness; every rotation holding one of four consecutive pairs out retains one.
A parity schedule was rejected because it confounds profile and witness; only
one witness in three was rejected because its holdout can remove the signal.
The structural validator remains broad and does not require this witness.

`generate` and scheduling now require exact integer seeds, nonnegative exact
integer indices, and None/easy/medium/hard. Booleans/coercible scalar types
raise ValueError. Negative integer seeds remain supported. Unknown overrides
continue failing loudly.

### Validation and limits

The final battery passes12/12; portable task tests pass91 plus21subtests.
An exact seed0 cycle census covers36lessons/144rotations; a separate100-per-band
census covers300lessons/1,200rotations and1,200unique inputs with no declared
ambiguity. A production seed17 episode has3demos+4distinct queries and seven
Racket-labelled inputs. See the returned REVIEW.md/RESULTS.json for exact
source-bound commands and evidence; full failed baseline/intermediate runs are
retained there. These results do not prove arbitrary hypothesis uniqueness,
all-seed distributional coverage, or training admission. The increased witness
frequency is deliberate; the free role prevents it from becoming the entire
sampler. No unseen profile combinations or shared API changes are claimed.

### Separate proposed parameter family

`workspace/parametric/` supplies direction=both/horizontal/vertical and
min_anchors=2/3, fixed once per episode. Defaultboth/2 emits the exact canonical
program. Each of six demonstrated settings uses3demos+4distinct queries, with
Racket labels and demo-only identification; public challenges hide settings,
code and query answers. This prototype is separate from canonical approval,
uses a bounded4–5row/column scene subfamily, and is not a production parametric
API. Its README contains portable commands and stated limits.

## Historical bounded assessment (unchanged issued text)

The block below describes the older source hash at the time of its disposition,
not approval of the current bytes. Preserve its exact machine-managed record.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-42c8ad933d52e759:v0001`. Disposition: **no_issue**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `3d840b93077aaf640b9f596ce1a41298424d35edcdb3e2e78d96ee6dc4029a27`. At disposition, audited bytes match the current source.

### Current decision

Bounded reviewer-reported audit of SHA 3d840b93077aaf640b9f596ce1a41298424d35edcdb3e2e78d96ee6dc4029a27: 54 task tests, strict generated/canonical inputs, declared witnesses/rivals, 12 sampled lessons and 48 rotations reported passing. No concrete issue in that scope; no universal proof, new approval or maintainer execution implied.

### Assessment or prior finding

## b3d7f3a15b3d

**No issue found.** I inspected the canonical profiles, generator summary/notes, executable rivals/witnesses, and portable task tests, then ran the combined audit check against generator SHA-256 `3d840b93077aaf640b9f596ce1a41298424d35edcdb3e2e78d96ee6dc4029a27`.

The snapshot passed 54/54 task tests. Its strict semantic gate accepted 600/600 generated inputs and 8/8 canonical inputs, fired all 3/3 witnesses, verified all 3/3 rival claims, found 12/12 lessons identifiable, and found 0/48 ambiguous query rotations. Evidence: `checks/audit-b3d7f3a15b3d/checks/b3d7f3a15b3d_audit_summary.json` and `checks/audit-b3d7f3a15b3d/checks/b3d7f3a15b3d_audit_semantic_gate.log`.

This is a finite audit, not approval. I did not exhaust undeclared rival programs or all seeds, but I did not find a concrete counterexample within the documented exact profile grammar.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.
<!-- arcpuzzles-current-audit-assessment:end -->


## Current external prototype work

The retained manifest at
`generators/b3d7f3a15b3d/evidence/external-parametric-followup-58c6359b7db58ccc/manifest.json`
records the older setting-order naming defect and remains unchanged as historical
evidence. The current task-local prototype implements the requested visible-byte
public IDs and four-query writer regression. Proposed variants remain unapproved.


## Current public-export finding resolution

The earlier public-export finding is resolved only on prototype `456c43d556501946422edde7f820123e60fb13d4cd837877bb7eb026f735a7a2`: visible-only public IDs and public-ID-sorted emission are now present. 10 focused tests plus21subtests and six-setting3-demo/4-query Racket-backed export reported pass; owner statically confirmed visible-byte IDs and prevalidated public-ID-sorted write plan. Exact old source and the original owner capsule remain under `generators/b3d7f3a15b3d/evidence/external-parametric-followup-58c6359b7db58ccc/historical`; the owner inventory points to those same old bytes. Other audits/frozen-fixture limits remain unchanged and rule variants remain proposed. Source-bound decision: `generators/b3d7f3a15b3d/evidence/external-parametric-followup-58c6359b7db58ccc/manifest.json`.
