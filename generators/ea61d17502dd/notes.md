# Working notes: ea61d17502dd


## Review `review-842bc44bfd895986` — 2026-10-20

Baseline generator SHA-256: `a212a4a60bdaa985fbac7edf242b131c7a490526ab6aca50f1e341a11559f3d4` (`3.0.1`). Intermediate SHA-256 after public-call validation: `7fc469ebbdb6fa50ea40e00c9ca493c1824e49b94f30ce1bcaca56e1c382b068` (`3.0.2`). Final generator SHA-256: `b63450ce5a6c8c7153ace29e10bb3b1aaee13e02ca8fd605c2f7d824438db17b` (`3.1.0`). Canonical `RULE_HASH` remains `b956a6f1bc99`; no Racket authority was changed.

### Prior evidence used as a lead

I used the immediately preceding current account, review `review-6e2948c1d94fba69`, to understand why the five-axis generator and `crossing_to_farthest` rival were selected. I also checked the unresolved audit bound to older source `0ef9e4de...`; its override/alias findings are source-stale against `3.0.1` and were not treated as measurements of this baseline.

### Reproduced defects and decisions

1. **Strict public-call scalars.** The completed before battery had 11 green stages and one failing stage: `defect_lint` reported 24 warnings because `generate()` accepted boolean/float/string seeds plus boolean or negative sample indices. The repair validates `type(seed) is int`, `type(sample_index) is int`, and `sample_index >= 0` before sampling. Minimal reproducer: `counterexamples/review-842bc44bfd895986-invalid-scalars.json`; focused tests cover every reported class.
2. **Query-rotation teaching ambiguity.** The first 300-lesson census found no ambiguity in ordered production lessons, but 201/1,200 artificial query rotations could hold out the cycle's only straddled-marker example. Then the declared canonical-fitting rival `crossing_to_farthest` fit all remaining demonstrations and changed the query answer. Minimal deterministic reproducer: `counterexamples/review-842bc44bfd895986-rotation-ambiguity.json` (easy seed `2747585556`, start `0`, held-out pair `1`). The prior schedule `(outside, straddle, outside)` was changed to `(outside, straddle, straddle)`. Every three-sample cycle still covers both crossing priorities, full and partial strands, and both relation classes, while every three-demo subset of a four-pair window retains a straddled witness.

### Parametric-rule prototype

A separate proposed extension lives in `workspace/parametric/`. It chooses `vertical_bounds_mode` once per episode:

- `all_markers` is the canonical default and emits the exact selected Racket program (`program SHA-256 59177d...`, normalized hash `b956a6f1bc99`).
- `crossing_to_farthest` is the nearby alternative (`program SHA-256 a33870...`, normalized hash `e61c2b7b199f`).

At seed `271828`, both Racket-executed settings have complete three-demo/one-query episodes, train pair 1 distinguishes the programs, no opposite-setting rival survives the demonstrations, and the query answers differ. Public challenges omit the hidden mode, program, seed, and query output. Final source-bound evidence is under `checks/parametric/vertical-bounds-seed-271828-v2/` (the retained earlier directory records the same probe before the final schedule hardening). This is a prototype only; it does not change or approve the production authority.

### Final measurements

- Final source-bound battery: 12/12 green (`checks/after-v2/`).
- Final portable task tests: 52/52 passed (`checks/task-tests-v2/`).
- Final source-bound census: 300/300 ordered lessons identifiable and 1,200/1,200 query rotations identifiable; 1,200 unique inputs, zero materialization/hook/scoring errors (`checks/lesson-census-v2.summary.json`; full report archived losslessly as recorded in `checks/CENSUS-ARCHIVE-MANIFEST.json`).
- Blind task `874aa60956cc`: 3/3 visible examples, two recorded attempts including the initial diagnostic harness probe.
- Fresh exposed solve from final generator bytes: 3/3 visible examples on the first solve attempt; earlier rule exposure declared `yes`, reference consultation `no`.

### Remaining limits

The semantic result is relative to one declared rival plus bounded generic mutations, not a proof of unique induction against every possible program. The 300-lesson census samples 100 starts per band rather than every seed. The parametric evidence covers two declared settings at one deterministic seed, and the alternative remains proposed rather than production-approved. Mixed strand extents, gapped strands, reused role colors, and equidistant straddled markers remain outside the selected generator domain.

## Review `review-6e2948c1d94fba69` — 2026-10-04

Baseline generator SHA-256: `0ef9e4dee146770a6458aef7bea5688d5ae573f2dc8d22fd9de3b42e3782b608` (`2.1.0`). Final generator SHA-256: `a212a4a60bdaa985fbac7edf242b131c7a490526ab6aca50f1e341a11559f3d4` (`3.0.1`).

### Reproduced baseline defects

- Advertised ten axes, but singleton and inert pseudo-axes could not be observed; unknown keys were silently accepted; valid dimension values were rejected in some difficulty bands.
- `self_check` encoded a full-span assumption and rejected the lawful canonical `25x15` partial-strand pair.
- `defect_lint` found lawful and negative texture labels mixed into one domain.
- No executable semantic rival/witness contract existed.
- All six unique canonical pairs fit the plausible wrong rule `crossing_to_farthest`: use the crossing and only the farther vertical marker as vertical bounds.
- The selected augmented authority carrier differed textually from the canonical source.

### Repair

- Replaced the false surface with five exact, observable axes: dimensions, crossing priority, vertical marker relation, and strand extent.
- Added strict request validation and complete `GenCtx` provenance for scheduled defaults and explicit overrides.
- Added canonical-compatible structural recovery and validation, including strict partial strands.
- Added an independent Python mirror, declared rivals/witnesses, and a three-profile teaching schedule containing a straddled-marker counterexample in every three consecutive samples.
- Added task-local regression tests and `workspace/reference_probe.py` for deterministic, structural, semantic, and optional Racket-parity checks.
- Synchronized the augmented carrier to the unchanged canonical program.

### Final measurements

- Source-bound battery: 12/12 green.
- Portable task tests: 32/32 passed.
- Independent probe: 400/400 lawful deterministic samples; 38/38 Racket parity cases.
- Lesson census: 300/300 lessons refuted the declared rival; 1,200 unique materialized inputs; no ambiguity or execution errors.
- Fresh exposed solve from final bytes: 3/3 visible examples on first genuine attempt; earlier rule exposure declared; no reference consulted during solve.

Detailed rationale is in packet-root `DECISIONS.md`; evidence paths and exact commands are in `REVIEW.md` and `RESULTS.json`.

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `b63450ce5a6c8c7153ace29e10bb3b1aaee13e02ca8fd605c2f7d824438db17b`.

# Decisions — `ea61d17502dd`

## D1 — Reject malformed scalar identities at the public boundary

**Choice.** Require `type(seed) is int`, `type(sample_index) is int`, and `sample_index >= 0` before invoking `gen_ctx` or sampling.

**Original state and rationale.** Version `3.0.1` delegated these values without an exact public validation. Any original rationale for accepting numeric lookalikes is unknown; the behavior appears incidental rather than an intentional API promise.

**Alternatives considered.** `isinstance(value, int)` was rejected because booleans are integer subclasses. Coercing floats or numeric strings was rejected because it collapses distinct sweep labels and hides caller errors. Allowing negative indices as Python-style reverse indexing was rejected because the API documents a sample identity, not list access.

**Probe.** Two test-first regressions cover `True`, `False`, integral/nonintegral floats, strings, boolean indices, and negative indices. The before battery reports 24 warnings; the final `defect_lint` is green and all 52 task tests pass.

**Failure modes and limits.** Python integers remain unbounded, which is acceptable because `gen_ctx` hashes them deterministically. This decision does not define validation for unrelated future parameters.

## D2 — Preserve the selected rule and five-axis input contract

**Choice.** Keep the canonical Racket program, `RULE_HASH=b956a6f1bc99`, dimensions, priority, vertical relation, and strand extent semantics unchanged.

**Rationale.** The reproduced defects were at the Python request boundary and lesson schedule, not in label correctness. Rule smoke, Racket lint, authority sync, canonical pins, and the existing independent mirror were already green.

**Alternatives considered.** Editing the authority to make the rival disappear was rejected because it would change the task rather than teach it. Reopening the old `0ef9e4de…` audit repair was rejected because its finding was bound to a stale source and the current baseline already had the five-axis repair.

**Probe.** Final authority sync and Racket stages pass; the canonical program SHA-256 remains `59177d…`; the final solve generated from `b63450ce…` still passes every visible example.

**Failure modes and limits.** Authority synchronization proves selected carriers agree, not that every archived external copy is audited.

## D3 — Harden every legal query rotation with two straddled profiles

**Choice.** Change the repeating teaching schedule from `(outside, straddle, outside)` to `(outside, straddle, straddle)` while retaining alternating priorities and full/partial coverage.

**Rationale.** The old schedule was sufficient only when the fourth pair stayed the query. A four-pair episode could contain exactly one structural witness; holding it out removed the only evidence against `crossing_to_farthest`. Two straddled profiles ensure that every three-demo subset retains at least one such witness.

**Alternatives considered.** Randomly resampling until a rotation happened to pass was rejected as nondeterministic and harder to audit. Increasing lessons to four demonstrations was rejected as unnecessary token cost. Declaring query order immutable was rejected because the assignment's data-quality goal and shared rotation diagnostic explicitly support legal rotations. Adding a second rival-specific synthetic pair outside the normal profile schedule was rejected in favor of a minimal schedule change using an already supported axis.

**Probe.** The retained counterexample fixes seed `2747585556`, start `0`, and held-out index `1`. A focused test enumerates every held-out position in every four-pair window for all three difficulty bands. The first census measured 201/1,200 ambiguous rotations; the final census measured 0/1,200, with 300/300 ordered lessons still passing.

**Failure modes and limits.** Defaults now favor straddled relations 2:1, although outside remains guaranteed once per cycle and all exact overrides remain legal. The guarantee is against the declared rival, not every conceivable wrong program.

## D4 — Keep the parametric extension separate from canonical production

**Choice.** Prototype `vertical_bounds_mode` with two episode-level values: canonical `all_markers` and alternative `crossing_to_farthest`. Select the mode once per episode and keep it hidden from the public challenge.

**Rationale.** This is a genuine semantic parameter: it changes a nearby program choice while holding grammar, colors, crossing cue, and weave logic fixed. A straddled labelled demonstration makes the parameter inferable, and a straddled query makes it consequential.

**Alternatives considered.** Cosmetic palette, size, or priority parameters were rejected because they alter inputs but not the rule program. Per-example mode selection was rejected because it would make one lesson inconsistent. Promoting the alternative into the production generator was rejected because the assignment requested an extension prototype, not a new canonical task.

**Probe.** `checks/parametric/vertical-bounds-seed-271828-v2/probe_report.json` is Racket-executed and source-bound to final generator `b63450ce…`. Both programs have distinct hashes, train index `1` distinguishes them, no opposite-mode rival survives, and query outputs differ. Public/private redaction tests are part of the 52-test suite.

**Failure modes and limits.** The probe covers one medium seed and two declared values. Episodes without a straddled labelled example can be ambiguous, so the prototype explicitly schedules one. The alternative remains proposed, not approved.

## D5 — Retain exact failure evidence but archive oversized census reports losslessly

**Choice.** Keep compact readable summaries and deterministic gzip copies of the two full 300-lesson reports. Record original and archive SHA-256 hashes, byte counts, and restoration commands in `checks/CENSUS-ARCHIVE-MANIFEST.json`.

**Rationale.** The raw reports total about 37 MiB and would violate the 25 MiB expanded return budget by themselves. Gzip preserves every byte of the original JSON while keeping the maintainer brief and first witnesses directly readable.

**Alternatives considered.** Deleting the pre-repair census was rejected because it is the only complete retained measurement of the 201-rotation defect. Keeping only summaries was rejected because it would discard replay recipes and exact instances. Re-running a smaller census was rejected because it would weaken the measured claim.

**Probe.** The manifest's original hashes equal the `full_report.sha256` fields in both generated summaries. Restoring with the recorded `gzip -dc` commands reproduces those hashes exactly.

**Failure modes and limits.** A maintainer must decompress the archive to inspect every lesson row; the compact summaries and minimal counterexample avoid that for routine intake.

## D6 — Separate visible-only solves from authoring evidence

**Choice.** Complete the assigned blind solve before source inspection, and after the final generator change prepare a new solve episode from final bytes. Record earlier exposure honestly as `yes` and reference consultation as `no` in the post-repair solve.

**Rationale.** A solution generated from an intermediate source would not verify the final generator. Moving the intermediate solve into `checks/prior-solve/` preserves history without presenting it as final evidence.

**Alternatives considered.** Reusing the earlier solution notes was rejected because the solve contract forbids prior explanations. Claiming the post-repair solve was blind was rejected because generator work necessarily exposed the family rule.

**Probe.** `solve/summary.json` binds the episode to final generator `b63450ce…` and records one revision with 3/3 visible examples. `solve-blind/summary.json` retains both blind attempts, including the failed diagnostic harness probe.

**Failure modes and limits.** Visible checks deliberately withhold private-query correctness; independent maintainer scoring remains authoritative.

## D7 — Do not repair audit targets in the selected-task patch

**Choice.** Reproduce and report findings for `675dcb932594` and `c3cb6bb4b6e8` without editing their sources.

**Rationale.** The assignment explicitly makes the two audit lanes findings-only. Mixing their fixes into this patch would violate source scope and make acceptance harder.

**Probe.** Audit evidence is source-bound to `ee5d8766…` and `9ee85421…` respectively, and `AUDIT.md` contains exactly one section for each assigned target.

**Failure modes and limits.** These findings remain open for their maintainers; they are not listed as failures of the selected generator.
