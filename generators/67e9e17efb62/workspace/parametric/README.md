# Proposed `peak_repetitions` prototype

This task-local artifact proposes one small rule parameter for family
`67e9e17efb62`:

- `peak_repetitions = 1` is the original/default rule.  The emitted run lengths
  are `1,2,...,L,L-1,...,2,1`.
- `peak_repetitions = 2` repeats the maximum-length run once.  The emitted run
  lengths are `1,2,...,L,L,L-1,...,2,1`.

The input grammar, bar interpretation, one-zero separators, row-major wrapping,
and final-row padding are unchanged.  The parameter is selected exactly once
from the episode seed and applies to all three demonstrations and the query.
Every lawful prototype input distinguishes the two settings, so the alternative
setting is refuted by the demonstrations before its query is presented.

`render_program(1)` returns the exact canonical `program_solution`, whose text
SHA-256 is
`1212a5180faaf8260ab3490d2b2cf153a607dd72076a17babe9a9e9b8637cb64`.
The value `2` changes exactly one source expression, from
`(range (- L 1) 0 -1)` to `(range L 0 -1)`.  Both settings are executed through
the included Racket bridge; no Python mirror supplies labels.

This is a **proposed, unapproved prototype**.  It does not change the selected
production generator, canonical rule identity, shared runtime interfaces, or
approval records.  Its finite evidence covers two deterministic complete
episodes and one common discriminator; it is not an exhaustive identifiability
proof.

From the outer extraction directory, use fresh output paths:

```bash
python3 review.py run python3 generators/67e9e17efb62/workspace/parametric/prototype.py \
  --out ../checks/parametric/peak-repetitions-v1
python3 review.py run python3 -m pytest -q \
  generators/67e9e17efb62/tests/test_parametric_peak_repetitions.py
```

Private evidence records seeds, hidden parameter values, exact programs, query
answers, rival predictions, runtime identity, commands, and hashes.  Public
challenge JSON contains only demonstration inputs/outputs and query inputs.
