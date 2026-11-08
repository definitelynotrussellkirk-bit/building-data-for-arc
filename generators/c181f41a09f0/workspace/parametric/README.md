# Parametric prototype: marker-count-directed strip travel

This task-local family preserves the canonical `opposite_end` rule byte-for-byte
and adds one nearby rule with a real sequential dependency:

- `opposite_end` — recover each source-end 3×3 block and move it to the other
  end of its strip; this is the exact selected canonical Racket program.
- `marker_count_steps` — first recover the same source block and count its
  marker-colored cells, then move the block by that many 3-cell steps from the
  source, clipped only by the strip's lawful capacity.

The marker count is an input-derived intermediate, not a cosmetic setting.  A
protected-Racket counterfactual that replaces every count with one changes the
final output.  The minimum two demonstrations deliberately keep dimensions,
orientation, source side, and marked strip ranks fixed while permuting counts
`1/2/3`; one two-cell marker cap is noncontiguous.  This defeats constant-step,
strip-rank, side/rank, bounding-span, and marker-position shortcuts without
raising the two-demo minimum.

`adapter.py` exposes the native `program(settings)` and
`generate(seed, settings, demos, queries)` contract.  The family supports 2–6
independent demonstrations and 1–4 queries; qualification uses two demos and
four distinct queries.  Query order is privately shuffled but prefix-stable, and
single-query use has the same first-turn content as the four-query sequential
projection.  Public bytes contain demonstration labels and one query input only;
settings, programs, future queries, and answers remain private.

`adversarial_audit.py` is a reusable bounded audit for future agents.  It fits a
bank of static and lookup shortcuts to the smallest lesson, exercises size and
count boundaries through 30×30, checks crossed controls, replays protected Racket
parity, and verifies a wrong-intermediate witness.  Its finite pass is evidence
for the declared domain, not a proof of universal uniqueness or owner acceptance.
