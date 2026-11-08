# Working notes: b2f8fcc010d5

## Current rule and repair

Read the nine fixed input coordinates declared in `SAMPLED_POSITIONS` from a 5x5
input into a 3x3 output. All other cells are decoys. Racket remains the label
authority; its normalized hash is `f524e4ea450b`.

The source-matching audit A-b2f8fcc010d5-1 demonstrated that seed 67, medium,
indices 0–2 produce corner-anchor demonstrations that cannot distinguish an
opposite-corner swap. Index 3 separates those corners. The unpatched automatic
three-demo lesson accepted this query with `lesson_check = not_declared`.

The repair adds `CANONICAL_SHORTCUTS["swap_opposite_corners"]` and a
`lesson_identifiable(demos, query)` hook. The hook considers every rule that
independently selects one of the 25 input cells for each output cell. It filters
coordinate candidates using demonstrations only, then rejects a query if any
surviving coordinate gives a different value. This covers sampled-coordinate
permutations and decoy substitutions. Alternatives that agree on the query are
harmless; each query is checked independently, without treating another query
as a demonstration.

This is a **lesson acceptance repair**, not a sampler change. Automatic
unsupported lessons fail visibly. Explicit counts can still return
`diagnostic_unsupported`, which remains diagnostic evidence rather than
supported training data. The worker does not resample a rejected lesson.
`generate()`, its sampling helpers, per-grid validation, `VERSION = 2.1.0`, and
the canonical/base Racket programs remain unchanged. Keeping VERSION preserves
the existing deterministic seed mapping; the new source hash binds the guard.

## Verification and retained evidence

- Baseline source: `33579df7feba0fa18710a5627d504d9fb0bc28a46ba71be40cc42e64df4f7cf8`.
- Repaired source: `66c5d69eda0983c8b763d45b58ff2a5b7c101edbc8f153b8bbb75d9412419c4e`.
- Canonical program SHA-256: `68cda958edb644bcd81c25ac99b2c92728012ae684909239f1f39783dd49dfcf`.
- The nine new regressions failed before the change and pass after it. The
  task-local suite passes **17 tests**, with nine additional unittest subtest
  results, both directly and in the staged task-test runner.
- The baseline staged test run failed preflight because inherited tests guessed
  the data root from `__file__`. They now use `reviewer_support`. Authority-sync
  assertions compare whitespace-normalized programs, matching RULE_HASH, and
  still require raw_code and target_code to be byte-identical. The canonical
  and task-bound program bytes were not edited.
- Actual canonical Racket application passed **52/52** retained inputs and
  matched the independent Python screening labels: four canonical inputs,
  eight seed-67 inputs, four representative adversarial inputs, and 36 palette,
  sampled-kind and decoy-boundary inputs. All 52 pass the generator domain check.
- Public generation reproduces the original seed-67 episode before the repair;
  after the repair the same automatic call exits 1 and writes no episode.
  Explicit three-demo/four-query generation is retained with unsupported flags
  `[true, false, true, true]`. Seed 1 medium produces a supported automatic
  three-demo/four-query lesson. Reversing query order preserves its individual
  verdicts. The original seed-67 four-pair leave-one-out flags are
  `[false, false, false, true]`.
- The bounded adversarial pass completed in 0.973 seconds. It checks all 36
  sampled-coordinate swaps, 144 output/decoy substitutions, 792 query verdicts
  against explicitly enumerated replacement rules, and 792 foreground-color
  permutations. No mismatch was found.

Compact evidence is under `../../../checks/b2f8fcc010d5/`; in particular
`adversarial/report.json`, `adversarial/verified.json`, `task-tests/result.json`,
and the before/after command receipts. The minimal original Racket-labelled
witness is `counterexamples/review-5bbd1c7f3c08fb63/seed67-medium.json`.
`workspace/probe_lesson_guard.py` prepares the bounded probe and verifies the
separate Racket and production-workflow evidence without overwriting receipts.

## Remaining sampling limit

A fixed Python screen used seeds 0–31 plus 67, start index 0, and each difficulty.
These counts measure agreement within the fixed-coordinate selector family;
only the selected retained inputs received separate Racket replay.

| Difficulty | 3 demos / 1 query | 3 demos / 4 queries | 4 demos / 1 query | 4 demos / 4 queries |
| --- | ---: | ---: | ---: | ---: |
| easy | 25/33 | 11/33 | 29/33 | 14/33 |
| medium | 26/33 | 16/33 | 28/33 | 19/33 |
| hard | 26/33 | 25/33 | 33/33 | 32/33 |

Only 1, 1, and 3 of the three-demo/four-query episodes respectively failed solely
because of decoy alternatives; sampled-coordinate ambiguity accounts for most
rejections. Raising a random demo count is not a guarantee. A future deterministic
teaching schedule is separate work and must preserve the observable axes and
be evaluated over supported starts and query-order policies.

The audit index is unchanged. Recommended disposition: accept the prevention of
silent automatic use for these repaired bytes while retaining the original
ambiguity witness and the sampler limitation above. No universal
identifiability, all-seed reliability, new source approval, or training-admission
claim follows from this repair. Full batteries and unrelated checks were not run.
