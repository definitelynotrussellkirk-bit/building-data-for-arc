# Working notes: 4c93dc1552b3

## Current selected design (v3.2.0)

The intended rule is unchanged: find each four-connected blue (1) component that exactly fills a bounding box at least 2×2, then recolor only that component's four corners red (2). Irregular blue components, non-corner blue cells, and every non-blue object remain unchanged. The selected Racket authority remains canonical rule hash `3b0c50f6c708`; this review changed no Racket source.

The generator retains nine observable geometry profiles, three per difficulty band. Each profile preserves its component shapes and whether its blue/distractor components touch an edge, but v3.1.0 replaced reflection-only rendering with deterministic seeded repacking over lawful translations. Blue components are kept at least one king-move apart so independently meaningful objects cannot merge visually. Across seeds 0–255 at sample index 0, every profile produced 256 distinct role layouts and all 2,304 draws passed `self_check`, `teaching_check`, and `strict_canonical_like` (`checks/layout-diversity-final.json`).

The first wide query-rotation census exposed a second issue: ordered production lessons were identifiable, but 201/1,200 held-out-query rotations could lose the only demonstration refuting `bbox_corners_all_blue_components`, `all_solid_rectangles_any_color`, or `interior_targets_only`. Version 3.2.0 adds redundant negative evidence to `easy_pair_8x10` and `medium_triple_9x12`. Every cyclic four-pair window now remains identifiable after any one pair is held out. The final census reports 300/300 production lessons and 1,200/1,200 rotations identifiable against all declared rivals (`checks/lesson-census-final.json`).

## Decisions and assumptions

- The profile name is an exact observable override; component placement is deliberately not exposed as an axis.
- Input palettes contain background 0, source blue 1, one multi-cell distractor color, and one singleton distractor color. Red 2 is reserved for output.
- Geometry is randomized by translation, not by rotation, reflection of individual shapes, scaling, or arbitrary shape synthesis. This preserves the audited semantic witness schedule.
- The strongest canonical-fitting declared shortcut is “recolor corners of every solid rectangle regardless of color.” It fits all five canonical pairs. The final generator emits a solid non-blue rectangle that defeats it; the retained public-Racket witness is under `checks/generator-shortcut-final/`.
- Prior return `external-local-random:a9afe833dbe5` was used as a lead for the finite-profile limitation and required negative witnesses. Its retained claims were remeasured on the pinned selected source rather than accepted as current evidence.

## Known limits

This remains a finite nine-profile shape curriculum. Seeded placement diversity removes the four-reflection absolute-position shortcut, but it does not establish generalization to unseen component shapes, rotations, scales, palettes, or undeclared rivals. The finite rival suite and 300-lesson census establish the reported contract only within the selected generator domain.
## Current reviewer considerations

Source SHA-256: `38ab04b8a77b336ccbf3411a31026607da6f9f516b3de023a5f1743a99981c0a`.

# Decisions: 4c93dc1552b3

## D1 — preserve semantic profiles, randomize only component placement

**Original choice.** The imported v3.0.0 curriculum used nine fixed templates and global reflections. This made every profile semantically clear but limited each to four geometry masks.

**Alternatives considered.** (a) add more hand-written templates; (b) rotate/scale each component; (c) synthesize arbitrary rectangles and irregular objects from scratch; (d) translate the existing components while preserving their shape and edge role.

**Decision.** Use (d). It removes the absolute-position/reflection orbit while retaining the already-audited component shapes, profile signatures, canonical dimensions, override observability, and witness schedule. A deterministic backtracking packer enumerates lawful translations. Separate blue components are forbidden from entering each other's eight-neighbor halo, preventing visual fusion that a four-connected validator alone would miss.

**Evidence.** The regression failed at four layouts before implementation and passed afterward. Final seeds 0–255 yielded 256 distinct role layouts for every profile and zero errors across 2,304 draws (`checks/layout-diversity-final.json`).

**Rejected risk.** Arbitrary synthesis or rotation would broaden shape coverage, but would require re-auditing profile uniqueness, edge obligations, irregular-object semantics, and Racket parity. That expansion is not necessary to fix the measured shortcut.

## D2 — require every cyclic four-pair window to survive any query holdout

**Observed failure.** The first 300-lesson census on v3.1.0 found all 300 ordered lessons identifiable, but 201/1,200 rotations ambiguous. The failures were not label errors: holding out the only negative example could leave `bbox_corners_all_blue_components`, `all_solid_rectangles_any_color`, or `interior_targets_only` consistent with the remaining demonstrations.

**Alternatives considered.** (a) document production ordering and accept diagnostic rotation failures; (b) lengthen lessons; (c) duplicate selected profiles in the scheduler; (d) add witness redundancy inside two existing profiles.

**Decision.** Use (d). It preserves `EXAMPLES_NEEDED = 3`, the public `scene_profile` axis, and the three-profile-per-band schedule. `easy_pair_8x10` gains irregular-blue and solid-wrong-color evidence; `medium_triple_9x12` gains a solid-wrong-color rectangle and an edge target. A focused test enumerates all three cyclic starts, all four held-out query positions, and all three bands.

**Evidence.** Final required-rotation semantic smoke: 48/48 rotations. Final large census: 1,200/1,200 rotations and 300/300 production lessons, with zero ambiguity or scoring/hook errors (`checks/final/`, `checks/lesson-census-final.json`).

## D3 — keep Racket authority unchanged

Canonical pairs and the selected mirror agree; the defects were distributional and pedagogical. The canonical normalized rule hash remains `3b0c50f6c708`. Public `arcpuzzles apply` on the retained shortcut witness matches the intended mirror and defeats the rival. No authority edit was justified.

## D4 — retain a dynamic shortcut probe

The new `workspace/probe_shortcuts.py` reads portable canonical data, iterates the generator's actual `CANONICAL_SHORTCUTS` mapping, finds a lawful generated disagreement, records source/rule hashes, and emits an input for public Racket execution. It does not hard-code a copied rival list or invoke private rule runners. A task-local test verifies that its selected rival fits all canonical pairs and that its witness is inside both generator validators.

## Limits and failure modes

- The generator still uses nine finite component-shape profiles; translation diversity is not shape diversity.
- Placement preserves each template component's edge/non-edge role, so the distribution does not explore every legal edge assignment.
- Eight-neighbor blue separation is a deliberate clarity restriction, stronger than the rule's four-connectivity semantics.
- Finite declared-rival elimination does not prove uniqueness against every imaginable rule.
- The intermediate failed census and TDD-red runs are retained as evidence; they are not final failures.
