# Working notes: d78409c82698

## Final decisions — 2026-10-26

- **Base defect:** `self_check` treated the presence of a diagonal singleton pair as canonical validity. That is a useful generated-distribution lesson, but lawful original ARC examples need not contain it, so native checks rejected valid originals.
- **Repair:** version `2.0.3` pins `RULE_HASH = "f38a8db401a2"`, keeps diagonal-pair coverage in focused distribution tests rather than canonical validity, exposes exact `grid_h`, `grid_w`, and `n_singletons` controls, and marks fixed metadata axes diagnostic.
- **Parametric family:** `connectivity ∈ {4, 8}` with exact canonical 4-neighbor default. Matched setting-neutral inputs contain cells isolated under both rules, diagonal-only red groups, cardinal red components, border cases, and non-red distractors.
- **Teaching decision:** the three-demo minimum distinguishes 4- from 8-connectivity and rejects identity, recolor-all-red, wrong-color, diagonal-only-neighbor, cardinal-endpoint, and border-only rivals using demonstrations alone.
- **Sequential dependency:** form red components under the selected adjacency → derive the singleton-coordinate mask → recolor exactly that mask from 2 to 3. Protected replay substitutes the 4-neighbor mask for a qualified 8-neighbor case.
- **Retained evidence:** final task tests and lint, 16-job deterministic self-audit over both settings/demo bounds/four seeds, 30×30 stress, exact-source protected-Racket authoring preflight, causal replay, public projection verification, and first-turn private-field invariance checks.
- **Limit:** these are reviewer authoring receipts, not owner qualification, source acceptance, or training admission.
- **Next owner action:** replay the unchanged source through native owner qualification and acceptance; do not regenerate the inventory first unless source changes.
