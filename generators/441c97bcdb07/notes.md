# Working notes: 441c97bcdb07

## Review repair 3.0.0 (2026-10-06)

The selected baseline already avoided its older disconnected-shape crash, but the current review reproduced two source-bound blockers: it did not pin `RULE_HASH`, and `self_check` accepted nearly any one-color grid. The advertised axes were also not read through `gen_ctx`, so exact overrides were not a trustworthy interface.

The repair keeps the canonical Racket authority unchanged and rebuilds the Python generator around an exact input grammar: one color; exactly three identical 4-connected, non-solid 3–5-cell shapes; origins at TL/TR/BL; a blank separating row and column; and an in-bounds empty BR target. Every public axis is exactly observable from pixels, invalid or unknown controls reject loudly, and `rule_mirror` is diagnostic only.

Both canonical training demonstrations (and the held-out canonical pair) use four-cell motifs, so `four_cell_only` is the strongest retained rival: complete the fourth corner only for tetrominoes. Shape IDs 4 and 7 supply three- and five-cell witnesses. The 16-step schedule alternates witness/anchor roles, making every three-consecutive-demo window and every three-of-four rotation refute that rival while still visiting all ten shapes.

Retained tests exhaust override boundaries, all cyclic teaching starts used by the schedule probe, all query rotations in four-pair windows, canonical parity, structural impostors, replay determinism, shape-bank coverage, and distribution diversity. The 100-per-band source-bound census remains finite evidence against declared rivals, not a proof of universal identifiability.
## Current reviewer considerations

Source SHA-256: `1ff876f8be6890633bff538663e9ab3cf9225ae9731f49ef6aaa4de5e32800af`.

# Decisions and rationale

## D1 — Preserve and pin the canonical authority

**Input and prior rationale.** The canonical task says to add a fourth translated copy at the missing rectangle corner. The baseline Python comments described that rule correctly, and the prior 2.2.0 note documented an already-fixed disconnected-shape crash. No retained associated-note return supplied a different authority.

**Decision.** Leave the Racket source unchanged and pin `RULE_HASH = "a51bdd8a29a6"`. Add an independent Python `rule_mirror` only for diagnostics and tests.

**Alternatives rejected.** Rewriting the Racket program would add authority risk without evidence of a label defect. Treating the Python mirror as authority would violate the packet contract.

**Probe and failure mode.** All three canonical pairs pass strict validation and Python/Racket parity; `rule_smoke` fired 120/120 and authority synchronization passed for active and archival texts. A future canonical edit must change the hash and force re-verification.

## D2 — Replace palette-only validation with the exact task grammar

**Input and prior rationale.** Baseline `self_check` verified only that one nonzero color existed. It therefore accepted full grids, singleton triples, short lines, and solid blocks; the before defect lint rejected only 6/42 structural mutations.

**Decision.** Parse the grid without mutation and require: ARC colors 0–9; exactly one nonzero color; exactly three 4-connected components; identical normalized shape; 3–5 cells; at least two rows and columns; non-solid shape; TL/TR/BL origin pattern; at least one blank separating row/column; and an in-bounds empty BR target. Use the same parser for `self_check`, `strict_canonical_like`, observation, and the diagnostic mirror.

**Alternatives rejected.** Checking only component count still admits mismatched shapes. Checking only bounding boxes admits disconnected or solid impostors. A permissive "canonical-like" validator would make profile numbers meaningless.

**Probe and limitation.** Task tests cover blank, full, singleton, short-line, solid-2×2, missing-copy, mismatched-copy, filled-target, ragged, bad-color, and boolean-cell cases. The strict domain deliberately excludes solid rectangles, one-dimensional shapes, multiple colors, and shapes outside 3–5 cells; those are explicit generator-domain limits, not claims about every conceivable instance the general Racket code could execute.

## D3 — Make the public axis surface small, exact, and jointly realizable

**Input and prior rationale.** The baseline declared `grid_h`, `grid_w`, and `shape_id` but drew dimensions and shape from a private RNG, so controls were not reliable. Its `grid_h/grid_w` lower bound of 8 could not realize the tallest shape twice with a blank gap.

**Decision.** Keep only those three meaningful axes. Set dimensions to 9–22 and shape IDs to 0–9. Validate unknown names, types (including rejecting booleans), and bounds before drawing. Route exact overrides and scheduled defaults through `gen_ctx`, then recover every axis from returned pixels and compare it with recorded draws.

**Alternatives rejected.** Keeping 8 as a lower bound would require incompatible-combination tables. Silently resampling a requested shape would falsify exact control. Adding palette/count aliases would enlarge the contract without changing task semantics.

**Probe and failure mode.** Four boundary combinations across all three bands pass, and the official override stage accepted 46,530/46,530 draws. Any future shape whose extent cannot fit 9×9 must either raise the public lower bound or declare incompatibilities.

## D4 — Use a ten-shape bank with explicit non-four-cell witnesses

**Input and prior rationale.** Both canonical training demonstrations and the held-out canonical pair use four-cell shapes. Consequently, the plausible rule “complete only tetrominoes” fits all canonical evidence.

**Decision.** Retain ten connected, normalized, non-solid shapes spanning 3, 4, and 5 cells. IDs 4 and 7 are the triomino/pentomino witnesses; IDs 0, 8, and 1 reproduce the canonical orientations. Declare `four_cell_only` in `CANONICAL_SHORTCUTS`, `SEMANTIC_RIVALS`, and `LESSON_COMPETITORS`, with executable witness mapping.

**Alternatives rejected.** An all-tetromino bank preserves the shortcut. An all-non-four bank overcorrects and loses canonical anchors. Randomly hoping to sample a witness leaves arbitrarily long ambiguous windows.

**Probe and limitation.** The exact 9×9 counterexample and authoritative output are retained under `checks/shortcut-counterexample/`. Only this strongest source-supported rival is declared; undeclared rivals remain unknown.

## D5 — Deterministic teaching schedule rather than probabilistic witness frequency

**Input and success criterion.** Lessons require three demonstrations, and downstream assembly may rotate any of four labelled pairs into the query position.

**Decision.** Use a 16-step cyclic shape schedule alternating `non_four_cell_counterexample` and `four_cell_anchor`. Every length-3 demonstration window therefore contains a non-four-cell witness, and every 3-of-4 rotation does too, while the period visits all ten shape IDs.

**Alternatives rejected.** Independent random shape selection can produce three or more consecutive tetrominoes. Forcing the witness into a fixed first demonstration supports only one ordering. Increasing demonstration count would spend curriculum budget to compensate for a scheduling defect.

**Probe and limitation.** Tests enumerate 32 starts across three bands and multiple seeds, plus every query rotation for 20 four-pair windows per tested seed/band. The source-bound census checks 100 lessons per band and all 1,200 rotations with zero declared-rival ambiguity. It does not prove universal induction or enumerate hypotheses not declared in code.

## D6 — Preserve useful variety without hiding semantic controls

**Decision.** Defaults use canonical-sized 10×10/10×12 witness scenes and broader easy/medium/hard anchors, keyed random legal origins/spans, and a keyed random nonzero color. Shapes are never rotated or recolored per copy because same orientation/color are part of the intended relation.

**Alternatives rejected.** Fixed positions make coordinate templates attractive. Independent per-copy colors or rotations alter the task. Unbounded random layouts can merge copies or move the BR target out of bounds.

**Probe.** Across 240 default draws, task tests observe all ten shapes, at least four size profiles, at least 220 unique inputs, non-identity outputs, deterministic replay, fresh returned objects, and no global-random mutation. The official diversity and profile-floor stages pass all bands.

## D7 — Test first and retain before/after evidence

The new 18-test suite was first run against a frozen baseline copy: 17 failed and 1 passed for the intended missing behavior. The same tests then passed 18/18 after the repair. The original before battery was externally interrupted after four stages and is retained as interrupted, not presented as a pass: lint and defect lint failed; self-check and rule smoke completed green. The final source-bound after battery completed all 12 stages green with required rotation identifiability.

## D8 — Stop at a source-bound, replayable repair

No Racket authority, shared runtime, canonical row, or unrelated generator was edited. The remaining limitation is epistemic: the finite shape bank, tests, and named-rival census cannot certify uniqueness against every human- or model-invented rule. Catalog approval and training admission remain external and unverified even though this review's required gates are green.

## Parametric admission review 1.0.0 (2026-10-24)

This return adds a native parametric family under `workspace/parametric/`; it does **not** edit the production generator or canonical authority. The default setting, `completion_transform=translate`, preserves the exact 1,268-byte canonical Racket program with SHA-256 `a51bdd8a29a68d931403ff3d56792b2c53d8d8920dd22fecb3aa7af91c1abda7`. The nearby alternative, `span_directed_turn`, first infers whether the source-copy rectangle is horizontally or vertically dominant, then rotates the copied pivot shape clockwise or counterclockwise before painting the missing fourth corner. Its qualified program SHA-256 is `3733f13f0a1f36575ce061c3cadd7c9cf7e5a173cd89c84525755579ba4bd09f`.

The family supports independently selected 2–6 demonstrations and 1–4 queries, with stable query prefixes and four stored queries. The first two demonstrations constructively show both horizontal- and vertical-dominant cases. The fourth query is a substantive 30×30 case containing three copies of a connected asymmetric 25-cell motif rather than a padded small puzzle. Inputs are matched across settings; private settings, programs, and query answers are excluded from public projections.

The required sequential dependency is: (A) locate the TL/TR/BL copies and compare row-span with col-span; intermediate `dominant_span` is `horizontal` or `vertical`; (B) use that value to choose clockwise or counterclockwise rotation and paint the fourth copy. The native witness at `checks/441c97bcdb07/causal/witness.json` selects an exact qualified alternate-setting query and replaces the inferred horizontal intermediate with the vertical branch. Protected Racket changes the final output, so B cannot be selected before A for that case. The companion replay record is `checks/441c97bcdb07/causal/replay.json`.

Focused changed-target tests passed 26/26. The finite self-audit rejected eight declared shortcuts across four two-demo/four-query episodes and 24 labelled pairs, executed 26 protected-Racket evaluations, checked four public projections, and swept 768 episodes / 5,888 pairs across demo counts 2, 3, and 6 with no failures. Native qualification passed both settings at seeds 0 and 17 with three demonstrations and four queries per job, totaling 40 protected-Racket evaluations. These are finite checks, not a universal identifiability or training-gain proof. The result is reviewer-ready only; exact-live-byte owner acceptance and any training admission remain pending.
