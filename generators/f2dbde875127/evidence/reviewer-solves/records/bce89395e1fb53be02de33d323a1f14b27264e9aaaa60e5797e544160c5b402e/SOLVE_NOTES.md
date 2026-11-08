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
