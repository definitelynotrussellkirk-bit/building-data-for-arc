## 04e2ffe8dc8e

**Classification: reproduced teaching shortcut and exact-control mismatch. Audit-only; source unchanged.**

Audited `repo/generators/04e2ffe8dc8e/generator.py` SHA-256: `21425260e0af633b53e19f217a8e6ba3f5959fa48b77b62a1356156ad465a165`, exactly the drawn audit source. The supported reference command executed canonical Racket rule `c67640298f12`; its rule hash matches the catalog.

**A1-04-TEACHING — four demonstrations still permit the wrong color-selection rule.** Generate with seed **3**, difficulty **medium**, no overrides, and consecutive sample indices **0–4**. The first four inputs contain only green foreground components. The plausible rival “recolor the globally smallest same-color, four-connected non-background component magenta” therefore fits all **4/4 actual Racket demonstration outputs**. The fifth input contains a smaller color-2 singleton at `(3,1)` and a smallest-green pair at `(3,8),(3,9)`. Actual Racket preserves the singleton and recolors the green pair; the rival does the reverse, disagreeing at exactly **three cells**. Coordinates are zero-based. All five inputs pass the target's final `self_check` and were generated inside its ordinary domain.

This independently reproduces the current review index's unresolved lesson-identifiability concern and extends its tested scope from three to **four consecutive demonstrations**. It does not establish how often the defect occurs. Individually correct labels do not ensure the demonstrations distinguish green-qualified selection from global size selection.

**A1-04-DECOY — an advertised decoy can contain no decoy.** Seed **0**, index **0**, medium, with `texture="decoy", small_size=1` passes `self_check` yet contains **zero non-green foreground cells**. Its actual Racket output equals the global-smallest rival. The source adds a decoy only when `small_size == 2`; the advertised joint request is neither fulfilled nor rejected as incompatible. This freshly confirms the existing source-bound override finding.

**Suggested repair direction:** guarantee an actual smaller non-green witness in each supported demonstration window and retain an executable global-smallest rival/lesson check. Treat `decoy` with `small_size=1` as an explicit incompatibility or revise the supported contract; silently omitting the promised decoy does not teach the color restriction. No repair, approval, or audit-resolution change was made here.

**Reproduction and scope.** The bounded search stopped at seed 3 after four seeds; only six saved inputs were sent to Racket. `checks/audit/04e2ffe8dc8e/probe.py` reproduces generation and the independent rival comparison. `generation.json` and `inputs.json` retain seeds, indices, overrides, grids and validator results. `racket.json` contains actual reference outputs, rule/source bindings and per-grid hashes. `finding.json` combines each input with authority/rival outputs and disagreement coordinates. `commands.json` records all three exact commands, cwd/environment, exit codes and output paths; each exited **0**. `manifest.json` hashes the evidence files.

From the outer extraction folder, the reference execution was:

```sh
/dev/shm/arc_review_071004/extracted/WORK/.venv/bin/python review.py run /dev/shm/arc_review_071004/extracted/WORK/.venv/bin/python -m arcpuzzles apply 04e2ffe8dc8e --input ../checks/audit/04e2ffe8dc8e/inputs.json --out ../checks/audit/04e2ffe8dc8e/racket.json
```

The recorded command uses the absolute interpreter path on both occurrences; use that exact argv from `commands.json` for replay because `review.py run` changes the payload cwd to `WORK/repo`. Checked scope: selected current source, notes, existing source-bound audit status, canonical rule/examples, six generated grids, final validator, actual Racket labels and one rival. No lint/battery rerun, corpus census, proof over all lessons, or defect in the Racket transformation is claimed. Missing `RULE_HASH` and duplicate validators were observed in source but were not independently re-linted in this audit.
