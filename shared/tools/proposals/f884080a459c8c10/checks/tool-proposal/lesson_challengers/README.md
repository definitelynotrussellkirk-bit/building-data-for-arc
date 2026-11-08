# Optional external lesson challenger gate

This standalone Python proposal tests a supplied rival against saved labeled
lessons independently of the generator's own rival declarations. It does not
generate reference labels or claim universal identifiability. The included
density-order plugin is copied from the independent audit parser and imports
only the Python standard library.

From the outer packet directory:

```bash
WORK/.venv/bin/python review.py run ../.venv/bin/python \
  ../checks/tool-proposal/lesson_challengers/gate.py \
  ../checks/audit/d5178d26d905/generated-lesson.json \
  --rival ../checks/tool-proposal/lesson_challengers/density_order.py \
  --function density_order \
  --reference-receipt ../checks/audit/d5178d26d905/evidence.json \
  --out ../checks/challenger-new-result.json
```

The input may be one lesson object or a list. Each lesson requires at least one
training pair and exactly one labeled query. Each input and output is a
rectangular 1..30 by 1..30 grid of literal integers 0..9; output size may differ
from input size. Explicit local plugin code is executed, so select a trusted
standalone module. The source hash binds its exact compiled bytes, not imported
third-party dependencies. Python output buffers are copied per prediction.

Exit 0 means no ambiguity found against this supplied rival; exit 1 means a
rival fits all demonstrations and changes a query; exit 2 means malformed data
or a rival execution error. Missing labels cannot count as a pass. A supplied
reference receipt is hashed for traceability, but the checker does not prove its
label authority; the actual audit's Racket receipts establish that separately.

By default only the given production order is scored. `--rotate-query` requires
every leave-one-out query position. An intentionally reordered control moves
the original ambiguous query into the demonstrations; it passes production
order but fails the rotation requirement. This is a diagnostic control, not a
proposal to duplicate examples or a claim that reordering fixes every policy.

Final results: `final-real-lesson.json` exit 1; `final-reordered.json` exit 0;
`final-rotated.json` exit 1. The fixed checker passes 15 tests in
`final-tests.log`. `commands.json` supplies exact executed argv/cwd/exit values.

Code review reproduced two implementation bugs on the retained
`gate-before-review.py`: stale timestamp-valid cached bytecode could run under
a new source hash, and a reused mutable result buffer could rewrite earlier
predictions. `review-red.log` has 2 failures / 13 passes; the corrected source
compiles the same bytes it hashes, parses the same lesson bytes it hashes, and
copies each result. Both genuine failures and the original missing-file red
phase remain retained. These tool failures are unrelated to natural puzzle
solve attempts.

Before making a new rival blocking, check its task-domain validity, canonical
fit, plausibility, and downstream query policy. An arbitrary query-specific
exception can always disagree and is not automatically a useful teaching defect.
The known density-order witness has independent task-domain and Racket evidence
under `checks/audit/d5178d26d905/`.
