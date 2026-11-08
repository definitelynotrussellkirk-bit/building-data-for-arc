# Working notes: a4333a244e11

## 2026-10-07 review-f6a3e89bc699138e

No prior reviewer return was used as a repair lead; the selected baseline,
canonical row, before battery, and the retained passing example
`b90d4c3d5553` were inspected directly.

### Baseline findings

- The source prose said “exactly two” seeds, but generation sampled 2–4.
- `RULE_HASH` was absent.
- Public axes included dead/singleton controls, unknown overrides were accepted,
  dimensions were not exact, and many multi-axis requests failed without a
  declared incompatibility.
- Degenerate texture values were mixed into the ordinary domain.
- No executable semantic rival/witness or lesson-identifiability contract existed.
- Canonical examples all placed the lower numeric seed color at the earlier
  row-major seed position, leaving a canonical-fitting shortcut unrefuted.

### Selected repair

The generator now emits exactly two seeds, pins the canonical authority hash,
and advertises only six constructive exact axes. Private seed-position selection
cycles through candidate pools with a seed offset to avoid needless
with-replacement duplicates. Diagonal pools are filtered so their examples are
actual Manhattan-vs-Euclidean counterexamples.

The final four-profile schedule makes every three-demonstration rotation refute
five executable rivals: `ascending_position_colors`, `euclidean_nearest`,
`lower_color_wins_ties`, `ascending_colors_on_axis_aligned`, and
`lower_color_ties_on_axis_aligned`. A late self-review found that the first
repair schedule perfectly correlated axis-aligned cases with ascending colors
and no ties. A failing regression reproduced that conditional shortcut; the
schedule was changed to include two axis-aligned descending/tie-present profiles
and the two conditional rivals were added to the contract.

`self_check`, `strict_canonical_like`, `observe_overrides`, semantic witnesses,
rivals, and `lesson_identifiable` are executable. The task-local suite includes
canonical parity, all legal joint semantic-axis combinations in every band,
boundary controls, invalid controls, destructive mutations, every cyclic lesson
start and query rotation, global-random isolation, relocated-runtime support,
and real Racket parity.

### Final evidence

Final generator SHA-256:
`a895916472f9f6fef36efafb0fae0edf60f94f65675db17b6adea58bad5ebeb9`.
The final battery is 12/12 green; protected task tests are 192/192; the census
materialized 300 lessons and found 0 ambiguous production pairs or rotations
across 1,200 of each. The independent probe checked 1,000 generated inputs and
35 real-Racket applications with no validation, determinism, or parity failure.

### Limits

The declared-rival set is finite; passing it is not a proof of unique induction
against every possible hypothesis. Palette families are fixed pairs rather than
all 28 unordered color pairs, deliberately trading combinatorial breadth for
observable color-role counterexamples and exact override semantics. The fourth
profile carries most broad size variation; the first three preserve canonical
frame profiles. The deterministic default schedule does not exercise every
cross-product in a single four-pair lesson, although the exact override suite
constructs all 288 semantic cross-products per difficulty band. Canonical
archival authority text remains divergent from the selected authority, but
selected-source synchronization and execution parity pass; no authority file was
changed.
## Current reviewer considerations

Source SHA-256: `a895916472f9f6fef36efafb0fae0edf60f94f65675db17b6adea58bad5ebeb9`.

# Decisions: a4333a244e11

Final selected generator SHA-256:
`a895916472f9f6fef36efafb0fae0edf60f94f65675db17b6adea58bad5ebeb9`.
No prior reviewer return was used as a repair lead.

## D1 — Match the documented and canonical two-seed grammar

**Choice.** Generate exactly two distinct-colored seeds inside one inset color-8
frame.

**Original rationale.** Unknown. The baseline prose said exactly two, but the
implementation sampled 2–4; canonical inputs contain two.

**Alternatives considered.** Keep 2–4 seeds and generalize the wording/rule; add
a separate multi-seed curriculum family; preserve degenerate no-seed/single-seed
textures.

**Probe/result.** Canonical inspection and selected Racket parity support the
two-seed task. Multi-seed and degenerate textures were off-contract and caused
validator/override failures. Final rule smoke is 120/120 and canonical parity is
3/3.

**Failure modes/limits.** This deliberately removes noncanonical multi-seed
breadth. A future multi-seed task should be a separate generator/rule contract,
not an undocumented axis here.

## D2 — Advertise only six exact public axes

**Choice.** Keep `frame_h`, `frame_w`, `palette_kind`, `alignment`, `tie_mode`,
and `color_order`; reject all unknown or retired keys. Declare no incompatible
combinations because the constructor supports the full cross-product.

**Original rationale.** Unknown. Baseline metadata exposed singleton/dead controls
and dimensions whose requested values were not observed.

**Alternatives considered.** Mark dead controls diagnostic; retain broad labels
that only influence distributions; declare thousands of pairwise
incompatibilities.

**Probe/result.** The shared override gate ran 24,480 draws across 272 cases,
three bands, and 30 seeds per case with 0 findings. Task tests also enumerate all
48 semantic cross-products in each band and dimension boundaries.

**Failure modes/limits.** Exact controls constrain future implementation changes:
renaming or changing semantics requires updating the observer, metadata, and
regressions together.

## D3 — Preserve canonical profiles while broadening dimensions

**Choice.** Fix the first three cycle positions to canonical frame profiles
(5×9, 6×10, 7×11) and let the fourth draw broader sizes by difficulty.

**Original rationale.** Canonical profile support was weak in the baseline and
the profile floor was advisory.

**Alternatives considered.** Draw every size independently; use only canonical
sizes; make each profile broad.

**Probe/result.** Final profile floor: exact canonical profile 48/60, envelope
54/60, canonical inputs accepted 3/3. The independent probe observed every
advertised size value and many canvas shapes in every band.

**Failure modes/limits.** Most size breadth is concentrated in one cycle slot,
so individual three-demo windows do not have uniformly broad dimensions.

## D4 — Use four fixed palette families

**Choice.** Use canonical `(2,3)`, warm `(4,9)`, cool `(1,6)`, and varied `(5,7)`.
Together they cover every non-background/non-frame ARC color.

**Original rationale.** Baseline palette/texture controls were not exact and
included degenerate behavior.

**Alternatives considered.** All 28 unordered pairs from colors excluding 0/8;
fully random pairs; only canonical colors.

**Probe/result.** Palette values are directly observable and exact under every
joint override. Descending color-order profiles refute the numeric-position
shortcut that fits all canonical pairs.

**Failure modes/limits.** Four pairs provide less combinatorial variety than 28.
This is an intentional trade: exact role counterexamples and reliable lesson
composition are more valuable here than unstructured pair breadth.

## D5 — Three demonstrations from a four-profile cycle

**Choice.** Final cycle:

1. diagonal / tie present / descending;
2. diagonal / tie absent / ascending;
3. row / tie present / descending;
4. column / tie present / descending.

Any one pair can be the query; the other three are demonstrations.

**Original rationale.** Baseline had no executable lesson contract. The first
repair cycle covered three obvious rivals but correlated all axis-aligned cases
with ascending colors and no ties.

**Alternatives considered.** Ordered-only lessons; four demonstrations; random
profiles with resampling; the first repair cycle; larger five- or six-profile
cycles.

**Probe/result.** A test-first self-review reproduced two conditional wrong rules
on the first cycle. The final cycle gives at least two refuting axis-aligned
profiles, at least two Manhattan-vs-Euclidean diagonal profiles, three tie
profiles, and three descending profiles. Every cyclic start and every
three-of-four holdout passes task tests. The 300-lesson census reports 0/1,200
ambiguous production cases and 0/1,200 ambiguous rotations against five rivals.

**Failure modes/limits.** Four examples cannot refute every arbitrarily
conditional hypothesis. The schedule is justified against a declared finite
rival set, not as a proof of unique induction.

## D6 — Cycle private seed pairs instead of sampling with replacement

**Choice.** Enumerate lawful seed pairs per profile and select
`(seed + profile_occurrence) mod pool_size`.

**Original rationale.** Initial tests found duplicate draws in small fixed
profile pools; with-replacement sampling reduced lesson and probe diversity.

**Alternatives considered.** Retry duplicates; use global history; shuffle a
mutable pool; accept collisions.

**Probe/result.** The cycle is deterministic, stateless, and independent of
Python global RNG. It raised reliable coverage without cross-call state. Final
shared diversity is 74% unique inputs over 300 pairs; independent per-band
counts are 201/250, 195/250, 200/250, and 200/250.

**Failure modes/limits.** Finite fixed profiles still repeat after their pool
period; the method improves local coverage but does not guarantee global
uniqueness.

## D7 — Filter diagonal examples for real metric disagreement

**Choice.** A diagonal candidate enters the private pool only when Manhattan and
squared-Euclidean rivals produce different labelled grids.

**Original rationale.** Merely declaring a diagonal alignment does not guarantee
that a Euclidean rival is observationally different on a finite frame.

**Alternatives considered.** Count all diagonal examples as witnesses; generate
until a disagreement appears; remove the metric rival.

**Probe/result.** The semantic gate found `manhattan_not_euclidean` on 274/600
final draws and verified 60/60 sampled rival claims. Every lesson rotation has at
least one diagonal disagreement witness.

**Failure modes/limits.** Filtering changes the private positional distribution;
that selection is intentionally not advertised as a public axis.

## D8 — Make semantics executable

**Choice.** Add pure rivals, witnesses, `WITNESS_RIVALS`,
`CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, and `lesson_identifiable`.

**Original rationale.** Baseline semantic gate had no contract, so correct
individual labels did not establish teachable lessons.

**Alternatives considered.** Documentation-only claims; a single reference
mirror; rely only on the shared smoke sample.

**Probe/result.** Five witnesses fire; five rival claims verify; shared smoke is
12/12 with 0/48 ambiguous rotations; the source-bound 300-lesson census is clean.
The independent probe reimplements rather than imports the production mirror.

**Failure modes/limits.** All finite rival lists are incomplete. New plausible
shortcuts should be added test-first rather than treating current green evidence
as permanent proof.

## D9 — Strengthen validation without rejecting canonical metadata calls

**Choice.** Validate the frame/outer-margin/two-seed grammar and enforce requested
axis observability only when nonempty override metadata is supplied.

**Original rationale.** The first implementation accidentally interpreted
canonical `meta={}` as generated-axis metadata, rejecting lawful canonical
colors outside the four generated pairs.

**Alternatives considered.** Force canonical colors into generated palettes;
skip all metadata validation; special-case canonical grids by hash.

**Probe/result.** A regression reproduced the integration failure before the
narrow fix. Final `self_check(pair, meta={})` accepts all 3 canonical pairs, while
24,480 override draws remain exactly observed.

**Failure modes/limits.** External callers that pass misleading nonempty metadata
will receive an error; that is intentional contract enforcement.

## D10 — Keep Racket authority unchanged

**Choice.** Pin the selected canonical hash and change only the sampler,
validation, tests, and reviewer tools.

**Original rationale.** Selected Racket behavior already matched all canonical
pairs and the intended two-seed rule. The defect was generator/contract quality,
not label authority.

**Alternatives considered.** Rewrite the rule for multi-seed inputs; synchronize
archival bank text; replace Racket with Python labels.

**Probe/result.** Selected execution parity passes across distinct source texts;
120/120 rule-smoke mirror matches and 35/35 independent real-Racket probes pass.

**Failure modes/limits.** One archival source remains textually divergent. It is
outside the selected active authority and is reported rather than silently
rewritten.

## D11 — Post-repair solve record

**Choice.** Prepare a fresh medium lesson from final bytes, implement one
visible-example solution, and stop after 3/3 visible passes.

**Original rationale.** Required by the assignment as a usability/teaching
record, not as proof of masked correctness.

**Alternatives considered.** Manufacture a negative revision; consult prior
solution text; iterate despite no visible failure.

**Probe/result.** One honest revision passed all demonstrations. Earlier exposure
is recorded `yes`, reference consultation `no`, and masked-query correctness is
left for independent scoring.

**Failure modes/limits.** This is an exposed human work log, not a blind model
trace and not evidence of token-level behavior or hidden-query success.
