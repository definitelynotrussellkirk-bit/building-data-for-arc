# Working notes: 7d970a1ea99b

## Base generator repair

- Preserved the selected canonical rule and `RULE_HASH=2b970065d6a3`.
- Replaced the conflicting source grammar with collision-free sampling: at most one occupied cell per unordered transpose pair, so `(overlay g (transpose g))` never destroys a differently colored original.
- Ordinary lessons now cover upper- and lower-triangle sources, diagonal cells, boundary contacts, three colors, and explicit counterexamples to identity, one-triangle-only, anti-diagonal, and one-color shortcuts.
- The declared controls are now only the controls generation consumes: `side=6..16`, `n_off_diagonal=3..12`, and `n_diagonal=0..3`. Overrides are exact and observable.
- `seed` and `sample_index` now require exact integers; sample indexes must be nonnegative. This was found by strict defect lint and retained as a regression test.

## Native parametric family

`reflection_scope` is episode-fixed:

- `all` — byte-exact canonical default; reflect every nonzero source cell.
- `diagonal_cued` — locate the unique nonzero main-diagonal cue, read its color, then reflect only source cells of that input-derived color.

The two settings use matched inputs. The minimum two demonstrations vary the cue color and cross color-frequency ranks, preventing a fixed-color, fixed-position, or frequency-rank replacement for cue discovery. The adapter supports 2–6 demonstrations and a 1–4 prefix of four prebuilt distinct queries. The full query bank is 8×8, 13×13, 20×20, and a substantive boundary-spanning 30×30 scene.

## Adversarial review and evidence

- 15 focused tests pass.
- 96 parametric episodes passed across both settings, demo/query minima and maxima, 12 seeds, and 24 substantive 30×30 cases.
- 864 fixed-color and 480 fixed-diagonal-slot shortcuts were refuted; 48 matched-input checks passed.
- Base checks: 120/120 protected-Racket applications and Python-mirror comparisons, strict defect lint clean, 120/120 lawful semantic draws, 12/12 identifiable lessons, and 3/3 rival claims verified.
- Native authoring preflight: four jobs, two settings, 24 labelled parametric pairs, five canonical pairs, and 32 protected-Racket evaluations.
- Causal witness: step A reads the diagonal cue color; step B masks/refects by that value. Replacing cue color 1 with 4 changes the final protected-Racket output.
- Sequential public projection: 16 one-query views, 24 first-turn private/future-query invariance checks, and four positive controls passed.

## Limits

This is finite reviewer evidence. It does not prove universal uniqueness over all possible grids. Owner source review/native acceptance and training admission remain separate; no approval flags were changed.
