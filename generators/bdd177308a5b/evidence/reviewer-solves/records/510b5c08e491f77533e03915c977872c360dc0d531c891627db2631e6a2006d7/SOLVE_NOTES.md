# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Scope and exposure

- Earlier rule/source exposure: none.
- Consulted only this directory's README.md, challenge.json, initial solution.py
  scaffold and this log, plus WORK/RETURN-GUIDE.md. No generator, canonical rule,
  reference solution, private query label, prior solution explanation, or audit
  evidence was opened. The supplied episode was not redrawn or prepared again.
- There are three visible labeled training pairs and two unlabeled test inputs.

## Revision 1: exact oriented shape matching

Hypothesis: the gray L-shaped border marks a template in its interior. Find
monochrome objects outside that interior with the same shape after translation,
without rotation or reflection, and change their occupied cells to gray (5).
Keep the template, border, backgrounds and other objects unchanged.

Evidence from the visible pairs: in each of the three pairs the four changed
cells have exactly the template's normalized coordinate mask, and all change to
5. A Python probe computed this directly from challenge.json and printed
`same_translation_only_shape: True` and `changed_to: [5]` for train 0, 1 and 2
(exit 0). Orientation-invariant matching would recolor visible distractors, so
it was rejected before implementation. Matching by input color cannot explain
the different template/target colors across the pairs. No failed candidate
solver was submitted before this revision.

Implementation: derive the template interior from the gray border's bounds;
compare normalized coordinate sets of four-connected same-color components;
recolor every matching component outside the template to 5. Same-color
connectivity keeps differently colored touching objects separate, as needed by
the first visible test input. The supplied NotImplementedError scaffold was
replaced directly with this candidate.

Planned verification (outer packet root):

```sh
python3 review.py blind check --intent solve --note 'Revision 1: exact oriented template-shape matches become gray; test against all visible pairs and query execution.'
```

Remaining uncertainty: three visible pairs cannot establish behavior for every
possible unseen input. Query labels are unavailable and will not be consulted;
successful query execution is not evidence of query correctness.
