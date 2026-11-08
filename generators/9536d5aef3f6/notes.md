# Working notes: 9536d5aef3f6

## 2026-10-03 review-cd846e20d1f37734

Prior return `review-3c3b4d18cfdc8272:v0001` was used as a lead, not as a
measurement. It identified ignored/rejected advertised controls and validator
holes in source SHA-256
`e616da88b90e96d9c49a32ff17d1be7a4c7e9d986cd8de176048675821f1fccf`.
The fresh before battery reproduced blocking lint, defect-lint, and override
failures.

The repair narrows the exact public surface to observable `size` and `markers`,
rejects unknown controls, pins `RULE_HASH=2b970065d6a3`, and validates rectangular
ARC grids. The curriculum initially added lower-side inputs to defeat the public
`upper_only` shortcut. Adversarial self-review then found a second canonical-fit
shortcut: copy to the transpose partner only when that partner is empty. An
actual Racket probe on an unequal occupied pair showed that the selected rule
swaps the values, so version 2.2.0 adds two unequal-conflict profiles, varies
the conflict orbit, and declares the `fill_empty_only` executable rival.

Every cyclic three-demo window in the six-profile schedule now contains one
unequal conflict and enough upper/lower evidence for all declared rivals. The
task-local tests preserve the canonical-fit premise, the conflict counterexample,
cyclic lesson coverage, exact override behavior, malformed-grid rejection, and
deterministic replay.

The Racket authority was not edited. Finite rival checks do not prove universal
identifiability; new plausible rivals should be added to `SEMANTIC_RIVALS` and
tested across every cyclic query position before changing the schedule.
## Current reviewer considerations

Source SHA-256: `4eebf8bb4fd963cd7f58416905a167ad2e916f03bc9a8e80c3efe0f91dec1d13`.

# Decisions for 9536d5aef3f6

Final generator version: `2.2.0`
Final generator SHA-256: `4eebf8bb4fd963cd7f58416905a167ad2e916f03bc9a8e80c3efe0f91dec1d13`

## D1 — Keep the selected Racket authority unchanged

**Original state and rationale.** The baseline Python docstring described a
one-way upper-to-lower mirror, but the canonical selected Racket rule is the
more general immutable operation `(overlay g (transpose g))`. The original
one-way input distribution concealed that distinction. Why the original
implementation restricted sources to the upper triangle is not recorded.

**Choice.** Pin `RULE_HASH="2b970065d6a3"` and change only the generator. A
supported Racket probe on an unequal occupied transpose pair confirmed that the
values swap, matching immutable transpose overlay
(`checks/conflict-probe/racket.json`). The final rule-smoke and authority-sync
stages pass under the same authority.

**Rejected alternatives.** Changing the Racket rule to the baseline's one-way
English description would contradict the canonical examples' selected authority
and reduce the true task. Sequential in-place mirroring was also rejected
because its result depends on traversal order and smears one conflict color.

**Limitation.** The review proves parity only for canonical pairs, battery
samples, the retained conflict probe, and generated samples—not all possible
square grids.

## D2 — Replace eight misleading controls with two exact observable axes

**Original state and rationale.** Version 1.1.1 declared `size`, `palette_kind`,
`markers`, `marker_density`, `palette_size`, `position_bias`,
`n_distinct_colors`, and `texture`. Only `size` and `markers` influenced ordinary
generation; several valid advertised values were rejected, unknown keys passed
silently, and degenerate texture modes bypassed normal validation. The original
rationale for this broad surface is unknown. Prior return
`review-3c3b4d18cfdc8272:v0001` supplied the lead, and the fresh before battery
reproduced the failures.

**Choice.** Expose only exact `size=5..10` and `markers=3..8`. Reject unknown
axes, invalid difficulties, Boolean/non-integer values, and out-of-range exact
overrides through `gen_ctx`. `observe_overrides` recovers both values directly
from returned pixels.

**Alternatives considered.** Implementing all eight axes was rejected because
most did not express meaningful independent task variation and would recreate
aliasing and incompatibility complexity. Retaining degenerate textures as
ordinary inputs was rejected because blank, diagonal-only, and already-symmetric
examples do not teach a nonidentity rule.

**Probe and failure mode.** The before override stage had 1,092 findings; the
final override stage is green. Task tests cover lower/upper bounds and middle
values in all three bands. Exact axes still do not expose curriculum profile;
that is intentionally an internal deterministic schedule.

## D3 — Make the input validator structural and task-linked

**Original state.** `self_check` inspected only the first-row width indirectly,
accepted ragged grids, invalid colors, and Booleans, and returned success for
metadata-declared degenerates.

**Choice.** Validate nonempty rectangular square grids, side 5..10, literal
integer ARC colors 0..9 (excluding `bool`), 3..8 markers, three or four foreground
colors, at least one off-diagonal marker, and at most one informative occupied
transpose pair. An occupied pair is accepted only when its colors differ, because
an equal-color pair cannot distinguish swap semantics.

**Rejected alternative.** Making `self_check` accept every square grid on which
the Racket rule executes was rejected: executable is broader than a useful
training manifold. Conversely, rejecting all occupied pairs was initially used
but later rejected because it preserved the `fill_empty_only` shortcut.

**Limitation.** This is a deliberately sparse, canonical-scale teaching
manifold; it does not claim to enumerate every lawful input for the abstract
transpose-overlay rule.

## D4 — Use a six-profile cyclic curriculum with local identifiability

**Choice.** Schedule `upper_sparse`, `lower_sparse`, `unequal_conflict`,
`upper_with_diagonal`, `lower_dense`, and
`unequal_conflict_with_diagonal`. Sizes cover 5..10 once per period; marker
anchors vary by band. Every cyclic three-demo window contains both directional
evidence and one unequal occupied pair.

**Why.** The five public pairs fit `upper_only`, and because they contain no
occupied transpose pair they also fit `fill_empty_only`. Global diversity is not
enough: the evidence must occur inside each lesson's demonstration window.

**Alternatives considered.** Pure random mixing was rejected because a short
lesson could miss the decisive profile. A fixed upper/lower alternation defeated
the public shortcut but not occupied-pair semantics. Putting the sole conflict
profile once in a longer period was rejected because some three-demo windows
would remain ambiguous.

**Probe.** The task-local test enumerates every cyclic start in all bands and
requires `lesson_identifiable` to return no reasons. The final 100-lesson-per-band
census materialized 1,200 unique inputs and found zero declared-rival ambiguity.

## D5 — Declare executable rivals and witnesses

**Choice.** Declare five rivals: `upper_only`, `lower_only`,
`fill_empty_only`, `transpose_only`, and `anti_diagonal`. The first and third fit
all five canonical pairs and are therefore also listed under
`CANONICAL_SHORTCUTS`. Witnesses identify lower-side sources and unequal occupied
pairs; `lesson_identifiable` checks that no rival fits every demo while differing
on the query.

**Why.** Prose about diversity cannot establish that a plausible wrong rule is
actually refuted. Executable rivals make both the semantic gate and lesson census
measure the intended distinction.

**Limitations.** This is a finite rival family, not proof of universal
identifiability. New plausible mechanisms should be added explicitly rather than
interpreting a green census as a theorem.

## D6 — Vary the occupied conflict orbit

**Intermediate failure.** Version 2.1.0 placed every unequal occupied pair at
`(0,1)/(1,0)`. Although all declared rivals were refuted, a coordinate-specific
solver could learn “swap only the anchor pair.” The RED regression retained at
`checks/tdd-red-conflict-location/result.json` found only one conflict location.

**Choice.** Version 2.2.0 samples the occupied transpose orbit from the available
off-diagonal orbits while retaining exactly one informative pair. Across the
focused regression's 48 conflict examples per band, at least six distinct pair
locations must appear.

**Rejected alternative.** Merely documenting the fixed anchor as a limitation
was rejected because varying the orbit is cheap and improves training value
without changing the public axes or authority.

## D7 — Preserve failures and add source-bound tests

Tests were written before each production repair and their failing receipts are
retained: the initial seven failures, the two missing conflict-contract failures,
and the fixed-coordinate failure. The final suite checks authority parity,
canonical support, exact overrides, malformed inputs, cyclic identifiability,
both canonical-fit shortcuts, variable conflict placement, canonical-scale
profiles, and deterministic/global-RNG-pure replay.

The complete battery remains separate from task-local tests by design; both
receipts are required in this return. A fresh-packet delta replay is recorded in
`checks/final-replay/` so the maintainer can verify that the packaged patch—not
an unrecorded working tree—reproduces the final source and focused tests.
