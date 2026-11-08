# Working notes: d8b498586958

## 2026-10-03 repair

Baseline generator SHA-256:
`19cf12d490ff4afc902de9af1b05fe2160b6aebea1849334e33ce15fbc1e901b`.
Selected v3.0.0 generator SHA-256:
`b5f72638b960c96622d4740f095d12eb103fb2a386c8ce6c84fbbb1489e48f4c`.
The Racket authority and `RULE_HASH=10616a474432` were not changed.

The baseline exposed a false control surface: dead palette/texture knobs,
impossible count overrides, unobservable exact axes, accepted unknown keys, and
no executable semantic contract. The repair replaces that surface with six
independent observable axes (`panel_side`, `operation`, three disjoint support
counts, and `b_color`) whose full Cartesian domain is constructive.

Every generated operand pair has nonempty shared, A-only, and B-only support.
Four consecutive examples cover union, intersection, XOR, and A-minus-B.
`SEMANTIC_RIVALS`, `CANONICAL_SHORTCUTS`, branch witnesses, and
`lesson_identifiable` make the teaching claim executable.

The strongest canonical-demo shortcut is `column_only_header`: ignore the marker
row, treat left as union and right as intersection. It fits both canonical train
pairs and fails the bottom-left XOR query. See
`checks/question-shortcut/counterexample.json`.

`workspace/lesson_window_probe.py` checks all declared rivals across cyclic
production starts. The documented four-demo-then-next-query policy passed 1,536
lessons in the retained run. Arbitrarily rotating a five-pair window is not
supported: it can withhold the only demonstration of one operation, allowing a
branch-local alias to survive. That boundary is recorded rather than hidden.
## Current reviewer considerations

Source SHA-256: `b5f72638b960c96622d4740f095d12eb103fb2a386c8ce6c84fbbb1489e48f4c`.

# Decisions — d8b498586958

## D1 — Replace the baseline control surface

**Decision.** Remove the baseline palette-size, distinct-color, density,
position-bias, and texture controls and replace them with six pixel-observable
axes: panel side, operation, three disjoint support counts, and B color.

**Why.** The before battery measured dead textures, unprobed single-token axes,
unobservable exact controls, impossible advertised counts, omitted provenance,
and accepted unknown keys. Preserving those names while special-casing the gate
would leave the underlying API dishonest.

**Rejected alternative.** Keep every legacy axis and add compatibility aliases.
That would preserve no useful curriculum behavior and would multiply invalid
combinations. There is no downstream approval to protect: the task is not
approved, and the Racket authority—not the generator control names—is the stable
contract.

**Probe.** `checks/after/checks/d8b498586958_after_override.log` exercises 381
override cases across three bands and reports 34,290 accepted draws with zero
findings. `tests/test_generator.py` also checks every exact axis, unknown keys,
type errors, and boundaries.

## D2 — `panel_side` is 4..9

**Decision.** Generalize square operand/output side length from canonical 5 to
4..9, with deterministic per-band schedules:

- easy: `(5,4,5,6)`;
- medium: `(5,6,5,7)`;
- hard: `(5,7,8,9)`.

**Why.** Side length is a true nuisance. The range changes geometry without
changing the Boolean rule, includes canonical side 5 in every four-draw lesson,
and gives hard examples materially larger search spaces.

**Rejected alternatives.** Fixed side 5 would overfit canonical dimensions.
Random independent size per pair could correlate with operation in small
lessons and could miss the profile floor. The fixed schedules are inspectable
and guarantee canonical support.

**Failure mode.** A consumer that treats side as part of the operation key could
still overfit finite samples. Repetition of side 5 at multiple operation slots
and the cross-band schedule reduce that cue; no finite generator can prove its
absence universally.

## D3 — Four-operation schedule

**Decision.** Set `operation=(seed+sample_index) mod 4` and
`EXAMPLES_NEEDED=4`, so every consecutive four demonstrations contain union,
intersection, XOR, and A-minus-B exactly once.

**Why.** The canonical train set demonstrates only union and intersection. A
row-ignoring shortcut therefore predicts union for the bottom-left query. A
complete four-example teaching block refutes branch aliases before the query.

**Rejected alternatives.** IID operation draws can omit one or more meanings in
a lesson. Three demonstrations cannot guarantee all four meanings. Increasing
lesson length beyond five violates the shared contract and is unnecessary under
the documented consecutive assembly policy.

**Failure mode / boundary.** Arbitrarily rotating a five-pair window can remove
the only demonstration of one operation. The generator does not claim support
for that assembly. `workspace/lesson_window_probe.py` reports supported
production windows and arbitrary rotations separately.

## D4 — Nonempty shared, A-only, and B-only regions

**Decision.** Independently expose each count in 1..5 and allocate three disjoint
cell sets.

**Why.** These regions are the truth-table atoms for two-set Boolean operations.
Keeping each nonempty makes all four outputs observationally distinct on every
input. With maximum total support 15, every Cartesian count combination fits the
minimum 4x4 panel.

**Rejected alternatives.** Allow zero counts as “edge cases.” A zero shared
region collapses union and XOR; zero B-only collapses union and A-minus-B; zero
A-only can collapse intersection and A-minus-B. Identical or disjoint operands
are valid mathematical cases but weak teaching examples, so they are excluded
from the ordinary training grammar rather than mislabeled as textures.

**Probe.** The focused test holds operands fixed and confirms four distinct
outputs. The semantic gate verifies every branch witness against its named
aliases.

## D5 — B color is a nuisance, held constant within a lesson

**Decision.** Use B colors `{3,4,6,7}` and schedule one color for each complete
four-example block.

**Why.** The rule depends on occupancy, not B's color. Holding color constant
inside a lesson prevents it from identifying operations; changing it across
lessons teaches color invariance. A is kept canonical color 2, separators 9,
header marker 5, and output 8 to retain recognizable grammar.

**Rejected alternatives.** A free palette-size axis was not independently
meaningful and was dead in the baseline. Changing every role color would make
canonical profile support harder without testing a distinct rule dimension.

## D6 — Strict parser and observable contract

**Decision.** Parse the complete grid grammar in `_analysis`; derive every axis
from pixels; make `self_check`, `observe_overrides`, the Python mirror, witnesses,
and rivals share that parser.

**Why.** One parser prevents the generator, validator, and semantic tools from
silently disagreeing about divider rows, marker position, colors, or support
counts. Exact overrides can now be falsified.

**Rejected alternative.** Trust generation metadata. Metadata can lie or be
lost; an exact axis is only honest if it is recoverable from the returned grid.

## D7 — Semantic rivals

**Decision.** Declare twelve branch-local operation aliases plus
`column_only_header`. Attach each operation witness to every rival that differs
on that branch and score the same rivals at lesson level.

**Why.** Marginal diversity does not prove that a lesson identifies the rule.
The aliases directly test whether each marker meaning was demonstrated. The
column-only rival is the strongest simple rule that fits both canonical training
pairs.

**Rejected alternatives.** Declare only identity/dihedral generic rivals. They
would miss the actual ambiguity in the header dictionary. Memorization rivals
were not added because the generator already varies layout broadly and a finite
list of memorized grids is not a stable task-local hypothesis.

**Limit.** These are finite declared rivals, not a proof against every possible
induction. That limitation is stated in the review and census.

## D8 — Keep the Racket authority unchanged

**Decision.** Do not modify the selected Racket rule or canonical data.

**Why.** Rule smoke, grammar, Racket lint, and authority sync already passed
before the repair. The defects were in generation, validation, and teaching
support. The Python mirror matches all three canonical pairs and the supported
Racket `apply` result used for the shortcut counterexample.

## D9 — Build reusable review tooling

**Decision.** Add `workspace/lesson_window_probe.py` rather than leaving a
one-off notebook or prose claim.

**Why.** It dynamically reads `LESSON_COMPETITORS` and
`CANONICAL_SHORTCUTS`, binds results to the generator SHA-256, audits all cyclic
production starts, and preserves concrete unsupported-rotation examples. Future
agents can rerun it after changes without copying a rival list.
