# Review: two native parametric candidates

Assignment `review-c5bd8cc3551df1d6` is complete at the reviewer-ready handoff stage.

- `fa3550d200a0`: added `quarter_turns=0|1|2|3`; zero is the exact canonical program. Minimum and maximum count qualifications passed with 96 and 224 protected-Racket evaluations; staged changed-target tests pass 66/66.
- `9c69eb63c11a`: added `selection_mode=median|second_largest`; median is the exact canonical program. Minimum and maximum count qualifications passed with 32 and 64 protected-Racket evaluations; staged changed-target tests pass 62/62.
- Both samplers are setting-independent, support 2–6 demonstrations and exactly four distinct queries, and include lawful 30×30 stress.
- Both demonstrations identify the episode setting from labels alone; query answers are not used for teaching selection.
- Both protected causal witnesses use `wrong_intermediate` ablations and change the final Racket output.
- Public projection produced 32 + 16 one-query views. Saved-file checks, preview verification, and 48 + 24 first-turn invariance checks passed.
- Repaired one inherited `fa3550d200a0` test-path defect exposed by the portable staged runner; it now resolves canonical data through `reviewer_support`.
- Canonical defaults and production generators remain unchanged. Manifests are current and explicitly reviewer-reported, with `variant_approved=false` and `training_admitted=false`.

Owner next step: integrate these exact source patches, rerun native qualification, inspect each parameter/input grammar, and run fresh `parametric accept` separately for both. This return performs no owner acceptance or training admission.
