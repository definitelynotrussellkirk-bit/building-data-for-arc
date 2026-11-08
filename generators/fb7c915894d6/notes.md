# Working notes: fb7c915894d6

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## Parametric family review — assignment review-11398f0d4b131dda

Preserved the exact canonical `most_frequent` Racket source and added an
input-matched `least_repeated` class policy. The intermediate is the selected
normalized shape plus its measured class frequency; the renderer consumes both
by scaling that shape by the frequency. The minimum two-example lesson reverses
area/mass and top-left cues and varies the scale. A bounded 64-seed audit found
no harmful survivor among the named class-selection/fixed-scale rivals. A
protected-Racket counterfactual replacing the intermediate with the other
repeated class changed the output. Owner exact-source acceptance and training
admission remain pending.
