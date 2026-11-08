# Working notes: 48732ebd41f9

## Review diagnosis

The imported generator taught a different shortcut from the canonical task:
it always carved exactly one **full-height** zero strip. Its validator also
required that shortcut, so it rejected four of the five canonical inputs. The
public override surface included branches that were unobservable, invalid, or
silently accepted. It had no pinned `RULE_HASH`, no exact canonical profile
support in the profile-floor sample, no three-color support, and no executable
semantic rivals. The selected base authority executed like the canonical rule
but stored different target source text.

The canonical selected program is not “tallest” despite its helper name. It
enumerates maximal horizontal zero runs for every row band and keeps the first
candidate of greatest **area**. Every canonical pair has a unique maximum-area
rectangle of height at least two.

## Repair choices

- Pin `RULE_HASH = 9d5297512997`; leave the canonical ledger unchanged.
- Construct a unique maximum-area target rather than filtering random grids.
- Use a four-slot schedule whose complete lesson covers all public canonical
  profiles, edge/interior targets, and binary/accent palettes.
- In the core slot, construct both a wider-but-smaller and a
  taller-but-smaller rectangle when they fit.
- Add only vertically isolated background zeros outside one-cell halos, making
  the no-accidental-rectangle argument structural rather than probabilistic.
- Advertise only exact controls that can be reconstructed from the resulting
  grid. Reject unknown or impossible combinations explicitly.
- Vary foreground identity in default training draws while retaining a
  canonical-heavy prior.
- Keep target width at least 3. A task-local regression demonstrates why a 2x2
  target is outside the supported evidence-backed manifold.
- Synchronize the selected base authority's `target_code` to canonical source
  while preserving its historical `raw_code` as archival evidence.

## TDD iterations retained

1. The first task-local semantic suite failed 15 behaviors against the imported
   generator.
2. The constructive replacement passed the focused suite and the fast gates.
3. Defect lint exposed an unsupported 2x2 impostor; target width was narrowed
   to the evidence-backed `3..8` interval and a regression was added.
4. The first exhaustive override run produced 978 findings, all from one root
   cause: a pinned short `grid_h` on the scheduled interior slot derived an
   impossible unpinned `target_h` of 0 or 1 before typed validation. Regression
   tests now require automatic adaptation to an edge target when location and
   target height are unpinned; explicit impossible interior tuples remain
   structured incompatibilities.
5. A regression then required ordinary default draws to vary rule-irrelevant
   foreground identity; exact foreground pins remain observable.

## Reusable probe

`workspace/semantic_probe.py` is source-hashed and imports the generator's
actual `CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, witnesses, schedule, and
axes. It tests 100 four-demonstration lessons per band, all four cyclic starts,
and 500 draws per band. It does not claim universal induction.

Imported associated notes remain in `evidence/associated_notes.jsonl`.

## Maintainer follow-up: 3.0.1

The replayed canonical census refutes every declared rival (full-height: 1/5, tallest: 1/5, widest: 3/5). They remain semantic/lesson competitors, but the canonical-shortcut registry is empty. The probe still measures every rival against canonical pairs. This corrects registry metadata; sampling and reference labels are unchanged. Added a canonical-fit regression test. Original return and its receipts remain immutable; fresh checks bind this follow-up.
## Current reviewer considerations (2026-10-19)

The imported `3.0.1` source SHA-256 was
`47facde8bc65c07eacf2b7be8ea33eb6ad140cb935c9a47073f47f6ce5519eeb`.
Its before battery was 11/12: defect lint emitted 33 strict-scalar warnings
because `generate` and `schedule_profile` accepted booleans, floats, strings,
`None`, and negative sample indices as replay identities. The repair validates
`seed` and `sample_index` before scheduling or RNG use. A source-bound parity
probe compared 340 lawful calls and found 340/340 byte-identical grids, so
`VERSION = 3.0.1`, `RULE_HASH = 9d5297512997`, and the Racket authority remain
unchanged. Final source SHA-256 is
`5bc7a1259c7fdb7fcee978112f9780e2cf2273eb3b68767291ddfc23fdf50c3f`.

The after battery is 12/12 green and the portable selected-task suite is 44/44
green. The task-local ordered lesson probe passed 100 lessons per band (300
lessons, 1,500 unique draws). The shared census likewise found 0/300 ambiguous
production lessons, but 225/1,500 arbitrary query rotations are ambiguous to
`tallest_only` and `widest_only`; downstream assembly must preserve the declared
four-demonstration ordering unless the schedule is strengthened.

A separate **prototype** under `workspace/parametric/` varies
`minimum_height` over `{2,3}` once per episode. Both complete episodes execute
exact Racket, use three demonstrations plus one query, and every demonstration
refutes the other threshold. It does not change production generation or
approval.

# Decisions for 48732ebd41f9

Each decision records the imported behavior, alternatives considered, the
selected choice, the probe used, and the remaining failure mode. Finding IDs
match `REVIEW.md`.

## D1 — Bind the generator to greatest area, not helper-name “tallest” (M1)

**Imported rationale.** Unknown. The imported comments and construction treated
the target as the tallest/full-height rectangle, apparently following the
historical helper name rather than reading its comparison key.

**Alternatives considered.** (a) Keep the generator and change the Racket rule
to tallest; (b) preserve the full-height construction but relabel it; (c) bind
the generator to the selected canonical program’s actual area ranking.

**Choice.** Use (c), pin `RULE_HASH = "9d5297512997"`, and independently
enumerate all solid zero rectangles with height at least two. Changing the rule
would contradict all selected authority and canonical examples; relabeling the
shortcut would still fail to teach area.

**Probe.** The independent oracle and generator mirror both reproduce 5/5
canonical outputs in `checks/48732ebd41f9_semantic_probe.json`; final rule smoke
and authority parity are green.

**Failure mode / limit.** The helper name remains historically misleading. The
summary and tests explicitly state that area is the key so a future maintainer
does not reintroduce the same inference.

## D2 — Construct a unique maximum instead of filtering random grids (M1, M2)

**Imported rationale.** The old sampler filled a random foreground then carved a
full-height strip and patched accidental ties. That was simple but encoded the
shortcut as an invariant.

**Alternatives considered.** (a) Randomly sample arbitrary grids until a unique
maximum appears; (b) retain a full-height target and add occasional exceptions;
(c) place a target and bounded named competitors by construction.

**Choice.** Use (c). Construction guarantees one intended maximum, makes
competitor relations inspectable, and avoids unbounded rejection loops.

**Probe.** Focused tests enumerate every candidate in 192 default draws (64 per
band), require one unique maximum, and compare changed-cell count with target
area. The final self-check stage validates 60 more default draws and all five
canonical inputs.

**Failure mode / limit.** Constructive geometry is less morphologically broad
than unconstrained random grids. D5 and D6 add deliberate counterexamples and
noise, but do not claim exhaustive rectangle topology.

## D3 — Use a four-slot lesson schedule (M4, M5)

**Imported rationale.** The old generator declared `EXAMPLES_NEEDED = 3` but no
schedule that guaranteed semantic coverage inside a complete lesson.

**Alternatives considered.** (a) Pure random mixture with expected coverage;
(b) stratify only by difficulty; (c) deterministic four-slot cycle containing
`canonical_core`, `interior_rivals`, `edge_rivals`, and `accent_rivals`.

**Choice.** Use (c) and `EXAMPLES_NEEDED = 4`. Every consecutive four-example
window contains every branch, and all four cyclic starts are equivalent in
coverage.

**Probe.** The focused test checks every start from 0 through 11. The source-bound
probe checks 100 lessons per band, 25 at each cyclic start, using the exact
sample-index and seed formulas recorded in its JSON report.

**Failure mode / limit.** Geometry is intentionally periodic and difficulty
bands share the same semantic schedule. Difficulty still changes keyed layout
variation, but this design prioritizes lesson identifiability over a broad
band-specific curriculum.

## D4 — Match all public canonical profiles without copying examples (M4)

**Imported rationale.** The old size ranges overlapped the broad task envelope,
but none of 60 baseline draws matched an exact canonical height/width/palette
profile.

**Alternatives considered.** (a) Copy canonical inputs; (b) add a low-probability
exact-profile lottery; (c) schedule profile dimensions while independently
constructing new contents.

**Choice.** Use (c). The four slots reproduce `(4,20,2)`, `(4,24,2)`,
`(2,20,2)`, and `(3,30,3)` while varying positions, colors, competitors, and
noise.

**Probe.** Final profile floor reports 60/60 exact-profile matches. The semantic
probe reports 125 draws of each profile in every 500-draw band sample.

**Failure mode / limit.** Exact profile balance is stronger than the canonical
frequency evidence warrants. It is a teaching schedule, not an estimate of a
natural data distribution.

## D5 — Teach three named shortcut separations explicitly (M5)

**Imported rationale.** Full-height examples made the `full_height_only` rival
indistinguishable from the intended rule. The imported generator declared no
executable rivals.

**Alternatives considered.** (a) Rely on generic diversity metrics; (b) add
unstructured random distractors; (c) construct direct witnesses against
`full_height_only`, `widest_only`, and `tallest_only` and expose executable
rivals.

**Choice.** Use (c). `canonical_core` includes both a wider-but-smaller and a
taller-but-smaller candidate when geometry permits; three of four slots use a
target that does not span full height.

**Probe.** `workspace/semantic_probe.py` imports the generator’s actual
`CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, witness map, and schedule rather
than duplicating rival names. Every rival is demonstration-refuted in 100/100
lessons per band.

**Failure mode / limit.** These rivals are deliberately small and interpretable.
They do not enumerate every symbolic program or model shortcut. A future new
rival must be added to the declarations and will then be picked up by the probe.

## D6 — Add zero noise only when it is structurally unable to form a competitor (M1)

**Imported rationale.** The old random extra blocks needed repair logic because
they could alter the target relation.

**Alternatives considered.** (a) Disable all extra zeros; (b) add arbitrary
noise and reject bad grids; (c) place isolated zeros outside target/competitor
halos with no vertical adjacency.

**Choice.** Use (c). One-row isolated zeros add local texture but cannot create a
height-at-least-two rectangle.

**Probe.** Every default generated grid is independently re-enumerated in the
focused tests and semantic probe; no tie or mirror disagreement occurs.

**Failure mode / limit.** This is intentionally conservative. It does not train
robustness to dense or overlapping zero clutter.

## D7 — Limit target width to evidence-backed `3..8` (M2)

**Imported rationale.** The old `empty_block_w` claimed `2..15`, but those bounds
belonged to the full-height shortcut rather than the canonical area task.

**Alternatives considered.** (a) retain width 2; (b) allow any width that fits;
(c) start at width 3 and cap at 8, matching canonical evidence and available
competitor construction.

**Choice.** Use (c). Strict defect lint exposed a `2x2` target as a minimal
impostor outside the canonical evidence. A focused regression now requires the
validator to reject it.

**Probe.** `test_validator_rejects_malformed_ambiguous_and_output_colored_inputs`
and final defect lint.

**Failure mode / limit.** The mathematical rule is valid for width 1 or 2, but
this generator intentionally does not claim those shapes as reviewed training
data. Expanding the domain requires new semantic and canonical-like evidence.

## D8 — Expose seven exact controls and reject everything else (M3)

**Imported rationale.** The old API mixed axes, aliases, floats, helpful and
degenerate textures, silent clipping, and values not reconstructible from the
output grid.

**Alternatives considered.** (a) preserve backward-compatible legacy names;
(b) label weak controls diagnostic; (c) replace them with exact observable
`grid_h`, `grid_w`, `fg_color`, `target_h`, `target_w`, `target_location`, and
`palette_mode` axes.

**Choice.** Use (c). Unknown keys and wrong types are errors. Exact caller pins
are never silently clipped. Unpinned defaults may adapt around a pin, and
impossible exact tuples raise structured incompatibility errors.

**Probe.** The final exhaustive matrix covers 506 cases in each of three bands
and 30 seeds per case: 45,540 draws, zero findings or warnings. `observe_overrides`
is independently checked by focused tests.

**Failure mode / limit.** `target_location` is a coarse edge/interior control,
not an exact coordinate. It is nevertheless exactly reconstructible and is the
semantic distinction needed by this schedule.

## D9 — Combine dynamic and declarative incompatibility descriptions (M3)

**Imported rationale.** None; the old generator generally clipped or ignored
conflicts.

**Alternatives considered.** (a) dynamic exception attributes only; (b) static
matrix only; (c) both.

**Choice.** Use (c). Dynamic tuples report the actual incompatible axes, while
`{"grid_h": (2, 3), "target_location": "interior"}` lets the checker classify
cases where an unpinned derived `target_h` also participates.

**Probe.** The first implementation retained under
`checks/iterations/override-derived-height/` produced 978 failures. A later
11/12 battery under `checks/after-final/` exposed 180 undeclared rejections.
The final matrix has 1,080 expected explicit rejections and zero findings.

**Failure mode / limit.** The checker’s declarative syntax is duplicated beside
the dynamic geometry logic. Regression tests assert the critical value-pair to
prevent drift.

## D10 — Vary foreground identity with a canonical-heavy prior (M7)

**Imported rationale.** Canonical inputs use foreground color 1, and the old
default often stayed close to that identity despite claiming broader support.

**Alternatives considered.** (a) always use 1; (b) uniformly sample all legal
colors; (c) weight 1 heavily while exposing every legal nonzero color except 6.

**Choice.** Use (c): five entries for 1 and one each for 2,3,4,5,7,8,9. This
keeps canonical appearance common without teaching that color 1 is essential.

**Probe.** Sixty-four medium draws must include 1 and at least four distinct
foreground identities. Exact `fg_color` overrides are checked in every band.

**Failure mode / limit.** The weights are a deliberate teaching prior, not
estimated from a larger ARC population.

## D11 — Preserve at most a three-color input palette (M4)

**Imported rationale.** The canonical set contains binary examples and one
three-color input profile.

**Alternatives considered.** (a) binary only; (b) arbitrary many colors; (c)
binary and one accent branch.

**Choice.** Use (c). `palette_mode='accent'` inserts a rule-irrelevant third
color without using reserved output color 6.

**Probe.** Every 20-draw band window includes a three-color input, and the exact
`(3,30,3)` profile appears 125/500 times per band in the semantic probe.

**Failure mode / limit.** More than three input colors are outside the reviewed
manifold even though the rule is palette-invariant.

## D12 — Synchronize selected source, preserve archival source (M6)

**Imported rationale.** The selected base record’s `target_code` and `raw_code`
were equivalent in execution but diverged textually from the canonical program.
The historical reason for the duplicate source is unknown.

**Alternatives considered.** (a) leave both divergent; (b) overwrite both; (c)
synchronize only the selected executable target and retain raw archival text.

**Choice.** Use (c). This restores exact selected-authority ownership without
erasing provenance. The canonical ledger and semantics were not edited.

**Probe.** Focused tests assert `target_code == canonical program_solution` and
`raw_code != target_code`; final authority sync reports selected synchronized,
archival divergent, execution parity PASS.

**Failure mode / limit.** Future tooling must continue treating `raw_code` as
archival rather than an active second authority.

## D13 — Build a source-bound lesson probe instead of relying on the small battery sample (M5)

**Imported rationale.** The packet explicitly warned that individual witness
frequency does not establish complete-lesson identifiability.

**Alternatives considered.** (a) trust the battery’s small semantic sample; (b)
write a one-off script with copied rival names; (c) build a reusable task-local
probe bound to source hashes and live declarations.

**Choice.** Use (c). The probe checks canonical oracle parity, all cyclic starts,
actual schedule profiles, exact observations, unique-input counts, witness
frequencies, and all declared rivals.

**Probe.** The probe itself is retained at
`repo/generators/48732ebd41f9/workspace/semantic_probe.py`; final output is
`checks/48732ebd41f9_semantic_probe.json`.

**Failure mode / limit.** Sampling 100 lessons per band is finite. The tool
reports exact seeds and denominators and makes no universal-induction claim.


## D14 — Reject ambiguous replay identities before scheduling

**Imported rationale.** Unknown. Python's arithmetic and modulo behavior let
`bool`, floats, strings in some paths, and negative indices reach scheduling or
RNG construction even though replay identity is specified as integer data.

**Alternatives considered.** (a) coerce with `int(...)`; (b) validate only in
`generate`; (c) require exact built-in integers in both public entry points and
require a nonnegative sample index.

**Choice.** Use (c). Coercion would collapse distinct caller mistakes onto the
same replay key, and validating only `generate` would leave `schedule_profile`
with a divergent contract.

**Probe.** Test-first regressions are retained in
`checks/development-red-strict-scalars.log`; the repaired suite is in
`checks/development-green-review-tests.log`. Focused defect lint and the full
after battery are green.

**Failure mode / limit.** Arbitrarily large integers remain legal. That is
intentional because the keyed hash has no finite replay-domain requirement.

## D15 — Keep version and authority unchanged after a validation-only repair

**Imported rationale.** Version `3.0.1` already described the lawful sampling
behavior and was bound to the canonical Racket authority.

**Alternatives considered.** (a) bump the version, changing every keyed draw;
(b) modify the Racket program; (c) retain both because no lawful output changes.

**Choice.** Use (c). The defect is at the API boundary, not in the task rule or
valid sampling distribution.

**Probe.** `checks/root-cause/valid-output-parity.json` compares 340 valid calls,
including overrides, and records 340/340 identical outputs before and after.
The final authority-sync stage is green.

**Failure mode / limit.** Callers that previously relied on malformed replay
keys now receive an exception. That is the intended incompatibility and is not
a generated-data change.

## D16 — Prototype a minimum-height threshold, isolated from production

**Imported rationale.** The original rule already contains a meaningful height
threshold of two; varying that threshold preserves the rectangle-search and
area-ranking reasoning while changing the executed transformation.

**Alternatives considered.** (a) output-color reskin; (b) distractor or size
sampling changes; (c) `minimum_height in {2,3}` with inputs that force different
winning rectangles.

**Choice.** Use (c). The low/wide two-row rectangle wins at threshold 2, while
threshold 3 excludes it and selects a taller, smaller-area rectangle. The value
is chosen once per episode and hidden from public challenges.

**Probe.** `checks/parametric/minimum-height-evidence.json` retains two complete
Racket-executed episodes, source/program hashes, public files, and rival checks.
The setting-2 program SHA-256 is
`cc353bac2416c32b1acb3702454a5a86b300c3190eae48d75d40895560a49c9f`;
the setting-3 program SHA-256 is
`f3b4d3e8f2f1c453c16e66483f2740998fd074186b6e77e59dee5e8f6679cd18`.

**Failure mode / limit.** This is bounded prototype evidence for two settings
and one declared parameter rival. It is not a production API, approval, or
proof against undeclared rules.

## D17 — Preserve ordered lessons; do not claim arbitrary query rotation

**Imported rationale.** The four-slot schedule was designed so every production
lesson's four demonstrations jointly cover all semantic branches. It was not
designed so every four-of-five subset does so.

**Alternatives considered.** (a) strengthen every individual draw enough that
all rotations pass; (b) suppress the rotation result; (c) retain the established
ordered curriculum and report rotation as unsupported.

**Choice.** Use (c) for this bounded review. Option (a) would materially narrow
or restructure the approved distribution and is not needed by the current
ordered assembler.

**Probe.** `checks/lesson-census-diagnostic.json` records 0/300 ambiguous
production lessons and 225/1,500 ambiguous rotations, exactly 75 per band at
held-out positions 1, 2, and 3. `checks/48732ebd41f9_semantic_probe.json`
independently passes 100 ordered lessons per band across all cyclic starts.

**Failure mode / limit.** Any downstream component that reassigns an arbitrary
labelled pair as the query can create underdetermined lessons. Such assembly
must remain disabled or be guarded by an episode-level rival gate.
## Current reviewer considerations

Source SHA-256: `5bc7a1259c7fdb7fcee978112f9780e2cf2273eb3b68767291ddfc23fdf50c3f`.

# Decisions for review `review-e5112bf2a88b2e01`

The imported task notes retain the earlier distribution design as decisions D1–D13. This document records the decisions made in the present review; the concise current account and full rationale are also appended as D14–D17 in `repo/generators/48732ebd41f9/notes.md`.

## D14 — Strict replay identity, without coercion

**Observed behavior.** The imported generator accepted non-integer `seed` and `sample_index` values and negative indices. The before battery emitted 33 strict-scalar warnings.

**Original rationale.** Unknown; no note justified accepting coercible or modulo-wrapped replay keys.

**Alternatives.** Coerce with `int`; validate only in `generate`; or validate exact types in both generation and schedule lookup.

**Decision.** Require exact built-in integers for both values and a nonnegative sample index in both public entry paths. Coercion was rejected because it aliases caller mistakes (`True`/`1`, `1.0`/`1`) onto one replay identity. Generate-only validation was rejected because direct scheduling would retain a different contract.

**Evidence.** Red regressions: `checks/development-red-strict-scalars.log`. Green regressions: `checks/development-green-review-tests.log`. Before/after aggregate: `checks/before/checks/48732ebd41f9_before_battery_summary.json` and `checks/after/checks/48732ebd41f9_after_battery_summary.json`.

**Limit.** Large positive integers remain valid because the keyed hash has no finite replay-domain requirement.

## D15 — Preserve valid sampling, version, and Racket authority

**Observed behavior.** The defect occurred before lawful generation and did not imply a wrong task rule or wrong generated label.

**Alternatives.** Bump `VERSION`; edit the Racket source; alter schedules while touching the generator; or make the smallest boundary repair.

**Decision.** Make only the boundary repair. Keep `VERSION = 3.0.1`, `RULE_HASH = 9d5297512997`, all keyed draws, and the selected Racket authority unchanged.

**Evidence.** `checks/root-cause/valid-output-parity.json` records 340/340 lawful calls with identical outputs before and after. The after authority-sync and rule-smoke stages pass.

**Limit.** Previously tolerated malformed calls now raise; this is intentional API tightening, not lawful-data drift.

## D16 — Use `minimum_height` as the nearby rule parameter

**Goal.** Satisfy `PARAMETRIC-RULES.md` with a rule-changing parameter that preserves the family's reasoning structure.

**Alternatives rejected.** Output-color variation was rejected as mostly cosmetic. Grid size, position, distractor density, and palette weights were rejected because they change sampling rather than the executed rule. Larger thresholds or multiple simultaneous parameters were rejected as unnecessary scope.

**Decision.** Prototype `minimum_height ∈ {2,3}`, default 2. Keep “enumerate zero rectangles, filter by minimum height, choose greatest area, recolor with 6” invariant. Construct separated low/wide and tall rectangles so both settings are lawful and observably different. Select the value once per episode, never per pair.

**Evidence.** `checks/parametric/minimum-height-evidence.json`; source at `repo/generators/48732ebd41f9/workspace/parametric/prototype.py`; exact programs under its `rules/` directory. Two settings, two complete episodes, three demonstrations and one query per episode, zero rival findings.

**Limit.** This is a bounded prototype against the sole alternative parameter value. It is neither a production API nor a uniqueness proof against undeclared transformations.

## D17 — Keep the approved ordered curriculum and disclose rotation failure

**Observed behavior.** Both ordered probes pass, but arbitrary holdout rotation removes the only widest/tallest witness in some episodes.

**Alternatives.** Redesign every generated pair to refute all rivals individually; suppress the rotation result; reject the generator outright; or retain ordered use and state the unsupported operation.

**Decision.** Retain the ordered four-demo-plus-query curriculum. Redesign was rejected in this bounded assignment because it would materially alter an otherwise approved distribution and is unnecessary for the current assembler. Suppression was rejected because a future assembler could otherwise silently create underdetermined data.

**Evidence.** `checks/lesson-census-diagnostic.json` reports 0/300 ambiguous production lessons and 225/1,500 ambiguous rotations. `checks/48732ebd41f9_semantic_probe.json` independently passes 300 ordered lessons across all cyclic starts.

**Limit.** Query rotation must remain disabled or be guarded by an executable rival-identifiability gate. Production success is not evidence of arbitrary-rotation success.

## D18 — Return reusable probes rather than prose-only findings

**Decision.** Retain executable artifacts for the main repair, parametric family, parity check, and audit findings. The task-local prototype can be rerun by future agents with the command in its README. `checks/audit/probe_generators.py` reproduces both audit findings and binds them to exact generator hashes.

**Reason.** These checks are cheaper and less ambiguous to rerun than reconstructing claims from narrative notes.
