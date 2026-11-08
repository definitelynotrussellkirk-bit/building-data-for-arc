# Working notes: bd8613daf5b1

## Review identity

- Assignment: `review-0c1966174e70c16d`
- Pinned baseline generator SHA-256: `882119a9b9fa8ec4ddb2aa6bf7c1fa662d2364a9ef62aa5ccef0696bc991b7b3`
- Final generator SHA-256: `3310718ba33634ae252ec8a3711219641ff23b44e4b701825b0c8fb601f2300d`
- Canonical rule hash: `94cb476392e1`
- Prior return used as a lead: none. The retained catalog hash matched the pinned baseline, and no task-specific prior repair was present.
- Racket authority changed: no.

## Measured baseline defects

The completed before battery had 7 green stages, 2 advisories, and 3 failures (`lint`, `defect_lint`, `override`). It found no `RULE_HASH`; a dead singleton `position_bias`; four byte-identical helpful textures; negative fixtures mixed into the lawful texture domain; canonical maximum-object median 33 outside generated range 8–20; permissive validation accepting blank/full impostors; no exact canonical profile in 60 draws; no semantic witness/rival contract; and 8,534 override findings in 84,780 draws across 942 cases. See `checks/before/`.

## Selected design

1. **Truthful controls only.** `AXES` now advertises exact `grid_h` and `grid_w` controls because both are directly observable in returned pixels. Unknown keys, invalid types/ranges, and invalid difficulties fail loudly. Every legal size remains available in every difficulty band; bands bias defaults instead of shrinking the legal contract.
2. **Thick, varied binary geometry.** A connected mask grows stochastically inside a 5×5–7×7 local box around a guaranteed solid 3×3 core. This guarantees onion depth at least 2 while producing object sizes through the canonical 33-cell regime. A separate paired profile supplies two disconnected thick components.
3. **Canonical profile anchors.** Monochrome schedule residues use 9×9 and 11×11 canvases with one foreground color, matching both public canvas/palette profiles in every band. Other residues draw broadly over 9–18 by 9–20.
4. **Shortcut witness schedule.** Four of six residues partition one connected binary component into exactly two connected color regions. The authority ignores this boundary; the declared wrong rule `peel_each_color_separately` does not. Every three consecutive demonstrations contain a witness, and every four-pair cyclic window keeps at least one witness under any single query rotation.
5. **Semantic and structural validation.** `self_check` rejects malformed cells, blank/full grids, border-touching components, more than two binary components, and components with no interior. `strict_canonical_like`, semantic witness/rival registries, `lesson_identifiable`, `observe_overrides`, and a diagnostic Python mirror make the contract executable.

## Rejected iterations

- A small fixed shape library passed correctness but produced only 8 distinct outputs in the linter sample; it was replaced by stochastic connected growth.
- Alternating stripe colors made one binary component look like roughly six exact-color objects to the generic distribution detector; a two-source connected partition keeps the intended witness while matching canonical object-count scale.
- Broadly sampled monochrome canvases left only 18.3% of the census inside the canonical envelope. Binding the two monochrome residues to the public profiles raised support without narrowing multicolor witnesses.

## Final evidence and limitations

- Final battery: all 12 stages green (`checks/after-final1/`).
- Task tests: 54 passed, including real Racket parity and all six cyclic schedule starts across all four difficulty values and every query rotation (`checks/task-tests-final/`).
- Production lesson census: 300 lessons, 1,200 rotations, 1,160 unique inputs, zero declared-rival ambiguities or scoring errors (`checks/lesson-census-final.json`).
- Independent probe: 237 unique inputs in 240 draws, 160 multicolor witnesses, 160 counterexamples to the canonical-fitting color-splitting shortcut, maximum component size 42, and zero self-check/mirror failures (`checks/reference-probe-final2.json`).

The generator deliberately covers a bounded grammar: one or two components, local component boxes no larger than 7×7, and one or two foreground colors. The finite declared-rival census is evidence against one plausible canonical-fitting shortcut, not a proof of unique induction against every possible rule. Imported associated notes remain in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `3310718ba33634ae252ec8a3711219641ff23b44e4b701825b0c8fb601f2300d`.

# Decisions — bd8613daf5b1

The original task notes contained no rationale beyond the imported summary, so “original rationale” below is either directly observable from the baseline source or marked unknown. Evidence paths refer to this return.

## D1 — Keep the Racket authority unchanged

- **Original choice/rationale:** The canonical program peels cardinal layers of binary foreground components and crops the depth map. Why the original generator lacked a `RULE_HASH` pin is unknown.
- **Decision:** Pin `RULE_HASH = "94cb476392e1"`; do not edit canonical data or the Racket program.
- **Alternatives considered:** Change the rule to split by color, or constrain all generated objects to one color. Both would contradict or underteach the canonical transformation.
- **Probe:** All three canonical pairs match the independent mirror; 27 canonical/generated grids match public `Catalog.apply` in task tests.
- **Failure mode/limit:** A Python mirror can share conceptual mistakes; real Racket parity and authority-sync therefore remain required.

## D2 — Advertise only observable exact size axes

- **Original choice/rationale:** The baseline advertised roughly ten controls, including singleton/dead `position_bias`, palette aliases, component counts, and negative textures. The intent appears to have been broad combinatorial metadata, but many values did not affect bytes or were rejected by difficulty-specific draw bounds.
- **Decision:** Keep only exact `grid_h` (9–18) and `grid_w` (9–20). Validate unknown keys/types/ranges and invalid difficulties before generation. Difficulty biases defaults but never changes the legal exact-control domain.
- **Alternatives considered:** Repair every legacy axis, or mark them diagnostic. That would preserve unnecessary surface area without adding task-relevant variation.
- **Probe:** The baseline override matrix produced 8,534 findings in 84,780 draws; final override stage is green. Tests exercise `(9,9)`, `(11,11)`, and `(18,20)` in all four difficulty values and verify `observe_overrides` plus `GenCtx` provenance.
- **Failure mode/limit:** Component count, shape size, color count, and schedule profile are intentionally not user overrides; they remain sampler-controlled.

## D3 — Use stochastic thick components around a guaranteed 3×3 core

- **Original choice/rationale:** Baseline objects were small (generated range 8–20 cells) despite canonical maximum-object median 33. The original shape rationale is unknown.
- **Decision:** Grow connected masks within 5×5–7×7 boxes around a solid 3×3 core, then rotate/reflect and place with a one-cell canvas margin. Profile-specific target ranges span 13–45 cells; observed final maximum was 42 in 240 draws.
- **Alternatives considered:** A fixed library of rectangles/crosses/diamonds and unconstrained random walks. The fixed library produced only 8 distinct outputs in the linter sample; unconstrained walks did not guarantee depth >1.
- **Probe:** `checks/lint-initial/` preserves the low-diversity failure. Final linter/diversity stages pass, and task tests require maximum component size at least 33.
- **Failure mode/limit:** Local boxes cap shape extent at 7×7; the grammar does not cover arbitrarily large or thin components.

## D4 — Include one- and two-component cases

- **Original choice/rationale:** Canonical examples use one component, while the rule naturally supports multiple components. The baseline component-control rationale is unknown.
- **Decision:** Most profiles use one component; `monochrome_pair` uses two disconnected thick components in one global crop.
- **Alternatives considered:** Canonical-only one-component generation or many components. One component undercovers the rule's compositional behavior; many components would drift farther from canonical examples and increase accidental shortcuts.
- **Probe:** `self_check` requires one or two binary components, and the final distribution/defect gates pass.
- **Failure mode/limit:** Multi-component examples are only one sixth of the deterministic schedule and use a constrained paired layout.

## D5 — Teach color invariance with exactly two connected color regions

- **Original choice/rationale:** Baseline helpful palette textures were byte-identical, so foreground color carried no teaching information. Canonical examples are monochrome and admit the plausible wrong rule “peel each exact-color component separately.”
- **Decision:** Four of six schedule residues partition one connected binary shape from adjacent seeds into exactly two connected color regions. The binary core center remains interior while one exact-color neighbor differs, guaranteeing disagreement with the color-splitting rival.
- **Alternatives considered:** Random per-cell colors, alternating stripes, or monochrome-only data. Random colors create many tiny objects; stripes triggered measured object-count drift (~6 generated versus ~1 canonical); monochrome-only lessons leave the shortcut unresolved.
- **Probe:** 160/240 final samples are multicolor and all 160 refute the rival. The 300-lesson/1,200-rotation census found zero surviving declared-rival ambiguities.
- **Failure mode/limit:** Only two foreground colors are used per witness, and the finite rival registry does not cover every color-conditional hypothesis.

## D6 — Bind monochrome residues to public canonical profiles

- **Original choice/rationale:** Baseline had zero exact canonical-profile hits in 60 draws. Broad random dimensions in the first repair improved exact hits but yielded only an 18.3% canonical-envelope rate.
- **Decision:** `monochrome_core` uses 9×9 and `monochrome_pair` uses 11×11; both use one foreground color, matching the public `(9,9,2)` and `(11,11,2)` grid/palette profiles. Multicolor residues continue broad dimension sampling.
- **Alternatives considered:** Increase random weight near 9/11 or force all draws to canonical sizes. Weighting did not guarantee per-band support; forcing all draws would destroy useful canvas variation.
- **Probe:** `checks/after/` retains the failed 18.3% run; final profile floor passes every band.
- **Failure mode/limit:** Monochrome status correlates with the exact profile residues. Multicolor 9×9/11×11 cases exist, reducing but not eliminating profile correlations.

## D7 — Harden structural validation

- **Original choice/rationale:** Baseline `self_check` accepted blank grids, full single-color grids, and all sampled negative textures. The intended validator scope is unknown.
- **Decision:** Require rectangular integer colors 0–8, dimensions in contract, visible background and foreground, one or two binary components, one-cell margins, and at least one interior cell in every component.
- **Alternatives considered:** Validate only shapes emitted by the current sampler or enforce the exact six schedule profiles. The first is too permissive; the second would reject lawful canonical/general inputs and overfit implementation details.
- **Probe:** Task tests include malformed, blank, full, boolean, and out-of-palette impostors; final self-check and defect-lint stages are green.
- **Failure mode/limit:** The validator accepts some lawful grids the production sampler never emits, by design; strictness is semantic rather than byte-for-byte profile membership.

## D8 — Deterministic six-residue lesson schedule

- **Original choice/rationale:** No executable lesson-identifiability contract existed.
- **Decision:** Use `W, N, W, W, N, W`, where `W` is a multicolor witness and `N` a monochrome anchor. Every three consecutive demos include a witness; any four-pair window retains one after any query holdout.
- **Alternatives considered:** Independent Bernoulli witness sampling or resample-until-identifiable. A deterministic schedule gives a cheap exhaustive proof over all cyclic starts and avoids unbounded rejection loops.
- **Probe:** Task tests enumerate all six starts, all four difficulty values, and all four query rotations. The production census independently samples 100 lessons per band and rotates every query.
- **Failure mode/limit:** The shared census does not enumerate every possible schedule start, so the task-local exhaustive test is part of the contract.

## D9 — Reusable independent probe

- **Original choice/rationale:** No task workspace tool existed beyond a placeholder README.
- **Decision:** Add `workspace/reference_probe.py` with an independent onion mirror, canonical shortcut, canonical helper use, source-selectable generator loading, profile/uniqueness metrics, and public Racket parity.
- **Alternatives considered:** Put all logic in production or tests. Keeping it in the workspace lets future reviewers inspect and rerun measurements without expanding production API.
- **Probe:** `checks/reference-probe-final2.json` is the final 240-draw report; task tests import the probe through the portable task-test runtime.
- **Failure mode/limit:** The mirror is still a human transliteration; authority comparison remains the final oracle.
