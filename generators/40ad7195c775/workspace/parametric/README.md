# Waypoint choice: proposed parametric prototype

**Status: proposed prototype; not production-approved.** This workspace experiment does not alter the selected canonical Racket authority, catalog state, or training admission.

## Parameter

`waypoint_choice` is chosen once per episode from `{left, middle, right}`. The canonical/default setting is `middle`; its Racket source is byte-for-byte the canonical program. All settings preserve the task's role inference, orientation normalization, ordered stripe traversal, endpoint-colored staircase, and preservation of non-route cells. The only changed rule step is which cell of each contiguous three-cell waypoint run the path crosses.

Every lawful input in the retained episodes distinguishes all three settings: the selected crossing cell and the following route column differ. The parameter is hidden from the public challenge and must be inferred from the labeled demonstrations. Input grammar is unchanged except that the variant relies on the existing three-cell waypoint runs.

## Run

From the extracted review directory:

```bash
python3 review.py run python3 generators/40ad7195c775/workspace/parametric/prototype.py \
  --seeds 0 1 2 --out ../checks/parametric/waypoint-choice
```

Focused tests:

```bash
python3 review.py run python3 -m pytest -q \
  generators/40ad7195c775/tests/test_parametric_waypoint_choice.py
```

The materializer writes model-visible challenges under `public/`, evaluator-only labels and metadata under `private/`, and exact Racket sources under `rules/`. Its private manifest records parameter values, source hashes, exact Racket applications, candidate outputs, runtime identity, commands, and finite-evidence limits.

## Scope and limits

This is a three-setting task-local authoring prototype, not a production parametric API. The retained checks establish Racket/Python parity and demonstration-level distinction for seeds 0, 1, and 2 only. They do not prove universal identifiability against every imaginable rival rule.
