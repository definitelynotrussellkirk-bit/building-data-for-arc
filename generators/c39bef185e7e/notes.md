# Working notes: c39bef185e7e

## Review-3554b90eafb204ac, 2026-10-06

Baseline v3.0.0 hash:
`14546a8bb3311d85d923f957c0b3bff0afecd7ba512ba93bb35d2efde4b71143`.
Repaired v4.0.0 hash:
`2176196eaa90ff3a14d71444be3d23c1e55fa4395d6b18321372a60ab839dd94`.
The Racket authority, canonical examples, and `RULE_HASH = 622186409963` did not change.
The associated-notes file was empty and this home had no retained prior-return
index. The pinned source and its comments were the only historical design lead.

### Reproduced defects

- The old two-demo curriculum has only one equal-size witness in some three-pair
  windows. The original declared rivals expose 150 ambiguous rotations among
  900 holds from 300 production lessons, although all 12 before checks passed.
- Bounding-box area and a cell-count / bbox-area / chirality / endpoint cascade
  each fit all five canonical pairs. Adding those rivals to the *saved baseline*
  lessons exposes 60/300 ambiguous production lessons and 270/900 ambiguous
  rotations. No inputs or reference labels were regenerated for that rescore.
- Default size relation was perfectly coupled to left/right location. The
  chiral-only common pool could not emit four of the five canonical common
  shape classes (L triomino, T tetromino, U pentomino, W pentomino).

### Repair and tradeoff

Every even default index is a matched L/S tetromino scene. These shapes differ
under D4 but have identical coarse signatures, including graph endpoint count.
One common copy is mirrored, so both rotation-only and translation-only rivals
are refuted. Odd indices explore the shared three-, four-, and five-cell shape
pool in both common and singleton roles. A third demonstration preserves two
matched scenes in each four-pair window while leaving room for exploration.
This adds one demonstration per default lesson; no model-quality or token-cost
benefit was measured.

Quadrants use `(index + index // 4) % 4`, common counts retain `(3,3,2,3,4)`,
and the size relation has period six. The raw combined period is 240, with 36
aggregated role/quadrant/count profiles. The direct probe exercises all starts;
the 100-lessons-per-band production census exercises starts 0..99 and records
actual accepted indices. Neither is described as the other population.

`motif_size` now supports 3..5; `size_relation` is exactly `equal|different`.
Every advertised finite control combination remains constructible. `None`
means omission before scheduled defaults, matching the shared draw convention.
Explicit controls can replace teaching witnesses; use the actual lesson hook
and production evidence for those populations rather than extending the default
schedule claim.

### Final evidence and remaining limits

The source-bound after battery passes 12/12 stages, including a required 48-rotation
smoke check. The strict canonical profile rate remains 351/600 (58.5%). The
production census has 0/300 ambiguous lessons and 0/1,200 ambiguous rotations.
The public-Racket cyclic probe has 0/720 ambiguous ordered windows and 0/2,880
ambiguous rotations over three bands and 240 starts, using 729 draws / 728 exact
unique inputs. The selected portable suite has 24 passing tests, including
72 explicit joint-control cases and generated canonical-class support over
seeds 17, 41, 103 and indices 0..479.

Direct consecutive windows do not model arbitrary duplicate rejection patterns.
Shape support remains a finite 3x3-slot polyomino pool, not every lawful shape or
layout. Difficulty salts choices without a calibrated monotone hardness promise.
No GPU/model evaluation, training-admission change, or authority change is claimed.
## Current reviewer considerations

Source SHA-256: `2176196eaa90ff3a14d71444be3d23c1e55fa4395d6b18321372a60ab839dd94`.

# Decisions: c39bef185e7e v4.0.0

## Source and intended outcome

Improve the assigned generator's training examples while retaining the selected
dihedral-outlier rule. Baseline source was the immutable packet's v3.0.0,
SHA-256 `14546a8bb3311d85d923f957c0b3bff0afecd7ba512ba93bb35d2efde4b71143`.
Its notes and associated evidence were empty; no prior return was used as a
measurement or lead. Original rationale is known only where its source comments
state one. The final source is
`2176196eaa90ff3a14d71444be3d23c1e55fa4395d6b18321372a60ab839dd94`.

## Input choices

| Choice | Original rationale / observation | Decision, alternative, and evidence |
|---|---|---|
| Grid height 10..11, width 12..13 | Keep canonical dimensions and palette profiles | Retain exact ranges. All four dimension pairs remain available; after profile-floor checks pass in all bands. Larger canvases would add distance without fixing the demonstrated teaching defect. |
| Background 0, objects 3, output 8 | Fixed semantic colors in the unchanged Racket rule | Preserve them. Arbitrary color permutations would change the task contract. |
| One corner marker, colors 4/5/6/7/9 | Canonical irrelevant marker; validator must accept it | Retain independently drawn exact color/corner controls and preserve the marker in labels. No marker-coded answer rule is added. |
| Common count 2..4 | `(3,3,2,3,4)` gives 60% canonical multiplicity | Keep this schedule. Measured strict-profile rate is 351/600 (58.5%), above the retained 50% floor. Fixed count 3 would reduce support unnecessarily. |
| Six separated 3x3 placement slots | Keep components separate at canonical scale | Retain slots and at most five objects. The geometry is deliberately bounded; this review does not claim arbitrary placement or shape support. |
| Outlier quadrant | Old index%4 schedule defeats bottom-right selection but couples location with size parity | Use `(index + index//4)%4`: each four-index block is a permutation, shifted between blocks. All 24 quadrant × relation × count combinations occur in each band's 240-index direct probe. Every four consecutive default indices retain at least two non-bottom-right objects. |
| Motif sizes and common shapes | Old chiral-only size4/5 pool guaranteed reflection witnesses but excluded four canonical common classes | Add size3 and use the same finite shape pool in both roles for exploratory scenes. The test observes every canonical common class over 3 seeds × 480 indices. This is generated support, not a proof of uniform class frequency. |
| Equal/different size | Old parity schedule provided one equal-size discriminator, sometimes lost when held out | Add exact observable `size_relation`. Even defaults are equal size; exploratory odd defaults cycle equal/different/different. Explicit controls win; `None` means omission. The suite checks 72 joint control combinations plus independent observed values. |
| Matched witness family | New requirement follows scalar-rival counterexamples | Alternate L/S tetromino witnesses with exploration. L/S share size4, bbox area6, chirality, and two endpoints, yet are different D4 classes. Reflection of one common copy defeats rotation-only matching. |
| Demonstration count | Baseline declares two | Raise to three. Every four-pair default window has two matched witnesses, so any single query holdout leaves one. Keeping two while retaining broad exploratory shapes failed the stronger scalar-cascade probes. This adds one demonstration; model/token benefit is unmeasured. |
| Difficulty | Existing code salts shapes/layout by band | Preserve this behavior, tested in easy/medium/hard. Do not label the bands a measured monotone difficulty scale. |

## Alternatives and genuine failed probes

The original battery passed 12/12 stages, so passing that battery was insufficient
evidence of lesson quality. The 300-lesson baseline census with its original
rivals has 0/300 production ambiguities and 150/900 query-rotation ambiguities.
The concrete seed17 medium direct triple at indices1,2,3 loses its equal-size
discriminator when index2 becomes the query.

The first proposed repair kept two demonstrations and used two equal-size
witnesses per triple. The independent adversarial review found that unique
bounding-box area also fits all five canonical pairs. Matching size and bbox
still leaves chirality and endpoint fallbacks: P/U or F/Z examples can teach
those shortcuts. Exact emulated proposal grids, identified as emulated rather
than production output, were executed through public `arcpuzzles apply` and
retained in `checks/adversary/`. No failed solver revision was manufactured.

Using only L/S scenes would defeat those rivals with two demonstrations but
concentrate the whole task on two four-cell shapes. The selected three-demo
design preserves two such witnesses and two exploratory scenes in a four-pair
lesson. It also restores the previously absent achiral/three-cell common shapes.

Re-scoring the unchanged baseline census with the final declarations finds
60/300 ambiguous production lessons and 270/900 ambiguous rotations. Its
`input_generator_sha256` is baseline and `rival_generator_sha256` is final;
there are zero new generated instances and zero new reference executions.
This isolates previously undeclared rival failures from the changed sampling.

The final three-demo census has 0/300 production ambiguities and 0/1,200
rotation ambiguities against six distinct rival behaviors. The direct public
Racket probe covers all 240 starts in each band: 720 ordered windows and 2,880
rotations, with 729 draws / 728 unique grids and no ambiguity or mirror mismatch.
The production census uses its actual sampler, seeds and accepted indices;
the direct probe does not simulate arbitrary rejection patterns.

## Reusable tooling and verification

`workspace/probe_curriculum.py` adds exhaustive cyclic windows and exact joint
axis support to the existing production census. It reads current declarations,
binds the generator/probe/reference hashes, and retains exact ambiguities. It
uses public `Catalog.apply`; private runner functions are not a dependency.

Focused tests were written and observed failing against baseline before repair.
The final suite contains 24 meaningful tests. Both the direct and staged task
runs pass. Initial missing-pytest runs and an intermediate test syntax error
are retained; the syntax error was corrected before measuring the intended red
tests. The final test environment is a venv because the staged runner disables
user-site packages. Those setup failures are not generator regressions.

## Limits and stopping criteria

The generator keeps a finite polyomino pool and canonical-scale slot layout.
Matched/exploratory roles affect motif-size frequencies; the repaired schedule
removes the measured left/right relation leak, not every possible distribution
correlation. Exact overrides that change matched scenes, custom query assembly,
or skipped indices require their own lesson evidence. The hook validates the
actual labelled lesson and declared rivals, not every possible hypothesis.

The reference rule, canonical data, frozen fixtures, audit targets, approval
state, and training-admission state are unchanged. Stop after the required
source-bound checks, final solve, audits, and fresh-packet replay pass; no model
training or universal-induction claim is made.
