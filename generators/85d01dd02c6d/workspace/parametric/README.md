# Wall-scope parametric family

`wall_scope` is fixed for an episode:

- `every_wall` is the exact canonical program: every color-9 cell blocks rays.
- `axis_dividers` first classifies the color-9 cells belonging to a complete
  row or column, then blocks rays only with that input-derived mask.

Each matched input contains a clear seed pair, a pair blocked by a complete
axis divider, and a pair separated by a short orthogonal wall. Thus the visible
2-demo minimum identifies the setting while preserving the original cardinal
ray, blocker, and overlap-count reasoning. The fourth query is 30x30.

The causal chain is: **A** classify the blocker mask from the input; **B** cast
seed rays against that mask and threshold the resulting per-cell visibility
counts. The protected witness uses the wrong blocker mask on a short-wall case.

From the packet root:

```bash
python3 review.py run python3 -m pytest \
  generators/85d01dd02c6d/tests/test_parametric_wall_scope.py -q
python3 review.py run python3 \
  generators/85d01dd02c6d/workspace/parametric/audit_lessons.py \
  --out ../checks/85d01dd02c6d/self-review.json
python3 review.py run python3 -m arcpuzzles parametric qualify 85d01dd02c6d \
  --out ../checks/85d01dd02c6d/qualification --summary
```
