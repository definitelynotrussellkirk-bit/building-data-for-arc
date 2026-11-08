# b1972482cb43 — point reflection through a 9-anchor

Version: **2.0.0**. Kind: `per_puzzle`. Canonical rule: `add600b28dfb`.

Preserve the input. For every colored shape cell at `(r,c)`, add the same color
at `(2*ar-r, 2*ac-c)`, where `(ar,ac)` is the single color-9 anchor. Drop each
out-of-bounds target individually. The selected Racket rule supplies labels.

The ordinary domain contains one connected, monochromatic shape of 2–5 cells,
a separate 9-anchor, background zero, no overlap between the shape and its
reflection, and at least one visible reflected cell. Generation supports heights
4–12 and widths 5–14 in every band. Exact dimensions and palette aliases are
validated; negative fixtures are explicit diagnostic calls.

The five-slot schedule supplies two visible-interior plus witnesses, two clipped
asymmetric witnesses, and one broad sample that retains small symmetric shapes
and complete asymmetric copies. With four demonstrations and one query, every
single-pair holdout retains a refutation of each declared rival. This assumes one
fixed seed and constant valid overrides. It is a finite-rival teaching contract.

See `notes.md`, `tests/`, `counterexamples/`, and
`workspace/probe_reflection_lessons.py` for decisions, regressions, small
Racket-checked witnesses, and the reusable lesson probe. Approval remains derived
by the catalog from current code and retained evidence.
