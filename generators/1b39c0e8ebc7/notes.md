# Working notes: 1b39c0e8ebc7

## 2026-10-26 repair and native-family review

### Canonical/base repair

- Re-read the canonical Racket rule and corrected the prior summary: the output is an all-zero grid with color 7 only at qualifying landing cells; input markers, sources, targets, and decoys are **not** copied.
- Replaced the four-vector sampler with a strict 24-vector signed domain that includes the canonical vectors `(2,3)`, `(3,1)`, and `(3,2)`.
- Made every advertised override exact and fail-closed, including `vector`; booleans, floats, unknown controls, malformed vectors, and out-of-domain values are rejected.
- Ordinary scenes now contain forward matches, reverse-only pairs, unmatched color-3 sources, and unmatched color-4 targets. This directly repairs the retained “recolor every 4” shortcut and gives the vector direction causal work.
- Added constructive high-density 30×30 generation with boundary and quadrant spread.

The older audit remains retained against its original source hash. The proposed source repairs its three findings, but owner review and fresh acceptance are still pending.

### Native parametric family

Selected one meaningful episode-fixed parameter, `vector_direction`:

- `forward` is byte-for-byte the canonical Racket program and uses the 8→9 vector;
- `reverse` uses the 9→8 vector while preserving the source/target intersection reasoning and empty-output convention.

Inputs are matched across settings. Episodes support 2–6 demonstrations and exactly four queries. The first two demonstrations are constructed to distinguish the two settings and the tested shortcut family. Query sizes are 11×13, 17×19, 23×27, and 30×30.

Sequential dependency:

1. **A:** locate the unique 8 and 9 markers and compute the signed episode-selected displacement;
2. **intermediate:** `(dr, dc)` for 8→9 in `forward`, or its negation for `reverse`;
3. **B:** translate every color-3 source by that intermediate and paint 7 only where the translated coordinate contains color 4.

Changing/skipping A changes which target coordinates B tests and therefore changes the protected-Racket output.

### Adversarial review and repair

The first adversarial pass found a real smallest-lesson failure at seed 31 under `reverse`: choosing the nearest color-4 targets to marker 9 fit both demonstrations while disagreeing on a query. The exact pre-fix lesson is retained in `workspace/parametric/evidence/current/seed31-nearest-target-counterexample.json`.

The repair keeps the two-demo minimum. It constructively relocates the marker pair while holding source/target geometry fixed until nearest/farthest marker-ranking shortcuts are refuted for both settings. Immutable scene caching then removed a long-tail regeneration cost without changing scene bytes.

Final bounded checks on current source:

- 11 focused task tests passed, including protected Racket execution;
- 64 two-demo episodes × 14 relevant rivals = 896 shortcut checks, with no surviving declared rival;
- crossed controls varied the intended intermediate at fixed non-marker cells and varied nuisance positions at a fixed intermediate;
- 192 sampler-stress episodes checked 1,472 scenes across 32 seeds, demo counts 2/3/6, both settings, all 24 vectors, and 320 unique inputs;
- all stressed 30×30 scenes met the recorded spread threshold.

Finite rivals and seeds do not prove universal uniqueness. No known supported-minimum ambiguity remains in the exercised family. Owner source review, native acceptance, and any later training admission remain separate.
