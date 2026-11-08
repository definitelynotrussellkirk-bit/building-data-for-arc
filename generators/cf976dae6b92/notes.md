# Working notes: cf976dae6b92

## 2026-10-26 review-a8b34beeb41b802f

- Reproduced and repaired two base-review defects without changing lawful generated examples or the canonical rule: the portable test used a fixed parent-depth canonical path, and explicit `grid_h`/`grid_w` overrides coercively accepted floats/strings (and treated bool as an integer). The test now uses `reviewer_support.find_root`/`canonical_path`; overridden dimensions use `draw_int_strict`.
- Added the native `relay_policy={fixed_4,nearest_to_2}` family. `fixed_4` returns the selected canonical Racket source byte-for-byte. `nearest_to_2` computes the unique Manhattan-nearest marker among colors 3 and 4, then uses that input-derived relay to choose both route order and bend coordinates.
- The first two shared demonstrations deliberately cross the nearest relay (3 then 4) while holding dimensions and transform fixed. They distinguish Manhattan distance from fixed-color, farthest, Euclidean, Chebyshev, row/column and route-construction shortcuts for the input-derived setting.
- Reversal during adversarial review: an initial audit demanded that the same two scenes falsify every absolute row/column selector under both settings. That is impossible as a general two-example claim, so the final probe records a setting-specific finite rival bank and its scope limit instead of claiming unrestricted uniqueness.
- Current evidence: 32 staged task tests pass; 384 generated episodes pass the bounded rival probe; base authoring preflight executes 5 canonical pairs plus 24 parametric labels through protected Racket; a protected counterfactual changes the final route; 16 one-query views and 24 first-turn invariance checks pass; answer-leak and ID-corruption mutations are rejected.
- Next owner action: review the exact integrated source, rerun native qualification and fresh acceptance, then separately decide whether to admit the family to training. No approval or training flag was changed here.
