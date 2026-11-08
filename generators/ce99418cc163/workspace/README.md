# Reusable review tools

Run commands from an extracted packet root; `run_with_racket.py` sets the
repository working directory and uses the bundled offline Racket runtime.
Output destinations must be new so failed evidence is never overwritten.

## Full lesson census

```bash
python3 run_with_racket.py python3 generators/ce99418cc163/workspace/review_probe.py --out ../checks/new-census --seeds-per-band 34
```

Produces 612 distinct draws and 306 overlapping three-demo/one-query lessons:
34 seeds × 6 draws × 3 bands; three cyclic lesson starts per seed. Seeds are
`1_000_000*(band_index+1) + 104729*k`, k=0..33. Scores the generator's actual
rival declarations against every canonical pair, independent exhaustive
rectangle enumeration, and batched public `Catalog.apply` Racket results.
Retains grids, labels, hashes, source identities, disagreements and unique-input
counts. Public `Catalog.generate` parity is checked once per band at seed 17.
All three default schedule offsets are covered; resampled/shorter lessons are
not automatically covered. This is evidence, not a training-data exporter.

## Assembly-policy mutation

```bash
python3 run_with_racket.py python3 generators/ce99418cc163/workspace/assembly_probe.py --census ../checks/new-census --out ../checks/new-assembly
```

Reuses already reference-labelled rows. Accepts a consecutive-demo control and
detects a deliberately constructed ambiguous lesson that drops teaching grids.
Only flags a rival when it fits every demo AND disagrees on the actual query.
No model execution or additional Racket calls are required. This is a diagnostic
negative, not a naturally failed solve or a measured production exporter defect.

## Read-only audits

```bash
python3 run_with_racket.py python3 generators/ce99418cc163/workspace/audit_probe.py --out ../checks/new-audits
```

Reproduces the assignment's two separate audit findings without editing either
target. Uses the supported `arcpuzzles apply` CLI and records exact source/rule
hashes, grids, overrides, actual controls, validator decisions and reference
receipts. Source revisions may resolve the defects and then make assertions fail.

## Exact delta replay

After preparing a return with `package_return.py`:

```bash
python3 repo/generators/ce99418cc163/workspace/verify_handoff.py --original /path/to/original-packet.zip --delta /path/to/review-response.zip --fresh-root /path/to/new-copy --out checks/new-replay
```

Extracts the original into a new external directory, checks and applies the
exact ZIP patch, compares every patched file's bytes to this working copy,
checks the final solve's generator hash, installs the original bundled runtime,
and reruns the focused tests plus all 12 task battery stages. Records actual
working directories and command statuses. Does not copy a repository tree or
installed runtime into the returned evidence. Rebuilding the outer ZIP after
adding replay reports is safe only if `patches/source.patch` remains identical.

The original packet contains no selected-task frozen legacy test fixture.
New tests are applied explicitly in the fresh copy rather than silently assumed
to be included by the portable-runtime manifest.
