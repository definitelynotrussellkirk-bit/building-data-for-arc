## Current owner-accepted parametric family

The retained reviewed family is now accepted through `workspace/parametric/`.
`parametric/accepted.json` pins its exact current source and programs. The owner
rebased reviewer074 without replacing current production code; protected native
qualification covered both settings at seeds0/17, three demos and four queries,
and fresh owner acceptance replay passed. See `evidence/owner-prototype-rebase/`.
Canonical audits and training admission remain separate; earlier prototype
status below describes the source-bound reviewer handoff.

# Working notes: d38b0f2356c1

## Current repair — strict recipe identity boundary, 2026-10-24

Assignment `review-400900fb9684fbbd` resolves the retained scalar-contract audit
without changing version `2.1.0`, labels, schedule profiles, canonical data, or
Racket code. `generate` now rejects non-exact-integer seeds and non-exact or
negative sample indices before schedule lookup and `gen_ctx`; signed integer
seeds remain supported.

Current generator SHA-256:
`2b18e5165e31a51f4a9155078541d7a84b27f773971381aef7299fbc93581bef`.
Selected canonical rule hash remains `20d59edf7f3a`.

Evidence: 126/126 staged task tests passed; all tested boolean, float, string,
`None`, and negative-index requests reject at the public boundary; four fixed
valid calls are byte-identical to the pre-change grids; and 4/4 bounded canonical
Racket outputs match `_intended_output`. The contract tests now use the
portable `reviewer_support` canonical reader rather than fixed parent depth. See
`checks/final-verification-summary.json`,
`checks/scalar-boundary-after/result.json`, and
`checks/racket-parity/comparison.json`.

Remaining scope: the strict three-profile family and its documented semantic
limits are unchanged; this repair addresses recipe identity only.


Review assignment: `review-f488e46623fb0139`.

No prior associated review note or unintegrated return was present; the supplied
selected source and its before battery were the baseline. The original design
rationale is therefore unknown except where directly stated by code/metadata.

## Final review findings

- Baseline v1.1.1 lacked `RULE_HASH`, had a singleton separator-color axis,
  inert or unproven controls, dead difficulty bands, overlapping texture domains,
  no executable semantic contract, and selected-authority text divergence.
- All five canonical pairs have exactly four occupied cells in the clean block
  and five in every cyan block. Thus both “choose the sparsest block” and
  “choose the unique occupied-count outlier” fit every canonical pair without
  reading cyan.
- v2.1.0 exposes four exact pixel-observable controls, rejects unknown/invalid
  overrides, keeps every ordinary draw on the strict manifold, and uses a
  three-profile schedule: canonical density, sparser cyan distractors, and equal
  occupancy with a non-first clean block.
- The active base `target_code` was synchronized byte-for-byte to canonical
  `program_solution`; archival `raw_code` remains unchanged. Rule semantics did
  not change.
- The retained semantic probe enumerates executable declarations and reports
  finite sample evidence only; it does not claim universal induction.
## Current reviewer considerations

Source SHA-256: `ed0473c8a5872873ad3268da8640a840ba697dd69c2cd491f0c31ea430b6254b`.

# Distribution and repair decisions — d38b0f2356c1

Assignment: `review-f488e46623fb0139`. No prior associated note or unintegrated
return was available, so original rationales are marked unknown unless the
baseline source directly stated them.

## D1 — replace advisory metadata with an executable strict contract

**Original behavior.** The v1.1.1 generator described a fixed lattice but omitted
`RULE_HASH`, advertised a singleton `sep_color`, accepted unknown overrides, and
contained controls whose effects/provenance were not demonstrated. Original
rationale: unknown.

**Decision.** Pin `RULE_HASH=20d59edf7f3a`; expose only four exact constructive
axes (`clean_block`, `template_cells`, `distractor_noise`, `cyan_count`); validate
type/range/unknown keys before generation; recover every axis from returned
pixels; and make `self_check` enforce 11×11 geometry, gray separators, one
nonempty no-cyan block, no interior gray, and uniform legal distractor counts.

**Rejected alternative.** Keep diagnostic/singleton axes and mark them exempt.
That would preserve metadata volume without producing observable control.

**Limit.** This remains a deliberately strict family: all eight distractors in
one input share cyan/noise counts. It is not an exhaustive enumerator of every
lawful puzzle with a unique no-cyan block.

## D2 — retain a canonical floor while making difficulty real

**Original behavior.** The before defect lint found dead difficulty bands and
texture/domain overlap. Original rationale: unknown.

**Decision.** Keep a `canonical_density` profile (clean occupancy 4; distractor
occupancy 5) once per three samples, so each band has a canonical-size/palette
floor. Difficulty changes pattern phase, palette choices, and the scheduled
counts in adversarial profiles. Colors 5 and 8 are excluded from ordinary
non-marker palettes.

**Rejected alternative.** Random weighting over a broad domain. The first
implementation tried this and tests showed that a required witness could be
missed; scheduled defaults give a checkable lesson guarantee while exact
overrides still cover every legal value.

**Limit.** The three-step schedule is intentionally predictable. Sample indices
are not puzzle pixels, but downstream lesson assemblers should preserve or
explicitly replace this schedule rather than assume IID draws.

## D3 — schedule two different count counterexamples

**Canonical accident.** Every canonical clean block has four occupied cells and
every distractor has five. This admits both “choose sparsest” and “choose the
unique occupied-count outlier.”

**Decision.** Use three profiles:

1. `canonical_density` preserves the published density relation;
2. `sparser_cyan_distractor` makes cyan blocks strictly sparser than the clean
   block, refuting “choose sparsest”;
3. `equal_occupancy` gives all nine blocks the same occupied count and schedules
   the clean block away from index 0, refuting both occupancy-only rivals.

Every three consecutive samples contain all three profiles. Easy/medium/hard
equal-occupancy counts are respectively 3/5/8 cells per block.

**Rejected alternative.** Only reverse the density ordering. A final shortcut
self-review measured that the unique-count rival still survived 91/100 easy,
80/100 medium, and 99/100 hard three-demo lessons, so the intermediate all-green
v2.0.0 result was retained as evidence and then superseded.

**Failure mode.** Exact user overrides can intentionally remove a scheduled
witness (for example `clean_block=0`); semantic lesson guarantees apply to the
default sampler, while override correctness is checked separately.

## D4 — executable semantic declarations and independent task-local tooling

**Decision.** Add Python intended and rival functions, canonical shortcut
bindings, witness-to-rival mappings, strict/canonical predicates, and
`lesson_identifiable`. Add 116 focused tests and retain
`workspace/semantic_probe.py`, which enumerates the declarations rather than a
copied rival list. The final probe checks 100 lessons per band, all cyclic starts,
deterministic replay, self-checking, distinct inputs, canonical fit, and rival
disagreements.

**Rejected alternative.** Rely on the repository's small semantic-gate smoke
sample alone. It is useful as a gate but does not satisfy the required 100
lessons per band or document actual sampler coverage.

**Limit.** The probe covers declared rivals and a finite deterministic schedule;
it is not a proof that no other shortcut exists or that a learner will infer the
rule.

## D5 — preserve the selected rule and synchronize authority text

**Observed behavior.** Before repair, canonical `program_solution` and active
base `target_code` were whitespace/comment-normalized equivalent and execution
parity passed, but exact selected text had two groups.

**Decision.** Copy canonical text exactly into active `target_code`, preserve
archival `raw_code`, and pin its normalized hash. No Racket behavior or canonical
output changed. Final authority status is selected-synchronized with one archival
divergence and execution parity pass.

**Rejected alternative.** Rewrite or simplify the Racket rule. There was no
semantic defect to justify source churn.

## D6 — output semantics are macro-expansion, not literal tiling

The initial Python review oracle mistakenly tiled the selected 3×3 block into all
nine regions. Canonical tests failed immediately. Reading the authoritative rule
and outputs showed that source cell `(i,j)` is instead expanded to a solid 3×3
region at macro-position `(i,j)`. The failing iteration is retained in
`checks/tdd-green-attempt1.log`; canonical parity tests prevent recurrence.

## D7 — stopping condition

Stop after the final source passes 116 focused tests, all twelve after-battery
stages, the 300-lesson semantic probe, canonical Racket execution on the exact
shortcut witness, a final solve episode bound to identical generator bytes, and
a fresh-extraction patch replay. Remaining limits are distribution scope and
unmodeled rival rules, not known blockers.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/d38b0f2356c1/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-24c37bc1b0e2c645:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `ed0473c8a5872873ad3268da8640a840ba697dd69c2cd491f0c31ea430b6254b`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Accepted review-400900fb9684fbbd exact scalar guards at generate and schedule_profile reject bool/float/string/negative indices before coercion.126task tests reported; source2b18e5165e31a51f4a9155078541d7a84b27f773971381aef7299fbc93581bef. No owner battery run.

### Assessment or prior finding

## d38b0f2356c1

**Source binding:**
`ed0473c8a5872873ad3268da8640a840ba697dd69c2cd491f0c31ea430b6254b`.

**Reproduced defect — invalid public scalar requests are accepted.**  The
strict audit stage accepts `sample_index=-1` and reports it as
`accepted_invalid_scalar`.  The source-bound targeted probe additionally shows
that `seed=True`, `seed=1.25`, `seed="1"`, and `sample_index=True` all return
grids that pass `self_check`.  The clearest contract counterexample is:

```python
gen.generate(123, -1, difficulty="hard")
```

It returns an 11×11 grid rather than rejecting the negative index.  This can
alias or distort schedule semantics and lets invalid recipe identities produce
apparently valid training rows.

**What was checked.** Portable task tests passed 116/116; declared fractional
overrides `clean_block=4.75` and `template_cells=4.75` are correctly rejected;
invalid difficulty is correctly rejected.  Thus this is a boundary-coverage gap,
not evidence that the task labels are wrong.

**Evidence:**

- `checks/audit/d38b0f2356c1-defect-lint/result.json`
- `checks/audit/d38b0f2356c1/strict-scalar-probe.json`
- `checks/audit/d38b0f2356c1-task-tests/result.json`

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-24c37bc1b0e2c645-v0001/audit_assets.json), manifest SHA-256 `8d170af6f57f17c340eff3f5cb160c9a944e4c3a0fc47fdf9676c638eb6e7b5b`.
<!-- arcpuzzles-current-audit-assessment:end -->

## Current parametric review — review-074a25e1be19297f

Built a proposed `marker_color` family under `workspace/parametric/`. The
canonical setting `8` preserves the selected Racket program byte-for-byte; the
alternate setting `9` changes only which marker absence identifies the 3×3
source template. Inputs are matched across settings and contain distinct unique
no-8 and no-9 blocks, so demonstrations rather than input confounds identify the
rule. The source task's macro-expansion and fixed 11×11 lattice remain intact.

Original reviewer-reported evidence covers both settings with three demonstrations and four
protected-Racket-labelled queries, demo counts 2–6, public/private projection,
query-prefix stability, ambiguity rejection, atomic export and tamper rejection.
The bounded sampler pass exercised 60 episodes / 480 labelled pairs across six
seeds and all supported demo counts without a finding. Evidence is bound by
`workspace/parametric/evidence/reviewer-original/manifest.json`; broader claims are not implied.

Current status: **prototype only**. The production generator and canonical
Racket authority are unchanged; `variant_approved=false` and
`training_admitted=false`. The next useful action is independent semantic review
followed by the repository's explicit parametric qualification/acceptance path.
Exact 30×30 stress is not lawful for this fixed 11×11 lattice grammar.
