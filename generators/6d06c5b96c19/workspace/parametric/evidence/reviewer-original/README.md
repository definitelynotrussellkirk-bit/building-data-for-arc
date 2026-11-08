# Proposed `shift_direction` episode parameter

This task-local prototype leaves the selected generator, canonical examples,
canonical Racket program, and approval metadata untouched.

One hidden value is chosen once for a complete episode:

- `down` — canonical default: rotate payload rows downward by the red cue row.
- `up` — nearby alternative: rotate payload rows upward by the red cue row.

`prototype.py` builds identical source inputs for both settings, labels every
pair with one fixed setting, and emits answer-free public challenges. The four
training pairs include direction-sensitive cues, so the hidden setting is
learnable before the query. The query itself is also direction-sensitive.

Replay the retained Racket/Python verification from the packet root:

```bash
python3 review.py run python3 \
  generators/6d06c5b96c19/workspace/parametric/verify.py \
  --seed 20261023 \
  --out ../checks/parametric-final-pass/verification.json \
  --artifact-dir generators/6d06c5b96c19/workspace/parametric/materialized
```

This is proposed evidence only, not production or canonical authority.
