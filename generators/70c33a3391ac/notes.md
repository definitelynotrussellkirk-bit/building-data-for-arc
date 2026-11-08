# Current notes: 70c33a3391ac

## Intended rule and authority

Find every four-connected nonzero component, crop its complete colored bounding
box (including internal zeros), and return the one crop that occurs exactly
unchanged twice. Rotation, reflection, geometry-only equality, palette-only
equality, component size, position, and modal color are not equivalent. The
canonical Racket program is unchanged (`RULE_HASH = 4fc872f50360`); active
`target_code` copies were synchronized byte-for-byte to that authority while
archival `raw_code` was preserved.

## Current distribution

Version `3.1.0` retains one canonical-prior draw followed by two generalized
draws in each three-position schedule. Both ordinary generalized positions now
make all three declared canonical-compatible shortcuts prediction-changing:

- a nontrivial rotated/reflected exact-color decoy defeats D4 normalization;
- a same-mask recolor defeats geometry-only matching;
- shared palette and palette-confounding components defeat palette-only choice.

The duplicate crop is not first or last in component order in either generalized
position. Exact controls remain available for `n_components`,
`duplicate_rank`, and `duplicate_palette_relation`; combinations that cannot
preserve the canonical profile are explicitly declared incompatible rather than
silently ignored. Seed, sample index, difficulty, and axis values are strictly
type/domain checked.

## Resolved finding and evidence

`F-AUD-70-01` was valid for version 3.0.0: a D4-normalized rival fit all four
unique canonical pairs and 600/600 ordinary generated draws while failing a
lawful exact-orientation input. The final source SHA-256 is
`c46624014b3b8b0d28cb7283e814a70858a49b8f46f47abdf91cfda5e1377a60`.
The source-bound final census in `checks/shortcut-census.json` refutes every
declared rival on 1,200/1,200 generalized samples (400 per band, both ordinary
generalized slots). `checks/question/d4-counterexample.json` re-executes the
small retained orientation witness under the final source and current Racket
authority. The 300-lesson rotated-query census is in
`checks/lesson-census.json`.

## Executable semantic contract

`CANONICAL_SHORTCUTS`, `SEMANTIC_RIVALS`, `LESSON_COMPETITORS`,
`SEMANTIC_WITNESSES`, `WITNESS_RIVALS`, `strict_canonical_like`, and
`lesson_identifiable` now expose the intended distinctions to the shared gate
and future probes. Canonical-only demonstrations intentionally fail the lesson
hook; the ordinary three-pair production schedule passes because the two
generalized demonstrations make each named rival disagree.

## Proposed parametric extension

`workspace/parametric/` contains a separate, unapproved episode-level prototype
for `minimum_occurrences in {2,3}`. Setting 2 is the canonical Racket program
byte-for-byte; setting 3 changes only the count threshold. Each retained episode
contains one exact crop twice and another three times, keeps one setting fixed
across all pairs, and distinguishes both settings in every demonstration. See
`checks/parametric/report.json`. This prototype is not wired into production.

## Known limits

The declared rival set is finite and does not prove unique induction against all
possible rules. Canonical examples alone remain compatible with the three named
shortcuts; teaching support is supplied by the production schedule, not by
rewriting canonical data. The generalized sampler covers exact colored crops
with four-connected components on zero background; it does not claim support
for diagonal connectivity or nonzero backgrounds.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-7f28fe235b1f6ca3:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `0e0f9fbca4708e279beea980c372069679b6d1830381079f16abad79cb163a3e`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Explicitly resolve F-AUD-70-01 on c46624014b3b8b0d28cb7283e814a70858a49b8f46f47abdf91cfda5e1377a60: both ordinary generalized slots independently include an earlier nontrivial D4 transform, with prediction-changing rival checks. Reviewer reports 1200/1200 unique generalized draws refute D4, shape-only and palette-only rivals across all difficulties and both slots; 300 three-demo/query lessons and 1200 query rotations have zero declared-rival ambiguity. Added executable semantic contracts and strict controls; final 12/12 reported battery, 67 local/fresh focused tests. Two selected authority copies independently token-checked against unchanged canonical. Prior source and minimal Racket witness retained. Bounded declared-rival evidence only; no universal identifiability, owner battery rerun or prototype approval.

### Assessment or prior finding

## 70c33a3391ac

**Finding `F-AUD-70-01`: reproduced undeclared D4-invariance shortcut.**
Generator SHA-256:
`0e0f9fbca4708e279beea980c372069679b6d1830381079f16abad79cb163a3e`.
Canonical rule hash: `4fc872f50360`.

The generator's ordinary checks are strong: its completed battery is `10/12`
green. The failed stages are `semantic_gate` (no executable semantic contract)
and `authority_sync` diagnostic divergence, with execution parity still passing.
See
`checks/audit/70c33a3391ac/battery/checks/70c33a3391ac_after_battery_summary.json`.

The audited rival compares complete colored component crops modulo all rotations
and reflections, then returns the first component in the first repeated D4
class. Measured results:

- fits all `4/4` unique canonical pairs;
- fits `600/600` ordinary generated draws, using 200 draws per band with seeds
  `80000..80199`, `90000..90199`, and `100000..100199`;
- disagrees on a hand-made input that passes `self_check` and observes declared
  axes `canonical_prior=false`, `n_components=5`, `duplicate_rank=middle`, and
  `duplicate_palette_relation=shared`.

On that lawful input, the Racket authority returns the exact duplicated crop:

```text
1 1 2
1 2 0
```

The rival returns the earlier rotated distractor:

```text
1 1
2 1
0 2
```

Evidence and reproducer:

- `checks/audit/70c33a3391ac/input.json`
- `checks/audit/70c33a3391ac/racket.json`
- `checks/audit/70c33a3391ac/counterexample.json`
- `checks/audit/70c33a3391ac/probe.stdout.log`

The `600/600` fit is bounded sample evidence, not proof over all possible draws.
The single lawful disagreement is sufficient to show that exact orientation is
not currently made load-bearing by the sampled data. No audit-target file was
changed.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-7f28fe235b1f6ca3-v0001/audit_assets.json), manifest SHA-256 `ff6a2bbba5973f476925d795b6b3ce2a0f420a5ebf95194b42f496a70827fed4`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `c46624014b3b8b0d28cb7283e814a70858a49b8f46f47abdf91cfda5e1377a60`.

# Decisions for 70c33a3391ac

## D1 — Preserve the canonical rule; repair teaching evidence

**Prior state.** Version 3.0.0 generated correct labels, but a D4-normalized
crop rival fit all canonical pairs and 600/600 sampled draws. The rule itself
was not wrong.

**Decision.** Keep the canonical Racket semantics and `RULE_HASH` unchanged.
Repair only the generalized input distribution and expose executable rivals.

**Alternatives rejected.** Treating rotations/reflections as equivalent would
change the task. Merely documenting the shortcut would leave generated lessons
ambiguous. Replacing canonical pairs would break supplied-source authority.

**Probe.** `checks/question/d4-counterexample.json` gives a lawful exact input
where exact-orientation output is `[[1,1,2],[1,2,0]]` but the D4 rival returns
`[[1,1],[2,1],[0,2]]`. `checks/shortcut-census.json` binds the repair to the
final source.

## D2 — Make every ordinary generalized slot independently load-bearing

**Decision.** In both noncanonical schedule positions, construct a nontrivial
D4 transform of the target as an earlier decoy, a same-mask recolor, and
palette-confounding distractors. Validate actual rival predictions after
placement; do not count a cue that happens to be redundant.

**Rationale.** A complete lesson may rotate the query. Each generalized pair
must therefore carry the distinction itself rather than relying on one special
schedule position.

**Failure modes considered.** D4-symmetric targets cannot distinguish
orientation, so they are resampled. Tight canvases can merge components, so the
teaching scenes use additional separation. Duplicate-first/last order can teach
a positional shortcut, so both generalized slots reject those placements.

**Measured result.** 1,200/1,200 final generalized samples refuted all three
named rivals. The source-bound lesson census materialized 300 lessons / 1,200
pairs and found 0 ambiguous production lessons and 0 ambiguous rotations.

## D3 — Fail closed on invalid controls

**Prior state.** Boolean/float/string scalar requests were accepted in several
integer positions, and canonical-profile override conflicts were reported only
as unexplained rejections.

**Decision.** Validate literal integer types (excluding bool), nonnegative
sample indices, difficulty, all axis values, and unknown names before drawing.
Declare the minimal canonical-profile incompatibility patterns in
`INCOMPATIBLE_OVERRIDE_COMBINATIONS`.

**Alternatives rejected.** Coercing floats/strings hides caller errors. Silently
falling back from incompatible exact controls violates the advertised contract.

**Probe.** Portable task tests cover invalid scalars, every generalized exact
axis combination, and every rejected canonical tuple. The final override stage
passes.

## D4 — Synchronize active authority text without changing semantics

**Decision.** Use the repository's reviewed `authority-sync` proposal to update
only `racket_target.target_code` in the two selected solution records. Preserve
`raw_code` as archival input and leave the canonical program unchanged.

**Evidence.** `checks/authority-sync/proposal.json` is the exact hash-bound
proposal; `checks/authority-after/result.json` and the full after battery pass
both authority and rule-smoke checks.

## D5 — Add a bounded parametric prototype, separate from production

**Parameter.** `minimum_occurrences` with allowed values `{2,3}` and default 2.
The value is selected once per episode. Setting 2 materializes the canonical
program exactly; setting 3 changes `count > 1` to `count > 2`.

**Why suitable.** It preserves component extraction, exact colored-crop
equality, occurrence counting, and selection order while exposing a nearby
meaningful behavior. The retained grammar includes one pair, one triple, and
two unique distractors so every demonstration distinguishes the settings.

**Limitations.** The threshold-2 setting inherits the canonical reversed-scan
tie break when more than one crop class repeats. The evidence covers two bounded
settings at one retained seed, not all lawful scenes. The prototype remains
proposed and unapproved.

**Evidence.** `workspace/parametric/README.md`, `prototype.py`, `verify.py`, the
materialized Racket/episode artifacts, and `checks/parametric/report.json`.

## D6 — Retain reusable source-bound probes

`workspace/shortcut_census.py` discovers the generator's declared shortcut,
competitor, and witness maps rather than hard-coding rival names. It records
canonical fit, both ordinary generalized schedule slots, source/probe hashes,
unique-input counts, and first witnesses. This is review tooling, not a solver
or production dependency.
