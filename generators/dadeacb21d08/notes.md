# Working notes: dadeacb21d08

## Review 2026-10-03 — assignment `review-10f279c13980cc5c`

### Baseline defect

The selected 2.0.1 generator produced isolated target Ls plus weak single-cell noise. Its validator rejected all five canonical inputs, its declared controls were largely dead or misleading, and it had no executable semantic rivals. That distribution could teach broad shortcuts such as “complete every red component,” “complete every three-cell red shape,” “complete every L regardless of color,” or “fill only an empty corner.” The full baseline battery retained at `checks/before-full/` had six failing stages.

### Repair

Version 3.0.0 is a constructive nine-slot sampler with four linked profiles. It deliberately combines:

- exact red L targets in every orientation;
- red straight triomino, domino, and 2×2-square negatives;
- non-red L negatives;
- empty, occupied, and mixed missing corners;
- interior and edge targets;
- two canonical-compatible shortcuts that are broken only by generated examples: canonical-envelope-only behavior and at-most-three-target behavior.

The sampler has no rejection loop for ordinary generation. Exact overrides are checked and observable, unknown overrides and difficulty labels fail loudly, and all canonical inputs are accepted by `self_check` and reproduced by `rule_mirror`.

### Rule authority

The Racket semantics were not changed. The selected archival `target_code` was synchronized byte-for-byte to its already-existing canonical `raw_code`; this removed a comment-only authority mismatch while preserving execution parity. Canonical rule hash remains `4dc2707cc06e`.

### Verification retained

- Focused task tests: 8/8 pass (`checks/task-tests/`).
- Shared lesson census: 300/300 lessons materialized, 0 ambiguous, 1,500/1,500 unique inputs, every declared rival refuted in every lesson (`checks/lesson-census-final.json`).
- Independent cyclic probe: 100 lessons per band, all four start residues, 0 identifiability failures, 192/192 joint boundary combinations honored (`checks/independent-audit-final.json`).
- Post-repair solve: visible examples 4/4 on the first revision; prior exposure declared honestly in `solve/summary.json`.

### Limits

The semantic checks cover declared and task-local plausible rivals, not every hypothesis a model could learn. The four-profile schedule is intentionally structured; downstream lesson assembly should keep four consecutive demonstrations together. Catalog approval and train-safety status remain separate maintainer decisions.
## Current reviewer considerations

Source SHA-256: `ab33a55161bca6aa2ac3fa0a061e148e3b86816efb56ee17d0a1ef8e0578e749`.

# Decisions — dadeacb21d08

All repair decisions below apply to selected generator version 3.0.0, SHA-256 `ab33a55161bca6aa2ac3fa0a061e148e3b86816efb56ee17d0a1ef8e0578e749`.

## D1 — Preserve the canonical transformation

- **Choice:** Keep the Racket rule unchanged: transform only red, four-connected, three-cell components with a 2×2 bounding box; paint the complete box green, including an occupied fourth corner.
- **Original rationale:** Unknown. The selected baseline description was close, but its validator and sampler did not cover the canonical domain.
- **Alternatives rejected:** Narrowing the rule to empty missing corners; changing connectivity; preserving a non-red fourth-corner cell; changing the authority to fit the baseline generator.
- **Probe:** All five canonical pairs are accepted and exactly reproduced by the Python mirror; shared `rule_smoke` and authority execution parity pass.
- **Failure mode / limit:** The Python mirror is supporting test code, not the authority. Racket remains decisive.

## D2 — Replace the rejection sampler with constructive, separated slots

- **Choice:** Use a 3×3 set of disjoint placement bands with a one-cell moat and assign at most one connected component to each slot.
- **Original rationale:** The old sampler tried to keep Ls far apart, but it did not provide truthful joint controls or systematic negatives.
- **Alternatives rejected:** Continue random placement with retries; post-hoc repair of accidental mergers; enlarge grids until placement happens to succeed.
- **Probe:** The task test exhausts all 192 joint boundary combinations. `workspace/audit_distribution.py` independently repeats the same matrix and reports 192/192 valid combinations.
- **Failure mode / limit:** The slot geometry is intentionally synthetic. It favors clear object separation over natural-looking clutter.

## D3 — Use a four-profile linked curriculum

- **Choice:** Set `EXAMPLES_NEEDED = 4` and map consecutive sample indices to four deterministic profiles. Together they cover the canonical anchor, empty and occupied holes, edge targets, four targets, all orientations, and shape/color negatives.
- **Original rationale:** Unknown; the baseline had no linked teaching policy.
- **Alternatives rejected:** Independent IID draws, which could produce an underdetermined four-example lesson; a single overloaded example; six or more profiles, which would require longer lessons.
- **Probe:** The shared census materialized 100 lessons per band with zero ambiguity. The independent probe tests all four cyclic starting residues and reports 100/100 identifiable lessons per band.
- **Failure mode / limit:** Consumers that shuffle individual demonstrations can break the intended linked coverage. The schedule assumption is documented and executable through `lesson_identifiable`.

## D4 — Make shape, color, and occupancy negatives mandatory

- **Choice:** Every generated input contains exact red L targets, red non-target components, and non-red components; across the four profiles, red straight triominoes, red squares, red dominos, and non-red Ls are explicit.
- **Original rationale:** The baseline used sparse noise and did not make semantic alternatives falsifiable.
- **Alternatives rejected:** Random single-cell decoys; only red negatives; only non-red shape negatives.
- **Probe:** Semantic witnesses fire in the final shared gate, and every declared broad rival is refuted in every retained census lesson.
- **Failure mode / limit:** The finite rival set cannot enumerate every learned shortcut. The independent tool reports this explicitly.

## D5 — Include occupied missing corners

- **Choice:** Support `hole_mode = empty|occupied|mixed`; occupied corners use non-red colors and are overwritten by the canonical rule.
- **Original rationale:** Canonical examples include occupied missing corners, while the old sampler effectively taught an empty-cell-only completion.
- **Alternatives rejected:** Empty holes only; occupied holes only; placing the occupied cell adjacent but outside the target box.
- **Probe:** A focused test asserts that the occupied corner becomes green while red and non-red distractors survive unchanged. The rivals “empty holes only” and “preserve occupied corner” are refuted in every census lesson.
- **Failure mode / limit:** A non-red occupied corner is deliberately part of a red target's bounding box, so object-only preprocessing that discards cross-color occupancy will lose critical information.

## D6 — Teach edge and count extrapolation explicitly

- **Choice:** Two profiles require at least one target box touching an edge; one profile has four targets. These break canonical-compatible shortcuts that only operate inside the canonical envelope or with at most three targets.
- **Original rationale:** The baseline did not distinguish semantic validity from canonical-range mimicry.
- **Alternatives rejected:** Treat edge placement and target count as random optional variation; rely only on larger dimensions.
- **Probe:** Both shortcuts fit all five usable canonical pairs, then are refuted 100/100 lessons per band in the shared census and every cyclic lesson in the independent audit.
- **Failure mode / limit:** These are selected extrapolation dimensions, not proof that every out-of-envelope case is covered.

## D7 — Advertise only exact, observable controls

- **Choice:** Replace legacy axes with seven task-relevant axes: dimensions, target count, red-decoy count, non-red-decoy count, hole mode, and target position. Unknown difficulty labels and unknown override keys raise `ValueError`.
- **Original rationale:** The old declarations contained unrelated palette/texture concepts and silently swallowed unknown keys.
- **Alternatives rejected:** Keep singleton diagnostic axes; leave legacy aliases; permit best-effort incompatible overrides.
- **Probe:** `observe_overrides` round-trips every tested combination exactly; final override gate passes.
- **Failure mode / limit:** The public ranges are deliberately bounded to 10–16 and the constructive slot capacity. Larger grids are outside this version's declared domain.

## D8 — Keep a 25% canonical-like anchor rate

- **Choice:** Profile 0 mirrors canonical dimensions/palettes closely; the other three profiles provide semantic contrasts outside that envelope. This yields one strict example in each four-profile cycle.
- **Original rationale:** The baseline happened to overlap canonical profiles weakly and rejected canonical structure semantically.
- **Alternatives rejected:** Make every draw canonical-like, which preserves shortcuts; make none canonical-like, which weakens distribution continuity.
- **Probe:** Independent sampling reports exactly 25/100 strict draws in each band; the shared semantic gate measured 152/600 (25.3%) under its seed schedule.
- **Failure mode / limit:** “Strict” is a structural profile metric, not a guarantee of visual similarity to every canonical pair.

## D9 — Declare executable semantic contracts

- **Choice:** Add a Python rule mirror, semantic observables/witnesses, two verified canonical shortcuts, thirteen lesson competitors, and `lesson_identifiable`.
- **Original rationale:** The baseline had no contract, so the semantic stage was advisory and non-probative.
- **Alternatives rejected:** Narrative-only invariants; hard-coded expected witness names in the external audit tool; a single aggregate ambiguity score.
- **Probe:** Shared semantic gate passes with all canonical pairs accepted, all witnesses firing, all rival claims verified, and all smoke lessons identifiable. The independent audit iterates the generator's declarations directly.
- **Failure mode / limit:** Declared-rival elimination is finite evidence and can miss undeclared feature leaks.

## D10 — Synchronize selected authority text without changing semantics

- **Choice:** Replace the selected authority's comment-decorated `target_code` with its already-existing canonical `raw_code`, byte-for-byte.
- **Original rationale:** The comments were presumably explanatory, but active authority checks require exact synchronization.
- **Alternatives rejected:** Modify the canonical rule; suppress the detector; keep behaviorally equivalent active texts divergent.
- **Probe:** Focused defect-lint and authority-sync checks pass after synchronization; execution parity had already passed before the text-only change.
- **Failure mode / limit:** This is a source normalization, not a semantic repair. The authority file hash changed and is reported explicitly.

## D11 — Leave a reusable independent audit tool

- **Choice:** Add `workspace/audit_distribution.py` to recheck canonical compatibility, all joint axis boundaries, sampled uniqueness/strict rates, and every cyclic lesson start against live declarations.
- **Original rationale:** The shared census does not rotate every pair into the query position and the standard override matrix is not a concise task-local acceptance receipt.
- **Alternatives rejected:** A one-off notebook; copied rival-name lists; manual spot checking.
- **Probe:** Retained final report has zero failures across 192 boundary combinations, 300 draws, and 300 cyclic lessons.
- **Failure mode / limit:** It uses the Python mirror for bulk speed. Shared Racket gates remain required.
