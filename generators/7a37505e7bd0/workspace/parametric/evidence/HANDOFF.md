# Parametric prototype handoff — 7a37505e7bd0

**Status: proposed prototype; public-filename leak repaired and v2 checks passed.**
Independent review found that v1 numeric public filenames exposed parameter
setting by suffix modulo six (144/144 classified). V2 filenames are derived
only from the exact canonical public JSON bytes; private IDs and matrix order
remain private. The source-bound defect, expected failures, prior source bytes,
and original exports are retained separately from current v2 evidence. No
production generator, existing test, note, authority, contract, shared script,
or audit-source edit was made by this subtask. The parent separately repaired
scalar controls in production; evidence binds its final generator SHA-256
`9e1b827924f2445dc0f57d593c04b3bb55dc0a47649ef03c276648df90d980d3`.

## Delivered changes

- `WORK/repo/generators/7a37505e7bd0/workspace/parametric/prototype.py`:
  deterministic complete episodes, six bounded rules, actual Racket labels,
  declared-parameter scoring, query rotations, public/private export, exact
  receipts, complete evidence CLI, common-input witness and ambiguity control.
- The same directory's `README.md` and six exact `rules/*.rkt` files document
  the domain, canonical setting, seed selection, execution, replay commands,
  production boundary, and limitations.
- `WORK/repo/generators/7a37505e7bd0/tests/test_parametric_7a37505e7bd0.py`:
  42 focused prototype tests. Prototype code SHA-256 is
  `0a7dfa603bc599dae51d707ea609bce8e71f682256b69d9bf200446060fa72f8`;
  test SHA-256 is
  `35b1e71cd7aae2ce34e6fb7721c6c911bf1ff450fd5edce58fda6f7270879323`.
  README SHA-256 is
  `b315215eef2f072a087a8dd64a2fa5d6ed42a351e3f56b50891cad3ed0263581`.

## Actual verification

All paths below are relative to `WORK/checks/parametric/`. Each corresponding
`*.command.json` retains the actual argv, cwd, exit code and duration. Main
authoring commands ran from `/workspace/scratch/e75e2a7b168e/packet` through
`WORK/.venv/bin/python review.py run ../.venv/bin/python ...`; payload cwd was
`/workspace/scratch/e75e2a7b168e/packet/WORK/repo`.

| Evidence | Actual result |
|---|---|
| `tdd-red.log` / `tdd-red.command.json` | Expected missing-prototype RED: 39 failed, exit 1. |
| `materialize.log` / `.command.json` | Six exact task-local Racket programs written, exit 0. |
| `first-green.log` / `.command.json` | 30 failed, 9 passed, exit 1: general `wrap_rule` required unavailable direct-layout `scripts.comment_solutions`. Retained honestly. |
| `second-green.log` / `.command.json` | Prior source: shared `strip_rule_wrapper` resolved the direct-layout issue; 39 passed, exit 0. This did not cover the later filename defect. |
| `v1-filename-leak.json` and `v2-filename-red.log` / `.command.json` | Filename defect reproduced; new behavior regressions: 4 failed, 38 deselected, exit 1 before implementation. |
| `v2-filename-green.log` / `.command.json` | Current full focused suite: 42 passed, exit 0, 19.75 seconds pytest time; final source hashes unchanged. Covers public-byte filename hashes, identical-payload sharing across private IDs, corrupt-file rejection, and unique-file count. |
| `final-v2-matrix.log` / `.command.json` and `final-v2/report.json` | Six settings × three bands × seeds 0,1,2,17 × starts 0,3: 144 episodes, **144 unique public files**, 864 labels and 864 query rotations; all episodes/rotations refute every other setting, zero ambiguity. Exit 0. |
| `seeded-episode-v2.log` and `explicit-episode-v2.log`, each with `.command.json` | Regenerated seed-selected and explicit-canonical CLI exports both exit 0, with content-addressed public files and private receipts. |
| `retention-integrity-v2.json` / `.command.json` | 444 artifact hashes and 14 current source hashes match; all 864 labels bind to actual execution records; all 144 public bodies and SHA-256 filenames verified; 864 rotations and 4,320 rival scores recomputed from retained outputs, exit 0. |

The main matrix executed **494 real Racket grid applications through six exact
programs**. Cached real labels were reused for repeated grids/rotations; there
is no Python output oracle. Eight canonical labeled pairs matched separately
executed canonical reference output and stored labels. All source hashes were
unchanged across the evidence run.

`final-v2/private/difference-witness.json` retains one lawful exact input yielding
six distinct outputs: 12×12, 12×3, 3×12, 9×9, 9×3 and 3×9. The separate
`ambiguity-negative-control.json` truthfully measures one ambiguous control:
zero-free demos fit both counting policies, while the zero-containing query
separates them. **Zero solver attempts** were created by this subtask.

## Public boundary, retention and parent integration

Public filenames are `challenge-<full SHA-256 of public file bytes>.json`.
Bytes are canonical compact sorted-key UTF-8 JSON with one trailing newline.
The filename adds no information beyond the visible body. Identical public
payloads may share one file, while private episode IDs, receipts and report
references stay separate. Every episode reference remains in the private report;
both episode and actual unique public-file counts are disclosed. Private report
ordering and parameter iteration are not challenge-visible.

`prior-source-v1/` retains exact earlier prototype/test/README bytes;
`v1-source-retention.json` binds their hashes and the old report. Parent handles
verified lossless compression and relocation of the unchanged old `final`,
`seeded-episode` and `explicit-episode` trees. Their old commands and failed logs
remain retained, including unique controls. V2 does not overwrite or relabel
those source-bound exports.

Independent narrow re-review closed the filename finding under this documented
interface after checking all 144 references and unique public files; see
`WORK/checks/code-review/closure.md`. The original finding/evidence remains
unchanged. This closure is separate from the bounded semantic claims.

Parameter identification is only against the five other declared settings in
the reported finite sample. The base sampler's broader histogram-shortcut
limitation remains unchanged and documented. Factor is at least one, all-zero
and non-3×3 inputs remain excluded, and canonical sampler observables are named
as such alongside actual variant labels. Only `public/*.json` is challenge
visible together with their content-addressed filenames; all reports, numeric
IDs, ordering, receipts, labels and rules remain private authoring data.

Parent owns the final portable task-stage/full-suite/battery and return package.
The README and source were frozen before current focused tests, matrix and CLI
exports. All bind the same final hashes. The parent's old 103-pass task receipt
applies only to prior source; parent is rerunning that stage on v2. No copied
runtime trees were added. Reproducible pytest basetemp outputs and every failed
run log are retained; nothing unique was deleted by this subtask.
