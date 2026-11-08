# Working notes: 306f5b5f899c

## 2026-10-24 repair

The prior generator under-covered the canonical canvas and singleton grammar, accepted unknown controls, and advertised helpful textures that did not affect its palette. Version `3.1.1` restores 7×9 canonical support, 2–5 separated motifs with singleton distractors, broader connected-polyomino shapes, live palette texture aliases, exact observable `n`/`n_distinct_colors`, and strict public override validation.

A dependent-default regression was found during final stress: a standalone `n_distinct_colors=5` request could draw two objects first and reject itself. Defaults now expand `n` and `palette_size` to the requested distinct count, while contradictory explicit pairs are rejected clearly. The canonical Racket rule was not changed.

Evidence: `checks/306f5b5f899c-task-tests-final/`, `checks/306f5b5f899c-lint-final/`, `checks/bounded-override-final/`, `checks/final-adversarial/`, and `checks/racket-parity-final/`. The bounded official override analyzer completed 4,059 draws with no findings; the focused adversarial probe adds 720 exact single-axis observations and 320 deterministic/default draws.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/306f5b5f899c/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->
