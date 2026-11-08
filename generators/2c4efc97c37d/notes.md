# Working notes: 2c4efc97c37d

## Current rule and authority

The canonical Racket rule is unchanged (`RULE_HASH = dcdf1daba7ab`). Colors 0 and 9 are background. All other cells form a binary 4-connected foreground mask; components are ordered by minimum column then minimum row, peeled by cardinal boundary layers, and their maximum peel depths are returned as one row.

## Repair history

Version 3.0.0 replaced a rectangle-only sampler with constructive squares, diamonds, and L-tailed squares. Every generated input contains an irregular component whose true onion depth differs from bounding-box thickness. It also replaced broad/dead controls with five exact, observable axes:

| Axis | Domain |
| --- | --- |
| `grid_h` | 9..18 |
| `grid_w` | 25..30 |
| `object_count` | 3..4 |
| `max_depth` | 2..4 |
| `irregular_count` | 1..3 |

Version 3.1.0 repairs a second teaching gap. The 3.0.0 distribution used one unique color per component and never emitted color 9, so two canonical-fitting shortcuts survived: treat each non-background color as one object, or treat every nonzero cell—including 9—as foreground. Both shortcuts can obtain correct labels without learning the authority's binary mask.

Every 3.1.0 draw now uses one of two deterministic palette topologies:

- **reused:** two disconnected components with unequal depths share a color;
- **mixed:** one depth-at-least-two connected component has an accent-colored top row.

Every draw also places one isolated color-9 cell in background space. Geometry, exact overrides, component order, and the canonical rule remain unchanged. Construction fails loudly unless all three declared rivals disagree with the intended output.

## Retained counterexample and executable rivals

`counterexamples/binary-mask-shortcuts.json` is one 9×25 lawful witness. Its intended output is `[[1,2,3]]`; the executable rivals produce:

- `bbox_rectangle_depth` → `[[2,2,3]]`;
- `color_partition_depth` → `[[2,2,1]]`;
- `nonzero_foreground_depth` → `[[1,2,3,1]]`.

`workspace/onion_probe.py` independently finds components, computes cardinal peeling, and evaluates all three rivals without importing production geometry helpers. `SEMANTIC_RIVALS`, `CANONICAL_SHORTCUTS`, and `LESSON_COMPETITORS` now register the same three functions, with one witness predicate per rival.

## Validation and lesson policy

`self_check` validates the binary component grammar rather than requiring uniform unique colors. It accepts 0..9 integer cells, ignores 0 and 9 for component extraction, and still enforces exact dimensions, 3–4 components, maximum depth 2–4, at least two distinct depths, and 1–3 irregular components. `observe_overrides` recovers every advertised axis from the returned pixels.

Lessons use three demonstrations and one query. Since each generated pair refutes each declared rival, ordinary lessons and every single-query rotation remain identifiable against all three. This is finite-rival evidence, not a proof of unique human interpretation.

## Verification at source `fddf9f38fe0ac9646fb8fbdd70c2f1a0a184282762b817d5bbc5143e1ecb3873`

- Focused staged suite: **38 passed**, including canonical acceptance, exact override boundaries, all three shortcut witnesses, lesson rotations, malformed inputs, determinism, output diversity, and canonical Racket parity. Evidence: `checks/task-tests-final/`.
- Static generator lint: pass, zero warnings. Evidence: `checks/lint-final/`.
- Strict semantic gate: canonical accepted 3/3; strict draws 600/600; each witness fired 600/600; each rival claim checked 60/60; 12/12 lessons identifiable; 0/48 ambiguous rotations. Evidence: `checks/semantic-gate-final/`.
- Independent boundary census: **512/512** exact-axis cases, covering all four difficulty settings and both topologies equally (256 mixed, 256 reused), with no failures. Evidence: `checks/binary-mask-census/report.json`.
- Focused lesson-rival replay: 3 bands × 4 starts × 4 held-out positions, all declared rivals refuted. Evidence: `checks/lesson-rivals/command.json` and the focused test.

## Decisions and limits

- Palette semantics are scheduled, not advertised as a sixth override: the public control surface stays limited to exact geometric quantities recoverable from pixels.
- Color 9 is placed only where cardinally isolated from foreground. This makes the nonzero shortcut observably wrong without changing component depth or ordering.
- The generator still has a finite shape grammar and alternates only two palette topologies. Template-specific or undeclared rivals may remain; no universal identifiability claim is made.
- A full twelve-stage battery was not run. The changed scope was checked with focused tests, Racket parity, lint, strict semantic gating, and two adversarial surfaces.
- The canonical Racket source, canonical data, catalog approval, and frozen fixtures were not changed.

Imported associated notes remain in `evidence/associated_notes.jsonl`.
