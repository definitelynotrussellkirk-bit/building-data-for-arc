# Working notes: 5573cf8e2aa4

## Review finding

The selected Racket rule was already correct and synchronized. The defect was the training distribution and its contract:

- the old generator declared nine axes, several of which were singleton, aliases, inert, or not probeable;
- `self_check` accepted almost any rectangular input and rejected none of the destructive mutations in the baseline battery;
- there was no semantic contract, no rule hash, and no lesson-level rival analysis;
- all generated panels used different fixed colors, so raw cell inequality was answer-equivalent to occupancy union;
- hard-band draws had no exact canonical 5x11/four-color support;
- scattered independent cells produced far more connected objects than the canonical scale;
- unknown overrides were silently accepted.

## Implemented design

- Kept Racket rule hash `59a18f0cd9d4` unchanged.
- Reduced the public contract to four exact, observable axes: `grid_h`, `half_w`, `palette_size`, and `relation_profile`.
- Built panel supports as contiguous intervals on a randomized 4-connected snake. Each panel therefore remains one connected object while every ordinary draw contains blank, left-only, right-only, and overlap cases.
- Scheduled one strict canonical anchor in every three consecutive samples. Anchors preserve 5x11 shape and the canonical left/right color roles; ordinary samples use one shared panel color so occupied overlap falsifies raw cell inequality.
- Added strict structural validation, canonical ownership, a Python rule mirror, named rivals/witnesses, and lesson identifiability.
- Added focused regressions for canonical pairs, exact overrides, unknown-key rejection, semantic rivals, pinned profile support, mutation rejection, object scale, determinism, global-RNG isolation, canonical metadata, and the official strict-census floor.

## Iteration findings

1. The first after-battery revealed that canonical provenance keys in `meta` were being treated as axis overrides. The validator now checks only keys declared in `AXES`.
2. A one-in-four anchor schedule produced only 10/60 exact-profile samples under the pinned profile sampler. The schedule changed to one-in-three, yielding 24/60.
3. The first one-in-three implementation still allowed anchors to swap panel color roles. The profile gate passed, but the semantic strict census measured only 102/600 (17.0%) against a declared 20% floor. Anchors now preserve canonical roles, yielding 200/600 (33.3%).

## Final evidence

- Focused suite: 12 tests, 64 subtests passed.
- Official after-battery: 12/12 stages green.
- `self_check`: 60/60 default samples clean, 3/3 canonical inputs accepted, 66/66 destructive mutations rejected.
- Canonical profile: 24/60 exact and in-envelope.
- Semantic census: 200/600 strict canonical-like, all four witnesses firing, all four rival claims verified, 12/12 lessons identifiable.
- Diversity: 99% unique inputs and 71% unique outputs over 300 pairs.
- Override contract: 8,910/8,910 draws accepted across 99 cases; unknown key rejected.
- Racket execution parity and selected-authority synchronization passed.

## Remaining scope

The generator intentionally uses individually monochrome panels and path-like connected supports. The authoritative rule is broader: it applies to arbitrary nonzero colors and arbitrary support geometry. The present curriculum covers the decisive occupancy truth table and color invariance, but a future expansion could add multicolor-within-panel and disconnected-within-panel examples while preserving lesson identifiability and canonical support.
## Current reviewer considerations

Source SHA-256: `741c159b6ea59db191c59de14107e63bb8eef78c994996e9318d463f8c2746a9`.

# Decisions for 5573cf8e2aa4

## D1 — Keep the selected Racket rule

**Choice.** Leave canonical data and Racket source unchanged.

**Original rationale.** The source implements the written solution and reproduces all canonical outputs. Exact origin of the implementation style is unknown.

**Alternatives considered.** Rewrite the rule to remove style warnings; replace it with a shorter panel-split helper; edit the archival divergent copy.

**Probe.** Rule smoke, canonical pairs, selected-authority synchronization, and execution parity all passed before any generator edit.

**Failure modes / limitations.** The selected rule still carries nonblocking style warnings and an archival `raw_code` copy differs. Rewriting a correct authority would add regression risk without improving the training distribution.

## D2 — Preserve the canonical side-by-side panel grammar

**Choice.** Use equal left/right panels separated by one centered full-height maroon(9) column.

**Original rationale.** This is the exact canonical representation and the Racket split logic expects it.

**Alternatives considered.** Top/bottom panels, multiple divider columns, off-center panels, or variable panel sizes.

**Probe.** All three canonical inputs are accepted; broken or off-divider inputs are rejected; rule mirror matches all canonical outputs.

**Failure modes / limitations.** It does not train invariance to alternative panel layouts, which are outside this task’s canonical grammar.

## D3 — Replace nine weak axes with four exact axes

**Choice.** Declare `grid_h` 5..9, `half_w` 5..9, `palette_size` 1..2, and `relation_profile` sparse/balanced/dense.

**Original rationale.** The old axes appear to have been generated from a generic template; several were aliases, singleton values, or not connected to generation. No stronger original rationale was retained.

**Alternatives considered.** Keep diagnostic axes; expose raw cell counts; expose color identities; retain degenerate textures.

**Probe.** `observe_overrides` recovers every axis exactly. The override gate accepted 8,910/8,910 draws and rejected unknown keys.

**Failure modes / limitations.** Four axes intentionally describe only observable curriculum choices. Color identities and relation counts remain internal variation, not caller contracts.

## D4 — Use connected snake intervals instead of scattered cells

**Choice.** Place a run of left-only, overlap, and right-only relations along a randomized 4-connected Hamiltonian path.

**Original rationale.** The old generator used shuffled independent cells. That created high superficial diversity but many disconnected objects unlike the canonical examples.

**Alternatives considered.** Random independent points; rectangles; arbitrary flood-filled blobs; direct copying or perturbation of canonical masks.

**Probe.** Focused object-count regression caps generated same-color 4-connected objects at six; defect lint and diversity both pass.

**Failure modes / limitations.** Supports are path-like and each panel is connected. The authoritative rule also permits disconnected or more irregular supports.

## D5 — Guarantee the full occupancy truth table

**Choice.** Every ordinary draw contains at least one both-zero, left-only, right-only, and occupied-overlap coordinate.

**Original rationale.** The old sampler probabilistically added overlap and could leave decisive relations absent from a lesson.

**Alternatives considered.** Purely random relation counts; allow no-overlap or panel-empty degenerate examples; rely on many examples to eventually cover relations.

**Probe.** Relation-count tests and semantic witnesses fire on every relevant draw. Intersection, XOR, copy-left, and copy-right rivals are all refuted.

**Failure modes / limitations.** Requiring all relations in each ordinary input narrows natural frequency variation. Canonical inputs without overlap remain accepted as explicit canonical exceptions.

## D6 — Schedule same-color overlap counterexamples

**Choice.** Non-anchor unoverridden samples use the same foreground color in both panels.

**Original rationale.** Fixed different colors in the old generator made raw cell inequality indistinguishable from occupancy union: an occupied overlap had different values and therefore still produced cyan under the wrong rule.

**Alternatives considered.** Randomly choose same versus different colors; use multicolor panels; add a separate degenerate texture.

**Probe.** Every three consecutive samples include two same-color examples. The `same_color_overlap` witness fires 400/600 times, and the raw-inequality rival is verified to disagree on all 60 checked witness grids.

**Failure modes / limitations.** Same-color examples are scheduled rather than independently random. Within-panel multicolor invariance is not covered.

## D7 — Insert one strict canonical anchor every three samples

**Choice.** Unoverridden sample indices divisible by three produce a 5x11 input with left red(2), right green(3) or yellow(4), divider9, and four total colors.

**Original rationale.** The baseline hard band had no exact canonical-profile support. The first attempted one-in-four schedule was too sparse under the pinned sampler.

**Alternatives considered.** One-in-four anchors; probabilistic anchors; force every sample to canonical dimensions; separate schedules by difficulty.

**Probe.** Pinned profile floor is 24/60 exact. The semantic census is 200/600 strict canonical-like. A regression reproduces the official 600-draw census.

**Failure modes / limitations.** A sample-index schedule can interact with downstream subsampling. The official pinned samplers now cover it, but an external loader that selects only one residue class could bias the curriculum.

## D8 — Preserve left/right color roles on anchors only

**Choice.** Ordinary examples may swap relation roles; strict anchors never swap red-left and green/yellow-right.

**Original rationale.** Random role swapping was useful to prevent left/right location shortcuts, but it silently cut strict canonical support in half.

**Alternatives considered.** Never swap roles; relax `strict_canonical_like`; lower the declared strict floor.

**Probe.** The failing strict census measured 102/600. After the change it measures 200/600 while ordinary-role variation remains.

**Failure modes / limitations.** Canonical anchors have predictable color roles by design. Ordinary same-color draws and relation-role swaps provide the counterbalance.

## D9 — Make `self_check` a semantic validator

**Choice.** Validate dimensions, divider exclusivity, panel nonemptiness and monochromaticity, allowed colors, decisive relations, profile occupancy, and exact overrides. Ignore non-axis provenance metadata.

**Original rationale.** The old validator intentionally permitted degenerate cases and rejected none of the destructive mutations.

**Alternatives considered.** Structural-only validation; require connectivity; reject canonical no-overlap examples; validate all metadata as overrides.

**Probe.** 66/66 destructive mutations are rejected, 60/60 generated inputs are accepted, and 3/3 canonical inputs are accepted.

**Failure modes / limitations.** It cannot validate output correctness because its API receives only an input grid. It also permits canonical exceptions at union sizes seven or eight to own the real data.

## D10 — Add explicit semantic rivals and lesson checks

**Choice.** Declare intersection, occupancy XOR, copy-left, copy-right, and raw cell inequality as named wrong rules; declare witnesses and require three-example lessons to refute them.

**Original rationale.** No prior semantic contract existed. High uniqueness alone did not establish that the intended rule was learnable.

**Alternatives considered.** Rely on comments; test only the Python mirror; use a learned solver as evaluator; enumerate every conceivable shortcut.

**Probe.** The semantic gate verifies all four witness-to-rival claims and all 12 pinned lessons across three difficulty bands.

**Failure modes / limitations.** The list is finite and task-authored. An unanticipated shortcut can still survive, motivating the counterfactual gate proposed in `QUESTION_ANSWER.md`.
