# Working notes: 3ef9eae12446

## Current rule and assumptions

For every 3×3 window, if all eight border cells share one nonzero color and the
center is 0, fill that center with the border color. Other cells remain unchanged.
Overlapping lawful windows are allowed by the rule; the current sampler uses two
separated motifs for clarity. The selected Racket authority was not changed and
is pinned by `RULE_HASH = "ddc9a34d6cd5"`.

## Reversed decisions

Version 2.0.1 sampled only isolated positive rings and used a validator that
accepted any eight nonzero cells. It also advertised several ignored,
unobservable, or unprobeable axes. Version 3.0.0 replaces that with four
contrastive profiles, a structural target-ring validator, and only three exact
observable axes: `grid_h`, `grid_w`, and `profile`.

A first four-profile round-robin schedule was rejected during TDD because a
three-demo/one-query lesson could hold out the sole strongest witness. The final
six-position schedule is `cross_guard, multi_target, cross_guard, filled_guard,
cross_guard, mixed_guard`; every cyclic four-pair window retains a cornerless
cross after any query rotation.

## Strongest known shortcut

`orthogonal_neighbors_only` fills a zero center when its four cardinal neighbors
match, ignoring corners. It fits all 3 canonical pairs but disagrees on the exact
4×6 witness in `counterexamples/orthogonal-neighbors-shortcut.json`. Current
generation emits that distinction in three of six schedule positions. The
independent 400-draw audit measured 66 disagreements per 100 draws in every band.

## Evidence and current status

- Final generator SHA-256: `535dab381cf2ef8800223ddaae616defb86e0c36582e1d79ed90ca32037398f6`.
- Focused tests: 53/53 pass.
- Final battery: 12/12 stages green.
- Override probe: 11,160/11,160 draws accepted, zero findings.
- Lesson census: 300/300 production lessons and 1,200/1,200 query rotations identifiable against the declared rival.
- Independent probe: `workspace/reference_probe.py`; retained report: `workspace/final-audit.json`.

## Known limits and open findings

The schedule is proven only against declared competitors; finite rival checks do
not establish universal unique induction. The sampler intentionally uses two
separated motifs and exactly two nonzero colors, so it does not cover all lawful
overlapping-window or richer-noise inputs. `self_check` remains broader than the
sampler so canonical and other lawful task inputs are not rejected. The retained
v2 validator finding is resolved in
`counterexamples/validator-impostor-resolution.json`.
## Current reviewer considerations

Source SHA-256: `535dab381cf2ef8800223ddaae616defb86e0c36582e1d79ed90ca32037398f6`.

# Design and review decisions for `3ef9eae12446`

## D1 — Preserve the selected Racket authority

**Choice.** Leave the canonical Racket program unchanged and pin
`RULE_HASH = "ddc9a34d6cd5"` in the generator.

**Reason.** The rule executes correctly on every canonical pair and on lawful
generated inputs. The failures were in sampling, validation, curriculum, and
metadata rather than label semantics. The after battery's rule smoke,
Racket lint, and authority synchronization stages are green.

**Rejected alternative.** Editing the Racket rule to accommodate malformed or
ringless samples would widen the task rather than repair the generator.

**Failure mode watched.** A stale pin or altered selected source. Covered by
focused authority tests and `checks/after/checks/3ef9eae12446_after_authority_sync.json`.

## D2 — Replace positive-only isolated blocks with contrastive pairs

**Prior choice.** Version 2.0.1 generated one or two isolated hollow rings.
That made all visible nonzero structures valid targets and supplied no evidence
that corners, border uniformity, or center emptiness mattered.

**New choice.** Every input contains one real target and one contrast motif,
except `multi_target`, which contains two real targets. The four profiles are
`cross_guard`, `multi_target`, `mixed_guard`, and `filled_guard`.

**Reason.** These profiles expose four independent aspects of the rule:
all eight border cells, multiplicity, border uniformity, and a zero center.
They preserve near misses unchanged instead of deleting them.

**Rejected alternatives.** Random decorative noise was rejected because it
adds entropy without proving a decision boundary. A profile containing only a
single real ring was rejected because it preserves the original shortcut. A
negative-only input was rejected because the authority should fire on every
ordinary generated input and because lessons need positive evidence.

**Probe.** `generators/3ef9eae12446/workspace/reference_probe.py` and
`workspace/final-audit.json` independently classify every profile and compare
the intended rule with the cardinal-neighbor rival.

## D3 — Use a six-position schedule, not a four-position round robin

**Initial attempted choice.** A four-position schedule emitted each profile
once. The first focused test run exposed that, in a three-demo/one-query lesson,
`filled_guard` could become query-only and the demonstrations could lose the
strongest shortcut witness.

**Final choice.** Use
`cross_guard, multi_target, cross_guard, filled_guard, cross_guard, mixed_guard`.

**Reason.** Every cyclic four-pair window has two `cross_guard` entries. Holding
out any one pair leaves at least one cross witness in the three demonstrations,
while all four profiles still occur in ordinary generation. Focused tests
exhaust all six cyclic starts. The larger census then rotates all four labeled
pairs for 300 lessons.

**Rejected alternative.** Merely increasing the random probability of a witness
was rejected because frequency does not guarantee that every complete lesson
contains one after query rotation.

**Known limit.** The guarantee is against the declared
`orthogonal_neighbors_only` competitor. It does not enumerate all possible
hypotheses.

## D4 — Keep only exact, observable public axes

**Prior choice.** Version 2.0.1 advertised dimensions, block counts, palette
statistics, position bias, density, texture, and other axes that were clamped,
ignored, unprobeable, or missing provenance.

**New choice.** Expose only `grid_h` (4..10), `grid_w` (6..12), and `profile`
(the four named motifs). Implement `observe_overrides` so each realized value is
recovered from pixels.

**Reason.** These are meaningful controls that can be honored exactly and
jointly. A smaller honest surface is safer than a broad fictional one.

**Rejected alternative.** Keeping decorative one-token axes as diagnostics was
rejected because they do not change the grid. Keeping `n_blocks` separately was
rejected because it is already determined by `profile` and would create
incompatible combinations.

**Failure modes watched.** Unknown keys, bool-as-int, wrong types, boundary
combinations, and dimension/profile interactions. The final override probe
accepted 11,160/11,160 draws with zero findings.

## D5 — Validate the rule manifold, not the sampler template

**Prior choice.** `self_check` effectively required only eight nonzero cells.
The retained counterexample had eight arbitrary cells, no true ring, and still
passed.

**New choice.** Validate rectangular ARC colors and require at least one uniform
nonzero 3×3 border with a zero center. Do not require the exact two-motif layout.

**Reason.** Canonical examples may not share the sampler's placement and profile
conventions. A validator should accept every lawful task input while rejecting
rule-inert noise.

**Rejected alternative.** Requiring exactly two colors or exactly two motifs in
`self_check` was rejected because it would disown canonical or otherwise lawful
inputs. Those restrictions remain sampler invariants only.

**Evidence.** The exact retained impostor is in
`generators/3ef9eae12446/counterexamples/validator-impostor-resolution.json` and
is exercised through `mutation_fixtures()` and focused tests.

## D6 — Declare and test the strongest canonical-fitting rival

**Choice.** Declare `orthogonal_neighbors_only` in `SEMANTIC_RIVALS`,
`CANONICAL_SHORTCUTS`, and `LESSON_COMPETITORS`, with the
`missing_corners_cross` witness.

**Reason.** It fits all three canonical pairs because those pairs contain no
cornerless cardinal cross, yet it is materially wrong: it ignores four of the
eight required border cells. This is stronger and more plausible than a trivial
identity or single-target shortcut.

**Exact disagreement.** In the 4×6 witness stored at
`counterexamples/orthogonal-neighbors-shortcut.json`, both rules fill `(1,1)`;
only the rival fills `(1,4)` with color 3.

**How checked.** The independent Python oracle, the generator's named rival,
focused tests over every canonical pair, the public semantic gate, and the
Racket-labeled lesson census agree. The generator emits `cross_guard` at three
of six schedule positions; the independent audit observed 66/100 disagreements
per band.

## D7 — Anchor canonical profiles without shape-locking

**Choice.** Schedule canonical dimensions densely and add one or two adjacent
larger shapes per band. Always use exactly two distinct nonzero colors.

**Reason.** The canonical profiles are `(4,6,3)`, `(5,7,3)`, and `(6,7,3)` when
background is counted in palette size. Dense anchors avoid the baseline's zero
support in easy and hard, while adjacent shapes prevent a solver from tying the
rule to one canvas size.

**Evidence.** Final profile census: 48/60 exact hits, 49/60 in-envelope hits,
all bands supported, and all canonical inputs accepted. The independent 400-draw
audit reports every realized shape and 340 distinct inputs.

**Rejected alternative.** Fully random dimensions across the broad override
range were rejected for default generation because they would dilute canonical
profile support. The full range remains available through exact overrides.

## D8 — Build an independent reusable probe

**Choice.** Add `workspace/reference_probe.py`, which carries an independent
literal eight-border oracle, rival implementation, profile classifier, and
determinism/distribution audit.

**Reason.** The generator's own helpers cannot independently validate themselves.
The tool gives future reviewers a small replayable check without invoking private
runner functions.

**Limit.** It is still a second implementation written from the same human rule
understanding. Racket remains the authority; the public battery and lesson census
provide source-bound execution evidence.

## D9 — Preserve failed and interrupted evidence

**Choice.** Keep the initial red tests, failed baseline battery, and interrupted
stage directory rather than replacing them with only green artifacts.

**Reason.** They establish the defect and the actual development path. The first
post-repair defect-lint wrapper was externally interrupted and remains under
`checks/dev-defect_lint`; a fresh completed rerun is under
`checks/dev-defect-lint-complete`.

**Limit.** A stale `status: running` in an interrupted wrapper receipt needs
human interpretation; this motivates feedback item F1.
