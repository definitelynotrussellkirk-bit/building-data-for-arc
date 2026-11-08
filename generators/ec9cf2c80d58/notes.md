# Current notes: ec9cf2c80d58

## Selected source and authority

The selected implementation is version **4.1.0**, generator SHA-256
`39cb6a9ff704cbc37689246fc0a7f2cd40a6b95de37ea6fb94fa20e8947413e9`.
The canonical Racket authority was not changed: `RULE_HASH = 899eb4e6a25d`.
Production labels continue to come from that Racket program. `rule_model` and
all rivals in `generator.py` are source-bound authoring and audit instruments,
not replacement label authority.

The intended rule reads every zero in the original grid, chooses its first
nonzero neighbor in UP/DOWN/LEFT/RIGHT order, and counts cells equal to that
color or zero over the complete original row and column. If the row count is at
least the column count, matching cells in the column are erased; otherwise
matching cells in the row are erased. Ties therefore clear columns, and all
hole decisions use the unedited input.

## Inherited baseline and review lead

This review started from version 4.0.0, generator SHA-256
`3bec7d4e76bcf5d481b86d66091253174eb2553cecb9b869bdf8853d8a149e87`.
The specific prior lead used was
`counterexamples/review-c8b4d6a0930468cd-v0001/retained/checks/audit/ec9cf2c80d58/finding.json`.
It reproduced a profile-gated rule that recognizes the old two-band teaching
template and otherwise erases perpendicular to the visible band orientation.
That rival fit three demonstrations at seed 2, indices 7–9, but disagreed on
query index 10 without ever comparing extents.

The baseline battery also found a separate call-contract defect: invalid
`seed` and `sample_index` scalar types, plus negative `sample_index`, were
accepted. The retained before run is `checks/before/result.json`; it finished
11/12 stages green and failed `defect_lint` with 30 strict-scalar warnings.

## Repair decisions

The canonical rule, ordinary sampler, canonical-profile anchors, public axes,
and eight-slot schedule were retained. The repair changes the carrier used by
odd teaching slots rather than changing labels or weakening the semantic gate.

The old teaching carrier had exactly two equal vertical bands, dimensions
`(m+1) x 2m`, and three holes. Version 4.1.0 instead chooses three to five
vertical bands. Two active bands have width `m = 6..9`; one to three additional
inactive bands have independently varied widths. The same three-hole extent
proof is placed inside the two active bands, with optional left/right
reflection. Thus the examples still jointly teach zero-inclusive extents,
original-grid decisions, and the column-on-tie branch, but the old recognizable
profile is no longer the only carrier.

`profile_template_gate` is now an explicit `CANONICAL_SHORTCUTS` and
`LESSON_COMPETITORS` member. It remains defined exactly as the retained audit
hypothesis: special-case the old template, otherwise use perpendicular erasure.
A focused regression at seed 2, indices 7–10, and an exhaustive task-local
rotation test require this rival and every other declared competitor to be
refuted by the demonstrations.

`generate` and `schedule_profile` now require actual Python integers for `seed`
and `sample_index`, reject bool/coerced scalars, reject negative
`sample_index`, and validate `difficulty`. Existing override validation remains
strict and observable.

## Lesson policy and measured scope

The default period remains eight:

| Residue | Profile |
|---:|---|
| 0 | canonical horizontal |
| 1 | teaching |
| 2 | general horizontal |
| 3 | teaching |
| 4 | canonical vertical |
| 5 | teaching |
| 6 | general vertical |
| 7 | teaching |

A materialized lesson has three demonstrations followed by one query. Any four
consecutive default slots contain two odd teaching slots, so holding out any one
pair leaves at least one teaching demonstration. Explicit overrides bypass this
profile schedule; no equivalent lesson guarantee is claimed for arbitrary
override-defined sequences.

The final strict battery in `checks/after-enumerated/` ran with required query
rotations and enumerated every declared start residue at seed 0. All 12 stages
passed. Its semantic gate measured 285/600 strict-canonical-like draws, 12/12
sampled lessons identifiable, 0/48 ambiguous rotations, and 24/24 fixed-seed
period lessons with 0/96 ambiguous rotations. The profile floor measured 19/60
exact profile hits and 21/60 envelope hits, with exact support in every band.

The larger source-bound census in `checks/lesson-census.json` sampled 100
lessons per difficulty, three demonstrations plus one query, and held out every
pair in turn. It materialized 300/300 lessons, 1,200 pairs, and 1,200 unique
inputs with zero materialization or scoring errors. Production ambiguity was
0/300 and rotated-query ambiguity was 0/1,200 against the finite declared rival
set. This does not prove uniqueness against undeclared programs or all seeds.

The first after battery is intentionally retained at `checks/after/`. It had
11/12 green stages and failed strict aggregation only because the declared
period had not been enumerated; its semantic smoke itself found 12/12
identifiable lessons and 0/48 ambiguous rotations. The strengthened fresh run
at `checks/after-enumerated/` supplied the required schedule enumeration rather
than hiding that warning.

## Parametric prototype

`workspace/parametric/` contains a separate proposed two-setting prototype.
Its episode-level `tie_policy` is selected once as either `column` (the exact
canonical default) or `row` (ties clear rows). It preserves the input grammar,
uses three demonstrations and four distinct hidden queries, and deliberately
emits a real tie in every pair so both demonstrations and queries distinguish
the chosen policy.

The reconciled public projection keeps the owner's privacy correction and uses
the current shared content-ID contract: policy, program text, source metadata,
and query labels stay private, while the exact visible bytes—including public
demonstration labels—determine each `challenge-<sha256>.json` name. The writer
emits those exact bytes, sorts the aggregate keys, and rejects duplicate visible
challenges. Both historical three-demo/one-query episode prefixes remain
byte-for-byte unchanged; three new queries are appended to each episode.

`checks/parametric-reconciled/summary.json` records live protected-Racket
execution for two complete episodes. Both programs matched their Python mirrors;
all 14 stored labels matched, and all six demonstrations plus all eight queries
distinguished the opposite setting. Program SHA-256 values are
`50c5529ccd94c80451ec4f6b7a71846f24c0aab41ec49eadee8e023f01d87dc7`
for the exact canonical column policy and
`effa77b1feaf65154c6b537daf06454e5d160b5a024c7bba01d034b9db6bbe1d`
for the proposed row policy. This remains bounded prototype evidence, not catalog
or training approval, and the production rule remains fixed.

## Focused verification and remaining limits

Portable task-local verification passed **74/74** tests in
`checks/task-tests-final/result.json`, including the production call
contract and lesson regressions plus exact visible-byte public identities,
duplicate export rejection, four distinct parametric queries, privacy masking,
and live execution of both parametric Racket programs.

The strongest canonical shortcut remains perpendicular-to-band erasure: it and
four other declared rivals fit all 10 labeled canonical entries. The exact tiny
counterexample is retained in `counterexamples/combined_minimal.json`; the
current generator emits scaled multi-band witnesses, not that 3x4 fixture.
Finite rival checks cannot establish universal induction, and the scheduled
teaching family remains deliberately structured. Future reviews should test
new shape-, color-rank-, or metadata-conditioned hybrids rather than treating
this finite pass as closure.

## Current owner source and evidence limits

Accept 4.0.0→4.1.0 production repair: odd-slot extent carriers use two active
bands among three to five total bands with independent widths, reflections, and
colors; the old profile-gated rival is explicit. Literal scalar guards reject
bools, coercions, and negative indices. Canonical Racket is unchanged. Prior
71-test and battery claims remain bound to their submitted bytes. The reconciled
prototype preserves reviewer tie-policy/Racket logic and owner privacy masking,
then adopts exact visible-byte public IDs and four queries per episode. Fresh
scope: 74/74 task tests, 14/14 live-Racket labels, eight distinguishing queries,
and unchanged historical four-pair prefixes. No production variant API or
training admission.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-c8b4d6a0930468cd:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `3bec7d4e76bcf5d481b86d66091253174eb2553cecb9b869bdf8853d8a149e87`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Resolve exact recognizable-profile-gated rival finding on accepted39cb6a9f/version4.1.0:old rival declared executable,odd-slot carrier teaches true extent among variable bands;new regression and300 lessons/1200 rotations plus24 period lessons/96 rotations reported clean. Canonical Racket unchanged. Exact prior source and witness preserved;bounded reported evidence,no owner battery rerun.

### Assessment or prior finding

## ec9cf2c80d58

**Suspected shortcut — reproduced as a default-lesson ambiguity.** Audited
generator SHA-256:
`3bec7d4e76bcf5d481b86d66091253174eb2553cecb9b869bdf8853d8a149e87`;
rule hash `899eb4e6a25d`.

A visible profile-template rival can recognize the generator's distinctive
teaching geometry (two equal vertical bands, `width = 2*(height-1)`, three
holes). On that profile it clears columns for holes sharing a row and clears a
row for the remaining hole. On every other profile it uses the canonical-fit
“erase perpendicular to the band orientation” shortcut. It never computes the
intended original-grid row/column extents.

For difficulty `easy`, seed `2`, sample indexes `7,8,9,10`, the first three
examples are `teaching`, `canonical_horizontal`, and `teaching`; the rival
matches all three authoritative outputs. The fourth example is
`general_horizontal`; the canonical Racket output differs from the rival. All
four inputs are unoverridden default draws and pass the target validator. The
generator's declared `lesson_identifiable` result is nevertheless empty because
this profile-gated rival is absent from its finite competitor set.

Evidence and replay:

- `checks/audit/ec9cf2c80d58/finding.json` — compact parameters, exact differing
  query, source/rule hashes, and `[true,true,true,false]` match vector.
- `checks/audit/ec9cf2c80d58/racket.json` — canonical Racket receipt for all four
  inputs.
- `checks/audit/ec9cf2c80d58/build_repro.py` and `finalize_repro.py` — reusable
  rival/replay tools.

No repair was made. A likely repair is to add this rival (or a generalized
profile-gated rival family) to the semantic contract and alter the ordinary
schedule so every three-demo rotation includes a non-template extent witness.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-c8b4d6a0930468cd-v0001/audit_assets.json), manifest SHA-256 `88a057ab2c0a39d6b3937762c3172191c26499b4831b772cd02ad1ae60466b43`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `39cb6a9ff704cbc37689246fc0a7f2cd40a6b95de37ea6fb94fa20e8947413e9`.

# Decisions for ec9cf2c80d58

## D1 — Keep the canonical Racket authority unchanged

**Prior choice:** v4.0.0 already bound production labels to `RULE_HASH
899eb4e6a25d` and used Python only for authoring checks.

**Decision:** preserve the Racket program and canonical ledger exactly.

**Reason and probe:** the reproduced failure was a curriculum shortcut, not a
wrong label. Final rule smoke and authority sync passed in
`checks/after-enumerated/`. Changing labels or making the Python mirror
production authority would have obscured the actual defect.

**Limit:** the Python mirror is still trusted only as a source-bound audit aid;
authoritative checks use the selected Racket execution.

## D2 — Vary the teaching carrier, not the extent proof

**Prior choice:** every odd slot used a conspicuous two-band `(m+1) x 2m`,
three-hole template.

**Decision:** retain the same tie/non-tie extent relationships but embed them in
three to five bands. Choose two active bands of width `m=6..9`; vary one to
three inactive bands, their widths, colors, active positions, coordinates, and
left/right reflection.

**Alternatives rejected:**

- Removing teaching slots would restore canonical shortcuts rather than teach
  the rule.
- Random hole placement alone would not guarantee a complete lesson refutes
  zero-excluding, sequential, tie-row, and perpendicular rivals.
- Changing the Racket rule to match the shortcut would be semantically wrong.
- Keeping the two-band carrier and merely changing its size would preserve the
  profile gate.

**Probe and failure mode:** the retained seed-2 lesson first demonstrates the
old gate; `test_retained_profile_shortcut_is_refuted_by_the_seed2_rotation` now
requires a refuting demonstration. The finite construction remains structured,
so new undeclared visual hybrids remain possible.

## D3 — Promote the retained shortcut into the executable contract

**Decision:** add `rival_profile_template_gate` to `CANONICAL_SHORTCUTS` and
therefore to `LESSON_COMPETITORS` and semantic witnesses.

**Reason:** a repair that changes examples but omits the known rival from future
checks can regress silently. The final semantic gate verifies that the rival
fits all 10 canonical labels yet is refuted by generated witnesses in all three
difficulty bands.

**Probe:** `checks/after-enumerated/checks/ec9cf2c80d58_after_semantic_gate.json`.

**Limit:** executable declarations are not an exhaustive hypothesis class.

## D4 — Enforce strict call scalars at the boundary

**Decision:** require `type(seed) is int`, `type(sample_index) is int`,
nonnegative `sample_index`, and an allowed difficulty before schedule or random
state is consulted.

**Reason:** the baseline defect lint reported 30 accepted invalid scalar calls
across easy/default/hard. Coercion would make replay identity ambiguous.

**Alternative rejected:** relying on downstream RNG errors; that produced
inconsistent acceptance and poor diagnostics.

**Evidence:** baseline failure in
`checks/before/checks/ec9cf2c80d58_before_defect_lint.log`; final defect lint
green and focused scalar regressions in `tests/test_contract.py`.

## D5 — Preserve the eight-slot schedule and require rotation evidence

**Decision:** keep residues 0/2/4/6 as canonical/general profiles and every odd
residue as teaching. Lessons are three consecutive demonstrations plus one
query; query rotation is supported for the default sampler.

**Reason:** every four-slot window contains two teaching positions, so every
single holdout leaves at least one refuting demonstration. This is stronger and
simpler than hoping a randomly rare witness appears.

**Probe:** task-local tests enumerate starts 0–7, four query positions, three
difficulties, and seeds 0–3. The source-bound fixed-seed census checked 24
lessons and 96 rotations; the broader census checked 300 lessons and 1,200
rotations.

**Limit:** explicit overrides bypass the schedule, and seed-0 period enumeration
does not prove all-seed behavior or undeclared-rival uniqueness.

## D6 — Retain the strict warning and run a stronger fresh battery

**Observed attempt:** `checks/after/` had 11 green stages; semantic smoke found
12/12 identifiable lessons and 0/48 ambiguous rotations but warned that the
declared period was not enumerated. Strict aggregation therefore failed.

**Decision:** preserve that result and run a new output with
`--require-rotations-identifiable --enumerate-schedule-period --schedule-seed 0`.

**Reason:** suppressing the warning or overwriting the prior directory would
lose useful process evidence. The strengthened run passed 12/12 stages.

## D7 — Build, but do not promote, a tie-policy parameter

**Decision:** place a separate prototype under `workspace/parametric/` with
`tie_policy in {column,row}` chosen once per episode. The default column setting
uses exact canonical text; row changes only the tie branch.

**Reason:** equality handling is a small meaningful rule parameter that
preserves object roles and the original extent-comparison reasoning. Every pair
can contain a tie, making the parameter learnable from demonstrations.

**Alternatives rejected:** varying whether zero counts toward extent or whether
updates are sequential changes more of the rule and creates harder coupled
validity/teaching questions. Per-hole policy selection would violate the
once-per-episode requirement.

**Evidence and limits:** `checks/parametric-reconciled/summary.json` records two
protected-Racket episodes, six distinguishing demonstrations, eight
distinguishing queries, and exact canonical public files. Historical four-pair
prefixes are unchanged. This is bounded prototype evidence, not production or
training approval.
