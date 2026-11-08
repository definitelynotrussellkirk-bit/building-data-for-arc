# Allocation-quality ticket: ticket-c1f4465e8b29b5d4

**Status: completed. Recommendation: keep the issued allocation and live dataset weights; run a bounded owner pilot before considering a change.** This ticket produced a proposal, not an allocation edit, approval decision or new generator-quality verdict.

## Scope and method

The issued seed `46d0fc6ba2ecb5d90e0b6ff34203b12e8d4941710f6d226aa090c12e44e8c1b8` sampled **0281fbec1cf2, 36275402c6b2 and 8b0844e3951e** with `random.Random(int(seed,16)).sample(sorted(manifest.all_ids),3)`. The one static probe ran in **0.191 seconds**, with zero generator executions, Racket jobs, model calls or census runs. Sources absent from the lean workspace were read directly from the original ZIP. Source hashes, observations and limits are in `report.json` and `probe.json`.

The recorded inspection-to-report interval was **8.05 minutes**, within the ten-minute authoring budget. The probe's raw-catalog approval diagnostic was corrected to read manifest approval: raw catalog rows do not contain the derived `approved` field. Saved script and result agree on 162 approved normal targets. This was a reporting correction, not another probe.

## Actual allocation and weight behavior

The packet has **300 all_ids, 164 main_ids and 162 normal targets**. The issued manifest marks 212/300 records approved and all 162 normal targets approved. The focus decision reserves **10%** for public-evaluation authoring focus. It selects among **120 anchors**; only **one** has related main generators, covering **two** IDs. The other 119 anchors use inspiration on a normal-priority target. Thus the direct-related focus branch is about **0.0833% of all draws** under uniform seeds (`0.10 × 1/120`), while the full focus remains 10%. This is policy arithmetic, not a measured draw frequency. Focus is not training admission.

Catalog weights are **1.0 for 298 raw records and 0.0 for two**. All three sampled records have weight 1.0. Default weighted dataset export independently filters for approval and an available generator, rejects invalid/nonpositive weights, and samples by `mix_weight`; equal weights do not constitute equal quality. Dataset export defaults to **one query**. Explicit four-query support and evidence are needed before claiming it. See the captured `datasets.py`, `cli.py` and `review_full_draw.py` excerpts.

## What the sampled evidence supports

### 0281fbec1cf2 — directional rays, current source 074f2bad…

The source represents independent blocking of a red rectangle's rows and columns by markers. Imported current associated notes describe four exact-public and twelve directional scene profiles, fail-closed validation and removal of textures that hid or trivialized the rule. The concrete retained lint issue is **A012 for the legacy canonical rule!/lambda wrapper**; the note reports exact execution on seven training and one expected-test occurrence and other final gates with zero findings. Raw gate receipts are not retained in this task home, and none was rerun here.

These are input-profile controls around a fixed canonical rule. They do not establish latent rule parameters or four-query identifiability. Review cost must include independent directional blocking and preservation of existing nonzero cells. Current rejection, Racket-time and duplicate rates are unknown.

### 36275402c6b2 — crop and directional legends, current source b65d3ab8…

This record has the richest retained teaching analysis: coupled border/side witnesses, six observable axes and six declared rivals. Notes report 12/12 battery stages, 300 Racket-labelled lessons and 1,200 unambiguous query rotations. The documented assembly is **three demonstrations and one query**; rotations do not establish four-query support. Review-index verification is explicitly `reviewer_reported`.

A retained 126-slot sampler benchmark reports **2.592 s / 21,681,400 peak bytes before** and **0.00210 s / 21,592 bytes after**, with identical selections and RNG continuation. This motivates measuring sampling cost; it does not establish current end-to-end Racket speed. The current notes distinguish an unselected source 14022562 proposal that rejects previously legal negative seeds. Its test claims cannot be attributed to the selected source. The notes also mention a border-policy prototype with **four complete episodes**, not four queries; its referenced proposal manifest and source are absent from this packet's task-home inventory.

### 8b0844e3951e — nonzero mode, current source dd29df3e…

Zero-dominant scenes refute filling with the overall mode/background. Associated notes retain **duplicate-output and constant-color grammar warnings as lawful diagnostics**: repeated solid outputs are canonical and do not prove repeated public challenges. A concrete recorded risk is the different default zero treatment of Racket `mode` and Python `_grid_mode` (WFB-001). That discrepancy was not reproduced here.

The retained tie example is especially useful: an oracle can execute a tied mode using its implementation tie-break, yet demonstrations have not taught that tie rule, so tied nonzero modes are deliberately rejected. Execution success alone is insufficient teaching quality. Small grids may be inexpensive, but this needs measurement and a representation floor.

Across all three inventories, **no executable parametric Python entrypoint or explicit four-query receipt is retained**. Current sources and imported evidence have exact hashes in the report. The sample establishes training/augmented provenance, not ARC-GEN or RE-ARC identity; provenance receives no automatic quality credit.

## One concrete alternative: a shadow pilot within this cohort

Keep the exact **10% focus decision, anchor choice and fallback** unchanged. Keep every target outside this three-record cohort and the cohort's total probability mass unchanged. For non-focus choices that land inside it, compare the current uniform split with **50% uniform exploration plus 50% normalized estimated quality/cost**, capped at 45% per record. Keep catalog `mix_weight`, source approvals and training admission unchanged.

A qualifying unit must have the documented demonstration minimum, exactly four queries, correct source-bound canonical Racket labels, valid inputs, a distinct public challenge identity and demonstrations that refute the relevant declared rivals. Count actual latent-rule parameter coverage separately from input layout controls.

The following is an **illustrative assumption set per 100-attempt bundle**, not measured acceptance or timing. Costs combine reviewer minutes, deduplication-review minutes and Racket CPU minutes at an explicitly chosen 0.25 reviewer-minute equivalent per CPU-minute. The report contains each component.

| Record | Assumed qualified units | Assumed cost, equivalent min | Current conditional share | Alternative conditional share |
|---|---:|---:|---:|---:|
| 0281fbec1cf2 | 55 | 45.0 | 33.3% | 29.2% |
| 36275402c6b2 | 75 | 60.0 | 33.3% | 29.5% |
| 8b0844e3951e | 60 | 25.0 | 33.3% | 41.3% |

Under these assumptions the current ratio is **1.462 quality units per cost-minute** and the alternative is **1.530**, an estimated **4.7% conditional gain**. This is a three-record illustration, not a forecast for the 162-target pool. It is below the proposed 15% adoption threshold and supplies no basis for immediate reweighting. Different true costs or acceptance rates can reverse it.

## Bounded owner test and stopping rule

Pre-register frozen source identities, qualification criteria and cost accounting. Attempt **20 deterministic episodes per sampled record, 60 total**, preserving documented demonstration minima and requesting exactly four queries. Use the same observations to estimate both policies. Record Racket startup separately from execution, and measure validation rejection, label parity, demonstration ambiguity, public-challenge duplicates and actual parameter coverage. Include directional blockers, border/side and signed-seed boundaries, and zero-dominant/tied-mode handling within that finite cohort.

Cap the future pilot at **90 reviewer-minutes, 15 Racket CPU-minutes and 30 machine wallclock minutes**. Stop a record on a wrong label, public/private leakage, changed source binding, or an allegedly identifiable but ambiguous demonstration. Missing four-query or parameter support is an unsupported result; do not silently request one query or lower demonstration requirements. Stop at the first cap without expanding to a census.

Consider owner-controlled adoption only with **at least 15% measured quality/cost improvement**, a paired-bootstrap **95% lower bound above zero**, preserved representation floors and no label/leakage regression. Otherwise retain current allocation and report inconclusive or no improvement. This experiment is proposed and **has not been run**.

## Reproduction and provenance

Run `probe.py` with `--packet` pointing to the original ZIP, `--work` pointing to WORK, and `--out` pointing to a new JSON path; use `python3 -B`, `PYTHONDONTWRITEBYTECODE=1` and TMPDIR under WORK/checks/tmp. The probe never imports generators or starts Racket. The three retained `evidence/associated_notes.jsonl` files were read manually to interpret the captured task inventories; their exact hashes are in `report.json`. Historical filesystem paths quoted inside those records were not opened. No peer source, manifest, baseline, shared code or root report was edited.

## Executed command and bound rules

The single static probe exited **0** with empty stderr. Its actual working directory was `/workspace/scratch/cd86c06020be`. Exact argv and the before/after diagnostic-correction script hashes are retained in `report.json`.

```sh
/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python3 -B /dev/shm/arcpuzzles-cd86c06020be/WORK/checks/tickets/ticket-c1f4465e8b29b5d4/probe.py --packet '/workspace/scratch/cd86c06020be/upload/SEND-THIS-ARCpuzzles-review(2).zip' --work /dev/shm/arcpuzzles-cd86c06020be/WORK --out /dev/shm/arcpuzzles-cd86c06020be/WORK/checks/tickets/ticket-c1f4465e8b29b5d4/probe.json
```

| Sampled record | Current source SHA-256 | Canonical rule hash |
|---|---|---|
| 0281fbec1cf2 | 074f2bad074d925d9b39b7e71a7c743031c47406a85c4893e7020de521c55bc9 | 0c0061f8ed33 |
| 36275402c6b2 | b65d3ab83f95f86f64fee72b91222edf31101a70fb7e1770acaf67b5befc0c58 | 08894540e7f2 |
| 8b0844e3951e | dd29df3ec18cda8c98a1ba1f165a0b013e2e2f4519d4eb10750f528b283af5f2 | b2abbd0be28f |

Pinned ticket identity: `a2d9d069c7d5`, source `a9bfd8dc636a8ed242ce89c21f4fa6a977c809a5672f637891f5e1d684824e29`, rule `e2513b1ebd3d`.
