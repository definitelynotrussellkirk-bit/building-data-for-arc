# Review: public-evaluation creation pair

Assignment `review-03cc38e69e8971fc` is complete at the reviewer-authoring stage. I built both assigned families from their exact public parents rather than substituting easier tasks. Each task now has a standalone generator, a general protected-Racket `reference.rkt`, a byte-identical parametric `canonical.rkt`, a native adapter and promotion manifest, notes, focused tests, finite-rival and export audits, generated-label Racket parity evidence, and a source-bound A→intermediate→B witness.

## `public_eval_e87109e9`

The six-row header contains four target-color commands. Stripe position encodes left/right turn hand. Every command starts from the same cyan square, travels toward the first axis-aligned target, turns, continues to the boundary, and redirects around rectangular blockers toward their farther transverse extension; an absent or non-aligned target takes the upward fallback. The output discards the header and paints the union of cursor footprints.

The native axis is `turn_mode`: `header` is the canonical parent rule and `reverse` swaps every decoded hand while preserving identical inputs. Generated scenes cover both 2×2 and 3×3 cursors, missing-target fallback, and blocker-bounce behavior. The default program is byte-identical to `reference.rkt`.

Verification retained in the return:

- all 4 supplied labelled official pairs execute exactly in Python and protected Racket;
- 30 focused task tests pass with zero failures or errors;
- authoring preflight passes for both settings, two demonstrations, and four distinct queries;
- the 32-seed finite-rival audit covers 192 episodes / 1,472 pairs with no failures;
- adversarial/private-export checks cover 18 episodes / 138 pairs with no failures;
- generated protected-Racket stress covers 96 evaluations with no failures;
- the causal witness is reviewer-replayed and changes B when A's decoded-hand intermediate is replaced.

## `public_eval_21897d95`

Solid-color rooms contain four-cell color-1 T arrows. The stem points into a target room, the strict local plurality identifies the source room, and the center either carries an explicit payload or inherits the source color. The glyph is erased, the target room is flood-filled from the seed beyond the stem, and an optional isolated five-cell L cue is erased and rotates the completed grid clockwise or counterclockwise.

The native axis is `payload_mode`: `payload` is the canonical parent rule and `source_only` deliberately ignores explicit centers while preserving inherited arrows and rotation. Generated scenes cover inherited and explicit payloads, edge-centered arrows, and both L-cue directions. The default program is byte-identical to `reference.rkt`.

Verification retained in the return:

- all 6 supplied labelled official pairs execute exactly in Python and protected Racket;
- 33 focused task tests pass with zero failures or errors;
- authoring preflight passes for both settings, two demonstrations, and four distinct queries;
- the 32-seed finite-rival audit covers 192 episodes / 1,472 pairs with no failures;
- adversarial/private-export checks cover 18 episodes / 138 pairs with no failures;
- generated protected-Racket stress covers 96 evaluations with no failures;
- the causal witness is reviewer-replayed and changes B when A's selected-payload intermediate is replaced.

## Scope and status

No shared repository source, canonical dataset, or immutable `public-parent.json` was changed. The return intentionally contains only the two assigned task-home deltas plus compact checks and required review documents. These receipts are authoring evidence, not owner qualification, training admission, or acceptance; both tasks still require owner registration, source reconciliation, unchanged native qualification, and fresh acceptance.
