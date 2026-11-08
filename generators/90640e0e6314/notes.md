# Current task notes: 90640e0e6314

## Canonical rule and authority

The selected production generator is version `3.0.0`, SHA-256
`97508cbdd531c0ba6b564aaf818b6a58adf829abfdaaaab45b89e97f176a401e`,
with canonical rule hash `370706e398d4`. For an asymmetric square input, the
canonical 2x2 output places `rot180` at top-left, vertical flip at top-right,
horizontal flip at bottom-left, and the unchanged input at bottom-right. The
production generator and canonical ledger were not changed in this review.

## Proposed parameter decision

The task-local prototype adds one finite episode parameter,
`identity_corner ∈ {top_left, top_right, bottom_left, bottom_right}`. The
unchanged input occupies that corner; reflection across the horizontal and
vertical seams fixes the other three quadrants. `bottom_right` is the original
default and loads the canonical Racket program byte-for-byte. A setting is chosen
once per episode, never per pair.

Sampling is independent of the hidden setting. The default episode has three
demonstrations and four separately configured, distinct queries; each count is
bounded to `1..64` in this prototype. All seven default inputs
come from the selected generator and have four distinct reflection variants, so
every setting changes every label. Public challenge bytes contain only visible
demonstrations and query inputs; public IDs are hashes of exactly those bytes.
Seeds, settings, programs, and query answers remain private.

## Verification and retained evidence

The staged task-test runtime passes all 16 selected-task tests after replacing a
fixed `__file__.parents[...]` canonical-data lookup with portable
`reviewer_support.find_root` and `canonical_pairs` helpers. The pre-fix staged
failure is retained alongside the passing post-fix receipt.

The protected-Racket verifier materializes one episode per setting and checks
seven shared inputs under all four exact programs: 28 setting calls, all
Python/Racket exact, all four labels distinct on every input, every demonstration
refuting all three rivals, and four query answers sensitive to the setting. It
also checks the canonical default against all three labeled canonical pairs and
confirms exact canonical-program identity. Main evidence:
`checks/parametric/90640e0e6314-identity-corner-verification.json`.

## Known limits and next useful action

This is a bounded four-setting proposal, not proof against every possible rival.
It is not catalog-approved, runtime-integrated, or training-admitted. If the
family is adopted, the next useful action is to integrate it through an opt-in
consumer that preserves the public/private split, then replay the episode-level
setting-identifiability gate and the normal admission checks without changing the
canonical default.
