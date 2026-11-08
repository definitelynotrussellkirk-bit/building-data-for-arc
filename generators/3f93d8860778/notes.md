# Working notes: 3f93d8860778

## 2026-10-04 review repair

Baseline sampler defect: every nonempty column was already a valid matching pair and every valid pair had a globally unique colour. In a 200-draw-per-band probe, both `fill_every_active_column` and `global_exact_two_colours` agreed with the authority on 200/200 inputs in every band.

Version 4.0.0 keeps the canonical Racket authority unchanged and installs a deterministic three-profile curriculum. `canonical_clean` preserves direct canonical-like examples. Both guard profiles now contain a mismatched pair, a singleton, a gapped same-colour triple, repeated valid-pair colours and at least one distinct valid-pair colour. This is intentionally redundant so every three-of-four query rotation retains all essential negative evidence.

Intermediate evidence mattered:
- first rotate-query census: 212/1,200 ambiguous rotations because holding out the only multiplicity guard removed the witness;
- second census: 11/1,200 ambiguous rotations because a rare two-pair guard admitted the one-colour rival;
- final census: 300/300 lessons, 1,200 unique inputs, 1,200 rotations, zero declared-rival ambiguity or runtime errors.

Other repairs: sparse deterministic canonical-profile anchors satisfy the small profile-floor gate; unknown overrides are rejected; the strict validator accepts only complete clean/guard signatures; the exact `spans=2` override remains supported. The baseline frozen fixture was restored byte-for-byte and portable canonical access is supplied from a separate `tests/conftest.py`.

Final generator SHA-256: `966b81f54c5130ca20546ff4a973bdbe58b8530d6f0b749291ca614b0b515b91`. Final battery: 12/12 green. Portable selected-task tests: 83/83. Authority changed: no.

Limitation: declared-rival and finite-sample checks establish separation only for the tested executable rule family and current lesson assembly policy; they do not prove universal identifiability.
## Current reviewer considerations

Source SHA-256: `966b81f54c5130ca20546ff4a973bdbe58b8530d6f0b749291ca614b0b515b91`.

# Decisions for `3f93d8860778`

## D1 — Keep the reference authority unchanged

**Choice.** Retain the canonical Racket rule and pin `RULE_HASH = "abdf780ecbe7"`.

**Reason.** Canonical examples and rule smoke agreed: a column fires only when it has exactly two nonzero cells of the same colour; the inclusive interval is filled, and every other column is unchanged. The defect was in what the sampler taught, not in the labels.

**Rejected alternative.** Broadening or rewriting the Racket rule to match the old all-valid-column distribution. That would preserve the shortcut rather than repair the data.

**Probe/failure mode.** Authority sync, Racket lint and rule smoke are all green in `checks/after-final-v2/`. Finite smoke testing still does not prove the authority is mathematically complete.

## D2 — Use a deterministic three-profile teaching schedule

**Choice.** Cycle `canonical_clean`, `mismatched_guard`, `multiplicity_guard` by `sample_index % 3`.

**Reason.** The original independent sampler never generated a non-firing active column. A deterministic curriculum makes lesson-level coverage auditable and permits exhaustive cyclic-start tests.

**Rejected alternatives.** Pure random guard injection could leave complete lessons without a counterexample. A single special guard profile failed when that profile became the query during rotation.

**Probe/failure mode.** The first rotate-query census found 212/1,200 ambiguous rotations. Making both non-clean profiles complete reduced this to 11, exposing the next issue rather than hiding it.

## D3 — Put the complete non-firing grammar in every guard scene

**Choice.** Each guard scene contains exactly one mismatched pair, one singleton and one gapped same-colour triple, all left unchanged.

**Reason.** These distinguish “fill every active column,” “fill matching extrema despite extra markers,” and singleton extrapolation shortcuts. Repeating the full trio means any three-of-four lesson rotation retains the negative evidence.

**Rejected alternatives.** Splitting mismatch and multiplicity evidence across separate profiles; the 212-rotation failure showed that query holdout can remove the only witness.

**Limits.** These three patterns cover the most plausible column-local rivals, not every possible malformed column pattern or nonlocal hypothesis.

## D4 — Reuse one valid-pair colour but retain a second pair colour

**Choice.** Guard scenes use at least three valid spans by default: two share a colour and at least one uses another colour. Explicit `spans=2` remains legal.

**Reason.** Repetition refutes “fill colours occurring exactly twice globally.” A distinct pair colour simultaneously refutes “paint every interval one colour.”

**Rejected alternatives.** Two default valid pairs of one repeated colour. That passed most checks but caused the remaining 11/1,200 rotated lessons to admit the one-colour rival.

**Probe/failure mode.** `checks/shortcut-probe-final.json` records 133 guard draws per 200-sample band and refutes both rivals. Arbitrary user-composed override lessons are not promised identifiable.

## D5 — Anchor canonical profiles without collapsing diversity

**Choice.** When there are no overrides and `sample_index % 5 == 0`, draw one of the five observed canonical height/width profiles with three valid spans; otherwise use full difficulty-aware ranges.

**Reason.** The first complete battery had zero exact canonical profile hits in its small profile-floor sample despite lawful broad coverage. Deterministic sparse anchors satisfy the floor while leaving four of five slots unconstrained.

**Rejected alternatives.** Shrinking every draw to canonical dimensions, which would create a new shape shortcut; or relying on chance, which already failed the reproducible gate.

**Limits.** Anchors cover observed height/width/palette profiles, not every higher-order canonical feature combination.

## D6 — Preserve a strict structural validator

**Choice.** Accept only two signatures: clean scenes with distinct pair colours, or complete guard scenes with repeated pair colours. Reject unknown overrides explicitly.

**Reason.** The frozen fixture expects single accidental endpoint deletions, mismatches, inserted markers and duplicate-colour impostors to remain invalid. Weakening the validator to accept arbitrary partial guard mixtures would erase that defense.

**Rejected alternative.** General acceptance of any singleton/mismatch/triple combination. It would make the new curriculum easy to generate but would break the retained malformed-input contract.

**Probe/failure mode.** The frozen fixture remains byte-identical at SHA-256 `c9e4a1e6ebb1873156bf79a6357b9123a8dee23ce609114f9cd9ee70b3e489f6`; all 83 portable tests pass.

## D7 — Add source-discovered rival tooling instead of a copied list

**Choice.** `workspace/shortcut_probe.py` loads the current declarations dynamically, verifies canonical fit, samples every band, and exhausts schedule starts/query rotations.

**Reason.** A hand-copied rival list can silently drift from production declarations and produce a false pass. The reusable probe makes future additions automatically part of the audit.

**Rejected alternative.** Treating witness frequency as proof that each assembled lesson contains the witness. The two failed censuses demonstrated why lesson assembly must be tested directly.

**Limits.** The tool establishes separation only for declared executable rivals and the current deterministic assembly policy.

## D8 — Keep the frozen fixture immutable and adapt only the portable harness

**Choice.** Restore the baseline fixture exactly and add a separate `conftest.py` plus new regression module.

**Reason.** The assignment explicitly forbids rewriting the frozen root fixture. The failure was a legacy path assumption in the portable snapshot, not a test expectation that should be weakened.

**Rejected alternative.** Editing the frozen file to import `reviewer_support.canonical_pairs`; this would make the suite pass by violating the review contract.
