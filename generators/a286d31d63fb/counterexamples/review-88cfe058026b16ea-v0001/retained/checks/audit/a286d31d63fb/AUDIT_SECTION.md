## a286d31d63fb

**Classification: reproduced generator teaching-coverage and API contract defects. No Racket-rule defect is claimed. The audited source and authority were not modified.**

Generator SHA-256: `a831e29015bb5b1fb90332adedd799655969ce0d925970debdd90d5d2eca5ac2`. Canonical raw rule SHA-256: `bc2002d0a0d4dd9628242b448e63f2a988832268d371b2f1b03c7540d031e7ac`; the active base authority has exactly the same rule text. This is the same generator source as the existing unresolved API audit; the findings below do not close or supersede it.

### New finding: the sampler never refutes a rectangle-only shortcut

The selected rule recolors each component whose per-row cell counts are constant. However, every shape in `_FLAT` is a solid rectangle, and every shape in `_NON_FLAT` is a nonrectangle. The ordinary placement logic preserves those shapes as separate, monochromatic components; the three degenerate modes use the same templates. Consequently, the simpler rival **“recolor solid rectangles to 8; leave every other component unchanged”** agrees throughout the implemented template support. It also fits both canonical TRAIN examples.

A concrete lawful witness separates the two rules. `input.json` is a padded 10×12 grid with three distinctly colored components: a color-2 shifted shape at zero-based cells `(1,1), (1,2), (2,2), (2,3)`, and two ordinary nonflat components in colors 3 and 4. The shifted component has row profile `[2,2]` but does not fill its bounding rectangle. The generator's `self_check(..., difficulty="easy")` returns `[]`.

Actual execution through the supported `arcpuzzles apply` command recolors exactly those four color-2 cells to 8 and leaves the nonflat components unchanged. The rectangle-only rival leaves the entire input unchanged. The retained Racket receipt reports `valid_output: true`, `error: null`, and the expected executed rule hash `bc2002d0a0d4`. This is a reproduced teaching counterexample, not merely a request to expand the domain: it satisfies the stated constant-row-profile semantics, normal scene dimensions, component contrast, spacing, and distinct-color conditions.

Evidence: `checks/audit/a286d31d63fb/probe.py`, `probe.json`, `input.json`, `rectangle_rival.json`, `racket.json`, and `verification.json`. Six templates were inspected exhaustively; 15 ordinary draws (five seeds in each of three bands) agreed with the rival under an independent Python row-profile model. Those 15 checks are explicitly supplemental model comparisons, not 15 claimed Racket executions. The witness alone was executed with Racket.

### Fresh bounded reproduction of API findings

Six direct calls on the unchanged source produced:

| Request | Observed result |
|---|---|
| `generate(0, 0, difficulty="easy", height=8)` | Rejects the advertised height with `ValueError: draw_int('height'): override 8 outside [10, 11]`. |
| `generate(0, 3, difficulty="easy", texture="all_flat", height=10)` | Returns 12×14; its own validator reports no nonflat component. |
| `generate(0, 0, palette_size=2)` | Returns four foreground colors: 2, 3, 4, and 5. |
| `generate(0, 0, difficulty="hard", flat_component_count=3)` | Produces three flat components but only one nonflat component, contrary to the summary's two-nonflat-component promise. |
| `generate(0, 0, typo_profile="sentinel")` | Silently accepts the unknown override. |
| `generate(True, 0)` | Accepts a Boolean seed; request identity is not restricted to literal integers. |

The first five corroborate the existing unresolved API report. The Boolean call records an additional strict-scalar acceptance. Exact calls, working directories, exit codes, observed API facts, source identities, and artifact hashes are retained in `checks/audit/a286d31d63fb/receipt.json`.

**Repair direction:** add at least one connected, nonrectangular constant-row-profile shape and a regression that refutes the rectangle-only rival; repair or narrow advertised controls and align degenerate-mode validation. No repair or approval was performed in this audit.

**Scope:** source/rule inspection; all six shape templates; two canonical TRAIN pairs; 15 ordinary draws; six focused API requests; one constructed, self-check-accepted witness executed by actual Racket; and verification of its four-cell disagreement. No full battery was run. Source hashes were checked before and after.

