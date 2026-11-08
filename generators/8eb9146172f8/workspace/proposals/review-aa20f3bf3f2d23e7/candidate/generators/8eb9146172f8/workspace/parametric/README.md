# Deflection step size — proposed parametric prototype

This task-local prototype is separate from the approved production generator,
canonical Racket authority, and training admission. It preserves the original
family's marker roles and reasoning: cyan `8` edge markers emit inward rays;
red `2` markers select perpendicular rows or columns; each encounter moves the
ray away from the red edge before painting; off-canvas tails remain clipped.

## Parameter

| Name | Values | Original/default | Effect |
|---|---|---|---|
| `step_size` | exact integer `1` or `2` | `1` | Number of lateral cells moved at every red-selected row/column. |

`step_size=1` returns the exact canonical Racket text byte-for-byte.
`step_size=2` changes only the four signed values in the canonical
`shift-val` block; unexpected source structure raises instead of silently
materializing another rule. Input constraints do not depend on the parameter.
Without `--step-size`, `STEP_SIZES[seed % 2]` is selected once and retained for
every demonstration and query in the episode.

## Exact commands

Run from the outer extraction directory containing `review.py`:

```bash
python3 review.py setup
python3 review.py run python3 generators/8eb9146172f8/workspace/parametric/prototype.py \
  --all-settings --seed 2468 --n-train 4 --n-test 4 \
  --out ../checks/parametric-step-size
python3 review.py run python3 -m pytest -q \
  generators/8eb9146172f8/tests/test_parametric.py
```

A single deterministic episode can be requested with either an explicit setting
or the seed-selected setting:

```bash
python3 review.py run python3 generators/8eb9146172f8/workspace/parametric/prototype.py \
  --seed 101 --step-size 2 --n-train 4 --n-test 4 \
  --out ../checks/parametric-step-size-single
```

`n_train` and `n_test` are independent exact integers in `1..32`. Invalid
settings, bool-as-int values, duplicate visible payloads, nonempty output
locations, and inability to obtain the requested number of unique distinguishing
inputs fail loudly rather than truncating.

## Evidence contract

Labels for both declared settings are executed with the packet's pinned
`RacketBridge`; an independent Python loop must match every execution. Inputs
come from the unchanged selected production generator with exact lawful axis
overrides. Candidate inputs are retained only when step sizes `1` and `2` yield
different outputs. The default evidence run contains four labeled demonstrations
and four distinct unlabeled query inputs for each setting. Every demonstration
refutes the sole alternate declared setting, so identification uses demonstrations
alone; every query also changes under the rival, but query answers are never used
to select the setting.

The output directory separates visibility:

- `public/challenge-<sha256>.json` contains only labeled demonstrations and
  query inputs. The filename is the SHA-256 of the exact visible bytes produced
  by `reviewer_support.public_challenge_bytes`.
- `private/episode-NNN.json` retains the seed, parameter, generator provenance,
  exact Racket text/hash, query outputs, rival hashes, and identifiability checks.
  Batch episodes are ordered by opaque public ID before these private ordinals are assigned.
- `private/rules/` retains the exact executed Racket bytes; each rule filename is
  their SHA-256. `report.json` and `manifest.json` summarize and hash the bounded run.

Changing private metadata or hidden query outputs cannot change public bytes or
IDs. Public filenames contain no seed, setting, setting-associated ordinal,
reference code, hidden parameter, or query answer.

## Limits

Identifiability is only against the declared `{1, 2}` family, not all possible
ARC programs. The prototype stays within the production generator's current
`9..20` by `9..22` domain and does not claim larger-grid coverage. It changes no
production source, approval, canonical task, shared runtime, or dataset identity.
