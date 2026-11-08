# Review — `5e8e4691afde`
Task/source: assignment `review-16de47cf2eee9a3e`; generator `75d65fd7…` → `8a564c3c…`.
Canonical authority is unchanged: task `5e8e4691afde`, normalized rule hash `ee2251228926`.
Defect reproduced: 33 invalid scalar calls were accepted across difficulty bands.
Repair: `generate` now requires exact integer seed/index values and a nonnegative index; negative integer seeds remain valid.
Portable test repair: canonical/base paths now use `reviewer_support` root helpers; source identity retains raw/target and rule-hash pins.
Prototype built separately: episode-fixed `diagonal_mode = both | falling | rising`, with canonical `both` as the exact default program.
Focused verification: `16 passed, 33 subtests passed`; strict-scalar defect lint scanned the repaired source with `FLAGGED 0`.
Racket evidence: canonical default replayed `5/5`; each of three settings has 2 demos + 4 distinct queries and Racket-executed rival comparisons.
Supplementary tickets completed: one allocation experiment proposal and one lawful adversarial witness; neither is a peer safety finding.
Limits: no full production battery, universal rival search, production-parameter approval, or training admission was claimed.
Disposition: routine source-bound repair plus bounded prototype; owner replay and promotion decision remain separate.

## Production repair

The retained audit showed that `generate` passed `seed` and `sample_index` directly into context construction. Values such as booleans, floats, strings, `None`, and negative indices therefore crossed the public API boundary instead of failing closed. The new boundary checks use exact-type tests (`type(value) is int`) so booleans are rejected despite being Python integer subclasses. A negative integer seed remains lawful; a negative sample index raises `ValueError`.

The regression test covers five invalid seed values, five invalid index values, and one negative index under `None`, `easy`, and `hard` difficulty, for 33 failing subcases before the repair. The green scalar-only stage retained `10 passed, 33 subtests passed`. The focused defect detector subsequently scanned the repaired source and reported `FLAGGED 0`.

The original task test also embedded a fixed-depth path assumption and an exact-whitespace comparison between canonical and base Racket text. In a relocated runtime that prevented the relevant assertions from executing. The test now uses `find_root`/`canonical_path`; it compares canonical and base programs after whitespace normalization, while still requiring base `raw_code == target_code` and retaining the exact normalized rule hash `ee2251228926`.

## Parametric extension prototype

`generators/5e8e4691afde/workspace/parametric/prototype.py` adds one isolated episode-level parameter without changing the production generator or canonical data:

- `both`: the byte-for-byte canonical program;
- `falling`: only the `\` diagonal through the relocated center;
- `rising`: only the `/` diagonal through the relocated center.

Input generation, the indicator-to-endpoint path vector, relocated 3×3 frame, fill color, and preserved center remain fixed. For each setting, the prototype selects six distinct production-lawful inputs, executes all selected labels and both alternative-setting predictions with `RacketBridge`, exposes two demonstrations and four queries, verifies that the demonstrations refute both declared rivals, and verifies that every query answer changes under both rivals.

The materializer writes public challenges as the exact bytes returned by `public_challenge_bytes`, names them by `public_challenge_id`, sorts by public ID, rejects duplicate visible payloads, and stores settings/programs/query labels only under `private/`. Evidence at `checks/parametric/5e8e4691afde-diagonal-mode-v1/` records three public IDs, exact rule files, private episodes, a same-input pairwise-distinguishing witness, source/test hashes, a report, and a file manifest. The canonical/default program passed all five labeled canonical pairs.

This remains a proposal. The finite retained episodes only establish separation from the two declared diagonal variants; they do not establish unique program induction, production readiness, approval, or training value.

## Focused verification ledger

- Scalar red: `checks/5e8e4691afde-red-strict-scalars/` — 33 expected scalar subfailures, plus the newly exposed pre-existing whitespace-only authority assertion.
- Scalar green: `checks/5e8e4691afde-green-strict-scalars/` — `10 passed, 33 subtests passed`.
- Parametric red: `checks/5e8e4691afde-red-parametric/` — six expected errors because the tested prototype file did not yet exist; existing repaired tests remained green.
- Parametric green: `checks/5e8e4691afde-green-parametric/` — `16 passed, 33 subtests passed` with real Racket execution.
- Focused audit detector: `checks/5e8e4691afde-after-defect-lint/` — exit 0 and `FLAGGED 0`.
- Materialized episode evidence: `checks/parametric/5e8e4691afde-diagonal-mode-v1/`.

A fresh final task-suite receipt is added before packaging and is the completion gate. No unrelated battery or schedule census was run.

## Supplementary tickets

### `ticket-17ad79dd651dc0ff` — allocation quality

The ticket-seeded sample was `f3076f3858b4`, `8eb9146172f8`, and `5cff0d794bdf`. One record had independent task-level verification; two retained unresolved distribution/API/teaching defects. A bounded probe executed 18 real Racket labels in 2.43 seconds and found valid, distinct generated inputs, but that does not establish parametric identifiability. The proposed owner experiment preserves the 10% evaluation focus, then stratifies the remaining authoring draw into 50% extension-ready gaps, 30% repair-first records, and 20% uniform exploration. Compare 10 baseline-uniform assignments with 10 stratified assignments using verified deliverables per authoring hour; adopt only for at least 20% uplift without increased unresolved safety findings. The sample contained no ARC-GEN or RE-ARC record, which is an explicit coverage gap.

Evidence: `checks/tickets/ticket-17ad79dd651dc0ff/assessment.md`, `probe.json`, and `first-run-diagnostic.json`.

### `ticket-29c307a442daa588` — adversarial witness

A plausible shortcut hard-codes the canonical 23×23/6×6 lattice and scans starts `{0,4,8,12,16,20}`. It fits all four retained canonical examples. A lawful current-generator 27×27 instance with exact overrides contains canonical matches at `[8,24]` and `[16,24]`; the authoritative Racket rule and shortcut disagree in 10 cells. This refutes the shortcut on the current documented domain, so the bounded ticket produced no source-bound peer safety finding.

Evidence: `checks/tickets/ticket-29c307a442daa588/witness.json` and `adversarial_witness.py`.

## Remaining limits

The verification is deliberately scoped to changed behavior. It does not include a full twelve-stage generator battery, large schedule census, exhaustive program search, owner integration, or training-admission decision. The allocation proposal is an experiment, not an automatic policy change. The peer witness is one bounded shortcut probe, not a universal proof of semantic completeness.
