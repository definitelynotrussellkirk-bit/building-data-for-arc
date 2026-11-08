# Working notes: 2b6886e6e1b3

## Current rule and authority

VERSION `4.1.0`; generator SHA-256
`dad8ada5831256eda6eae7ce0db53fe4f0fc14e813bb77633303f94cae13429b`.
The selected Racket authority was not changed. `RULE_HASH` remains
`860b011c178c`, and the final authority-sync check gives execution parity on all
4 train and 1 test canonical pairs.

The input is a fixed 4×7 scene with a command at `(0,3)`, a left 3×3 motif, and
a right 3×3 motif. Commands `1..4` mean identity, clockwise 90°, left-right
reflection, and 180° rotation of the right occupancy mask. The 3×3 output is
color 8 on the intersection of the left mask and transformed right mask.

## Repair decisions

### Connected canonical morphology

The v4.0.0 sampler drew arbitrary five-cell subsets of a 3×3 panel. All ten
panels in the five canonical inputs are four-connected, but a reproducible
3,000-draw baseline census found both generated panels connected in only
185/1000 easy, 127/1000 medium, and 98/1000 hard draws. Version 4.1.0 samples
from the complete finite set of 49 four-connected five-cell 3×3 masks. The same
census is now 1000/1000 in every band (`checks/morphology-census.json`).

This is deliberately a curriculum restriction, not a change to executable
authority. `self_check` still accepts authority-lawful disconnected motifs;
`strict_canonical_like` rejects them, and a focused regression records that
boundary. I did not additionally require edge spanning, endpoints, or a
particular polyomino family because the canonical evidence does not justify
those narrower restrictions.

### Literal scalar contracts

The baseline defect linter reported 96 strict-scalar warnings: coercible
`cmd`/`overlap_size` overrides, invalid difficulty values, non-integer seeds,
and non-integer or negative sample indices were accepted. Exact call validation
now requires literal integer seeds, literal nonnegative integer sample indices,
`difficulty` in `{None, easy, medium, hard}`, and strict integer public
overrides. Unknown axes still raise. Test-first regressions preserve every
reproduced case.

### Portable focused tests

The inherited task test used a fixed parent-depth data path and a repository-only
helper import, so portable task-test preflight failed before executing the new
regressions. It now uses `reviewer_support.find_root`, `canonical_path`, and
`canonical_pairs`, while retaining the same canonical rule pin and pair checks.
The final portable selected-task suite passes 29/29.

## Teaching schedule and measured limits

The existing four-command cyclic schedule remains: four consecutive
demonstrations contain each command once, and the production query is the next
consecutive pair. The generator still requires a nonempty proper overlap and
rejects pairs on which another command transform yields the same answer.

A source-bound production census materialized 300 lessons (100 per band), 1,500
pairs, and 1,495 unique inputs with zero materialization errors, hook warnings,
scoring errors, or named-rival ambiguities. Across all 1,500 single-pair query
rotations, no declared rival became ambiguous, but 900 rotations correctly
triggered the stronger lesson hook because holding out a unique command leaves
that query command undemonstrated. Therefore the supported assembly is the
ordered production policy, not arbitrary query rotation. Evidence:
`checks/lesson-census-final.json` and its compact companion.

## Verification and remaining limits

- Final after battery: 12/12 green; 60/60 exact profile hits; 600/600 strict
  semantic draws; 2,250/2,250 override draws accepted with zero findings.
- Rule smoke: 120/120 applications, 61 distinct outputs, no crashes, identity
  cases, mutations, or out-of-bounds outputs.
- Fresh post-repair visible-only solve: 4/4 examples on the first revision;
  prior generator exposure was declared honestly.
- Named-rival and finite-sample checks do not prove universal identifiability.
- Connectivity intentionally narrows training morphology relative to the broad
  authority grammar, but exactly matches the stable canonical morphology.

Imported associated notes remain in `evidence/associated_notes.jsonl` and were
used only as historical leads, not as fresh measurements.
## Current reviewer considerations

Source SHA-256: `dad8ada5831256eda6eae7ce0db53fe4f0fc14e813bb77633303f94cae13429b`.

# Decisions — 2b6886e6e1b3

Final generator: VERSION `4.1.0`, SHA-256
`dad8ada5831256eda6eae7ce0db53fe4f0fc14e813bb77633303f94cae13429b`.
Selected Racket authority and `RULE_HASH 860b011c178c` are unchanged.

## D1 — Treat connectivity as a teaching-distribution invariant

- **Prior choice:** v4.0.0 sampled any five of nine panel cells.
- **Original rationale:** Unknown; likely maximal combinatorial variety and a
  simple implementation.
- **New choice:** Sample each panel from all 49 four-connected five-cell subsets
  of a 3×3 grid and require connectivity in `strict_canonical_like`.
- **Evidence:** All 10 canonical panels are connected. A fixed replay of 1,000
  draws per band found both panels connected in 185 easy, 127 medium, and 98
  hard baseline draws; after repair it is 1,000 in every band
  (`checks/morphology-census.json`).
- **Alternative rejected:** Keep arbitrary masks and merely increase the chance
  of connectivity. That would retain a large morphology mismatch and make
  canonical-looking lessons rare rather than guaranteed.
- **Overfitting alternative rejected:** Require a specific edge span, symmetry,
  endpoint count, or exact canonical polyomino. The canonical set is too small
  to justify those restrictions.
- **Failure mode/limit:** The authority can process disconnected motifs. To
  avoid changing the task grammar, `self_check` remains broad and only the
  strict training profile is connected.

## D2 — Keep the command schedule and overlap semantics unchanged

- **Choice:** Preserve the four-step command cycle, nonempty proper overlap,
  and pairwise transform-disambiguation condition.
- **Probe:** Existing exhaustive focused tests cover every cyclic start, three
  bands, multiple seeds, and all 16 `(cmd, overlap_size)` combinations.
- **Reason:** These mechanisms already teach all command meanings in the
  intended four-demo ordered lesson and refute the declared fixed-transform,
  copy, and union rivals.
- **Rejected alternative:** Rework the schedule to make every one-of-five query
  rotation retain all four commands. With only four demonstrations and four
  command labels, arbitrary single holdout support is impossible unless the
  lesson grows materially; the production assembler does not require it.
- **Limit:** Only the ordered production query policy is supported. The larger
  census records 900 hook warnings among 1,500 arbitrary rotations.

## D3 — Enforce literal call and override types

- **Prior choice:** `gen_ctx.draw_int` coerced booleans, floats, and numeric
  strings; schedule helpers also called `int()` on seed/index; unknown
  difficulties fell into a default range.
- **New choice:** Require `type(seed) is int`, `type(sample_index) is int`,
  `sample_index >= 0`, and difficulty in the four supported values. Use
  `draw_int_strict` for explicit `cmd` and `overlap_size` overrides.
- **Evidence:** The baseline defect lint reported 96 strict-scalar warnings.
  Separate red tests reproduced coercible overrides, invalid difficulties, and
  invalid seed/index values before each minimal repair. Final defect lint is
  green and the portable suite is 29/29.
- **Alternative rejected:** Continue coercion for convenience. It creates
  collisions such as booleans acting as integers and silently changes requested
  values, undermining deterministic replay and metadata truthfulness.
- **Limit:** Default internally selected integers still use ordinary bounded
  draws; strictness is required only at public inputs and explicit controls.

## D4 — Repair the task test’s portable data access

- **Prior choice:** The test guessed a source-tree parent depth and imported a
  repository-only script helper.
- **New choice:** Resolve roots and canonical data through
  `reviewer_support.find_root`, `canonical_path`, and `canonical_pairs`.
- **Evidence:** The first portable task-test run failed during collection on the
  unavailable path/helper. After the migration, the same canonical pin/pair
  assertions and all new regressions run in the isolated portable runtime.
- **Alternative rejected:** Rewrite or suppress the inherited canonical test.
  The assertions are valuable; only their location assumptions were defective.
- **Limit:** The test computes the normalized canonical hash directly rather
  than asserting task-specific archival metadata that is not part of the
  portable public contract.

## D5 — Do not change the Racket rule

- **Reason:** The selected authority already expresses the intended command
  transforms and matches all canonical labels. Generator morphology and Python
  call contracts—not rule semantics—caused the observed defects.
- **Probe:** `rule_smoke`, `racket_lint`, and `authority_sync` are green; both
  selected and archival executable forms solve 4/4 train and 1/1 test pairs.
- **Rejected alternative:** Edit Racket to require connected masks. That would
  conflate a training-distribution decision with executable authority and alter
  a correct task.

## D6 — Preserve failed iterations as evidence

The first focused defect-lint repair exposed additional scalar categories only
after the earlier category was closed. Red/green task-test directories and the
intermediate failed after battery remain under `checks/`. These are evidence of
the actual debugging sequence, not final verdicts; final claims use
`checks/after-final` and the final source hash.

## D7 — Use associated notes only as leads

Historical notes in `evidence/associated_notes.jsonl` were not treated as fresh
measurements. All reported counts in this return come from commands run on the
current packet or from a reproducible comparison with the original packet bytes.
