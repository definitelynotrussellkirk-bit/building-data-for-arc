# Working notes: 8e52225f35b8

## Final design

- Canonical behavior remains byte-for-byte `row_then_column`: split on full-height color-9 separators, close each panel's marked cells by rows and then columns, and paint 8 where at least two panel closures cover a cell.
- The nearby episode-fixed parameter is `closure_order` with exactly two settings: `row_then_column` and `column_then_row`. The alternate Racket source changes only the `double-close` composition.
- Step A is the selected first-axis closure. Its input-dependent intermediate is the three panel-local first-stage masks. Step B closes those masks on the other axis, aligns panels, counts coverage, and thresholds at two. The second pass therefore consumes cells created by the first; swapping the order changes four final cells in every generated scene.
- The native adapter supports 2–6 demonstrations and exactly four queries. Inputs are matched across settings; changing the demonstration count only changes the training prefix, never the four-query bank.

## Sampler decisions

- Three nine-column panels are used throughout the parametric family. Normal scenes are width 29; the substantive maximum query is 30×30 with adjacent full-height separator columns, which the canonical splitter lawfully skips as an empty segment.
- Motif A distinguishes row→column, motif B distinguishes column→row, and motif D supplies a stable all-three-panel overlap. An incomplete shelf and one output-neutral decoy add distractor structure without changing either label.
- The first two demonstrations share dimensions but use opposite horizontal orientation. This refutes a memorized first output/fixed-position rule at the two-demo minimum.
- Decoys are selected only when they preserve both settings' outputs and make panel 0 reach at least seven local columns. This repairs a fresh-seed 30×30 coverage failure found during adversarial probing.

## Findings repaired

1. The old easy band emitted only two panels, making “covered by at least two” indistinguishable from “inside every panel.” Ordinary base generation now emits three or four panels and requires both a three-way overlap and an exactly-two overlap.
2. The first full-size parametric draft used only 22 of 27 non-separator columns for some seeds. A focused regression now checks multiple fresh seeds; final full-size scenes use at least 25 columns, all 30 rows, and at least 27 marks.

## Finite evidence and limits

- Focused tests cover exact canonical preservation, matched inputs, 2/6-demo boundaries, four distinct queries, first-turn privacy, strict malformed/stale/duplicate rejection, input-dependent intermediates, protected-Racket parity, and seed-independent 30×30 spread.
- The reusable adversarial probe checks six seeds, both settings, 2/6-demo corners, eight plausible semantic rivals, crossed orientation/order controls, forged certificates, and protected-Racket labels.
- Authoring preflight and causal witness passed on source-bound final bytes. These are reviewer evidence only; owner qualification, acceptance, and training admission remain pending.
