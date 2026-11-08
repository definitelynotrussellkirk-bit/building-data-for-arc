# Proposed selected-color-cardinality variant for 4d5bb3c0250b

**Status: proposed prototype, unapproved.** This workspace does not alter the
production generator's selected rule, catalog approval, or canonical authority.

## Contract

- Parameter: `selected_color_count`, literal integer `1` or `2`.
- Default: `1`; materialized Racket source is byte-for-byte canonical and pinned
  by SHA-256 `0bc50653fe240f5837696c7c20156315278dbb9f9cd295877e76d28799fb5dc5`.
- Alternative: `2`; a guarded one-token predicate change selects the unique
  block with exactly two distinct nonzero colors.
- Episode: one parameter draw before all pairs, three demonstrations, and four
  distinct queries.
- Inputs: each has exactly one one-color block, exactly one two-color block, and
  only three-color distractors. The same input therefore distinguishes both
  settings while preserving the separator/block/crop invariant.
- Labels and rival predictions: exact execution through the bundled protected
  Racket bridge. Public exports contain only train input/output pairs and masked
  query inputs; hidden parameters, seed, source, rivals, and query labels remain
  private.

## Run from the outer extraction directory

The evidence output directory must not already exist.

```bash
python3 review.py run python3 \
  generators/4d5bb3c0250b/workspace/parametric/prototype.py \
  --seeds 0 1 2 3 4 5 6 7 --demo-count 3 --query-count 4 \
  --out ../checks/parametric/color-cardinality-v1

python3 review.py run python3 -m pytest -q \
  generators/4d5bb3c0250b/tests/test_parametric_prototype.py
```

## Evidence boundary

This is bounded evidence for two settings, twelve authored fixtures, and the two
declared parameter rivals. It is not a proof over all grids or rival rules.
Acceptance of the repaired canonical generator does not approve this extension.
