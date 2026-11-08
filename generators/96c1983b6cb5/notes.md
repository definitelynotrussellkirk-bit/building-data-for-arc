# Working notes: 96c1983b6cb5

## Baseline findings

The selected 3.0.1 generator had five independent defects:

1. It did not declare `RULE_HASH`, so the Python sampler was not pinned to the
   selected canonical Racket authority.
2. `self_check` assumed source color 2 and target color 3. It rejected two of
   the three canonical pairs, whose roles are 4/5 and 6/7.
3. The public axes advertised palette and texture controls that `generate`
   ignored. The override contract therefore could not observe or honor them.
4. The normal transform sampler omitted identity even though the authority's
   domain is all eight D4 transforms.
5. The generator had no executable semantic-rival contract. In particular, a
   solver that only knows the three transforms exposed by the canonical pairs
   fits all canonical demonstrations but is wrong on five lawful transforms.

The before battery was interrupted during its expensive override stage. Its
retained checkpoints independently reproduced the missing rule pin, canonical
self-check rejection, dead axes/degenerate overlap, canonical-profile failure,
and missing semantic contract. The interrupted aggregate is not reported as a
completed battery pass or fail.

## Prior-return lead

I used the accepted repair for sibling task `53de1fcb2e13` as a design lead
because its canonical Racket rule has the same normalized hash
`9c8ca59a982a`. I did not copy its domain verbatim: this task retains the
canonical 3x3 profile and uses panel sizes 3–5, 3–6 foreground cells, and its
own five source/target palette pairs. An independent task-local oracle checks
all transform, validation, and Racket-parity claims without importing generator
helpers.

## Repair

Version 4.0.0 declares exactly five observable axes: `panel_n`, `transform`,
`a_cells`, `c_cells`, and `palette_id`. Every Cartesian combination is lawful.
A shared analyzer validates exact separator placement, palette roles, cell
counts, D4 asymmetry, and a unique A-to-B transform; it powers `self_check`,
`strict_canonical_like`, `observe_overrides`, and `reference_output` so those
surfaces cannot silently disagree.

The transform schedule `(1, 0, 4, 2, 6, 3, 5, 7)` has no three-element cyclic
window wholly inside canonical transform set `{1,4,6}`. Consequently every
three-demonstration default lesson contains a noncanonical transform and
falsifies the declared rival `canonical_transform_subset_only`, regardless of
schedule start. A/C shapes are each fully D4-asymmetric and C is outside A's
D4 orbit, so transforms are both uniquely inferable and visible in the query.

## Tests and probes

The task-local test was written before the production replacement and produced
38 expected failures against 3.0.1. It now has 41 passing tests, including all
eight transform codes, exact overrides, invalid-call rejection, canonical
profiles, shortcut counterexamples, every cyclic three-demo start, RNG
independence, and real Racket parity.

`workspace/reference_probe.py` is an independent executable oracle. On the
final generator it checked 140 samples per difficulty band (420 unique inputs):
zero self-check errors, zero nondeterminism, all panel sizes/transforms/palettes
in every band, 264 declared-rival counterexamples, and 51/51 real Racket output
matches. Counts and source hashes are retained under `checks/reference-probe.*`.

## Limits

The semantic contract tests one strong, named rival; it does not prove unique
induction against every imaginable program. The task is a single D4 operation,
not multi-rule interaction, sequential state, contextual gating, or learned
symbol semantics. Difficulty bands alter frequencies rather than the underlying
rule domain. The authority itself was not changed.
## Current reviewer considerations

Source SHA-256: `9588c1ef3120c640d32b2858fbb48de7d4bcd3be691858f9294458b9c69c751b`.

# Decisions: 96c1983b6cb5

## D1 — Preserve the selected authority

**Choice.** Do not alter the Racket rule; pin Python generator 4.0.0 to
`RULE_HASH = "9c8ca59a982a"`.

**Rationale.** The canonical outputs are internally consistent and the selected
rule already expresses the intended three-panel D4 transfer. Baseline failures
came from the sampler and validator, not from authority execution. Rule smoke,
authority sync, task tests, and 51 independent parity calls all pass.

**Rejected alternative.** Editing the Racket rule to accommodate the baseline's
color-2/3 assumptions would corrupt correct canonical examples using 4/5 and
6/7. One archival base copy remains divergent, but the selected canonical
execution group is synchronized; no archival file was changed.

## D2 — Replace the legacy axis surface with five exact axes

**Choice.** Advertise only `panel_n`, `transform`, `a_cells`, `c_cells`, and
`palette_id`; every Cartesian combination is supported and observable.

**Rationale.** The former `palette_kind`, `texture`, `palette_size`,
`position_bias`, `n_distinct_colors`, and `density` declarations either did
nothing, duplicated another name, or described constants. An axis that cannot
be inferred from the generated grid is not a usable exact control. The shared
`_analyze_grid` function is the single source for validation and observation.

**Rejected alternatives.** Keeping “diagnostic” aliases would preserve API
noise without adding lawful variation. Keeping degenerate textures in the
ordinary domain would intentionally emit inputs outside the stated rule and
would continue the defect-lint overlap.

**Failure mode considered.** Unknown keys or band-incompatible values can appear
to work when `**overrides` silently swallows them. The new call validator rejects
unknown keys, non-integers (including booleans), and values outside exact ranges.
The exhaustive override gate passes.

## D3 — Retain this task's canonical-scale domain

**Choice.** Use square panel sizes 3–5 and foreground counts 3–6.

**Rationale.** Size 3 is required for direct canonical-profile support. Sizes 4
and 5 provide shape diversity without changing the task grammar. Counts 3–6
admit many asymmetric shapes even at 3x3 while avoiding singleton/dot shortcuts
and near-solid panels.

**Prior lead and adaptation.** The accepted sibling repair
`53de1fcb2e13` uses the same normalized authority hash and provided a useful
architecture pattern. I did not copy its 4–6 size and 3–8 count domain; those
choices would eliminate this task's canonical 3x3 profile and make some
size/count combinations impossible.

**Rejected alternative.** A wider count range at n=3 would create sparse
feasibility corners and more retry behavior without adding a new reasoning
concept.

## D4 — Cover all eight D4 operations

**Choice.** Sample identity, three rotations, two axis flips, transpose, and
anti-transpose in the selected authority's exact order.

**Rationale.** The baseline omitted identity from ordinary sampling despite the
authority accepting it. All operations are now exact overrides, appear in every
difficulty band, and are checked against an independent implementation and real
Racket.

**Failure mode considered.** If A or C is symmetric, multiple transform codes
can share an image. Both shapes are therefore required to have an eight-element
D4 orbit. C is additionally forbidden from belonging to A's orbit.

## D5 — Vary semantic color roles, not arbitrary colors

**Choice.** Use palette pairs `(2,3)`, `(4,5)`, `(6,7)`, `(1,6)`, and `(5,2)`;
reserve 0 for background and 8 for separators.

**Rationale.** The first three pairs preserve all canonical role profiles. The
last two break shortcuts based on numeric ordering or fixed source/target
identity. A/B always share a source color; C/output use a distinct target color.

**Rejected alternative.** Arbitrarily permuting all ARC colors could assign 0 or
8 to foreground roles and would change the separator grammar. Fixed 2/3 was the
baseline bug.

## D6 — Use an explicit lesson schedule to teach beyond canonical transforms

**Choice.** Schedule transforms as `(1,0,4,2,6,3,5,7)` and require three
demonstrations.

**Rationale.** Canonical pairs expose only `{1,4,6}`. No cyclic window of three
schedule entries lies wholly in that set, so every default lesson contains a
noncanonical witness regardless of starting index. Task tests enumerate every
cyclic start; the source-bound census then tests actual production assembly and
all query rotations.

**Rejected alternative.** Independent uniform random transforms would have good
average coverage but a nonzero probability of an all-canonical demo set, leaving
the strongest canonical-fitting rival alive. Resampling inside
`lesson_identifiable` would hide schedule quality and complicate reproducibility.

**Limit.** This schedule refutes the declared canonical-subset rival. It does not
establish universal program identification.

## D7 — Make the rival executable and source-bound

**Choice.** Declare the same pure function under `SEMANTIC_RIVALS`,
`CANONICAL_SHORTCUTS`, and `LESSON_COMPETITORS`; declare a corresponding
noncanonical-transform witness and implement `lesson_identifiable`.

**Rationale.** A prose warning cannot be scored by the semantic gate or lesson
census. The rival demonstrably fits all three canonical pairs and disagrees on
the retained identity witness. Production and rotated-query verdicts can now be
replayed against the final source hash.

**Rejected alternative.** Naming many weak rivals would inflate apparent
coverage without increasing confidence. The selected rival is the most direct
one induced by the canonical demonstrations.

## D8 — Build an independent oracle rather than testing helpers against themselves

**Choice.** Add `workspace/reference_probe.py`, which reimplements parsing,
transforms, validation expectations, canonical loading, and optional real
Racket parity without importing generator transform/validation helpers.

**Rationale.** Shared bugs between `reference_output` and tests could otherwise
produce false confidence. The probe measured 140 samples per band using disjoint
seed ranges and recorded source hashes and exact denominators.

**Rejected alternative.** Relying only on battery receipts would verify public
contracts but provide less transparent task-specific evidence. The task-local
suite was also written first and observed to fail 38 cases on the baseline.

## D9 — Difficulty affects frequency, not legality

**Choice.** All difficulty bands share the same lawful axis ranges; schedules
bias panel sizes and foreground counts only.

**Rationale.** This preserves exact override semantics and avoids a control that
is legal in one band but rejected in another. Easy favors n=3 and smaller
counts; hard favors n=4/5 and larger counts, without removing canonical support.

**Limit.** Difficulty is distributional rather than a guarantee of monotonic
human difficulty.

## D10 — Solve records remain evidence, not labels

The untouched blind task passed 3/3 visible examples before source inspection.
The post-repair solve was prepared from final generator bytes and passed 3/3
visible examples in one revision. It declares earlier exposure `yes` and
reference consultation during the solve `no`; masked query correctness remains
unknown and no solve record is claimed as training admission.
