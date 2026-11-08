# Working notes: 2a1d4a2b313a

## 2026-09-28 review

The Racket authority was correct; the baseline generator was not teaching or enforcing it reliably. The original independent scatterer had no `RULE_HASH`, `self_check`, override observer, or semantic contract; several declared axes were inert; unknown overrides were accepted; and no ordinary draw guaranteed the relation cases needed to identify occupancy XOR.

The replacement generator is relation-first. It constructs background agreement, both XOR directions, occupied agreement, and—when multicolor—a different-color occupied overlap. Relations occupy a contiguous interval of a randomized snake path so the curriculum remains morphologically close to the canonical task rather than creating dozens of disconnected colored objects.

Public exact axes are now `grid_h`, `half_w`, `palette_size`, and `relation_profile`. Unknown keys are rejected, every axis is recoverable through `observe_overrides`, and every return passes `self_check`.

Every fourth unoverridden sample is an exact 4x9/red-only anchor, independent of difficulty. Other samples retain difficulty-biased dimensions and use 2..4 colors. This schedule guarantees canonical-profile support in easy, medium, and hard while ensuring every three-example lesson includes evidence against raw cell inequality.

Named rivals:

- raw cell inequality;
- occupancy union;
- copy left occupancy;
- copy right occupancy.

Decisive witnesses map one-to-one to those rivals: different-color occupied overlap, occupied agreement, right-only occupancy, and left-only occupancy.

Retained iteration evidence:

- `checks/iterations/profile-floor-cross-band-failure/` — canonical support initially missed medium/hard;
- `checks/iterations/semantic-rival-contract-failure/` — witness/rival declaration and claim verification were initially incomplete.

Final evidence: 10 focused tests / 83 subtests passed; source-bound after battery 12/12 green; exact canonical profile 19/60; semantic witnesses 4/4 and rival claims 4/4; 12/12 sampled lessons identifiable; override contract 15,120/15,120 accepted with unknown keys rejected.

Known limitation: the spatial curriculum uses structured connected runs rather than arbitrary scatter. This is deliberate to control object-count drift, but it does not cover every lawful spatial arrangement.

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `00e5c100eac96f5ad350a56f6350024f5ed808a33f874bdcf5cc72bded670214`.

# Design decisions for `2a1d4a2b313a`

## Intended rule and ownership

**Choice.** Keep the existing canonical Racket rule and rebuild only the Python generator curriculum.

**Rationale.** The canonical examples, written solution, Racket smoke test, and authority-sync check all agreed: locate the centered full-height gray(5) divider, compare equal-sized panels, and emit cyan(8) where exactly one corresponding cell is background. The baseline failures were generator-contract failures, not transformation failures.

**Alternative rejected.** Editing the Racket rule to accommodate baseline samples. That would have treated symptoms from a weak input distribution as defects in an already-correct authority.

**Probe.** The final rule smoke applied 120 samples with zero crashes and Python mirror agreement; authority synchronization remained green.

## Public axes

**Choice.** Replace the ten mostly inert or redundant baseline axes with four exact axes: `grid_h`, `half_w`, `palette_size`, and `relation_profile`.

**Rationale.** Each surviving axis changes an observable property of the returned grid and has a clear semantic or distributional purpose. `relation_profile` controls occupied-union density while preserving the decisive relation set.

**Alternatives rejected.** Retaining `palette_kind`, `n_left`, `n_right`, `n_distinct_colors`, `position_bias`, `density`, and `texture`. In the baseline, several were aliases, constant single-token metadata, ignored, or incompatible with one another. Keeping them would expand the contract without adding independent coverage.

**Probe.** `observe_overrides` reconstructs all four values from a lawful grid. The final override gate exercised 168 cases over three bands and 15,120 draws with no findings.

**Failure mode/limitation.** The reduced surface does not expose every low-level relation count independently. This is intentional: exact low-level count axes would create many incompatible combinations and encourage teaching counts instead of the rule.

## Shape curriculum and canonical anchors

**Choice.** Use difficulty-biased dimensions over heights 4..10 and panel widths 3..8, but make every fourth unoverridden sample an exact 4x9 canonical-scale anchor in every difficulty band.

**Rationale.** The baseline had zero canonical-profile support. A fixed minority of anchors guarantees task ownership and familiar scale, while the remaining 75% still train size generalization.

**Alternative rejected.** Make every draw 4x9. That would satisfy the profile floor but discard useful shape diversity. Also rejected: easy-only anchors, because the profile gate checks support within each band and medium/hard would still drift.

**Probe.** The retained cross-band failure showed the easy-only defect. The final profile gate found 19/60 exact-profile matches, and the focused test verifies at least one exact profile in each band.

**Failure mode/limitation.** Anchor cadence is deterministic from `sample_index`, not randomly distributed. This makes lesson guarantees auditable but introduces a periodic pattern.

## Palette curriculum

**Choice.** Canonical anchors use only red(2). Other ordinary draws use 2..4 colors selected from nonzero, non-divider ARC colors; explicit `palette_size` overrides always take precedence.

**Rationale.** Red-only samples preserve canonical appearance. Multicolor samples are necessary to distinguish occupancy XOR from raw cell-value inequality: two differently colored occupied cells must still output black(0).

**Alternative rejected.** Always use red(2), which leaves the strongest canonical shortcut unrefuted. Also rejected: always multicolor, which would eliminate exact canonical profiles.

**Probe.** The semantic gate observed the different-color-overlap witness on 451/600 draws and verified all 60 sampled raw-inequality rival claims.

**Failure mode/limitation.** A single canonical anchor remains ambiguous in isolation. The lesson schedule, not each individual sample, carries the disambiguation guarantee.

## Relation construction

**Choice.** Construct panel pairs from explicit relation categories rather than placing left and right cells independently. Every lawful draw includes left-only, right-only, and occupied-agreement cells; multicolor draws also include different-color occupied overlap. Background agreement follows from leaving part of the panel unoccupied.

**Rationale.** These are the truth-table cases needed to teach occupancy XOR and refute the principal rivals. Independent scattering gives only probabilistic coverage and can accidentally make a lesson ambiguous.

**Alternatives rejected.** Independent Bernoulli cells and independent fixed-count scatters. Both can omit decisive cases and are hard to audit semantically.

**Probe.** Focused tests inspect all five relation counts. The final semantic gate reports 4/4 witnesses firing and 12/12 lessons identifiable.

**Failure mode/limitation.** The generator guarantees at least one of each decisive relation rather than balancing every truth-table category equally.

## Spatial layout and morphology

**Choice.** Place the occupied relation sequence in a contiguous interval of a randomized row- or column-snake path. The sequence is left-only, overlap, then right-only, optionally mirrored.

**Rationale.** The first implementation scattered relation categories and produced far more disconnected same-color objects than the canonical examples. A snake interval keeps each panel's occupied support connected or nearly connected while retaining every semantic witness.

**Alternatives rejected.** Fully scattered placement, which failed the strict defect profile; rectangular blocks, which offered too little shape diversity; post-hoc connected-component repair, which would obscure the actual distribution and risk changing requested counts.

**Probe.** A focused regression mirrors the defect linter's object statistic and requires a maximum of ten objects over 60 draws. The final strict defect lint flagged zero issues.

**Failure mode/limitation.** Snake intervals favor path-like or block-like supports and do not sample arbitrary disconnected arrangements.

## Density profiles

**Choice.** Define occupied-union targets as approximately one third (`sparse`), one half (`balanced`), and all but one cell (`dense`).

**Rationale.** The profiles are exact, recoverable from the grid, distinct over all supported areas, and vary the amount of evidence without changing the rule.

**Alternative rejected.** A free integer occupied-count axis. It would be more expressive but would add a large override cross-product and make lesson quality dependent on invalid tiny counts.

**Probe.** `observe_overrides` infers the profile from the occupied-union count; exact override tests pass for all declared axes.

**Failure mode/limitation.** Dense scenes contain only one background/background cell, so that witness is present but visually small.

## Validation and override policy

**Choice.** Reject unknown override keys immediately; generate through keyed RNG only; return fresh rows; run `self_check` before returning.

**Rationale.** Silent typo acceptance was one of the baseline's largest contract failures. Exact, deterministic overrides are necessary for future automated curriculum searches and adversarial probes.

**Alternative rejected.** Ignore unknown keys for backward compatibility. That makes misspelled experiments appear successful.

**Probe.** Focused tests cover unknown keys, exact observation, deterministic replay, fresh objects, and unchanged global RNG state. The final override gate reports `unknown_key_verdict: rejected`.

## Semantic contract

**Choice.** Declare four executable rivals and four relation-specific witnesses:

- left-only occupancy refutes copying the right panel;
- right-only occupancy refutes copying the left panel;
- occupied agreement refutes occupancy union;
- different-color occupied overlap refutes raw cell inequality.

**Rationale.** These competitors are simple, plausible, and collectively cover the main ambiguities in the canonical demonstrations.

**Alternative rejected.** A larger list of weakly related witnesses. The first semantic-gate attempt showed that naming a witness is insufficient unless its claimed relation actually forces a rival disagreement.

**Probe.** The retained semantic-contract failure documents the incomplete declaration. The final gate verified 4/4 claims and all 12 sampled lessons.

**Failure mode/limitation.** The competitor set is not exhaustive over arbitrary programs; it is an explicit high-value rival set, not a proof of unique identification among all possible rules.
