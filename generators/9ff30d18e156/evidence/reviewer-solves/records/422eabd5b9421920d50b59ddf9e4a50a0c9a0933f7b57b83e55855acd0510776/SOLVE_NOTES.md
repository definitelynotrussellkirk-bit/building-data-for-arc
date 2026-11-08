# Fresh Python solve — visible-only phase

## Provenance and exposure

This is an assistant-authored work log, not a captured token-level conversation,
not model log probabilities, and not a blind solve. Earlier in the generator
review I read the canonical Racket rule, generator, and canonical examples.
Earlier rule exposure is therefore **yes**. Once `solve_episode.py prepare`
started this phase, I consulted only `solve/challenge.json` and my newly written
Python files. I did not reopen generator/reference source, previous solution
explanations, or private query labels. The checker supplies only visible-example
and execution feedback. There are two masked query inputs.

## Visible observations and hypotheses tested

The first example expands same-color endpoint pairs horizontally while leaving
all other rows blank. The second has multiple colors within one row: their
spans complete separately and singleton distractors remain unchanged. The
third has more than two occurrences of a color and completes its internal
holes. No visible example requires joining positions across rows or choosing
an overwrite priority for overlapping spans of different repeated colors.

I wrote `visible_probe.py` to compare three candidate rules against only the
three displayed training outputs: whole-row filling, exactly-two-occurrence
filling, and independent row-local color-span completion. The first two are
explicit diagnostic rival hypotheses, **not submitted failed solve attempts**.
The exact results are in `visible_probe.json`. No deliberate wrong submission
was created to manufacture a failure/revision pair.

## Submitted revision 1

`solution.py` groups nonzero positions by color separately in each row. Colors
with two or more occurrences fill their minimum-to-maximum interval. Other
cells stay unchanged; output is a copy rather than mutation of the input.
Shape/type checks fail clearly for malformed grids. The visible-only probe
also verifies nonmutation on the demonstrations.

The implementation uses deterministic first-occurrence color ordering, but
there is no claim that the visible examples establish a collision-priority
rule outside their disjoint-span domain. All three displayed transformations
support the submitted rule. `solve_episode.py check --intent solve` records
this genuine first attempt and retains its source and note snapshot. Any
query prediction produced by the harness remains unscored to this reviewer.
