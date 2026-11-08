# Working notes: db63430eeffa

## Review 2026-10-24 — review-7bf06f49e1f9de14

The task-local `path_policy = both | diagonal_first | straight_first` family now has a native adapter, promotion contract, source inventory, protected-Racket evidence, and a passing native qualification. The production generator and canonical Racket authority remain unchanged; canonical/default `both` still hashes to `738576fedc01cbcd29e0e5a381777ed10929461bca3c60994cee0a3fb4010c46`.

The published contract accepts exactly one declared setting, 2–6 demonstrations, and exactly four distinct queries. Demo and query streams are independent and prefix-stable. Authored profiles span 7×7 through 30×30 while keeping two unequal-gap color-8 endpoints, so all three policies remain behaviorally distinct. The minimum two demonstrations deliberately oppose orientation, major-axis, border-contact, and large-grid shortcuts; all eight feature-conditional rivals per setting are killed by demonstrations and would change at least one query.

Focused validation passed 39 tests plus 62 generated subtests. The retained verifier executed 128 protected-Racket evaluations across all three settings, including replay, shortcut checks, public/private projections, and a causal wrong-intermediate witness. In that witness, step A derives signed endpoint displacement and `major_is_row`; step B consumes those values to draw the selected segment order. Flipping only `major_is_row` changes 73 final cells, so the dependency is not a narrative-only decomposition. The detailed result is projected into the exact source-bound packet replay schema and checked by the native admission validator.

Native qualification passed six source-bound jobs (three settings × seeds 0 and 17), each with three demonstrations and four queries. In every job, the selected setting was the sole demonstration-compatible program. Public export checking passed for all three retained challenges. Status is **ready for owner admission**, not accepted: owner-side fresh qualification, witness replay, acceptance, and any training admission remain pending.

## Current generator contract

`generate(...)` rejects unknown override names even when their value is `None`, non-exact integer axes, non-exact or negative `sample_index`, non-exact `seed`, and undeclared `difficulty` values. `orientation` and `texture` require strings or `None` before `gen_ctx`; this closes the silent `orientation=0`, `0.0`, or `False` random-orientation fallback found while reconciling the second return. `square_diagonal` remains an explicitly lawful coincidence case through `LAWFUL_DEGENERATE_TEXTURES`, rather than an ordinary two-arm teaching example.

`VERSION` remains `2.2.0` because it participates in keyed RNG seeding. The reconciliation retains the existing strict integer draws, seed keys, and canonical rule. All 64 locally compared lawful calls have identical before/after grids, including omitted/explicit-None controls, explicit geometry, and the lawful degenerate texture.

## Historical reconciliation context

`workspace/parametric/` uses one hidden episode parameter, `path_policy = both | diagonal_first | straight_first`. `both` returns the exact canonical Racket source; each alternative deletes one uniquely guarded sibling path loop while preserving endpoint detection and diagonal/major-axis decomposition. Ordinary prototype inputs require unequal row/column gaps so all three settings differ. A default episode fixes one policy for three identifying demonstrations and four distinct queries, and executes all labels/rivals in protected Racket. Public bytes and filenames depend only on visible demonstrations and query inputs.

The incoming `path_mode` implementation remains an unselected source-bound alternative at `workspace/proposals/review-7d8f4fcc562b905b/`. Its overlapping scalar repair, lawful-texture declaration, and three-setting family are already present or superseded by the selected strict-draw/Racket-first implementation. Its categorical guard, fractional scalar cases, endpoint/path-union invariants, and bounded sampler/privacy checks were ported without applying the native patch. Exact decisions and source identities are in `evidence/conflict-reconciliation.json`; the original candidate inventory is unchanged.

## Historical reconciliation verification

Local reconciliation validation: 32 focused tests and 62 subtests passed; the new categorical test first reproduced three silent fallbacks. The cross-setting sampler/privacy checks cover two seeds in each difficulty band (18 episodes, 126 pairs); the standalone verifier separately performed 63 generation plus 63 replay Racket evaluations on three fixed seeds. The wrapper inventory pins current code/tests and keeps both returns' old claims explicitly reviewer-reported against their original sources, including the incoming 96-episode sweep.

At that earlier reconciliation point the prototype had no native adapter. The 2026-10-24 section above supersedes that status with a source-inventoried, natively qualified reviewer-ready adapter; owner acceptance and training admission are still pending. Evidence remains finite and equal-gap layouts remain outside the teaching prototype because the one-path variants coincide. No approval, catalog reference, canonical source, or frozen fixture was changed.
