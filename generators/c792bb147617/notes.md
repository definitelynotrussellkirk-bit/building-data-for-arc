# Working notes: c792bb147617

## Current rule and authority

For every **original** blue(1) input cell, preserve the input and write its in-bounds cardinal neighbors in row-major anchor order: up=2, left=7, right=6, down=8. Racket remains the label authority. The generator pins canonical rule hash `98769b9435a0`; Python `rule_mirror` exists only for regression and rival checks.

The selected training and augmented `target_code` fields were synchronized to the canonical `program_solution`. Their archival `raw_code` fields remain unchanged; final authority sync reports execution parity PASS.

## Reversed decisions

The previous version generated only 2–4 strictly interior blue anchors and rejected canonical boundary inputs. That choice was reversed because canonical scenes use clipped edge/corner anchors and contain up to seven blues. The accepted prior audit `review-23d5a1d9901f74bc:v0001` was used as a lead, then reproduced against baseline source SHA `f4a92bd98ca15f29b5c70ebebbedbebd70c61e797734eba3818139e3c120d3b3`.

The old nine-axis contract was replaced with four exact observable controls:

- `grid_h`: 6..16
- `grid_w`: 6..16
- `n_blues`: 2..8
- `edge_mode`: `none|some`

Unknown keys, invalid scalar types, and out-of-range values fail loudly.

## Distribution and teaching design

A checkerboard-parity maximin sampler guarantees exact counts without cardinal adjacency. `edge_mode=some` chooses a boundary anchor first. Four recurring profile names provide two 8-anchor boundary witnesses, one broad draw, and one canonical-sized six-anchor boundary draw. With three demonstrations and one query, every cyclic query position leaves both a boundary witness and an eighth-anchor witness in the demonstrations.

Declared rivals:

- `first_seven_blues` — fits all labeled canonical pairs; refuted by count-8 inputs.
- `skip_boundary_blues` — induced by the old sampler; refuted by edge anchors.

The exact first-seven counterexample is retained at `counterexamples/first-seven-blue-limit.json` and covered by focused tests.

## Verification

Final generator SHA-256: `4660797fc369c376d3f1e389f41da48ee427d44f6c4284c6cabf4ff969a91fa1`.

- final battery: 12/12 stages green;
- task-local tests: 27/27 passed;
- semantic smoke: 12/12 lessons identifiable, 0/48 ambiguous rotations;
- large census: 300/300 lessons, 0/300 production ambiguities, 0/1,200 rotated-query ambiguities, 1,190 unique inputs;
- post-repair solve: 3/3 visible examples passed on revision 1 (earlier exposure declared).

## Known limits and open findings

The generator grammar intentionally excludes cardinally adjacent blues, although the authority defines an overwrite order for them. It also excludes fewer than two or more than eight anchors, multiple input colors, and dimensions outside 6..16. Shared-neighbor writes at Manhattan distance two remain lawful.

Finite rival checks and the census are not a proof of universal identifiability. No unresolved blocking finding remains for the selected generator.
## Current reviewer considerations

Source SHA-256: `4660797fc369c376d3f1e389f41da48ee427d44f6c4284c6cabf4ff969a91fa1`.

# Decisions: c792bb147617

## D1 — Treat boundary anchors as ordinary inputs

**Prior choice:** every blue had to be interior. The original rationale is unknown; the source comment suggests it was intended to avoid clipped crosses and overlap.

**New choice:** allow anchors on any top, bottom, left, or right edge. `edge_mode=none` guarantees none; `edge_mode=some` guarantees at least one.

**Evidence:** canonical inputs contain boundary anchors, the authoritative program clips writes to in-bounds cells, and the baseline `self_check` rejected those same canonical inputs. The final strict hook accepts 6/6 canonical inputs and the boundary witness fired in every band.

**Rejected alternative:** keep boundary cases as a rare degenerate texture. That would continue treating core canonical behavior as outside the ordinary distribution and would not guarantee it appears in complete lessons.

## D2 — Replace nine nominal axes with four exact controls

**Prior choice:** `grid_h`, `grid_w`, `n_blues`, `position_bias`, `min_separation`, `anchor_corner`, `asymmetry_force`, `include_decoy`, and `texture` were advertised. Several were ignored, silently coerced, aliases, or negative fixtures.

**New choice:** expose only `grid_h` (6..16), `grid_w` (6..16), `n_blues` (2..8), and `edge_mode` (`none|some`). Every legal value works in every difficulty band, can be recovered from the returned grid, and unknown/ill-typed inputs fail loudly.

**Probe:** the final override gate and focused test matrix exercise exact controls across `None`, easy, medium, and hard. The final stage has no findings or warnings.

**Rejected alternative:** keep decorative axes for apparent variety. An axis that cannot be observed or forced is not a falsifiable control and made the previous contract misleading.

## D3 — Expand count support to 2..8

**Prior choice:** ordinary defaults used 2–4 blues; the advertised valid range was 1–6.

**New choice:** ordinary and explicit support is 2–8. Counts 5–7 cover canonical profiles and count 8 is an intentional counterexample to the strongest canonical-fitting shortcut.

**Evidence:** canonical labeled inputs contain up to seven blues, so “process only the first seven” fits all canonical labels. The retained 8-anchor witness changes three cells relative to that rival. The final semantic gate refuted the rival on 60/60 checked witness firings.

**Rejected alternative:** stop at seven because it matches observed canonical maxima. That preserves the exact count-threshold shortcut the generator should teach against.

## D4 — Use a four-profile teaching schedule

**Choice:** profiles are `eight_boundary_a`, `broad`, `eight_boundary_b`, and `canonical`. Three demonstrations plus one query are assembled from consecutive samples.

**Reason:** two 8-anchor boundary profiles in every four-pair cycle ensure that holding out any one pair still leaves at least one demonstration refuting both the first-seven and interior-only rivals. The broad slot supplies size/count variation; the canonical slot anchors the 10×10, six-blue regime.

**Probes:** the task-local suite exhausts every cyclic start and every query rotation in all three bands. The semantic smoke reports 12/12 identifiable and 0/48 ambiguous rotations; the large census reports 0/300 production and 0/1,200 rotation ambiguities.

**Limitation:** this schedule is evidence against declared rivals, not a universal rule-identification proof. `SCHEDULE_PROFILES` remains public; cyclic coverage is enforced by the task-local test rather than a global `LESSON_SCHEDULE_PERIOD` declaration.

## D5 — Spread anchors on one checkerboard parity

**Choice:** select one parity, force a boundary start when requested, and use deterministic maximin placement within that parity.

**Reason:** the smallest legal interior domain is 4×4, whose parity class contains exactly eight cells. This guarantees every legal count while preventing cardinal adjacency and keeping examples readable.

**Failure discovered:** an earlier validator accepted short lines and solid 2×2 clusters. Defect lint flagged this as a minimal impostor. A failing regression test was added first; `self_check` now rejects cardinally adjacent anchors, and final defect lint passes.

**Alternatives rejected:**

- fixed minimum Manhattan distance 3: not feasible for all 6×6/count-8 overrides;
- arbitrary sampling with fallback: exact but could create dense, overwrite-heavy clusters;
- forbidding all shared-neighbor writes: unnecessarily narrows the domain beyond what the task needs.

## D6 — Make semantic assumptions executable

**Choice:** add `rule_mirror`, `strict_canonical_like`, two witnesses, two rivals, `CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, and `lesson_identifiable`.

The lesson hook requires concrete evidence in demonstrations: all four directional color assignments, an observable clipped boundary anchor, and an observable eighth anchor. It also verifies every supplied label against the independent Python mirror.

**Limitation:** Python is not the label authority. The Racket program remains authoritative; Python mirrors are regression and adversarial-audit helpers only.

## D7 — Synchronize selected authority text without rewriting archival source

**Prior state:** selected `target_code` text differed from canonical exact source, while execution parity already passed.

**Choice:** copy the canonical `program_solution` into the two selected `target_code` fields only. Preserve `raw_code`, lineage, metadata, and all other fields.

**Reason:** this resolves selected-source drift without erasing the preserved legacy expression. Final authority sync reports selected synchronization and execution parity PASS.

## D8 — Preserve and test the strongest counterexample

The exact 10×10/count-8 input, intended output, first-seven rival output, differing cells, generation recipe, and hashes are stored at `repo/generators/c792bb147617/counterexamples/first-seven-blue-limit.json`. A focused test reloads and replays it, avoiding a prose-only claim.

## D9 — Known domain boundaries

The generator deliberately does not cover empty/single-anchor inputs, dimensions outside 6..16, more than eight anchors, multiple input colors, or cardinally adjacent anchors. The authority may define behavior for some of these, but they are outside this generator's stated training grammar. Overlap order is still mirrored exactly for lawful shared-neighbor cases.

## D10 — Keep palette rotation as a separate, promotion-ready prototype

**Choice:** add `workspace/parametric/{prototype.py,adapter.py,promotion.json}` and a focused test without changing the selected generator or canonical rule. One episode-fixed `orientation` rotates the canonical directional palette through `canonical`, `rotate_cw`, `rotate_180`, and `rotate_ccw`; the canonical setting returns the exact authoritative Racket bytes.

**Reason:** this is a small falsifiable extension of the reviewed rule rather than a new input grammar. Sampling is independent of the hidden setting, so the same seed/count request yields identical ordered inputs under every orientation. Two demonstrations leave exactly one declared setting; ordinary qualification retains three demonstrations and four queries.

**Evidence:** 12 focused prototype tests and all 39 selected task tests pass. Native qualification covered all four settings at seeds 0 and 17 with 3 demonstrations and 4 queries, replayed 128 labels/rivals through protected Racket, and left the chosen setting as the sole demonstration-consistent survivor in all 8 checks. A bounded adversarial replay also verified a setting-neutral, duplicate-free 8+8 request at seed `2**63-1`.

**Status/limits:** proposed and qualified only. No variant is owner-accepted, catalog-selected, exported, or admitted to training. The retained maximum-count check uses the independent Python mirror; protected-Racket evidence is the 3+4 qualification. Finite declared settings do not establish uniqueness against arbitrary rules or learning benefit.
