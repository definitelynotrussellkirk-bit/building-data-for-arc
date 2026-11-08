# Current notes: 4512012999bb

## Canonical behavior
Find the unique paired vertical guides and detached crop, compare side-color
match counts, mirror only on a strictly better score, and copy each wall row.
The selected generator, canonical rule, existing tests, and approval bytes are
unchanged by this proposal. Parent: training:846bdb03.

## Proposed tie policy
`workspace/parametric/prototype.py` exposes `direct` (exact canonical source)
and `mirror` (change only `>` to `>=` at the orientation comparison). It keeps
one policy per episode and independent demonstration/query counts. The default
three demonstrations teach a positive-score asymmetric tie and both strict
branches. Four queries have active crop areas 49, 64, 72, and 100 versus
12, 18, and 24 in the default demonstrations; larger inputs contain larger
crops, not only padding. Input sides remain at most 30; no exact-30 quota is
claimed. Zero-score ties and uninformative symmetric ties have independent
Racket-backed checks in the returned evidence.

All labels and four declared rival programs execute through Racket. The default
seed-17 batch retains both settings, 14 distinct inputs, all eight query
certificates, and replayable private programs. Each setting is the sole survivor
from its demonstrations within {direct, mirror, always-direct, always-mirror}.
This finite-family claim is not uniqueness among all possible ARC rules.

Public content and filenames derive only from visible challenge bytes via the
shared reviewer support helper. The private directory contains settings,
programs, answers, source hashes, and prediction matrices. Expose only public/.

## Verification and remaining work
Eight prototype contract tests, an actual 61-evaluation generation, a separate
61-evaluation source-bound replay, and ten independent Racket-backed cases passed.
Five of the independent cases are original canonical pairs. Production batteries
were not rerun because production source is unchanged. Source drift is rejected
by the replay tool rather than silently refreshing evidence.

Normal review intake remains blocked: assignment review-f41cf94e34ab02dd was
observed for this task, but its seed/journal was lost when the initial temporary
execution session closed. No assignment was reconstructed or redrawn; no
supplementary tickets were drawn. The return is an independently verified
proposal patch, not a controller-approved return or a training-admission claim.
The next action is owner review of this source-bound proposal; a normal new
assignment requires an explicit recovery decision.
