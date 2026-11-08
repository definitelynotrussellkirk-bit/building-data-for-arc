# Working notes: a2fc4c442e35

- 2026-10-23 repair: ordinary lessons now contain 1-3 exact-length-3 target runs plus one isolated length-4 no-op run. The `runs` override continues to count actionable triples; the negative is additional.
- `self_check` accepts only isolated runs of length 3 or 4 and requires at least one of each, so canonical inputs are in-domain and the “extend every run” rival is visibly false.
- Generator version bumped from `2.1.0` to `2.2.0`; the canonical Racket rule is unchanged.
- This addresses the retained audit `review-697a3a8d141148fd:v0001`, which found 0/300 sampled lessons with a non-three run.
- Plain repository-root pytest and staged task tests pass 24/24. A fresh return replay exposed and then fixed the test-only `reviewer_support` import bootstrap; four real-Racket mixed cases match the exact-triple oracle, and 784 generated cases plus 8 validator-rejection mutations found no failures.
- Remaining scope is deliberately bounded rather than exhaustive. The next useful maintainer action is source-bound replay of the returned patch and evidence; no canonical-rule or shared-runtime migration is needed.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-697a3a8d141148fd:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `41ced5bfc5ede61f79a0e06e7bafcea188a745dacb0fca5de44b2c73b5026907`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Explicit owner disposition after accepted reviewer repair review-1b1279ef5d4a2571: current repo/generators/a2fc4c442e35/generator.py SHA256 5f8db07f3af3a87e298cb25e6825ddcbc29466931238c61fb052c7b7731fb4b7. Reviewer-reported evidence: 24focused tests and mixed-run Racket cases. Every ordinary scene now includes an unchanged length-four negative alongside exact triples; validator admits canonical negatives. No owner battery rerun, universal identifiability or training admission. The audit on 41ced5bfc5ede61f79a0e06e7bafcea188a745dacb0fca5de44b2c73b5026907 is resolved only for these repaired findings.

### Assessment or prior finding

## a2fc4c442e35

**Reproduced teaching-domain defect: the sampler omits the canonical longer-run negative.**

The intended task extends a horizontal run only when its length is exactly three; canonical examples deliberately include length-four runs that remain unchanged. The audited generator’s `self_check` rejects every canonical input containing those distractors, with errors such as `row 3 has run of color 4 length 4 (expected 3)`. In 300 sampled inputs—100 each for easy, medium, and hard, using `seed=4800+index` and `sample_index=index`—the only observed run length was 3; 0/300 contained a non-three run and 0/300 failed the generator’s validator. See `checks/audit/a2fc4c442e35/probe.json`.

A strong rival is **extend every nonzero horizontal run by one clear cell on each side, regardless of run length**. It agrees with every emitted sample because the generator never emits any other run length. On canonical train input 0, the authoritative Racket output extends the length-three color-2 run but leaves the length-four color-4 run unchanged. The rival additionally paints row 3, columns 1 and 6, color 4. Exact input, source/rule hashes, validator result, authoritative output, rival output, and differing cells are retained in `checks/audit/a2fc4c442e35/counterexample.json`; the supported Racket receipt is `checks/audit/a2fc4c442e35/racket.json`.

This exact counterexample is outside the generator’s documented/validated domain, which is the defect: the canonical negative needed to distinguish “exactly three” from “any run” cannot appear in lessons. Audit target source was not modified.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-697a3a8d141148fd-v0001/audit_assets.json), manifest SHA-256 `ac7be85b4a297079e0095ca87f0d374dbe6966039fd97b7026802161f8e5ebab`.
<!-- arcpuzzles-current-audit-assessment:end -->
