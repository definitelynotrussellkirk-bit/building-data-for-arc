# Proposed anchor-side variant for 0162460030af

**Status: proposed prototype, unapproved.** This directory does not replace the
selected `generate(...)`, alter the canonical Racket authority, change catalog
metadata, or grant training/variant approval.

## Parameter contract

| Item | Contract |
|---|---|
| Parameter | `anchor_side`, exactly `"right"` or `"left"` |
| Original/default | `"right"`; the emitted source is byte-for-byte canonical |
| Alternative | `"left"`; the leftmost object is 8 and colors alternate rightward |
| Episode selection | One `random.Random(seed).choice(("right", "left"))` draw before any pair |
| Complete episode | Three labeled demonstrations and one masked query |
| Inputs | Four fixed lawful scenes with 2, 3, 4, and 6 separated objects |
| Input dependence | None; the same four inputs are used for both settings |

The invariant reasoning is unchanged: extract all nonzero 4-connected objects,
sort by leftmost occupied column, and recolor them with alternating 8 and 2.
Only the endpoint receiving the first 8 is parameterized. The canonical `right`
setting remains pinned to rule hash `617100877d72` and full source SHA-256
`cac9cdefdad193cd609d31fb743a18fb645e4f0b7ed9c48d1e08e5f81bdae035`.
The alternative is admitted only when reversing one guarded expression restores
that exact source.

The demonstrations include two even-object scenes, which refute the other
anchor setting, plus one odd-object scene where both anchors intentionally agree.
The six-object query requires the inferred setting. All labels and rival
predictions are executed through the included protected `RacketBridge`; there is
no Python answer mirror.

## Run from the outer extraction directory

The output directory must not already exist.

```bash
python3 review.py run python3 \
  generators/0162460030af/workspace/parametric/prototype.py \
  --seeds 0 1 --out ../checks/parametric/anchor-side-v1

python3 review.py run python3 -m pytest -q \
  generators/0162460030af/tests/test_parametric_prototype.py
```

Public challenges are written under `public/` using an explicit allowlist: three
training input/output pairs and one test input. Hidden parameters, seeds, Racket
source, rival predictions, and query answers remain under `private/`.

## Evidence boundaries

This is finite evidence for two settings, two seeds, and four authored inputs.
For odd object counts the two settings coincide, so the schedule deliberately
uses even counts where parameter identification matters. Rival checks cover only
the declared two anchor settings and do not prove uniqueness against every
possible rule. Acceptance of the canonical generator does not approve this
extension.
