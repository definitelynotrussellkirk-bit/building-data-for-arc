# Working notes: 8dafcfb1101f

## Final decisions — 2026-10-26

- **Base defect:** production samples placed color-1/color-2 anchors so `(dst-src)` was always down/right; an absolute-value-vector shortcut therefore fit generated labels. The source also lacked its literal `RULE_HASH` pin.
- **Repair:** version `1.3.2` pins `RULE_HASH = "8ab33123477f"`, deterministically covers all four signed vector quadrants, keeps translated payloads in bounds and collision-free, makes `blob_size` a strict observable control, and marks fixed metadata axes diagnostic.
- **Parametric family:** `vector_direction ∈ {src_to_dst, dst_to_src}` with exact canonical `src_to_dst` default. Inputs are setting-neutral; each episode has 3–6 demonstrations and four distinct queries, including a substantive 30×30 boundary case.
- **Teaching decision:** the three-demo minimum spans both signs on both axes and rejects identity, absolute-vector, one-axis, swapped-axis, fixed-down/right, and marker-moving rivals using demonstrations alone.
- **Sequential dependency:** locate anchors → compute the signed vector → translate every payload cell by that vector on a fresh grid. Protected replay uses the canonical direction as a wrong-intermediate counterfactual for a reverse-direction case.
- **Retained evidence:** final task tests and lint, 16-job deterministic self-audit over both settings/demo bounds/four seeds, exact-source protected-Racket authoring preflight, causal replay, public projection verification, and first-turn private-field invariance checks.
- **Limit:** these are reviewer authoring receipts, not owner qualification, source acceptance, or training admission.
- **Next owner action:** replay the unchanged source through native owner qualification and acceptance; do not regenerate the inventory first unless source changes.
