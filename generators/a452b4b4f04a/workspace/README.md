# Reusable source-bound probes

These tools run from the extracted review packet plus its returned delta. They
need the packet's Racket wrapper, or a working local Racket installation. They do
not label training data with Python. All decisive parity and counterexample
outputs are obtained from the actual canonical Racket authority.

## Reproduce the repaired task

From `packet_root`:

```sh
python3 run_with_racket.py python3 -m pytest generators/a452b4b4f04a/tests -q
python3 run_with_racket.py python3 -m arcpuzzles check a452b4b4f04a --battery --timeout 4000 --phase after --out ../checks/after
python3 run_with_racket.py python3 generators/a452b4b4f04a/workspace/review_probe.py --per-band 600 --lessons 100 --cycles 20 --out ../checks/qualification_final.json
```

`review_probe.py` copies current sources into a fresh standalone runtime using
`arcpuzzles.runtime.prepare_runtime`, removes inherited Python-path assumptions,
opens the runner's real Racket bridge, and records generator/rule/probe hashes.
The output reports the **actual** temporary runtime directory; it is not guessed
from source depth. The `--lessons` parameter means lessons **per band**, not total.

The probe checks all canonical pairs, 600 default cases per band, 243 exact-axis
combinations, 100 ordinary real-runner lessons per band, and all three starts of
the default cycle for seeds 0–19 in every band. It iterates the generator's actual
rival declarations, first verifies that claimed canonical shortcuts match every
canonical pair, and records refutations from demonstrations only. It checks
runner sample-index drift rather than assuming lesson assembly preserves raw
indices. Unique inputs, pair uses, overlapping cyclic windows, and source hashes
are reported separately. `geometry()` is an independent Python cross-check, not
a substitute authority.

## Reproduce the adversarial audits

```sh
python3 run_with_racket.py python3 generators/a452b4b4f04a/workspace/audit_targets.py --per-band 300 --out ../checks/adversarial_audits.json
```

This makes a separate relocated runtime containing only the two fixed audit
targets plus shared runtime files. It samples 900 row-key cases and exhausts all
256 profile/palette/seed-position inputs of the frame task in three bands (768
uses, not 768 distinct inputs). It writes an aggregate report and two compact
counterexample JSON files, including canonical Racket outputs, rival outputs,
source hashes, reproduction controls, validator results, and domain status.
The rivals are deliberately incomplete diagnostic programs, never solvers to
promote or training labelers. Audit targets are not patched.

## Interpreting results

A probe process returning zero means its stated assertions held. Inspect its
`passed` and `failures` fields as well as its exit code. The frame audit's
`passed=true` means the shortcut was successfully **reproduced**, not that the
audited generator has no issue. The row-key distractor is rejected by that
validator and is explicitly a domain question.

The finite rival tests and Python solve provide no measured Qwen accuracy gain.
No generator or Racket source changes were made after the final solve was prepared. A future
generator change requires a fresh solve episode, with the previous one retained.
Do not read the private query labels to improve the reviewer-authored solve.
