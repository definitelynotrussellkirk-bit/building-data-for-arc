## d476983a3d6c

**Finding: High — object-color count reveals the command branch throughout the generated curriculum.** The generator never supplies evidence that distinguishes reading the command value from choosing the bend direction using the number of other colors. This is a teaching defect; no incorrect label on a generated input is alleged.

**Source binding.** Audited and rechecked `generators/d476983a3d6c/generator.py` SHA-256 `80d94a6e64895839b4da9c63524f47d7ea1568fa2714a8f846933ccd166fb497`. Both official Racket executions report that generator hash, executed rule hash `c83bfd047bef`, rule text SHA-256 `7494f424963eb40b6949c8ab526c75fe2acfc7a5db52c325afcc6d915e88ba82`, and `rule_hash_matches_catalog: true`.

### Mechanism and impact

`SCENE_SIGNATURES` at generator line 66 couples the command to paired-color and singleton-color counts:

| Scene profile | Command | Paired colors | Singleton colors | Object colors, excluding (0,0) |
| --- | ---: | ---: | ---: | ---: |
| `cmd1_three_pairs` | 1 | 3 | 0 | 3 |
| `cmd2_two_pairs` | 2 | 2 | 0 | 2 |
| `cmd1_two_pairs_singleton` | 1 | 2 | 1 | 3 |
| `cmd2_three_pairs_singleton` | 2 | 3 | 1 | 4 |

An executable rival can preserve the input, count distinct nonzero colors outside `(0,0)`, use horizontal-then-vertical paths when that count is odd, and use vertical-then-horizontal paths when it is even. It otherwise connects exactly-two-cell colors in first-appearance order. This rival never reads the command value to select its orientation.

Generation takes its command and counts directly from this table at line 625. Validation also requires one of the same signatures at lines 276–284. Consequently the rival agrees with the intended command branch on every generated or validator-accepted input, including explicit scene/grid overrides. More seeds, difficulty bands, or lesson rotations cannot provide a separating example while this table remains the entire domain.

The lesson gate iterates the declared `LESSON_COMPETITORS` at lines 453–461; the count-based rival is absent. Its success against the declared rivals therefore does not establish that the command is taught. The existing notes acknowledge profile coupling, but the retained executable rival demonstrates a specific systematic shortcut caused by that coupling.

### Reproduction and evidence

The portable probe uses `reviewer_support.find_root`, `load_selected_generator`, and `canonical_pairs` and asserts the assigned source hash before sampling.

- The rival matches **3/3 labeled canonical pairs**. All three pass `self_check`.
- It matches the Python mirror on **36/36 generated draws**, covering all three difficulties and all four profiles, with nine draws per profile. Every `self_check` and `strict_canonical_like` result is empty. `probe.json` retains every seed, sample index, profile, validator result, and input/actual/rival hash.
- The retained five-pair lesson uses seed **476984**, difficulty **medium**, sample indices **0–4**. Its four demos pass `lesson_identifiable`; the undeclared rival matches all four demos and the query. Exact grids and both outputs are in `lesson.json`.
- Official Racket evaluation of the generated draw at seed **476984**, sample index **0**, difficulty **medium**, matches the rival. Its input hash is `38af92ebbed85670efc7d1c1533c073cdc695042628564fa8eb14153cc8a7f98`; its Racket/rival output hash is `c03026c56ac27aad1773b01afa52a144ed1e04cb350f749b1c04a1637e519d04`. See `generated-input.json`, `generated-rival.json`, and `generated-racket.json`.

### Small separating witness

`input.json` is an 8×8 zero grid with command **1** at `(0,0)`, color **3** at `(1,1)` and `(2,2)`, and color **4** at `(4,4)` and `(5,5)`. It uses the smallest declared dimensions and the minimum two marker pairs: five nonzero input cells total. No path crosses a foreign marker.

The official Racket rule validly draws horizontal-first paths. The rival sees two object colors and draws vertical-first paths. The complete outputs differ at four cells:

| Cell | Racket output | Rival output |
| --- | ---: | ---: |
| `(1,2)` | 3 | 0 |
| `(2,1)` | 0 | 3 |
| `(4,5)` | 4 | 0 |
| `(5,4)` | 0 | 4 |

Both validators reject this witness with exactly one reason: `command, pair count, and singleton count do not match a declared scene profile`. It is a handcrafted counterfactual, not a generated draw. Its rejection documents the missing separating case and is not presented as a generated-label failure.

Hashes using the official compact-grid serialization:

- Input: `f2ac9a3a1056c3f13a45cc6a9f46e0721a86c9f5e57cb51e95360f5d7f476af7`
- Racket output: `213f24436a15f7854392a9010f7f145d54f314d5c36dc8cc78034f9838d99921`
- Rival output: `6152f43fbe4e69eb0574b0878039bc953d45d9368e87a01d7dc4be5e99f2d1fd`

`racket.json` retains the official apply receipt and actual grid; `rival.json` retains the rival grid. `finding.json` combines the binding, validator results, cell differences, and hashes.

### Commands, scope, and recommendation

All evidence is under `WORK/checks/audit/d476983a3d6c/`. `command-records.json` records exact command argv, cwd, exit code, log path, and log hash. The probe, witness apply, generated-draw apply, and final evidence verification each exited **0**. The outer cwd was `/workspace/scratch/223e51309a1a/review`; official apply ran through `review.py run` with effective cwd `WORK/repo`.

The audit inspected the assigned source, its notes and tests, and the current review index, then checked three canonical pairs, 36 generated draws, one generated lesson, and two official Racket outputs. It did not rerun the full audit battery. No audited source, notes, tests, catalog, or shared tool was edited.

Recommended future repair: include matched object-count configurations under both command values, add this executable rival to the semantic contract, and require generated lessons to refute it. The validator and sampler must permit such separating configurations; adding the rival alone would expose the failure without resolving it. This audit applies no repair and grants no approval.
