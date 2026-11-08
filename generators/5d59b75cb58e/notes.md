# Working notes: 5d59b75cb58e

## Selected implementation

Version `3.0.0`; selected generator SHA-256
`12f0465e4fde83a6354d5b8c9aac3344a85337b86b86cc88a56eecd7680f5e5a`.
The canonical Racket rule was not changed; `RULE_HASH` remains
`2b970065d6a3`.

The intended transformation preserves a square zero-background grid and copies
every nonzero cell from `(row, column)` to `(column, row)`. Generated inputs use
two or three differently colored, 4-connected, off-diagonal blobs. Transpose
targets are empty, at least one blob is non-rectangular, and normal lessons use
three demonstrations followed by one query.

The three canonical demonstrations place every source below the main diagonal.
Consequently the strongest canonical-fit shortcut is `lower_only_add`: preserve
the input but transpose only lower-triangle sources. The selected generator
already counters this with the deterministic `lower`, `upper`, `both` source-side
schedule. The exact generated upper-only witness is retained in
`counterexamples/lower_only_shortcut.json`; its authoritative output was checked
with the canonical Racket rule.

## Repair in review-27ad3777a90f6d7f

The unresolved audit from `review-09078f3c08634910:v0001` was used as a lead,
not as current-source evidence. On the pinned baseline SHA-256
`7fb73fd337c36a1c896661140f1e3cba9e29f1eb1ea697cb5e489812491da2aa`,
`side=12.75`, `n_blobs=3.75`, and `blob_size=5.75` were silently truncated by the
legacy `draw_int` helper. Independent baseline probing also showed that
`sample_index=True`, `False`, `1.0`, `"1"`, and `-1` were accepted. The before
battery therefore had 11 green stages and one failed `defect_lint` stage.

The repair makes two bounded contract changes:

1. `seed` must be a Python `int` but not `bool`; `sample_index` must additionally
   be nonnegative. `schedule_profile` enforces the same sample-index contract.
2. Exact integer axes use `draw_int_strict`, so floats, strings, and booleans are
   rejected instead of coerced.

`VERSION` deliberately remains `3.0.0`: the change affects only invalid calls.
A 144-case comparison of default and legal override calls found zero output
mismatches between the pinned baseline and repaired source
(`checks/valid-parity/report.json`).

## Verification

- The focused task tests were written first and failed with 19 expected
  assertions against the baseline; all 19 pass after the repair.
- The completed after battery is 12/12 green with no advisory or failed stage.
- The standalone linter and selected portable task-test stage pass.
- A source-bound census materialized 100 lessons in each of easy, medium, and
  hard: 300 lessons, 1,200 labelled pairs, and 1,200 exact unique inputs. With
  three demonstrations and one query, all 300 production lessons and all 1,200
  hold-one-pair-out query rotations had zero declared-rival ambiguity, hook
  warning, or scoring error. In every band, `lower_only_add` was refuted in all
  100 lessons.
- The post-repair visible-only solve passed all three visible demonstrations on
  revision 1. Earlier rule exposure was declared; no reference was consulted
  during that solve. Masked query correctness remains withheld.

## Input choices and limits

- `side=8..12`, `n_blobs=2..3`, and generated `blob_size=3..5` are retained from
  the selected design. `self_check` also accepts lawful canonical blobs of size
  2, so the validator is intentionally broader than the sampler on that axis.
- Distinct nonzero colors, off-diagonal placement, empty transpose partners, and
  a non-rectangular blob make common palette, collision, and bounding-box
  shortcuts observable. They are a bounded teaching grammar, not the full
  mathematical domain of transpose-add.
- The source-side schedule is ordered and deterministic. The 300-lesson census
  also checked every query rotation within each materialized four-pair bundle,
  but did not enumerate all seeds or every imaginable rival program.
- No Racket authority, canonical row, or valid generation distribution changed.
  Catalog approval and training admission remain maintainer decisions.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-09078f3c08634910:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `7fb73fd337c36a1c896661140f1e3cba9e29f1eb1ea697cb5e489812491da2aa`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Accepted repair review-27ad3777a90f6d7f:v0001, exact source 12f0465e4fde83a6354d5b8c9aac3344a85337b86b86cc88a56eecd7680f5e5a, changes exact-axis override path to shared draw_int_strict before generation and validates common scalar calls. This addresses the named fractional truncation defect; 19 focused tests and 144 legal parity calls are reviewer-reported and not rerun by owner. Original source-bound audit/witness retained in current bounded assessment; not a claim of improved labels or training admission.

### Assessment or prior finding

## 5d59b75cb58e

**Finding: exact integer override controls silently accept and truncate fractional values beyond their advertised bounds.** Severity is low: this is a request-validation and exact-control defect, not an incorrect Racket label or an in-domain grid counterexample. No audit target or shared source was changed.

The selected generator advertises `side` as integer `8..12`, `n_blobs` as integer `2..3`, and `blob_size` as integer `3..5`. Its `_draw_int_axis` calls the legacy `ctx.draw_int`, whose implementation applies `int(ov)` before checking bounds. Consequently the following malformed overrides are accepted rather than rejected:

| Input index in `input.json` | Request, with other axes fixed | Observed exact axis | Validator |
| --- | --- | --- | --- |
| 36 | `side=12.75, n_blobs=2, blob_size=3, source_sides='upper'` | `side=12` | `self_check == []` |
| 37 | `side=8, n_blobs=3.75, blob_size=3, source_sides='upper'` | `n_blobs=3` | `self_check == []` |
| 38 | `side=8, n_blobs=2, blob_size=5.75, source_sides='upper'` | `blob_size=5` | `self_check == []` |

All three use `generate(seed=29051, sample_index=1, difficulty='medium', **overrides)`. **Documented-domain status:** every emitted grid satisfies the documented structural grid domain and passes the generator validator; every malformed request is outside the documented integer override domain and exceeds its axis's numerical upper bound. This does not show that a legal integer override is ignored. It shows that an illegal exact-axis request is silently transformed into a legal, different request. A caller can therefore mistake an impossible requested condition for a successfully controlled sample.

The existing shared helper `draw_int_strict` provides an opt-in way for a later generator repair to reject non-integer values. Alternatively validate these three overrides locally before calling their draw helper. This audit proposes that change without applying it.

**Source binding:** generator SHA-256 `7fb73fd337c36a1c896661140f1e3cba9e29f1eb1ea697cb5e489812491da2aa`; canonical rule hash `2b970065d6a3`. Full rule text and SHA-256, normalized rule SHA-256, and relevant helper/notes hashes are in `checks/audit/5d59b75cb58e/hashes.json`. There was no task-local `evidence/review_index.json`; the public catalog reported zero unresolved audits. Existing associated notes were used only as leads for the intentional bounded structural grammar and lower-only teaching shortcut, not as fresh pass evidence.

**Measured scope:** `repro.py prepare` materialized 39 inputs: all 24 joint extreme integer override combinations (`side` 8/12, `n_blobs` 2/3, `blob_size` 3/5, all three source directions) at one seed, three normal scheduled draws in each difficulty band, all three public canonical pairs, and the three malformed requests above. Every input passed `self_check`; the 24 legal overrides were exactly recoverable. All 39 outputs were executed through the supported canonical Racket apply command, with zero disagreements against independently implemented per-cell transpose-add and with the three canonical outputs preserved. Each default three-example lesson covered lower, upper and both source sides. Holding out each materialized pair once yielded nine two-demo/query checks with no declared rival fitting the demonstrations while disagreeing on the query. These are bounded checks, not proof of universal lesson identifiability or exhaustive generator coverage.

**Reproduction and evidence:** from `packet_root/WORK/repo`, run `PYTHONPATH=src:shared/runtime ../.venv/bin/python ../checks/audit/5d59b75cb58e/repro.py prepare`; from `packet_root`, run `python3 review.py run python3 -m arcpuzzles apply 5d59b75cb58e --input ../checks/audit/5d59b75cb58e/input.json --out ../checks/audit/5d59b75cb58e/racket.json`; then from `packet_root/WORK/repo`, run the first Python command with `verify` instead of `prepare`. An existing Racket output must be removed or a new output chosen for another apply run. Exact commands, launcher/effective working directories, exit codes and evidence paths are retained in `checks/audit/5d59b75cb58e/commands.json`. Materialized requests/observations are in `cases.json`, grids in `input.json`, authoritative outputs in `racket.json`, and the final measured result in `summary.json` under that folder. An initial verification script expected the wrong apply JSON field and failed with `KeyError: 'outputs'`; its log is retained separately, the parser was corrected to the public `results[].output` schema, and verification then passed. That scripting failure was not a generator or Racket failure.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-09078f3c08634910-v0001/audit_assets.json), manifest SHA-256 `3e2fbbfccc43fc86aa8af7aad6dbf9c312718157db82b313e3f9d95bec37c290`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `12f0465e4fde83a6354d5b8c9aac3344a85337b86b86cc88a56eecd7680f5e5a`.

# Decisions for 5d59b75cb58e

## D1 — Reject invalid common scalar controls

**Prior choice.** The selected baseline delegated `seed` and `sample_index` to
shared context construction without a task-local exact-type/nonnegative check.
The original rationale is not documented. In practice, booleans, floats, a
numeric string, and a negative sample index were accepted.

**Decision.** Require `type(seed) is int`; require `type(sample_index) is int`
and `sample_index >= 0`; enforce the sample-index rule in both `generate` and
`schedule_profile`.

**Alternatives considered.** Coercing with `int(...)` would preserve legacy
behavior but makes a malformed exact request look successful. Relying only on
`gen_ctx` would leave schedule indexing vulnerable before context construction.

**Probe and failure mode.** The RED task-test run produced 19 expected failures.
`checks/root-cause/strict-scalars-before.json` records five accepted invalid
sample indices. The repaired portable task tests reject all cases. This remains
request validation, not a claim that the previously emitted grids were unlawful.

## D2 — Use strict integer draws for exact axes

**Prior choice.** `_draw_int_axis` used `ctx.draw_int`. That helper converted an
override with `int(value)` before checking bounds, so `12.75`, `3.75`, and
`5.75` became legal but different requests for `side`, `n_blobs`, and
`blob_size`.

**Decision.** Use the existing shared `draw_int_strict` helper whenever an exact
integer override is supplied.

**Alternatives considered.** Three local type checks would work, but duplicate
the shared strict-control policy. Removing exact controls would avoid the bug at
the cost of useful, observable axes.

**Probe and limit.** The focused fixture is
`counterexamples/strict_scalar_controls.json`; task tests cover fractional,
float-integral, string, and boolean values. Legal output parity was separately
checked over 144 seeded default/override calls with zero mismatches. The test
matrix is representative rather than exhaustive over every Python object type.

## D3 — Keep version and valid generation stable

**Decision.** Retain `VERSION = "3.0.0"` and make no change to random draw order,
shape placement, colors, or the canonical rule.

**Why.** The defect is entirely outside the advertised valid-call domain. A
version bump would deliberately perturb every keyed sample even though no valid
semantic or distribution change was needed. The 144-case baseline comparison
supports, but cannot mathematically prove, stability over every valid seed.

**Failure mode considered.** Adding validation after any draw could alter or
partially consume state. Validation now happens before context construction and
before all draws.

## D4 — Preserve the lower/upper/both teaching schedule

**Input choice.** The baseline uses `side=8..12`, two or three colored blobs,
exact generated blob sizes 3..5, and a deterministic three-profile source-side
schedule: lower, upper, both. Colors are distinct and nonzero; transpose targets
are empty; at least one blob is non-rectangular.

**Original rationale.** The canonical demonstrations are lower-only, so a
lower-triangle-only transpose is a perfect canonical shortcut. Upper and mixed
examples expose the missing direction, while non-rectangular shapes refute
bounding-box filling. I found no evidence that changing these choices would
improve the bounded repair.

**Alternatives considered.** Randomly choosing source sides independently could
produce all-lower lessons. Forcing only mixed examples would refute the shortcut
but narrow the distribution and remove clear one-direction demonstrations.
Changing the Racket rule was rejected because authority checks and canonical
outputs were already coherent.

**Probe and limit.** `checks/lesson-census.json` covers 300 three-demo/one-query
lessons and every hold-one-pair-out rotation: zero declared-rival ambiguities.
This is an ordered finite curriculum with named rivals; it does not establish
universal induction or exhaust all seeds.

## D5 — Retain an exact shortcut witness and a reusable authoring probe

**Decision.** Add
`counterexamples/lower_only_shortcut.json` and
`workspace/build_shortcut_counterexample.py`. The script selects the source by
hash-aware `reviewer_support`, materializes a legal upper-only case, and writes a
rival comparison; the authoritative label is obtained separately through the
supported Racket `apply` command.

**Why.** A compact, replayable witness is more useful to future reviewers than a
prose-only shortcut claim. Keeping the Racket call separate avoids presenting a
Python mirror as output authority.

**Limit.** The helper targets the named canonical shortcut; it is not a general
program synthesizer or an exhaustive rival search.
