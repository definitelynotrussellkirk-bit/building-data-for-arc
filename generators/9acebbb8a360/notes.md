# Working notes: 9acebbb8a360

## Current decisions

- Preserve the useful prior repair: exactly two non-overlapping rooms, bounded retry with a deterministic legal fallback, and explicit malformed negative fixtures.
- Sample the two seed colors without replacement. Independent per-room sampling admitted same-color lessons (for example seed `1`, sample `0`), leaving a one-global-color shortcut consistent with the lesson.
- Advertise only controls that are both live and non-singleton: `grid_h` and `grid_w`. Reject stale/unknown overrides, booleans masquerading as integers, invalid difficulties, and mixtures of degenerate textures with ordinary controls.
- Treat a closed color-5 frame with a strictly interior seed as the semantic domain. The checker accepts canonical three-cell-wide rooms; generated layouts may use stronger size/clearance preferences without redefining the rule.
- Keep the canonical Racket rule unchanged. Bind the Python mirror and semantic witnesses to rivals `identity` and `single_global_seed_color`, and require lesson-level separation.

## Reversals made during review

- Removed `n_frames` from `AXES` after lint showed it was only a singleton control; calls that try to override it are rejected instead.
- Lowered the structural frame minimum from four to three after the canonical self-check exposed an official three-cell-wide room. The earlier minimum was a generator preference incorrectly promoted to rule validity.

## Remaining limits and next action

Verification is bounded rather than a universal proof: it covers all 42 declared canvas shapes across three bands, 1,000 default draws, forced retry exhaustion, 120 Racket smoke applications, the repaired regression/boundary cases, and semantic-gate samples. The next useful action is maintainer replay and merge of this source-bound delta; no rule edit or broader peer battery is required for this return.

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
