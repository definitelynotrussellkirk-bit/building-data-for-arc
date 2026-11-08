# Review and repair: `351de765e33f`

- **Ship:** generator 3.1.0, regression tests, standalone verifier, counterexample, and bounded prototype.
- **Authority:** unchanged canonical Racket rule; `RULE_HASH=f074243a0544`.
- **Root defect fixed:** the noncanonical 8-neighbor moat rejected every canonical input.
- **Teaching defect fixed:** every cyclic five-demo window now refutes retained distinct-size and colorblind-4 shortcuts.
- **Coverage:** every period contains all eight profiles and separated, diagonal-contact, and edge-contact scenes.
- **Validation:** malformed difficulty, seed, index, and profile values fail closed.
- **Fresh tests:** 50/50 pass.
- **Independent check:** 4096 draws, 4096 oracle comparisons, 0 failures.
- **Replay:** the patch applies cleanly and yields a byte-identical 17-file target tree.
- **Installer:** fresh apply, idempotent rerun, and unknown-byte refusal all behave as designed.
- **Acceptance:** needs attention only for the explicitly documented packet-reset/Racket limitations.

## Repair

The generator now follows the actual authority semantics: components are same-color and 4-connected, so different-colored objects may touch. The finite schedule places repeated-rank witnesses no more than four positions apart and edge-contact witnesses densely enough to distinguish both retained shortcut families before a query. Default public-profile draws use exact canonical dimensions, restoring canonical-profile support in every band.

Pure rival functions and witness predicates make the lesson claim executable. The standalone verifier loads source directly from an ordinary checkout, checks canonical acceptance, strict calls, all cyclic windows, deterministic replay, exact overrides, rival purity, prototype bindings, and an independent output oracle.

## Evidence

- TDD baseline: 30 failures on the untouched source.
- Repaired target: 50 tests pass.
- Stress: 14400 draws, 12799 unique inputs.
- Patch replay: 50 tests pass; verifier status `PASS`; task bytes exactly match.
- Blind solve: 4/4 visible examples pass.
- Exposed post-repair smoke: 64 cases, 0 failures.

See `QUESTION_ANSWER.md` for the exact shortcut witness and `RESULTS.json` for machine-readable receipts.
