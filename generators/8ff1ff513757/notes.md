# Working notes: 8ff1ff513757

## Current rule and source

Version `2.2.0`, generator SHA-256
`848dc677b1ec180c1fced2b9f1bc451310c131b1ed2c6c1f67394f3649535256`.
The pinned Racket authority remains unchanged at rule hash `ed6dfa957511`:
remove every all-zero row, preserve every nonempty row byte-for-byte and in
order, and preserve the original width. An entirely blank grid is outside this
generator's teaching domain.

## Repair decisions

- Require literal integer `seed`, nonnegative literal integer `sample_index`,
  and literal integer exact-axis overrides. The baseline silently accepted
  booleans, floats, strings, and negative indices.
- Declare every impossible exact `(grid_h, n_active_rows)` pair rather than
  relying on hidden layout failure. The declared domain uses heights 6..12 and
  2..6 pairwise-separated active rows; exactly the pairs with
  `grid_h < 2 * n_active_rows` are incompatible.
- Use a four-slot schedule: canonical 6x6, canonical 7x7, canonical 8x8, then a
  broad draw. This gives every difficulty band canonical-profile support while
  retaining varied dimensions, palettes, masks, and row counts.
- Make lesson-level teaching distinctions explicit. The schedule includes a
  trailing-blank witness and a consecutive-internal-blank witness, and declares
  two canonical-fitting rivals: preserve trailing blanks, and remove only one
  row from each internal blank run. `lesson_identifiable` rejects any lesson in
  which either rival survives the demonstrations and disagrees on the query.
- Preserve a source-bound generated counterexample under
  `counterexamples/generator-shortcuts/`, replayed by the focused tests.

## Verification summary

The baseline battery was 9 green, 2 advisory, 1 failed. The final battery is
11 green and 1 nonzero semantic stage; that stage reports no semantic defect
and exits only because the declared four-slot schedule must be enumerated by a
separate census. The required fixed-seed enumeration passed 12/12 lessons and
48/48 query rotations. A wider production census passed 300/300 lessons and
1,200/1,200 rotations, with zero materialization errors, hook warnings, scoring
errors, or ambiguity against the declared rivals. Task-local tests pass 24/24.
Exact evidence is indexed in `WORK/REVIEW.md` and `WORK/RESULTS.json`.

## Limits

These checks establish correctness and lesson identifiability only over the
selected generator domain and the two declared plausible rivals. They do not
prove uniqueness against every imaginable rule or every random seed. The
fixed-period census exhausts starts only at seed 0 across easy/medium/hard; the
300-lesson census samples broader seeds but is finite.

Associated historical notes in `evidence/associated_notes.jsonl` were used only
as leads. All claims above were remeasured on the selected baseline and final
source.
## Current reviewer considerations

Source SHA-256: `848dc677b1ec180c1fced2b9f1bc451310c131b1ed2c6c1f67394f3649535256`.

# Decisions for 8ff1ff513757

## D1 — Keep the canonical Racket rule unchanged

**Prior state.** The baseline generator was bound to canonical rule hash
`ed6dfa957511`, and rule-smoke/authority-sync evidence showed that rule removes
all all-zero rows while preserving every nonempty row and the full width.

**Decision.** Repair only the generator and its executable teaching contract.
No Racket source changed.

**Reason.** The reproduced defects were input-contract, distribution, and
lesson-identifiability defects. Changing correct authority semantics would have
expanded scope without fixing their source.

**Probe.** Final rule-smoke and authority-sync stages are green; the exact
shortcut counterexample was also evaluated by the same pinned authority.

## D2 — Reject scalar coercion at the public generator boundary

**Baseline failure.** `sample_index` accepted `True`, `False`, `1.0`, `"1"`, and
`-1`. Exact integer axes likewise relied on permissive conversion paths.

**Decision.** Require `type(value) is int` for `seed`, `sample_index`, and every
provided exact integer override; require `sample_index >= 0` before constructing
the generation context. Unknown axes reject loudly.

**Rejected alternative.** Normalizing with `int(value)` was rejected because it
aliases materially different caller requests and made the defect linter unable
to verify exact public controls.

**Tests.** Parameterized regressions were written first and observed failing on
the baseline. They now cover booleans, floats, strings, `None`-adjacent cases,
negative indices, and all declared axes.

## D3 — Declare the complete joint-axis incompatibility set

**Baseline finding.** The override stage found 1,080 predictable failing
combinations in its sampled matrix because a requested height could not hold a
requested number of pairwise-separated active rows, yet no incompatibility was
declared.

**Decision.** Publish every `(grid_h, n_active_rows)` pair in the declared domain
for which `grid_h < 2 * n_active_rows`. A lone `n_active_rows` request raises the
minimum default height so it does not fail because of a hidden random draw.

**Reason.** This is the actual geometric feasibility condition under the
chosen grammar: active rows are nonadjacent, and the generator forbids occupying
both boundary rows simultaneously.

**Rejected alternative.** Silently lowering the requested active-row count or
resampling height would violate exact override semantics.

**Probe.** The focused suite checks every domain pair. The final override stage
is green with zero undeclared rejected combinations.

## D4 — Anchor all three canonical profiles in every difficulty band

**Baseline finding.** The profile-floor stage was advisory: canonical-scale
support was weak or missing outside medium.

**Decision.** Declare a four-slot schedule:

1. `canonical_6x6` with four nonzero colors;
2. `canonical_7x7` with three nonzero colors;
3. `canonical_8x8` with four nonzero colors;
4. a difficulty-skewed broad draw over the advertised ranges.

The slot is `sample_index mod 4`; difficulty still affects the broad draw and
the non-anchored axes.

**Reason.** Three deterministic anchors provide reviewable canonical support in
easy, medium, and hard. The fourth slot keeps dimensions, row counts, palettes,
blank positions, and row textures broad rather than collapsing all data onto
three templates.

**Rejected alternatives.** Pure random sampling had already missed profile
floors. Making every draw canonical would have reduced diversity and encouraged
shape memorization.

**Probe.** Focused tests enumerate every band and schedule slot. The final
profile-floor and diversity stages are green. The semantic smoke sampled all
four profiles in every band.

## D5 — Model canonical-fitting rivals explicitly

**Finding.** The canonical demonstrations do not distinguish two plausible
rules:

- `preserve_trailing_blank_rows`: delete blanks only through the last nonempty
  row;
- `remove_one_internal_separator`: remove one row from each internal blank run,
  but preserve additional rows in a longer run.

**Decision.** Declare these functions in `SEMANTIC_RIVALS`,
`CANONICAL_SHORTCUTS`, and `LESSON_COMPETITORS`; declare narrow witness predicates
and rival mappings; use `lesson_identifiable` to evaluate the actual assembled
lesson.

**Reason.** Per-grid validity does not prove that three demonstrations teach the
intended transformation. Executable rivals make the ambiguity measurable and
turn future schedule regressions into test failures.

**Rejected alternative.** A prose warning in `notes.md` would not be exercised
by the battery or production lesson materializer.

## D6 — Make the four-slot lesson rotation-safe against those rivals

**Decision.** Slot 1 guarantees trailing blank rows. Slot 2 guarantees at least
two consecutive internal blank rows. Slot 3 carries both boundary and internal
witnesses when lawful. Slot 0 retains a leading-blank distinction. Candidate
selection falls back to the broad lawful set only for exact overrides that make
a preferred witness impossible.

**Reason.** A lesson has three demonstrations and one query. Any one of the four
positions may become the query downstream, so each rival must be refuted by
more than one position in the period rather than by a single fragile example.

**Probe.** A focused test enumerates all four starts and all query rotations.
The fixed-seed public period census materialized 12/12 lessons across three
bands and found 0/48 ambiguous rotations. The wider census materialized 300/300
lessons and found 0/1,200 production or rotated ambiguities.

## D7 — Retain one exact generated authority counterexample

**Decision.** Preserve seed `20261011`, sample index `1`, medium as a compact
counterexample to the trailing-blank rival. Store the input and both outputs in
the task directory and re-create it in a focused test.

**Reason.** This binds the answer to final generator bytes and the public Racket
authority instead of relying on a hand-written hypothetical grid.

## D8 — Treat the semantic battery nonzero as a discharged follow-up, not a hidden pass

**Measured result.** The final aggregate battery is 11 green / 1 failed. The
semantic stage itself reports 12/12 lessons identifiable, 0/48 diagnostic
rotation ambiguity, 2/2 witnesses firing, and 2/2 rival claims verified. It
exits 1 only because a declared `LESSON_SCHEDULE_PERIOD=4` requires a separate
period enumeration.

**Decision.** Report the nonzero exactly and retain both requested source-bound
follow-ups rather than relabeling the aggregate battery green. Completion is
based on the explicit period census and wider census, not on suppressing the
warning.

## Remaining limitations

- The executable semantic claim is finite and rival-relative. Other plausible
  hypotheses may exist.
- The fixed-period census exhausts start residues at seed 0 only. The 300-lesson
  sample broadens seed coverage but is not exhaustive.
- The generator intentionally targets a structured teaching manifold: 2..6
  nonadjacent nonempty rows, at least two blanks, at least two nonzero colors,
  varied masks, and one globally blank column. It does not claim to cover every
  input accepted by the abstract Racket rule.

## Native parametric admission review — 2026-10-25

Built `workspace/parametric` with exact canonical setting `compress_only` and
sequential setting `mark_vertical_contacts`. Step A removes all-zero rows; step
B consumes the compacted intermediate and recolors nonzero cells with a vertical
nonzero neighbor to 9. A source-bound `skip_compression.rkt` counterfactual
applies B before A and changes both output shape and content.

The minimum curriculum originally admitted a `repeated_columns` shortcut for
seed 156. The sampler now reserves a column on alternating compacted rows and
forbids it on the rows between them. That column is repeated but never forms a
vertical contact, so the shortcut is constructively refuted. A regression fixes
this witness, and `workspace/parametric/audit.py` replays structural, public,
teaching, protected-Racket rival, and causal checks for future agents.

Bounded review evidence is in `workspace/parametric/evidence/current/`; native
qualification and owner acceptance remain separate authority steps.
