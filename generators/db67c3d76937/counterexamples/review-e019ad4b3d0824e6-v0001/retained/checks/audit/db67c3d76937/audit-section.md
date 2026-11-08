## db67c3d76937

**A-db67-1 — Reproduced distribution and teaching-support defect; prior finding remains unresolved.**
The selected generator always constructs exactly one horizontal pair and one
vertical pair, crossing once. Its validator requires exactly two nonzero colors.
The canonical task also requires three spans and two crossings: four of its five
labeled inputs have three nonzero pair colors, and the current validator rejects
all four. The Racket authority reproduced all five stored canonical outputs.

This independently reaffirms the prior finding in
`review-744c58f59a7bb8e9:v0001`, found through the current
`generators/db67c3d76937/evidence/review_index.json`. That finding and this audit
bind to the same unchanged generator SHA-256:
`af9c47c3df9078e7440e1b7f72fa7bc4a119fc49cba50c573099b6d82b6aa671`.
The supported application receipt reports executed/catalog rule hash
`1c1ba2ee5331` and rule-text SHA-256
`6918fee1d0134d81e6f61f3fb317ea5bbfe989867fecf173e69cb38d58e69de6`.

Two explicit rivals were checked: (1) connect only the first encountered pair
of each orientation, leaving other markers unchanged; (2) connect only the two
lowest nonzero colors, the prior audit's shortcut. The first is a natural
object-count shortcut added by this audit.

| Measured scope | Inputs | Validator-valid | First pair per orientation matches Racket | Two lowest colors matches Racket |
| --- | ---: | ---: | ---: | ---: |
| Easy, seed 17, indices 0–11 | 12 | 12 | 12 | 12 |
| Medium, seed 17, indices 0–11 | 12 | 12 | 12 | 12 |
| Hard, seed 17, indices 0–11 | 12 | 12 | 12 | 12 |
| All five canonical pairs | 5 | 1 | 1 | 1 |

The 36 production draws contain **28 unique inputs** across bands. All have
exactly two nonzero colors. Inspection of the fixed-two-pair construction supports
the stronger inference that a lesson assembled only from ordinary production
draws cannot refute either rival. This is a restriction of the teaching domain,
not a demonstrated ambiguity between a production lesson and a production query.
No lesson-census or rotation count is claimed.

The compact witness uses canonical train pair 2, a different canonical input
from the prior audit's retained witness. Its input and output are both 10 rows
by 12 columns, with colors 2, 5, and 7. Both rivals omit the lower horizontal
7 span and disagree with Racket at seven cells; in particular, at zero-based
`(6, 5)` Racket outputs intersection color 9 and both rivals output 5.
The exact input, Racket output, both rival outputs, differing coordinates,
source/rule hashes, and validator rejection are retained in
`checks/audit/db67c3d76937/reproduction.json`. It is canonical and Racket-labeled,
but outside the current generator's declared/validated two-color domain;
that exclusion is the defect.

Evidence: `checks/audit/db67c3d76937/racket.json` contains the supported
`arcpuzzles apply --check-generator-domain` receipt for all 41 cases.
`summary.json` and `probe-inputs.json` retain per-case metadata and rivals;
`probe.py` and `verify.py` reproduce the measurements. Exact wrapper argv,
actual working directories, exits, and evidence paths are in
`checks/audit/db67c3d76937/commands.json`. Both probes and Racket application
exited 0; this means the audit reproduced the finding, not that the generator
passed an acceptance battery.

Suggested repair: admit and generate canonical three-span configurations with
two pairs of the same orientation, then include demonstrations that distinguish
count-limited rivals while preserving the two-span cases. No repair was made
because this is a findings-only audit. No task-local tests were present in the
target file inventory. No full battery, broader-domain proof, or untested rival
claim is made; all target source, notes, and rule files remain unchanged.
