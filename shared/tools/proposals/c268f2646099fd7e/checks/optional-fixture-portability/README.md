# Optional maintainer proposal: portable task fixture

This directory proposes a migration of the frozen task fixture:
`repo/generators/563e1df172df/test_generator_563e1df172df.py`.
The actual fixture remains unchanged. This proposal is separate from the allowed
`source.patch`; it does not clear the current official `task_tests` blocker.

## Proposed change

The unified diff replaces the private generator import and fixed
`Path(__file__).resolve().parents[3]` ledger lookup with the existing public
`reviewer_support.find_root`, `load_selected_generator`, and
`canonical_pairs(..., labeled_only=True)` helpers. The helpers bind both the
selected generator and canonical data to the fixture's own copied runtime or
repository tree. Labeled train and test pairs are normalized by the helper;
unlabeled test queries are excluded. Every test body and assertion is unchanged,
including the requirement for exactly **eight labeled canonical pairs**.

## Verification performed

The proposed fixture was parsed and compiled for syntax without executing it.
`git apply --check` passed against an unchanged copy of the frozen fixture in a
separate temporary tree containing only that fixture and the syntax-check input.
Both checks exited **0**. The temporary fixture was not modified by the check.
The frozen actual fixture's SHA-256 was verified before and after these checks.
Exact commands, exit codes, and baseline/proposed hashes are in `receipt.json`.

The modified fixture was **not run**. No `task_tests` success is claimed. A
maintainer may review and apply this patch separately, then perform their own
runtime and assertion checks. Keep the frozen-file blocker in the current return.
