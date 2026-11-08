# Small retained counterexamples

`largest-object-tiny.json` is a hand-built, accepted 5×6 input: the target has
three cells and a non-6 distractor has four. The largest-object rule fits all
canonical examples but fills the wrong box here. This exact tiny grid is not
a default draw; it establishes a lawful disagreement.

`largest-object-generated.json` is the actual seed-7, index-1, medium default
draw from the final generator. It demonstrates that the proposed population
emits the same kind of largest-object counterexample. `elongation-generated.json`
is index 7 from that cycle and records the second maximum-aspect-ratio witness.
All three include authoritative Racket output, selected rival output, source
hashes, domain status and the public command. Their complete receipt is
`checks/witnesses-v4/racket.json` in the review return.

`ignored-controls-before.json` retains the pinned baseline's failed exact
5×6 / three target cells / zero distractors request. `area12-intermediate.json`
and `elongation-intermediate-review.json` preserve independent authoring
counterexamples from failed intermediate repairs, with their original source
bindings. Their Python rival analyses are distinct from the final Racket
witness receipts. Do not relabel these records as final-source measurements.

The task tests cover exact controls, invalid inputs, each declared rival's
canonical fit, cyclic lesson refutations and the elongated-object holdout
regression. `workspace/probe_counterexamples.py` regenerates a current-source
Racket witness pack without overwriting earlier evidence.
