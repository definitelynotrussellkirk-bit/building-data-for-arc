# Review notes — 48a4d72eb621

Assignment `review-7c04f2d3430413da`; selected version `2.0.0`.
Final generator SHA-256: `2dc04df6cd1959f6a918dc08df14a57ec37c50d7af402d99fe0bad18634f4161`.
Canonical rule hash: `ea16ba808d09`; the Racket authority was not changed.

## Intended rule and domain

Count every nonzero input cell, discard spatial position, sort the complete color
multiset numerically, and return it as one row. The sampler emits a 5..12 by
6..12 zero-background canvas with 2..5 colors from the full ARC palette 1..9.
Each selected color occurs 1..3 times, and marker cells are orthogonally isolated
so object geometry does not introduce a second task.

## Reversed baseline decisions

Version `1.2.0` advertised nine controls, including aliases and pseudo-axes that
were not independently observable. It sampled only three or four colors, omitted
color 5 entirely, capped every count at two, rejected two canonical inputs, and
accepted or ignored invalid controls. Difficulty did not change the sampled
population. It had no pinned `RULE_HASH` or executable semantic lesson contract.

Version `2.0.0` replaces that interface rather than preserving misleading aliases:

- exact controls are only `grid_h`, `grid_w`, and `n_colors`;
- every declared boundary is legal and observable in every difficulty band;
- invalid seed, sample index, difficulty, key, type, and range values fail loudly;
- the full nonzero palette 1..9, two-color cases, and multiplicity three are lawful;
- easy/medium/hard reweight profile and count distributions without changing the
  legal override domain;
- canonical-profile-biased defaults retain broad support and accept all five
  canonical inputs.

The reason for reversal is measured, not stylistic. The completed before battery
failed lint, self-check, defect lint, profile floor, and overrides. In particular,
canonical count-three and two-color inputs were rejected. The completed after
battery has all 12 stages green and is bound to the final generator hash above.

## Teaching schedule and semantic contract

Four consecutive sample indices form the teaching unit. Color 5 appears in three
of every four positions; a count-three witness appears in three of every four
positions, on a different omitted residue. Duplicate counts and row-major
nonsorted placement occur in every sample. Therefore, after any one pair is held
out as query, at least two demonstrations remain for both sparse branches.

Executable rivals are:

- `cap_two`: preserve colors but cap each multiplicity at two;
- `drop_five`: silently omit color 5;
- `distinct_only`: output one instance of each color;
- `row_major`: preserve scan order instead of sorting.

Task-local tests check every query rotation over eight consecutive starts in all
three bands. The strict semantic gate checked 12 source-bound lessons with
required rotations. The larger census materialized 300 lessons (100 per band),
1,200 pairs, and 1,200 query rotations: zero ambiguity, zero materialization or
scoring errors, and 1,200 unique inputs against the declared rivals.

A minimized lawful counterexample retained at
`counterexamples/all-rivals-minimal.json` simultaneously exercises two colors,
color 5, and count three and disagrees with all four rivals. The portable task
suite covers it.

## Verification summary

- Before battery: 6 green, 1 advisory, 5 failed of 12; generator SHA-256
  `e8f0cfb51cb8f77a41de71227df890e3adfe4dd07f84e6fbfcd0d2eda4094928`.
- After battery: 12/12 green with required rotation identifiability.
- Profile floor: all 5 canonical inputs accepted; exact-profile hits 20/60 and
  envelope hits 24/60, with exact support in every band.
- Semantic census: 600/600 generated draws valid; strict-canonical-like rate
  241/600 (40.17%), above the declared 15% floor.
- Final portable task tests: 14/14 passed.
- Post-repair visible-only solve: 3/3 visible examples in one revision; earlier
  rule exposure declared `yes`, reference consultation during solve `no`.

## Known limits and open questions

The sampler intentionally does not cover one-color inputs, more than five colors,
counts above three, nonzero connected shapes, or background-as-data variants.
Those cases are outside the documented generator domain, not established rule
impossibilities. The semantic contract is finite: passing four named rivals does
not prove unique induction against every computable hypothesis. The large census
samples production lessons and rotations but does not enumerate every seed.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-eb01b8c7cb621e3d:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `e8f0cfb51cb8f77a41de71227df890e3adfe4dd07f84e6fbfcd0d2eda4094928`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Accepted source SHA 2dc04df6cd1959f6a918dc08df14a57ec37c50d7af402d99fe0bad18634f4161 replaces misleading controls with three observable axes and restores color 5, count 3 and two-color canonical cases. tests/test_generator.py and counterexamples/all-rivals-minimal.json accompany reviewer-reported 5/5 canonical acceptance and 14 portable tests. Explicitly resolve the prior override/canonical-domain findings; no maintainer rerun.

### Assessment or prior finding

## 48a4d72eb621

**Reproduced defects; findings-only audit, no source changes.** Version 1.2.0,
generator SHA-256 `e8f0cfb51cb8f77a41de71227df890e3adfe4dd07f84e6fbfcd0d2eda4094928`.
Supported Racket apply records rule-text SHA-256
`ed0bfa7ed21d1a0ffc0368b18057532954697f15931ee923a2c6a9cd58999c3a`
and executed rule hash `ea16ba808d09`. The receipt separately preserves the
exact canonical `program_solution` string hash.

**A48-1 — Exact controls do not implement the advertised contract.** At seed 0,
sample index 0, difficulty `medium`, each of `n_colors=5`, `palette_size=5`, and
`n_distinct_colors=5` silently returns the same baseline grid with only three
non-background colors (1 occurs twice; 8 and 9 occur once). All three outputs
pass `self_check`; actual Racket output is `[[1,1,8,9]]`. All three axes advertise
valid values 3–5, but `generate` independently executes `rng.randint(3, 4)` and
never reads these overrides. Four further exact-control probes fail despite
being advertised valid: `grid_h=5`, `grid_h=12`, `grid_w=6`, and `grid_w=12` each
raise `ValueError` because medium draw bounds are 6–8 by 7–9. Thus this finite
audit reproduced three ignored and four rejected controls in seven calls.

**A48-2 — The generator and validator exclude taught canonical branches.**
Normal generation uses 3–4 colors, 1–2 cells per color, and a palette that omits
color 5. Of all five canonical pairs, two inputs fail `self_check`: training
index 2 contains three 4s, and training index 3 contains only colors 2 and 6.
The supported Racket labels match all five canonical outputs. Two explicit
rivals demonstrate the missing teaching cases:

| Canonical witness (zero-based) | Self-check/domain status | Actual Racket output | Rival output |
|---|---|---|---|
| Train 2: cap each color at two occurrences | Rejected: color 4 occurs three times; outside declared count invariants, inside canonical task domain | `[[1,4,4,4,9]]` | `[[1,4,4,9]]` |
| Train 1: discard color 5 | Accepted; satisfies declared invariants, but color 5 is absent from normal generation | `[[3,5,5,8]]` | `[[3,8]]` |

Both rivals agree with every normal generated input by inspection of the
source restrictions; the measured baseline also confirms agreement. Each
rival fits 4/5 canonical pairs, so these are **untaught canonical branches**,
not claims of canonical-fitting shortcuts. Degenerate texture overrides are
excluded from this normal-generation statement.

Evidence: [receipt.json](checks/audit/48a4d72eb621/receipt.json) contains exact
inputs, actual labels, both rival outputs, validator/domain results, seed/index/
overrides, hashes and command arrays with working directories and exit codes.
[racket.json](checks/audit/48a4d72eb621/racket.json) is the unmodified supported
apply receipt. Reproducer: `python3 run_with_racket.py python3
../checks/audit/48a4d72eb621/probe.py`, followed from packet root by
`python3 run_with_racket.py python3 -m arcpuzzles apply 48a4d72eb621 --input
../checks/audit/48a4d72eb621/input.json --out
../checks/audit/48a4d72eb621/racket.json` (both exit 0). Scope: five canonical
pairs plus one generated baseline, six unique input grids, and seven exact-
control calls; no battery or lesson census. Generator hash was rechecked after
the probes; no Racket authority change or solve/private-solve inspection.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-eb01b8c7cb621e3d-v0001/audit_assets.json), manifest SHA-256 `b93ce6c45d2a66263b230dda33c21028f5872329cbfeb04b06f6bd25c234f2ab`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `2dc04df6cd1959f6a918dc08df14a57ec37c50d7af402d99fe0bad18634f4161`.

# Decisions — 48a4d72eb621

Final generator version `2.0.0`; SHA-256
`2dc04df6cd1959f6a918dc08df14a57ec37c50d7af402d99fe0bad18634f4161`.
The canonical Racket authority remained unchanged at rule hash `ea16ba808d09`.

## D1 — Preserve the Racket rule

**Choice.** Keep the authoritative rule unchanged and pin its hash.

**Original rationale.** Unknown. The selected baseline did not pin `RULE_HASH`,
but canonical outputs and rule smoke agreed with the written multiset-sort rule.

**Alternatives considered.** Reimplementing output production in Python or
changing the rule to match the baseline's restricted 3–4-color/count≤2 domain.
Both were rejected: the defects were in sampling, validation, and teaching, not
canonical labels.

**Probe.** Before and after rule smoke, Racket lint, and authority sync all pass;
the after battery reports the same authority set.

**Failure mode / limit.** Behavior outside the documented sampler domain is still
defined by the Racket rule, not by the Python diagnostic rivals.

## D2 — Replace nine nominal controls with three exact controls

**Choice.** Advertise only `grid_h`, `grid_w`, and `n_colors`, each exact and
recoverable from returned pixels.

**Original rationale.** Version 1.2.0 exposed `palette_kind`, `palette_size`,
`position_bias`, `n_distinct_colors`, `density`, and `texture`, apparently to
increase apparent combinatorial variety. Several were aliases, single-token
pseudo-axes, or ignored values; the exact historical intent is otherwise unknown.

**Alternatives considered.** Preserve aliases for compatibility; mark all weak
axes diagnostic; or add exact palette/count-vector controls. Aliases would keep
the contract misleading, while exact palettes/count vectors would overfit a
small task and greatly enlarge joint override testing. The smallest observable
surface was selected.

**Probe.** Final task tests exercise a joint boundary request in every band and
bad keys/types/ranges. The override stage finishes with no findings or warnings.

**Failure mode / limit.** Individual palette members and per-color multiplicities
are intentionally stochastic, not externally controllable.

## D3 — Match the canonical support instead of the baseline restriction

**Choice.** Permit 2..5 colors from 1..9 and multiplicities 1..3.

**Original rationale.** The baseline chose 3..4 colors, excluded color 5, and
used counts 1..2. No evidence explained those exclusions; they appear inherited
from generic sampler assumptions.

**Alternatives considered.** Add only the two rejected canonical cases as special
fixtures; widen counts but retain the palette gap; or allow arbitrary counts up
to canvas capacity. Special cases would not improve ordinary lessons, retaining
the palette gap would preserve `drop_five`, and unbounded counts would move far
from canonical evidence. The narrow canonical envelope plus modest extrapolation
was chosen.

**Probe.** All five canonical inputs pass `self_check`. The profile floor has
20/60 exact and 24/60 envelope hits, with exact support in every band. The
retained minimal counterexample exercises two colors, color 5, and count three.

**Failure mode / limit.** Counts above three and more than five colors remain
outside the documented domain.

## D4 — Bias toward coherent canonical profiles

**Choice.** Draw a coherent `(height, width, n_colors)` anchor from the five
canonical profiles, then give each axis heavy weight around that anchor while
retaining every declared boundary.

**Original rationale.** Baseline dimensions were drawn from broad hard-coded
bands independently, which produced some exact hits but did not make the input
validator canonical-complete.

**Alternatives considered.** Literal replay of canonical dimensions only;
independent uniform axes; or a single fixed canonical profile. Literal/fixed
sampling would reduce variety and risk memorization, while independent uniform
sampling gives weak exact support. Profile-biased broad sampling balances both.

**Probe.** The profile-floor table reports exact support 8/20 easy, 8/20 medium,
and 4/20 hard; no band is unsupported and no draw crashes.

**Failure mode / limit.** The generator reproduces profile statistics, not exact
canonical pixel layouts.

## D5 — Make difficulty change population, not legality

**Choice.** Easy uses more canonical anchors and mostly singleton nonrequired
counts; medium uses mixed counts/profiles; hard uses more broad anchors and
higher nonrequired multiplicities. Overrides keep the same legal domain.

**Original rationale.** The baseline accepted a `difficulty` argument but the
three bands produced identical samples.

**Alternatives considered.** Band-specific legal bounds or no difficulty effect.
Band-specific bounds were rejected because an exact override should not change
meaning by band; no effect is a dead contract.

**Probe.** A test compares 24 matched seed/index triples and requires at least one
population difference while every result stays lawful. Defect lint, which had
reported a dead-band warning, is green after the change.

**Failure mode / limit.** Difficulty is distributional, not a guarantee that an
individual hard sample is harder than every easy sample.

## D6 — Validate all call scalars before constructing context

**Choice.** Require nonnegative exact integers for `seed` and `sample_index`, and
`None|easy|medium|hard` for difficulty; reject booleans, floats, strings, negative
indices, unknown axes, and invalid override values.

**Original rationale.** Baseline relied on downstream behavior and accepted many
invalid scalar forms. The rationale is unknown.

**Alternatives considered.** Coerce strings/floats to integers or let `gen_ctx`
normalize them. Coercion hides caller defects and creates collisions, so strict
failure was selected.

**Probe.** Seven parameterized invalid-call regressions failed before the patch
and pass now. Final defect lint has no blocking warnings.

**Failure mode / limit.** The code does not impose an arbitrary upper bound on
valid nonnegative integer seeds or indices.

## D7 — Schedule semantic witnesses over four positions

**Choice.** Use sample-index residue modulo four: color 5 is present except
residue 3, and a count-three witness is present except residue 2. Every sample
has duplicates and deliberately nonsorted row-major order.

**Original rationale.** Baseline examples were independently sampled and had no
lesson-level teaching contract.

**Alternatives considered.** Independent witness probabilities; one dedicated
counterexample followed by ordinary samples; or more demonstrations. Independent
sampling can omit a branch from a complete lesson, one dedicated witness is lost
when held out as query, and a longer lesson spends unnecessary tokens. A 3-of-4
schedule guarantees redundancy with three demonstrations.

**Probe.** Task tests inspect eight starts in each band and every query rotation.
The semantic gate requires rotations. The 300-lesson census finds 0 production
ambiguities and 0/1,200 ambiguous rotations against declared rivals.

**Failure mode / limit.** Downstream assembly must preserve four consecutive
sample indices or provide equivalent witness coverage; arbitrary subsampling can
break the guarantee.

## D8 — Declare four concrete rivals and witnesses

**Choice.** Test `cap_two`, `drop_five`, `distinct_only`, and `row_major` with
executable witness predicates and source-bound authoritative labels.

**Original rationale.** No prior semantic contract existed. These rivals were
selected because each corresponds to a specific baseline restriction or a
simple transformation shortcut.

**Alternatives considered.** A large open-ended rule search, only natural-language
warnings, or no rival declaration. Full hypothesis search is not tractable;
prose cannot be checked; no declaration lets correct labels form ambiguous
lessons. The small high-value set was chosen.

**Probe.** The semantic gate checks each witness claim; all checked witness/rival
pairs disagree with authority as promised. The large census has no hook or
scoring errors.

**Failure mode / limit.** This is finite falsification. Undeclared hypotheses can
still survive, as the two audit findings on other tasks demonstrate.

## D9 — Preserve spatial neutrality

**Choice.** Place markers on one checkerboard parity so they are orthogonally
isolated, randomize value placement, and swap endpoints if row-major values happen
to be sorted.

**Original rationale.** Baseline used isolated marker placement, likely to avoid
object-shape semantics; exact intent is not recorded.

**Alternatives considered.** Allow connected same-color objects; encode counts as
shape; or use deterministic positions. Connected objects introduce segmentation,
shape encoding creates a second rule, and fixed positions encourage positional
shortcuts. Spatially neutral random markers were retained.

**Probe.** `self_check` independently enforces orthogonal isolation. The
`sorting_matters` witness fires on every sampled lesson in task-local tests.

**Failure mode / limit.** The sampler does not teach that connected occurrences
would also be counted by the Racket rule.

## D10 — Retain one minimized all-rival counterexample

**Choice.** Store a hand-minimized 5×6 lawful grid in
`counterexamples/all-rivals-minimal.json` and load it in the portable task suite.

**Original rationale.** No task-local counterexample fixture existed.

**Alternatives considered.** Rely only on large generated logs or copy a canonical
input. Large logs are slow to understand; copying canonical data would not isolate
all four rivals in one case. The minimized fixture is easier for future agents.

**Probe.** The test first failed because the fixture was absent, then passes after
adding it. Final suite: 14/14.

**Failure mode / limit.** One fixture proves only those four exact rival
predictions; the production census remains necessary for lesson-level coverage.
