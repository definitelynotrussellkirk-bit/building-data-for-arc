# Focused repository migration

Develop puzzles, training and model candidates in independent repositories while
preserving ARCagi2 and its running jobs. Each maintained workflow has local code,
declared dependencies and explicit artifacts. Older inactive experiments stay in ARCagi2 until the user asks to import them;
see [deferred imports](deferred-imports.md).

| Owner | Workflow | Verified state |
|---|---|---|
| ARCpuzzles | Generator homes, queries, shared checks, review workspaces, HTTP | Independent source/wheel interfaces implemented |
| ARCpuzzles | Mixed data, grids/code, DSL, mutations, execution traces, native JSON/tensors | Eight bounded export styles, public/private separation;53 local and isolated tests pass |
| ARCpuzzles | Generation compatibility | Full v0.3 one-seed census complete; all449 approved match;30 exceptions classified and specific v0.5 fixes checked |
| ARC2train | Qwen3.5-9B rank128 program RL, Pi/Docker, private verifier, durable async workers | CPU implementation and fixed candidate export verified; real hardware rehearsal pending |
| ARC2train | Qwen27 trainer/compiler/restore/evaluation, panel preparation/native capture/stats | Core0.5:361tests/3subtests pass in fresh isolated install |
| ARC2train | Qwen27 remote collection/baseline, full SFT admission/preflight and artifact import | Independent;577-file campaign verified and64 rule authorities rebuilt identically; saved incomplete collection rejected |
| ARC2model | Candidate import, independent Pi/Docker inference, sampler and daily workflow |233tests/15subtests pass in isolation; real candidate quality remains unmeasured |
| ARCagi2 | Older model/notebook/custom-model experiments | Import deferred until requested |
| ARCagi2 | Older training/platform families, including DSL/TPU | Import deferred until requested |
| ARCagi2 | Older Kaggle generator service | Import deferred; current ARCpuzzles entry is local export/API |

[Notebook ownership](migration/notebook-ownership.json) inventories45 predecessor
notebook directories. The maintained sampler is in ARC2model; the other44 remain
in ARCagi2 until their import is requested. This inventory makes no claim about
live job status. Earlier archive copies were moved into recovery-only storage
outside the new repos; original sources were not moved or deleted.

The selected new experiment follows Thinking Machines' published method using
Qwen3.5-9B rank128/alpha32 LoRA and Transformers/PEFT on the user's4090 + Spark.
No Unsloth or SFT warm-up. Existing occupied GPU services remain untouched while
a previously asked resource decision is pending. No GPU training has started.

Runtime sharing uses pinned local distributions or immutable artifacts. ARC2train
intentionally retains ARCpuzzles0.2.0 and exports an ARC2model runtime wheel as
artifact bytes, never a training import. A tiny CPU adapter has crossed from
training into model-owned storage and run through its independent Pi/Docker
inference runtime. This proves the exercised handoff, not real Qwen quality.

Relocation uses normal wheel installs and Landlock denial of /home reads, inherited
by subprocesses. Tests and copied historical receipts retain their actual scope.
No sibling imports, source symlinks or borrowed environments are supported.

The maintained repository split is ready for ongoing work. Training collection
and admission now have independent code and fixed artifact interfaces. Older
non-selected launchers remain in ARCagi2 until requested. Future real model training,
quality evaluation and manual competition handoff are separate measured steps.
This work does not stop existing jobs, activate watchdogs or submit a competition.

The full12-stage shared battery ran on one generator in the isolated puzzle repo:
seven green, two advisory, three failed. Rule-text divergence, palette/profile
support and missing semantic-contract findings are retained in
[the battery receipt](migration/battery-evidence/receipt.json). Portability is
verified for those tools; generator quality was not upgraded by the migration.
