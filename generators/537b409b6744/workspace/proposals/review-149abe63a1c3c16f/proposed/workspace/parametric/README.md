# Nearest/farthest candidate selection — prototype

This task-local extension is **proposed and unapproved**. It adds one bounded
rule parameter, `candidate_selection`, with values `nearest` and `farthest`.
`nearest` is the canonical default and its Racket text is required to match the
selected canonical program byte for byte. `farthest` changes only the primary
gap comparison in the candidate sort; wall-size tie-breaking and the entire
pass-through transformation remain unchanged.

The parameter is chosen once per episode from a deterministic SHA-256 digest of
the episode seed and is then shared by all three demonstrations and the query.
The retained evidence command explicitly materializes one complete episode for
each value on the same four generated inputs. Every input has both a nearer and
a farther qualifying mover/wall pair, so each demonstration distinguishes the
two settings.

## Run from the outer packet directory

```bash
python3 review.py run python3 \
  generators/537b409b6744/workspace/parametric/prototype.py evidence \
  --seed 19073 --out ../checks/parametric/candidate-selection
```

The command writes exact Racket sources, two public challenges, private replay
records, a shared differing-output witness, and a hash-bound manifest. Public
challenge files contain demonstration inputs/outputs and query inputs only; they
omit the parameter, program text, source metadata, and query answers.

Focused tests:

```bash
python3 review.py run python3 -m pytest -q \
  generators/537b409b6744/tests/test_parametric_extension.py
```

All retained labels are freshly executed by the included `RacketBridge` and
checked against a Python parity mirror. The evidence covers two values, one seed,
and four shared inputs. It is not a production API, catalog approval, training
admission, or proof that the demonstrations exclude every undeclared rival.
