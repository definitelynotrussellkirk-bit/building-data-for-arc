# Boolean result, then component selection

This native family has one episode-fixed parameter:

| `finish` | Executed rule |
|---|---|
| `full_result` | Exact canonical source: infer union, intersection, or XOR from the top row, then write the full red result for the bottom operands. |
| `mark_largest_component` | Perform the canonical Boolean result first, recompute its four-connected red components, and recolor the unique largest component cyan (8). |

The alternate setting is genuinely sequential. Stage B cannot know which cells
belong to the selected component until Stage A has inferred the demonstrated
operator and materialized its bottom result. The retained counterfactual forces
union as Stage A; on the qualified witness this changes the selected component
and the final output.

`adapter.py` loads the exact adjacent `prototype.py`. The interface supports
2–6 demonstrations and independently 1–4 queries. Inputs are identical across
settings for a given seed/count, query prefixes are stable, and the four-query
bank is deterministic and distinct. The first two demonstrations reject the
other setting plus six declared component and wrong-intermediate shortcuts.

The equal-square 2×3 layout has shape `(2p+1) × (3p+2)`. Therefore `p=9`, or
19×29, is the lawful ARC-limit maximum; an exact 30×30 case would violate the
canonical grammar. The largest query uses that maximum with substantive content.

From the packet outer directory:

```sh
python3 review.py task-tests a20ecf84f041 --phase after --out ../checks/a20ecf84f041-tests
python3 review.py run python3 generators/a20ecf84f041/workspace/parametric/self_audit.py --out generators/a20ecf84f041/workspace/parametric/evidence/current/self-audit.json
python3 review.py run python3 -m arcpuzzles parametric manifest a20ecf84f041 \
  --evidence generators/a20ecf84f041/workspace/parametric/evidence/current \
  --include generators/a20ecf84f041/tests/test_parametric_finish.py \
  --include generators/a20ecf84f041/tests/test_generator_a20ecf84f041.py \
  --reported-checks '87 staged tests; 128-episode finite-rival audit; protected-Racket parity and causal ablation'
python3 review.py run python3 -m arcpuzzles parametric qualify a20ecf84f041 \
  --seed 0 --seed 17 --demos 2 --queries 4 \
  --out ../checks/a20ecf84f041/qualification --summary
```

The inventory and qualification are reviewer evidence, not owner acceptance or
training admission. Finite rivals do not prove unique induction.
