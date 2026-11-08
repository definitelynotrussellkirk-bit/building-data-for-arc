# Review notes: d1dab66b0d54

## Canonical defect and repair

The inherited `2.0.1` sampler did not model the canonical puzzle. It emitted exactly two green cells plus a short red line near the positive canvas edge. The selected Racket rule infers a positive guide interval from the green cells, erases all red cells, and repaints only in-bounds destinations. A bounded seed-17 probe therefore produced red counts `3→0`, `2→0`, `2→0`, and `2→0` while the old `self_check` still returned success.

Version `2.1.0` replaces that sampler with a constructive canonical scene: four to nine equally spaced green guide cells and an eight-cell red 3×3 ring centred on a guide point with two later guide positions. Horizontal and vertical guides, spacing 2–5, dimensions 9–30, guide count, and source index are exact controls. The ring always moves forward in bounds and remains nontrivial. The semantic validator now checks exact ARC colors, guide collinearity/equal spacing, the complete ring perimeter, its green centre, and a later guide point. All four canonical pairs are accepted and the Python mirror matches their labels.

A focused census generated 240 ordinary scenes (`3 difficulty bands × 80 seeds`): every input and translated output retained eight red cells and passed validation. A 30×30 exact-control case spans more than 20 columns rather than padding a small puzzle. Unknown, coerced, and infeasible controls reject explicitly.

## Parametric direction prototype

`workspace/parametric/` adds one episode-fixed parameter:

- `forward` is the exact canonical Racket program byte-for-byte.
- `backward` negates the inferred guide interval while preserving the same clearing/repainting law.

The prototype places the source ring on an interior guide point, making both directions total over the shared input grammar. Every demonstration separates the settings. It supports 2–6 demonstrations and independent 1–8 queries; retained evidence uses three demonstrations and four distinct queries with both orientations and a content-bearing 30×30 case.

Bounded adversarial checks targeted the previous erasure surface and minimum/maximum lesson counts. A wider boundary-seed pass then found one deterministic collision at seed `-2^63`: query indices 0 and 4 could choose the same visible layout when eight queries were requested. A regression now pins that case, and a bounded deterministic novelty retry preserves query-prefix stability while guaranteeing distinct episode inputs. All generated labels retained eight red cells; all demo counts 2–6 refuted the alternate direction; invalid counts/settings/grids failed before a partial episode. Protected Racket replayed two retained episodes, one per setting, for 14 label executions. Public challenge bytes exclude the direction, program, and query answers.

The native source/evidence manifest is current. Native owner qualification was attempted but correctly refused because this repaired production generator is not yet catalog-approved on its current source/rule binding. That is an approval-state boundary, not a prototype execution failure; no acceptance or training admission is claimed.
