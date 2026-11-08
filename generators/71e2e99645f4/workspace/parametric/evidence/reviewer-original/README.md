# Proposed section-order and class-palette variants for 71e2e99645f4

**Status: proposed task-local prototype, unapproved.** The prototype varies two
small episode-level rule parameters while preserving the canonical object roles,
hole classification, fixed three-section input grammar, and `3×3` row-coded
output.

| Parameter | Allowed values | Canonical/default |
| --- | --- | --- |
| `section_order` | `left_to_right`, `right_to_left` | `left_to_right` |
| `palette` | `canonical`, `swap_center_bottom` | `canonical` |

`right_to_left` reverses only the order in which the three already-classified
sections become output rows. `swap_center_bottom` swaps output colors `8` and
`4`, leaving the no-hole color `2` and edge-hole color `3` unchanged. The
canonical/default program is returned byte-for-byte with SHA-256
`4c0a9e13b111d722867ab8519d03504c09fe23c1da7f1185a0fa55351fceaef8`.
Each alternative replaces only the selected rule's unique final
`(classify r)` expression; the production generator, canonical authority, and
approval records are not modified by this prototype.

A setting is chosen once from the integer episode seed and reused for all three
demonstrations and the query. Four controlled lawful inputs are produced through
the selected generator's exact `fill_color` and `hole_patterns` controls. Each
input makes all four order/palette combinations produce distinct outputs, so
every non-selected declared setting is refuted by every retained demonstration.
All labels, rival predictions, canonical replays, and the shared setting witness
are executed by the bundled Racket runtime; no Python mirror supplies labels.
Public challenge files omit parameters, seeds, Racket source, rival predictions,
and query answers.

From the outer packet directory:

```sh
python3 review.py run python3 \
  generators/71e2e99645f4/workspace/parametric/prototype.py \
  --seeds 0 1 2 3 \
  --out ../checks/parametric/order-palette-v1

python3 review.py run python3 -m pytest -q \
  generators/71e2e99645f4/tests/test_parametric_order_palette.py
```

Seeds `0..3` cover all four parameter combinations. The retained evidence includes
exact `.rkt` programs and hashes, complete private episodes, masked public
challenges, canonical replay of all five supplied pairs, a common-input witness,
source/runtime metadata, and a content manifest. This finite four-setting study
is not production approval, training admission, or proof against undeclared
parameterizations.
