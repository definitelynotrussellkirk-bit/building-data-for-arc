# Current notes: 587396c0817d

## Intended rule

Process rows independently. Let `non7` be the non-background columns in order.
A row with no color-6 anchor becomes all 7. A row with one 6 becomes a
contiguous color-8 bar whose length is `len(non7)` and whose start is
`c6 - rank(non7, c6)`; every other cell becomes 7. `RULE_HASH=703072e0ab28`
remains pinned to the canonical Racket authority.

## Current generator contract

- Lawful grids are rectangular 6..18 by 8..20, use colors 0..9, have 7 as
  the strict modal color, contain at most one 6 per row, at least one active
  row, and at least three non-7 cells in each active row.
- Active rows contain one 6 plus other non-7 cells. Decoy rows contain non-7
  cells but no 6. Empty rows are all 7. Color 8 is allowed as an input decoy.
- Request scalars are strict: `seed` and nonnegative `sample_index` are exact
  Python ints; difficulty is `None|easy|medium|hard`; unknown, mistyped, or
  out-of-range axes fail before RNG construction.
- Explicit overrides are exact and bypass the default lesson curriculum.

## Decision changes in this review

The imported lead `GNOTE-000086` described v3.1.0's 80% canonical prior only
in the medium band and considered zero easy/hard strict support intentional.
The pinned baseline was remeasured rather than trusted: profile-floor found
zero exact canonical-profile support in easy and hard, defect-lint found 138
strict-scalar acceptances, semantic-gate found no declared contract, and
selected `target_code` text had drifted from canonical authority.

Version 4.0.0 replaces the medium-only random prior with a deterministic
period-2 default schedule in every band:

1. `rank_six_witness`: retain the band's generalized dimensions and force one
   seven-cell active row whose 6 is the seventh non-7 cell. This refutes the
   canonical-fitting `rank_cap_5` rival.
2. `canonical_core`: emit a 10x10, 4..5-active, 4..5-decoy scene using all
   colors in the small palette, giving exact canonical profile `(10,10,5)`.

With three demonstrations, every four-pair window contains two rank-six
witnesses, so every single-query rotation leaves at least one refuting demo.
The fixed-seed period enumeration and the larger production lesson census are
retained under `WORK/checks/`.

## Semantic evidence

`rank_cap_5` uses the intended rule except it caps the anchor's non-7 rank at
5. It fits all three canonical labels because their maximum observed rank is
5. The retained lawful counterexample has active row
`[0,1,2,3,4,5,6,7]`: canonical Racket paints `[8,8,8,8,8,8,8,7]`, while the
rival paints `[7,8,8,8,8,8,8,8]`. See
`counterexamples/rank-cap-5/counterexample.json` and
`WORK/checks/rank-cap-5-racket.json`.

The executable contract is `strict_canonical_like`, `SEMANTIC_WITNESSES`,
`SEMANTIC_RIVALS`, `WITNESS_RIVALS`, and `lesson_identifiable`. Focused tests
also exhaust both schedule starts and all four query rotations.

## Parametric extension

`workspace/parametric/prototype.py` studies one episode-level parameter,
`bar_color in {8,3}`. Color 8 returns the exact canonical source byte-for-byte;
color 3 changes only the bar-paint literal. Every label and counterfactual is
executed through the real Racket bridge. Two episodes cover both settings,
three demos plus one query each, with all rotations checked. This is evidence
only and is not a production axis or canonical rule change.

## Authority and limits

The reviewed authority-sync patch copied canonical `program_solution` text to
selected `racket_target.target_code` while preserving archival `raw_code`.
Behavior and `RULE_HASH` did not change.

Finite declared-rival checks do not prove unique induction against every
possible program. The curriculum guarantee applies to default sampling;
explicit override calls intentionally bypass it. The parametric prototype tests
only output color, not anchor/background roles or a production API. Catalog
approval/training status remains a maintainer decision independent of passing
checks.
## Current reviewer considerations

Source SHA-256: `c5c8f3618a62ad81eabb7fb95461fc1fd2eae5242417c3cd8e22a86448d719e8`.

# Decisions — review-5bbc1d2de31efc00

## D1 — Treat the pinned packet as authority, not the historical approval note

**Input choice.** Start from source SHA `9b14c423…`, run the complete before
battery, and use imported `GNOTE-000086` only as a lead.

**Rationale.** The assignment explicitly says prior claims are not measurements
of the selected baseline. The before battery found 7 green stages, 3 advisory
stages, and 2 failures despite the historical “approved” narrative.

**Alternatives.** Preserve v3.1.0 unchanged; copy historical metrics into the
review. Both were rejected because they would miss current scalar, profile,
semantic, and authority defects.

**Limits/failure modes.** Baseline evidence is tied to the original hash and
cannot be used as final-source proof.

## D2 — Add strict request validation before `gen_ctx`

**Choice.** Reject non-int/bool seeds and sample indexes, negative indexes,
invalid difficulty values, unknown axes, mistyped values, out-of-range values,
and conflicting aliases before any RNG call.

**Probe.** A task-local parametrized test was run red against v3.1.0, reproducing
all baseline scalar acceptances, then green after the repair. The portable task
snapshot is retained in `checks/task-tests/`.

**Alternative.** Rely on `gen_ctx` coercion. Rejected because the baseline
strict-scalar detector showed 138 accepted malformed requests.

**Limit.** Validation is task-local; a shared strict helper would reduce repeated
code across generators.

## D3 — Alternate a decisive witness and an exact canonical core

**Choice.** Use period 2 with profiles `rank_six_witness` and `canonical_core`.
The canonical core is 10x10 with 4..5 active and 4..5 decoy rows and exact
five-color coverage. The witness keeps band dimensions and forces an anchor at
non-7 rank 6.

**Original rationale.** v3.1.0 concentrated canonical support in medium while
easy/hard intentionally extrapolated. The current after policy instead requires
at least one exact profile in each band and a declared teaching contract.

**Alternatives considered.** Random 25% or 80% priors in easy/hard; a wider
non-deterministic witness probability; dropping difficulty bands. Random priors
could miss pinned draws and lesson windows; dropping bands would collapse
useful extrapolation. The alternating design gives deterministic coverage while
leaving half of default draws band-shaped.

**Probes.** Pinned profile-floor seeds; exhaustive starts modulo 2; all four
query rotations; semantic gate with fixed-seed schedule enumeration; larger
lesson census.

**Limits.** Explicit overrides bypass the schedule. Half of default draws in
each band are intentionally 10x10, so difficulty affects only the alternating
witness profile.

## D4 — Declare `rank_cap_5` as the primary rival

**Choice.** The rival caps the anchor's non-7 rank at 5. It fits all canonical
labels and disagrees on rank-six rows.

**Why strongest/plausible.** Canonical rows demonstrate ranks only 0..5, with a
seven-cell bar present but no anchor at rank 6. A learner can therefore infer
that the sixth index is a maximum positional role rather than an observed
boundary.

**Probe.** Exact 6x8 counterexample evaluated by canonical Racket; executable
rival and witness; all canonical pairs checked; generated lessons checked.

**Alternatives.** “Any non-7 row becomes a bar” is already refuted by canonical
decoy rows. Fixed bar length, left alignment, and color-count-only rules are
also refuted by canonical examples. `rank_cap_5` survives all of them.

**Limit.** This is one finite rival family, not a proof of unique induction.

## D5 — Parametric extension changes only bar color

**Choice.** Prototype `bar_color in {8,3}`, chosen once per episode. The default
8 source is byte-identical to canonical authority; 3 edits one literal.

**Rationale.** This preserves all original object roles, row relationships, and
rank/count reasoning while creating a small, easy-to-audit rule family.

**Alternatives.** Parameterize anchor color or background color; parameterize
rank cap. Anchor/background changes require parameter-dependent input roles and
risk confusing fixed semantic colors. Rank cap changes the intended geometric
reasoning and overlaps the identified shortcut, so it is better used as a
negative competitor.

**Probe.** Real Racket labels for two episodes, 3 demos + 1 query each, both
settings, 8 counterfactual labels, and all 8 query rotations. Canonical default
checked on all 3 labels.

**Limits.** Output-color variation is modest and remains prototype-only.

## D6 — Apply exact authority text sync

**Choice.** Apply the saved authority-sync proposal changing only
`/racket_target/target_code` in
`shared/data/base/solutions/training/2a28add5__587396c0817d.json`.

**Rationale.** Execution parity already passed, but the selected text differed
from canonical `program_solution`. Exact synchronization removes provenance
drift while preserving `raw_code`.

**Alternative.** Leave semantically equivalent compact text. Rejected because
the assigned after gate requires source binding, not only behavior.

**Limit.** The apply receipt is per-file atomic, not a general repository-wide
transaction; recovery receipt is retained by the tool.
