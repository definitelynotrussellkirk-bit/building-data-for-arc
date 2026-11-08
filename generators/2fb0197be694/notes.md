# Working notes: 2fb0197be694

## Current review — 2026-10-24

- **Decision:** keep the selected production generator and canonical rule unchanged. Add an opt-in native parameter `encoding = direct | running_parity`; `direct` returns the exact canonical Racket bytes, while `running_parity` recovers the same four local occupancy bits and folds them left-to-right with cumulative XOR.
- **Sampling contract:** inputs are setting-independent; demonstrations support 2–6, queries support 1–4, every requested input is distinct, and the first two demonstrations distinguish the declared settings. Query profiles include a cluttered 30×30 case and a boundary-contact case.
- **Portable-test repair:** the retained test used a fixed `__file__` depth and the private `scripts.generator_module_loader`. It now uses `reviewer_support.find_root`, `canonical_path`, `canonical_pairs`, and `load_selected_generator`, and compares selected authority through the copied catalog/canonical data. Production generator bytes remain SHA-256 `6566fd91ff79bf1da400073937d780ccf705fd14dccf96e095c624db8ae759e9`.
- **Fresh checks:** 5/5 focused tests and 12/12 staged portable task tests passed. Native qualification passed four jobs (two settings × seeds 0 and 17), three demonstrations and four queries per job, with 40 protected-Racket evaluations.
- **Adversarial evidence:** four qualified episodes were checked against ten finite rival rules with zero surviving wrong-rule/query disagreements. Two wrong-intermediate counterfactuals replayed through protected Racket in four evaluations; both changed the final output.
- **Current inventory:** `workspace/parametric/evidence/manifest.json`, SHA-256 `7a0cc68ad6314f9e69e87496c81c9a7d98630bbdb3e682c0adff02437d53cfeb`; all 148 files named by the qualification source binding matched current bytes.
- **Limit / next action:** reviewer-ready is not owner-accepted. The owner must integrate these exact bytes and run fresh native acceptance replay; no setting or generated episode is admitted to training by this return.
