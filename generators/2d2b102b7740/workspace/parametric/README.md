# Proposed `extension_mode` rule prototype

This task-local prototype leaves the selected generator and canonical production
rule unchanged. It chooses one hidden setting once per episode:

- `forward` — the canonical/default behavior: continue the blue arithmetic line
  only beyond its last blue cell.
- `both` — continue the same step before the first blue cell and after the last.

All retained inputs remain lawful for generator `2d2b102b7740` and deliberately
contain at least one in-bounds continuation position on each end. Three labelled
demonstrations and one masked public query are emitted per setting. The builder
executes the exact materialized Racket for every label, compares a Python debug
mirror, checks the default normalized rule hash against `8db0d36e6e45`, runs the
other setting as a rival, and rejects an episode unless its demonstrations
separate the two settings.

From the outer packet directory, build fresh evidence with:

```sh
python3 review.py run python3 \
  generators/2d2b102b7740/workspace/parametric/build_prototype.py \
  --out-dir ../checks/parametric/2d2b102b7740-extension-mode-v1
```

The output directory must not already exist. `public/` omits the episode seed,
hidden setting, Racket source, and query answer. `private/` retains those fields,
exact program hashes, rival outputs, commands, runtime identity, and source
hashes. `summary.json` is the concise pass/fail receipt.

## Scope and limits

This is **proposed prototype evidence**, not a production API or approval. It
covers only `forward` and `both`, uses a finite six-scene lawful input bank, and
checks one declared parameter rival. It does not prove identifiability against
all possible programs or authorize changes to the selected canonical rule.
