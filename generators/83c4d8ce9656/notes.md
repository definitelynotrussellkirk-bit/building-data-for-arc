# Review notes

The canonical examples are intentionally ambiguous: three simpler rules fit all
public pairs. This implementation keeps the canonical Racket source unchanged
and repairs the *teaching distribution* instead. The only caller-facing axis is
`scene_profile`; it is exactly observable and every four consecutive samples
cover all four values.

The strongest public-data shortcut is `color_span_per_row`: for each row/color,
keep only its first and last occurrence. It agrees with every canonical pair,
including the two separated color-5 singletons, but fails when two separated
same-color runs both have interiors. The scheduled `repeated_color_runs`
profile emits that counterexample once per four-example lesson.
## Current reviewer considerations

Source SHA-256: `c6dc5079fc6da7a74184184c4385b0a93a3cb1b6ca95d1f17eeb23de0136efa6`.

# Decisions for `83c4d8ce9656`

## 1. Preserve the canonical Racket rule

**Input choice / authority.** The canonical written rule and Racket program say
to operate on each maximal same-color horizontal run independently, retaining
both endpoints and preserving singletons.

**Original rationale.** The imported generator described the same broad rule,
but did not pin the canonical rule hash.

**Probe.** The Racket smoke test executed 120 generated grids with 0 crashes,
120 transformations fired, A-B-A reentrancy, and 120/120 agreement with an
independent Python mirror. All three canonical pairs also agree.

**Decision.** Add `RULE_HASH = "8cf1fe655564"` and leave the Racket source
unchanged.

**Alternatives rejected.** Rewriting the Racket program to remove two style
findings would change an already-correct authority without improving the
lessons. Replacing Racket with the Python mirror would weaken source authority.

**Failure modes / limitations.** The Racket source retains one dummy binding
and one `= 0` style finding. They are non-blocking and execution parity passes.

## 2. Remove nine misleading axes; expose one exact semantic axis

The imported generator declared these controls:

| Original choice | Stated or inferable rationale | Probe result | Decision |
|---|---|---|---|
| `grid_h` (`3..12`) | vary height by difficulty | actual sampling only reached 5–7; many declared values were rejected | remove as a public override; dimensions are profile/band internals |
| `grid_w` (`5..18`) | vary width by difficulty | actual sampling only reached 8–11; many declared values were rejected or observed incorrectly | remove as a public override |
| `palette_kind` | intended warm/cool/varied color texture | all named values were behaviorally inert | remove |
| `runs` (`1..12`) | intended control of run count | ordinary draws only reached 3–5; much of the domain was rejected | remove |
| `palette_size` (`1..9`) | intended color-count control | provenance/observability failures and conflicts with `n_distinct_colors` | remove |
| `position_bias` | presumably reserve future layout modes | only one token, `horizontal_runs`; no actual choice | remove |
| `n_distinct_colors` (`1..9`) | duplicate palette-size intent | inert under mixed overrides and not exactly observable | remove |
| `density` | presumably reserve sparse/dense modes | only one token, `sparse`; no actual choice | remove |
| `texture` | alias helpful palettes and expose negative fixtures | helpful values were ignored; negative fixtures polluted the ordinary domain | remove |

**Decision.** Expose only `scene_profile`, whose four values correspond to
visibly different semantic lessons and are recovered exactly by
`observe_overrides`.

**Alternative rejected.** Keeping numeric size/count axes and implementing the
entire Cartesian product would create many combinations with no pedagogical
value and would require a large incompatibility policy. Diagnostic negative
fixtures also do not belong in the ordinary generator domain.

**Failure modes / limitations.** Callers that depended on the old undocumented
or broken overrides must switch to `scene_profile`. This is intentional: silent
acceptance of a control that is ignored is worse than a loud interface change.

## 3. Use four scheduled scene profiles

**Choice.** `canonical_mix`, `multiple_long_runs`, `repeated_color_runs`, and
`touching_color_runs`.

**Original rationale.** Unknown. The old generator sampled independent runs and
only guaranteed that some length-three run existed. It did not identify public
ambiguities or schedule lessons.

**Probes.** I evaluated wrong rules against all canonical pairs. Three rivals
fit every pair: longest-run-only, per-color row span, and color-blind nonzero
block endpoints.

**Decision.** Give each rival one constructive counterexample profile, plus one
canonical-scale anchor. A four-example lesson must contain all four.

**Alternatives rejected.** Pure random sampling could eventually emit the
witnesses but gives no per-lesson guarantee. A single overloaded scene could
refute all rivals at once, but it would be harder to diagnose and easier for a
learner to treat as an outlier.

**Failure modes / limitations.** These are named plausible rivals, not an
exhaustive hypothesis class. New rivals should be added to
`SEMANTIC_RIVALS`, paired with a witness and a scheduled profile if necessary.

## 4. Match public morphology deliberately

**Choice.** `canonical_mix` emits exact public signatures `(height, width,
palette size including zero)` of `(5, 8, 6)` or `(5, 9, 5)`.

**Original rationale.** The old dimensions happened to overlap the canonical
sizes, but the combined shape/palette profile matched 0/60 checker draws.

**Probe.** Baseline profile floor: 0/60. Initial rewritten schedule: 7/60.
Final schedule: 17/60, above the 25% floor.

**Decision.** Make public-profile support an explicit renderer and validate it
with `strict_canonical_like` rather than relying on marginal size overlap.

**Alternative rejected.** Declaring a canonical-profile opt-out would hide an
avoidable distribution gap.

**Failure modes / limitations.** Exact signatures do not by themselves prove
semantic similarity. The strict hook also requires the canonical ambiguity:
all named public-data shortcuts must still agree with the authoritative rule on
an anchor.

## 5. Let difficulty affect scale, not semantics

**Choice.** Non-anchor profiles use 5×10 (`easy`), 6×11 (`medium`), and 7×13
(`hard`) grids; run lengths grow modestly by band. The four semantic profiles
remain present in every band.

**Original rationale.** The old generator used larger dimensions and more
requested runs in harder bands.

**Decision.** Retain that intuitive scale progression while keeping the rule
and curriculum invariant. Difficulty must not remove a rival witness.

**Alternatives rejected.** More colors or many more segments in hard mode would
increase visual clutter without teaching a new concept. Different semantics by
band would make the lesson contract unstable.

**Failure modes / limitations.** Difficulty here measures scene size and run
length, not reasoning depth. The task has one compact transformation, so a
larger gap would be artificial.

## 6. Seed-phase the four-profile schedule

**Choice.** Select profile index `(sample_index + seed % 4) % 4` when no exact
override is supplied.

**Original rationale.** The first rewrite used `sample_index % 4`, which is the
simplest periodic schedule.

**Probe.** That schedule passed every contiguous four-example lesson but
aliased the checker's fixed off-diagonal census, yielding only 7/60 public
anchors. A regression test pinned the checker census before the change.

**Decision.** Add a seed-dependent rotation. Every four consecutive sample
indices still cover all profiles exactly once, while cross-seed samples do not
collapse onto one residue.

**Alternatives rejected.** Weighted random choice cannot guarantee lesson
coverage. A larger-period pseudorandom schedule complicates reasoning and
observability without adding value.

**Failure modes / limitations.** A consumer that requests fewer than four
examples may not see every witness. `EXAMPLES_NEEDED = 4` and
`lesson_identifiable` make that requirement explicit.

## 7. Construct scenes directly; never repair by overwriting

**Choice.** `_put_run` checks bounds and overlap before writing. Each renderer
places its required witness first and fills remaining rows with isolated runs.

**Original rationale.** The old sampler tried up to 160 random placements and,
if no long run existed, overwrote `g[h // 2][1:4]` unconditionally.

**Probe.** `hard`, seed 61, sample 3 reproduced a mixed-color adjacency caused
by that overwrite. The old `self_check` then disagreed with the generated grid.

**Decision.** Use bounded constructive layouts with no retry exhaustion and no
fallback mutation. Any impossible placement raises immediately.

**Alternatives rejected.** Increasing retry count leaves the same probabilistic
failure mode. Clearing a row before fallback would hide lost content and still
make lesson composition accidental.

**Failure modes / limitations.** The renderers are intentionally specialized;
new dimensions must be checked against each witness's minimum span.

## 8. Define a lawful teaching grammar in `self_check`

**Choice.** Require a rectangular ARC-color grid, supported dimensions,
visible background, at least two active colors, at least three maximal
same-color horizontal runs, at least one length-3+ run, and at least one
length-1/2 run.

**Original rationale.** The old check only rejected ragged grids and adjacent
nonzero cells of different colors. It accepted an all-zero grid and other
non-lessons.

**Probe.** Baseline defect lint showed only 7/48 destructive mutations rejected
and accepted every minimal impostor family. Final checks reject all blank-grid
mutations and report no defect-lint findings.

**Decision.** Validate enough structure to ensure the transformation both fires
and demonstrates endpoint preservation.

**Alternatives rejected.** Requiring every row to be active or every color to
have a long run would unnecessarily narrow lawful inputs. Treating blank or
length-two-only grids as ordinary edge cases teaches identity rather than the
rule.

**Failure modes / limitations.** Some generic mutations remain lawful because
they do not destroy the grammar. Task-specific correctness is enforced by the
semantic witnesses and lesson contract, not by pretending every mutation must
be invalid.

## 9. Make shortcuts executable contracts

**Choice.** Implement three explicit rival functions, three witness predicates,
`WITNESS_RIVALS`, `CANONICAL_SHORTCUTS`, and `lesson_identifiable`.

**Original rationale.** None was present; the baseline semantic gate reported
`NO_CONTRACT`.

**Probe.** The final semantic gate examined 600 inputs: 153 strict anchors,
all three witnesses firing, all three rival claims verified, and 12/12 lessons
identifiable across easy/medium/hard.

**Decision.** Encode ambiguity as executable evidence rather than prose. A
lesson is accepted only when all four profiles are present, outputs match the
rule, and no named competitor—including identity—survives every demonstration.

**Alternatives rejected.** A metadata-only profile label could be spoofed by a
grid that does not contain the witness. The observer and witness predicates
therefore recover semantics from the grid itself.

**Failure modes / limitations.** The Python mirror is test support, not the
execution authority. Any future rule change must update the rule hash and prove
Racket/mirror parity again.

## 10. Fail loudly on override mistakes

**Choice.** Reject unknown keys before creating the generation context; use
`gen_ctx` for exact `scene_profile` selection; verify the resulting grid with
both `self_check` and `observe_overrides`.

**Original rationale.** The old `**overrides` path silently swallowed unknown
keys and exposed combinations it did not honor.

**Probe.** Baseline override stage: 8,840 findings. Final override stage:
450/450 accepted draws across five cases and three bands; unknown key rejected.

**Decision.** A requested profile must be both generated and independently
observable, or generation raises.

**Alternatives rejected.** Treating unknown keys as no-ops preserves typo bugs.
Returning a best-effort nearby profile makes experiments irreproducible.

**Failure modes / limitations.** There is only one public axis. Adding another
requires a genuine observable contract and explicit incompatibility evidence
for any invalid combinations.

## 11. Add local regression and census tooling

**Choice.** Add a 16-test task suite and `workspace/profile_audit.py`.

**Original rationale.** The task workspace contained no tests or analysis tool.

**Probes covered.** Canonical-pair agreement, rule-hash pinning, exact override
observability, unknown-key rejection, every scheduled profile, all witnesses,
all named rivals, deterministic generation, public-profile support, diversity,
and lesson identifiability.

**Decision.** Keep a fast local loop for future agents instead of requiring the
full multi-minute battery for every edit. The profile audit reports counts and
all contract failures in one JSON-serializable record.

**Failure modes / limitations.** The local suite complements rather than
replaces the source-bound battery and canonical Racket smoke test.
