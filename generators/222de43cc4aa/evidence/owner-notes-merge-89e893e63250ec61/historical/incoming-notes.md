# Current notes: 222de43cc4aa

## Decisions now in force

- Keep the approved canonical rule unchanged: rule hash `ce9518b81cf8`, two full vertical ping-pong round trips, exact canonical Racket bytes retained by the prototype default.
- Repair the public generator contract at its entry point. Unknown override names and non-`None` texture values outside the six declared tokens now raise `ValueError` before `gen_ctx`; no generator version bump was made because 114 representative lawful calls, including explicit `texture=None`, remained byte-for-byte identical.
- Keep rule variation outside production in `workspace/parametric/`. The proposed parameter is `round_trips ∈ {1, 2}`, with canonical/default `2`; output height is `1 + 2*round_trips*(h-1)`. This is reviewer-reported, not catalog approval or training admission.
- Fix one setting for an entire episode. Each retained episode has three demonstrations and four distinct queries drawn from seven distinct parent-generator inputs. Demonstrations alone refute the other declared setting.
- Public challenge files contain demonstrations and query inputs only. Filenames are SHA-256 hashes of exact visible bytes; seeds, settings, Racket programs, and query answers stay private.
- Keep the promotion adapter fail-closed: settings must be exactly `{"round_trips": 1|2}`, demos must be literal integers in 3..16, and queries literal integers in 1..16.
- Treat evidence as invalid if public-ID inventory, private outputs, input hashes, or any declared source binding drifts.

## Source and evidence identities

- Baseline generator SHA-256: `0e43a13ef9eb3745adf7a22d5973a2e9b7a0d691666136b25adaf7d0d0b7b04a`.
- Repaired generator SHA-256: `9158679a51cb22d17a53b6fb68ec00edb02e88a58f71920c6f6224feeadfcdf5`.
- Prototype SHA-256: `c65b11035f3c26e6b64694d7f6ba682dd353a0078f034086cdbe82837e6a2c07`.
- Adapter SHA-256: `1b88f80b0888628d19784221fcdc65227214ee4fd5bd18f24c5308cb4bcb4607`.
- Parametric tests SHA-256: `8b267039d5e94842c0f722bd304dafc4e8dd195de1132d42877976cd1779e869`.
- Task-local evidence inventory SHA-256: `6281d5a87bebf53369378aa761578a3817cf1aae3dce232c544491a1d2509155`.
- Protected Racket evidence: 28 episode applications, 6 canonical/default checks, and 4 boundary applications; 14 distinct episode inputs; both declared settings; security canaries passed. See `workspace/parametric/evidence/manifest.json` and `checks/parametric/round-trip-count-v1/` in the return.
- Final selected-task aggregate: 61 tests passed. The override wrapper also passed. The duplicate-ID wrapper invocation and missing-`PYTHONPATH` direct invocation are retained as command-use errors, separate from the corrected green runs.

## Limits and next useful action

Evidence is finite: two seeds/settings, the current parent input grammar, and rivalry only between declared values `1` and `2`. It does not prove uniqueness against arbitrary programs. Because the production generator source hash changed, a maintainer must replay the override repair against the approved baseline and separately decide whether to qualify the parametric prototype; neither packaging nor these receipts updates approval automatically.
