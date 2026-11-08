# Working notes: 8712c5635d80

## Current rule and domain

A full color-9 column separates two equal square panels. The left panel contains one 4-connected monochrome shape strictly inside its border. The right panel contains a complete monochrome perimeter frame in a different color. The unchanged canonical Racket rule preserves the input and paints the left shape's panel-relative coordinates into the right panel with the frame color.

Generator version `3.0.0` pins `RULE_HASH = 2c2e07bc5619`. Supported exact controls are `panel_size=5..14`, `shape_size=3..9`, and `palette_id=0..55` for all ordered distinct source/frame color pairs from 1..8. Canonical panel sizes 5 and 6 remain weighted in every difficulty band; broader sizes test the same coordinate law.

## Reversed decision

The selected baseline emitted only one right-panel marker and described that shortcut as the domain. The original rationale is undocumented. This was reversed because all three canonical inputs contain a full perimeter frame and all outputs preserve it. The old distribution could teach the rival “keep one marker, stamp the mask, discard all other frame cells.” The repaired distribution always emits the full frame, accepts every canonical input, and retains an executable `single_marker_only` rival plus `counterexamples/single_marker_shortcut.json`.

## Evidence

- Before evidence: `checks/before/checks/8712c5635d80_before_battery_summary.json` records lint, self-check, and defect-lint failures on baseline generator SHA-256 `00c3eafd...`.
- Final generator SHA-256: `72d0ace0331824d8b5d9e6b7e2d9ce0e5ea2cc490c041b20b5bb2d4501168e76`.
- Final battery: `checks/after/checks/8712c5635d80_after_battery_summary.json` — 12/12 stages green.
- Focused tests: `checks/task-tests/result.json` — 29 passed, including canonical ownership, exact controls, the saved shortcut counterexample, determinism, freshness, and global RNG isolation.
- Lesson smoke: two demonstrations plus one query; 12/12 production lessons identifiable and 36/36 diagnostic query rotations unambiguous against the declared rival. No larger lesson census was claimed because the declared rival already disagrees with every full-frame canonical/generated example.

## Limits and open findings

The generator intentionally covers square panels, interior connected shapes of 3..9 cells, and source/frame colors 1..8. It does not claim rectangular panels, border-touching source shapes, color 9 outside the separator, same-color source/frame pairs, or universal identifiability against undeclared rivals. No prior return was used as a repair lead; the selected baseline, canonical examples, and retained check outputs were used directly. No Racket authority changed.
## Current reviewer considerations

Source SHA-256: `72d0ace0331824d8b5d9e6b7e2d9ce0e5ea2cc490c041b20b5bb2d4501168e76`.

# Decisions — 8712c5635d80

## D1 — Restore the complete right-panel frame

**Prior choice:** the baseline generated one colored marker in the right panel. Its rationale was not recorded; the stale summary treated that marker as the whole context.

**New choice:** every generated input has a complete monochrome perimeter frame with an empty interior.

**Why:** all three canonical inputs have that frame and the canonical outputs preserve every perimeter cell. The one-marker distribution made a materially different rule sufficient: delete all right-panel context except one color marker, then stamp the left mask. The saved witness in `repo/generators/8712c5635d80/counterexamples/single_marker_shortcut.json` separates that rival from the authority.

**Rejected alternatives:** (a) retain one marker and merely relax `self_check`; this leaves the shortcut intact, (b) mix marker-only and framed examples; marker-only lessons remain off-manifold and can still weaken training, (c) alter the Racket rule to match the shortcut; canonical behavior proves the authority is already correct.

**Probe:** canonical acceptance, the executable `single_marker_only` rival, and all 600 semantic-gate draws. **Failure mode:** an undeclared rival could still fit finite lessons; the result is not a proof of unique induction.

## D2 — Equal square panels, sizes 5..14

**Choice:** one full-height color-9 separator divides two panels whose width equals grid height. Sizes 5 and 6, the canonical profiles, are weighted in every difficulty band; 7..14 broaden coordinate and frame-length coverage.

**Why:** this preserves exact canonical geometry while preventing a model from equating the rule with one fixed canvas. Size 5 is the minimum that can hold a strict interior connected shape and a meaningful frame.

**Rejected alternatives:** rectangular panels were not demonstrated by the canonical task; sizes below 5 make the declared shape range cramped; unrestricted large panels add cost without a new semantic branch.

**Probe:** profile-floor and strict-profile gates plus exact `panel_size` tests at 5, 6, and 14. **Limit:** rectangular-panel generalization remains unknown rather than silently claimed.

## D3 — Connected interior shapes of 3..9 cells

**Choice:** generate exactly one 4-connected monochrome source shape, strictly inside the left border, with 3..9 cells.

**Why:** it matches canonical object structure and keeps the task about coordinate transplantation rather than segmentation or border overlap. Random growth produces irregular as well as compact masks.

**Rejected alternatives:** single cells and two-cell shapes are too close to marker-copy shortcuts; disconnected sets introduce an unobserved multi-object interpretation; border-touching shapes collide with the frame coordinates and were not canonical.

**Probe:** focused tests sample 24 inputs in each band and assert size, color, margin, and connectivity through `self_check`. **Limit:** multi-object and border-touching variants are intentionally outside the domain.

## D4 — Ordered distinct colors 1..8 through `palette_id`

**Choice:** `palette_id=0..55` indexes every ordered pair of distinct source/frame colors from 1..8.

**Why:** a single exact integer control makes all legal role assignments observable and avoids dead palette metadata. Distinct colors keep source and destination roles visually separable. Color 9 is reserved for the separator; 0 is background.

**Rejected alternatives:** independent color axes make incompatible equal-color combinations possible; allowing 9 outside the separator violates the structural cue; using only canonical color pairs encourages color memorization.

**Probe:** exact override tests cover IDs 0, 17, and 55 in every band; override stage passes. **Limit:** same-color source/frame tasks are not claimed.

## D5 — Pin and preserve the existing authority

**Choice:** pin `RULE_HASH = 2c2e07bc5619`; do not edit the Racket rule.

**Why:** baseline rule smoke already passed, and the rule exactly maps all canonical inputs/outputs. The defect was the generator distribution and validator, not label authority.

**Probe:** final rule smoke, Racket lint, and authority sync are green. Authority sync notes only an archival divergent bank copy; selected execution parity passes.

## D6 — Make the shortcut executable and teachability testable

**Choice:** declare `full_frame_context`, `single_marker_only`, `WITNESS_RIVALS`, `CANONICAL_SHORTCUTS`, and `LESSON_COMPETITORS`; require `lesson_identifiable` to see a frame-preservation disagreement.

**Why:** prose warnings are easy to lose. An executable rival makes the old failure reproducible and lets the semantic gate test each produced lesson.

**Lesson assembly policy:** `EXAMPLES_NEEDED=2`; production smoke materialized 12 lessons (4 per band), each with two demonstrations and one query. All 12 were identifiable. Diagnostic rotation checked 36 held-out positions with no ambiguity. Rotation was inspected but not required by the production policy; no universal claim is made beyond the declared rival and sampled lessons.

## D7 — Strict override and validation contracts

**Choice:** reject unknown keys and non-literal integers; require every accepted grid to satisfy the full frame grammar; expose `observe_overrides` for exact recovery.

**Why:** the baseline had dead texture controls and rejected canonical frames. Exact contracts prevent metadata from promising variation the returned grid does not contain.

**Probe:** lint, defect lint, self-check, strict profile, override stage, and 29 focused tests all pass on final source.
