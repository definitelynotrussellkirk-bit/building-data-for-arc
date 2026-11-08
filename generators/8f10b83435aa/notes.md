# Working notes — 8f10b83435aa

## 2026-10-07 — assignment review-40a48f4e27e667d8

Baseline generator `2.0.1` SHA-256 `23c4da5187cc4ae031c6347646a89d19d15056894e6cea5ddb79df2c927d9c14`; final `2.1.0` SHA-256 `a435a00bc4b849d31965afb03b669f2d60df069f84b43f79f1fd9c6225f80b08`. Canonical Racket rule hash `bd5f126e874d` and all shared/canonical source are unchanged. Imported associated notes were empty.

The baseline generated occupied local positions only in exactly two or three panels. Therefore the incorrect union rule (keep any occupied position) fit every generated grid, while canonical examples included count-1 negatives. The baseline also lacked `RULE_HASH`, exposed dead/singleton/invalid axes and textures, accepted unknown controls, had no `observe_overrides`, and declared no semantic contract. Before battery: 8 green, 1 advisory, 3 failed of 12; override gate reported 4,936 findings.

The repair replaces the sampler with disjoint constructive occupancy classes. Each grid has at least three singleton negatives distributed across all panels, at least three pair-only positives covering every panel pair, and at least one triple positive. Exact axes are panel height, majority count, singleton count and triple count. All are pixel-observable, legal in every band and validated before generation. Difficulty rotates full keyed-choice domains so matched bands differ without making controls incompatible.

Added `rule_mirror`, strict/canonical validation split, five executable rivals and witnesses, `lesson_identifiable`, `EXAMPLES_NEEDED=2`, deterministic/global-RNG regression checks and a portable task test suite. The RED run had 18 failures/4 passes; a second RED run caught byte-identical bands. Final task tests are 23/23. The task-local `workspace/probe_majority_contract.py` provides a cheap future-agent JSON audit.

Final evidence: battery 12/12 green; rule smoke 120/120; profile floor 60/60 exact; override matrix 10,890/10,890 accepted with zero findings; required semantic smoke 12/12 lessons and 36/36 rotations; larger census 300/300 lessons, 900 unique inputs and 900/900 rotations with zero declared-rival ambiguity. These finite checks do not prove uniqueness against undeclared hypotheses.

The blind-before-repair solve of task `eb92fce9b549` and exposed post-repair solve each passed 3/3 visible examples in one revision. The latter is bound to the final generator bytes and honestly declares earlier rule exposure.

Remaining limits: fixed input/output role colors, fixed width-4 panels and two dividers, height 6–7, bounded density/counts, and only five declared rivals. Shared tooling should add an automatic undeclared-shortcut/counterfactual gate; audit task `2636c90a673a` demonstrates a frequency shortcut that survives all declared gates but is separated by a lawful exact override.
## Current reviewer considerations

Source SHA-256: `a435a00bc4b849d31965afb03b669f2d60df069f84b43f79f1fd9c6225f80b08`.

# Decisions — 8f10b83435aa

All selected-source decisions below bind to final generator SHA-256 `a435a00bc4b849d31965afb03b669f2d60df069f84b43f79f1fd9c6225f80b08`. The original rationale for baseline `2.0.1` is unknown beyond its source comments; associated notes were empty.

## D1 — Preserve and pin the existing authority

**Choice.** Keep the canonical rule and examples unchanged and set `RULE_HASH = "bd5f126e874d"`.

**Rationale.** All three labeled canonical pairs agree with the existing majority-over-three-panels rule. The defect was in lesson generation, not authority.

**Alternatives rejected.** Rewriting Racket to match the baseline union-like curriculum would make the authority wrong. Changing canonical pairs was unnecessary and outside the evidence.

**Probes.** Task test `test_declares_rule_authority_and_matches_every_canonical_pair`; after authority sync; rule smoke; profile floor.

**Failure modes/limits.** The Python mirror is not itself authority. Its parity is checked against canonical labels and the battery's Racket execution, not assumed.

## D2 — Replace the advertised axis surface rather than preserve dead compatibility

**Choice.** Expose only four exact axes recoverable from the grid: `panel_h` 6–7, `n_majority` 6–10, `n_singletons` 3–9 and `n_triples` 1–3.

**Rationale.** Baseline `panel_w`, palette, density, position-bias and texture controls were singleton, ignored, semantically misleading or included invalid degenerates. A smaller truthful surface is more useful than broad metadata that cannot be honored.

**Alternatives rejected.** Keeping aliases for the old controls would perpetuate silent no-ops. Expanding panel width or palette would leave the demonstrated canonical domain and create new color/geometry semantics without evidence.

**Probes.** `observe_overrides`; exact-control tests across all bands; invalid/unknown-control tests; 10,890-draw override matrix; `workspace/probe_majority_contract.py`.

**Failure modes/limits.** The fixed width/palette are intentional constants, not axes. Future expansion must add a lawful authority-backed domain and new semantic tests rather than merely widening metadata.

## D3 — Construct threshold evidence in every example

**Choice.** Every generated grid contains at least three one-panel negatives, at least three pair-only positives covering all three panel pairs, and at least one triple positive. Each panel also receives at least one singleton temptation.

**Rationale.** FND-1 was caused by sampling only counts 2 and 3. The output threshold cannot be learned robustly without examples on both sides; local construction is stronger than relying on lesson-level chance.

**Alternatives rejected.** A rejection sampler could keep drawing until enough witnesses happen, but it wastes calls and complicates exact overrides/replay. Adding one singleton somewhere would refute union but could leave one or more panel-copy shortcuts intact.

**Probes.** `test_every_default_example_teaches_the_majority_boundary_and_refutes_shortcuts`; five semantic witnesses; required semantic gate; larger lesson census; independent majority probe.

**Failure modes/limits.** These witnesses refute the named union/intersection/copy rules, not every possible program. The count ranges also bound density rather than covering all 24 local cells.

## D4 — Use disjoint local positions and canonical role colors

**Choice.** Sample `n_majority + n_singletons` distinct local coordinates, paint occupied cells color 2, retain color-5 dividers and output color 8.

**Rationale.** Disjoint positions make exact counts observable and avoid collisions that would silently alter controls. The fixed colors and separators are part of the canonical task representation.

**Alternatives rejected.** Mixed foreground colors would add an unsupported color-invariance claim. Overlapping separately sampled position sets would make `n_*` controls non-exact.

**Probes.** Exact override recovery, `self_check`, canonical profile floor and rule mirror tests.

**Failure modes/limits.** No color-role permutation is claimed. Models may still exploit fixed role colors, but that is representation-equivalent within the owned domain rather than a mislabeled axis.

## D5 — Keep full legal domains available in every difficulty band

**Choice.** Rotate each complete value list before the keyed default draw for easy/medium/hard; exact overrides remain identical across bands.

**Rationale.** The first repair's matched seed/index outputs were byte-identical across bands and defect lint treated difficulty as dead. Narrow band-specific subranges would conflict with the requirement that exact public overrides work in every band.

**Alternatives rejected.** Hard-coded easy/hard values collapse axis support. Band-specific legal domains would require declared incompatibilities and reduce counterfactual coverage.

**Probes.** Failing regression `checks/tdd-band-red.txt`; passing difficulty test; defect lint; independent probe's observed full domains per band.

**Failure modes/limits.** Rotation changes deterministic schedules, not an intrinsic notion of puzzle difficulty. The bands are distribution labels rather than a calibrated human/model difficulty scale.

## D6 — Separate lawful validation from strict teaching support

**Choice.** `self_check` accepts canonical lawful grids with at least one majority-positive position. `strict_canonical_like` additionally requires one-panel and pair-only evidence.

**Rationale.** Canonical validity and training usefulness are related but not identical. A validator should not reject lawful canonical examples merely because a generated lesson policy is stricter.

**Alternatives rejected.** Encoding all teaching requirements in `self_check` risks rejecting lawful external inputs. A permissive shape-only validator would admit impostors and hide malformed controls.

**Probes.** Canonical parity test, profile floor, semantic strict fraction 600/600 and defect lint.

**Failure modes/limits.** Triple evidence is guaranteed by generation but not required by `strict_canonical_like`, because the threshold's positive side is already represented by pair-only cells and canonical validity does not require a triple.

## D7 — Declare executable rivals and witnesses

**Choice.** Add `union_any`, `all_three_only`, and three panel-copy rivals; connect them to five witnesses and use the same functions in `LESSON_COMPETITORS` and `lesson_identifiable`.

**Rationale.** Metadata statements cannot demonstrate that lessons distinguish the intended rule. Executable rivals make the teaching claim falsifiable and source-bound.

**Alternatives rejected.** A hand-written list of rival names without functions cannot score lessons. Claiming simple canonical shortcuts in `CANONICAL_SHORTCUTS` was rejected because none of the five rivals fits every usable canonical pair.

**Probes.** Semantic gate witness/rival reports, task test lesson loops, 300-lesson census and workspace probe.

**Failure modes/limits.** The declared set is not exhaustive. Shared tooling should search undeclared cheap hypotheses too; see `QUESTION_ANSWER.md` and F1.

## D8 — Set two demonstrations and require all query rotations

**Choice.** `EXAMPLES_NEEDED = 2`; lessons use two demonstrations plus one query, and arbitrary query rotation is supported/required.

**Rationale.** Every single generated example already refutes all five declared rivals, so two demonstrations provide redundancy without wasting context. No pair is intentionally reserved as a special query-only witness.

**Alternatives rejected.** One demonstration would be adequate for the named rivals but leaves no redundancy. Three or more demonstrations add token cost without measured benefit for this contract. An ordered-only curriculum would introduce an unnecessary schedule dependency.

**Probes.** Required semantic gate checked 36 rotations; larger census checked 900 rotations; task tests iterate lesson starts; probe checks 30 lessons per band.

**Failure modes/limits.** Rotation evidence is finite and only tests the declared competitors. Downstream assemblers must still preserve one labeled query and the stated two-demo contract.

## D9 — Make generation deterministic, fresh and global-RNG pure

**Choice.** Use `gen_ctx` keyed draws plus a local `layout` RNG; return newly allocated grids.

**Rationale.** Reproducibility is required for source-bound evidence and exact counterexamples. Global Python RNG state must not leak into or out of generation.

**Alternatives rejected.** Module-level RNG calls or cached mutable grids would make replay and parallel generation unreliable.

**Probes.** Determinism/global-state test, override replay matrix, rule-smoke A-B-A checks and workspace probe.

**Failure modes/limits.** Changing `VERSION`, labels or draw order intentionally changes deterministic instances; such changes require fresh evidence and a new post-repair solve.

## D10 — Retain both regression tests and a lightweight standalone probe

**Choice.** Add 23 portable task tests and `workspace/probe_majority_contract.py`.

**Rationale.** The task-test stage is the acceptance-grade integration path; the standalone JSON probe gives future agents a cheap semantic diagnosis without parsing the full battery.

**Alternatives rejected.** Relying only on the general battery would miss task tests because they are not auto-discovered. Relying only on the probe would omit Racket and shared contract checks.

**Probes.** `checks/task-tests/result.json` and `checks/final-majority-probe.json`.

**Failure modes/limits.** The probe uses the Python mirror and a finite seed schedule. It explicitly does not replace the authoritative battery or larger lesson census.
