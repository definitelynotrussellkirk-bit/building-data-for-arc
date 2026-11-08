# Working notes: 61c0bcd32328

## Current decisions — 2026-10-23

- Preserve the canonical `bc93ec48` rule unchanged. The exact canonical Racket text SHA-256 is `0dc3328fe8ad885a19f7c620a4d641ffc733e8cc641a331d01b3e88410c5f64e`; its whitespace-normalized authority hash remains `e3835c9a174e`.
- Repair the retained teaching gap by allowing `_SHAPES[0]`, the one-cell shape, for corner anchors. Generator version `2.1.0` now samples singleton corner components in every general scene profile; the Racket rule already handled them, so no authority or output-law change was needed.
- Keep the nearby `direction` extension task-local and proposed. Values are `clockwise` (the byte-exact canonical default) and `counterclockwise`; the parameter is fixed once per episode, while input sampling is independent of it. Only the corner-to-corner translation direction varies. Component discovery, corner selection, shape preservation, input preservation, and copy coloring stay invariant.
- The prototype emits three demonstrations and four distinct queries by default. Every label is executed in the matching Racket program. Demonstrations refute both the opposite direction and the retained “ignore singleton components as noise” shortcut.
- Public challenge IDs are SHA-256 of exact visible JSON bytes only. Hidden seed, direction, Racket source, and query outputs are kept in private evidence and cannot affect the public ID.
- The fixed profile schedule supports at most ten total demo/query pairs; larger requests fail instead of cloning inputs. Evidence covers seeds `0` and `1`, both direction values, and is bounded rather than universal.
- Base solution files store compact Racket while canonical rows store pretty-printed Racket. Source-sync tests therefore compare whitespace-normalized source, matching the existing `RULE_HASH` convention, rather than requiring byte-identical formatting.

## Evidence and next owner action

- Retained prototype report: `checks/parametric/61c0bcd32328-direction-v1/report.json`.
- Portable selected-task tests: `checks/final/task-tests/` (`22 passed`).
- The direction extension remains `proposed_unapproved`. A maintainer can decide whether to add a production parametric-rule API; this return intentionally does not change shared interfaces, canonical rows, approval, or training admission.
