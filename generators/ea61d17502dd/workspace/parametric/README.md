# Proposed vertical-bounds parameter for `ea61d17502dd`

This directory is a **prototype**, not a production rule change or approval.
The selected generator, canonical Racket authority, `RULE_HASH`, and catalog
records are intentionally unchanged.

## Parameter

`vertical_bounds_mode` is chosen once per episode from two bounded values:

- `all_markers` — canonical/default. The output rectangle spans the crossing row
  and both vertical special markers. `program_for("all_markers")` returns the
  exact canonical Racket text and normalized rule hash `b956a6f1bc99`.
- `crossing_to_farthest` — proposed alternative. The rectangle spans the crossing
  row and only the farther vertical special marker.

Everything else remains invariant: crossed contiguous strands, four role colors,
marker recovery, crossing ownership, horizontal bounds, and parity weave logic.
The input grammar does not depend on the mode. Teaching does: each episode
includes a labelled straddled-marker input (train index 1) because outside-only
examples make these two settings agree. The query also straddles so it tests the
inferred episode rule.

## Run the retained Racket probe

From the outer extracted packet directory:

```sh
python3 review.py run python3 \
  generators/ea61d17502dd/workspace/parametric/prototype.py \
  --seed 271828 --difficulty medium \
  --out ../checks/parametric/vertical-bounds-seed-271828
```

The command executes both exact Racket programs, checks them against independent
Python mirrors, writes one complete 3-train/1-test episode per setting, verifies
that the opposite setting fails a labelled demonstration, and retains a lawful
input whose outputs differ. Public `challenge.json` files contain labelled
training pairs and query inputs only; they omit the hidden mode, seed, program,
reference code, and query answer.

`--python-only` is available for debugging but is explicitly marked unverified
and is not acceptable evidence for this prototype.

## Focused tests

```sh
python3 review.py run python3 -m pytest -q \
  generators/ea61d17502dd/tests/test_parametric_prototype.py
```

The tests are prototype-scoped. They do not assert production admission or
modify canonical repair coverage.

## Limits

The retained probe is bounded to its recorded seed and the two declared modes.
It does not establish universal identifiability. A lesson without a labelled
straddled-marker case can leave the modes indistinguishable. The alternative is
purposefully the previously documented canonical-fitting rival, promoted only
as an explicit nearby teaching variant; it remains unapproved for production.
