# Historical migration pickup — 2026-09-11

This is the September 11 migration snapshot. Its uncommitted-change statements,
job observations, and next-training notes describe that date, not current Git or
run state. Start with [teammate pickup](onboarding.md) and the
[review guide](../REVIEW/README.md) for maintained puzzle work; cross-project
direction lives in [HQ strategy](https://github.com/definitelynotrussellkirk-bit/ARC2HQ/blob/main/STRATEGY.md).

The focused-repository split is verified for maintained work. Preserve ARCagi2
and its existing jobs. Selected new training: Qwen3.5-9B rank128/alpha32 LoRA, Transformers/PEFT,
Thinking Machines' published method on the user's4090 + Spark, no Unsloth or SFT
warm-up. No subagents authorized. Extraction changes remain uncommitted.

## ARCpuzzles complete work

Version0.5.0 normal wheel: `dist/arcpuzzles-0.5.0-py3-none-any.whl`, SHA256
`9b060fcb3080812053ee9fc6df5386079536bada46c5376fe535b663095155c7`.
All53 tests pass locally (83.94s) and in a fresh wheel installation (84.61s)
at `/tmp/arcpuzzles-v05-isolated-h2fhedwl`, with Landlock denying /home reads.
CPU Torch2.14.0/safetensors0.8.0; pip check passed. Evidence:
`docs/migration/v05-evidence/receipt.json`. Final documentation/receipts postdate
the wheel build; executed API sources are unchanged and hash-bound in that receipt.

CLI/Python query, generation, checks, review workspaces and read-only HTTP are
independent. Eight export styles include native JSON/private safetensors, all query
slots and explicit input/label separation. JSON-only works without Torch (v0.4
isolated proof retained). Requested native difficulty is preserved in v0.5.
Oversized grids fail rather than crop. Incomplete exports remain rejected.

Explicit `--reference archival --allow-unapproved` retains access to older rules.
Actual executed and catalog rule hashes are separate. Archival execution is always
unapproved; unsafe stays unsafe. Self-checks/identity/duplicate admission remain.
Four historical pair hashes and two self-check cases pass regression tests.
Bare expressions from generic_gather_gen1/2/3 are now wrapped as equivalent rules;
emitted bytes and normalization are recorded. All three pass Racket verification
at seeds0/easy,17/medium,42/hard. No generator source or safety label changed.

## Completed census

The full v0.3 census is TERMINAL, not running. All3941 generators attempted at
seed17/medium/one train+one test:3911 equal,21 current-only,2 historical-only,
4 different,3 both-failed. All449 approved matched. Every exception is classified
in `docs/migration/census-classification.md`; immutable output/worker/wheel hashes
are in `docs/migration/census-evidence/`. v0.5 targeted tests supplement it; there
was no second full census. Old progress snapshots are historical, not live state.

Twenty current-only generics emit task-local programs; the old runner demanded a
module PROGRAM. deb310c21d0c's archival rule emits rejected identity pairs.
The three both-failed cases were the bare expressions now supported. Two missing/
failing canonical authorities remain explicit unapproved archival research;
two authority changes and two self-check sample rejections explain differences.

The old Kaggle generator service and inactive experiments remain in ARCagi2
until explicitly requested. Prior archive copies were moved out of the new repos;
see docs/deferred-imports.md. The45-notebook inventory records current or deferred ownership in
`docs/migration/notebook-ownership.json`.

## Full shared-tool baseline

All12 stages ran on6c68e1b008a5 under source-read denial:7 green,2 advisory,
3 failed, no timeout or missing dependencies. Active rule texts differ while
sampled execution agrees; palette4..6 misses canonical7, profile/envelope support
is0/60, and semantic contract is absent. No generator source or approval changed.
Evidence: docs/migration/battery-evidence/receipt.json. Generator notes retain
these limitations. This is not a clean quality result or a whole-corpus battery.

## Adjacent work and next training steps

ARC2train intentionally keeps its pinned ARCpuzzles0.2.0 wheel. Its new9B program
RL controller/learner and fixed candidate export are CPU tested; no actual9B
hardware rehearsal yet. The unanswered resource question about occupied Qwen3.8
servers remains pending; do not stop them or treat elapsed time as approval.

Historical ARC2train core0.5:27modules,84source imports,361tests/3subtests pass in
fresh isolated wheel. Remote collection/baseline, full admission/preflight and
artifact import are included. Real577-file campaign copied and verified;64 rule
authorities rebuilt identically from pinned puzzle0.2 under source-read denial.
Its saved incomplete collection is rejected; no real model run. Older inactive
training/platform families remain in ARCagi2 until explicitly requested.

ARC2model candidate/Pi-Docker/sampler/daily workflow passed233tests/15subtests in
isolation. Older inactive model/notebook families remain in ARCagi2 until their
import is requested. Maintained routes still need real model
quality evidence. No real candidate promoted or notebook pushed/submitted.

Maintained workflows now use local code and explicit artifacts. Next work is
real9B capacity, actor/learner parity, LoRA reload, async rehearsal and evaluation
after hardware allocation. Do not repeat completed migration censuses or expand
archives automatically. Repository changes remain uncommitted.
