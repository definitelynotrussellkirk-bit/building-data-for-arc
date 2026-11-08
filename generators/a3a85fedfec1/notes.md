# Current notes: a3a85fedfec1

## Decision

Keep the canonical rule unchanged (`f96ecacc4b71`) and repair only the generator/teaching contract. The selected source moves from generator `2.0.1` / SHA-256 `68793e4bb3d1afb21d8649d3bdb0777714a781095a91b9110f2b81020bdbdf6d` to `3.0.0` / SHA-256 `07ce84a249286ab9134fc211e7211b2523b1cb03cb6aa1fafaeee294d7f83c5a`.

## Reproduced defect

A 2,000-draw census per difficulty band showed that the old random placement exposed any different-color overlap in only 20.30% / 28.05% / 40.25% of easy/medium/hard scenes. The complete adjacent-priority chain appeared in only 20.30% / 12.70% / 2.10%. Several advertised controls were also ignored or disagreed with their documented boundary behavior. Evidence: `checks/baseline-defect.json`.

## Repair

- Replace retry-based random seed placement with a deterministic constructive chain. Every generated input now uses every legend color and contains a distance-two conflict between each adjacent priority rank.
- Alternate sample parity so both numeric priority order and row-major seed order reverse. Any three consecutive demonstrations refute `numeric_min_color`, `numeric_max_color`, `row_major_first_hit`, and `row_major_last_hit`.
- Retain only four honest override axes: `grid_h`, `grid_w`, `n_priority`, and `n_seeds`; validate literal integer types, exact boundaries, unknown keys, difficulty, seed, and sample index.
- Separate lawful-domain validation (`self_check`) from the stronger generated-curriculum requirement (`teaching_check`). This split is required because four of the five canonical inputs lawfully omit the full adjacent-rank conflict chain.
- Add pure observability, a Python authority mirror, semantic rivals/witnesses, lesson identifiability checks, and the lawful priority-blind counterexample at `counterexamples/priority-blind-lawful-input.json`.

## Verification

- Focused staged tests: 10 tests and 329 subtests passed (`checks/task-tests-final/`).
- Complete period-two schedule census: 6 lessons, 24 rotations, 0 ambiguous, 0 hook/materialization/scoring errors (`checks/schedule-period-final.summary.json`).
- Semantic gate: 49/600 strict-canonical-like draws (8.17%, declared floor 4%), all 5 canonical inputs accepted, 4/4 witnesses retained, 12/12 lessons identifiable, 0/48 diagnostic rotations ambiguous (`checks/semantic-source-final/`).
- Native `selfcheck` and `override` stages passed (`checks/selfcheck-source-final2/`, `checks/override-source-final2/`).
- Adversarial replay: 1,200 legal override cross-products, 720 lesson windows, 11 bad scalar/unknown calls, unchanged global RNG, 0 failures (`checks/adversarial-final.json`).
- Protected Racket parity: 14/14 exact outputs, including all five canonical pairs and nine generated/boundary cases; executed and catalog hashes both `f96ecacc4b71` (`checks/racket-parity-final-summary.json`).

## Remaining limits

The managed `grammar` and final managed `rule_smoke` wrappers were externally interrupted with empty stage logs, so no aggregate pass is claimed for either. Direct protected-Racket parity and the semantic gate passed on the final generator source. This package is a routine maintainer review only; it does not approve the generator or admit data to training.
