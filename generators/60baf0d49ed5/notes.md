# Working notes: 60baf0d49ed5

## 2026-10-25 source review and native parametric build

The retained source advertised palette and color-count controls but did not use them, and an episode could teach a fixed horizontal mirror because its demonstrations did not require reading the A→B analogy. Version 3.0.0 makes both controls effective, uses fully asymmetric A/C panels, and cycles the five allowed operations over consecutive samples.

The native family adds `application_mode`:

- `direct` preserves the selected canonical Racket program byte-for-byte: infer A→B and apply it once to C.
- `repeat_transform` performs a sequential composition: Step A infers the operation and builds the once-transformed C; Step B consumes that intermediate and applies the same operation again.

The protected counterfactual replaces the Step-A intermediate with the original C, which collapses the result to the canonical direct program. Authored limits are 2–6 demonstrations and 1–4 private queries. The largest lawful scene is 9×29: three square panels plus two divider columns cannot form an exact 30×30 grid.

Evidence and qualification are source-bound under `workspace/parametric/evidence/current/` and `WORK/checks/60baf0d49ed5/`. Training admission remains false pending owner review and integration.
