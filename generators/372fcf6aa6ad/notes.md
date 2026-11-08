# Working notes: 372fcf6aa6ad

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## Review `review-292f4956276cdcea` — native winner-width relay

The production generator and canonical rule remain unchanged.  The new native
adapter under `workspace/parametric/` exposes `mode=canonical` and
`mode=winner_width_relay` with matched deterministic inputs, 2–6 demonstrations,
and 1–4 prefix-stable queries.  The alternate first performs the canonical
holes/size/position ranking and clockwise rotation, then uses the rotated width
of the first-ranked crop as a 1-based index selecting which packed crop is
recolored to 8.  The authored scenes deliberately place a large hole-free object
before smaller one-hole frames, repairing the retained size-before-holes
teaching shortcut inside this family.

Fresh evidence: 28 focused tests, 44 portable task tests, a 32-seed/two-mode
bounded audit with 448 named-rival checks and 30 protected-Racket evaluations,
native qualification for both settings at seeds 0 and 17, and a protected
wrong-height causal witness with status `reviewer_replayed`.  Query four is a
substantive 30x30 scene.  Public projection was checked one query at a time and
is identical to a native one-query call.  This is reviewer-ready evidence only;
owner acceptance, variant approval, and training admission remain pending.
