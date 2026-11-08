# Working notes: 9fbd0923e6ae

## Baseline examined

- Selected baseline source SHA-256: `924ff0684676474bb80094abdd8e49eadf8694fcf2089cf14e73da4a0445bd5e` (`checks/source/generator_before.py`).
- No prior associated review was available: `evidence/associated_notes.jsonl` was empty, so no prior return was used as a repair lead.
- The baseline emitted only a centered vertical guide, only selector-side sources, always-changing outputs, one distractor, and exactly four colors. Its `self_check` rejected lawful horizontal canonical examples; it had no pinned `RULE_HASH`; several declared axes were dead or overlapping.
- The before battery was interrupted by the outer harness after checkpointing evidence. It is **not** a completed aggregate. At that point rule smoke was green; lint, self-check, defect lint, and distribution gate had failed, with seven stages still pending. See `checks/before/`.

## Canonical rule analysis

The canonical Racket authority reads the target color from `(0, 0)`, finds the first complete gray column or row, and reflects every other target-color cell across it, clipping out-of-bounds destinations. The selector is metadata and is never reflected. The authority was not edited.

The strongest plausible rival left by all five canonical pairs is:

> Reflect target cells only when they lie on the selector's side of the guide.

That rival fits 5/5 canonical pairs. It fails when a target cell on the opposite side has an in-bounds mirror. Exact evidence is in `checks/shortcut/`.

## Repair design

- Pinned `RULE_HASH = "63d7f8006f35"` and replaced the old sampler with a constructive versioned sampler.
- Added both guide orientations and three observable guide positions.
- Added exact observable axes for dimensions, target count/layout, distractor count/palette size, and isolated gray noise.
- Added six deterministic profiles. Four contain opposite-side or both-side targets, one is canonical-like selector-side reflection, and one is a lawful clipped identity case.
- Changed the scheduled horizontal profile from selector-side to opposite-side after a new cyclic-query regression demonstrated one rotation in which the only counterexample became the query. Every four-example window now retains a rival-refuting demonstration under all four query choices.
- Added executable semantic witness/rival declarations and `lesson_identifiable`.
- Expanded `self_check` to accept the canonical horizontal and vertical authority domain while retaining structural diagnostics on malformed grids.
- Kept all rule behavior in the existing canonical Racket authority; no Racket source changed.

## Tests and probes

`tests/test_generator.py` and `workspace/reference_probe.py` are task-local and independent of production solving helpers. They cover:

- canonical normalization, acceptance, and independent-oracle parity;
- real canonical Racket parity;
- all exact override endpoints and invalid overrides;
- deterministic schedule coverage and 96 cyclic query rotations;
- canonical shortcut fit plus generated counterexample;
- selector exclusion, clipping/identity, malformed inputs, and mutation rejection;
- distribution coverage over 120 draws per difficulty setting;
- independence from `PYTHONHASHSEED`.

TDD evidence is retained in `checks/tdd/`, including the initial missing-contract failure and the cyclic-rotation red/green pair.

## Final measurements

- Final generator SHA-256: `68444f3c9cf333af93b58d4eb91a749e10417bc980626032dec710b645d74086`.
- Full after battery: 12/12 stages green (`checks/after/`).
- Portable selected-task tests: 50/50 passed (`checks/task-tests-final/`).
- Declared-rival lesson census: 100/100 lessons per band, 0 ambiguous, 1,200 unique inputs; every declared instance of `selector_side_only` was refuted in every lesson (`checks/lesson-census.json`).
- Final visible-only solve: 3/3 demonstrations passed in one revision, bound to the final generator hash; earlier exposure was declared yes and reference consultation during the solve was declared no (`solve/`).

## Limits

The census is finite and tests declared rivals, not universal induction. The shared census does not rotate query positions; the task-local regression does so exhaustively for the six-profile schedule. The generated dimension envelope is intentionally bounded to 8–11 by 9–12 even though `self_check` accepts a broader lawful structural envelope for canonical compatibility.
## Current reviewer considerations

Source SHA-256: `68444f3c9cf333af93b58d4eb91a749e10417bc980626032dec710b645d74086`.

# Decisions for `9fbd0923e6ae`

## D1 — Keep the canonical authority unchanged

**Choice.** Pin `RULE_HASH = "63d7f8006f35"` and repair only the Python sampler/validator/test surface.

**Rationale.** The canonical Racket program matches all five canonical pairs and expresses a coherent rule: select the top-left color, find a complete gray row or column, reflect every other selected-color cell, and clip out-of-bounds destinations. The baseline failure was distributional and contractual, not an authority defect.

**Alternatives rejected.** Rewriting the Racket rule to match the old vertical-only sampler would have narrowed a valid authority and contradicted horizontal canonical examples. Adding a second task-local rule would have created source divergence.

**Probe/failure mode.** Real Racket parity is tested on all canonical pairs and generated cases. `authority_sync` and `rule_smoke` are green in `checks/after/`.

## D2 — Use a six-profile deterministic curriculum

**Choice.** Schedule:

1. `vertical_canonical`
2. `horizontal_opposite`
3. `vertical_opposite`
4. `horizontal_clipped`
5. `vertical_opposite_end`
6. `horizontal_both_broad`

**Rationale.** A short deterministic period makes lesson composition auditable and guarantees exposure to both orientations, canonical-like dimensions, opposite-side witnesses, off-center guides, and identity/clipping. Random-only sampling could pass aggregate diversity while producing ambiguous individual lessons.

**Alternative rejected.** A larger random curriculum was unnecessary and harder to reason about. The initial schedule used a selector-side horizontal profile; a red cyclic-query regression showed that one four-example window then had only one rival-refuting example. Making that profile opposite-side gives every window at least two such examples.

**Probe/failure mode.** `test_every_cyclic_query_rotation_keeps_a_rival_refuting_demo` checks all 96 band/start/query combinations. The red and green runs are retained in `checks/tdd/`.

## D3 — Model both guide orientations and three positions

**Choice.** Advertise exact controls `guide_orientation ∈ {vertical,horizontal}` and `guide_position ∈ {start,middle,end}`, mapped to one-third, one-half, and two-thirds of the relevant dimension.

**Rationale.** Canonical examples use both row and column guides, and several are off-center. This directly repairs the baseline's centered-vertical shortcut.

**Alternative rejected.** Arbitrary integer guide indices would add override complexity without improving the bounded lesson objective. Three positions cover the meaningful branch structure while remaining exactly observable.

**Probe/failure mode.** Full endpoint/choice override tests compare production `observe_overrides` against an independent observer. Accidental second full gray lines are prevented constructively and diagnosed by `self_check`.

## D4 — Vary target side, count, and clipping

**Choice.** Emit 2–7 non-selector target cells with layouts `selector_side`, `opposite_side`, or `both_sides`. One profile puts every mirror out of bounds and intentionally yields an identity output.

**Rationale.** Opposite-side cells refute the strongest canonical-compatible rival. Both-side scenes establish bidirectionality. The clipped profile teaches that reflection is conditional on bounds rather than an always-changing operation.

**Alternatives rejected.** Keeping all sources on the selector side preserves the baseline shortcut. Forcing every mirror in bounds hides lawful canonical identity behavior. Reflecting the selector would contradict a canonical horizontal example.

**Probe/failure mode.** The exact counterexample in `checks/shortcut/` differs at `(2,1)`, `(4,0)`, `(5,0)`, and `(5,4)`. Separate tests distinguish the authority from both `selector_side_only` and `mirror_selector_too`.

## D5 — Broaden distractors and palettes without changing the rule

**Choice.** Emit 2–6 distractor cells using one or two distinct nonzero, non-gray, non-target colors. Allow 0–3 isolated gray noise cells outside the complete guide.

**Rationale.** The baseline fixed one distractor and exactly four colors, while canonical examples reach five colors. Two distractor colors and isolated gray cells prevent “all gray belongs to the guide” and fixed-palette shortcuts while staying within the positional guide rule.

**Alternatives rejected.** Dense textures or multiple complete guides would introduce genuine authority ambiguity. More than two distractor colors did not add a new rule branch.

**Probe/failure mode.** Distribution tests verify both 4- and 5-color palettes, exact distractor controls, and unique-guide validity. A distractor or isolated gray cell may occupy a reflected destination; the authority correctly overwrites it, which is lawful paint semantics.

## D6 — Separate broad authority validation from narrow generated defaults

**Choice.** `self_check` accepts structurally lawful 5–30 grids, including all canonical pairs, while `generate` advertises an exact 8–11 by 9–12 envelope.

**Rationale.** A validator should not reject lawful canonical inputs merely because the training distribution is intentionally bounded. Generated controls remain honest and observable.

**Alternative rejected.** Restricting `self_check` to generated dimensions would repeat the baseline's canonical rejection. Expanding generation to 30×30 would spend lesson budget on scale rather than semantic branches.

**Probe/failure mode.** Canonical acceptance, malformed-grid diagnostics, and generated endpoint checks are separate tests.

## D7 — Keep independent review tooling task-local

**Choice.** Add `workspace/reference_probe.py` rather than importing production helpers into tests.

**Rationale.** The probe normalizes compact canonical rows, independently identifies guides and outputs, implements rivals, observes axes, and calls the real Racket authority without fallback. This reduces correlated implementation error and gives future agents reusable evidence machinery.

**Alternative rejected.** Testing `_intended_output` against itself would only prove internal consistency. Copying shared private runners would make the artifact brittle.

## D8 — Treat finite semantic evidence honestly

**Choice.** Report the 300-lesson census and exhaustive schedule rotations as evidence against declared rivals, not proof of unique induction.

**Rationale.** The shared census checks fixed demo/query assembly and a finite rival list. The task-local rotation test closes one known gap but cannot enumerate every conceivable hypothesis.

**Remaining limitation.** Generated dimensions and profile families are bounded. Unknown rivals may exist outside the tested hypothesis set.
