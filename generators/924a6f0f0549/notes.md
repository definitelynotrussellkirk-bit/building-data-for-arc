# Working notes: 924a6f0f0549

## Base review and repair

The supplied v2 generator advertised nine axes, but only grid dimensions affected ordinary draws; notably, `target_size` was ignored, several fixed-value controls were inert, and the declared dimensions stopped below the required 30×30 stress surface. The repaired v3 generator exposes only four observable controls: `grid_h`, `grid_w`, `target_size`, and `n_objects`. Every accepted override is consumed, cross-band legal, recoverable with `observe_overrides`, and checked by `self_check`. The canonical Racket program remains byte-identical with SHA-256 `23fd1d61a026f5aed86bf59e77a3fc5ffae49ebbeaea5ff89f5916ea88c264c5`.

The new sampler produces three to five pairwise-distinct component areas, exactly one equal to the color-1 marker count, and deterministic fresh grids up to 30×30. A bounded row-layout fallback guarantees legal output when random compact-object placement cannot fit.

## Parametric family

`render_mode` is fixed for an episode:

- `outline` is the exact canonical program.
- `silhouette` uses the same marker-count-selected object but renders every selected cell before cropping.

Stage A counts row-0 markers and selects the unique equal-area body object. The intermediate is that object's color, area, bounding box, and cell set. Stage B consumes the cell set and applies the episode render mode. Inputs are matched across settings; every selected rectangle has an interior, so every demonstration distinguishes the two finite settings. Episodes support 2–6 demonstrations and exactly four distinct queries. The final query is a substantive 30×30 grid with a 5×5 selected object and four differently sized distractors, not a padded small instance.

## Adversarial self-review

The main shortcut attack replaced Stage A with “take the first body object.” The sampler deliberately puts a different row-major distractor first. On the retained protected-Racket witness, the correct silhouette result is a 3×5 color-4 block while the wrong intermediate produces a cropped 2×2 color-2 L, proving that Stage B's final output changes when A supplies the wrong object. Varying selected dimensions and using matched inputs across settings also defeats fixed-output-size and setting-correlated-input shortcuts. This is finite evidence, not a universal uniqueness proof.

## Verification and limits

- Focused base tests: 4 passed.
- Focused parametric tests: 6 passed, including exact canonical hash and protected-Racket parity.
- Bounded adversarial probe: 12 episodes and 96 protected-Racket evaluations across seeds 0–2 and demo counts 2 and 6.
- Portable changed-target suite: 10 passed.
- Authoring preflight: all 3 canonical pairs, both settings, 24 generated labels, and 32 protected-Racket evaluations passed.
- Current witness replay: `reviewer_replayed` against the exact qualified source binding.

The inventory and receipts are ready for owner source review and native admission. They do not grant variant approval, owner acceptance, or training admission.
