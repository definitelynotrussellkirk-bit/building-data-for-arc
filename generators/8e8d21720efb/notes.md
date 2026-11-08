# Working notes: 8e8d21720efb

## Current rule and authority

The unchanged canonical Racket rule keeps a nonzero cell iff at least one
up/down/left/right neighbor has the same color. `RULE_HASH` is pinned to
`76b667ae03a8`; Python `rule_mirror` is testing support, not authority.

## Repaired teaching distribution

Baseline version 1.1.1 used two blobs and two nominally distinct-color
singletons. That made the canonical-fitting global-frequency shortcut (“keep a
color if it occurs at least twice anywhere”) observationally correct on most
ordinary samples. It also advertised dead or overlapping controls, accepted
unknown overrides, and validated little beyond rectangularity and two nonzero
cells. The retained audit `review-c231a5768f77dff2:v0001` was used as the lead;
its baseline source hash was
`854b90e0f0e55f721dda3d800235e3f89d58d7d8bd574d14a8ff4148b47851c9`.

Version 2.0.0 uses only three exact observable controls: `grid_h` (7..12),
`grid_w` (8..13), and `lesson_profile` (`canonical|witness`). Even sample
indices preserve one of five linked public dimension/component-size profiles;
odd indices construct a witness containing:

- a local blob plus a remote singleton of the same color;
- a same-color diagonal singleton pair;
- a cardinally adjacent different-color singleton pair;
- both horizontal and vertical surviving blobs; and
- isolated cells that identity would retain.

The ten-slot schedule cycles all five canonical profiles while alternating
canonical/witness. Any four consecutive pairs contain two witnesses, so any
single held-out query leaves a witness in the three demonstrations. Exact
construction uses finite backtracking for canonical components and a bounded
constructive witness layout; generation never silently drops a component.

## Decisions and reversals

- Reversed broad, mostly dead axes in favor of three exact observable controls.
- Reversed unconstrained random lessons in favor of a deterministic alternating
  curriculum. Pure-witness lessons were rejected because they would abandon the
  linked public manifold; purely canonical lessons cannot refute locality
  shortcuts.
- Kept the Racket authority unchanged because all five canonical labels and the
  independent mirror agree.
- Strengthened `self_check` to recognize only the two documented teaching
  grammars, reject malformed ARC values and minimal impostors, and support exact
  override observation.
- Added executable rivals, witness predicates, a rotation-aware lesson hook,
  82 focused tests, a retained global-frequency counterexample, and the cheap
  `workspace/locality_shortcut_probe.py` authoring tool.

## Evidence and current limits

Final generator SHA-256:
`9117be8035b5244cf7d95855b08b38f2a9e13d5e5b9b7a8b708d95de758b6270`.
The final battery is 12/12 green; task tests are 82/82; the 300-lesson Racket
census materialized 1,200 unique pairs and found zero production or query-
rotation ambiguities against the six declared rivals. The cheap probe found
0/1,164 ambiguous rotations for the global-frequency rival, versus 46/1,164 on
the baseline under the same seed and sample budget.

These are finite rival checks, not proof of unique induction. Canonical profiles
remain limited to the five linked size signatures, witness layouts deliberately
use a compact structural grammar, and undeclared position- or shape-specific
hypotheses remain possible. Hidden solve-query correctness is unknown.


## Current owner acceptance

Accepted the scoped generator, portable tests and task-local authoring tools using the October 3 lightweight policy. All semantic batteries, Racket comparisons, censuses, solves and replay counts in the reviewer evidence remain reviewer-reported; no routine maintainer rerun or model training admission is claimed. Exact source/rule approval records bind the accepted bytes. Both random audits remain independent findings, and shared tool requests remain proposals unless separately implemented.
## Current reviewer considerations

Source SHA-256: `9117be8035b5244cf7d95855b08b38f2a9e13d5e5b9b7a8b708d95de758b6270`.

# Decisions for 8e8d21720efb

## D1 — Keep the canonical Racket authority unchanged

**Original choice.** Version 1.1.1 already described the correct local
same-color cardinal-neighbor law, but did not pin its hash.

**Decision.** Pin `RULE_HASH=76b667ae03a8` and keep Racket unchanged. All five
labeled canonical pairs match an independent Python implementation and the
selected authority; the defect was distribution and contract quality, not
label semantics.

**Failure mode considered.** Rewriting the authority merely to fit the old
four-object layout would change the task instead of repairing its teaching data.

## D2 — Replace eight broad/dead axes with three exact observable controls

**Original choice.** The baseline advertised height, width, palette, blob count,
palette size, position bias, distinct-color count, density, and texture. Several
were constants or aliases; exact dimensions failed or were ignored; unknown keys
were accepted.

**Decision.** Expose only `grid_h`, `grid_w`, and `lesson_profile`. Each is
recoverable from the returned input and honored over its full declared range in
every band. Invalid types, values, and unknown keys raise.

**Alternative rejected.** Preserving legacy axis names for compatibility would
continue to promise distinctions that the task does not need and the generator
did not implement honestly.

## D3 — Alternate linked canonical profiles with explicit witness profiles

**Original choice.** Ordinary draws used nominally distinct colors for two blobs
and two singletons. The locality requirement was therefore usually confounded
with global color frequency.

**Decision.** Even samples preserve one of the five linked public dimension and
component-size signatures; odd samples use a counterexample-rich witness. The
witness combines six contrasts in one compact grid: identity, global frequency,
8-neighbor contact, any-color contact, horizontal-only, and vertical-only.

**Alternatives rejected.** All-canonical generation cannot teach the missing
locality distinctions. All-witness generation would drop public-profile support.
Pure random resampling could still produce three demonstrations that all support
the same shortcut.

## D4 — Use a ten-slot deterministic schedule and three demonstrations

Five canonical cases require ten alternating slots. Any four consecutive pairs
contain exactly two canonical and two witness profiles. Holding out any one
query therefore leaves at least one witness among the three demonstrations.
This supports the actual rotating-query policy used in verification; it is not
a claim about arbitrary lesson sizes or multiple simultaneous queries.

## D5 — Construct complete components, never paint opportunistically

Canonical components are placed by finite backtracking with a one-cell external
halo. Witnesses use a bounded constructive layout valid at the minimum 7x8 size,
then may be reflected. This prevents the baseline's accidental overwrites and
fragmentation from serving as the only counterexample to a shortcut.

**Failure mode considered.** Retry loops that silently abandon an object can
produce superficially valid but semantically wrong examples. Construction now
raises rather than returning an incomplete scene.

## D6 — Make validation describe the teaching grammar

`self_check` now validates ARC integer colors, rectangularity, dimension bounds,
background majority, same-color components, and one of the two explicit profile
grammars. Exact observations and strict canonical support are separate helpers.
Minimal impostors and mutation fixtures are rejected.

**Limit.** This intentionally narrow grammar does not enumerate every lawful
input to the abstract Racket rule. Passing it means “belongs to this curriculum,”
not “the authority is undefined elsewhere.”

## D7 — Bind teaching claims to executable rivals and retained evidence

Six executable competitors, semantic witnesses, a rotation-aware
`lesson_identifiable` hook, and 82 focused tests now make the curriculum claims
machine-checkable. `counterexamples/global_frequency_shortcut.json` retains the
main repaired witness. `workspace/locality_shortcut_probe.py` compares a source
against the global-frequency rival without relying on declarations; the full
Racket census remains authoritative.

## D8 — Self-review and remaining uncertainty

The repair removes the measured locality shortcut without changing labels: the
same cheap probe moved from 46/1,164 ambiguous rotations on the baseline to
0/1,164 on the final source, and the larger Racket census found zero ambiguity
against all six declared rivals. The new restriction is that canonical profiles
use five linked signatures and witnesses use a deliberately compact grammar;
a yet-undeclared shape- or position-specific hypothesis could still exploit that
structure. Finite rivals and 300 lessons do not prove unique induction.

<!-- arcpuzzles-trainer-ambiguity:start -->
## Current trainer ambiguity follow-up

Claude supplied 1 exact canonical lesson(s) with a proposed alternative rule. Retained privately with source hashes and all stored queries: `evidence/trainer-ambiguity-current/current.json`. These are **open describer flags**, not confirmed wrong labels or failed current parametric qualifications. Check whether the proposed rival fits every demonstration and changes any stored query; distinguish source revisions before repairing. Approval and training state are unchanged.
<!-- arcpuzzles-trainer-ambiguity:end -->

## 2026-10-25 native parametric promotion: linked-color projection

This review added a native two-setting family under `workspace/parametric/`.
`projection_mode=local_cells` is byte-for-byte the selected canonical Racket
program. `projection_mode=linked_colors` first derives the input-dependent set
of colors participating in a same-color cardinal link, then consumes that set
to project all occurrences of those colors across the grid, including remote
singletons. The sampler keeps matched inputs across settings, supports 2–6
demonstrations, always emits four distinct private queries, and includes a
substantive 30×30 query.

The bounded self-review used the canonical local-cell rule as the cheap bypass
for the linked-color setting. Every authored pair contains remote occurrences
of linked colors, so the two settings disagree on every visible demonstration
and query; the discovered linked-color intermediate also varies across an
episode. Native qualification covered both settings at seeds 0 and 17 with
three demonstrations and four queries (40 protected-Racket evaluations), and
the four-case wrong-intermediate witness was replayed through protected Racket.
Single-query projection and first-turn private-field invariance also passed.

Evidence is under `checks/8e8d21720efb/qualification-v1/`,
`checks/8e8d21720efb/causal-v1/`, and
`checks/8e8d21720efb/first-turn-v1.json`. This is reviewer-ready source, not
owner acceptance or training admission; finite rival checks do not prove unique
induction.
