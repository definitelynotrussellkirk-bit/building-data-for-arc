# Shared tooling feedback

F1: Add a first-class bounded audit/export command for public-creation families

**Symptom:** The public-creation preflight correctly binds source and replays official labels, but it does not sweep lesson prefixes, test matched-setting distinguishability, verify episode-seed/presentation-seed independence, or emit/check sequential one-query public projections. Reviewers currently need ad hoc scripts for those checks.

**Evidence:** The packet-local `checks/tools/public_creation_audit.py` found a real issue in both initial adapters: with a fixed presentation seed, every episode exposed the same first source ordinal. After a regression and fix, each family passed a 32-seed sweep with first ordinals `[0,1,2,3]`, 64 public poison-invariance checks, 12 protected-Racket generated pairs, and 16 public export checks.

**Suggested change:** Add an `arcpuzzles.review_public_creation audit` action that consumes a passing preflight, runs a bounded matched-input setting sweep and prefix/invariance checks, executes a fixed generated bank in protected Racket, and writes source-bound public/private export receipts. Make the bounds explicit and keep the receipt reviewer-only, not owner qualification.

F2: Classify public-creation `reference.rkt` changes as Racket in the global intake summary

**Symptom:** Per-target validation correctly treats `repo/generators/TASK/reference.rkt` as the `racket` component for public-creation work, but the generated `INTAKE.json.components` only classifies paths under `repo/shared/data/` as Racket. A valid public-creation return can therefore list `generator` and `tests_notes` globally while omitting `racket` despite adding two authoritative Racket rules.

**Evidence:** This package's `INTAKE.json.changed_paths` contains both task-root `reference.rkt` files, and both repair outcomes report `changed_components=["generator","racket","tests_notes"]`; the generated global component list is only `["generator","tests_notes"]`.

**Suggested change:** In `_intake_summary`, reuse the public-creation path classification already used by `validate_full_return`: when the work policy is public creation, classify each assigned `repo/generators/<task>/reference.rkt` path as `racket`.
