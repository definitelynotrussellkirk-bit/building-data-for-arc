# Working notes: 5751039becb2

## 2026-10-03 review — assignment `review-3da34ef2844fd1c5`

The selected 2.0.2 baseline generated diagonal pairs plus singletons but did not
pin `RULE_HASH`, advertised mostly dead controls, silently ignored unknown
controls, and accepted unlawful degenerate textures. Its distractor colors were
always disjoint from survivor colors, so three global shortcuts fit every public
pair and the sampled distribution: keep every repeated color, keep an entire
color once any diagonal pair exists, and accept any same-color 8-neighbor.

Version 3.0.0 replaces those controls with four recoverable axes and a
four-position teaching schedule. The two decisive additions are a remote erased
singleton reusing a survivor color and an erased same-color cardinal pair. A
three-cell diagonal chain is always present to separate the rule from an
“exactly two occurrences” shortcut. `self_check` now validates pixels rather
than generation metadata, `observe_overrides` reconstructs every advertised
control, and unknown/wrong-type/out-of-range overrides fail loudly.

Executable `SEMANTIC_RIVALS`, `CANONICAL_SHORTCUTS`, `SEMANTIC_WITNESSES`, and
`lesson_identifiable` declarations make the intended lesson contract testable.
The task-local `workspace/curriculum_probe.py` uses an independent Python oracle,
reads those declarations dynamically, and enumerates every cyclic schedule
start. It complements rather than replaces the selected Racket authority.

### Verification snapshot

- Final generator SHA-256:
  `181ca03a7640f82475de40134451c820ff0f167fe1b997d943f49e3d05e86aec`.
- Full after battery: 12/12 stages green.
- Portable task tests: 44/44 passed.
- Semantic gate: 600/600 strict lawful draws; 12/12 smoke lessons identifiable.
- Exact override gate: 12,600/12,600 draws accepted, zero findings or warnings.
- Racket-backed lesson census: 300/300 lessons, 1,200 unique inputs, zero
  declared ambiguity.
- Cyclic task probe: 300/300 lessons, all four starts in every band, zero oracle
  mismatches and zero rival survivals.

### Known restriction

The reviewed sampler intentionally restricts survivor components to lengths two
or three and uses a deterministic four-profile curriculum. This is narrower than
the mathematical rule, so it does not prove induction against every possible
shortcut. Randomized positions, colors, dimensions, group counts, complete
cyclic-start checks, and explicit rivals reduce template memorization, but future
expansion should add longer/branching diagonal components and additional legal
decoy geometries without weakening canonical support.

Imported associated notes remain in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `181ca03a7640f82475de40134451c820ff0f167fe1b997d943f49e3d05e86aec`.

# Decisions for `5751039becb2`

## D1 — Preserve the selected rule authority

**Original rationale.** The task already had a coherent Racket rule and all
canonical outputs matched it. The baseline failures were in the input sampler,
contract metadata, and teaching distribution, not the transformation.

**Decision.** Pin `RULE_HASH="8626f391dcea"`, implement an independent Python
`rule_mirror` for tests, and leave the Racket source unchanged.

**Alternatives rejected.** Rewriting the rule would add unnecessary authority
risk. Generating labels in Python would also weaken the existing Racket contract.

**Probe.** Final `rule_smoke`, `racket_lint`, and `authority_sync` stages are green;
canonical pairs match the independent oracle.

**Failure mode / limit.** The Python mirror could share a conceptual mistake with
tests, so it is never treated as final authority; the Racket-backed census and
rule-smoke stage remain required.

## D2 — Replace eight nominal controls with four observable controls

**Original rationale.** The baseline listed `palette_kind`, `palette_size`,
`position_bias`, `n_distinct_colors`, `density`, `texture`, and dimensions/pair
counts, but most were ignored, aliased, singleton domains, or contradicted by
returned pixels. The exact historical rationale is not recorded beyond comments.

**Decision.** Advertise only `grid_h`, `grid_w`, `n_survivor_groups`, and
`profile`. `observe_overrides` reconstructs all four from the grid, the complete
Cartesian product is constructive, and unknown or malformed controls raise.

**Alternatives rejected.** Keeping diagnostic-only fake axes would preserve API
surface but mislead dataset builders. Declaring many incompatible combinations
would hide construction weaknesses rather than fix them.

**Probe.** The final override gate exercised 140 cases and 12,600 draws with no
finding/warning/rejection; boundary and type cases are in the task tests.

**Failure mode / limit.** `profile` is a curriculum category, not a complete
semantic description of every possible lawful grid. New profiles require updates
to construction, classification, witnesses, tests, and schedule guarantees.

## D3 — Use a four-position counterexample curriculum

**Original rationale.** In canonical and baseline-generated data, singleton
colors were distinct from survivor colors. Therefore “keep repeated colors” and
“keep the whole color if any diagonal pair exists” were observationally
indistinguishable from the true local rule. Cardinal same-color negatives were
also absent, leaving an 8-neighbor shortcut.

**Decision.** Cycle four profiles by `sample_index mod 4`:

1. `canonical`: one unique-color singleton;
2. `shared_color_singleton`: that canonical singleton plus a remote erased cell
   reusing a survivor color;
3. `orthogonal_repeat`: a same-color cardinal pair that must be erased;
4. `combined`: both decisive decoys.

With three demonstrations, every cyclic start contains enough evidence to refute
all declared competitors.

**Alternatives rejected.** Pure random sampling could leave whole lessons without
a decisive negative. Putting every counterexample in every grid would reduce
variation and make profile recognition itself a stronger shortcut. A two-slot
schedule did not separately preserve canonical-style examples and both negative
families.

**Probe.** `workspace/curriculum_probe.py` enumerated 300 non-overlapping lessons,
all four starts in each band, with zero rival survivals. The Racket-backed census
independently materialized 300 lessons with zero declared ambiguity.

**Failure mode / limit.** Periodic schedules can be learned as templates. The
positions and colors are randomized, but future expansions should permute or
compose more lawful profile variants while preserving window-level coverage.

## D4 — Require a three-cell chain plus two/three-cell components

**Original rationale.** Pairs alone let the rival “keep colors occurring exactly
twice” survive. A three-cell diagonal chain is the smallest direct
counterexample. One canonical input contains two three-cell chains, so the
validator must allow multiple chains rather than enforce exactly one.

**Decision.** Every generated grid has two to four distinct-color diagonal
components of size two or three and at least one size-three component. The
validator accepts the canonical multiple-chain case.

**Alternatives rejected.** A global color-count hack would not teach locality.
Allowing arbitrary diagonal graphs immediately would broaden coverage but make
exact constructive overrides and the profile grammar harder to guarantee in this
bounded repair.

**Probe.** The initial focused test caught the mistaken exactly-one-chain
assumption; the corrected suite passes all public pairs and 44/44 final tests.

**Failure mode / limit.** The size-2/3 restriction is narrower than the rule.
Longer, bent, or branching diagonal components remain an explicit future stress
axis.

## D5 — Validate from pixels, not generation metadata

**Original rationale.** Baseline `self_check` mostly verified dimensions and the
presence of one pair, allowing identity-like blocks, undeclared degenerates, and
outputs outside the intended lesson grammar.

**Decision.** `_analyse` recomputes the rule output, survivor components, decoys,
component colors/sizes, and profile directly from the returned grid. It rejects
malformed grids, booleans, illegal colors, empty outputs, no-erasure examples,
reused survivor colors, 2x2 identity blocks, and unclassified decoys.

**Alternatives rejected.** Trusting RNG metadata would not protect replayed or
mutated grids. A validator that accepts the entire mathematical input space would
be correct but too weak to certify the promised training distribution.

**Probe.** Defect lint and self-check stages pass; targeted impostors fail in the
focused suite; all 600 semantic-gate draws pass strict validation.

**Failure mode / limit.** This validator defines the selected training grammar,
not every grid on which the Racket rule is mathematically defined.

## D6 — Declare executable rivals, witnesses, and lesson identifiability

**Original rationale.** Prose descriptions did not let gates verify that examples
actually teach the local rule. The public pairs themselves are ambiguous under
three plausible shortcuts.

**Decision.** Add dynamic `SEMANTIC_RIVALS`, `CANONICAL_SHORTCUTS`,
`SEMANTIC_WITNESSES`, `WITNESS_RIVALS`, and `lesson_identifiable`. Tests and the
workspace probe iterate those declarations rather than duplicating a rival list.

**Alternatives rejected.** Hard-coded expected frequencies alone can pass while a
rival still fits complete lessons. Comparing only outputs’ diversity does not
measure semantic identifiability.

**Probe.** The semantic gate confirms all declared shortcut fits on canonical
pairs, all witness claims, and 12/12 lesson checks. Both 300-lesson probes find no
surviving declared rival.

**Failure mode / limit.** A finite rival library cannot prove uniqueness against
all programs. New suspected shortcuts should be added as executable competitors
and accompanied by a minimal lawful witness.

## D7 — Build a reusable cyclic curriculum probe and portable tests

**Original rationale.** The shared census is authoritative but comparatively
expensive and does not guarantee every cyclic query rotation for a task-specific
period. Fast feedback was needed for future edits.

**Decision.** Add `workspace/curriculum_probe.py`, using an independent oracle,
source hashes, dynamic rival declarations, non-overlapping lesson windows, and
complete period-4 start coverage. Add 44 portable task tests, including a test of
the probe itself.

**Alternatives rejected.** A one-off notebook or copied rival list would drift.
Replacing the Racket census with the Python tool would weaken authority.

**Probe.** The tool reports 1,200 unique inputs, zero oracle mismatches, zero
unidentifiable lessons, and zero rival survivals. Portable task tests pass 44/44.

**Failure mode / limit.** The probe is source-bound and Python-based; it is a fast
preflight, not a substitute for Racket execution or independent maintainer
scoring.
