# Adversarial-witness ticket — 22d736100571

**Outcome: finding.** Current source SHA-256 `67378d6b4be7a0d84490fdc90a8bb4e94a09e75854eb9ee6b1cfdb3ae7f768b6` matches the ticket pin; executed rule hash is `8557e6e9275d`. No peer source was edited.

The tested rival fills an original zero only when its immediate horizontal or vertical neighbors are both red, in one simultaneous pass. This is plausible because the intended rule fills the sole missing cell inside a complete red row/column span, while short generated spans often place the gap directly between adjacent red cells.

A fresh source-bound Racket generation of seed 0, easy, sample indices 0–3 produced three demonstrations and one query with no rejection. The rival matched all three demonstration labels but disagreed with the query at `(row=2, column=7)`: the rival paints red `2`, while the selected Racket rule leaves `0` because the relevant full span does not satisfy the intended exactly-one-gap condition. The query passes the current generator's `self_check`; therefore it is a lawful generated witness and a teaching-support defect, not a wrong saved label.

`witness.json` retains the full input, Racket output, rival output, exact differing cell, source/rule pins and validation result. The same exact-source issue is already present in the task's current unresolved review index; the new probe independently replays it rather than claiming novelty. Scope is one ordered lesson only—no peer battery or census was run. Separate retained override-contract defects were not re-probed.

Commands from `WORK/`:

```sh
python3 run_with_racket.py python3 -m arcpuzzles generate 22d736100571 \
  --count 1 --seed 0 --sample-index 0 --difficulty easy --train 3 --test 1 \
  --allow-unapproved --out ../checks/tickets/ticket-edd2d68e817adeae/lesson.jsonl
PYTHONPATH=repo/shared/runtime:repo python3 \
  checks/tickets/ticket-edd2d68e817adeae/analyze_witness.py
```

The Racket wrapper took 4.86 seconds.
