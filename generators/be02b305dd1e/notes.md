# Working notes: be02b305dd1e

## Current reviewed state

- Generator version: `3.1.0`
- Final generator SHA-256: `b70ae4e93b362406f3233b4de9d019f8a51ec3c98f176ee35b70b368839e12ee`
- Selected authority hash: `ed1eb3ca2cbf` (unchanged)
- Curriculum: four demonstrations plus one query; twelve exact `scene_profile` values, four per difficulty band.

## Repairs in this review

1. **Strict request scalars.** The baseline accepted booleans, floats, strings, and negative sample indices. `generate()` now requires exact integers for `seed` and `sample_index` (therefore rejects `bool`) and requires `sample_index >= 0`.
2. **Lesson-order shortcut coverage.** A retained semantic replay (`seed=232922564183033`, medium, samples 33–37) let first/topmost-object-only rivals fit all four demonstrations and fail only on the query. Two slots in every four-sample schedule now place the magenta template before the green target in row-major object order, with the seed rotating which profile slots receive that ordering. Every one-pair holdout from a five-pair window therefore leaves a demonstration that refutes first-object-only attribution.
3. **Portable tests.** Canonical-pair loading now uses `reviewer_support.canonical_pairs(..., root=find_root(__file__))` instead of the legacy staged `scripts` namespace.

## Verification summary

- Task tests: 19 passed.
- Strict defect lint: zero flagged generators.
- Semantic gate: 12/12 production lessons identifiable; 0/60 ambiguous query rotations; all declared rival claims verified.
- Wider lesson census: 300/300 materialized lessons, 1,500 pairs and 1,500 rotations; zero production or rotation ambiguities, zero hook/scoring/materialization errors, 1,498 unique inputs.
- Distribution, profile floor, diversity, override contract, grammar, Racket lint, rule smoke, self-check, lint, and authority synchronization all passed independently on the final source.

## Limits

The ordering guarantee is deliberately finite and schedule-local; it refutes the measured first/topmost-object shortcut but is not a proof against all possible solver hypotheses. The aggregate multi-stage battery wrapper stalled at `defect_lint` even though the identical stage passed alone in 11 seconds, so final evidence is retained as source-bound per-stage checks plus a fresh-copy replay rather than a single aggregate receipt.
## Current reviewer considerations

Source SHA-256: `b70ae4e93b362406f3233b4de9d019f8a51ec3c98f176ee35b70b368839e12ee`.

# Decisions: be02b305dd1e

## D1 — Preserve the selected Racket authority

The canonical rule and its hash `ed1eb3ca2cbf` matched the intended transformation and passed rule smoke, Racket lint, execution parity, and canonical-pair checks. I changed no Racket or canonical data. The defects were in request validation and lesson construction, so changing authority would have expanded scope and invalidated otherwise correct labels.

## D2 — Enforce exact integer request types at the public boundary

The baseline strict defect lint reproduced 33 invalid-call acceptances across bands: booleans, floats, strings, and a negative sample index. I chose `type(value) is int` rather than `isinstance(value, int)` because Python booleans are integers under `isinstance`, and accepting them makes replay identities ambiguous. I rejected silent coercion because `1.75`, `"1"`, and `True` must not collapse onto legitimate replay keys.

The regression was written first and failed in `checks/development-red-strict-scalars-v2`; the minimal `_validate_call()` guard then made all 18 cases pass in `checks/development-green-strict-scalars`, and final strict defect lint flagged zero generators.

## D3 — Repair the teaching distribution, not only the diagnostic hook

A real production-order lesson let first/topmost-object-only rivals fit all four demonstrations and fail the query. Merely adding a message to `lesson_identifiable()` would detect but not repair the training example, so I changed generation to guarantee both object orderings within every four-slot lesson. The ordering bit is `(seed + sample_index) % 4 < 2`: exactly two slots place the template before the target, while the seed rotates which profile slots carry that relation.

I rejected three alternatives:

- **Always put the template first:** creates a stronger fixed positional shortcut.
- **Randomly resample until a lesson happens to contain both orders:** makes a single sample depend on surrounding lesson assembly and complicates deterministic replay.
- **Change profile scheduling:** risks reducing existing exact-profile coverage and correlating object order with a fixed profile.

The retained holdout regression failed first in `checks/development-red-object-order` and passed after the repair in `checks/development-green-object-order`. The final 300-lesson census found zero ambiguity in production order or any of 1,500 query rotations.

## D4 — Keep a defensive semantic hook

`lesson_identifiable()` now explicitly reports when demonstrations never refute first-object-only attribution. This is intentionally redundant with the schedule guarantee: it catches future generator refactors that bypass or weaken the construction invariant. It is not treated as a proof against undeclared hypotheses.

## D5 — Use portable canonical fixtures

The task tests now resolve canonical pairs through `reviewer_support` and `find_root(__file__)`. I rejected fixed `parents[...]` path guesses and the staged `scripts` import because the handoff requirement includes a fresh extraction and repository/staged portability.

## D6 — Verification policy after aggregate-wrapper interruption

The monolithic battery stalled at the fourth stage both before and after repair, while the same stage completed alone. I preserved those interrupted receipts and used the packet's documented per-stage fallback: every final stage was invoked separately on generator SHA-256 `b70ae4e93b362406f3233b4de9d019f8a51ec3c98f176ee35b70b368839e12ee`. I do not report the aggregate battery as passed.

## Self-review for new shortcuts or restrictions

The repair introduces an exact 50/50 row-major ordering balance in each four-slot schedule, but the seed rotates its association with the twelve scene profiles, so no profile is permanently tied to one order. Every five-pair holdout retains a non-target-first demonstration, and a 300-lesson/1,500-rotation census refuted all measured generic ordering rivals; the finite rival set remains the explicit limitation.
