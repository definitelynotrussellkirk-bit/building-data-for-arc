# Native parametric family: e9238d278276

This task-local family preserves the exact canonical `gravity up` program as
`gravity_policy=all_up`. The alternative `signal_ranked_down` counts the cells
in the unique all-9 signal column, uses that count as a one-based rank among
all other active columns from left to right, applies canonical upward gravity,
and then packs only the selected payload column downward while preserving its
original value order.

The input scene is setting-independent. Episodes support 2–6 demonstrations and
1–4 prefix-stable queries; the four query constructions are 14×16, 19×21,
24×27, and a substantive 30×30 case. The first two demonstrations use ranks 2
and 4 and distinguish the two settings plus the declared fixed-rank, reversed
rank, signal-position, all-down, size-based, and sorted-value shortcuts.

Run the focused tests through the packet wrapper, then the reusable audit:

```bash
python3 review.py run python3 -m pytest -q generators/e9238d278276/tests/test_parametric_signal_ranked_down.py
python3 review.py run python3 generators/e9238d278276/workspace/parametric/audit_lessons.py --seeds 64
```

The family is proposed/native and owner-pending. Qualification, acceptance, and
training admission remain separate source-bound operations.
