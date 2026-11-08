# Working notes: 2d5acf84dd20

The retained audit `review-9f53d3b826ce7dc0:v0001` was used only as a lead. It identified that the imported 2.0.1 generator emitted separated blobs, making the unchanged authority teach bounding-box-area ranking rather than the canonical nested-frame concept.

Version 3.0.0 replaces that distribution with strict nested rectangular outlines. Exact overrides are `frame_count`, `layout_style`, and `outer_margin`; all are observable from pixels. A deterministic four-profile schedule gives every ordinary four-demo lesson shallow/deep depth evidence and offset/canvas-distance separators.

An intermediate 300-lesson census found one `recenter_frames` ambiguity because an offset stack could accidentally be centered in the canvas. Final offset profiles are therefore guaranteed off-center. The final 300-lesson / 1,500-rotation census found no ambiguity in the declared rival family.

The Racket authority and canonical data were not changed. Finite declared-rival checks do not prove universal identifiability.
## Current reviewer considerations

Source SHA-256: `41632e8f4cf17e612feff15a8723b35690448652e40a3e14ebce64c2d135eada`.

# Decisions for `2d5acf84dd20`

## D1 — Preserve the Racket authority; repair the input domain

**Choice.** Keep the canonical Racket rule and `RULE_HASH=9cbecad9efb8` unchanged. Restrict generated inputs to strictly nested frames, where descending bounding-box area is exactly the same ordering as containment depth.

**Rationale.** Every canonical pair has nested rectangular frames. The retained prior audit `review-9f53d3b826ce7dc0:v0001` suggested that the baseline's disjoint blobs—not the authority on canonical examples—created the semantic defect. The before battery independently confirmed missing grounding and contract failures. The final rule smoke and authority-sync stages pass against authority-set SHA `b4a968a9f525c26d48dc80cc21ed163eaa364b39c86f12788c0d94c795979b2a`.

**Alternatives rejected.** Changing the Racket rule to compute explicit containment would alter authority unnecessarily; continuing to emit disjoint blobs would preserve R1; supporting both nested and disjoint scenes would teach two different concepts and make the intended abstraction underdetermined.

**Probe.** `test_prior_disjoint_area_rank_counterexample_is_rejected` retains the exact old morphology as a negative. All five canonical pairs must pass `self_check`, `strict_canonical_like`, and the Python mirror.

**Limit.** The generator does not claim that area ranking means containment on arbitrary component arrangements. Its lawful domain is explicit and narrower.

## D2 — Use 2–4 complete rectangular frame components

**Choice.** Emit 2, 3, or 4 separate four-connected color-1 outlines. Permit the canonical 1×1 and 2×2 innermost cases; reject other one-cell-wide line shapes and incomplete outlines.

**Rationale.** Canonical examples cover shallow and deeper stacks, including small innermost frames. Four frames use output colors 2–5 while keeping the scene compact and within ARC limits. Multiple depths are necessary to distinguish flat-red, two-level, and reverse-depth rivals.

**Alternatives rejected.** A fixed depth would permit depth-count shortcuts. More than four frames adds palette/depth behavior not grounded by the canonical ledger. Filled rectangles or broken outlines change the canonical morphology.

**Probe.** Semantic witnesses require 2-, 3-, and 4-frame examples; the final 600-draw gate fired all three. The strict validator verifies exact outline cell sets.

**Failure modes.** Touching frames merge into one component; duplicate bounding-box areas make order ambiguous; malformed tiny lines can mimic frames. The validator rejects all three.

## D3 — Require strict nesting and a blank moat

**Choice.** Each inner frame must lie at least two cells inside every side of the adjacent outer frame, leaving at least one black-cell moat.

**Rationale.** This makes components separate under four-connectivity and makes containment order unambiguous. It also preserves the visual mechanism in the canonical data.

**Alternatives rejected.** One-cell insets make outlines touch; arbitrary spacing without a minimum risks connectivity changes; nonnested placement recreates R1.

**Probe.** `_analyze` records side-specific insets and rejects any minimum inset below two. The old disjoint counterexample is retained as a regression.

**Limit.** The distribution does not cover diagonal touching, overlapping, open, or partially occluded frames.

## D4 — Vary `layout_style` between concentric and offset

**Choice.** `concentric` uses symmetric two-cell insets. `offset` makes at least one side of each expansion three cells, and final placement forces the stack off the global canvas center.

**Rationale.** Canonical demonstrations happen to be centered, so “redraw frame sizes around the canvas center” fits all five. Offset nesting separates location preservation from frame-size/depth behavior. The first implementation allowed an offset stack to land globally centered; the full census caught exactly one ambiguous lesson (R3), so the final implementation makes this discriminator structural rather than probabilistic.

**Alternatives rejected.** Random placement with no off-center guarantee failed the 300-lesson census. Making every scene offset would lose a clean canonical-style anchor. Translating only the whole concentric stack would refute recentering but not exercise asymmetric containment.

**Probes.** `test_offset_profiles_always_refute_recentering`, the exact retained ambiguity, every query rotation of a five-pair bundle, every cyclic four-demo window, and `workspace/probe_shortcuts.py`.

**Failure modes.** Equal opposing canvas margins can globally center an asymmetric stack. `_place_boxes(..., force_offcenter=True)` deterministically adjusts a margin or raises rather than silently returning such a case.

## D5 — Vary `outer_margin` between edge and inset

**Choice.** `edge` pins at least one side of the outer frame to the canvas boundary. `inset` leaves at least one black cell on all four sides.

**Rationale.** A canonical-fitting shortcut colors from distance to the canvas boundary. Edge and inset examples with preserved frame depth provide direct counterexamples while maintaining the nested-frame grammar.

**Alternatives rejected.** Always edge-bound scenes conflate depth with canvas distance; always inset scenes weaken exact canonical envelope coverage.

**Probe.** `edge_canvas_distance_killer` must fire; the final gate found it in 436/600 draws. `workspace/probe_shortcuts.py` verifies an actual emitted disagreement for `canvas_distance`.

**Failure modes.** Random margins can exceed 30×30 or misclassify an intended edge scene. Margin construction trims to capacity while respecting mode-specific floors, then `observe_overrides` verifies pixels.

## D6 — Expose exactly three caller-facing axes

**Choice.** The supported overrides are `frame_count` (2–4), `layout_style` (`concentric|offset`), and `outer_margin` (`edge|inset`). Unknown keys and invalid values reject loudly.

**Rationale.** Each axis is recoverable from pixels and affects the semantic teaching distribution. Grid dimensions and raw offsets are implementation details and would add combinations without a distinct task concept.

**Alternatives rejected.** The baseline advertised `grid_h`, `grid_w`, and texture controls it did not honor, causing thousands of override/self-check findings. Retaining those names would reproduce the contract failure. A free-form geometry override would be difficult to validate and unnecessary.

**Probe.** The exact boundary matrix test covers every band and all boundary/categorical values. The shared override stage accepted 2,160/2,160 draws over 24 cases and rejected an unknown key.

**Failure modes.** Metadata can claim one value while pixels realize another. `observe_overrides` re-derives all axes from the returned grid, and `self_check` compares requested values to observations.

## D7 — Use a deterministic four-profile teaching schedule

**Choice.** Every four consecutive samples cycle through:

1. `(2, concentric, edge)`
2. `(3, offset, inset)`
3. `(4, concentric, edge)`
4. `(3, offset, edge)`

The production hook returns these exact tuples, matching `SCHEDULE_PROFILES`.

**Rationale.** A normal four-demo lesson contains shallow/deep depth evidence plus two offset discriminators, including both margin modes. This makes declared rival rejection a schedule property rather than a lucky frequency event.

**Alternatives rejected.** Independent random axes can produce four examples that all preserve the same shortcut. Returning numeric schedule indices while declaring tuple metadata caused R2 and was rejected by the task-local test.

**Probes.** Every sliding four-demo window is tested for all three bands and eight starts. `workspace/probe_shortcuts.py` checks all 12 cyclic band/start windows. The final census covers requested starts consecutively over period six and all query rotations of each materialized lesson.

**Limit.** The downstream census reports a period of six from its assembler, while the generator's profile schedule has period four. The task-local cyclic probe covers the generator schedule directly; neither finite check proves resistance to undeclared rivals.

## D8 — Include exact canonical-size anchor canvases without replaying examples

**Choice.** Profile zero uses 9×9 or 10×12 canvases with seed-varying two-frame geometry and one outer side pinned to the canvas.

**Rationale.** This provides exact canonical dimension/palette support and a strong canvas-distance discriminator while avoiding memorized canonical grids.

**Alternatives rejected.** Replaying canonical inputs would reduce diversity and risk memorization. Fully unconstrained sizes failed the baseline profile floor.

**Probe.** Final profile floor: 15/60 exact-profile and 20/60 envelope hits, with all five canonical inputs accepted.

**Failure modes.** An anchor could accidentally duplicate a canonical grid. Geometry is seed-varying; the generator constructs frames rather than loading canonical inputs.

## D9 — Declare executable rivals and witnesses

**Choice.** Rivals are `flat_red`, `only_two_depth_levels`, `reverse_depth`, `canvas_distance`, and `recenter_frames`; the latter two are explicitly marked canonical shortcuts. Witnesses cover each depth and the two canonical-fitting shortcuts.

**Rationale.** Named English counter-hypotheses are not enough for a teaching gate. Executable competitors let the battery and census test whether each demonstration set actually falsifies them.

**Alternatives rejected.** Hard-coding rival names in a separate test tool would drift from the generator. The reusable probe imports the declarations from the selected source.

**Probes.** Final semantic gate: 6/6 witnesses and 6/6 rival claims. Final census: every declared rival refuted in all 100 lessons per band, with 0 ambiguous rotations. Exact canonical fit for `canvas_distance` and `recenter_frames` is verified on 5/5 pairs.

**Limit.** This is a finite declared-rival family. Other plausible rules can exist; results must not be presented as a mathematical uniqueness proof.

## D10 — Keep generation deterministic, fresh, and global-RNG pure

**Choice.** Use `gen_ctx`-derived RNG streams; return newly allocated grids and never mutate global `random` state.

**Rationale.** Reproducible seeds/sample indices are necessary for audit and census replay, and fresh objects prevent cross-example contamination.

**Probe.** `test_replay_is_deterministic_fresh_and_global_rng_pure` checks byte-equivalent replay, independent row objects, mutation isolation, and unchanged global RNG state.

## D11 — Retain compact, replayable evidence and a reusable probe

**Choice.** Keep all decisive failures, exact counterexamples, final reports, and both complete census JSON files. Store the two 16 MB census reports losslessly as gzip with source sizes/SHA-256 and restoration instructions in `checks/census/EVIDENCE_MAP.json`. Add `workspace/probe_shortcuts.py` for future agents.

**Rationale.** The return has a 25 MiB expanded budget, while duplicate full stage directories do not add acceptance value. The compact mapping preserves exact bytes; the probe prevents future agents from copying a stale rival list.

**Alternatives rejected.** Dropping the failed census would erase the evidence that motivated R3. Keeping every duplicate successful rerun would exceed the handoff's intended size and obscure the final source-bound run.

<!-- arcpuzzles-trainer-ambiguity:start -->
## Current trainer ambiguity follow-up

Claude supplied 1 exact canonical lesson(s) with a proposed alternative rule. Retained privately with source hashes and all stored queries: `evidence/trainer-ambiguity-current/current.json`. These are **open describer flags**, not confirmed wrong labels or failed current parametric qualifications. Check whether the proposed rival fits every demonstration and changes any stored query; distinguish source revisions before repairing. Approval and training state are unchanged.
<!-- arcpuzzles-trainer-ambiguity:end -->
