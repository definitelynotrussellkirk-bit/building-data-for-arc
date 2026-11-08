# Proposed parametric chevron rule

This task-local prototype preserves the selected canonical Racket detector,
aligned-near marker components, supported depths, and all four orientations.
The episode fixes `fill_color` to one of `2,4,6,8` and `fill_edges` to a boolean.
The original setting is `(8,true)` and must return the exact canonical text,
including its leading/trailing newlines. Other settings replace only the paint
literal and, for false, the four transverse `<=` comparisons with `<`. Axial
depth bounds, every green marker, and outside background remain unchanged.

The selected input generator is loaded through `reviewer_support`; it is never
modified here. Its complete program SHA-256 is pinned to
`b4c2540796af088ba41f486413b1be85ff6f8a9db373d30e6105bdc4529c7f25`.
Racket supplies every label and all eight parameter-program predictions. An
independent Python implementation is a diagnostic agreement check only.

An episode has at least three demonstrations and defaults to four distinct
queries. A bounded deterministic stream supplies inputs. A demonstration window
must refute all seven different parameter settings and all eight selected
canonical lesson competitors, adapted to the episode's color and edge rule.
The adapted competitors are checked against their actual selected declarations
at the default setting on every accepted input. This is a finite-rival claim.
The gate never uses query answers to choose demonstrations. Generation failures,
duplicates, unsuccessful demo windows, and actual accepted sample indices are
retained; exhaustion fails rather than cloning or truncating examples.

Public files contain only train input/output pairs and test inputs. Private
files retain parameters, complete labels, exact programs, hashes, competitor
predictions, and source-bound evidence. A deliberately ambiguous diagnostic
lesson uses complete arms in demonstrations and a sparse arm in its query;
it is a designed probe, not a natural solve failure.
