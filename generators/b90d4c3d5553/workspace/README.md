# Task-local review tools — b90d4c3d5553

The selected implementation is `../generator.py`. These tools are not alternate generators and are not a source of admitted labels. They use the source packet's existing Python/NumPy dependencies; no new dependency is added. Python 3.12+ is required by the repository.

## One-command qualification

From the repository root after applying the return patch:

```bash
PYTHONPATH=src python3 -B generators/b90d4c3d5553/workspace/qualify.py \
  --out /tmp/b90-review-checks-new --count 2000 --battery
```

Use a new output directory. The driver explicitly runs the task pytest suite, root pytest suite, independent geometry audit with **required Racket parity**, the Cartesian stress sweep and, with `--battery`, all twelve repository battery stages. It retains per-command logs, return codes, timeouts, elapsed times, and generator SHA-256 in `commands.json`. It continues collecting evidence after nonzero commands and exits nonzero if any required command fails. The static tests' Racket skips do not override the required parity result.

Install/provide Racket using the repository's supported runtime mechanism before reference qualification. No automatic install, Python fallback, authority rewrite, or approval edit is performed by these tools. The review environment could not supply Racket; runtime-present parity is still to be executed.

## Individual probes

```bash
PYTHONPATH=src python3 -B -m pytest generators/b90d4c3d5553/tests -q
PYTHONPATH=src python3 -B -m pytest -q
python3 -B generators/b90d4c3d5553/workspace/stress_counts.py \
  --out /tmp/b90-cartesian.json
python3 -B generators/b90d4c3d5553/workspace/reference_probe.py \
  --count 2000 --racket --out /tmp/b90-reference.json
```

`reference_probe.py --generator PATH` compares another generator against the same seed/index schedule. Omitting `--racket` gives explicitly Python-only evidence. Each band uses seed `1009+i`, index `7*i+3`, for `i=0..count-1`. Global distinct counts are set unions; these crossed draws are correlated. Output includes canonical acceptance, deterministic replay, structural coverage, rival disagreements, source hashes, and the exact hand witness. Racket mode stages the normal executable layout with `prepare_runtime`, then applies the unchanged canonical program to three canonical inputs, the hand witness and 16 samples from each of four bands. The task runtime test separately checks all 64 forced orientation pairs.

`stress_counts.py` exhausts the 57,600 count/orientation tuples on 10x14, then every advertised h/w/orientation combination at maximum counts (10,560 more). Difficulty cycles by case, so this is not all possible seeds or all count/size/difficulty combinations. It checks exact observed overrides, validation, and the independent predicted number of changed cells. It does not execute Racket.

## Integration

The compact return contains `patches/source.patch` rooted at `repo/`. From the matching, pristine packet root:

```bash
git apply --check /path/to/extracted-return/patches/source.patch
git apply /path/to/extracted-return/patches/source.patch
```

A Git working tree is not required for this patch operation. Divergent source should be reconciled rather than forced. Root reports and checks in the return are review artifacts; they are not source files to overlay on unrelated generators. Rule and approval metadata are unchanged.
