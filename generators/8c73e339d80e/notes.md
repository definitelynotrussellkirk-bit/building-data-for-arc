# Working notes: 8c73e339d80e

## Current bounded rotation-visibility repair

The prior sampler accepted layouts where every chosen rotation code was
observationally inert. The retained square-base witness at seed 0 / sample 6
reproduces this: the executed canonical output equals a rival that ignores all
codes and always stamps the unchanged base. Before source SHA-256:
`c09752705ef4509488e326cd281495179bdde0d6fed738e73b79a911570991cc`.

The sampler now retries a completed layout unless at least one actually selected
code changes the normalized base cells. Partial symmetries remain available when
a selected rotation is visible; this does not require four distinct orientations
or expose the entire code mapping in each pair. Canonical reference behavior and
structural `self_check` remain unchanged: a square input is legal, but unsuitable
as the sole evidence of a rotation in an ordinary generated pair.

Focused Racket-backed regression (`tests/test_rotation_visibility.py`): 12 fixed
draws across medium/easy/hard bands changed from 11/12 to 12/12 refuting the
ignore-code rival, with all 12 passing structural checks. The same probe confirms
the historical square remains structurally accepted and rotation-invisible.
Executed canonical rule hash: `d2185c0081d9`. Compact source-bound reports and
actual process exits are in `checks/8c73e339d80e/{before,after}.json` and
`checks/8c73e339d80e/{before,after}-command.json` in the return.

This is a pair-level teaching repair, not a full-lesson identifiability claim.
The inherited audit's broad override/contract findings remain unaddressed, and
its current index is intentionally unchanged. No parametric work or full battery
was performed in this secondary scope.

## 2026-10-24 parametric handedness proposal

Built `workspace/parametric/` around one episode-fixed rule parameter:
`direction=clockwise|counterclockwise`. The clockwise program is byte-exact
canonical; the alternate reverses only the 4/9 quarter-turn mapping while
preserving code extraction, rotation, clipping, and cyan stamping. Inputs are
setting-independent, demos and queries use separate deterministic streams, and
2–6 demos plus 1–8 queries are supported. The ordinary retained form uses three
demos and four distinct queries; query 4 is a substantive 30x30 case with far
markers and irrelevant-color distractors. Query prefixes do not depend on demo
count or future query count, and public IDs hash only visible demos and query
inputs.

A first implementation exposed one nondiscriminating source motif whose 90- and
270-degree rotations were identical. That motif was replaced rather than
weakening the demonstration-only certificate. Final focused tests cover exact
canonical preservation, both settings under protected Racket, count boundaries,
matched inputs, public/private separation, query-prefix stability, rejection
paths, and the 30x30 stress case. The bounded adversarial pass generated 32
episodes over four count corners, four seeds, and both settings. Native
qualification passed for seeds 0 and 17 at three demos/four queries; the receipt
is `checks/qualification-verification/8c73e339d80e/qualification.json` in the review
return. This remains a proposed variant, not owner acceptance or training
admission.
