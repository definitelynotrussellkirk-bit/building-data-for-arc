# Working notes: a2e8d5ad83e5

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## Current proposed extension: minimum anchor area

`workspace/parametric/` adds `minimum_anchor_area` in `{4,9,16}` with the exact
canonical default `4`. It changes only the qualifying-component size predicate;
filled-component detection, floor centers, row/column propagation, preservation
outside crosses, and distinct-color cancellation remain invariant. Production
source, reference rules, approvals and frozen fixtures were not changed.

The first mixed-size demonstration distinguishes all three declared thresholds
using Racket. Inputs and retries are matched across settings. Separate `1..8`
demo/query counts support four distinct queries; default counts are `3/4`.
Two new 4x4-anchor profiles are necessary to teach collision at threshold16:
the original sampler never supplies two area16 anchors in one input. Same-color
and shared-row/shared-column variants are included for every setting.

The tested scope is this prototype and its strict export/adapter contract.
Eighteen focused unittest tests pass, and an independent Racket replay agrees
on 27 threshold/witness combinations plus all five distinct canonical pairs.
The canonical production battery is not applicable to these unchanged bytes.
See `workspace/parametric/README.md` and its current evidence/manifest for replay.

Remaining boundary: finite-rival identification proves only the declared three
thresholds, not all possible programs. Generated inputs remain square-based and
at most26x26; rectangle semantics are checked with explicit witnesses. Learning
benefit and production use of variants require separate decisions. The next
owner action is to assess the source-bound qualification and, if desired,
explicitly accept the variants; this prototype grants no training admission.
