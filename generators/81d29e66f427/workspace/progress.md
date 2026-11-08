# Review ledger — 81d29e66f427

## Baseline and root causes

- Baseline source SHA-256: `243c44159cf3fa603ce2d5750951659283dbbd4b60231deffefe318418afb852`.
- The baseline battery failed lint, self-check, defect lint, profile floor, and override; the semantic stage reported `NO_CONTRACT`.
- Root cause: `self_check` treated nonempty/distinct OR/AND/XOR results as legality, but canonical test pair 0 is disjoint and lawfully has an empty AND panel and OR=XOR.
- Root cause: `AXES` advertised derived/dead controls (`grid_h`, `grid_w`, palette, density, texture) and per-band draw bounds rejected globally advertised values.
- Root cause: generated geometry had noncanonical left/bottom margins, yielding zero easy-band canonical-profile support.
- Root cause: there was no executable semantic contract, and two-key defaults could omit a Boolean branch.

## Rulings

- Ruling: keep the Racket authority unchanged — an independent Python oracle matches all five labeled canonical pairs; the defects are in sampling/validation/teaching contracts, not the rule.
- Ruling: advertise only four exact observable axes (`interior_h`, `interior_w`, `n_keys`, `gap`) — mask pixels and key identities remain deterministic latent variation, not false exact controls.
- Ruling: accept lawful degenerate mask relationships in `self_check`, but make every default draw realize 00/10/01/11 so lesson rivals are distinguishable.
- Ruling: use a three-position ordered schedule (`canonical_key4`, `canonical_other_xor`, `broad`) with three demonstrations; every consecutive triple contains a non-4 XOR key and both canonical-scale and generalized support.
- Ruling: declare the canonical shortcut `key4_only_xor`, plus all-OR/all-AND/all-XOR/fixed-order rivals. Query rotation is intended to be supported and will be checked.

## TDD record

- Added independent `workspace/reference_probe.py` and `tests/test_generator.py` before production edits.
- Red run: `checks/tdd-red.log`, 36 failed / 13 passed. Failures reproduced canonical rejection, unobservable/rejected axes, unknown-key acceptance, missing hooks, absent profile support, and weak validation.
- First green run: `checks/tdd-green-1.log`, 49 passed.

## Intermediate final-source checks (SHA pending full battery)

- lint: pass
- selfcheck: pass
- defect_lint: pass (`scanned 1; FLAGGED 0`)
- profile_floor: pass, canonical accepted 5/5, exact profile 46/60, envelope 46/60
- semantic_gate: pass, strict 210/600, witnesses 5/5, rival claims 5/5, 12/12 lessons identifiable, 0/48 rotated ambiguities
- override: pass, 11,520/11,520 accepted with zero findings
- staged task tests: 49/49 pass

## Final-source results

- Final generator SHA-256: `4b70cb6f8f0d9a669b363c2182d76367ffb951ac16c4a4f2216f3acd7ff9acd4`.
- Completed after battery: 12/12 green; no advisory, failure, interruption, or pending stage.
- Task-local tests: 49/49 passed.
- Exact override contract: 11,520/11,520 accepted, zero findings, unknown key rejected.
- Canonical profile floor: 5/5 canonical inputs accepted; 46/60 exact-profile draws, support in every band.
- Semantic gate: 210/600 strict canonical-like; 5/5 witnesses and rival claims; 12/12 lessons and 48/48 rotations identifiable.
- Source-bound census: 300/300 lessons materialized, 1,200 unique pairs, 0 production or rotated ambiguities against declared rivals.
- Post-repair visible-only solve: one revision passed 3/3 demonstrations; earlier exposure yes, reference consulted during solve no.

## Assigned audits

- `15dd333aa99b`: source-bound generated witness has a blocked endpoint pair accepted by `self_check`; 60/300 sampled draws violated the documented clear-gap/count contract.
- `d17f2bbc0878`: target validator rejects canonical training pair 0 because its color bboxes overlap; a separation-precondition shortcut fit 300/300 sampled generated draws.
- Neither audit target was modified. Evidence and public Racket receipts are under `checks/audit/`; reusable extraction/verification is `workspace/audit_probe.py`.
