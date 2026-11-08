# Native parametric family for `5d6fcce80b6a`

This workspace promotes the retained prototype without changing the approved
production generator or canonical rule.

## Private episode parameters

- `copy_diagonal=main|anti`: choose the copied block diagonal. `main` is the
  exact canonical behavior.
- `separator_policy=through_last|strict_between`: identify colored row bounds,
  then either paint every blank row through the last colored row or only blank
  rows strictly between the first and last colored rows. `through_last` is the
  exact canonical behavior.

The default program is copied byte-for-byte to `canonical.rkt`. Inputs are
matched across settings. The first demonstration has an internal and trailing
blank; the second has leading, two internal, and trailing blanks, so two visible
examples identify all four declared settings and reject the bounded shortcut
set. Supported counts are 2–6 demonstrations and 1–4 queries. Query outputs are
14×16, 18×20, 24×26, and 30×30.

## Sequential dependency

A scans the source rows and produces the input-dependent first/last colored-row
bounds. B consumes those bounds to choose which blank source rows become
full-width color-3 separators before the selected diagonal copies are rendered.
A wrong `last_colored` value changes the final output; `audit.py` retains the
protected-Racket case and the native witness helper replays it after
qualification.

## Commands

From the outer packet directory:

```bash
python3 review.py run python3 -m pytest -q \
  generators/5d6fcce80b6a/tests/test_native_parametric_5d6fcce80b6a.py
python3 review.py run python3 \
  generators/5d6fcce80b6a/workspace/parametric/audit.py \
  --out ../checks/5d6fcce80b6a/self-review
python3 WORK/check_public_exports.py \
  WORK/checks/5d6fcce80b6a/self-review/public --demos 3 --queries 1 --summary
python3 review.py run python3 -m arcpuzzles parametric qualify 5d6fcce80b6a \
  --out ../checks/5d6fcce80b6a/qualification --summary
```

The adapter and evidence are reviewer proposals until the owner integrates the
exact bytes, reruns native qualification, and explicitly accepts them. No
training admission is claimed.
