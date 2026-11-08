# Proposed rotation-direction variant for 3eff273eeb83

**Status: proposed prototype, unapproved.** This directory does not replace the
selected production generator, alter the canonical Racket authority, change
catalog metadata, or grant training/variant approval.

## Parameter contract

| Item | Contract |
|---|---|
| Parameter | `rotation_direction`, exactly `"clockwise"` or `"counterclockwise"` |
| Original/default | `"clockwise"`; emitted source is byte-for-byte canonical |
| Alternative | `"counterclockwise"`; preserve each offset and turn it the other 90-degree direction |
| Episode selection | One deterministic seed-based choice before any pair |
| Complete episode | Three labeled demonstrations and one masked query |
| Inputs | Four lawful scenes covering all source directions; both turns remain in bounds |
| Input dependence | None; input generation does not inspect the hidden setting |

The invariant reasoning is unchanged: locate the color-5 pivot, recolor every
original color-2 radial-line cell to 3, preserve its pivot-relative distance,
and draw the rotated copy in color 2. Only the sign of the quarter-turn is
parameterized. The canonical clockwise setting remains pinned to normalized
rule hash `3ac43b22416f` and full source SHA-256
`5e10aaa7e9867e2390957e6659b9e0e5581948b77e63c99c2f2ebc6e0c81bffe`.
The counterclockwise source is admitted only when reversing one guarded
coordinate site restores that exact canonical source.

Every demonstration distinguishes the two declared settings, and the query
also differs. All labels and rival predictions are executed through the
included protected `RacketBridge`; the Python transform is used only as an
independent test oracle.

## Run from the outer extraction directory

The evidence output directory must not already exist.

```bash
python3 review.py run python3 \
  generators/3eff273eeb83/workspace/parametric/prototype.py \
  --seeds 0 1 --out ../checks/parametric/rotation-direction-v1

python3 review.py run python3 -m pytest -q \
  generators/3eff273eeb83/tests/test_parametric_rotation_direction.py
```

Public challenges are written under `public/` using an explicit allowlist:
three training input/output pairs and one test input. Hidden parameters, seeds,
Racket source, rival predictions, and query answers remain under `private/`.
The root manifest hashes every emitted evidence file.

## Evidence boundaries

This is finite evidence for two settings, two seeds, and four generated inputs
per episode. Rival checks cover only the declared clockwise/counterclockwise
choice and do not prove uniqueness against every conceivable rule. Acceptance
of the canonical generator does not approve this extension.
