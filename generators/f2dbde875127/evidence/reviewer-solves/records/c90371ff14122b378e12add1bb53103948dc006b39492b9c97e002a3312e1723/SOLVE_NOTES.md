# Visible-example solve work log

This is a reviewer-authored, concise experiment log, not captured token-level
model reasoning or a blind evaluation. Earlier rule exposure: **yes**, during
the generator repair. Since preparing this challenge, I have read only its
public `challenge.json`, my own new Python programs, and visible checker
feedback. I have not reopened the generator, Racket rule, reference solutions,
private answers, or previous solution explanations during this phase.

The public challenge has three demonstrations and two masked queries. The
visible demonstrations contain markers 4 and 5 only. A query also contains
marker 3. Thus fitting the demonstrations alone does not establish arbitrary
behavior for marker 3; any candidate must state its extrapolation assumption.

## Revision 0001 — intentional teaching negative
An identity program is deliberately checked to establish that the visible
comparison rejects an unchanged grid. This is **not an accidental failed model
solution**. Its failure is useful as a checker/teaching negative, not evidence
of reasoning difficulty. The next probe will enumerate quarter-turn and
centering hypotheses directly against the visible input/output pairs.

## Public-example probe
`python solve/probe_model.py` enumerated 64 candidates: 16 affine maps from
marker value to a clockwise quarter-turn count, crossed with floor/ceiling
choices for each centering dimension. `visible-hypothesis-probe.json` retains
all candidate scores, not just the best result. Exactly one candidate in this
family matched all three demonstrations: turns `(marker+2) mod 4`, with floor
centering in both dimensions. The unmodified identity baseline matched 0/3.

This is a bounded hypothesis comparison, not a proof that no other rule exists.
In particular, marker 3 is extrapolated by the affine-map assumption from the
observed marker values 4 and 5. Earlier repair exposure can bias this choice;
this episode must not be labeled blind or independently learned.

## Revision 0002 — visible-fit candidate
The submitted standalone program contains only the new Python geometry helper
used in the public probe and the fitted constants. It imports no generator,
Racket runtime, puzzle ledger or reference solution. The masked queries are
executed only for shape/purity checks; their private outputs remain unread.
All 3/3 public demonstrations pass `python solve/check_visible.py`; both queries
execute and preserve dimensions and input bytes. The official visible-only
checker is run next to retain the actual candidate and its feedback.
