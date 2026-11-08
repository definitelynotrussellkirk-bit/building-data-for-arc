# Working notes: 204213f10aff

## 2026-10-26 reviewer repair

- Replaced the version-2.0.1 sampler with version 3.0.0 while preserving the selected canonical Racket rule hash `7e1018f60923`.
- Repaired both retained source-bound findings: legends now occupy sparse, non-prefix top-row positions, and every ordinary draw includes 1–3 unlisted-color body distractors that the legend must exclude.
- Replaced dead/coercive controls with exact observable integer axes: `grid_h=9..30`, `grid_w=12..30`, `piece_count=2..4`, and `distractor_count=1..3`. Added structural analysis, strict self-checking, and override observation.
- Built the task-local `piece_order` family. `legend` is the byte-exact canonical program; `area_descending` consumes the same decoded/cropped pieces and stable-sorts them by occupied area before packing.
- The first two matched demonstrations cross legend order, occupied area, bbox area, color rank, width, height, and body position. Four fixed-count queries include a substantive 30x30 boundary scene. All scenes retain unlisted-color distractors.
- A retained bounded adversarial probe covers 64 production draws, 64 min/max episodes, 3,584 total rival evaluations, strict verifier/export attacks, and 32 protected-Racket evaluations. This is finite evidence, not universal uniqueness.
- The max-lesson probe initially exposed a certificate crash when the `pack_all_body_colors` rival exceeded 30 columns. The rival is now total: it wraps its all-body gallery within ARC bounds, so its rejection is based on an actual wrong output rather than runtime failure. A focused regression is retained.

## Pending authority

Owner source review, fresh native qualification/acceptance, and any training admission remain separate. This return must not edit approval flags or claim accepted status.
