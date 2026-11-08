# Working notes: db63430eeffa

## 2026-10-23 — canonical API repair

- Baseline generator SHA-256: `7c732860b8701c13d24771feba4fbaec9103d541a7c8c903ff42c16a596dd581`.
- Repaired the source-bound `A-DB6-001` symptoms at the generator boundary: unknown override names now fail, `seed`/`sample_index`/`difficulty` and override scalar types are checked before `gen_ctx`, and negative `sample_index` fails.
- `square_diagonal` remains accepted because it is rule-lawful—the two constructed paths coincide—but is now declared through `LAWFUL_DEGENERATE_TEXTURES`. It is still an edge texture, not evidence of a distinct ordinary output family.
- Kept `VERSION = "2.2.0"`: valid calls and draw order are byte-preserving; only formerly invalid controls are rejected and a linter declaration was added.
- Current generator SHA-256 after repair: `2531249a89d6991dc3644274518f787d6de3bd2a734000d9119c708c9a399acf`.
- Focused result: 17 tests and 48 subtests pass; defect lint passes. The historical audit record remains `needs_triage` until maintainer assessment rather than being self-cleared here.

## 2026-10-23 — proposed path-selection parameter

- Added an unselected task-local prototype at `workspace/parametric/` with one hidden episode-fixed parameter: `path_mode ∈ {both, diagonal_first, straight_first}`.
- `both` is the exact canonical/default Racket source (exact SHA-256 `738576fedc01cbcd29e0e5a381777ed10929461bca3c60994cee0a3fb4010c46`; normalized SHA-256 `3e3bf77eb552f1b44d376e68304bd479643b4dce5f09e62b73ff0f17a69e083b`). The two alternative programs remove exactly one of the canonical path walks; endpoint extraction, direction/major-axis logic, colors, and all input sampling stay invariant.
- Every retained setting uses the same seven inputs for seed 17, with three demonstrations and four distinct queries. Protected Racket execution agreed with the Python mirror for all settings/pairs, and demonstrations left exactly the selected setting among the three declared rivals.
- Public challenges omit the path setting, program, seed, sampling metadata, and query outputs. Their filenames/IDs are SHA-256 of exact visible bytes.
- A separate 32-seed sweep checked 96 episodes / 672 pairs: all were identifiable, query sets were distinct and demo-disjoint, all settings shared inputs within a seed, and private mutations did not change public IDs.
- Limits: this is finite declared-rival evidence only. The prototype is not catalog-selected, approved, or admitted to training; no claim is made about undeclared rival programs.
