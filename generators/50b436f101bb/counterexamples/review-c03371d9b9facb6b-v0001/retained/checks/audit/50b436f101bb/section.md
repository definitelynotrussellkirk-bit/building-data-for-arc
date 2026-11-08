## 50b436f101bb

**Classification: current-source validator defect; teaching/distribution shortcut; ignored declared axis.** Findings-only audit: no generator, rule, or shared file was edited.

**Binding.** Audited `repo/generators/50b436f101bb/generator.py`, version 3.2.1, SHA-256 `748cd41ef175b9445cca25f8f03e8c4a143b13e29a0943497d4c2dc34e7cfc4b`. Actual canonical Racket rule text SHA-256 `84104d23b8f1297f1583a4f19ed0b532c17059de8fa695c4a321bd6096203e9a`, executed normalized hash `427028b09a7e`, matches catalog. The target has no `evidence/review_index.json`; `notes.md` is an empty decision scaffold and `associated_notes.jsonl` is empty. Thus these are newly demonstrated findings on current bytes, not a claim about resolving or repeating an old audit. Apply reports existing `train_safety=unsafe`, `approved=false`; that status is not the proof of these findings.

### 1. Self-check accepts an input on which the reference cannot return a grid

`self_check` checks aggregate color counts, requiring at least 20 cells of a dominant non-background color, but does not check that the selected cluster's bounding box admits the inset-two crop. Input 2 in `checks/audit/50b436f101bb/input.json` is a 15×15 zero background with a solid 3×7 color-2 bar at rows 2–4, columns 2–8 (21 cells). It is handcrafted: seed/index/overrides do not apply. Both direct `self_check` and `apply --check-generator-domain` accept it (`[]`, domain `valid`). Actual Racket returns no valid grid: `output=null`, `valid_output=false`, error `rule returned a value that is not a rectangular 0-9 grid`. The nominal inset has height −1. This is a concrete domain-validator false acceptance, not evidence that ordinary default generation emits this bar.

### 2. Default distribution teaches a color-frequency shortcut that fails canonical data

Rival: ignore clustering and single-color eligibility; take the globally most frequent non-background color, crop that color's global bounding box inward by two, retain that color and replace others with background. The current generator makes one conspicuous same-color frame and a same-color interior, with tiny separated distractors. Consequently this rival agreed with an independently authored Python translation of the reference on **64/64** default draws (`seed=17`, sample indices `0..63`, difficulty `None`, overrides `{}`); all 64 passed self-check. Those 64 comparisons are Python probes, not 64 Racket executions or a universal proof.

The rival matches **0/10** labeled canonical pairs across both variants, loaded via `reviewer_support.canonical_pairs`. Canonical motifs reuse colors across groups and require selecting a single-color cluster rather than aggregating a color globally. Actual Racket input 0 verifies the generated witness (`seed=17`, index=0, no overrides): a valid 5×5 output identical to the rival. Input 1 verifies the canonical contrast (variant 0, train pair 0): actual output `[[4,4,3],[3,4,4],[4,4,3]]`, identical to the canonical label, while the rival returns a 12×5 crop. Exact rival grids are in `checks/audit/50b436f101bb/rival.json`; per-pair identities and outputs are in `checks/audit/50b436f101bb/probes.json`.

This establishes a useful teaching contrast and distribution weakness. No canonical rule/output mismatch was found on the executed canonical witness. A repair should include competing groups and repeated colors that force cluster-based, single-color selection.

### 3. Declared `rect_size` override is ignored

`AXES` advertises `rect_size` as an integer axis, but `generate` chooses size only from `texture`, difficulty, or RNG. At seed 17/index 0, `{rect_size:7}` and `{rect_size:11}` produce identical grids. The advertised alias `{texture:"s7"}` versus `{texture:"s11"}` does change the grid. This focused probe is recorded in `probes.json` and reproducible by `audit.py`. Related summary/invariant prose still says zero background and a solid two-wide ring although current code draws dotted motifs with frequently nonzero background.

### Evidence and limits

Run `WORK/.venv/bin/python3 WORK/checks/audit/50b436f101bb/audit.py` from the outer packet directory to regenerate the input/rival/probe files. Then use the exact supported apply command in `checks/audit/50b436f101bb/command-records.json`; payload cwd is `WORK/repo` and its interpreter path is absolute. Its exit **1** is expected and retained because input 2 fails; inputs 0 and 1 both execute successfully. `racket.json` includes actual outputs, errors, self-check domain results, and source/rule hashes. `summary.json` is a compact extraction.

No full battery was run. All ten canonical labels were compared to the rival, but only one canonical input was independently executed through Racket. The bounded sample does not establish a shortcut-success probability outside the stated draws. No source repair, approval, audit resolution, or training admission is claimed.
