# Working notes: 3a96552d8c7c

## Selected rule

A row triggers only when it contains exactly two nonadjacent color-5 cells and every interior cell is 0. The authority replaces the whole interior with color 3. The rule is row-local and leaves every non-trigger row unchanged.

## Repair decisions

- Pinned `RULE_HASH = "91ba1164c014"` and preserved the canonical executable behavior.
- Replaced the baseline's fake/dead palette, density, position, and texture controls with five exact pixel-observable axes.
- Removed the validator's invented requirement for an adjacent-5 distractor; all three canonical inputs now pass.
- Added the canonical minimum boundary `5 0 5`, which the baseline never generated.
- Added explicit blocker, three-5, and wrong-color negatives, and a three-slot schedule in which every three consecutive examples cover all four declared shortcut witnesses.
- Kept canonical size/palette profiles in every difficulty band instead of treating difficulty as permission to leave the public task envelope.
- Kept the Python rule mirror pure and source-bound; the repository Racket battery is still the final parity check.

## Reusable probes

- `workspace/reference_probe.py` loads canonical pairs and the selected authority metadata without embedding task answers in tests.
- `workspace/qualify.py` checks canonical ownership, 300 generated draws, exact overrides, declared witnesses/rivals, and all cyclic query rotations for 12 starts per band.
- `tests/test_generator.py` and `tests/test_qualify.py` are portable task-local regressions.

## Known limits

The rival census is finite. Passing the four declared competitors and all tested rotations does not prove that every conceivable learner hypothesis is eliminated. Exact override checks cover reviewed extremes and teaching modes rather than every Cartesian combination.
## Current reviewer considerations

Source SHA-256: `310f5886b8ae3dfd5bdb47dc29df256edc2e56c258e6bd29106b2b3c4d9e60de`.

# Decisions for 3a96552d8c7c

## D1 — Preserve the selected authority

**Decision.** Keep the canonical row-local rule and pin `RULE_HASH = "91ba1164c014"`.

**Reason.** Rule smoke already passed on the baseline, and the observed failures were generator/validator/data-contract failures rather than incorrect labels. Changing semantics would have added unnecessary risk.

**Alternative rejected.** Reinterpret adjacent pairs or require an adjacent-5 distractor. Neither condition is present in the Racket predicate, and the baseline validator rejected all canonical examples by inventing the latter.

## D2 — Replace fake controls with exact observable axes

**Decision.** Advertise only `grid_h`, `grid_w`, `n_fill_rows`, `span_style`, and `negative_mode`; validate types/ranges before constructing `GenCtx`; recover every control from pixels through `observe_overrides`.

**Reason.** The baseline's palette, density, position, distinct-color, and helpful-texture controls were singleton, dead, or aliases with no observable effect. Exact controls make override tests meaningful and prevent metadata from overstating diversity.

**Alternative rejected.** Keep legacy names for compatibility. There was no genuine behavior to preserve, and aliases would continue to pass caller intent without changing data.

## D3 — Make the minimum legal boundary mandatory in default generation

**Decision.** Every default draw contains at least one `5 0 5` trigger.

**Reason.** The authority accepts one interior zero, the canonical examples include it, and the baseline sampled only gaps of at least two zeros. Without this boundary, the strengthening “require at least two zeros” is indistinguishable.

**Alternative rejected.** Depend on random short spans. A frequency guarantee is weaker than a lesson guarantee; a deterministic witness costs almost no diversity.

## D4 — Use a deterministic three-profile curriculum

**Decision.** Schedule `canonical`, `teaching_a`, `teaching_b` by `sample_index mod 3`, so any three consecutive examples include every profile.

**Reason.** Production lessons use three demonstrations. Individual witness frequency does not ensure lesson-level support; deterministic coverage makes all cyclic starts testable and query rotation safe.

**Alternative rejected.** Independent random profile choice. Even high marginal witness frequency can produce complete lessons with no relevant negative, as reproduced in audit A2 for another task.

## D5 — Teach four predicate boundaries with lawful rows

**Decision.** Include blocker, three-5, and wrong-color rows in teaching profiles while keeping 2–4 genuine positives.

**Reason.** These rows isolate the authority's exact predicates and keep every generated input non-identity. The mixed blocker/wrong-color row economizes grid rows without conflating the observed override classification.

**Alternatives rejected.**

- Put negative-only textures outside normal generation: learners would rarely or never see the distinction.
- Emit malformed/random noise: it would test robustness rather than the intended rule boundary.
- Require an adjacent pair distractor: unsupported by canonical data and the authority.

## D6 — Preserve canonical profile support in every band

**Decision.** Rotate all three canonical `(height, width, palette-size)` profiles through the `canonical` slot regardless of difficulty; use difficulty only for teaching-profile scale.

**Reason.** Difficulty should expand presentation scale without abandoning the public task envelope. This gives the profile-floor gate exact support in easy, medium, and hard.

**Alternative rejected.** Map hard exclusively to larger noncanonical shapes. That creates training drift and can make the generator appear valid only because strict checking is too permissive.

## D7 — Synchronize source text without changing Racket behavior

**Decision.** Remove one extra comment from the selected base `target_code` so it exactly matches canonical source; leave canonical data unchanged.

**Reason.** The source divergence was behavior-neutral but blocked strict defect lint and obscured which text was authoritative. Exact sync is simpler than carrying a permanent exception.

**Alternative rejected.** Suppress the divergence warning. That would make future semantic source drift harder to distinguish from benign formatting.

## D8 — Build a reusable source-only qualification tool

**Decision.** Add `workspace/reference_probe.py` and `workspace/qualify.py`, plus portable tests.

**Reason.** Future agents can cheaply check canonical ownership, 300 generated draws, exact controls, witness frequencies, and all cyclic lesson rotations before paying for the full Racket battery. The tool reads rival declarations from the generator rather than duplicating a stale name list.

**Limit.** It mirrors the rule in Python. Racket authority, grammar, and source synchronization still require the repository battery.

## Probe history and failure modes

- Baseline before checkpoint: lint, self-check, and defect-lint failed; the aggregate was interrupted and retained as partial evidence.
- First repaired defect-lint run exposed a comment-only selected-source divergence. The only change was exact source synchronization; behavior was rechecked independently.
- Focused tests followed red/green order: the first regression failed on missing `RULE_HASH`; the qualification test initially failed because the tool did not yet exist; both then passed after the minimal implementation.
- Final source qualification and production census found no ambiguity among the four declared competitors, including all tested query rotations.

## Remaining uncertainty

The distribution is intentionally narrow around the reviewed task grammar. It does not generate arbitrary distractor colors outside the explicit blocker/wrong-color curriculum, and the finite rival set cannot establish unique induction against all programs. Those limits are documented rather than hidden behind a universal-safety claim.
