# Findings-only adversarial audits

Draw: assignment.py audit selected these two targets after main implementation. No audit target source was modified. The target IDs and hashes are preserved; the random audit seed was lost with the OOM-killed private workspace. AUDIT_ASSIGNMENT.json explicitly records that recovery limitation, without a redraw.

## 26cfe7595a4a

**Reproduced exact-control defects; confirmed canonical representation gap. Findings only; source unchanged.** The existing source-bound audit remains relevant rather than resolved. This audit adds a fresh, bounded Python replay and a source-level explanation of the connectivity gap; root also ran the supported Racket apply command on three retained inputs (3/3 valid outputs). This is a bounded audit, not a complete generator review.

**Identity.** Original packet member `WORK/repo/generators/26cfe7595a4a/generator.py`, version `2.0.0`, SHA-256 `7e1c0eea19980272d2cb3067d01cd9e7f59997346d996d9cc3b0ca136b71c09a`. Selected canonical rule task `26cfe7595a4a`, normalized hash `a6ccad31118b`, raw rule-text SHA-256 `46adbf1580f619905b96cdacaf96844b9b510a3fdbd5e9e8c5725dc0ef1e479f`, from `WORK/repo/shared/data/canonical/puzzles.jsonl`. Catalog status is `unsafe`, not approved; no change to approval or admission is proposed. The source lacks a `RULE_HASH` constant.

### A26-1 — Advertised controls are ignored or rejected inconsistently

Fresh replay at seed `23`, sample index `4`, difficulty `medium` found that `motif_size=2`, `motif_size=4`, `palette_kind="warm"`, `palette_kind="cool"`, and the unknown key `typo=1` all return the same grid as the call with no overrides. All five returned grids pass the current validator. The `motif_size` and palette controls are never consumed by the generator; no unknown-key guard exists. Separately, `generate(23,4,difficulty="easy",grid_h=16)` raises `ValueError("draw_int('grid_h'): override 16 outside [6, 7]")`, although `AXES["grid_h"]` advertises the exact global domain `5..16`.

Evidence: `checks/audit/26cfe7595a4a/evidence.json`, fields `override_probes` and `advertised_grid_h_16_easy`; runnable reproducer `checks/audit/26cfe7595a4a/probe.py`. This reproduces and extends the matching-source prior audit's ignored `motif_size` finding. It is a real request-contract defect, not a disagreement about the crop rule. Suggested repair: consume meaningful controls with observable pixel effects or remove them, reject unknown keys, and honor declared exact bounds consistently or declare genuine incompatible combinations.

### A26-2 — Ordinary generation cannot represent canonical component structure

All three canonical inputs contain one monochrome, 4-connected foreground component, of sizes **5, 6, and 7** respectively. In contrast, the current ordinary construction sets motif colors to `colors[(r+c)%3]` with three distinct colors. Every horizontal or vertical step changes that index, so two same-color nonzero cells can never be cardinal neighbors. Consequently, every monochrome 4-connected generated component is a singleton, irrespective of seed or motif holes. This is a source-level limitation; the bounded observed check independently found it on **12/12 draws**: seed `23`, sample indices `0..3`, all three difficulty bands. All 12 passed `self_check`.

The rule itself is an unconditional tight crop of all nonzero cells, so these generated outputs need not be mislabeled. The concern is canonical representation and teaching distribution: checker-colored disconnected pixels systematically replace the connected monochrome objects in every supplied anchor. Retained source-specific defect lint already reports generated object count about 7 versus canonical about 1 and canonical largest-object size outside generated singleton support. This audit provides the construction argument behind that report.

Evidence: `checks/audit/26cfe7595a4a/evidence.json`, fields `canonical_profile` and `ordinary_generated_probe`; source `generate()` palette indexing. The original retained lint is at `WORK/repo/generators/26cfe7595a4a/counterexamples/review-42253c55fd25c42a-v0001/retained/checks/audit/26cfe7595a4a-defect_lint/checks/26cfe7595a4a_before_defect_lint.log`, SHA-256 `dddf165e3d6814e95509581b55456e330cfb066448d36fbcc7f5c59ab0cc1245`. Suggested repair: restore meaningful canonical monochrome connected-object support while retaining lawful crop variation; verify source-bound profile and grammar coverage. Increasing sample volume alone cannot remove this structural gap.

### A26-3 — Validator and declared domain disagree; reconcile the domain with canonical authority

A 7×8 zero grid with one color-5 cell at zero-based `(3,4)` returns `self_check == []`, despite named invariants requiring multiple nonzero cells and at least two nonzero colors. This freshly confirms the retained validator-contract finding. The singleton is outside the generator's stated ordinary multicolor domain; it is not evidence of ordinary generation emitting that singleton. The canonical crop transformation is defined on it, and the matching-source retained Racket receipt outputs `[[5]]`.

Do not fix this merely by rejecting single-color inputs: **every canonical anchor is itself single color**. The declared grammar, ordinary generator, and canonical coverage must first be reconciled. Racket-defined input legality and the narrower advertised generator domain are distinct here. No rival output is asserted for these contract/coverage findings.

The three inputs used by root for the completed supported Racket replay are in `checks/audit/26cfe7595a4a/input.json`: index 0 is canonical training input 0, index 1 is the ordinary seed-23/index-4/medium generated grid, and index 2 is the singleton validator impostor. The fresh Python report contains crop outputs only for comparison and explicitly records `racket_labels_executed_in_this_probe=false`. `checks/audit/26cfe7595a4a/retained-racket-singleton.json` is copied unchanged from the original packet's prior audit, SHA-256 `f18edcc615b3411dd3e3673bc2b1aa50a4004739bb2156b3342e8ac557cfeb45`; it is **inherited evidence**, not a newly executed command.

### Bounded reproduction and limits

Actual fresh probe: `python -B /tmp/arc_audit_26cfe7595a4a_5514/probe.py --zip /workspace/scratch/f3b8fc463f03/upload/SEND-THIS-ARCpuzzles-review(20261023-064546).zip --out /tmp/arc_audit_26cfe7595a4a_5514/evidence.json`, from `/workspace/scratch/f3b8fc463f03`, final exit `0`. The probe selects only this task and eight unchanged pure-Python runtime dependency files. It performs 12 ordinary draws, one baseline draw, five control calls, one rejected size call, three canonical input inspections, and one handcrafted singleton validation. A ZIP-import setup failure and an evidence-write space failure preceded the successful run; neither is a generator test failure. Setup details are retained in `checks/audit/26cfe7595a4a/setup-failure.txt`.

Portable replay after copying the small probe into the return: from `WORK/`, `python3 run_with_racket.py python3 ../checks/audit/26cfe7595a4a/probe.py --repo . --out ../checks/audit/26cfe7595a4a/replay-evidence.json` (new output path; this portable invocation is documented, not run by this subagent). Root then ran `python3 run_with_racket.py python3 -m arcpuzzles apply 26cfe7595a4a --input ../checks/audit/26cfe7595a4a/input.json --out ../checks/audit/26cfe7595a4a/racket.json`, exit 0. The retained `racket.json` and `racket-console.log` report 3/3 valid outputs, with matching source/rule hashes and outputs equal to the retained Python crops. The Python-only probe flag remains truthful for that earlier probe.

The current review index (`WORK/repo/generators/26cfe7595a4a/evidence/review_index.json`, SHA-256 `7827bba8c95d63da3ea3dc2afcd2238899706daa5a628c977450b5ee8098a70f`) retains the same-source prior audit as `needs_triage`, with accepted triage and reviewer-reported verification. No source, rule, approval, or audit-resolution state was changed. No battery, corpus-wide census, model job, or universal lesson-identifiability claim was attempted.


## 735ba14c7162

**Findings-only audit: defects found; no target source, tests, authorities, or approval records edited.** The row-gravity transformation behaved correctly in the bounded Python checks. The actionable defects concern false semantic metadata, test portability, and scalar input validation.

### Exact sources and evidence

Inspected the original supplied ZIP, `SEND-THIS-ARCpuzzles-review(20261023-064546).zip`, without extracting the full archive.

| Source | SHA-256 |
|---|---|
| `WORK/repo/generators/735ba14c7162/generator.py` | `9fe7aac58ae7ec3b3a859dc2b5e00daa55cea264b6f21014bdf2e4d0c0aaf630` |
| `WORK/repo/generators/735ba14c7162/test_generator_735ba14c7162.py` | `c209bb8cc1b0f2e4168c459d0d949e6a0a7e6e244615ef37eaa00399089afc10` |
| `WORK/repo/generators/735ba14c7162/evidence/associated_notes.jsonl` | `a26440a8b52a5ec50e7fbf68bbe39b1bf8cc1778339d0459d5488d179257b327` |
| Exact canonical `program_solution` text | `3a57e906c3d31d0c9a44aea04fddfdf2f28a2290d465b9eeff2d2b608ec16f69` |
| Whitespace-normalized canonical program | `63d032c43a969458a5e062223673564063bbe26d200844fef17c381763d4db61` |

The canonical ledger identifies bank `97e1cc8b45f0`, original ID `E46`, with two demonstrations and one labeled test. Its selected rule is `(rule! ... (gravity g "right"))`; the normalized hash agrees with declared `RULE_HASH = "63d032c43a96"`. The exact canonical JSONL row, including its newline, hashes to `52af8aa157a9cff5aaf1e7c1e9351f2bb2771dac75ce327ed2b04cbdd62a8119`.

Machine evidence: `checks/audit/735ba14c7162/evidence.json`. A concrete three-input Racket probe is `checks/audit/735ba14c7162/racket-probe.json`; it contains one batched `gravity` expression, the three supplied canonical expected outputs, and the exact canonical rule/hash. No fresh Racket execution was performed for this target; the probe is an input fixture, not an execution receipt.

### Finding A: six false `CANONICAL_SHORTCUTS` assertions

The generator assigns `CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)`. In the included semantic gate this field asserts that each named solver fits **every labeled canonical pair**. These entries instead describe intentionally wrong competitors, already correctly listed under `SEMANTIC_RIVALS` and `LESSON_COMPETITORS`.

Executing the six Python competitors against all three supplied canonical input/output pairs produced:

| Declared canonical shortcut | Canonical mismatches | Pair indices, train 0/train 1/test 0 |
|---|---:|---|
| `identity` | 3/3 | 0, 1, 2 |
| `left_pack` | 3/3 | 0, 1, 2 |
| `reverse_order_then_right_pack` | 3/3 | 0, 1, 2 |
| `sort_colors_then_right_pack` | 2/3 | 0, 1 |
| `pack_only_first_active_row` | 3/3 | 0, 1, 2 |
| `move_each_cell_one_step_right` | 3/3 | 0, 1, 2 |

This is a semantic-contract defect, rather than an inferred geometric defect. `WORK/repo/shared/tools/generator_semantic_gate.py` explicitly appends an error for each invalid declared canonical shortcut and states that partial/noncanonical heuristics belong in `LESSON_COMPETITORS`. A full current semantic-gate run was not performed here; the false declarations are established directly by the recorded canonical comparisons.

**Bounded proposed repair:** remove the false entries from `CANONICAL_SHORTCUTS`, retaining the useful six rivals and lesson competitors. Do not change the canonical Racket or weaken the gate. Confirm the corrected classification against the three canonical labels and one targeted semantic-gate run.

### Fresh recovery replay

The runnable `checks/audit/735ba14c7162/probe.py` was executed after recovery,
exit 0. `replay-evidence.json`, `console.log` and `command-receipt.json` retain
its exact source/input bindings and command. The replay confirms all six false
canonical-shortcut declarations, acceptance of all seven invalid scalar calls,
and 12 bounded draws with seven unique inputs. All five witnesses fire on all
12 draws, each of the six rivals disagrees on all 12, the four declared mutation
fixtures are rejected, and the inspected input grids are not mutated. This is
fresh Python evidence. Racket was not executed, and the earlier frozen-test
static preflight was not rerun. The selected main generator remained unchanged.

### Finding B: canonical fixture path breaks source and task-test mirrors

The frozen test uses `ROOT = Path(__file__).resolve().parents[3]` followed by `ROOT / "data/canonical/puzzles.jsonl"` (line 18). That depth works in its legacy execution location, `puzzle_generators/per_puzzle/735ba14c7162/test_generator_735ba14c7162.py`. It does not work in the repository/task-test mirror at `generators/735ba14c7162/test_generator_735ba14c7162.py`.

The packet's `_task_test_snapshot` collects the latter mirrored file. A small copied-layout fixture, with a canonical ledger present at the correct runtime path, was inspected using the packet's unmodified AST functions `_static_test_path`, `_missing_legacy_import`, and `_task_test_import_diagnostics`. The result was an **error**, code `fixed_depth_canonical_path`, at line 18, resolving the requested ledger outside the selected runtime. The evidence JSON retains the precise diagnostic and method. This was a static preflight reproduction, not a full pytest invocation.

**Bounded proposed repair:** use `reviewer_support.find_root(__file__)`, `canonical_path`, and `canonical_pairs`; bind the generator with `load_selected_generator`. Replay the frozen tests in the actual relocated task-test layout. Preserve the three canonical input/output pairs and exact rule-hash assertions.

### Finding C: invalid scalar generation controls are accepted

`generate` validates override names but does not enforce seed/index scalar types before constructing `gen_ctx`. All seven bounded probes below returned grids instead of rejecting the controls:

| Seed | Sample index | Result |
|---|---|---|
| `True` | `0` | accepted, 8×9 |
| `1.0` | `0` | accepted, 4×10 |
| string `"1"` | `0` | accepted, 5×9 |
| `1` | `True` | accepted, 4×10 |
| `1` | `-1` | accepted, 6×7 |
| `1` | `1.5` | accepted, 8×8 |
| `1` | string `"1"` | accepted, 6×8 |

This leaves integer seed/sample-index provenance unenforced, including a negative index. The returned geometries were not claimed to be wrong.

**Bounded proposed repair:** require `type(seed) is int` with signed integers permitted and `type(sample_index) is int` with a nonnegative index before `gen_ctx`. Preserve the established sampling-version salt so this API repair does not unnecessarily change valid seed/index draws. Add focused rejection cases and valid-input golden comparisons.

### Bounded positive evidence and limits

All three supplied canonical inputs passed `self_check`, and the Python diagnostic mirror matched all three provided canonical outputs. Twelve generator calls were checked, yielding seven unique input hashes: difficulty `easy`, `medium`, and `hard`, each with `(seed, sample_index)` equal to `(0,0)`, `(17,1)`, and `(20261023,2)`, plus three exact override corners at seed 17/index 2. Those corners were `(grid_h, grid_w, active_rows, palette_size)` equal to `(4,7,3,4)`, `(8,11,8,9)`, and `(5,9,4,9)`.

All 12 scenes passed `self_check`, agreed with direct row-wise zero removal/right padding, fired all five declared witnesses, and disagreed with all six competitors. Witness and rival calls did not mutate the input. This supports retaining the core teaching geometry and useful rivals while repairing the issues above.

The retained associated notes describe earlier canonical-scale, non-monotone witness, and override work, but their external historical check paths were not available as current executable evidence. The audit did not rerun a broad distribution census, validate every override combination, conduct model evaluation, establish four-query supervision, or execute Racket. Do not upgrade approval or claim universal coverage from these bounded checks.
