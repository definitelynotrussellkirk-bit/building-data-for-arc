# Working notes: 17de34436a9f

## Review result

Version 2.1.0 mixed lawful generation with negative textures and advertised eight
axes that were mostly constants, aliases, or unobservable. Exact dimension
requests were frequently ignored, unknown keys were accepted, and the summary's
fixed 3–4-cell bank no longer matched the random 3–6-cell implementation.
`self_check` also accepted several malformed structures.

Version 3.0.0 replaces that surface with five observable exact controls:
`grid_h`, `grid_w`, `marker_corner`, `body_size`, and `body_color`. Unknown keys
fail loudly. Shapes come from deterministic, enumerated, 4-connected polyomino
banks with four distinct rotations; legal placements are enumerated, so there is
no retry exhaustion or silent fallback.

## Curriculum decision

The canonical set has one bottom-right example whose body is invariant under a
180° turn. Therefore the wrong rule “bottom-right means identity” fits all five
canonical pairs. Four sequential demonstrations now cover all four marker
meanings, and generated bottom-right bodies are rotation-asymmetric. Named rivals
and `lesson_identifiable` check that no declared rival fits every demonstration
while changing the query.

## Structural scope

Malformed non-integer or unhashable cell values return a color-domain error
before object analysis; they do not raise from sorting or set construction.

`self_check` enforces rectangular ARC grids, one corner marker, a 4–7-cell
single-color 4-connected body, and marker/body separation. It deliberately does
not reject all symmetric bodies: the canonical bottom-right body is lawful even
though its required transform is visually invariant. Asymmetry is a generation
and teaching constraint, not part of the reference rule's input validity.

Ordinary defaults are 9×9 with body sizes 4–6 to stay on the canonical structural
profile. Exact controls permit 7–14 dimensions and body size 7 for bounded
variation. This finite domain is not evidence of universal rule induction.

## Authority

`RULE_HASH = 9f94f78b9fd2` binds the unchanged Racket authority. The task-local
Python mirror exists for cheap probes; authoritative checks still execute Racket.

Imported associated notes, if any, remain in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `d8284f612540c12feaeafbc93dbf4d3b178cb6d8bbc87d0df787b38e843cbbde`.

# Decisions for 17de34436a9f

Generator source after repair:
`repo/generators/17de34436a9f/generator.py`, SHA-256
`d8284f612540c12feaeafbc93dbf4d3b178cb6d8bbc87d0df787b38e843cbbde`.

## D1 — Replace legacy metadata with five observable controls

**Original rationale.** Unknown. Version 2.1.0 inherited generic axes for palette
kind/size, position bias, color count, density, and texture. Four helpful texture
values were aliases with no behavioral effect; negative fixtures also shared the
same texture domain.

**Decision.** Keep only `grid_h`, `grid_w`, `marker_corner`, `body_size`, and
`body_color`, each directly observable through `observe_overrides`. Reject every
unknown key.

**Rejected alternatives.** Keeping singleton axes for schema compatibility would
continue to advertise nonexistent variation. Keeping negative textures in
ordinary generation would mix malformed inputs into the positive task domain.

**Probe and failure mode.** The baseline override gate found 8,325 findings over
29,970 draws, including ignored dimensions and accepted unknown keys. Final exact
controls pass all boundary/band cases and the authoritative override gate's
39,150/39,150 draws across 435 declared cases with no findings or warnings
(`checks/before/checks/17de34436a9f_before_override_results.json`;
`checks/after/checks/17de34436a9f_after_override_results.json`).

## D2 — Anchor ordinary data to the canonical profile

**Original rationale.** Version 2.1.0 broadened dimensions by difficulty, but the
canonical examples are 9×9 and use 4–6 body cells. The original comments and
summary disagreed about whether bodies were fixed 3–4 cells or random 3–6 cells.

**Decision.** Default to 9×9 and schedule body sizes 4–6; retain explicit 7–14
row/column and 4–7 body-size controls for bounded variation. `MIN_STRICT_FRAC` is
1.0 for ordinary draws.

**Rejected alternatives.** Broad random dimensions by default produced only
5/60 canonical-profile hits in the baseline profile gate, with zero in easy and
hard. Restricting all exact controls to 9×9/4–6 would remove useful bounded
variation without improving the ordinary curriculum.

**Limit.** This is a finite canonical-like domain, not a universal statement that
the Racket rule only accepts those sizes.

## D3 — Teach all four corner meanings in every lesson

**Original rationale.** Random corner choice could omit a transform from a short
lesson. The canonical bottom-right pair is 180°-symmetric, so the wrong rule
“bottom-right means identity” fits all canonical examples.

**Decision.** Set `EXAMPLES_NEEDED = 4` and schedule `tl, tr, br, bl` by
`sample_index % 4`. Test every cyclic start and use asymmetric generated bodies,
so the bottom-right half-turn is visible.

**Rejected alternatives.** Random balancing only in aggregate does not guarantee
that an individual 4-demo lesson identifies the mapping. Rejecting symmetric
inputs in `self_check` would incorrectly reject the lawful canonical BR example.

**Probe.** The retained lesson probe checks 300 lessons/1,500 inputs, all four
cyclic starts, and six declared competitors. Every lesson is identifiable;
`bottom_right_identity` disagrees on 376 generated inputs
(`checks/17de34436a9f_final_lesson_probe.json`).

## D4 — Use constructive asymmetric polyomino banks

**Original rationale.** Version 2.1.0 grew random shapes with bounded retries and
fell back to a small fixed bank. That made exact size realization and failure
behavior hard to reason about.

**Decision.** Enumerate all compact 4-connected fixed polyominoes of sizes 4–7,
retain those with four distinct rotations and maximum dimension 4, then enumerate
all marker-separated legal origins. Select from those finite sets deterministically
through the task RNG.

**Rejected alternatives.** Retry-and-fallback generation can silently change the
requested axis or fail only for unlucky seeds. A single handcrafted shape per
size would create unnecessary duplication and additional shortcuts.

**Failure mode and limit.** An impossible future dimension/shape combination
raises explicitly instead of falling back. Current advertised dimensions all have
legal placements, as covered by tests and the override battery.

## D5 — Strengthen validation without redefining the authority

**Original rationale.** Baseline `self_check` only counted a corner marker, body
cells, and colors. It did not require ARC color values, rectangularity beyond a
shallow check, connectivity, marker separation, or exact marker count.

**Decision.** Validate rectangular integer ARC grids, exactly one corner `9`, a
single-color 4–7-cell 4-connected body, and Chebyshev separation from the marker.
Keep symmetry out of validity because the canonical set contains a lawful
symmetric body.

**Probe.** Eight mutation fixtures are rejected, while every canonical input and
the symmetric canonical BR scene remain accepted. A later adversarial test found
that string or unhashable cells could crash body-color analysis; the failing and
passing TDD runs are retained in `checks/tdd-non-arc-red.log` and
`checks/tdd-non-arc-green.log`. The final checker returns a structured ARC-color
error instead. The final self-check and semantic stages are green.

## D6 — Keep Racket authoritative; add an independent Python mirror

**Original rationale.** The existing contract uses Racket reference rules.

**Decision.** Do not edit Racket. Pin `RULE_HASH = 9f94f78b9fd2`; use
`rule_mirror` only for inexpensive local rivals and volume probes.

**Rejected alternative.** Rewriting or broadening the rule was unnecessary: the
baseline rule smoke already passed, and the defects were in distribution,
metadata, and validation.

**Probe.** The mirror matches all 5 canonical pairs. The final Racket rule-smoke
checks 120/120 applications and Python parity; authority sync remains green.

## D7 — Make lesson identifiability executable and source-bound

**Original rationale.** Version 2.1.0 declared no semantic witnesses, rivals, or
lesson-level check.

**Decision.** Declare fixed-rotation, marker-retention, and canonical-shortcut
rivals; declare witnesses for all four corners and marker removal; implement
`lesson_identifiable`; retain `workspace/lesson_probe.py` with generator,
canonical-rule, and probe hashes.

**Rejected alternative.** Counting witness frequency across independent draws is
insufficient because every witness might occur somewhere while individual
lessons remain ambiguous.

**Limit.** The rival set is targeted, not exhaustive. The probe reports finite
sample sizes, unique-input counts, the exact sampler, and domain limits rather
than claiming universal induction.

## D8 — Add the native rotation-sense family without changing canonical production

**Decision.** Add a task-local native parametric family with private episode
parameter `rotation_sense ∈ {clockwise, counterclockwise}`. The clockwise default
returns the canonical Racket program byte-for-byte (SHA-256
`9f94f78b9fd26ca22f06035669600941ff89acb16f31d9e422bb6a645fec6ff3`);
the alternate swaps the top-right and bottom-left quarter-turn directions while
preserving top-left identity and bottom-right half-turn behavior. The production
generator and canonical ledger remain unchanged.

**Curriculum.** Support independent 2–6 demonstration and 1–4 query counts. The
minimum two demonstrations use top-right and bottom-right markers, and every
query uses one of those demonstrated branches. Later demonstrations add top-left,
bottom-left, and larger scenes without changing the query stream. Inputs are
setting-independent and prefix-stable. The fourth query is a substantive 30×30
case with a 26×24, 372-cell connected body touching the boundary.

**Evidence.** Seven focused parametric tests and the complete 22-test task suite
pass. Retained evidence executes 14 labels through protected Racket. A bounded
32-seed × two-setting × five-demo-count audit covers 320 episodes with no
query-changing survivor among the declared setting and shortcut rivals. Public
exports contain only demonstrations and masked query inputs. Fresh native
qualification binds prototype SHA-256
`1bb8ad7292dd3b6846d96c53358c87883ea133cb104a16fb87cc5b904e579b25`
and promotion SHA-256
`90509bce4720f5080e19b9627b0ac6f7f2d67d0d2a136653a0404ff6ed9d127c`.

**Sequential dependency.** Step A maps the input marker corner through the fixed
episode rotation sense to an input-dependent quarter-turn count. Step B removes
the marker, crops the body, and rotates that crop by the derived count. Two
source-bound protected-Racket counterfactuals change 296 and 66 final cells.
This is bounded causal evidence, not a universal proof of reasoning depth.

**Limit and handoff.** The finite rival audit does not prove unique induction.
The family is reviewer-ready only; exact integrated-source owner replay and
native acceptance remain mandatory before any training admission.
