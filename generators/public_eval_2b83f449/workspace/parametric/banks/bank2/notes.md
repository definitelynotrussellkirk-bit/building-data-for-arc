# Current design — public_eval_2b83f449

General reference: rewrite each horizontal orange triple as two cyan side
passages around a vertical three-cell magenta pole. Erase the green markers to
cyan for connectivity analysis. In each resulting nonbranching four-connected
cyan path, collect its original green population at its lower endpoint, packing
inward along the path. Equal-height endpoints retain the original marker
positions. Empty loops remain empty. All two supplied demos and the provided
gold query match protected Racket; the implementation uses no lookup of labels.

The episode-fixed flow parameter is down|up. Up preserves gate semantics and
population but collects at the upper endpoint. The source-bound counterfactual
renders the right gates while routing on the OLD strips, proving that movement
consumes the gate-derived topology. Canonical default bytes are preserved exactly
between reference.rkt and workspace/parametric/canonical.rkt.

Constructive sampler: 9..30 by 16..30 grids, varied gate counts, two alternating
safe column pools, horizontal and vertical reflection, optional holes creating
interior endpoints, truly empty road lanes, and both stripe offsets. Exact gate
counts reject infeasible widths rather than silently falling back. A failed
curriculum test showed that the first sampler omitted empty lanes present in the
original test; the second demonstration now contains one, and query profiles
include them too. Every episode has four distinct queries, with a substantive
30x30 case containing 15 cyan strips and many gates. With alternating rows an
even-height canvas necessarily has one empty outer road row; this is not a
claim that all four outer edges contain colored cells.

2..6 demos, four private queries, stable prefixes, matched setting inputs.
Default generated support is a structured stripe/path grammar, not arbitrary
branching mazes. Green markers start at endpoints, and components have degree
at most two. Gates/markers/background retain their original semantic colors.
The finite rival set covers ignored gate topology, reversed flow, lost marker
multiplicity, global sinking, straight vertical dropping, and missing pole arms.
No universal uniqueness or measured learning benefit is claimed.

Current source evidence: WORK/checks/public_eval_2b83f449/preflight-current/ and
WORK/checks/public_eval_2b83f449/audit-current/. These are unapproved authoring
checks. Owner registration, source review, native qualification and fresh
acceptance are still required. training_admitted=false.
Final review is author self-review, not an independent reviewer.
