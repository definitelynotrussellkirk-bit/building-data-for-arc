# Current decision — public_eval_135a2760

General parent rule: detect uniform outer-frame separators; each inner ring
bounds a strip. Along its long axis, choose the periodic color-vector sequence
with fewest changed cells, using the shortest period on ties. Individual motif
colors use the smaller color on vote ties. The authored Racket rule reproduces
all two training labels and the supplied held-out gold (3/3 protected labels).
The short-period, repeated-evidence prior is implicit in these finite examples;
the exact minimum-error/shortest-period extension is an authored generalization.
It is not uniquely proved by the original examples.

`repair_mode=restore` is the default and exactly equals reference.rkt.
`mark_errors` retains the observed strip except at inferred anomalous positions,
which become the ring color. Both settings use the same input streams and
recover a genuine input-dependent period and motif before painting.

Sampler: two or three strips normally, four in the exact 30×30 stress scene;
one to five transverse lanes, periods 2/3/4/6, variable palette and phase,
horizontal and vertical orientations, corruption both inside the first repeat
and later repeats. It constructs a clean motif then corrupts it, independently
checking that the decoder recovers its intended clean labels. The finite
shortest-period convention is part of the admitted grammar. 2–6 demonstrations
and 1–4 queries have stable independent prefixes; the fourth query is 30×30.
The public presenter shuffles the full four-query bank from an explicit private
presentation seed before selecting a single query. Its directory/mapping must
remain controller-only. No count/end hint is emitted.

Tests: 24 focused tests pass. A failing regression caught pair-level private
metadata copied into demonstrations by the initial public projection; the
fixed projection explicitly whitelists input/output and the test now passes.
The bounded self-review covers 64 seeds × 2 settings × 5 demo counts = 640
nested lesson views and 5,120 pair exposures (not independent fresh pairs).
Eight executable Python shortcut rules have no query-changing survivors.
The separate Racket audit uses 40 fresh generated labels at six demos, plus
two causal labels; a separate process replays the two causal labels. Replacing
the recovered period/motif with the period-one candidate changes 159 cells in
the retained 30×30 mark-errors case. Sixteen saved one-query public views pass
the packet checker and private-field mutation/positive-control tests.

The `task-tests` wrapper cannot run an unregistered public target (Unknown
puzzle). This is not a passing staged check: the retained direct pytest suite
runs in the supplied runtime via review.py, and public-creation preflight is
passing. Owner registration/native qualification/acceptance remain pending.
The final review is an author self-review; no independent reviewer is available.
No shared authority, parent provenance, or runtime source was modified.
