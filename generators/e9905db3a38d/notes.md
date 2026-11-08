# Working notes: e9905db3a38d

## 2026-10-02 review

Baseline `3.1.0` had three blocking battery failures and two advisory stages.
The principal data defects were:

- no `RULE_HASH` pin;
- `palette_kind`/`texture` axes that did not affect ordinary generation;
- invalid degenerate fixtures declared inside the ordinary texture domain;
- difficulty-dependent override bounds that rejected declared values;
- unknown overrides accepted silently;
- code 1 forced at the upper-left active code cell and code 4 forced at the
  lower-right active code cell in every sample;
- rotation-symmetric or duplicate templates in some samples;
- many inputs whose shape relation to the output was reshape/grow rather than
  the canonical strict shrink relation;
- effectively no canonical-linked support and no executable semantic contract.

Version `4.0.0` replaces the distribution rather than patching individual
symptoms. It adds a strict analyzer, override observer, canonical-linked profile,
Python rule mirror, lesson-identifiability hook, three executable shortcut rivals,
and task-local regression tests. The shape enumerator selects connected,
full-bbox, rotation-observable square motifs. Code assignments contain all four
branches but are shuffled, so the former corner pattern can occur only by chance.

The selected Racket rule remained unchanged because canonical parity, generated
rule smoke, purity/reentrancy, and authority synchronization all passed. The
final full battery is 12/12 green. See:

- `checks/after/checks/e9905db3a38d_after_battery_summary.json`
- `checks/e9905db3a38d_before_after_census.json`
- `tests/test_generator_contract.py`

Known scope boundary: generated templates remain square, use colors 1 and 2,
and the code grid remains exactly two rows with clockwise rotation only. Those
are task semantics, not claimed general ARC augmentation invariances.
## Current reviewer considerations

Source SHA-256: `ebc2d78ae0c648e55b9f0ac70008b3d6c017e67f1ca8e8530e964289f4bb9ad8`.

# Decisions — e9905db3a38d

## D1. Keep the selected Racket rule unchanged

**Original rationale:** The rule decodes codes 1/2 as the two templates and 3/4
as their clockwise rotations, then lays out a two-row mosaic with one-cell
gutters.

**Evidence/probe:** All five canonical examples are matched by the new Python
mirror; generated rule smoke reports 120/120 applications, 120/120 mirror parity,
zero crashes, A-B-A reentrancy, and authority synchronization.

**Alternatives considered:** Rewrite or simplify the Racket program; update
archival authorities.

**Decision:** No rule edit. A rewrite would introduce authority risk without
fixing the actual defects, which were in generation and metadata. Pin
`RULE_HASH="7b04fc79d5f0"` instead.

**Failure mode/limit:** Any future rule edit must update all selected authorities
atomically and repeat canonical plus generated parity checks.

## D2. Reduce the public axes to two real controls

**Choice:** Keep only `tile_size` and `n_codecols`, each with valid domain 2..4.

**Original state:** `palette_kind` and `texture` were declared but did not affect
ordinary output. Degenerate names were mixed into the ordinary texture domain.
Numeric ranges were also inconsistent with difficulty-specific draw bounds.

**Alternatives considered:** Make palette/texture genuinely vary; keep t=5 and
code width 5/6; retain degenerates as ordinary values.

**Decision rationale:** Colors 1 and 2 and codes 1–4 are semantic in this task,
so palette variation would change the rule rather than add harmless diversity.
Sizes 2–4 provide substantial variation while keeping examples compact and near
the 3×3 canonical regime. Degenerates belong in negative tests, not the training
domain.

**Probe:** The override gate accepts 1,440/1,440 draws across 16 cases and three
bands; unknown keys fail.

**Limit:** The rule can mathematically process some larger scenes, but this
review does not claim those are useful or canonical-linked training data.

## D3. Use a four-profile cyclic curriculum

**Choice:** `canonical`, `compact`, `wide`, `large`, selected by
`sample_index mod 4` in every band.

**Rationale:** A deterministic schedule gives each short lesson a stable
canonical anchor plus controlled size variation. It avoids relying on chance to
cover important profiles.

**Alternatives considered:** Pure uniform draws; 100% canonical profile; separate
profile names per difficulty.

**Decision:** One shared profile vocabulary with band-specific size pairs. The
canonical slot is always t=3/n=3 and uses one of the five canonical input
dimension pairs. Other slots scale by band.

**Probe:** The semantic gate observed all four profiles in every band and
161/600 strict canonical-linked samples (26.8% under random seed/sample probes).
The profile-floor check found 19/60 exact/envelope hits.

**Failure mode/limit:** Cyclic schedules can correlate profile with sample index.
The profile itself is not a target label, and shape/code randomness remains keyed
by seed and index; future lesson builders should still shuffle task episodes.

## D4. Require observable rotations and distinct templates

**Choice:** Enumerate connected square-bbox shapes and retain only shapes changed
by a clockwise rotation. Choose two different shapes of the same area.

**Rationale:** If a template is rotation-symmetric, codes 1 and 3 (or 2 and 4)
become observationally equivalent and stop teaching the intended branch. Equal
area mirrors the canonical examples without making family identity depend on
size.

**Alternatives considered:** Retry random growth; hand-written shape library;
allow symmetric shapes as natural variation.

**Decision:** Exhaustive candidate enumeration for sizes 2–4 is small,
deterministic, and removes retry/fallback edge cases.

**Probe:** 180/180 final census samples have two distinct templates and both
rotations observable; baseline counts were 163/180 and 143/180 respectively.

**Limit:** At t=2 all asymmetric three-cell shapes are dihedrally related, though
the colors still distinguish families and clockwise rotation remains visible.

## D5. Put all four code branches in every ordinary sample

**Choice:** Assign codes 1,2,3,4 to four distinct random cells, then populate
remaining cells and repair any empty active column.

**Rationale:** The old random grid plus two guard cells often omitted code 2 or
3. Every sample should directly teach the complete decoder because the code grid
has at least four cells.

**Alternatives considered:** Cover branches only across a lesson; weighted random
sampling with a minimum count threshold.

**Probe:** 180/180 final census samples contain all four codes versus 76/180
before. Both family and rotation rivals disagree on every checked witness.

**Failure mode/limit:** For two-column scenes all four cells are nonzero, so those
examples do not teach zero/skip inside the active span. Wider profiles do include
zeros; the rule’s zero behavior is also structurally simple.

## D6. Randomize code positions without banning the old pattern

**Choice:** Shuffle both code identities and positions. Do not force or forbid
upper-left=1/lower-right=4.

**Rationale:** Baseline forcing created a 180/180 position shortcut. An outright
ban would replace it with a new anti-correlation. Natural random occurrence is
healthier.

**Alternatives considered:** Fixed Latin-square layouts; rejection sampling that
forbids the former pair; preserve the guard cells.

**Probe:** The former pair falls from 180/180 to 10/180 in the retained census,
with 160 distinct layouts. The executable `fixed_corner_decode` rival is refuted
on 60/60 sampled witness claims.

**Failure mode/limit:** Some samples still happen to show the pair. Lesson-level
identifiability, rather than single-example prohibition, is the intended guard.

## D7. Match the canonical strict-shrink relation

**Choice:** Compute decoded output dimensions first, then choose input dimensions
one to three cells larger in each dimension. Canonical slots use exact canonical
dimension pairs.

**Rationale:** The old padding scheme independently sized the template canvas and
frequently produced reshape or grow relations that were absent from canonical
data.

**Alternatives considered:** Preserve unrestricted padding; require only one
dimension to shrink; exactly copy canonical dimensions for all profiles.

**Probe:** Strict shrink rises from 55/180 to 180/180; hard rises from 3/60 to
60/60.

**Limit:** This intentionally narrows a mathematically valid rule domain to the
observed task distribution.

## D8. Centralize validation and observability

**Choice:** One `_analyze` function feeds `self_check`, `observe_overrides`,
`strict_canonical_like`, rule mirroring, witnesses, and rivals.

**Rationale:** Duplicated parsing logic tends to disagree about bbox, active code
span, or validity. A single analysis contract makes diagnostics reproducible.

**Alternatives considered:** Keep minimal self-check and separate ad hoc helpers.

**Probe:** The linter, grammar gate, override gate, canonical profile gate, and
semantic gate all pass. All five canonical inputs are accepted.

**Failure mode/limit:** Tight shared validation means a mistaken invariant could
reject both generation and tests consistently; canonical parity and task-local
mutation tests are the independent checks.

## D9. Add executable rivals and lesson-level identifiability

**Choice:** Declare `ignore_rotation`, `swap_template_families`, and
`fixed_corner_decode`; map each to a witness and require a four-demo lesson to
refute every rival at least once.

**Rationale:** Presence-only witnesses are weak. A semantic feature matters only
when a plausible wrong program produces a different answer.

**Alternative considered:** Boolean witnesses without rivals; requiring every
single demo to refute every rival.

**Decision:** Rival refutation is evaluated across the lesson. The first after
run exposed why: a randomized sample can legitimately reproduce the old corner
pair, but the lesson still kills that shortcut.

**Probe:** Final semantic gate: 3/3 witness/rival claims verified and 12/12 lessons
identifiable.

**Failure mode/limit:** Named rivals are a curated set, not a complete search over
program space.

## D10. Add task-local regression tests

**Choice:** Add `tests/test_generator_contract.py` and document its exact command
in `workspace/README.md`.

**Rationale:** The highest-risk properties are distributional and can regress
without syntax or single-sample failures.

**Probe:** Six test groups pass, including every canonical input/output pair and
all override combinations.

**Limit:** The distribution test uses deterministic sample windows; repository
censuses remain necessary for broader stochastic coverage.
