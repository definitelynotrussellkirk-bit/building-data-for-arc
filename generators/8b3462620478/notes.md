# Working notes: 8b3462620478

## Current rule and implementation

Pinned rule hash: `805506f84e33`. Red `2` is the source; cardinal-adjacent blue `1` gives the heading; empty cells become `8`; mirror `3` uses slash reflection and mirror `4` uses backslash reflection; gray `5` or the edge terminates the beam.

Version 3.1.0 replaced the imported east-only straight-ray/horizontal-wall sampler. The generator now constructs compact serpentine routes for all four headings. Every requested mirror interacts; routes with at least three mirrors mix left and right turns. A connected gray border frame restores canonical wall scale, while `n_walls` counts only exact optional interior blocker cells.

Public exact axes: height 9–18, width 12–20, 2–6 mirrors, 0–6 interior blocker cells, four headings, and two initial turn sides. Three of four default schedule positions favor the canonical dimension envelope; one explores the full range.

## Shortcut evidence

The strongest canonical-fitting rival is `first_three_mirrors_only`: all five canonical beams meet at most three mirrors. The saved four-mirror witness in `counterexamples/first_three_mirrors_only.json` differs at nine cells. `workspace/reference_probe.py` independently replays the intended rule or a finite mirror limit without importing the generator.

## Final verification

- final generator SHA-256: `f3794014b466fab737ca0249cdb02fe187d86f16bd46a40a45657da1d49008d0`;
- 74 focused tests pass;
- final battery: 12/12 green;
- exact overrides: 52,830/52,830 accepted, zero findings/warnings;
- canonical: 5/5 accepted and exact authority parity;
- semantic smoke: 12/12 three-demo lessons, 48/48 query rotations;
- larger census: 300/300 lessons and 1,200/1,200 rotations, 1,197 unique inputs.

The task-local base/selected Racket text was synchronized exactly to canonical source; canonical semantics were not changed.

## Known limits

The sampler covers a constructive serpentine family, always uses a border frame, and intentionally does not sample arbitrary lawful mirror mazes or loops. Its identifiability claim is only against the declared finite rival set. Add new executable rivals and witnesses when new shortcut hypotheses appear.
## Current reviewer considerations

Source SHA-256: `f3794014b466fab737ca0249cdb02fe187d86f16bd46a40a45657da1d49008d0`.

# Design decisions — `8b3462620478`

## D1 — Treat the canonical Racket program as the sole semantic authority

**Choice.** Pin `RULE_HASH = "805506f84e33"` and implement the four-direction reflected-beam rule exactly: source `2`, adjacent heading `1`, slash mirror `3`, backslash mirror `4`, wall `5`, painted background `8`.

**Rationale.** All five canonical pairs require this behavior. The imported east-only straight-ray description was not a smaller variant of the same task; it omitted its central operation.

**Rejected alternative.** Extending the old horizontal-wall sampler with occasional turns. That would retain an architecture organized around the wrong one-direction rule and would not make mirror interaction or exact axes provable.

**Probe/failure mode.** Canonical ownership and an independent oracle are regression tests. Wrong color mapping, heading orientation, or wall handling changes official outputs immediately.

## D2 — Construct a route rather than place random mirrors and hope they interact

**Choice.** Build the beam route first, then render source, heading, mirrors, walls, and empty space around it.

**Rationale.** Constructive generation makes “every requested mirror is encountered” true by design and keeps exhaustive override checking fast. A cached compact family describes valid source-placement rectangles rather than enumerating every full grid.

**Rejected alternative.** Random mirror placement plus rejection. It wastes draws, makes hard override combinations unreliable, and can silently create dead distractor mirrors.

**Probe/failure mode.** For every generated grid, `observe_overrides` must exactly recover all public axes, and `_trace_report` must encounter the requested mirror sequence and terminate at a wall.

## D3 — Use a compact mixed-turn serpentine

**Choice.** Mirror turn sides follow `R,R,L,L,…` or the reflected `L,L,R,R,…` sequence. Route legs are two cells long.

**Rationale.** Two equal turns reverse one coordinate direction; alternating pairs produces a compact snake without retracing. With at least three mirrors, both relative turn directions appear, refuting “repeat the first turn side.”

**Rejected alternative.** Alternating every turn (`R,L,R,L,…`) was easier to self-intersect in compact grids. Repeating one turn side generated loops or a simple rectangular shortcut.

**Limits.** This family is intentionally regular; it does not represent every lawful mirror arrangement.

## D4 — Expose six exact, pixel-observable axes

**Choice.** Public axes are `grid_h` 9–18, `grid_w` 12–20, `n_mirrors` 2–6, interior `n_walls` 0–6, all four `direction` values, and both `turn_side` values.

**Rationale.** Each value can be recovered from the returned grid without hidden metadata. Every value is available in every difficulty band, so an override means the same thing everywhere.

**Rejected alternative.** Declaring latent “complexity” or palette axes. Those would be difficult to observe exactly and would duplicate effects already represented by mirror and blocker counts.

**Probe/failure mode.** The final override checker accepted 52,830/52,830 draws with zero findings or warnings and rejected unknown keys.

## D5 — Define `n_walls` as interior blocker cells, not total gray cells

**Choice.** Every generated scene has a connected gray outer frame; `n_walls` counts only optional interior blocker cells.

**Rationale.** Canonical scenes contain large gray structures. An early repair with only tiny terminal walls failed canonical coverage and profile diagnostics. A frame restores the correct object scale while keeping the variable portion exactly countable.

**Rejected alternative.** Counting the frame in `n_walls`. That would require an axis range dependent on grid dimensions and make exact override semantics awkward. Tiny terminal walls were rejected by the profile gate.

**Probe/failure mode.** `observe_overrides` counts gray cells only inside the border. The profile gate reports 32/60 exact canonical profiles and 48/60 envelope hits, with support in all bands.

## D6 — Favor canonical dimensions without collapsing diversity

**Choice.** Three of four default schedule positions draw from canonical-height/width anchors; the fourth explores the full declared range.

**Rationale.** The first intermediate profile run showed only 21.7% envelope support. Purely broad uniform sampling underrepresented the official 10–11 by 12–14 scale, while an all-canonical sampler would eliminate useful size variation.

**Rejected alternative.** Restrict all grids to canonical dimensions. That would pass coverage but unnecessarily narrow the generator.

## D7 — Keep lawful validation separate from generated teaching guarantees

**Choice.** `self_check` accepts lawful canonical-style inputs, while stricter properties—every mirror interacting, mixed turns, exact frame construction—are enforced by generation, semantic witnesses, and focused tests.

**Rationale.** A validator that required the synthetic serpentine would reject lawful official or hand-authored inputs. Conversely, a generation contract needs more than broad rule legality.

**Probe/failure mode.** All five canonical inputs pass `self_check`. Generated scenes independently prove interaction and exact axes.

## D8 — Make the canonical-fitting finite-depth rival executable

**Choice.** Declare `first_three_mirrors_only` in `CANONICAL_SHORTCUTS`, `SEMANTIC_RIVALS`, and `LESSON_COMPETITORS`.

**Rationale.** Every canonical path encounters at most three mirrors, so the rival exactly fits all five demonstrations. It is stronger than “ignore mirrors” or “swap mirror colors,” which canonical examples already refute.

**Counterexample.** Seed 4242, sample 7, 10×13, four mirrors, one interior blocker, downward launch, first turn right. The fourth reflection changes nine output cells. Full data: `repo/generators/8b3462620478/counterexamples/first_three_mirrors_only.json`.

**Probe/failure mode.** The independent `workspace/reference_probe.py` does not import the generator. Public Racket replay matched the intended output and not the rival. Every measured three-demo lesson refuted the rival.

## D9 — Use three demonstrations per generated lesson

**Choice.** Set `EXAMPLES_NEEDED = 3`; all declared rivals must fail on at least one demonstration.

**Rationale.** Three examples are sufficient for the current route schedule and rival set while leaving one query in the standard four-pair lesson. A larger number would reduce lesson throughput without adding measured identifiability.

**Probe/failure mode.** Semantic smoke: 12/12 production lessons and all 48 query rotations. Large census: 300/300 production lessons and all 1,200 query rotations, with no hook errors.

**Limit.** This is a finite-rival claim, not proof against all programs consistent with three examples.

## D10 — Synchronize task-local Racket text without changing canonical semantics

**Choice.** Replace the selected/base `target_code` text with the exact canonical `program_solution`; canonical ledger remains unchanged.

**Rationale.** The intermediate defect lint found comment-only source divergence. Exact synchronization removes ambiguous authority provenance while preserving behavior.

**Rejected alternative.** Leave behaviorally equivalent but textually divergent code. That needlessly complicates source-bound review and hash invalidation.

**Probe/failure mode.** Final authority report has one exact source group, one normalized rule hash, and 5/5 execution parity.

## D11 — Build a standalone future-agent oracle

**Choice.** Add `workspace/reference_probe.py` and a machine-readable counterexample.

**Rationale.** Future reviewers can replay arbitrary grids and finite-depth rivals without trusting or importing the implementation under review. The tool also makes the semantic disagreement inspectable outside the test suite.

**Probe/failure mode.** Portable tests run the CLI on the saved counterexample and compare its intended/rival outputs and differing cells.

## Remaining limits

- Generated layouts are compact serpentine routes, not arbitrary mirror mazes.
- Every generated input has a gray border frame; sparse-wall lawful inputs are validator-owned but not sampled.
- Mirror counts are 2–6; longer lawful routes remain outside the generation distribution.
- Loop handling is bounded and lawful, but the constructor does not intentionally generate loops.
- The named-rival set is useful and measured, not exhaustive.
