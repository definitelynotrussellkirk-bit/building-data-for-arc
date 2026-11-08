# Working notes: efb59efe0080

## Review outcome

Baseline `2.1.0` SHA-256: `734aa995ea376525074c90cae2418e6d28e4a6036e163d5b832f654ccf171801` (retained in `workspace/baseline_generator_2.1.0.py`). Final `3.0.0` SHA-256: `0317cd7ebf2fd286ff60e54b72c1c7e002cb75cc581f6dd8523250c1ed5eaf53`.

No prior return was used as a lead; `evidence/associated_notes.jsonl` was empty.

The baseline failed lint, defect lint, and override checks; profile and semantic gates were advisory. Main causes were a missing rule pin, dead/invalid texture controls, ignored exact axes, sparse canonical-profile support, and no executable semantic contract.

The final design narrows the domain to five canonical canvas profiles and connected 4–8-cell color-2/color-3 masks with normalized bboxes at most 3×3. It constructs every requested size/profile combination, requires overlap and two-sided differences, refutes filled-bbox and absolute-position rivals per example, and alternates crop-required/crop-noop cases by sample-index parity.

## Evidence map

- Before battery: `checks/before/`
- TDD red/green: `checks/tdd/`
- Completed final battery: `checks/after-2/`
- Interrupted first final battery: `checks/after/` (not a pass)
- Portable task tests: `checks/task-tests/`
- 100 lessons/band census: `checks/lesson-census.json`
- Baseline/final cyclic query probes: `checks/window-probe/`
- Post-repair visible-only solve: `solve/`

## Known limits

The generator is diagnostic rather than exhaustive. It does not cover touching objects, disconnected masks, masks outside 4–8 cells, normalized bboxes larger than 3×3, arbitrary canvas dimensions, or color permutations. The five declared rivals are plausible and measured, not complete. Racket remains the label authority.
## Current reviewer considerations

Source SHA-256: `0317cd7ebf2fd286ff60e54b72c1c7e002cb75cc581f6dd8523250c1ed5eaf53`.

# Decisions — efb59efe0080

The selected baseline is preserved at `repo/generators/efb59efe0080/workspace/baseline_generator_2.1.0.py`. No prior return was available: `evidence/associated_notes.jsonl` was empty. “Original rationale” below is taken only from comments/source when present; otherwise it is marked unknown.

## D1 — Keep the selected Racket authority unchanged

**Original rationale:** the baseline documentation described normalized color-mask XOR; the canonical program and all five canonical pairs agreed. No source evidence suggested a rule defect.

**Choice:** pin `RULE_HASH = "1cb444e6f050"`, retain the Racket source unchanged, and use Python mirrors only as diagnostics/tests.

**Alternatives rejected:** rewrite the rule to match the baseline generator’s uncropped wording; add generator-specific behavior to the rule. Both would change authority to accommodate data defects rather than repair the data.

**Probe:** rule smoke, Racket lint, authority sync, canonical-pair oracle comparison.

**Failure mode/limit:** a Python mirror can share a conceptual error with the generator, so label authority remains Racket and the battery/census independently execute it.

## D2 — Replace arbitrary size axes with canonical canvas profiles

**Original rationale:** baseline `grid_h`/`grid_w` sought visual variety. Exact-control semantics were not implemented because raw RNG calls bypassed `gen_ctx`; why they were nevertheless advertised as exact axes is unknown.

**Choice:** expose one categorical `canvas_profile` axis containing the five canonical input dimensions.

**Alternatives rejected:** preserve `grid_h` and `grid_w` ranges; mark them diagnostic; support every rectangular cross-product. These alternatives either retain dishonest exact controls or spend support on dimensions with no canonical grounding.

**Probe:** profile-floor check and exact override tests.

**Failure mode/limit:** the learner can infer the five canvas profiles as incidental support. This is documented and preferable to sparse 3/60 canonical-profile support.

## D3 — Split shape size into exact `size_2` and `size_3`

**Original rationale:** baseline `shape_size` was intended to vary object complexity, but the two objects were independently sampled and the override was ignored.

**Choice:** expose exact realized cell counts separately for colors 2 and 3, each 4–8.

**Alternatives rejected:** a single approximate size band; independent hidden random sizes; 1–9 cells. Separate exact axes are directly observable and cover every 25-value cross-product. Sizes 4–8 keep enough internal shape detail for rivals while preserving constructive support in both crop profiles.

**Probe:** full size cross-product tests for both schedule residues and every difficulty band; final override matrix.

**Failure mode/limit:** smaller or 9-cell masks are absent even though the rule could apply to them.

## D4 — Enumerate connected 3×3 masks instead of random-walking with retries

**Original rationale:** random walks were a compact way to make polyominoes. The baseline could overshoot stated ranges, depend on retry history, and return the last partial grid after exhaustion.

**Choice:** enumerate all normalized connected subsets of the 3×3 board for each supported size and cache them.

**Alternatives rejected:** longer random walks plus larger retry limits; hand-written shape lists; post-hoc rejection sampling. Exhaustive catalogs make every advertised size/profile combination demonstrably nonempty and eliminate silent fallbacks.

**Probe:** catalog connectivity/normalization tests and all-axis generation tests.

**Failure mode/limit:** normalized bboxes are capped at 3×3, a deliberate distribution restriction rather than a rule requirement.

## D5 — Require overlapping masks with exclusive cells on both sides

**Original rationale:** baseline required only non-identical masks so XOR was nonempty. It did not guarantee evidence distinguishing XOR from union or one-mask copying.

**Choice:** every generated normalized pair must have nonempty intersection, `A-B`, and `B-A`.

**Alternatives rejected:** rely on random occurrence of overlaps; dedicate occasional negative fixtures; permit disjoint pairs. Always-on evidence raises data value without changing the target rule.

**Probe:** `two_sided_overlap` witness; normalized-union and red-only rivals; task tests.

**Failure mode/limit:** disjoint-mask lawful cases are omitted, so the support is intentionally more diagnostic than exhaustive.

## D6 — Require shape detail that refutes filled-bounding-box XOR

**Original rationale:** unknown; baseline random walks sometimes produced detailed shapes but did not enforce it.

**Choice:** filter out pairs whose true cropped XOR equals XOR of the two filled bounding boxes.

**Alternatives rejected:** count witness frequency after sampling; include rectangles and trust other demos. Constructive filtering guarantees every example contains non-rectangular evidence.

**Probe:** `shape_detail_not_bbox` witness fired 600/600 in the semantic gate; named rival was refuted in every census lesson.

**Failure mode/limit:** simple rectangular examples are absent.

## D7 — Separate physical objects while varying absolute positions

**Original rationale:** baseline kept a margin so colors remained distinct components.

**Choice:** enumerate all placements whose bounding boxes have at least one blank row or column between them, then sample positions independently of normalized masks.

**Alternatives rejected:** permit touching/adjacent colors; fixed canonical positions; force opposite corners. Separation makes color-object extraction unambiguous; varied positions refute absolute-coordinate XOR.

**Probe:** `normalization_required` witness fired 600/600; absolute-position rival refuted in all sampled lessons.

**Failure mode/limit:** touching objects are not represented.

## D8 — Alternate crop-required and crop-noop profiles deterministically

**Original rationale:** the baseline and summary described a “max-dims grid” and did not encode the canonical final crop. Random draws therefore allowed lessons where uncropped XOR fit every demonstration.

**Choice:** sample-index parity alternates `crop_required` and `crop_noop`. With three consecutive demonstrations, both states necessarily appear.

**Alternatives rejected:** random 50/50 profile selection; require every example to crop; require every example not to crop. Random selection gives nonzero ambiguous-window probability; one-sided schedules teach the wrong boundary behavior.

**Probe:** retained baseline cyclic probe found 6/48 ambiguities; final probe found 0/4,800. Shared lesson census found 0/300 declared ambiguities.

**Failure mode/limit:** parity is a deterministic schedule artifact. It is not visible in a single grid and is used only to guarantee lesson composition.

## D9 — Remove palette/texture/position singleton axes and negative fixtures from ordinary support

**Original rationale:** palette aliases and degenerate fixtures appear to have been copied from a generic template; task-specific intent is unknown. The rule itself fixes semantic colors 2, 3, and 8.

**Choice:** delete controls that cannot or should not change a lawful input. Keep malformed/degenerate behavior in tests, not in the valid generator domain.

**Alternatives rejected:** mark the controls diagnostic; make palette aliases alter semantic colors; declare invalid fixtures lawful. Each would obscure the actual rule or let negative data enter normal sampling.

**Probe:** final lint and defect lint are clean; unknown/invalid overrides reject.

**Failure mode/limit:** no color permutation augmentation is attempted because the canonical rule is color-specific.

## D10 — Add strict grammar and exact-observation validation

**Original rationale:** baseline `self_check` checked only one component of each color and non-identical normalized masks.

**Choice:** validate grid form, allowed colors, canonical profile, exact cell counts, connectivity, bbox size, overlap/exclusive cells, and filled-bbox counterevidence. When override metadata is supplied, compare every requested exact axis to observed values.

**Alternatives rejected:** trust construction only; validate only after Racket application. Explicit validation makes failures local and portable.

**Probe:** strict semantic gate 600/600, canonical 5/5, malformed-input tests, and override contract.

**Failure mode/limit:** strict validation defines the reviewed training manifold, not all inputs on which the Racket rule is meaningful.

## D11 — Declare a finite semantic rival contract

**Original rationale:** no baseline contract existed.

**Choice:** expose the same five callables through the three framework surfaces and map four semantic witnesses to the relevant rivals. Add a lesson hook that checks labels, crop-state coverage, and demo-level refutation.

**Alternatives rejected:** prose-only rival notes; canonical-pair-only testing; a single “wrong XOR” rival. Executable rivals can be scored by shared gates and future tools.

**Probe:** semantic gate, source-bound lesson census, and task-local cyclic rotation probe.

**Failure mode/limit:** the list is not exhaustive; undeclared programs may still fit finite lessons.

## D12 — Retain independent probes and genuine failed iterations

**Original rationale:** required by the review protocol and useful for future agents.

**Choice:** keep the baseline source, TDD red/green logs, interrupted first after-battery aggregate, independent reference probe, cyclic probe, and audit counterexamples.

**Alternatives rejected:** delete failed evidence; report only final green checks; embed all logic inside tests. Retention makes the repair falsifiable and reusable.

**Probe:** clean-room patch replay and final package validator.

**Failure mode/limit:** the independent oracle and generator implement the same mathematical description, so agreement is not formal proof; the Racket-backed checks remain decisive for labels.
