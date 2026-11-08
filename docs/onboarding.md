# Teammate pickup

Start here for current navigation; the
[September 11 pickup](SESSION_STATE.md) records historical migration work.
ARCpuzzles owns generators, reference rules, review evidence, and hashed dataset
exports. [ARC2HQ](https://github.com/definitelynotrussellkirk-bit/ARC2HQ/blob/main/README.md)
owns the shared plan; ARC2train owns rollout archives and learner admission;
ARC2kaggle owns competition notebooks. Work in the repo that owns your task.

## Resume owner review intake

The saved checkpoint has **941 native-accepted parametric families / 2,174 rule
settings**, and **1,984 effectively approved base generators / 4,061 total**.
These are source-acceptance counts, not a verified count of generators currently
feeding training. Read the [accepted-family index](../REVIEW/parametric-families-current.json)
and [current packet record](../REVIEW/full-packet-current.json) for updated counts,
source identities and verification limits; rerun `arcpuzzles stats` for live base
approval counts. The checkpoint source/evidence is pushed at
[`8d91eb358`](https://github.com/definitelynotrussellkirk-bit/ARCpuzzles/commit/8d91eb35837247e9e983a3f34c6beca150a18009).

The sendable file is `var/review/SEND-THIS-ARCpuzzles-review.zip`. A clone can
retrieve the same hash-bound artifact, checksums and source identity from the
[saved private release](https://github.com/definitelynotrussellkirk-bit/ARCpuzzles/releases/tag/review-packet-20261026-a1204407);
the [latest release](https://github.com/definitelynotrussellkirk-bit/ARCpuzzles/releases/latest)
may be newer. Fast source closure/content hashes and the remote asset digest
were verified. Historical-evidence validation and cold-runtime replay remain
pending; trainer reload/activation was not verified.

Resume in this order:

1. Check `git status`, read [AGENTS.md](../AGENTS.md) and the
   [current review workflow](../REVIEW/README.md#one-parametric-build-with-deep-adversarial-self-review--current-trial),
   and preserve unrelated work. Current packets draw **one unapproved base from
   a rotating 500-target subset** for one complete parametric build with deep
   adversarial self-review. No peer audits, second build or solves are assigned.
   Require meaningful input-dependent sequential composition, a teachable family
   minimum within 2–6 demonstrations, and four distinct queries privately
   randomized and shown one at a time without future-query or total-count hints.
2. For new ZIPs, copy the supplied files into a new ignored intake directory;
   preserve Downloads originals and old packet caches needed by in-flight returns.
   Run `PYTHONPATH=src .venv/bin/python -m arcpuzzles review collect INCOMING_DIR`.
   Read each short repair summary and feedback, compare source bindings and
   existing acceptance, then use `review integrate ASSIGNMENT --version N
   --reviewer-reported` with the actual accepted components (`tests_notes`, plus
   `generator` or `racket` only when accepting those changes). Ordinary intake
   remains about one minute per ZIP; investigate concrete conflicts rather than
   rerunning broad reviewer batteries. Preserve reported checks as reported.
3. Require actual current-source native qualification, protected causal replay
   and fresh acceptance before counting a new family. Inspect every
   `parametric_admissions` row and `objective_met`; reviewer `ready`/`prototype`
   status is not acceptance. Keep semantic vetoes and unresolved audits explicit.
   The four latest returns are complete in local
   `var/review/intake-20261026ac/progress.json`; task-owned acceptance, notes and
   retained evidence are the durable records.
4. Retain current task evidence and refresh the accepted-family index and packet
   counts once per intake group, then commit/push the scoped source and approvals.
   Local convenience scripts are `var/review/retain-current-intake.py` and
   `var/review/stage-current-intake.py`, each taking an intake directory containing
   `sources.json` and `progress.json`. They are ignored local helpers, absent from
   a fresh clone; the supported workflow is in [REVIEW/README.md](../REVIEW/README.md).
   Managed archive disposal still requires the [retention gate](placement.md#generator-notes-and-review-retention);
   do not rerun global compaction for every arrival.
5. Publish workflow changes **before further intake**. Use the fast build below,
   replace the sendable file immediately, and publish its exact source/hash-bound
   private release. Do not wait for historical or cold verification. New-family
   qualification/acceptance gates remain unchanged. Local
   `var/review/publish-fast-artifact.py BUILD_RECEIPT` publishes and verifies the
   remote asset; inspect its release tag/date before reusing it later. Update
   `REVIEW/full-packet-current.json` with the actual publication identity and push
   that pointer too. A documentation-only handoff edit needs no packet rebuild.

```bash
PYTHONPATH=src .venv/bin/python -m arcpuzzles review pack-full --fast \
  --racket-archive var/review/racket-minimal-8.10-x86_64-linux-cs.tgz \
  --out var/review/SEND-THIS-ARCpuzzles-review.zip
```

Three ordinary overlap proposals await the next **five-case Astra reconciliation**:
[`9aed2df94248`](../generators/9aed2df94248/workspace/proposals/review-36c37a1bf2ee7ee3/decision.json),
[`e6cf1120a17d`](../generators/e6cf1120a17d/workspace/proposals/review-691233545f793e4f/decision.json),
and [`8a851bf5cdd7`](../generators/8a851bf5cdd7/workspace/proposals/review-f37a3de5a3dfe30b/decision.json).
Keep incumbent accepted programs and sampler coverage until a reconciled
replacement qualifies. Prefer disjoint episode-level branches for complementary
rules. The separate
[`3fb5ef8ad60e` grammar conflict](../generators/3fb5ef8ad60e/workspace/proposals/review-abc25c186f3648f3/decision.json)
is retained explicitly; it is not an unattempted ordinary merge.

The [maintenance counter](../REVIEW/packet-maintenance.json) is **5 / 25** at this
checkpoint, so no new maintenance pass is due. Run
`PYTHONPATH=src .venv/bin/python -m arcpuzzles.review_maintenance status` before
acting. At 25 distinct validated returns, use its `start` checkpoint, have Astra
address worthwhile current friction requests, verify the applied changes, and
bind the outcome with `complete`; later arrivals remain in the next count.
[REVIEW/suggestions.json](../REVIEW/suggestions.json) owns the current requests.

Keep the current admission/runtime freeze: do not change
`src/arcpuzzles/{parametric_promotion,parametric_worker,parametric_priority,catalog,runtime}.py`,
`shared/runtime/**`, or `shared/tools/comment_solutions.py` as an intake workaround.
This lane owns data curation; training mixtures, model jobs and checkpoints stay
with the trainer. The append-only coordination channel is
[ARC2HQ/TRAINING-FEEDBACK.md](https://github.com/definitelynotrussellkirk-bit/ARC2HQ/blob/main/TRAINING-FEEDBACK.md)
(locally `/home/user/Desktop/ARC2HQ/TRAINING-FEEDBACK.md`). Use it when dataset
consumption needs checking; source acceptance alone does not prove the trainer
has loaded the new families.

## Read without starting work

Read [AGENTS.md](../AGENTS.md), [placement](placement.md), and the
[review workflow](../REVIEW/README.md). From a fresh clone, Python 3.12+ is enough
for these queries; no environment installation or Racket is required:

```bash
python3 --version
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m arcpuzzles stats
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m arcpuzzles list --approved --limit 5
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m arcpuzzles review list
```

These commands read catalog/source identity and assignment metadata without
importing generators or claiming a task. Rerun `arcpuzzles stats` for current
generator and approval counts rather than relying on an older snapshot. The
October 3 owner policy automatically approves accepted, source-bound reviews.
Follow [installation](../README.md#install-and-start) before generation or checks.
`show ID` is an authoring view containing reference answers/programs; use the
documented challenge projection for model-visible inputs.

## Authority and evidence

Edit the selected `generators/<id>/generator.py`, with that task's notes, tests,
and evidence. Workspace drafts are proposals. Canonical Racket programs live in
`shared/data/canonical/puzzles.jsonl`; archival authority mappings live in
`catalog/authority_files.json`. Prose and Python mirrors do not replace the
selected executable rule. See [placement](placement.md) before changing authority.

| Recorded state | What it establishes |
| --- | --- |
| Return retained / audit reported | Source-bound evidence or a lead to investigate |
| Candidate check passed | The recorded checks passed for that candidate and source |
| Component integrated | The owner selected those source changes; inspect the integration receipt |
| Effectively approved | The current source/rule and recorded safety evidence satisfy [every approval condition](../README.md#query-with-flags) |

An accepted full-packet repair is its safety review under the October 3 owner
policy. Integration automatically records `reviewed_safe`, current source/rule
hashes and a compact current approval record; a complete review of an unchanged
generator can also approve it. `review approve --all-integrated` recovers older
or interrupted approvals without rerunning reviewer code. Preserve the reported
evidence basis and limitations; later source changes revoke approval, and
adversarial findings can reopen it. Generator approval does not admit model
trajectories to training. See [the review policy](../REVIEW/README.md).

## Bounded work leads

Pick one with the owner. These are evidence-backed follow-ups, not newly verified
fixes or authorization to launch compute. Check current source hashes first.

| Next contribution | Evidence and completion target |
| --- | --- |
| Reproduce an unresolved generator audit | Run `PYTHONPATH=src python3 -m arcpuzzles list --audit-unresolved --limit 10 --format json`. Open that ID's `notes.md`, `evidence/review_index.json` and referenced `counterexamples/`. Compare the finding's source hash to current code, reproduce its witness, then propose a bounded repair. Acceptance or a source edit does not clear the flag; resolve it explicitly with evidence. |
| Improve a shared review tool | Open [REVIEW/suggestions.json](../REVIEW/suggestions.json). Each request has a stable ID, current status, source and reason; linked prototype assets are proposals. Agree one request, demonstrate the issue on current source, add a focused regression and update its current status. |
| Check actual lesson teaching | Read a generator's `notes.md` and declared lesson policy before assembling a dataset. Compare the actual demonstration/query layout with its witnesses and rivals; keep ordered-production and rotated-query verdicts separate. The [lesson census guide](../REVIEW/README.md) explains exact replay and finite-rival limits. A source battery does not certify a differently assembled lesson. |
| Review unresolved lineage | The [September 26 supply snapshot](arc2-qwen9-puzzle-supply-20260926.md#review-queue-behind-the-approved-pool) identifies candidate `d6607fc42bcc` and failing rule `deb310c21d0c`; finite original-example fit did not verify lineage. Use the tracked [lineage map](../shared/data/derived/official_generator_lineage.jsonl) and obtain the pinned local receipts before reproducing or promoting a mapping. Its cohort counts and hashes are historical. |

## Coordinate ownership first

`review list` reads the owner checkout's current preassigned review records.
Confirm the owner of any active assignment before overlapping work. An old date
does not release a claim. Teammates coordinate through ProjectBus/Arcy; Git
remains source authority, and a ticket does not authorize compute or admission.

The operator's `review pick` excludes active/preparing tasks in the **same
REVIEW root**. Separate clones do not share that lock. Full-library ZIP copies
draw independently and can collide. Agree the task ID, current source hash,
assignment/branch, and owner before editing; read its single `notes.md` and
current `evidence/review_index.json`. Keep colliding returns through triage and use the review guide's
comparison/recheck route. Record completion or deferral in the existing task
record so the next teammate can pick it up.

## What a clone lacks

[.gitignore](../.gitignore) excludes `var/`, environments, build output, request
workspaces/baselines, and incoming ZIPs. Git retains source, current task-owned
notes/audits, shared requests and compact approvals; the raw returns, candidate copies,
check logs, derived inventories, datasets, and sendable packet are local artifacts.

Ask the owner for the artifact named by its receipt and verify its hash. The
[packet handoff](../REVIEW/full-packet-current.json) pins the current sendable ZIP
and build/smoke receipts; `ready_to_send` does not put those bytes in a clone.
Use the [review guide](../REVIEW/README.md) for retrieval/rebuild requirements.
Rebuilding with changed bound sources produces a new packet identity; preserve old
packet caches for in-flight returns. September 26 source-bound cohorts also need
rebuilding after bound sources change. Keep model-visible challenges separate
from private labels and reference programs.
