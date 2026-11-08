# Working notes: 501c7f0770eb

## Current source

- Generator version: `3.1.0`
- Final generator SHA-256: `a7b747ac99b15297f8f23ca7b03b165e8b89e79f34757e86005dcd89fb7ab315`
- Canonical rule hash: `a850cef9c1ff`
- Racket authority changed: **no**

## Intended rule

A color-5 connected component is an active chamber only when that entire component is exactly one rectangular border. Blue (`1`) emits a vertical orange (`7`) ray and red (`2`) emits a horizontal orange ray inside active chambers. Gray (`5`) and yellow (`4`) cells stop rays. Two touching rectangle outlines form one malformed component, so their seeds and blockers remain unchanged.

## Reversed baseline decisions

Version `2.1.0` separated every frame and therefore taught the shortcut “fire every visible rectangle.” It also defined `self_check()` twice; the later weak definition shadowed the strict one. Version `3.1.0` removes the duplicate validator and alternates isolated active frames with a touching inactive pair. The retained witness is `counterexamples/touching_frames_inactive.json` with authority receipt `counterexamples/touching_frames_racket.json`.

## Distribution and lesson schedule

- Real axes: `grid_h=10..15`, `grid_w=16..22`, `layout_kind=isolated|mixed_touching`, and `blocker_style=axis_only|mixed`.
- Schedule period 2, keyed only by `sample_index`: `isolated:mixed`, then `mixed_touching:axis_only`.
- Standard lesson: three demonstrations plus one query; every cyclic four-pair window has two examples of each topology.
- Isolated layouts contain two or three active frames. Mixed layouts show three rectangle outlines, but only the isolated component is active.
- Every input contains both seed colors. Every frame contains one seed and one or two blockers; at least one active seed has an axis blocker with open space behind it.
- Even seeds anchor exact canonical profile `12×18` in every difficulty; odd seeds retain difficulty-weighted size variation.

## Validation and performance

`self_check()` accepts all five canonical inputs and both generated topology families. `observe_overrides()` and validation share one `_frame_analysis()` result. Rectangle discovery uses a summed-area table; this reduced the complete 10,440-draw override matrix from a timeout after 5,000 draws to a clean pass.

Focused tests cover superficial-frame rejection, touching topology, all canonical pairs and mirror parity, two/three isolated chambers, schedule non-cancellation, schedule labels, canonical profile anchoring, and one frame scan per validator/observer path.

## Evidence

- Final 12-stage battery: `../../../checks/after-v6/checks/501c7f0770eb_after_battery_summary.json`
- Task tests: `../../../checks/task-tests-v5/result.json`
- Random lesson census: `../../../checks/lesson-census-v5.json`
- Fixed schedule census: `../../../checks/schedule-census-v5.json`
- Curriculum probe: `../../../checks/curriculum-probe-v5.json`

## Known limits / open questions

- Rival coverage is finite and explicit: `all_rectangles_fire` and `ignore_blockers`. Passing those checks does not prove unique induction against undeclared hypotheses.
- Fixed schedule enumeration exhausts both residues at seed 0 only; random census provides broader but non-exhaustive support.
- Semantic colors are intentionally fixed because numeric colors define behavior in the canonical rule.
- Selected canonical and task authority are synchronized. One archival raw-code source is textually divergent but execution-equivalent on all canonical pairs.
## Current reviewer considerations

Source SHA-256: `a7b747ac99b15297f8f23ca7b03b165e8b89e79f34757e86005dcd89fb7ab315`.

# Decisions: 501c7f0770eb

All final measurements in this document use generator SHA-256 `a7b747ac99b15297f8f23ca7b03b165e8b89e79f34757e86005dcd89fb7ab315` and canonical rule hash `a850cef9c1ff`.

## D1 — Treat connected gray components, not visible rectangle candidates, as chambers

**Prior choice.** Version 2.1.0 placed every frame with a one-cell buffer and described every rectangular border as a chamber. That was simpler to sample, but it removed the canonical distinction between an exact rectangular connected component and two touching borders that merely contain two visible rectangle outlines.

**New choice.** Frame activity is determined by equality between a candidate border and an entire color-5 connected component. A touching pair shares one component and is inactive; an isolated exact-border component is active.

**Why.** Canonical examples include touching borders whose seeds do not fire. The old distribution let `all_rectangles_fire` fit every generated example. `counterexamples/touching_frames_inactive.json` is the minimal retained witness: it passes `self_check`, Racket leaves the touching pair unchanged, and the rival changes four cells.

**Alternative rejected.** Merely adding closer but still disconnected frames would increase visual variety without teaching the component rule. Making all frames touch would invert the bias and under-teach ordinary active chambers.

## D2 — Alternate two explicit topology profiles

**Choice.** `SCHEDULE_PROFILES` alternates:

1. `isolated:mixed`
2. `mixed_touching:axis_only`

The schedule is keyed only by `sample_index` and has period 2.

**Why.** A standard lesson contains three demonstrations and one query. Any four consecutive indices contain two of each profile, and holding out any one pair leaves at least one touching counterexample and at least one blocker witness in the demonstrations. Keying by `seed + sample_index` was rejected after the defect checker’s `generate(seed, seed)` probe collapsed the schedule to one parity; the retained failure is under `checks/after-v3/`.

**Limit.** This schedule guarantees support against the two declared rivals, not all conceivable rivals. The fixed-seed schedule census covers both residues and all query rotations, while the random census checks broader seeds and geometry.

## D3 — Keep exactly four advertised axes, all observable from pixels

**Choice.** Advertise `grid_h`, `grid_w`, `layout_kind`, and `blocker_style`. `observe_overrides()` recovers each from the returned grid, and unknown keys are rejected.

**Why.** The baseline declared nominal palette, density, position, color-count, and texture controls that were either fixed, aliases, or unrelated to the rule. Such declarations inflate the override matrix without giving downstream agents meaningful control. The final 10,440-draw override matrix reports zero findings.

**Alternative rejected.** Keeping singleton or ignored axes as “documentation” was rejected because callers interpret `AXES` as an executable contract.

## D4 — Preserve both seed directions and make blocker effects observable

**Choice.** Every input contains both blue (`1`) and red (`2`) seeds. Every visible frame has one seed and one or two blockers. At least one active seed has an on-axis blocker with open cells behind it; `mixed` adds off-axis blockers while `axis_only` keeps blockers on the ray axis.

**Why.** Both ray directions and clipping must be inferable. A blocker immediately adjacent to a wall or seed could be present yet fail to demonstrate clipping. Open space behind the blocker makes `ignore_blockers` observably wrong.

**Alternative rejected.** Random blockers without a witness constraint produced visually plausible grids that did not always distinguish the blocker rival.

## D5 — Support canonical profiles in every difficulty while retaining size range

**Choice.** Valid dimensions are `10..15 × 16..22`. Even seeds use exact canonical profile `12×18` in every band; odd seeds use difficulty-weighted dimensions. Palette size remains the task’s fixed five colors.

**Why.** An earlier repair passed easy but missed exact canonical profiles in medium and hard, failing `profile_floor`. Deterministic anchoring guarantees support without restricting odd-seed variation. Final profile evidence has 31 exact hits in 60 draws and no unsupported band.

**Alternative rejected.** Narrowing every draw to canonical dimensions would satisfy the gate but reduce useful geometry diversity. Pure random weighting did not guarantee a hit in a 20-draw band check.

## D6 — One strict validator and one shared analysis result

**Choice.** Remove the duplicate weak `self_check()` and retain one strict validator that accepts all five canonical inputs plus both generated topology families. The validator and observer each call `_frame_analysis()` once; its result is passed to topology/blocker inference.

**Why.** The duplicate definition silently replaced the earlier strict validator. Separate repeated scans also made the override matrix impractically slow.

**Tests.** Focused tests assert rejection of a superficial border, acceptance/mirror parity for all canonical pairs, and exactly one frame scan in each validator/observer path.

## D7 — Optimize rectangle discovery without changing semantics

**Choice.** Use a summed-area table for constant-time gray-cell counts over candidate rectangles. Share frame/component analysis and avoid redundant validation in hot override paths.

**Why.** The first semantically correct version reached 5,000 of 10,440 clean override draws but exceeded 300 seconds. The optimized version completes the full matrix with no findings; standalone timing was 23.74 seconds, and the final battery’s override stage was 18 seconds.

**Alternative rejected.** Increasing the timeout would hide an avoidable authoring/runtime cost and make future exhaustive checks harder to run.

## D8 — Keep Python mirrors diagnostic; keep Racket authoritative

**Choice.** `rule_mirror()` and rival functions exist for tests, canonical parity checks, and lesson diagnostics only. Labels continue to come from the canonical Racket program; its source was not changed. The canonical hash is pinned as `RULE_HASH`.

**Why.** A Python reimplementation is useful for fast local assertions but must not become a competing authority. Rule smoke and authority sync confirm the selected canonical and task authority agree on all canonical pairs. One archival raw-code representation is textually divergent but execution-equivalent; this is documented, not rewritten.

## D9 — Preserve genuine failures and avoid invented negatives

**Choice.** Keep the incomplete baseline run, schedule/profile failures, and the override timeout under separate evidence directories. The blind and exposed solve episodes each contain one genuine successful revision; no artificial failing solution was created.

**Why.** Intermediate failures explain why each design change exists and are more useful than a polished-only history. Solve metadata records exposure honestly.

## Known limits

- Declared rivals are `all_rectangles_fire` and `ignore_blockers`; undeclared rivals remain possible.
- The fixed schedule census exhausts residues at one seed, not every seed/geometry.
- The 300-lesson random census is strong finite evidence, not a proof of unique identifiability.
- The generator intentionally fixes semantic colors because the Racket rule assigns behavior by numeric color; palette permutation would change the task.
- No selected Racket rule change was made.
