# Proposed priority-direction family (prototype only)

This runnable prototype is separate from the selected canonical generator and
Racket authority. It does **not** change production behavior or the pinned
canonical `RULE_HASH`.

- Parameter: `priority_direction`
- Allowed values: `left_to_right`, `right_to_left`
- Canonical/default setting: `left_to_right`
- Episode selection: `ALLOWED_PRIORITY_DIRECTIONS[seed % 2]`, chosen once and
  shared by two demonstrations and one query
- Dependent input constraint: each retained demonstration has two distinct
  legend-colour seeds in every chamber, so the opposite direction gives a
  different output

Each setting has an exact standalone Racket program under `rules/`. The probe
executes both Racket settings on every pair, checks a Python mirror only as a
secondary assertion, and verifies that every labelled demonstration refutes the
opposite parameter setting. Public challenge files hide the parameter and query
answer.

Run from the outer packet directory so the bundled Racket runtime is selected:

```bash
python3 review.py run python3 \
  generators/e03758508612/workspace/parametric/prototype.py \
  --seed 17 \
  --out ../checks/parametric/priority-direction-seed17.json \
  --write-public generators/e03758508612/workspace/parametric/examples
```

The evidence is bounded to two settings and one seed. This is a **prototype**,
not production approval, and it does not exhaust undeclared alternative rules.
