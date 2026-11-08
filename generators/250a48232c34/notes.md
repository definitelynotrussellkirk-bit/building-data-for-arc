# Working notes: 250a48232c34

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/250a48232c34/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->

## Parametric family review — 2026-10-25

**Base repair:** unknown keyword overrides were silently ignored. `generate` now rejects every key outside `AXES` before constructing `gen_ctx`; the regression verifies the typo `n_anchor` fails closed and that rejection does not perturb the valid deterministic draw. The production generator SHA-256 is `f10ba457c7cbaa30ebaffca4c0f4a93805814710ea45367566637412cd782dcd`.

**Decision:** add a task-local episode parameter `rotation_direction = clockwise | counterclockwise`. The default `clockwise` program is byte-identical to canonical SHA-256 `04793d6ba90d6882f0d6544b4fe8315209679e63819062864250da5a45b865a6`. The alternative reverses the color-coded quarter-turn direction while preserving the color-1 identity and color-3 half-turn cases.

**Teaching design:** every scene has one asymmetric gray template and one anchor of each color 1–4; the color-to-corner assignment is shuffled so position cannot replace color role. Inputs are matched across settings, 2–6 demonstrations and 1–4 queries are supported, and the fourth query is a distributed 30×30 case with a 6–7-cell template. A 128-episode audit found no harmful demonstration-only survivor among six named shortcuts.

**Evidence and limits:** the final task suite passes 28/28. Authoring preflight passed 4 source-bound jobs and 40 protected-Racket evaluations; substituting the clockwise intermediate into a counterclockwise episode changed the final output; 16 public one-query views passed 24 private-field invariance checks and 4 positive controls. These are finite reviewer checks, not owner qualification, acceptance, or training admission. The next action is owner integration followed by native exact-source qualification and fresh acceptance.

