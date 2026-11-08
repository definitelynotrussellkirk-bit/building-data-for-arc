# Extent-tie policy parametric prototype

This task-local prototype leaves the production generator, canonical Racket
program, and `RULE_HASH` unchanged. It declares one bounded parameter selected
once per episode:

- `tie_policy="column"` (default): exact canonical behavior; a row/column
  extent tie clears the matching column.
- `tie_policy="row"`: the proposed alternative; an extent tie clears the
  matching row.

The input grammar is unchanged. Complete episodes contain three demonstrations
and four distinct hidden queries. Every pair is generated from a varied
multi-band teaching slot that contains a real extent tie, so every demonstration
and query distinguishes the selected setting from the other setting.
`public_challenge()` removes the policy, source metadata, Racket program, and
query outputs.

Public challenge files are named from the SHA-256 identity returned by the
shared `public_challenge_id()` helper over the exact visible challenge bytes.
Visible demonstration labels therefore contribute to the ID, while private
metadata and hidden query labels do not. The evidence writer emits those exact
bytes under `public/challenge-<sha256>.json`, retains the aggregate
`public_challenges.json` for compatibility, sorts its keys, and rejects duplicate
visible challenges.

Run the focused contract tests from the packet root:

```bash
python3 review.py run python3 -m pytest -q \
  generators/ec9cf2c80d58/tests/test_parametric_tie_policy.py \
  generators/ec9cf2c80d58/tests/test_parametric_public_names.py
```

Materialize both programs and verify both complete episodes with the included
Racket runtime:

```bash
python3 review.py run python3 \
  generators/ec9cf2c80d58/workspace/parametric/build_evidence.py \
  --out ../checks/parametric
```

The evidence builder refuses to write into a nonempty directory. It records
source hashes, exact materialized rule text, Racket runtime identity, private
episodes, masked public challenges, opposite-setting predictions, and a shared
cross-setting witness.
