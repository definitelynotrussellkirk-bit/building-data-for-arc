## 57488f2a7c15 — reproduced teaching gap: a completed pair can falsely mark its entire color as finished

**Finding:** an ordinary ordered lesson with the declared five demonstrations does not distinguish the canonical cell-by-cell reflection rule from the plausible shortcut, “If a color already has a complete mirrored pair, that color is finished; copy only the other colors.” The shortcut matches all five demonstrations and all five canonical pairs, then gives the wrong query answer. This is a new teaching counterexample on the selected version, not a recurrence of the earlier conflicting-color defect.

The audited generator is version 2.0.0, SHA-256 `695c31b0bf2506cde10a9f240b78d59f1bb5efd85038186bc9f532d4305eeaa7`; canonical rule hash is `2b970065d6a3`. Source files, rules, catalog and assignment were not modified. `checks/audit/57488f2a7c15/hashes.json` also binds the raw Racket source, canonical ledger row and executable probe.

### Production witness and exact disagreement

The public `Catalog.generate` invocation used **easy, seed 0, start sample index 17, no overrides, omitted `n_train`, one query**. Current public generation correctly resolves the declared minimum to five. Its native receipt records accepted indices `[17, 18, 19, 20, 21, 22]`, six attempted pairs and no rejections. All six inputs pass `self_check`. This witness uses consecutive, ordered production examples, with no query rotation, shortened prefix or displaced schedule.

| Role | Sample index | Colors with an existing complete off-diagonal pair | Those colors also have an incomplete source? | Rival matches Racket? |
|---|---:|---|---|---|
| Demonstration | 17 | none | no | yes |
| Demonstration | 18 | 3 | no | yes |
| Demonstration | 19 | none | no | yes |
| Demonstration | 20 | none | no | yes |
| Demonstration | 21 | 1 | no | yes |
| Query | 22 | 3 and 7 | yes, both | **no** |

Exact query input, also saved in `checks/audit/57488f2a7c15/input.json`:

```json
[[0,7,3,0,3],
 [0,0,5,2,7],
 [3,0,5,0,2],
 [0,0,8,0,8],
 [0,7,0,0,0]]
```

Using zero-based coordinates, color 7 already occupies the pair `(1,4)` / `(4,1)`, but its additional source at `(0,1)` still needs a new 7 at `(1,0)`. Color 3 occupies `(0,2)` / `(2,0)`, while its source at `(0,4)` still needs a new 3 at `(4,0)`. The rival leaves both destinations zero. Actual canonical Racket output supplies 7 and 3, respectively; the remaining cells agree. Full native output is in `checks/audit/57488f2a7c15/racket.json`, and the independent rival output is in `checks/audit/57488f2a7c15/rival.json`.

The five canonical inputs contain no complete off-diagonal pair, so the shortcut remains consistent with them. Their outputs were independently rerun with `Catalog.apply`, and all five agree both with the canonical records and with the rival (`checks/audit/57488f2a7c15/canonical-racket.json`). The full generated lesson and native sampling/provenance receipt are in `checks/audit/57488f2a7c15/episode.json`; every demonstration label in the comparison came from native Racket-backed generation.

### Why the current checks miss it

The current schedule balances source triangle and diagonal-color context. `n_pairs` is sampled separately, and its presence does not guarantee that a completed pair's color also occurs in an incomplete orbit within the demonstrations. The two demonstrations with completed pairs therefore teach preservation of those pairs without distinguishing whether completion operates on each cell or stops after a color has any completed pair.

The supplied 11 distinct rivals omit this shortcut. For this exact production lesson, the generator's `lesson_identifiable` returns `[]` and the native lesson report is `passed_declared_hook`, with all declared rivals refuted. Those bounded results are accurate for their declared scope; this counterexample exposes an additional useful rival, not an incorrect claim that the finite checker examined every possible rule. The independent rival reads only the input grid and does not inspect a seed, sample index, expected output, or generator metadata.

An actionable future repair would add this color-level shortcut to the declared competitors and ensure a demonstration includes an already-complete pair plus an additional incomplete orbit of the same color whenever needed by the lesson. A focused regression should retain this six-pair production witness and require its relevant copying behavior to be demonstrated. No audit-target repair was made.

### Reproduction, coverage and limits

Run from `WORK` in a fresh evidence directory:

```bash
python3 checks/audit/57488f2a7c15/probe.py --out checks/audit/57488f2a7c15/replay
```

The probe materializes the public episode, records canonical Racket labels, runs the native `apply` command, and verifies all agreements and disagreements. The authoritative query command actually executed from `WORK` was:

```bash
python3 run_with_racket.py python3 -m arcpuzzles apply 57488f2a7c15 --input ../checks/audit/57488f2a7c15/input.json --out ../checks/audit/57488f2a7c15/racket.json
```

`checks/audit/57488f2a7c15/commands.json` records all three evidence commands, their exact argument vectors, caller/effective working directories, stdout/stderr files, timing and exit codes: **3 executed, 3 exited zero, 0 nonzero exits**. `checks/audit/57488f2a7c15/assessment.json` contains the machine-readable finding, native five-demo policy, all pair agreements, validator results and two differing query cells. Nonzero source-inspection commands are retained separately in `checks/audit/57488f2a7c15/inspection-failures.json`; they were missing-path reads and the packet's lack of Git metadata, not hidden test failures.

Coverage is deliberately focused: one six-pair production lesson, all five canonical pairs, and an independent query rerun — **12 native Racket label evaluations**. Candidate discovery generated 23 easy inputs at seed 0 and examined the 18 possible five-demo starts 0 through 17 before selecting this witness; that structural discovery computed no reference labels. The target's three existing test files and current notes/review index were read; their historical battery and test counts were not rerun or adopted as new audit evidence. No prevalence, universal identifiability, hidden-score or training-performance claim is made. The selected source remains free of a demonstrated color-conflict or incorrect-reference-label defect in this audit; the reproduced issue is insufficient teaching against this concrete color-level alternative.
