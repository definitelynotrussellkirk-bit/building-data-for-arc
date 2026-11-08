# Working notes: 089c14df9952

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## 2026-09-28 review — assignment `review-8f1884f12a6bc9b2`

### Defect found

The original generator used homogeneous scene-level cue policies:

- every `hint` target carried red;
- every `plain` target was unhinted;
- every `clip` target was unhinted.

Therefore the rival `scene_uniform_hint_policy` fit all 8 canonical pairs and all 600 pinned ordinary draws: *if any target has red, solve only red-hinted targets; otherwise solve all targets*. The original semantic contract had ten witnesses, but every witness was reported weak because no `SEMANTIC_RIVALS` or `WITNESS_RIVALS` were declared.

### Distribution change

Multi-target `clip` scenes now contain one unhinted clipped target and redundant red hints on the other interior targets. This preserves the intended rule while forcing target-local reasoning. On the pinned 600-draw semantic census, the new `mixed_target_cues` witness fires 151 times and refutes the scene-level cue rival on all 151.

The default schedule is now named by `SCHEDULE_PROFILES` / `schedule_profile`:

1. `hint-2`
2. `plain-1`
3. `clip-mixed-3`
4. `hint-3`

### Semantic contract

Added public, executable declarations for:

- `SEMANTIC_RIVALS`
- `CANONICAL_SHORTCUTS`
- `LESSON_COMPETITORS`
- `WITNESS_RIVALS`
- `BRANCH_WITNESSES`

Three declared shortcuts reproduce all canonical pairs and are now tied to generated counterexample witnesses: `hinted_targets_only`, `scene_uniform_hint_policy`, and `skip_clipped_targets`.

### Runtime repair

The required baseline battery was killed by the outer 330-second cap while the 21,690-draw override stage was finishing. Correctness evidence existed, but the parent battery could not reach its final four stages. The generator hot path was repaired without changing output semantics:

- normalize each D4 orientation once;
- memoize structural analysis by immutable grid content;
- reuse the successful generation analysis for axis observation;
- represent candidate placements by lightweight anchors and materialize only candidates actually examined.

A reproducible 324-case boundary benchmark improved from a 1.600 s median on the frozen baseline to 0.423 s on version 4.1.0. The final battery completed all 12 stages green; override accepted all 21,690 draws across 241 cases.

### Exact shortcut fixture

`workspace/scene_uniform_hint_policy_counterexample.json` records the exact seed, input, intended output, rival output, target facts, and differing cells used in `QUESTION_ANSWER.md`. The focused regression test regenerates the same case rather than trusting the fixture blindly.

### Rule authority

No Racket change was made. Canonical parity, Racket lint, grammar, and authority-sync all pass on the final source.
## Current reviewer considerations

Source SHA-256: `029aff1e3ba3c7cc48e45ef32d24dd3e4bbe466549b2b75b91538cfb863e4041`.

# Decisions for `089c14df9952`

## D1 / R1 — enforce strict scalar types at the selected generator boundary

**Decision.** Validate exact integer `seed` and `sample_index` values in
`generate`, reject negative sample indices, and replace `_scheduled_int` calls to
`draw_int` with `draw_int_strict`.

**Why.** The baseline battery isolated one defect: 93 warnings for accepted
booleans, strings, and fractional floats. The public API should reject these
values rather than silently map them onto another requested sample or override.
The selected generator already depends on a shared strict helper, so the smallest
source-bound repair is local.

**Alternatives rejected.** Changing shared `GenerationContext.draw_int` would
alter unrelated generators. Manually checking only `target_count` would leave
`grid_h`, `grid_w`, seed, and sample-index coercion. Rounding or truncating floats
would preserve the defect rather than make the contract falsifiable.

**Probe and failure mode.** `tests/test_strict_scalar_contract.py` failed 21/21
on the baseline and passes 21/21 on the final source. The test intentionally does
not widen accepted input types to NumPy integer scalars; the contract is exact
built-in integers, excluding bool.

## D2 / R1 — keep version, distribution, and Racket authority unchanged

**Decision.** Leave `VERSION = "4.1.0"`, the schedule, all valid-output logic, and
the canonical Racket row unchanged.

**Why.** `VERSION` contributes to deterministic random seeding. A version bump
would rewrite the valid sample stream even though the repair only rejects inputs
that were invalid by the intended strict contract. The final 12-stage battery,
profile counts, override matrix, Racket lint, rule smoke, and authority sync show
that no semantic change was required.

**Alternatives rejected.** Bumping to 4.1.1 was considered but would create a
large unrelated distribution delta. Editing the Racket source was unjustified;
rule hash `1fa4f01a8b99` already matches all canonical pairs and generated lawful
inputs.

## D3 / P1 — parameterize target eligibility, not geometry or palette

**Decision.** Prototype one hidden episode-level parameter,
`target_policy ∈ {all, hinted_only}`, with `all` as the original/default value.

**Why.** This is a small semantic axis that preserves the family’s core
reasoning. Both settings still require base discovery, D4 shape matching,
red-hint orientation handling, transformed accent stamping, and clipping. The
only changed question is whether an otherwise matching unhinted target is
eligible. The existing mixed-cue clip scene gives a clean distinguishing witness.

**Alternatives rejected.** Palette permutation would change color roles rather
than the rule. Varying accent count or skeleton size changes input complexity but
not the transformation. A “skip clipped targets” parameter would entangle the
hidden rule with boundary placement and risks parameter-dependent input support.
An orientation-policy parameter could make red decorative or create ambiguous
labels. Adding both target eligibility and clipping as parameters was rejected as
unnecessary two-axis complexity.

## D4 / P1 — choose the parameter once per episode and keep inputs independent

**Decision.** Derive one setting from the episode seed, hold it fixed for all
three demonstrations and the query, and use the same four deterministic input
fixtures under either setting.

**Why.** Per-example switching would no longer be a learnable episode rule.
Parameter-independent inputs prevent leakage through shape, placement, or branch
frequency. Every fixture separates the two outputs, so any three demonstrations
identify the setting against the declared alternative.

**Probe and limits.** Seeds 0 and 1 cover both settings. Retained evidence records
zero parameter ambiguities, but it covers only two declared settings and four
fixtures; it is not a production distribution or proof against arbitrary rivals.
The prototype is therefore labelled proposed/unapproved and kept outside the
selected canonical execution path.

## D5 / L1 — preserve ordered production assembly; report rotation failure

**Decision.** Do not alter the existing schedule in this return. Report ordered
production and arbitrary query-rotation verdicts separately.

**Why.** All 300 sampled production lessons with four ordered demonstrations and
one query refute the declared rivals. The rotation diagnostic intentionally
changes the support set and exposed 229/1,500 ambiguities when the only clip
witness becomes the query. Fixing arbitrary rotation would require a curriculum
or schedule redesign—likely two independent clip witnesses in every five-pair
window—not a scalar-contract repair. Such a change would alter distribution and
should be evaluated as a separate decision if downstream assembly truly rotates
queries.

**Limit.** Production-order success does not authorize query rotation. The exact
first witness is retained in `checks/lesson-census-rotation-witness.json`.

## D6 / T1 — do not rewrite the frozen inherited test

**Decision.** Leave `tests/test_generator_089c14df9952.py` byte-for-byte frozen.

**Why.** The assignment explicitly assigns migration of inherited fixtures to
the library maintainer. Its legacy `scripts.canonical_profile_gate` import and
fixed `parents[...]` path fail portable preflight. Rewriting it locally would hide
rather than document the portability defect and violate the packet contract.

**Alternative.** New tests use public `reviewer_support` helpers and run
portably. The official aggregate stage remains accurately reported as blocked;
32/32 new tests are reported independently, not promoted to an aggregate pass.

## D7 / Q1 — retain the scene-level shortcut as the strongest canonical rival

**Decision.** Continue to name `scene_uniform_hint_policy` as the strongest
plausible canonical-fitting rival.

**Why.** It uses a simple scene-level correlation—if any target has red, process
only red targets; otherwise process all—and exactly matches all 8 canonical
pairs. The current generator deliberately emits mixed-cue clip scenes that break
it. Seed 4201/sample 2 is reproducible on the final source and the authoritative
Racket output differs from the rival in four cells.

**Alternative.** `hinted_targets_only` and `skip_clipped_targets` also fit 8/8
canonical pairs, but the scene-uniform rule combines the strongest observed
canonical correlation with plausible local behavior in plain scenes.

## D8 / A1–A2 — audit only; do not patch other tasks

The two drawn audit generators were kept unchanged. For `2f889ed81450`, concrete
source-bound failures and an exact counterexample were retained. For
`ebe355c22d70`, tests, semantic gate, and an exhaustive finite schedule/rival
probe found no issue; that conclusion is explicitly limited to the declared 16
profiles and eight rivals.

## D9 — compress only the oversized complete census

The 40,990,694-byte full lesson report exceeded the return’s expanded evidence
budget. It was losslessly gzip-compressed with deterministic metadata. The
original and compressed SHA-256 values, sizes, and restoration command are in
`checks/lesson-census-final.restore.json`; the compact summary and exact witness
remain directly readable.
