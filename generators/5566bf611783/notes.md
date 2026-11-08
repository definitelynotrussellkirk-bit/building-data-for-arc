# Current notes: 5566bf611783

## Intended rule and grammar

Color 5 is an impermeable wall. For each 4-connected non-5 chamber, count its
existing color-2 and color-3 markers. Preserve all markers and walls; fill only
zero cells with 2 when `n2 > n3`, 3 when `n3 > n2`, and 8 on an exact tie.
Lawful generated inputs are rectangular 8..16 × 9..18 grids using only
`{0,2,3,5}`, with at least one full divider line, at least two chambers, and
1..6 markers in every chamber.

The canonical authority remains unchanged and is pinned by
`RULE_HASH = "06016d46a01f"`.

## Reversed decisions in v5.0.0

### Random canonical prior → finite teaching schedule

The prior v4.1.0 choice used a 0.32 independent chance of drawing one complete
canonical linked profile. That preserved canonical support but did not guarantee
that a three-demonstration lesson refuted the strongest canonical-fitting rival.
The canonical pairs never contain a chamber with a 2-majority and at least one 3.
Therefore the rival “ties use 8; otherwise any present 3 wins” fit every official
labeled pair.

v5.0.0 replaces the random prior with the repeating four-index schedule:

`canonical_anchor, discriminator, broad, discriminator`

- `canonical_anchor` deterministically cycles through all five complete official
  profiles, retaining exact dimensions, walls, and role-wise marker counts while
  randomizing marker locations within roles.
- `discriminator` retains broad topology/dimension variation but forces one
  chamber with exactly two 2s, one 3, and at least one zero.
- `broad` retains the previous general distribution, including optional ties.

Any four consecutive pairs contain two discriminators. Holding out any query
therefore leaves at least one discriminator among the three demonstrations.
`LESSON_SCHEDULE_PERIOD = 4` and `EXAMPLES_NEEDED = 3` make this finite contract
executable and enumerable.

### Permissive scalar coercion → strict public API

The prior source allowed Boolean, float, and string coercion for seeds,
sample indices, difficulty, and integer axes, silently accepted unknown override
keys, rejected equal aliases, and raised undeclared multi-axis conflicts.

v5.0.0 validates call arguments before creating `GenCtx`, uses
`draw_int_strict`, requires an exact Boolean for `tie_mode`, rejects unknown
keys, accepts equal `texture`/`topology_kind` aliases, and declares every
value-dependent incompatible override tuple in
`INCOMPATIBLE_OVERRIDE_COMBINATIONS`.

## Executable semantic contract

- `strict_canonical_like`: the lawful chamber grammar.
- `SEMANTIC_RIVALS["green_present_dominates"]`: the strongest measured
  canonical-fitting shortcut.
- `SEMANTIC_WITNESSES["red_majority_with_green"]`: a lawful chamber where
  `n2 > n3 > 0` and at least one zero makes the rival disagree.
- `WITNESS_RIVALS`, `CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, and
  `lesson_identifiable`: connect canonical ambiguity, generated witnesses, and
  whole-lesson checks.

The minimal exact counterexample is retained at
`counterexamples/green_present_dominates.json` and covered by portable tests.

## Final measured evidence

Final generator SHA-256:
`1c9811447fdfa633f52107ba5464a208a37a98b3f7ef07734914c1ff62018182`.

- Full after battery: all 12 stages green.
- Selected portable tests: 50/50 pass.
- Override matrix: 47,970 attempted draws, 45,270 accepted, 2,700 declared
  incompatibility rejections, zero findings.
- Semantic sample: strict 600/600, canonical accepted 5/5, witness fired
  389/600; 60/60 fired rival claims agreed with canonical Racket labels.
- Fixed-seed schedule enumeration: 12/12 lessons and 48/48 query rotations
  completed across all bands, with zero ambiguity or hook/scoring errors.
- Post-repair visible-only solve: 3/3 visible examples; earlier rule exposure was
  disclosed and no reference was consulted during the solve.

The 100-lessons-per-band production census is reported in the return evidence;
its result should be read as finite evidence against the declared rival set.

## Assumptions and limits

- `texture` is a compatibility alias for `topology_kind`, not an independent
  semantic axis.
- Explicit overrides bypass the default schedule and are exact controls, not a
  promise that every custom one-off lesson is identifiable.
- The schedule guarantee covers consecutive sample indices and three demos plus
  one query under the declared period. The fixed-seed enumeration proves every
  residue/query rotation only for seed 0 and the declared finite rivals.
- The semantic rival family is not exhaustive. No finite census proves unique
  induction against all possible programs.
- Marker positions inside canonical roles and broad topologies are nuisance
  variation; the rule depends only on 4-connected chambers and counts.

## Open findings

No task-local blocker remains in the final battery. A future review could add
new plausible rival programs, especially shortcuts based on wall geometry,
absolute chamber location, or total marker count; such additions should be
checked against the existing period-4 lesson schedule rather than assumed
covered by the current finite family.
## Current reviewer considerations

Source SHA-256: `1c9811447fdfa633f52107ba5464a208a37a98b3f7ef07734914c1ff62018182`.

# Decisions for 5566bf611783

## D1 — Preserve the Racket authority

**Choice.** Keep the canonical rule unchanged and pin its existing hash
`06016d46a01f`.

**Rationale.** The before rule-smoke, grammar, Racket lint, and authority-sync
stages were already green. Direct inspection of all five official pairs and the
post-repair generated samples showed a coherent count-majority rule; the defect
was in public input handling and lesson composition, not labels.

**Alternatives rejected.** Changing the rule to “green present dominates” would
fit the canonical pairs but fail the exact counterexample and contradict the
natural chamber-count interpretation. Adding rule-side special cases for the
canonical wall geometry would narrow, not improve, generalization.

**Probe.** The after battery's unchanged authority stages and the semantic rival
claims compare generated witnesses to canonical Racket outputs.

**Failure mode / limit.** This decision assumes the current canonical rule is the
authoritative target; it does not claim the official demonstrations alone uniquely
identify it.

## D2 — Treat `green_present_dominates` as the primary rival

**Choice.** Declare the executable rival that fills a non-tie chamber with 3
whenever any 3 is present, otherwise 2; ties remain 8.

**Rationale.** It fits every usable labeled canonical pair, is simpler than the
intended count comparison, and differs on a single lawful chamber with counts
`(n2,n3)=(2,1)`. This is therefore a concrete teaching defect, not a generic
“finite data is ambiguous” observation.

**Alternatives considered.** Location-specific rules, fixed canonical wall
geometry, global rather than per-chamber counts, and “copy the only marker” were
weaker: broad v4 generation already challenged many of them, whereas the
red-majority-with-green branch was systematically absent from the canonical
examples.

**Probe.** `counterexamples/green_present_dominates.json`, the portable
canonical-fit and exact-output tests, and the semantic gate's 60/60 fired rival
claims.

**Failure mode / limit.** Other undeclared rivals can still exist. The declared
set is intentionally finite and should be extended when a stronger hypothesis is
found.

## D3 — Replace probabilistic canonical sampling with a four-slot schedule

**Choice.** Use
`canonical_anchor, discriminator, broad, discriminator`, with three demos and
one held-out query.

**Original choice reversed.** v4.1.0 used a 0.32 independent canonical-profile
prior. That supported official-looking inputs but supplied no whole-lesson
coverage guarantee.

**Rationale.** Two discriminator slots in every period mean that deleting any
one of four pairs leaves at least one discriminator among the three demos. A
single discriminator refutes the primary rival. One canonical anchor retains
25% exact-profile support, and one broad slot plus the discriminator nuisance
variation retain noncanonical coverage.

**Alternatives rejected.** A single discriminator per period fails when that pair
is the query. Making every draw a discriminator would reduce distributional
breadth and overteach one contrast. Random resampling until a lesson passes would
make index identity less transparent and harder to enumerate.

**Probes.** Portable tests enumerate every cyclic start and held-out query.
Fixed-seed Racket enumeration materialized 12 lessons and all 48 rotations across
bands with no ambiguity. The larger random census checks 100 lessons per band.

**Failure mode / limit.** The guarantee applies to consecutive sample indices,
three demos, one query, and the declared period. Explicit custom overrides bypass
the schedule and need their own lesson-level check.

## D4 — Force the smallest sufficient discriminator

**Choice.** In a discriminator, choose a chamber with at least four cells and
place exactly two 2s, one 3, and leave at least one zero; ensure another chamber
has a 3-majority.

**Rationale.** `(2,1)` is the minimal positive mixed red-majority count. Requiring
a zero makes the output disagreement visible. Retaining a separate 3-majority
chamber prevents a lesson from collapsing to “always fill 2.”

**Alternatives rejected.** Larger marker counts add no semantic evidence and can
make sparse canonical similarity worse. A chamber with no zero would make the
rival disagreement observationally irrelevant. A tie does not distinguish the
rules because both output 8.

**Probe.** The exact counterexample test checks the full intended and rival
outputs; schedule tests require the witness in every three-demo rotation.

**Failure mode / limit.** The forced branch targets one rival. It does not by
itself teach every detail of wall connectivity or tie handling; anchors and broad
samples carry those branches.

## D5 — Make the public scalar and override contract exact

**Choice.** Validate literal integer seeds and nonnegative sample indices,
validate difficulty, reject unknown keys, require exact axis types, consume
integer axes through `draw_int_strict`, accept equal aliases, and enumerate every
rejected public tuple in `INCOMPATIBLE_OVERRIDE_COMBINATIONS`.

**Rationale.** The before defect lint reported 138 coercive-scalar acceptances.
The override probe also found silent unknown-key acceptance and 1,620
unstructured multi-axis rejections. These defects make requested distributions
and deterministic identity unreliable even when generated grids happen to be
valid.

**Alternatives rejected.** Continuing `int(value)` coercion preserves legacy
convenience at the cost of Boolean/float/string aliasing. Silently choosing one
of two conflicting aliases hides caller mistakes. Rejecting equal aliases is
unnecessarily hostile and not a real incompatibility.

**Probe.** 50 portable tests, defect lint, and the complete override matrix:
47,970 attempts, 45,270 accepted, 2,700 declared incompatibility rejections, zero
findings.

**Failure mode / limit.** `texture` remains a supported alias rather than an
independent topology degree of freedom. Future axes must be added to both
validation and incompatibility declarations.

## D6 — Use the broad lawful grammar as `strict_canonical_like`

**Choice.** Define strict support as the generator's structural chamber grammar,
not only the five exact linked official profiles.

**Rationale.** The canonical rule is topology- and size-generic. Restricting the
strict hook to the official two-column bridge would penalize the very variation
needed to teach 4-connectivity and count semantics. Exact official support is
still measured separately by `canonical_profile_signature` and scheduled
anchors.

**Alternatives rejected.** An exact-profile-only strict hook would report 25%
support and conflate canonical resemblance with lawful semantic support. A
pure palette/dimension check would be too weak; `self_check` also requires walls,
multiple chambers, and 1..6 markers per chamber.

**Probe.** Semantic gate reports strict 600/600 and canonical acceptance 5/5;
self-check, profile-floor, distribution, and grammar stages all pass.

**Failure mode / limit.** Structural lawfulness is not proof of lesson quality.
That is why witness/rival and whole-lesson hooks are separate.
