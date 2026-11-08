# Working notes: 70abd9105769

## Current decision

Preserve the selected canonical program byte-for-byte. The production generator now samples filled 3x3/5x5 squares with repeated colors, strict exact controls, deterministic constructive placement, Boolean/type rejection, and realizability checks. Differently colored canonical squares may touch; each monochrome 4-component must still be a filled odd square of side at least 3.

The nearby native setting is `majority_frame`:
1. reduce every square to its colored center;
2. on that input-dependent intermediate, choose the unique object-majority color;
3. frame the bounding box of those centers with color 9, preserving centers.

The sampler deliberately makes a different color the raw-pixel majority by using fewer larger squares. It also keeps nuisance centers outside the target box and reserves all four minimum-lesson corners for 3x3 nuisance objects, crossing target role against source position.

## Defects repaired

The previous generator taught one color per square, advertised inert `n_distinct_colors`/`palette_size` controls, and exposed texture choices that did not faithfully represent the canonical domain. Those surfaces were replaced rather than silently coerced.

Deep review found and retained three concrete teaching failures:
- seed 21: the top-left source square was the target color in both demonstrations;
- seed 79: the first largest square was the target color in both demonstrations;
- protected Racket: sorting by the latest top-left anchor (distinct from the farthest lower-right edge) selected the target in 7/10 sampled episodes.

The first two demonstration profiles now use only 3x3 targets, 5x5 raw-pixel decoys, and 3x3 nuisance corners. The declared minimum remains two demonstrations.

## Evidence and limits

Final focused tests: 18/18. Final semantic sweeps: 400 two-demo episodes and 100 six-demo episodes, zero ambiguity and zero surviving declared rivals. Protected Racket: 20 episodes, 23 complete wrong programs, 350 evaluations including 120 selected-label replays, one retained counterexample per rival, and zero survivors. A substantive 30x30 query contains boundary contacts in all quadrants.

Finite rival testing is not a proof of universal uniqueness. Owner source review, native qualification/acceptance, official-query gold review, training admission, and training activation remain downstream gates.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/70abd9105769/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->
