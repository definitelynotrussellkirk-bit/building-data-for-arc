# Working notes: e777125624ca

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## Current reviewer decision — 2026-10-26

The version 2.1.0 generator already produces canonical NOR lessons with all four
aligned binary states and no observed semantic defect. Its retained test was not
portable: it derived canonical/base data from the task directory and therefore
failed in the copied runtime. The test now uses `reviewer_support.find_root`,
`canonical_path`, and `load_selected_generator`; it also treats the base JSON's
whitespace-only Racket spelling as execution-equivalent while the parametric
canonical default is separately required byte-for-byte. Focused and copied-runtime
runs both pass 29/29 after the parametric tests are included.

## Native parametric family — ready for owner source review

`workspace/parametric/` declares `rule_mode=nor|sparser_difference`. `nor.rkt` is
the exact selected canonical source. The alternate first counts occupied cells in
each 3-column panel, selects the uniquely sparser side, then marks positions where
that side is empty and the aligned cell on the other side is occupied. The first
two demonstrations force opposite selector outcomes. Inputs are independent of
the hidden setting, contain every aligned state, and remain prefix-stable from one
to four queries.

A bounded self-review covered both settings, seeds 0/17, demo counts 2/3/6, four
queries, 136 protected-Racket evaluations, and named shortcut rules. The native
authoring preflight passed, and a protected wrong-intermediate witness changed the
final output when the selector was forced to the opposite side.

Current handoff evidence:
- `workspace/parametric/evidence/current/self_review.json`
- `workspace/parametric/evidence/manifest.json`
- packet `checks/e777125624ca/qualification/`
- packet `checks/e777125624ca/causal/witness.json`

Domain limit: the source grammar is exactly two 3-column panels plus one separator,
so width 7 is semantic. The maximum lawful size is 30x7; the stress query uses that
shape with substantive panel content. This is authoring/preflight evidence only.
Owner qualification/acceptance and training admission remain unperformed.
