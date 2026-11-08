# Reusable task probes

The selected generator is ../generator.py. These tools audit that source; neither generates authoritative Python labels.

## Lesson and information-loss probe

From an extracted review packet root, using a new output directory:

```sh
python3 run_with_racket.py python3 generators/84def340ce03/workspace/lesson_probe.py --out ../checks/lesson-probe-new --baseline-generator ../checks/semantic-review/baseline_generator.py --expected-generator-sha256 8ea98607c8e772a16787bab201e6ce235f339d25bcf5e4f5f6c560db8b0eff61
```

The preserved baseline comes from this return's checks/ evidence. Restore the evidence bundle first if the packager bundled it. The probe iterates the selected source's actual CANONICAL_SHORTCUTS and LESSON_COMPETITORS declarations, verifies canonical fit, draws at least 100 seeds per band, checks every three-cycle start, and obtains labels through public Catalog.apply in batches of at most 64. It separates per-band uniqueness from cross-band duplicates and input changes from output changes. Its compressed oracle receipts have exact restoration hashes.

Known source and callable hashes have different meanings: the canonical stored-source SHA is distinct from the public apply receipt's legacy rule_text_sha256, which hashes runtime callable text. The probe binds both identities separately.

## Domain probe

```sh
python3 run_with_racket.py python3 generators/84def340ce03/workspace/domain_probe.py --expected-generator-sha256 8ea98607c8e772a16787bab201e6ce235f339d25bcf5e4f5f6c560db8b0eff61 --out ../checks/domain-probe-new
```

This tests lawful low-information matrices and actual invalid inputs, using literal expected outputs and public Racket execution. It documents the remaining generic mutation-gate mismatch; it does not bypass a gate or change admission.

## Focused regressions

```sh
python3 run_with_racket.py python3 -m pytest generators/84def340ce03/tests -q
```

Known controls set to None are intentionally equivalent to omission. The full return explains genuine baseline failures, early probe/test-harness corrections, and the final source hash. The final patch is also replayed into a fresh original extraction before handoff.
