# Working notes: 5d6fcce80b6a


## 2026-10-25 review-be44c9681d9b5391 — native parametric admission build

The approved production generator remains byte-identical at
`e603a3763bcdfd01d19d355a529a391b51112d9862466ef82b26b69a28db1c5a`.
Canonical `RULE_HASH = "652672c3e3c3"` and canonical puzzle data are unchanged.

### Native family

Promoted the earlier task-local idea into the native adapter contract under
`workspace/parametric/`:

- `copy_diagonal ∈ {main, anti}` chooses main- or anti-diagonal block copies.
- `separator_policy ∈ {through_last, strict_between}` chooses blank rows at or
  before the last colored source row, or only blank rows strictly between the
  first and last colored source rows.
- The default `main + through_last` returns the exact canonical Racket program
  byte-for-byte (SHA-256
  `4858dc35f6ad70e1770f668d337c75eb0b39b1a81e05a4afaf2b008c83c69f17`).
- Inputs are matched across settings. Counts are independently selectable from
  2–6 demonstrations and 1–4 queries. The four queries produce 14×16, 18×20,
  24×26, and substantive 30×30 outputs.
- Public projection reveals exactly one query input per turn and does not reveal
  settings, programs, answers, future queries, or a total-query hint.

The first two constructive demonstrations identify all four settings and refute
the retained finite shortcut set. The reusable protected-Racket audit is
`workspace/parametric/audit.py`.

### Sequential dependency and causal witness

Stage A scans source rows and produces the input-dependent ordered pair
`(first_colored_row, last_colored_row)`. Stage B consumes those bounds to decide
which blank rows become full-width color-3 separators before rendering the
selected diagonal copies. Replacing the true `last_colored_row` with
`first_colored_row` preserves the source grid and copy policy but removes lawful
separators, changing the qualified final output. The source-bound witness and
protected replay are retained under `checks/5d6fcce80b6a/causal/`.

### Verification and decisions

- 37/37 focused native tests passed; the complete MAIN directory passed 70/70
  directly and 70/70 in a fresh portable staged runtime.
- The bounded audit covered 24 episodes, 184 checked labels, 81 distinct
  protected-Racket executions, ten named rivals, and 32 sequential public turns
  with zero findings. All 32 saved turns passed the structural/leak checker.
- Native qualification passed all four settings on seeds 0 and 17: eight jobs,
  two demonstrations and four queries per job, and 96 protected-Racket
  evaluations.
- The causal counterfactual replay passed with two protected-Racket evaluations.
- Repeated per-test Racket process startup caused an intermittent harness stall;
  task-local tests now share one session-scoped protected bridge. The retained
  prototype test was also made portable through `reviewer_support` rather than a
  source-tree-only import.

No production generator or canonical rule edit was needed. Status is
reviewer-reported ready only. The owner must integrate these exact bytes, rerun
native qualification and the causal replay, and explicitly accept the family.
No training admission is claimed.

## 2026-10-22 review-8f48829dc498f85a

Final generator SHA-256:
`e603a3763bcdfd01d19d355a529a391b51112d9862466ef82b26b69a28db1c5a`.
Version remains `2.0.0`; canonical `RULE_HASH = "652672c3e3c3"` and the
selected Racket authority are unchanged.

### Current rule and sampler

The input is copied exactly into the top-left and bottom-right quadrants of a
2×2 enlarged canvas; off-diagonal quadrants stay zero. Every completely blank
input row at or before the last nonempty row is painted color 3 across the full
output width. The fixed four-demonstration schedule covers internal, leading,
trailing, and multiple blank-row profiles; palettes include single- and
multi-color controls.

### Repairs in this review

- Added an exact public request boundary: `seed` and `sample_index` must be
  exact Python integers, and `sample_index` must be non-negative. This closes
  the strict-lint acceptance of Boolean/coercible/negative controls without
  changing any valid generated output.
- Corrected `CANONICAL_SHORTCUTS`: `green_every_blank_row` and
  `copy_input_to_all_four_quadrants` contradict canonical labels, so they are
  no longer advertised as canonical-fitting. Both remain active in
  `SEMANTIC_RIVALS` and `LESSON_COMPETITORS`.
- Kept the inherited root test byte-identical. New request/registry tests and
  parametric tests live in separate task-local files.

### Verification and lesson policy

The final strict battery passed 12/12 stages. Focused tests passed 34/34 and the
portable task-test stage passed 33/33. A final-source census materialized 100
lessons per band: 300/300 fixed-order production lessons were identifiable with
0 ambiguity, 1,500 pairs, and 1,470 unique inputs. Arbitrary query rotation is
not supported: 550/1,500 rotated queries were ambiguous and 900/1,500 triggered
hook warnings when the held-out pair carried a unique semantic profile. This is
a reported curriculum limit, not hidden as a production pass.

### Proposed parametric extension

`workspace/parametric/` contains an isolated episode-level prototype with
`copy_diagonal ∈ {main, anti}` and
`separator_policy ∈ {through_last, strict_between}`. The canonical/default
setting is `main + through_last`. Four retained episodes cover the 2×2 setting
cross-product with exact Racket/Python parity; causal controls change 52 and 24
cells respectively. The prototype is proposed only and is not wired into
production generation, approval, or canonical metadata.

### Known limits and open findings

- The four original canonical examples do not independently identify leading
  blank-row handling; generated leading controls teach the authority-selected
  behavior.
- Finite declared-rival checks do not rule out every possible shortcut.
- No downstream model-training or accuracy experiment was run.
- The post-repair visible-only solve passed all four demonstrations in one
  revision, with earlier rule exposure recorded honestly; masked labels remain
  withheld.


## 2026-10-02 review-9d4f800edf4b72c2

- Baseline battery passed every individual stage except `authority_sync`.
  Canonical `program_solution` and selected `target_code` were execution-
  equivalent but not exact text, despite `selected_exact_canonical` status.
- Synchronized selected `target_code` to canonical text. Preserved archival
  `raw_code`; no Racket behavior or canonical program changed.
- Found two confounded semantic claims accepted by the old gate:
  non-singleton content was paired with a no-separator rival, and rectangular
  sizing with an all-quadrants rival.
- Added feature-specific rivals, honest generic witnesses, and direct surviving-
  competitor checks in `lesson_identifiable`.
- Added red/green regressions and a reusable matched-control probe under
  `workspace/`. See packet-level `REVIEW.md`, `DECISIONS.md`, and retained
  `checks/` evidence for exact commands and counts.

Imported associated notes retain original evidence/timestamps in
`evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `e603a3763bcdfd01d19d355a529a391b51112d9862466ef82b26b69a28db1c5a`.

# Decisions for `5d6fcce80b6a`

Final generator SHA-256: `e603a3763bcdfd01d19d355a529a391b51112d9862466ef82b26b69a28db1c5a`.
Canonical `RULE_HASH`: `652672c3e3c3` (unchanged).

## D1 — Preserve valid generation and deterministic versioning

**Prior choice.** Version `2.0.0` uses a four-slot semantic schedule—internal, leading, trailing, multiple—and scheduled palettes. Existing evidence showed broad structural validity and lesson coverage.

**Decision.** Do not change the valid sample stream, schedule, difficulty geometry, palette schedule, or version. The production defects were API-boundary acceptance and semantic-registry truthfulness, not scene generation.

**Alternatives rejected.** Bumping `VERSION` would reshuffle every deterministic sample despite no intended valid-output change. Reworking the schedule to make every arbitrary query rotation identifiable would change the supported fixed curriculum to satisfy a non-production permutation.

**Probe.** Final battery 12/12 green; ordered census 300/300 materialized with 0 ambiguity.

## D2 — Require exact scalar request controls

**Prior choice.** `gen_ctx` received values before an explicit task-local type boundary. Coercible values and Boolean integers could pass, and negative sample indices could select a schedule slot.

**Decision.** Add `_validate_call(seed, sample_index)` before generation. Both values must have exact type `int`; `sample_index` must be non-negative.

**Failure modes avoided.** Boolean scheduling, float/string coercion, negative modular schedule selection, and misleading API success for malformed requests.

**Evidence.** `checks/5d6fcce80b6a-tdd-red-strict-scalars.log` captured the failing-first behavior. The final strict defect lint is green in `checks/after-final/`.

## D3 — Correct the meaning of `CANONICAL_SHORTCUTS`

**Prior choice.** `green_every_blank_row` and `copy_input_to_all_four_quadrants` were labeled as canonical-fitting even though each contradicts labeled canonical pairs.

**Decision.** Remove only those two names from `CANONICAL_SHORTCUTS`. Keep both functions in `SEMANTIC_RIVALS` and `LESSON_COMPETITORS`, where they remain useful generated-lesson alternatives.

**Alternatives rejected.** Removing the rivals entirely would weaken lesson checks. Altering canonical labels or the Racket rule would be an unjustified authority change. Weakening the semantic gate would let false claims pass.

**Evidence.** The failing-first registry regression is `checks/5d6fcce80b6a-tdd-red-semantic-registry.log`; the intermediate failure is retained under `checks/after/`; final semantic gate is green under `checks/after-final/`.

## D4 — Keep the inherited fixture frozen; add separate focused tests

**Constraint.** `tests/test_generator_5d6fcce80b6a.py` is a packet-frozen fixture.

**Decision.** Restore it byte-for-byte after an early accidental append and put new scalar/registry tests in `tests/test_request_contract_5d6fcce80b6a.py`; put parametric tests in `tests/test_parametric_prototype_5d6fcce80b6a.py`.

**Evidence.** Frozen fixture SHA-256 is `48df2b1928a87f35751a94960f5dda52d73690ee35b38c5de84eb020de0f5029`. Combined source tests pass 34/34; portable task tests pass 33/33.

## D5 — Develop two small parameters in an isolated prototype

**Choice.** Add `copy_diagonal` (`main`/`anti`) and `separator_policy` (`through_last`/`strict_between`) under `workspace/parametric/`. Select both once per episode. Preserve `main + through_last` as the exact canonical/default setting.

**Why these parameters.** Each changes a meaningful rule operation while preserving the original 2×2 tiling, row classification, and copy structure. Their effects can be varied independently and demonstrated with existing semantic profiles.

**Alternatives rejected.** Palette-only changes are nuisance variation, not rule parameters. Pair-local parameter draws would make an episode inconsistent. Wiring variants into production would mix proposed and canonical authority.

**Probe.** Four retained episodes cover all parameter combinations. Racket/Python parity passed for every labeled pair. Holding the other parameter fixed, diagonal changes 52 cells and separator policy changes 24.

**Limit.** The prototype checks only four declared settings/seeds and declared witnesses. It is not approved training data and does not prove unique induction against undeclared rules.

## D6 — Retain fixed production ordering; report rotation failures honestly

**Measured result.** With four fixed demonstrations and one query, 300/300 lessons had no surviving declared rival. Rotating every one of 1,500 pairs into the query yielded 550 ambiguous rotations and 900 hook warnings.

**Decision.** Keep the supported fixed assembly and label arbitrary rotations unsupported. Do not reinterpret the overall census status as a production failure, and do not hide the rotation result.

**Reason.** Each scene profile carries a distinct causal witness. Holding out the sole instance of that profile can remove its witness from demonstrations. The downstream sampler does not claim arbitrary query placement.

**Evidence handling.** The full report is retained as `checks/lesson-census.json.gz`; `checks/lesson-census.summary.json` records original/compressed hashes, counts, and exact restoration instructions.

## D7 — Preserve honest solve boundaries

The blind solve was completed before any generator/rule inspection and records no prior exposure. The post-repair solve records earlier exposure `yes` and reference consultation `no`. Both stopped after one visible-example-passing revision; neither claims masked-query correctness.

## D8 — Leave peer-audit targets unchanged

The two drawn audits produced reproducible shortcut findings, but the assignment requires findings rather than repairs. No files under `repo/generators/e3f1bc75d654/` or `repo/generators/4993e4aad5e4/` were edited. Exact inputs, Racket receipts, rivals, source hashes, probes, and battery evidence are under `checks/audit/` and summarized in `AUDIT.md`.
