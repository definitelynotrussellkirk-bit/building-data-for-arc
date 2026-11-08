# Working notes: 557449d8b860

## 2026-09-28 review

The canonical rule was already correct and synchronized, so this review changed only the generator contract and input curriculum.

Baseline defects:

- no `RULE_HASH` pin;
- nine declared axes but several were inert, unobservable, single-token, or accepted as ordinary negative fixtures;
- declared bounds disagreed with difficulty-specific draw bounds, producing 7,097 override findings;
- `self_check` accepted all 54 generic destructive mutations;
- only 4/60 generated grids matched an exact canonical profile and 10/60 fell in the canonical envelope;
- no semantic contract or generated shortcut counterexamples.

The replacement grammar exposes five measurable axes: `grid_h`, `grid_w`, `n_cells`, `n_occupied_columns`, and `palette_size`. It constructively realizes the full Cartesian product in every difficulty band. Internal scene modes add canonical scatter, deep columns, bottom-supported partial falls, and mixed cases without pretending those modes are exact public overrides.

Named rivals cover identity, order reversal, treating floor contact as a frozen column, and applying gravity only to canonical-depth columns. The latter two fit every canonical pair and are now refuted by generated witnesses.

Final production battery: 12/12 green. Exact canonical-profile support rose to 32/60 and envelope support to 42/60. The semantic census measured 338/600 strict hits; all four witnesses fired and all four rival claims were verified.
## Current reviewer considerations

Source SHA-256: `f56d883e0c6df128521ee050463f4d768119c985d0f580a292611a2bc19abc51`.

# Decisions for 557449d8b860

## Authority and scope

**Decision:** Keep the selected Racket rule unchanged and pin `RULE_HASH = "c3638032481f"`.

**Evidence:** The baseline rule smoke applied the rule to 120/120 cases without a crash; grammar, Racket lint, authority synchronization, and execution parity were green. The canonical written solution and implementation both specify independent downward packing per column while preserving order. Changing a correct authority would add risk without improving data.

**Alternative rejected:** Rewrite or wrap the Racket rule. There was no behavioral defect to justify it.

## Public axis contract

**Decision:** Replace the old nine-axis surface with five exact axes:

| Axis | Domain | Rationale |
|---|---:|---|
| `grid_h` | 6..10 | Covers every canonical height (6, 7, 8), preserves moderate generalization, and keeps every cross-product constructible. |
| `grid_w` | 6..10 | Covers every canonical width (6, 7, 8) with broader but bounded layouts. |
| `n_cells` | 5..10 | Canonical inputs contain 5 or 6 cells; the upper range supports deeper columns without dense-grid shortcuts. |
| `n_occupied_columns` | 2..4 | Canonical inputs use three columns; two and four prevent a fixed-three-column strategy while avoiding a one-column-only lesson. |
| `palette_size` | 2..5 foreground colors | Canonical inputs use four or five foreground colors; lower values teach color irrelevance while every selected color is guaranteed to appear. |

The original rationale for `palette_kind`, `position_bias`, `n_distinct_colors`, `density`, and `texture` was not preserved in notes. Runtime probes showed they were inert or single-token, and the negative textures were mixed into the ordinary valid domain. Keeping them would make the API larger but less truthful.

**Alternative rejected:** Preserve the old declared ranges (`grid_h/grid_w` to 15, `n_cells` to 30) and patch only individual failures. The actual generator never sampled most of those domains, difficulty bands rejected valid declared values, and some combinations would hide movement or require a different scene grammar.

**Probe:** The strict override battery exercised 235 cases across three bands and 21,150 draws. Every draw was accepted and exactly observable; unknown keys are rejected.

## Canonical anchoring without memorization

**Decision:** On 62% of ordinary draws, select one of the four canonical `(height, width, total-palette)` profiles and heavily weight—rather than force—its values. Every weighted option list still contains the full public domain, so all overrides remain legal in all bands.

**Rationale:** The baseline had only 4/60 exact-profile and 10/60 envelope hits. A correlated prior is required because independent uniform height, width, and palette draws rarely land on a canonical tuple.

**Result:** 32/60 exact-profile and 42/60 envelope hits; semantic strict rate 338/600 (56.3%).

**Alternative rejected:** Emit copied canonical inputs on a fixed schedule. That would inflate the profile score without expanding the rule-relevant geometry and could encourage memorization.

## Constructive geometry

**Decision:** Allocate 5..10 cells as a positive bounded composition across 2..4 columns, with each column holding at most `height - 1` cells. Ordinary non-supported columns exclude the bottom row so at least one cell necessarily moves.

**Rationale:** This proves feasibility for the entire Cartesian axis product and removes rejection/fallback behavior. It also prevents an identity-only scene.

**Failure mode considered:** `height=6`, `n_cells=10`, `n_occupied_columns=2` is the tightest capacity case. The construction produces two five-cell columns, each with one remaining vertical gap, so it remains lawful and non-identity.

## Hidden scene modes

**Decision:** Use internal, non-public modes: canonical scatter, deep column, bottom-supported partial fall, and mixed.

- **Deep column:** at least four cells when the selected counts permit it. This refutes “gravity only works for canonical-depth columns.”
- **Bottom-supported partial fall:** one column includes a floor cell and leaves the penultimate row empty. This refutes “floor contact freezes the whole column.”
- **Mixed:** can satisfy both counterexamples in one scene.
- **Canonical scatter:** balances cells across columns to resemble the public sparse manifold.

These are hidden modes because they are curriculum choices, not quantities that can always be recovered uniquely from an output grid.

**Alternative rejected:** Publish a `texture` or `scene` axis. Overlapping observable outcomes would make exact override verification ambiguous.

## Color and order construction

**Decision:** Draw exactly `palette_size` distinct nonzero colors, use every one, and force the top and bottom cells of a multi-cell column to have different colors.

**Rationale:** Gravity is color-symmetric, but order preservation is not visible when a stack is monochrome or palindromic. The construction guarantees a counterexample to a reverse-within-column rival.

**Alternative rejected:** Assign every cell independently from 1..9. That can silently omit declared colors and occasionally makes the order rule unidentifiable.

## Validator

**Decision:** `self_check` now enforces dimensions, literal ARC values, 5..10 foreground cells, 2..4 occupied columns, 2..5 foreground colors, a multicolor stack, and non-identity under gravity.

**Rationale:** The old validator accepted empty grids, full grids, singletons, and all 54 generic destructive mutations. The new checker must reject rule-hiding structures while retaining color-renaming symmetry.

**Result:** All four canonical inputs are accepted; 32/59 generic destructive mutations are rejected. Color swaps remain accepted intentionally.

## Semantic contract

**Decision:** Declare four named wrong rules and matching witnesses:

1. identity;
2. reverse order while packing;
3. freeze any column touching the floor;
4. apply gravity only to columns with at most three cells.

The last two are declared `CANONICAL_SHORTCUTS` because they reproduce every public canonical answer. Generated witnesses explicitly refute them.

**Result:** All four witnesses fired in the 600-draw semantic census, and all four rival claims were verified. The floor-contact witness fired 120 times; the deep-column witness fired 147 times.

## Tests and limitations

A six-test regression file covers canonical acceptance, exact overrides and boundaries, distribution/witness floors, malformed and identity-only scenes, deterministic/global-RNG-pure replay, and actual disagreement between witnesses and rivals.

Remaining limitations:

- The curriculum covers only downward gravity, as required by this task; it does not teach direction inference.
- Grids remain sparse, at most 10×10 with at most 10 cells. Very dense or tall-column performance is outside this generator's intended manifold.
- `strict_canonical_like` follows the repository's empirical H/W/palette profile definition; it does not claim exact geometric equivalence to a canonical input.
- Counterexamples are guaranteed at corpus scale, not yet within every sampled training lesson. `QUESTION_ANSWER.md` proposes the cheapest gate for that residual risk.
- The Python gravity function is a validation/oracle mirror only. The selected Racket rule remains the output authority.
