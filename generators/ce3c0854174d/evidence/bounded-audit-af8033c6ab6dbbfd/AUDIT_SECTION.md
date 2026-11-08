## ce3c0854174d

**A2 — No issue found in this bounded findings-only audit. Severity: none
identified; scope: current generator's declared 1..4 transform vocabulary,
canonical labels, representative exact controls, and default teaching schedule.**

Audited generator version 3.0.0, SHA-256
`42da7ef9b8d1112303ad4a1645bf5c4b6f87148f724fee63bc78ee5f93a9d5d8`.
The supported canonical `apply` command executed rule hash `442270b293a4`,
exact rule-text SHA-256
`c81159aa33fd17fccc8df5abee6eaaf52fda1d88b905ab22b5b779599e2a54e6`.
The generator hash was checked before and after the audit; the audited generator,
canonical data, shared code and approval records were not changed.

**Executed evidence:** `checks/audit/ce3c0854174d/racket.json` contains all
24 distinct input grids and their actual Racket outputs, input/output hashes,
selected source/rule hashes, and generator-domain results. The sample consists of:

- Twelve default inputs: seed 101, indices 0..3, separately for easy, medium,
  and hard. All pass the selected validator. The six even-index cases contain
  every declared code and an asymmetric template, consistent with the documented
  witness schedule.
- Four exact joint endpoint cases: seed 202, indices 0..3, respectively
  `(height,width,script_len) = (7,10,2), (7,16,5), (12,10,5), (12,16,2)`;
  difficulty is easy at even indices and hard at odd indices. Pixel observations
  match the requested values in all four cases, and all inputs pass validation.
- All four canonical pairs. Their executed outputs match the stored labels.
- Four lawful, hand-constructed rectangular-template cases with scripts
  `[1,1]`, `[2,2]`, `[3,3]`, and `[4,4]`. Independently written expected frames
  check clockwise quarter-turn, half-turn, horizontal reflection, transpose,
  cumulative state, top alignment and one-column packing. All four exact
  expected galleries match actual Racket execution.

All 24 executed outputs match the generator's diagnostic, and all are valid
rectangular ARC grids within 30-by-30. This directly supports the corrected
current legend, not the old source's legend. For each band's four default
pairs, holding out each pair once yields **12 overlapping three-demo lessons**
from **12 unique default inputs**. No declared rival among the 30
`LESSON_COMPETITORS` fits those demonstrations while disagreeing on its query.
Two additional mutated inputs—a script hole and a body with an invalid color—
are rejected as expected. These two rejection probes are not part of the
24-input Racket batch.

**Reproduction and provenance:**
`checks/audit/ce3c0854174d/probe.py` builds the compact case list and verifies the
saved Racket results; `cases.json`, `input.json`, `comparison.json`, and the
build/apply/verify logs retain details. `commands.json` records actual argument
arrays, working directory, environment and exit codes: build **0**, supported
apply **0**, verify **0**. The exact apply command was:

```bash
python3 ../run_with_racket.py python3 -m arcpuzzles apply ce3c0854174d --input ../checks/audit/ce3c0854174d/input.json --check-generator-domain --out ../checks/audit/ce3c0854174d/racket.json
```

The payload cwd was `WORK/repo`. Execution used Python 3.12.14 and the prepared
Racket v8.10 [cs] runtime at
`/dev/shm/arc-review-70785a599723/runtime/racket/bin/racket`, executable SHA-256
`bdf13d3b5b7ff97eba51ac56fd9198a34725f4a6f7c54066e2d2353107e29ce9`.
`runtime.json` retains the executable, bridge and prelude hashes.

**Limits and status:** This is a small source-bound audit, not a full battery,
all-seed census, exhaustive override sweep, or unrestricted identifiability
proof. The declared finite seven-template bank, periodic witness schedule,
restricted 1..4 vocabulary, and loss of the full-legend guarantee under explicit
`script_len=2` or `3` remain documented distribution limits. The four endpoint
cases are evidence of controls, not short-script teaching guarantees. The older
finding in `evidence/review_index.json` is bound to a different source and still
has `needs_triage` status; this clean current-source sample does not close it or
change approval.
