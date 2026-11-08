# Working notes: 7515881f2786

## Current intended rule

The input is an 8..14 by 8..14 grid containing only background 0 and 4..8 cyan (8) anchors. On every row and column, join consecutive anchors by recoloring intervening zero cells to 8. A line with three anchors therefore fills both adjacent gaps; the outer pair is not a separate direct pair because the middle anchor blocks it. Every ordinary generated scene contains at least one positive-length horizontal bridge and one positive-length vertical bridge. Additional anchors use otherwise-unused rows and columns, so they remain isolated distractors.

## 2026-10-21 parametric review — production unchanged

The selected generator and canonical authority were intentionally left unchanged.
The current 12-stage baseline was already green, so this review added a separate,
proposed episode-level extension at `workspace/parametric/` rather than rewriting
a safe production distribution. The prior integrated return
`review-49e273671a31e21e` and the current source-bound audit assessment were used
as leads; their claims were rechecked against this packet's selected bytes.

The prototype chooses `bridge_axes` once per complete episode with values
`both`, `horizontal`, or `vertical`. `both` is byte-for-byte the canonical
program and keeps `RULE_HASH=7327f2eb0272`; the alternatives disable exactly
one canonical axis branch while preserving colors, anchor roles, consecutive-
pair blocking, zero-only painting, and source anchors. Existing production inputs
guarantee at least one positive horizontal and vertical bridge in every pair, so
each of four demonstrations refutes both rivals before the query.

Focused tests and `workspace/parametric/verify.py` execute all selected/rival
programs through bundled Racket. Retained evidence is
`checks/parametric/verification.json`; it records 45/45 Racket/Python exact
checks, 24/24 training rival disagreements, 6/6 query rival disagreements, and
nine SHA-256-bound private/public artifacts under
`workspace/parametric/materialized/`. Public challenges omit the setting, Racket
source, sampling metadata, and query outputs. This is proposed finite evidence,
not production integration, variant approval, or proof against undeclared rivals.

## Reversed schedule decision

Version 3.0 used the fixed `sample_index % 4` order `shared_l`, `disjoint`, `multi`, `chain`. The prior rationale was to ensure that four consecutive examples covered all four profiles. That did cover the branch set, but it also leaked the profile from sample-index position and left only one chain witness: holding that pair out as the query allowed the canonical-fitting shortcut “connect only lines with exactly two anchors” to survive all demonstrations.

Version 3.1 instead derives a deterministic permutation from `(task_id, seed)` of the five-slot multiset `shared_l, disjoint, multi, chain, chain`. Every seed-specific cycle contains all profiles and two chain witnesses. Any five labelled pairs therefore leave at least one chain in the four demonstrations under every query rotation, while profile-at-position varies across seeds. The code intentionally does not declare `LESSON_SCHEDULE_PERIOD`; evidence is finite over sampled seeds and starts, not an exhaustive all-seed proof.

## Distribution and controls

- `grid_h` and `grid_w` retain every integer in 8..14. The default choice list weights 10 so the canonical 10×10 shape has reliable support without deleting larger/smaller lawful grids.
- `n_dots` remains 4..8 and difficulty-aware. Every profile is constructive at every advertised boundary.
- `profile` remains exactly one of `shared_l`, `disjoint`, `multi`, or `chain`; an explicit override takes precedence over the curriculum schedule.
- `seed` and `sample_index` must be exact integers, Booleans are rejected, and `sample_index` must be nonnegative. Integer/string overrides are checked by exact type; unknown controls fail loudly.
- The palette is intentionally fixed to 0 and 8 because color is semantic here; adding decorative colors would change the task rather than improve diversity.

## Semantic teaching contract

The strongest identified canonical-fitting rival is `exactly_two_anchors_per_line`: fill a row or column only when it contains exactly two anchors, ignoring lines with three or more. It matches all four usable canonical pairs. The `three_anchor_line` witness and chain profile force disagreement. The exact generated counterexample is retained at `counterexamples/exactly_two_anchors_per_line/counterexample.json`; canonical Racket evidence is `checks/7515881f2786-shortcut-racket.json`. Focused tests verify canonical fit, witness disagreement, and every tested production/rotation window.

## Authority decision

The transformation itself was not changed. The selected `racket_target.target_code` was synchronized byte-for-byte to the canonical `program_solution` through the authority-sync proposal/apply path. The historical executable `raw_code` remains preserved and execution-equivalent. Final authority checks report exact selected sync and parity across all canonical pairs.

## Evidence and limits

The final battery is 12/12 green. Its semantic gate accepted 600/600 strict draws, all 4 canonical inputs, fired the chain witness 232/600 times, found 12/12 four-demo lessons identifiable, and found 0/60 ambiguous diagnostic rotations. A larger census materialized 300 lessons (100 per band), 1,500 labelled pairs and all 1,500 leave-one-out rotations with zero ambiguity against the declared rival; it found 1,498 unique exact inputs. This is strong finite evidence against named and bounded generic rivals, not proof of unique induction against every possible hypothesis.

Open limitation: the five-slot property is proved by the schedule construction and exercised by focused tests over multiple seeds/starts, but the public census does not exhaust all possible seed-keyed permutations or all undeclared rivals. Training admission remains unchanged.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-d95f82861019d7d9:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `979f52f0522e419cf3d4b4f5c7a09a27e12dda2e7cbcbf35f42d2350187c4386`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Accepted source SHA 3c68cdea3477c299b1060ff2f1d6babf1b59ca2a55807fa1ddcfcabc7a6d126d replaces fixed sample-index profile order with seed-keyed five-slot schedule. tests/test_generator_7515881f2786.py and review-49e273671a31e21e report multi-seed schedule diversity and rotation-safe chain witnesses. This explicitly resolves the original positional-leakage finding on reviewer-reported evidence; no maintainer rerun.

### Assessment or prior finding

## 7515881f2786

Possible positional shortcut: profile selection is completely determined by `sample_index % 4`, independent of the seed. A direct probe gives

`shared_l, disjoint, multi, chain, shared_l, disjoint, multi, chain`

for sample indices 0 through 7 under the same seed. The standard worker requests sequential sample indices, so a four-pair episode exposes each profile in a fixed cyclic order and pair position predicts the scene family. This does not make labels wrong, but it creates avoidable metadata/order leakage and can let a learner specialize by demonstration/test position rather than infer the profile from the grid. Shuffle the four-profile schedule with an episode-keyed permutation, or sample profiles keyed by seed while enforcing batch-level coverage outside the single-example generator.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `3c68cdea3477c299b1060ff2f1d6babf1b59ca2a55807fa1ddcfcabc7a6d126d`.

# Decisions for 7515881f2786

## D1 — Preserve the authoritative transformation

**Decision.** Keep the rule “join consecutive same-row/same-column cyan anchors” unchanged.

**Why.** Canonical pairs, the Python mirror and both Racket source spellings already agreed. The defects were sampling, teaching metadata, scalar validation and selected-source text drift, not rule behavior.

**Alternatives rejected.** Adding colors, changing anchor semantics, or composing another operation would create a different task. Replacing the rule to silence generic diversity flags was specifically rejected because the 0/8 palette is semantic.

**Probe/limit.** Rule smoke applied 120 generated inputs without crashes, identity, mutation or out-of-bounds output. This is finite execution evidence, not universal semantic proof.

## D2 — Replace the fixed four-profile order

**Prior choice.** Version 3.0 used `sample_index % 4` to force one of each profile in every aligned four-example block. Associated note `GNOTE-001537` records that rationale.

**Problem.** The profile was predictable from position. A four-demo-plus-query bundle also contains five labelled pairs; if its only chain pair becomes the query, the four demonstrations no longer refute the canonical-fitting “exactly two anchors per line” shortcut.

**Decision.** Use a seed-keyed permutation of `shared_l, disjoint, multi, chain, chain`. The second chain is deliberate redundancy: any one held-out pair leaves a chain witness in the demos. Seed keying varies profile-at-position while preserving deterministic replay.

**Alternatives rejected.** (a) Pure random independent profiles can omit a witness; (b) a fixed five-cycle solves rotation safety but retains global positional leakage; (c) six or more slots add complexity without improving the four-demo leave-one-out guarantee; (d) forcing every example to be a chain would narrow the topology distribution.

**Probe/limit.** Focused tests enumerate every held-out position over many seeds/starts and observe at least eight schedule orders. The large census checks 1,500 rotations. No `LESSON_SCHEDULE_PERIOD` is declared, so no claim of exhaustive all-seed period coverage is made.

## D3 — Name the strongest canonical-fitting shortcut

**Decision.** Declare `exactly_two_anchors_per_line`: connect a line only when it contains exactly two anchors; ignore lines containing three or more.

**Why.** It is simple, visually plausible and fits all four usable canonical pairs because none contains a three-anchor line. It differs exactly on the branch the chain profile was intended to teach.

**Implementation.** The rival is shared across `SEMANTIC_RIVALS`, `CANONICAL_SHORTCUTS` and `LESSON_COMPETITORS`; `three_anchor_line` is its witness; `lesson_identifiable` rejects a lesson when the rival survives demonstrations and changes the query.

**Probe/limit.** The exact generated disagreement is source-bound in `counterexamples/exactly_two_anchors_per_line/counterexample.json` and independently labelled by canonical Racket in `checks/7515881f2786-shortcut-racket.json`. Other undeclared rivals may still exist.

## D4 — Weight canonical dimensions instead of narrowing the domain

**Decision.** Keep all dimensions 8..14 but give 10 additional mass in the default choice tuple.

**Why.** The baseline exact-profile floor was 2/60, with no medium/hard support. Canonical 10×10 lessons need to remain represented, but exact overrides and ordinary diversity should still reach the full documented domain.

**Alternatives rejected.** (a) Always 10×10 would pass the floor by deleting size diversity; (b) an ad hoc per-band hard pin would couple shape to difficulty and create a new shortcut; (c) lowering the floor would hide the missing-support defect.

**Probe/limit.** After repair, exact hits were 5/20 easy, 13/20 medium and 14/20 hard (32/60 pooled). Boundary/cross-product tests exercise 8 and 14 explicitly.

## D5 — Strict scalar validation at the generator boundary

**Decision.** Reject coercible-but-invalid public values before calling draw helpers: Boolean, float and string seeds/indices and exact numeric overrides; negative indices; non-string profile; unknown axes and unsupported difficulty.

**Why.** The baseline linter recorded 87 accepted-invalid-scalar warnings. Exact controls should mean exact type and value, not Python coercion.

**Alternative rejected.** Relying on downstream helpers produced inconsistent acceptance and made metadata claims unreliable.

**Probe.** Focused invalid-control tests and the after defect-lint stage both pass with zero warnings.

## D6 — Keep isolated distractors

**Decision.** Extra anchors occupy unused rows and unused columns.

**Why.** This preserves `n_dots=4..8` support without accidentally creating untracked bridges or changing the requested profile. It retains the rationale from associated note `GNOTE-001538`.

**Alternative rejected.** Unconstrained random anchors can silently add row/column pairs and invalidate profile observability.

## D7 — Synchronize selected authority text, preserve archival source

**Decision.** Copy canonical `program_solution` into selected `racket_target.target_code` through authority-sync; do not rewrite `raw_code`.

**Why.** The selected source is required to be byte-exact canonical. The archival spelling is historically valid and execution-equivalent, so destroying it would lose provenance without improving behavior.

**Probe.** Final authority sync reports one selected exact group and execution parity for both source spellings on all canonical pairs.

## D8 — Stop the post-repair solve after one passing revision

**Decision.** Finish after the visible-only solver passed all four demonstrations using the row/column bridge hypothesis.

**Why.** Further revisions would not receive masked-query feedback and could only overfit. Earlier rule exposure was declared `yes`; reference consultation during the solve was declared `no`.

## D9 — Report finite evidence honestly

**Decision.** Use “no ambiguity found” rather than “uniquely identifiable.”

**Why.** The semantic gate and 300-lesson census test declared rivals plus bounded generic mutations. They do not quantify every possible hypothesis, every seed-keyed permutation, or semantic equivalence class.

## 2026-10-25 native parametric return

The retained `bridge_axes` prototype was promoted to a bounded native adapter
without changing production `generator.py`. `both` is byte-exact canonical;
`horizontal` and `vertical` consume axis-specific ordered consecutive-anchor
pair lists before zero-only painting. The setting-neutral sampler supports 2–6
demonstrations and four sequentially projected queries, including a substantive
30×30 boundary case with both exact-two lines and three-anchor chains. A finite
nine-policy audit, native qualification and protected-Racket skip-intermediate
witness are the current review evidence. Owner acceptance and training
admission remain pending.
