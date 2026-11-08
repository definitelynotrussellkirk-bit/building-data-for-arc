# Final independent code review: b8aea529acfd

## Verdict

**Ready from code review. No unresolved Critical, Important, or Minor source findings.** The Important duplicate-rejection defect found in the intermediate source is repaired in the current source and confirmed through supported production materialization. Final full battery/census acceptance remains the parent's separate verification responsibility; this review does not substitute for it.

Reviewed baseline commit: `09727a5a94ea62828ac2e23c2c23ef6fbbb56bb5`.

Intermediate reviewed generator SHA-256: `ef3d5004a125590f7af14f3fbe8bd0228532233557fde310f1d92ad8a01b1212`.

Current reviewed generator SHA-256: `5f2c9d9237f759ae3b52d75e7c9eb1d3e7b801e554713d55ff3e265061c1d999`.

Selected Racket authority hash remains `8e26e8f07755`. Review scope was generator.py and the two task tests, plus narrowly scoped public generation and rival scoring. No selected source, index, or HEAD changes were made by this reviewer; no full battery or census was duplicated.

## Resolved Important finding

In the intermediate source, dense witness edges were random. Easy seed 370, start 0, train 3/test 1 produced identical inputs at raw indices 1 and 3. Public materialization rejected index 3 as a duplicate and accepted indices [0,1,2,4]. The production lesson hook passed, but holding out the only dense witness at index 1 left three anchor demonstrations. Both canonical-fitting crop shortcuts fit those demonstrations and changed the held-out Racket-labeled query.

The retained exact pre-fix lesson is `before.jsonl`, SHA-256 `7e2fa318f34d402b362d89b9829314005d15ac0d2fdfd50c88008535d68fd155`. `rotation.json` retains the rotated query and both rival predictions. `score_rotation.py` independently reproduces the before finding.

The current source forces dense full accent edges to alternate by `(sample_index // 2) % 2`. Interior randomness remains seeded. Consecutive witness slots therefore have opposite full accent edges and cannot have identical inputs.

Replaying the same public command on current source produced accepted indices **[0,1,2,3]**, **zero rejections**, and a passing production hook. `after.jsonl` is SHA-256 `62ba71997a1c35a2be1e969baf5d3767e7993dad05b07b83b018d9bb5d2f65bb` and retains canonical Racket outputs and source provenance.

All four query positions were then held out once and scored against all six current declared semantic rivals. Every rotation had zero hook reasons and zero measured rival ambiguity. `after-rotations.json` retains inputs, authority labels, each rival prediction and demonstration fit, source hash, lesson hash, and accepted indices. `verify_after.py` reproduces the scoring and asserts current source binding.

`commands.json` records exact command argv, working directories, exit codes, source bindings, and evidence paths.

## Structural guarantee and strengths

For ordinary generation with three demonstrations and one query, any four consecutive slots contain two anchors and two witnesses. The two witness slots have opposite complete accent edges, and the opposite edge remains accent-free. Anchor profiles have distinct canvas/geometry/palette signatures within each difficulty band; witness canvas dimensions differ from every anchor in that band. Thus all four raw inputs are distinct, avoiding the materializer's duplicate skip that invalidated the earlier proof.

Each four-pair lesson has two witnesses. Holding out any one pair leaves at least one joint witness among the three demonstrations. Each joint witness defeats both crop shortcuts: the full accent edge makes the majority-color bounding box smaller than all-foreground bounds, and the nonzero majority exceeds black across every reachable accent count.

The dense minimum majority counts remain above black at the maximum accent counts: easy 31 > 30, medium 41 > 34, hard 53 > 38. The motifs remain sparse, strict-majority, fully occupied, padded two-color rectangles. The full edge and empty opposite edge prevent LR and 180-degree symmetry; one interior accent has its vertical counterpart forbidden, preventing UD symmetry independently of other sampled cells. Dense construction uses a single bounded sample with sufficient pool capacity.

All twelve original profiles remain valid exact controls. The period-8 ordinary curriculum rotates all four original anchors per difficulty. The role-aware profile signature prevents a majority/accent swap from falsely realizing the original profile. The filled-body self-check closes interior-hole acceptance. CANONICAL_SHORTCUTS now names only the two rivals that fit every labeled canonical pair. Both task tests use portable reviewer_support access and include seed 370 with four-input uniqueness checks.

## Considered and declined issues

- **Racket authority change:** no rule-authority edit is introduced; supported generation retains the selected canonical hash.
- **Grammar broadening:** dense profiles stay inside the existing padded, sparse-accent, completely occupied two-color rectangle grammar.
- **New convergence or symmetry failures:** dense construction is bounded and explicitly breaks the relevant symmetries; the original retry fallback is unchanged and earlier targeted forced-fallback diagnostics found no defect for shipped counts.
- **Explicit override bypass of curriculum:** intentional and documented exact input control; rotation guarantee is scoped to ordinary generation.
- **Deterministic edge reducing randomness:** appropriate semantic scheduling, with count, row, interior column and additional accents still seeded.
- **Literal rule-hash assertion in portable tests:** a regression pin, with live rule agreement owned by the separate authority/canonical execution gates; restoring a nonportable import is unnecessary.
- **General validator allowing UD/180 symmetry:** canonical acceptance and ordinary generation separation serve different scopes; the constructors enforce the ordinary claim.
- **Optional refactors or broader tests:** declined because no remaining concrete defect justifies them. Full final gates are already being run by the parent.
