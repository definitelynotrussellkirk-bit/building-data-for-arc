# Current notes: `5a8d42591332`

## Intended rule and authority

Fixed 11×11 count-comparison matrix. Three color-1 2×2 headers across the top
and three color-2 2×2 headers down the left encode counts 1–4. Fill each matching
body block with 4 for top>left, 3 for left>top, and 8 for equality. Semantic
colors and coordinates are rule-intrinsic. Selected `RULE_HASH=4c53ca03668e` is
unchanged.

## Final generator decision (v2.2.0)

- Exact axes: `relation_balance`, `min_count`, `header_layout`.
- Strictly reject coercible/negative `sample_index` and coercible invalid
  overrides before generation context creation.
- Every ordinary draw contains all comparison outcomes and every count from
  `min_count` through 4.
- Counts 2 and 3 occur on opposite axes.
- Compact headers preserve canonical morphology. Diagonal and reverse headers
  make counts 2 and 3 share a row-major-prefix score, so either noncompact input
  independently refutes the canonical-fitting `row_major_prefix_count` rival.
- Three consecutive examples always include a noncompact witness; all four
  possible query rotations of production lessons retain a witness.

Final generator SHA-256: `9c79cbe3eda497bf6b51e6c48b671f2b7d0e3d0f3fdd12f427c7a211bcf09963`.

## Reversed decision

Intermediate v2.1 used full count support plus mixed layouts, but 19/1,200
held-out-query rotations in the 300-lesson census still admitted the prefix
rival. The final design replaced probabilistic/order-preserving noncompact
patterns with equal-prefix-score count-2/count-3 patterns. Exact prior failure:
`counterexamples/row_major_prefix_ambiguous_lesson_before.json`. Exact final
emitted witness: `counterexamples/row_major_prefix_witness_after.json`.

## Verification

- Before: 11/12 battery gates green; defect-lint reported eight strict-scalar
  warnings.
- Final: 12/12 battery gates green.
- Focused portable reviewer test: 13 passed.
- Strict semantic gate: 600/600 strict draws; required rotations clean.
- Production census: 300 lessons, 1,200 rotations, zero declared-rival
  ambiguity, 1,084 unique inputs.
- Racket authority apply confirms the final prefix witness at four cells.

## Known limits and open item

Finite rival/census checks do not prove universal identifiability. Grid shape,
coordinates, and colors remain fixed by authority. The required portable
`task_tests` preset is blocked by the immutable baseline root fixture’s legacy
import and fixed-depth canonical path; the new task-local test itself passes.
Maintainer/tooling should migrate or separately classify that frozen fixture.

Associated historical notes were used only to preserve fixed-shape, semantic
color, and authority-sync constraints; no prior return supplied current
measurements.

## Current portable-fixture decision

The accepted reviewer repair reported `task_tests` blocked by the inherited frozen fixture; that original result remains reviewer evidence. The owner reproduced its missing fixed-depth canonical path, then migrated the fixture to the public `reviewer_support` helpers without changing test assertions, generator bytes, or rule. The copied-runtime stage now passes **73 tests, 0 failures/errors/skips**, with no import diagnostics. Source-bound retained proof: [fixture-migration-current.json](evidence/fixture-migration-current.json); it binds the original owner before/after receipts and copied runtime. Future reviewers receive the migrated baseline. This is a task-test result, not a new twelve-stage battery or universal semantic qualification.
## Current reviewer considerations

Source SHA-256: `9c79cbe3eda497bf6b51e6c48b671f2b7d0e3d0f3fdd12f427c7a211bcf09963`.

# Decisions — `5a8d42591332`

## D1: Preserve the fixed 11×11 authority grammar

**Choice.** Keep the canonical geometry, semantic colors, body coordinates, and
Racket rule unchanged (`RULE_HASH=4c53ca03668e`).

**Original rationale.** Associated note `GNOTE-003653` records that all canonical
pairs and the selected authority use fixed starts 3, 6, and 9; prior 12×12 space
was dead, not rule-supported variation. `GNOTE-003654` records that colors 1/2
are role-bearing and 3/4/8 encode ordered outcomes.

**Alternatives rejected.** Grid resizing, palette permutation, decorative body
texture, or a rule rewrite.  Each would either leave unused space, destroy
semantic roles, or expand the task beyond the selected authority.

**Probe and failure mode.** Final rule smoke and authority sync passed.  The
remaining limitation is intentional: this generator is structurally diverse
within a fixed 11×11 grammar, not scale- or palette-covariant.

## D2: Validate controls before creating the generation context

**Choice.** Require `type(sample_index) is int`, nonnegative value, literal
integer `min_count` in `{1,2}`, and literal valid strings for categorical axes.
Use `draw_int_strict` for the advertised exact integer control.

**Prior choice.** The baseline relied on `int(...)` schedule coercion and the
non-strict integer draw helper.  Its rationale is unknown; the observable result
was acceptance of booleans, floats, strings, and a negative index.

**Alternatives rejected.** Coercing values, validating only after `gen_ctx`, or
silencing the defect-lint warnings.  Those preserve aliasing and make replay
identity depend on accidental Python coercions.

**Evidence.** The before battery reports eight strict-scalar warnings; the final
battery is green and focused parameterized tests cover all eight cases.

## D3: Treat `row_major_prefix_count` as the primary canonical shortcut

**Choice.** Declare it in `CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, and
semantic witness metadata.  It counts only the occupied row-major prefix of each
2×2 header, then performs the same comparisons as the intended rule.

**Rationale.** It fits every canonical pair exactly and shares the intended
rule’s local comparison structure, making it more plausible than fixed-label or
global-output rivals.

**Probe.** Canonical fit is tested through `reviewer_support.canonical_pairs`.
The baseline exact ambiguous lesson is retained under `counterexamples/`, and
the final emitted disagreement is independently checked with Racket.

**Limitation.** This is the strongest shortcut found, not a proof that no more
complex canonical-fitting rival exists.

## D4: Reject the initial “mixed layouts plus full support” repair

**Prior choice (v2.1).** Make every draw include every count from `min_count`
through 4, cycle compact/diagonal/reverse layouts, and require at least one
prefix-rival witness in ordinary three-example windows.

**Why reversed.** A 300-lesson production census found 19 ambiguous query
rotations among 1,200.  Some noncompact count patterns changed prefix values but
preserved the true ordering, so one reverse-layout example could remain the only
decisive witness. Holding that example out reopened the shortcut.

**Rejected alternative.** Merely increase random witness frequency or resample
ambiguous lessons.  That would be probabilistic and position-dependent.

**Evidence.** `checks/lesson-census-v1-failure-summary.json` and the exact first
regression at easy seed 699585569, samples 1–4.

## D5: Make every noncompact example independently decisive

**Choice (v2.2).** Require counts 2 and 3 on opposite axes.  Give them equal
row-major-prefix scores in each noncompact family:

- diagonal: count 2 = top-left + bottom-right; count 3 = top-left + bottom-left + bottom-right (both prefix score 1);
- reverse: count 2 and count 3 both begin away from top-left (both prefix score 0).

**Rationale.** Comparing true counts 2 and 3 must produce 3 or 4, whereas the
shortcut sees equality and produces 8.  The layout cycle makes every consecutive
three-example lesson contain at least one noncompact example, and every held-out
rotation of a four-pair lesson retains at least one such witness.

**Alternatives rejected.** Remove compact examples entirely, hard-code a single
witness vector, or inspect/resample outputs after generation.  The chosen design
keeps canonical fidelity, exposes broad count vectors, and is deterministic at
the input-grammar level.

**Evidence.** Focused cyclic-window tests, exact census regression, strict
semantic gate, and final 300-lesson/1,200-rotation census.

## D6: Retain compact headers as a first-class layout

**Choice.** Keep `compact` alongside the two anti-shortcut layouts.

**Rationale.** Compact prefixes are the canonical presentation and preserve a
close bridge to source demonstrations.  Removing them would “solve” the shortcut
by abandoning canonical morphology rather than teaching the invariant across
morphologies.

**Failure mode guarded.** A lesson containing only compact headers would still
admit the shortcut, so the three-step schedule and cyclic-window regression are
required.

## D7: Add reviewer-owned tests without changing the frozen fixture

**Choice.** Add
`tests/test_strict_controls_and_prefix_shortcut.py`; restore the baseline root
`test_generator_5a8d42591332.py` byte-for-byte.

**Rationale.** Assignment policy explicitly marks the root fixture frozen.  The
new tests use portable public helpers and cover strict controls, support,
canonical shortcut fit, all cyclic three-example starts, each noncompact layout,
and the exact first census rotation.

**Known blocker.** The shared `task_tests` preset still preflights the frozen
fixture and fails on its legacy import/fixed-depth path.  Editing it would make
the check pass by violating the assignment, so the return is marked blocked and
requests maintainer/tooling action.

## D8: Evidence and prior-return policy

No prior return was opened or treated as current measurement.  The imported
associated-note index was used only after baseline reproduction to confirm
long-lived design constraints.  Current claims are bound to the selected
baseline, final source hashes, commands, and retained evidence in this return.

Large intermediate census evidence was reduced to a compact failure index with
the original path, byte size, SHA-256, all 19 failing rotations, and the exact
retained lesson.  The final successful census is retained in full.

## D9: Stop condition

Stop after: final battery green; strict required rotations green; 300 lessons and
1,200 rotations clean; direct focused tests green; the generated patch replayed
cleanly into a pristine packet and passed those tests again; both adversarial
audits have source-bound Racket counterexamples; blind and exposed solves are
finished.
The only unresolved required gate is the immutable frozen-fixture portability
conflict, which cannot be repaired within the permitted patch surface.
