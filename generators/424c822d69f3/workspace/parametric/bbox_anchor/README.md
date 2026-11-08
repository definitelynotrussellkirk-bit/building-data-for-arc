# Rectangle-anchor implementation

**Status:** task-local implementation used by the native root adapter. It does not
alter the approved `generator.py`, canonical authority, catalog approval, or training
admission. Source parent: `training:ddf7fa4f`.

## Rule family

Each episode fixes one private `anchor` value while preserving the task grammar:
read row-0 markers, find each color-5 rectangle, compute one horizontal point, choose
the uniquely nearest marker, and recolor the whole rectangle.

| `anchor` | Horizontal point |
| --- | --- |
| `midpoint` | `(left + right) // 2`; exact byte-for-byte canonical default |
| `left_edge` | left bbox column |
| `right_edge` | right bbox column |

All admitted inputs pass the approved generator's domain checks and have no nearest
marker tie under any declared anchor. Every retained demonstration set contains a
left-edge witness and a right-edge witness. The three exact Racket programs are fit to
demonstrations only; query answers never select the setting.

The supported native counts are 2–6 demonstrations and exactly four distinct queries.
One query is always a substantive 30×30 stress scene with six separated rectangles,
218 foreground cells, and left/right/bottom boundary contact. The remaining examples
are generated constructively by the approved source generator.

## Run

From the extracted packet root:

```sh
python3 review.py run python3 -m pytest \
  generators/424c822d69f3/tests/test_parametric_anchor.py -q
```

The root-level native adapter is
`generators/424c822d69f3/workspace/parametric/adapter.py`; this directory's adapter is
retained as a direct implementation surface. Both contracts declare the same anchor
values, canonical default, and count limits.

The episode writer separates visible challenge bytes under `public/` from settings,
query labels, programs, source hashes, and certificates under `private/`. Public IDs
are hashes of exact visible bytes. Existing destinations, empty batches, duplicate
visible payloads, stale source identities, and incorrect labels are rejected.

## Causal structure and limits

Step A extracts each rectangle bbox and computes the selected anchor column. Step B
uses that intermediate column to select a unique nearest marker and paint the entire
rectangle. A protected-Racket counterfactual in the returned review changes the
intermediate anchor and therefore changes the final label.

The finite rival family is the three declared anchors plus two source-task shortcuts
(`rank_order`, `vertical_overlap_only`). Passing these checks is not a universal
identifiability proof. The family remains reviewer-ready only until the owner replays
qualification and accepts the exact integrated bytes.
