# Working notes: 764b6b9e7771

## 2026-10-04 review

### Baseline finding

The selected baseline generated mirrors and walls mostly independently of the
beam. Therefore its nominal reflection task often taught only “draw a straight
ray from red through blue.” The public contract also advertised ineffective or
untruthful controls: the before battery failed lint, defect lint, override, and
authority synchronization. See
`checks/before/checks/764b6b9e7771_before_battery_summary.json` in the review
return.

### Selected construction

Version `4.0.0` uses a two-cell-per-leg serpentine. It deliberately routes the
beam through **all** requested mirrors, then either gives the final leg at least
two visible cells before the edge or places the requested connected wall on that
leg. A compact placement-family representation stores a rectangle of legal
source positions instead of enumerating every concrete placement. This keeps
the full override Cartesian product tractable without changing the generated
pixel semantics.

The relative turn schedule is `R,R,L,L,...` (or its mirrored form). A first
repair that made exactly two mirrors relevant passed its declared checks but
introduced a stronger shortcut: “apply the correct rule only at the first two
mirrors.” New failing tests exposed that defect; the final schedule supports two
to six interacting mirrors and mixes turn sides from three mirrors onward.

### Exact controls

- `grid_h`: every integer `9..18`
- `grid_w`: every integer `12..20`
- `n_mirrors`: every integer `2..6`
- `n_walls`: every integer `0..6`
- `direction`: `up|down|left|right`
- `turn_side`: `left|right`

All controls are recoverable from returned pixels through `observe_overrides`.
Unknown keys, invalid difficulty values, wrong types, and out-of-range values
fail closed. The exhaustive local geometry probe found support for all 25,200
axis tuples, with at least 30 concrete placements for the tightest tuple.

### Teaching contract

The five declared rivals all fit every canonical pair:

1. ignore mirrors and walls and continue straight;
2. stop at the first mirror or wall;
3. swap the meanings of mirror colors 4 and 6;
4. reflect only at the first two encountered mirrors;
5. repeat the first relative turn at every mirror.

`all_mirrors_interact` and `mixed_turn_route` are executable witnesses. The
default mirror-count cycle and `EXAMPLES_NEEDED = 3` make every consecutive
three-demo window refute all five rivals. `lesson_identifiable` checks that
finite set; it is not a proof against every possible induction rule.

### Rule authority

No canonical Racket behavior changed. The base authority record had two
semantically equivalent text copies; its selected `target_code` was synchronized
byte-for-byte to the already authoritative raw/canonical program. The after
battery reports execution parity and exact synchronization.

### Verification snapshot

Final generator SHA-256:
`3f2d2c7dd3b1ad50c433bd9f1d7f6e9714e353f722c90485a5211bc8b1b239ab`.
The final battery is 12/12 green, portable task tests are 79/79, and the
300-lesson census materialized 100 lessons per difficulty band with zero
declared-rival ambiguity and 1,200 unique inputs. Exact commands and retained
evidence are recorded in the packet-level `RESULTS.json`.

### Limits

The generator intentionally favors a compact serpentine family rather than all
possible mirror mazes. The deterministic mirror-count schedule is a teaching
choice, not a claim about the natural task distribution. The validator remains
broader than the generated curriculum so canonical lawful examples still pass.
## Current reviewer considerations

Source SHA-256: `3f2d2c7dd3b1ad50c433bd9f1d7f6e9714e353f722c90485a5211bc8b1b239ab`.

# Decisions for 764b6b9e7771

All final implementation decisions bind to generator version `4.0.0`, SHA-256
`3f2d2c7dd3b1ad50c433bd9f1d7f6e9714e353f722c90485a5211bc8b1b239ab`.

## D1 — Keep the canonical Racket behavior

**Original state.** The canonical examples and retained Racket program already
encode a coherent beam simulation. The before rule-smoke stage passed.

**Decision.** Do not change the canonical row or algorithm. Pin normalized
`RULE_HASH = b28f2ec65f40`. Synchronize only the selected base record's
`target_code` text to its authoritative `raw_code`/canonical source.

**Alternative rejected.** Changing the rule to match the weak baseline
distribution would redefine the task rather than repair its curriculum.

**Probe.** Before/after rule smoke and authority sync; final execution parity is
`PASS` and the selected copies are synchronized.

**Failure mode / limit.** Textual synchronization changes a base JSON file even
though behavior does not change. The review states this explicitly so it is not
mistaken for a semantic rule edit.

## D2 — Replace random dead obstacles with a constructive live route

**Original rationale.** Unknown; baseline documentation said mirrors and walls
“vary freely,” but did not establish that they affected the beam.

**Decision.** Build a compact serpentine in which every requested mirror is
encountered. Put any requested wall on the final ray.

**Alternatives considered.** (a) Keep random placement and rejection-sample until
some obstacle is hit; (b) guarantee one mirror but leave the rest decorative;
(c) construct the entire route. Option (c) gives exact observability, deterministic
coverage, and much simpler semantic evidence.

**Probes.** Independent trace tests, 600-draw semantic gate, all-axis support,
and the 300-lesson census.

**Failure modes / limits.** Constructive routes are less geometrically diverse
than unconstrained random mazes. The compact family is intentionally a teaching
curriculum, not a natural-distribution claim.

## D3 — Make all six public axes exact and fail closed

**Decision.** Retain only axes whose requested value is visible in returned
pixels: height, width, mirror count, wall count, launch direction, and first turn
side. Validate difficulty, keys, types, and ranges; reject unknown keys.

**Alternative rejected.** Keeping the baseline `texture`-like behavior or broad
metadata that cannot be recovered from pixels. Metadata-only controls are not an
exact generator contract.

**Probes.** `observe_overrides`, 79 task tests, battery override stage, and the
25,200-tuple exhaustive candidate-layout probe.

**Failure modes / limits.** `turn_side` describes the first relative turn, not a
fixed mirror color. Mirror color depends on incoming orientation; tests cover all
eight direction/turn combinations.

## D4 — Support 2–6 interacting mirrors

**Intermediate state.** Version 3.0.0 placed the requested number of mirror pixels
but made only two relevant to the beam. It refuted the original straight/stop/swap
rivals but admitted `first_two_mirrors_only`.

**Decision.** Route through every requested mirror and test maximum count under
all difficulty bands.

**Alternatives rejected.** Declare `n_mirrors` as decorative count, or cap it at
two. Both preserve a false teaching contract and reduce the intended task.

**Probe.** `checks/red-multimirror-task-tests.log` failed before implementation;
final task tests and `all_mirrors_interact` pass.

**Failure mode / limit.** A finite maximum of six remains part of this generator's
contract; it does not test arbitrarily long paths.

## D5 — Mix relative turn directions for 3+ mirrors

**Decision.** Use `R,R,L,L,...` or its mirror. This keeps a compact non-crossing
snake while ensuring both relative turn senses occur from the third mirror onward.

**Alternatives considered.** Alternate every turn (`R,L,R,L`) and repeat one side
forever. The first can self-intersect in the two-cell geometry; the second admits
`repeat_first_turn_side`. Pairwise runs are compact and expose the rival.

**Probes.** `mixed_turn_route`, the `repeat_first_turn_side` rival, exact question
counterexample, and the final lesson census.

**Failure mode / limit.** The pattern is deterministic and potentially learnable.
It is sufficient to teach mirror semantics, not intended as a random-walk model.

## D6 — Use a three-demo lesson schedule

**Decision.** Set `EXAMPLES_NEEDED = 3` and cycle default mirror count through
`2,3,4,5,6` by sample index. Every consecutive length-three window contains at
least one 3+ mirror case, while every individual case refutes the core three
rivals.

**Alternatives considered.** Pure random mirror count, or require every individual
example to expose every rival. Random scheduling can produce ambiguous lesson
windows; requiring every example to do everything reduces diversity and makes
two-mirror cases unavailable.

**Probes.** Test every consecutive three-demo window over a full schedule and run
100 source-bound lessons per band.

**Failure mode / limit.** The shared census does not rotate every pair through the
query position. Task-local consecutive-window tests cover all small schedule
starts, but this is still a finite-rival claim.

## D7 — Represent placements as compact families

**Decision.** Cache tuples of wall geometry plus inclusive source-position
rectangles, then sample uniformly over concrete positions across those families.

**Original implementation considered.** Enumerating every concrete start/wall
placement was correct but made the exhaustive override matrix unnecessarily slow
and memory-heavy.

**Probe.** The refactor preserved all 79 tests and supports all 25,200 tuples; the
smallest family still has 30 concrete placements.

**Failure mode / limit.** Correctness depends on the rectangle bounds faithfully
representing every translated route cell. Tests compare observed pixels and trace
results, not merely family metadata.

## D8 — Keep the validator broader than the curriculum

**Decision.** `self_check` accepts lawful canonical inputs even when their beam
does not interact with every obstacle. Strong interaction requirements live in
generation tests and semantic witnesses.

**Alternative rejected.** Tighten `self_check` to the selected curriculum. That
would reject canonical demonstrations and confuse lawful rule domain with training
schedule quality.

**Probe.** All canonical inputs pass strict profile/self-check; generated samples
satisfy the stronger witnesses.

**Failure mode / limit.** Passing `self_check` alone does not establish that an
input is educationally useful.

## D9 — Declare five concrete canonical-fitting rivals

**Decision.** Register `straight_to_edge`, `stop_at_first_obstacle`,
`swapped_mirrors`, `first_two_mirrors_only`, and `repeat_first_turn_side` in all
relevant rival registries. Associate the first three with `all_mirrors_interact`
and the last two with `mixed_turn_route`.

**Alternative rejected.** Rely only on generic image transforms or on the three
rivals noticed initially. The intermediate repair demonstrated that undeclared
algorithmic cutoffs can survive declared checks.

**Probe.** Each rival is verified to fit all five canonical pairs and to disagree
with generated authority outputs; every final lesson refutes each one.

**Failure mode / limit.** This registry is not exhaustive. Future reviews should
continue adversarially inventing rivals rather than treating a green finite set as
proof.

## D10 — Add an independent reusable observer

**Decision.** Put `workspace/reference_probe.py` beside, not inside, production
code. It independently traces beams, observes controls, and implements rivals.

**Alternative rejected.** Have tests call production `_trace_report` for every
assertion. That would allow a shared bug to make generator and test agree.

**Probe.** Portable task-test snapshot copies both source and workspace and reports
79 passing tests.

**Failure mode / limit.** The probe intentionally reads canonical data in tests;
it is prohibited during visible-only solve episodes and is documented as such.
