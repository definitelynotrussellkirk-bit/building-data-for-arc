# Proposed selector-role extension for `a9f315ca9cc7`

This task-local prototype is deliberately separate from the selected production
generator and canonical Racket authority. It varies one bounded, episode-level
rule parameter while preserving the original self-tiling reasoning structure.

| Parameter | Allowed values | Original/default |
|---|---|---|
| `selector_role` | `foreground`, `background` | `foreground` |

For both settings, the complete 3×3 input is simultaneously the block mask and
the copied template. The solver must inspect each mask cell, decide whether its
role is selected, and place an exact copy of the input in the corresponding 3×3
output block. `foreground` selects nonzero cells and is byte-for-byte the
canonical `(self-tile g)` rule. `background` selects zero cells with
`(self-tile g (lambda (v) (= v 0)))`.

The input grammar remains the production grammar: 3×3, background 0, exactly one
nonzero foreground color, and both roles present. That last constraint makes the
parameter observable. Each retained episode fixes one deterministic parameter
value for three demonstrations and one query. Every demonstration and query
produces different outputs under the rival setting.

From the outer packet extraction directory, run a fresh evidence build:

```bash
python3 review.py run python3 \
  generators/a9f315ca9cc7/workspace/parametric/verify.py \
  --out-dir ../checks/parametric/selector-role-v1
```

The verifier materializes both complete Racket rules, checks the canonical
setting against all six labelled canonical pairs, executes every retained label
through the bundled offline Racket bridge, verifies Python/Racket parity, retains
a lawful setting-difference witness, and writes private evidence plus public
challenges that omit the hidden parameter, rule source, and query answer.

This is a **proposed prototype**, not a production API, catalog approval, or
claim of universal identifiability. Its evidence is bounded to the two declared
settings, retained seeds, production input grammar, and one explicit parameter
rival.
