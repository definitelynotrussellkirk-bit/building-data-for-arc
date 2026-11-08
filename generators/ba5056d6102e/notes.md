# Working notes: ba5056d6102e

## Current review outcome — version 3.1.0

The imported `3.0.0` generator was already structurally strong and passed the
entire untouched 12-stage battery. A targeted semantic audit nevertheless found
one lesson-level blind spot: canonical color 3 appeared only in the bottom
panel. The wrong rule "compute the Boolean intersection unless the top
foreground color is 3; otherwise return a blank grid" therefore fit all five
canonical pairs, all 225 sampled default pairs, and all 75 sampled three-demo
lessons. Baseline generator SHA-256:
`81621f98d8c766c65237fa50e3e54f2fa5df0691b720dad5f962f7d587f413e2`.
Evidence: `checks/palette-role-baseline/shortcut-report.json`.

Version `3.1.0` uses color 3 in the top role in both `shape_shift` and
`structured` schedule slots. Because lessons consume three consecutive slots
from a four-slot cycle, every cyclic three-demo window now contains at least one
role-reversal example while preserving one canonical-support slot and
noncanonical palette evidence. The exact shortcut is declared as
`color_3_bottom_only`, with executable `top_color_3` witness metadata.

The selected authority remains pinned at `1586ec3843ec`; no Racket or canonical
row changed.

## Test-first repair record

Two new regressions were written before production edits:

1. every default three-demo window, in every difficulty band and cyclic start,
   must include color 3 in the top role;
2. the `color_3_bottom_only` rule must fit all canonical pairs, be declared as a
   shortcut/competitor, and be refuted by a lawful top-color-3 example.

Both tests failed against `3.0.0` for the expected reasons
(`checks/palette-role-tests-red-final.log`), then passed after the minimal schedule and
semantic-contract change (`checks/palette-role-tests-green-final.log`). The complete
task-local suite passed 37/37 (`checks/task-tests-final.log`).

The final source-bound Racket census materialized 100 nonoverlapping
3-demo/1-query lessons per band. All 300/300 lessons were identifiable against
all six declared competitors. Across the 1,200 generated pairs there were 1,023
exact-byte-unique inputs/pairs. In every band, `top_color_3` was present in 200
of 400 pairs and `color_3_bottom_only` was refuted by the demonstrations in
100/100 lessons. Evidence: `checks/lesson-probe-final.json`. This is a finite
census over declared rivals, not a proof of universal induction.

The final 12-stage battery passed all stages
(`checks/final/checks/ba5056d6102e_after_battery_summary.json`). The complete
repository suite also passed 237/237 through the verified Racket wrapper
(`checks/repo-pytest-racket-after.log`). The required post-repair visible-example
solve passed 3/3 examples in one revision; earlier rule exposure was declared
honestly in `solve/summary.json`.

## Rejected same-color domain extension

The Racket authority can execute a grid whose two panels use the same foreground
color. A provisional probe showed that a "solve only when colors differ"
shortcut also fits all canonical pairs and sampled default lessons. However,
the selected generator's documented domain, `SUMMARY`, `AXES`, and frozen
regression fixture explicitly require distinct panel colors and treat equal
colors as a destructive mutation. Expanding that domain would therefore be a
contract/architecture change rather than a bounded distribution repair. It was
not implemented. The failed exploratory test and Racket-backed candidate are
retained under `checks/same-color-*` and are reported as a domain question, not
as a completed fix.

## Curriculum rationale retained from version 3.0.0

- A four-slot schedule matches `EXAMPLES_NEEDED = 3`: every cyclic lesson can
  contain generalized evidence while retaining canonical support.
- Every single grid contains `00`, `10`, `01`, and `11`, so union, xor,
  top-only, and bottom-only are refuted without lucky lesson composition.
- The canonical slot uses measured public occupancy signatures instead of only
  matching dimensions/palette.
- Generalized slots vary palette, dimensions, and spatial organization. Style
  changes arrangement only; it does not change the rule domain.
- Exact numeric/color controls are observable from returned pixels.
  `support_style` is tested behaviorally because it is not uniquely recoverable
  from a single grid.
- A pinned color remains usable when it equals the scheduled color of the other
  panel; only an explicitly equal final color pair is rejected.

## Remaining limits

- The deterministic four-slot schedule is intentionally structured rather than
  IID.
- Exact-byte uniqueness does not quotient recoloring or geometric symmetries.
- The retained census covers three demonstrations and one query only.
- Only declared competitors were tested; unknown shortcuts remain possible.
- Same-color panels remain outside the selected generator contract.

Imported associated notes, if any, remain in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `96571a5f2bca605f2412422fabb268ee84246d0dc1e789d30d58945a1bb92b6c`.

# Decisions for `ba5056d6102e`

## D1 — Treat palette-role asymmetry as the bounded repair

**Input choice.** Preserve the existing distinct-color panel grammar, but ensure
canonical color 3 appears in the top panel as well as the bottom panel.

**Original rationale.** Version `3.0.0` intentionally varied palette, shape, and
texture, and it already refuted occupancy rivals inside every individual grid.
Its missing dimension was not general palette diversity; it was ordered
value-by-role coverage. Color 3 was legal in `AXES` for either foreground role
but absent from the top role in every default profile.

**Probe.** The baseline `color_3_bottom_only` shortcut fit 5/5 canonical pairs,
225/225 sampled pairs, and 75/75 sampled lessons
(`checks/palette-role-baseline/shortcut-report.json`).

**Alternatives considered.**

- Randomize top/bottom colors independently. Rejected because finite random
  lessons can still miss the discriminating role assignment and make CI flaky.
- Put color 3 in only one of four slots. Rejected because one cyclic
  three-example window would exclude that slot.
- Broaden all palette slots aggressively. Rejected as unnecessary distribution
  churn; the defect had a one-axis counterexample.

**Failure modes and limits.** The deterministic repair guarantees the witness
for three-demo lessons only. Different episode lengths need separate schedule
analysis. Role coverage does not rule out unrelated shortcuts.

## D2 — Use two schedule slots for the role reversal

**Input choice.** `shape_shift` and `structured` now use top color 3 in every
difficulty band; their bottom colors remain distinct and varied.

**Rationale.** Any three consecutive positions in a four-slot cycle omit at most
one slot. With two role-reversal slots, every cyclic three-demo lesson includes
at least one top-color-3 example, including wraparound starts. Retaining the
`canonical_like` and `palette_shift` slots preserves public support and the
existing noncanonical-palette witness.

**Probe.** The new regression enumerates starts `0..7` for every difficulty band
and fails if any three-example window lacks the role reversal. It failed before
the schedule change and passed after it.

**Alternative.** Use color 3 in all generalized slots. Rejected because two
slots are sufficient and retain more palette variety.

**Failure modes and limits.** The schedule is structured, so frequency statistics
should not be interpreted as IID sampling. The lesson census records exact
schedule residues to make that limitation visible.

## D3 — Represent the discovered shortcut explicitly

**Input choice.** Add `color_3_bottom_only` to `SEMANTIC_RIVALS`,
`LESSON_COMPETITORS`, and `CANONICAL_SHORTCUTS`, plus witness `top_color_3`.

**Rationale.** A curriculum claim is reusable only when the wrong rule is
executable and the intended evidence is machine-checkable. The rival is not a
straw man: it fits every canonical pair and the entire sampled baseline.
Declaring it lets the existing source-bound lesson probe audit future edits
without copying a hard-coded rival list into the tool.

**Probe.** The regression first verifies that the rival fits all canonical pairs,
then constructs a lawful `top_color=3` input and verifies disagreement with an
independent intersection oracle. The final Racket census confirms lesson-level
refutation.

**Alternative.** Add only a marginal assertion that top color 3 appears. Rejected
because occurrence alone does not demonstrate that the complete lesson refutes
the rival.

**Failure modes and limits.** Declared rivals are finite. Passing them does not
prove a human or model cannot infer another shortcut.

## D4 — Preserve the Racket authority

**Input choice.** No change to canonical data or Racket rule; keep
`RULE_HASH = "1586ec3843ec"`.

**Rationale.** The authority correctly computes occupancy intersection for the
new role assignment. The defect was exclusively in which lawful inputs were
shown. Changing the rule would have expanded risk without addressing the data
blind spot.

**Probe.** Final `rule_smoke`, `racket_lint`, and `authority_sync` all pass in the
12-stage battery. The lesson probe reports the selected normalized rule hash.

**Alternative.** Encode palette-role normalization in Racket. Rejected because
palette identity is already irrelevant to the authority.

**Failure modes and limits.** Authority correctness is established only over the
canonical checks and sampled generated inputs exercised by the battery/probe.

## D5 — Do not expand to same-color panels in this bounded review

**Input choice.** Keep top and bottom foreground colors distinct.

**Rationale.** A same-color candidate is executable by the Racket authority and
would refute another canonical-fitting shortcut. However, equal panel colors are
explicitly outside the selected generator's `SUMMARY`, `AXES` compatibility
rules, and frozen regression fixture. Changing that would alter the task-domain
contract rather than repair a missing combination inside the current contract.

**Probe.** `checks/same-color-baseline/racket.json` confirms authority execution;
`checks/same-color-baseline/shortcut-report.json` records shortcut survival;
`checks/same-color-tests-red.log` records the exploratory conflict with the
frozen contract.

**Alternatives considered.**

- Silently allow same colors. Rejected because it would invalidate inherited
  tests and make panel identity less directly observable.
- Modify the frozen baseline fixture. Forbidden by the assignment and wrong for
  a bounded review.
- Ignore the finding. Rejected; it is retained explicitly as a domain question
  for a future architectural review.

**Failure modes and limits.** A model can still learn "panel colors must differ"
because that is true of this generator domain. Whether the broader authority
should define a larger domain remains unresolved.

## D6 — Reuse the existing source-bound lesson probe

**Tool choice.** Do not create a second rival-specific probe. Extend the
generator declarations and let `workspace/lesson_probe.py` discover the new
rival/witness dynamically.

**Rationale.** The existing tool already stages final source, uses the selected
Racket authority, audits complete lessons, records hashes and seed policy, and
iterates declared competitors. A duplicate tool would risk semantic drift and
hard-coded rival names.

**Probe.** The unchanged probe discovered `color_3_bottom_only` automatically
and reported its canonical fit and per-band lesson refutation in
`checks/lesson-probe-final.json`.

**Alternative.** Add a palette-only census script. Rejected because marginal
color counts are weaker than complete-lesson competitor survival.

**Failure modes and limits.** The probe covers 3-demo/1-query episodes and
exact-byte uniqueness only. It does not quotient symmetry or prove general
identifiability.

## D7 — Keep tests local and test-first

**Test choice.** Add `tests/test_palette_role_curriculum.py` without modifying
the frozen inherited `tests/test_generator.py` fixture.

**Rationale.** The assignment explicitly freezes the baseline fixture. A
separate regression file makes the new defect and expected behavior auditable.
Both tests were observed failing for the intended reason before production
changes.

**Probe.** Red and green logs are retained; the complete selected-task test
folder passes 37 tests.

**Failure modes and limits.** Bare repository pytest does not discover generator-
local tests, so the explicit command must remain in `RESULTS.json` and workspace
documentation.

## Native overlap recovery — current review
The new task-local family preserves the exact intersection default and adds recover_top: largest connected overlap -> containing top component -> full object reconstruction. Production is unchanged, including its distinct-color domain. Implementation sequence was literal-oracle/contract tests first, native construction, adversarial teaching repair, bounded count/Racket audit, then manifest/qualification and causal replay. The 29x30 maximum is structural: equal panels plus one divider have odd height.

Two source-program-backed shortcuts fit both initial demos and failed queries: first-three top objects and six-cell-only recovery. The repaired second demo keeps the two-demo minimum but adds a fifth-parent winner and seven-cell connected overlap. Minimal before/after protected labels and the unchanged offending queries are retained in workspace/parametric/evidence/current. The prior review-index needs_triage entry reports no issue in its checked production scope; this native return does not relabel or resolve that historical record. Finite rival/seed evidence and author self-review only; owner exact-source acceptance and training admission remain pending.

Final staged tests: 55/55 after resolving the audit tool's library-versus-flat-runtime path assumption. The same-checkout guard remains active. The initial 54-pass/1-fail receipt is retained. Final audit: 800 count/setting requests, 200 unique scenes, 132 protected authoring evaluations; two teaching regressions and 16 D4 cases passed separately. A nonfatal test-path heuristic warning remains; no runtime path failure remains.
