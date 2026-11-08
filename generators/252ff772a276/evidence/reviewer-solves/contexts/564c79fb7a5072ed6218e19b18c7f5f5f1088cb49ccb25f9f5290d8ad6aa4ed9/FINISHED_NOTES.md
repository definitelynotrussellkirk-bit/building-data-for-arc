# Blind solve work log — 252ff772a276

Exposure: only packet directions and the public challenge were opened before
this solve. No generator, rule, reference solution, private query labels or
earlier solution explanations were consulted. A separate read-only collaborator
was restricted to this same public challenge for a hypothesis check.

## Revision 1

All three outputs crop one blue rectangular frame, preserve its red marks and
recolor its interior zeros green (3). External red noise in example 2 disappears.
Example 0 selects the 2-by-4 interior with 3 red cells instead of the 4-by-3
interior with 3 red cells; densities are 3/8 versus 3/12. Example 1 selects
3/12 over 1/6. Example 2 selects 3/20 over 1/12. Thus maximum red fraction in
the interior consistently selects the output. Largest frame, smallest frame,
topmost and bottommost each conflict with at least one visible pair.

Implemented complete rectangular blue-component detection, exact rational
comparison of red/interior-area density, cropping, and zero-to-green filling.
Tie handling is top-left by a deterministic convention; visible data do not
teach equal-density ties. Maximum red count with a topmost tiebreak, or simply
selecting a three-red frame, also fits these examples. Their different query
predictions are unresolved; density is the chosen geometric hypothesis.

Check command from packet root:
`python3 review.py blind check --intent solve --note 'Select maximum interior red density; preserve frame and red cells, fill interior zeros green.'`
No failed code revision has been discarded or deliberately manufactured.

Observed revision-1 check: exit 0, visible 3/3, execution completed; private query correctness remains unknown. Independent visible-only review agreed with density selection and noted most-red-then-smallest also fits these examples. No further revision is justified by the available examples.
