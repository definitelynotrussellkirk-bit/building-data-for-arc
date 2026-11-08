# Feedback-routed concentric rings

This proposed native family preserves the selected canonical rule as
`routing=direct` and adds `routing=feedback_min`.  The alternate rule paints
rings center-out.  After each rendered ring, the first minimum-color quadrant
in TL/TR/BL/BR order supplies a clockwise quarter-turn count for the next
row-major 2×2 source tile.

The setting is fixed for an episode. Inputs are setting-neutral and use
separate deterministic demo/query streams. Supported episodes contain 2–6
visible demonstrations and exactly four distinct private-answer queries; all
four query outputs are 30×30.

## Reproduce

From the packet root:

```bash
python3 review.py run python3 -m pytest generators/84def340ce03/tests/test_parametric_feedback_rings.py -q
python3 review.py run python3 generators/84def340ce03/workspace/parametric/audit.py \
  --out generators/84def340ce03/workspace/parametric/evidence/current/self_audit.json
python3 review.py run python3 -m arcpuzzles parametric manifest 84def340ce03 \
  --evidence generators/84def340ce03/workspace/parametric/evidence/current \
  --include generators/84def340ce03/tests/test_parametric_feedback_rings.py \
  --reported-checks 'focused pytest; protected-Racket learnability audit'
python3 review.py run python3 -m arcpuzzles parametric qualify 84def340ce03 \
  --out ../checks/84def340ce03/qualification
python3 review.py run python3 generators/84def340ce03/workspace/parametric/build_witness.py \
  --qualification ../checks/84def340ce03/qualification/qualification.json \
  --out ../checks/84def340ce03/sequential_dependency.json
python3 review.py task-tests 84def340ce03 --phase after \
  --out ../checks/84def340ce03-tests
```

## Public/private boundary

Use `reviewer_support.public_challenge_bytes`. It exports all demonstration
inputs and outputs plus query inputs only. It ignores settings, exact Racket
program text, and query answers. For sequential delivery, project the same
qualified episode to `test[:k]`; on the first turn use `test[:1]`, then reveal
one additional already-qualified query input per turn. Never regenerate from a
turn-dependent counter or expose later test pairs early.

Qualification is finite: it establishes the declared two-program survivor
property and exact labels for the checked jobs. The task-local audit additionally
checks four named plausible shortcuts. Neither artifact claims uniqueness among
unrestricted programs or downstream training benefit.
