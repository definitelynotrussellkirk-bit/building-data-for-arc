## F3: Randomized allocation and data-quality audit

**Proposal only:** keep the current 10% evaluation focus, draw probabilities, weights, approvals and training boundaries. This sample is separate from the official adversarial audits.

**Reproduction:** seed `77e4493c00addcfebbc4cc99cafd86e44a9be839938cf6b19e918d43c4cde85e`; `random.Random(int(seed,16)).sample(sorted(manifest["generators"]), min(3,len(manifest["generators"])))` selects **b6edfc119780, 10bc62b2de84, 69ebef53a2ac**, in order. Manifest SHA-256: `d6455f690c4ca33908aed3eada89e50d2dcac36352ad1bdde82b0f0f3d70cf12`. `checks/allocation/report.json` records all 37 inspected source/evidence hashes and 21 bounded generator calls (20 grids and one intentional rejection), with zero new Racket executions/model jobs. Reproduce with `checks/allocation/replay_allocation_audit.py --archive ORIGINAL.zip --work-root WORK --out REPORT.json` from the outer folder, using the script's actual WORK-relative path.

### Actual pools and weights

The packet has 3,941 generator IDs (1,571 approved), 252 main IDs and 250 normal IDs in the approved-originals-needing-parameters tier. Other tiers contain 555 originals needing repair/parameters and 1,767 other unapproved generators. It reports 198 current prototypes; this audit does not verify their settings/four-query coverage. The 10% focus includes all 120 public evaluation tasks. Only `5545f144` has eligible descendants (two waypoint generators); 119 anchors use inspired-extension fallback on the normal target. Direct mapped targets therefore receive nominally 1/1,200 assignments, while total focus remains 10%.

`repo/src/arcpuzzles/review_full_draw.py` selects authoring work by seed/hash/pool, without weights; its live bytes match the packet. `repo/src/arcpuzzles/datasets.py` first defaults to approved-only filtering, then uses positive catalog `mix_weight`. The catalog has 3,925 weights of 1.0 and 16 of 0.0. All sampled rows have weight 1.0, but only `10bc62b2de84` is approved. Equal raw weight neither admits the other two nor admits model trajectories.

### Source-specific evidence

Sources are `repo/generators/<ID>/generator.py`; exact SHA-256:

| ID | SHA-256 |
| --- | --- |
| b6edfc119780 | `63085213ec783db23b4a73a9648b85df85305d670e521012f585421d977d5b82` |
| 10bc62b2de84 | `5c1afcc5dcdc13ab461d1e327cf2ff8decb4300c0af524bf96f73f9ad2818756` |
| 69ebef53a2ac | `d9ebdee765eebc86d9220bb2947fb31c11c912cf85f7bff716b104fd73d5740a` |

- **b6edfc119780:** Sparse row closure/longest-span/topmost-tie grammar. The current schedule teaches tie, row-rank, color and marker-count contrasts. Seed 17/indices 0–6 gives seven distinct inputs; its Python lesson hook accepts four queries from three demos. This is not fresh Racket certification. `evidence/associated_notes.jsonl` retains reports of profile repair, authority agreement, low global density and incompatible ties; old check references are not current-source receipts. A fresh three-row/last-row-winner/`top_tie` request correctly raises `ValueError`. Sparse endpoints need not match a global density median.
- **10bc62b2de84:** Component extraction, left ordering, cropping and bottom packing. Current generation forces unequal heights, separating the top-aligned rival. `notes.md`, `evidence/review_index.json`, `counterexamples/top_aligned_shortcut.json` and `repo/REVIEW/approvals/72e86a2a95e965799c56ab6264dddc5b05cdb34397b8945b4dc42e790a86d914.json` bind a reviewer-reported accepted repair. Reported 24,480 overrides, 630 axis combinations and 300 lessons were not rerun. `repo/shared/tools/proposals/807e705cf509db23/checks/semantic-first/checks/10bc62b2de84_after_semantic_gate.log` retains an intermediate `declared_period_not_enumerated` warning; current code removed that declaration. This is neither a current failure nor current census proof. Seven seed-17 inputs are distinct with unequal heights. Repeated colors, touching objects, tied left edges and undeclared rivals remain outside that evidence.
- **69ebef53a2ac:** Horizontal reflection of one connected, one-color component. At seed 17/index 0, `num_marks=1`, `num_marks=6`, `n_distinct_colors=2`, `palette_kind="rainbow"` and an unknown key all produce the identical four-mark, one-color grid and pass `self_check`. Declared controls and multicolor teaching comments overstate current coverage. No `RULE_HASH`, executable lesson/rival contract or retained current lint receipt occurs in this selected home. This is a reproduced contract failure, not a corpus failure-rate estimate.

No sampled home contains a parametric-rule workspace or retained Racket-verified four-query receipt. Input axes, demonstration counts and single-query rotations do not establish those features. No full linter was rerun; absent evidence is not a pass. Selected authority files are `repo/shared/data/base/solutions/banks/129d068bbf4e/S18_E7__b6edfc119780.json`, `.../5dfff1627b31/medium_p06__10bc62b2de84.json` and `.../2eea055c3155/easy_04__69ebef53a2ac.json`. Their executable targets define inspected grammar; archival helper chains/catalog tokens do not measure executed coverage. All three are bank records. ARC-GEN/RE-ARC were not sampled, so no source-wide ranking or source-volume recommendation follows.

### Alternative, cost and stopping rule

Preserve selection policy, but allocate a small local budget to source-bound control/lesson repair and four-query evidence before adding more same-rule one-query episodes. Four separate 3-demo/1-query episodes need 16 pair labels; one 3-demo/4-query episode needs seven. Conditional on four distinct, Racket-correct, demo-identifiable queries, that saves nine labels (56.25%) and gives ~2.29× usable queries per label before caching. It does not add rule diversity or measure Qwen benefit. Correlation, longer prompts, deduplication and rejects can reduce the gain. Estimated review cost: 5–15 minutes for the approved packer's focused receipt versus 30–60 for the mirror's control/authority/lesson repair; these are not measured timings.

Proposed pilot: approved `10bc62b2de84`, seeds 17 and 23, two 3-demo/4-query episodes (14 labels), matching Racket authority, all inputs disjoint, each query checked against top alignment using only demos. Reuse accepted receipts for unrelated gates. Cap at 20 reviewer minutes and 28 attempted labels; stop on hash/rule mismatch, duplicate accepted query or a surviving rival changing an actual query. Retain seeds and rejection denominators; never clone or silently shorten. Unapproved samples remain authoring-only; no corpus sweep/model job.

## Suggested answer: qwen9-data-value

**Add an export gate checking that demonstrations determine every actual query answer among declared lawful rule alternatives.** Keep all candidates matching every demo; reject/resample if survivors disagree on any query input. Select survivors using demonstration evidence only and check every query after final assembly.

**Failure:** The `4ca8a7b38652` count-scope settings `nonzero` and `all` agree on zero-free demonstrations. On lawful query `[[0,1,0],[2,0,1],[0,2,0]]`, they produce 6×6 versus 9×9 outputs. Individual Racket labels may be correct while the episode is underdetermined. Use zero-free demos `[[1,1,2],[1,2,2],[1,2,1]]`, that layout recolored to 3/4, and `[[1,2,3],[2,3,1],[3,1,2]]`. This is a constructed negative test, not a claim that the current fixed curriculum emits it.

**False positive:** Zero-free demos followed entirely by zero-free queries remain answer-identifiable: the two surviving settings predict the same answers. Accept those. Reject only actual lawful query disagreement and exclude out-of-domain rivals. This is finite-rival evidence, not universal identifiability.

**Cheapest test:** Reuse both materialized Racket programs. Check the negative episode, a positive with one zero-present distinguishing demo, and a zero-free-query positive control. Place the ambiguous input fourth to catch partial query checking, and change only hidden query labels to ensure admission is unchanged. Cache demo labels; no Qwen training/corpus sweep. These extra Racket checks were not executed in this allocation audit; retain their actual result with focused prototype evidence. Expected benefit is fewer underdetermined supervision records, not measured model improvement.
