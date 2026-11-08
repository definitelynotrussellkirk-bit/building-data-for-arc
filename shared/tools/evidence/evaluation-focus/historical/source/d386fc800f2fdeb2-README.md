# Generator review ZIP workflow

Processed reviews retain **current task state, not a cumulative historical ledger**.
After triage, use `arcpuzzles review compact` to preview, then `--apply` for verified
extraction and managed cleanup. Keep current decisions in generator `notes.md`,
actionable audits and counterexamples with their target, compact exact-source
approvals, and useful authored solve data. `REVIEW/suggestions.json` is the current
shared tool-request list. Managed return ZIPs/expansions and redundant historical
records are removed only after the archive-independent retention checks pass.
See [placement and retention](../docs/placement.md#generator-notes-and-review-retention).

**Routine intake produces machine receipts and task records, not another batch
summary Markdown file.** Preserve the reviewer's useful findings/notes in its
workspace and task index. Update an existing pickup page only for a changed
next action or workflow. Do not write narrative transport summaries in ARC2train
or matching status summaries in HQ.

Extract the packet normally into a new folder and run `python3 review.py verify`,
then `start` and `duties`. Disk/memory capacity preflight was removed from the
review distribution at the owner's request. For restarting an interrupted draw,
use the [workspace recovery notes](../docs/reviewer-check-resume.md#resource-preflight-and-exact-assignment-recovery).

## Maintainer default — lightweight acceptance

Owner direction, October 3: **about one minute per ordinary return**, up to ten
minutes for a substantial upgrade. Read the short `REVIEW.md` opening and
`FEEDBACK_TO_CODEX.md`, accept ordinary repairs, and consider feedback for larger
changes. Extract useful current notes, witnesses, audits and shared requests; then dispose the processed transport.

```bash
PYTHONPATH=src python3 -m arcpuzzles review collect /path/to/new-returns
PYTHONPATH=src python3 -m arcpuzzles review integrate review-ASSIGNMENT_ID --version 1 \
  --reviewer-reported --component generator --component tests_notes
```

Select `--component racket` only when accepting a returned rule/authority change.
The lightweight path applies only changed files from the hash-bound baseline,
checks scope and collisions, and records `verification_status=reviewer_reported`.
It does not execute reviewer programs or claim independent verification. Run
additional checks only to resolve a concrete issue. Refresh indexes and the one
sendable ZIP once per batch. The longer checked workflow below remains optional.

### Approval follows an accepted repair

October 3 owner clarification: **getting reviewed and repaired makes a generator
safe**. Accepting a full-packet generator or rule repair now automatically
records its safety review and pins the exact live generator/rule hashes. There
is no second routine battery or certification queue. Keep reported checks,
failures, limitations and evidence basis; an approval does not claim a new
maintainer run or universal coverage. Random audits can expose later defects.

```bash
# Recover an interrupted approval step, or backfill older accepted repairs:
PYTHONPATH=src python3 -m arcpuzzles review approve --all-integrated
# Or finalize a particular accepted revision:
PYTHONPATH=src python3 -m arcpuzzles review approve review-ASSIGNMENT_ID --version 1
```

The command is idempotent and executes no submitted code. It skips superseded
source revisions, partial component selections and missing/changed rule bindings.
A complete review that finds the original generator correct and returns only
regressions/notes can also approve its unchanged, bound source. Existing
semantic vetoes remain active. Compact `REVIEW/approvals/` records retain the selected source/rule hashes and
verification basis. Superseded approval narratives and previous catalog records
are not retained in the working tree. Model trajectory admission remains separate.

## Replay an exact return in a fresh checkout

`review replay-return` verifies the original packet inventory and return,
extracts a new checkout, checks the exact Git root and complete patch inventory,
applies the delta, and compares every changed file with the reviewed WORK tree.
Use absolute paths when invoking it through the packet wrapper:

```bash
python3 -m arcpuzzles review replay-return \
  --source-zip /path/original-request.zip --return-zip /path/review_response.zip \
  --compare-work /path/review/WORK --out /path/new-replay --runtime-closure
```

The default extracts the complete original packet. `--runtime-closure` instead
extracts the selected task and declared runtime/API dependencies; the receipt
explicitly records this partial scope and both file counts. Existing output
directories and symlink paths are refused. Inputs and the reviewed WORK tree
are read only. Git and Python 3.12+ are required; extraction needs no installed
Racket or third-party Python packages.

`replay.json` and its compressed extraction inventory retain exact hashes and
commands. Success is `patch_replay_passed_tests_pending`: the command executes
neither returned programs nor tests and grants no approval. Run the selected
portable task tests from the fresh checkout using its own environment and
reference runtime, and retain that separate result. Routine maintainer intake
continues to use the lightweight acceptance policy above.

## Reusable full-library packet for parallel reviewers

For a wave of generator reviewers, build the generator packet once and
send the **same ZIP** to each reviewer:

| Review purpose | Stable local ZIP | Owner guide |
|---|---|---|
| Generator repair, Python solve and generator audits | [SEND-THIS-ARCpuzzles-review.zip](../var/review/SEND-THIS-ARCpuzzles-review.zip) | This guide |
| ARC2 collection, serving, capture and distillation process | [SEND-THIS-ARC2-loop-review.zip](../var/review/SEND-THIS-ARC2-loop-review.zip) | [ARC2train harness review](https://github.com/definitelynotrussellkirk-bit/ARC2train/blob/main/docs/harness-review.md) |
| Riri's CPU action-mask/token/length validation | [SEND-THIS-Flash-Qwen9-validation.zip](../var/review/SEND-THIS-Flash-Qwen9-validation.zip) | [English-first guide, then Chinese](https://github.com/definitelynotrussellkirk-bit/ARC2train/blob/main/docs/teammate-validation.md) |

Each purpose has one canonical sendable ZIP. The local generator
[handoff record](full-packet-current.json) gives its current size, SHA-256,
packet identity, current findings and fresh pending work.

New return ZIPs contain an automatically
generated `INTAKE.json`: changed components, feedback paragraphs, audit targets,
solve metadata, exact commands with working directories, and evidence hashes.
The validator derives this index again from the retained source; its claims are
reviewer-reported until maintainer checks. Reviewers follow `RETURN-GUIDE.md` and
edit the starter `RESULTS.json` produced by their draw.

A fresh Git clone has the handoff metadata, but not this ignored ZIP, its
build/check receipts, original returned ZIPs, or the optional Racket archive.
Ask the owner for the pinned packet and matching artifacts, then verify the
handoff hash. A rebuild uses current source and may produce a different packet
identity; it does not retrieve an older cached packet. See
[teammate pickup](../docs/onboarding.md) for ownership and current work leads.

After integrating returns, refresh the review indexes before building the next packet:

```bash
PYTHONPATH=src python3 -m arcpuzzles review inbox
build_dir=$(mktemp -d var/review/build-XXXXXXXX)
PYTHONPATH=src python3 -m arcpuzzles review pack-full \
  --blind-solve \
  --out "$build_dir/request.zip" \
  --racket-archive var/review/racket-minimal-8.10-x86_64-linux-cs.tgz
```

Use a fresh build directory each time; an existing packet at the output path
cannot be overwritten with a different identity. Verify the cached packet's ZIP,
included indexes, and a fresh main/audit draw,
then replace `SEND-THIS-ARCpuzzles-review.zip` in place and update
`full-packet-current.json`. Remove the temporary build after verifying its
content matches the cached packet. Keep a source packet only while it has outstanding reviewers. After verified
extraction, retain the minimal source/rule bytes needed by an open finding or
a useful authored example; retire obsolete full-library caches. The generator packet keeps its single stable `SEND-THIS` filename.

### Finish a review, then dispose its transport

Run `arcpuzzles review compact` after integration, feedback triage and audit
selection. Preview changes nothing. `--apply` checks archive hashes, retained
witnesses, current approvals, authored data and an archive-independent inbox/feed
before removing managed return copies, expansions and assignment ledgers.
Incoming audits are read directly from validated returns; a prior inbox refresh
is not required to retain their findings and referenced evidence. Explicit audit
dispositions remain in force.
Inbox/feed rebuilding, metadata migration, packet building and compaction share
the project's review lock with intake, integration, approval and audit decisions.
Nested calls in the same thread reuse it; other threads and processes wait before
reading or changing review state. Packet building reloads the catalog after
acquiring the lock. This does not coordinate manual edits or another project.
Integration keeps the lock through its automatic source-bound approval, so
compaction cannot retire the return between those two steps.
Unknown members or missing evidence block disposal. Original Downloads are outside
this command. Use the generator's notes, active audit index and current shared
request list for future work; processed ZIPs are not a project history database.

```bash
PYTHONPATH=src python3 -m arcpuzzles review compact
PYTHONPATH=src python3 -m arcpuzzles review compact --apply
```

The packet also includes `ARC-DESIGN.md`: concise paper guidance and optional
source-bound curriculum annotations for interacting rules, sequential state,
contextual gating and task-defined symbols. Reviewer `RESULTS.json.curriculum`
travels through intake and task records into manifest-hashed `curriculum.jsonl`
in the solve feed. Missing annotations mean unknown, changed bytes mean stale,
and all observations remain reviewer-reported; no extra intake gate or training
admission is implied. Single-operation tasks remain valid.

The packet contains all cataloged generators, notes, workspaces, canonical
rules, current questions and review tools. It also includes prior task-local
decision and audit indexes. The optional pinned Racket tarball adds a rootless,
offline Linux x86_64 runtime; its SHA-256 is checked against the official 8.10
release before packaging and unpacking.

New CLI packets open with only `START-HERE.md`, `review.py`, and `WORK/`.
Each reviewer runs `python3 review.py verify`, `python3 review.py start`, and
`python3 review.py duties` from that outer folder. `python3 review.py status`
prints the current lane map. The complete existing workspace is inside `WORK/`,
including its single `repo/` source copy. Blind-first directions hide the repair
navigation until the blind solve has a recorded finish. Reports, check evidence,
contracts and the small return ZIP stay inside `WORK/`. `WORK/WELCOME.md` and
`WORK/RETURN-GUIDE.md` remain detailed references; their older helper commands
work from inside `WORK/`. The manifest hashes workspace files relative to `WORK/`
and binds both outer entry files in `layout.entry_files`. Collection, candidate
checking and integration support both layouts and retain the existing return schema.

The main draw is seeded within the current priority tier and requires an
unambiguous canonical rule. Original-family parameterization comes first,
including already approved families whose parametric extension is missing.
New packets first draw a separate approved task for a Python solve before any
repair/reference work. Reviewers run `python3 review.py blind prepare/check/finish`,
record prior exposure honestly, and leave that task unchanged if preparation is
blocked. This is a self-reported unexposed attempt: references are in the library,
so the packet cannot enforce isolation. The usual post-repair solve remains
separate. Both kinds transport programs, work logs, instance/generator hashes
and exposure metadata into the reviewer feed; neither is automatically admitted.

Full-packet main assignments now prioritize families traced to the supplied original 1,120
ARC tasks. Approved original families without current parametric evidence come
first, followed by original families needing repair and parameterization, then
other unapproved generators. This can assign an already approved generator for
parametric authoring. Exact public-challenge matches and reviewed, challenge-bound
lineage establish ancestry; they do not refresh safety or training lineage.
Inspect the current source-bound queue with
`arcpuzzles review parametric-priority --out var/review/parametric-priority.json`.
The full-packet manifest pins this queue and keeps seeded draws reproducible.

New packets reserve a **10% chance per fresh assignment** for an explicit focus
on one of the 120 supplied public-evaluation tasks. Choose a public parent
uniformly, then prioritize parameterization of its eligible related generators.
If none exists, the normal priority target receives that public task as
inspiration for a separate proposed extension. The other branch retains the
original-family priority above. The source-bound policy, parent/hash and direct
or inspired mode are recorded in the manifest/assignment; collection reproduces
both the target and focus. Existing packets and reopened assignments retain
their original draw. This is authoring frequency, not a dataset mixing quota.
See the packet's `ARC-DESIGN.md` for the paper's evaluation-difficulty rationale,
representative reasoning expectations and the limits of synthetic variants.

After the blind solve, reviewers also assess one or two small rule parameters
using the packet's `PARAMETRIC-RULES.md`: where suitable, return a runnable
task-local prototype with matching Racket, episode-consistent parameters and
evidence that the demonstrations distinguish the chosen behavior. Otherwise
explain why it is not suitable. For original-family assignments, develop that
extension first and preserve the task's object roles and core reasoning. A
parameter inferred from demonstrations need not appear explicitly in the input.
Prototypes live in the assigned task's
`workspace/parametric/`; the current fixed canonical production path and variant
approval remain separate.

For future generator updates, aim to support four query/test inputs per episode,
independently of the demonstration count needed to identify the rule. The
production CLI already accepts `--test 4`; prototypes should expose separate
demo/query counts and retain a four-query episode for each demonstrated setting.
Use distinct lawful inputs under one episode rule/parameter setting, derive all
labels through matching Racket, and check every query against the demonstrations
alone. Report concrete limits instead of cloning pairs or silently truncating.
See the packet's `ARC-DESIGN.md` for the exact command. Global defaults and the
one-query rotation diagnostic remain unchanged; this is a reviewer authoring
request, not a new blanket intake gate or training-quality claim.

`python3 review.py audit` draws two distinct targets independently from the
library, including approved and previously reviewed ones, excluding this draw's
blind solve target. The return records
one `AUDIT.md` section per target and the inbox indexes each finding separately.
Eight offline draws can
occasionally collide; keep both returns and compare them.
The generated duties use `--phase before` for the baseline and `--phase after`
for the revised generator. Use `--phase audit` with the exact drawn peer target
for optional isolated audit checks, for example:

```bash
python3 run_with_racket.py python3 -m arcpuzzles check AUDIT_ID \
  --stage task_tests --phase audit --out ../checks/audit/AUDIT_ID-task-tests
```

`audit` is recorded in `result.json`, battery summaries and phase-specific
stage filenames. It uses the same strict battery policy as `after`, and works
with `check-run start --phase audit` too. Resume inherits the saved phase and
rejects relabeling audit evidence as repair verification. Checks copy the
selected source into an isolated runtime; they do not approve generators or
close audit findings. Record your conclusion separately in `AUDIT.md`.
The output directory name does not select a policy.
Full API/CLI batteries collect all twelve stages in both phases, retain failures,
and return a failing aggregate exit code. CLI checks stream progress to stderr
while the complete output stays in the check receipt. Single-stage runs keep
their original policy.

Reviewers can run `arcpuzzles lesson-census ID` through `run_with_racket.py` to
retain source-bound production lessons, replay seeds, unique-input counts and
declared-rival ambiguity results. `--rotate-query` also holds out every labelled
pair once (one query only), retaining indices and separate rotation counts without
another authority/generation run. It checkpoints partial progress and does not
replace exhaustive cyclic-window or joint-axis probes. Portable canonical-data
helpers are described in [shared tools](../shared/README.md); those authoring
helpers expose answers and must remain closed during visible-only solves.
This is a shared reviewer tool, not a new routine intake gate.
Each census CLI run writes the full `--out` report and a sibling `.summary.json`
companion with its exact hash, source bindings, verdict, all failure/warning
recipes and first exact rival witnesses. Both output paths must be new. The
companion is concise reviewer feedback, with authoring labels; use the full
report for rescore or schedule-receipt validation. Original reports stay intact.
See [compact evidence](../shared/tools/README.md#compact-lesson-census-evidence).

For a large census, add `--gzip --out ../checks/census.json`: the complete report
is written as `census.json.gz`, with `census.compression.json` and the compact
companion. Cite `checks/census.compression.json` in your review to retain its
compressed payload. Restore a copy in a new directory and verify its manifest
hash before supplying the full JSON to rescore or a schedule check. Gzip mode
preserves the report and exit verdict; it does not turn failures into passes.

After editing only the rival definitions, optional `--rescore saved-census.json`
rechecks every single-pair query holdout using the retained inputs and labels.
It binds the saved input source separately from the current rival source; it
does not generate or relabel examples. See the shared-tools guide for limits.

`check --stage task_tests` collects each generator-local source once even when
it is mirrored into the legacy runtime `tests/` directory. Mirrors remain
available for imports. `runtime_manifest.task_test_collection` records selected
roots and omitted mirrors; distinct legacy sources are still collected. Report
JUnit test cases separately from unique test functions and retain skip counts.
Historical double-collected receipts keep their original counts.

`check --stage task_tests` now retains JUnit evidence and structured test counts,
and checks recognizable portable-path problems before pytest. Available legacy
`scripts.*` imports still work in the staged runtime and produce warnings.
Known missing staged modules/private symbols and recognizable unguarded reads
of missing canonical files stop with `test_status: preflight_failed` and an
actionable `reviewer_support` alternative. Guarded, reassigned, fallback and
dynamic paths remain warnings for normal Python evaluation. New tests should
use `reviewer_support` or public APIs so they also run directly in the packet
library. The shared guide also documents opt-in `ctx.draw_int_strict` for new
exact integer controls; existing `draw_int` behavior remains compatible.

The reviewer runs before and after checks, writes `DECISIONS.md` explaining
their input choices and alternatives, answers the assigned question, then
does two findings-only adversarial reviews and writes general feedback. The
packet includes the generator linter, run by the battery or alone with
`--stage lint`; reviewers may add optional linter feedback with a concrete task,
seed/input, and message. Use stable `F1:` IDs for feedback so intake can track
each item. They run
`python3 review.py package --out review_response_NAME.zip`. A blocked or no-change return is useful when its
decisions and evidence are complete. The builder sends a small return ZIP,
not the full library again.

New packets also require a fresh Python solve after the generator improvement.
Reviewers must not consult the Racket rule while solving; the tools prepare a
public challenge and retain every program revision and work-log snapshot. See
[the solve loop and tracker](solves/README.md). Intake rebuilds the tracker at
`var/review/solves/index.html`; `review solve-check ID --version N` independently
replays the inspected solutions before marking them good or bad.

### Optional maintainer checks for a concrete issue

Routine intake follows the lightweight acceptance commands at the top of this
guide. Use the longer checked path below when a concrete conflict or substantial
upgrade needs independent verification. Put all returned `review_response_*.zip`
files in one folder and run:

```bash
PYTHONPATH=src python3 -m arcpuzzles review collect /path/to/returns
PYTHONPATH=src python3 -m arcpuzzles review check review-ASSIGNMENT_ID --version 1
PYTHONPATH=src python3 -m arcpuzzles review assess review-ASSIGNMENT_ID --version 1
PYTHONPATH=src python3 -m arcpuzzles review integrate review-ASSIGNMENT_ID --version 1 \
  --component generator --component tests_notes
```

`review collect` refreshes the inbox automatically and prints its path. Open
`var/review/full-inbox/index.html` locally. Run `review inbox` later only when
you want to refresh statuses after checks or dispositions. It groups independent returns
and current adversarial findings; original ZIP links are only for fresh intake. `collect` validates
source-bound contracts without executing reviewer code; `check` runs a
candidate in a disposable source copy and therefore requires you to inspect
the proposed code first. Select all desired `generator`, `racket`, and
`tests_notes` components in **one** `integrate` command after a passing check.
Integration writes one evidence record per return, so a second component-only
call cannot add files later. Omit a component when the reviewed return does
not change it. Use `review disposition` to record a reason for a rejected or
deferred component, audit, or feedback item. Use
`review combine --source ID:VERSION --source ID:VERSION --out DIR` to stage a
comparison of colliding returns; any staged combination needs fresh checks
before it can be adopted. A changed generator or the same canonical task row
requires manual rebase and recheck. Unrelated canonical rows are preserved
when a checked rule component is integrated. Accepted full-packet repairs also
record approval under the policy above. Commands do not send anything externally.

### Existing preassigned returns

The older preassigned, one-generator route remains below for existing returns.

An operator claims one generator, packs its independent workspace, and sends the ZIP to a reviewer. The reviewer improves that generator as far as they can, returns a ZIP, and the operator checks and assesses each proposed change before selecting anything to integrate. These commands do not send messages or start agents.

## Prepare and send a packet

```bash
arcpuzzles review pick --cohort var/derived/verified-unapproved-official-generator-review-20260926-v1/receipt.json \
  --not-approved --source training --train-safety provisionally_safe --seed 42
arcpuzzles review list
arcpuzzles review pack review-REPLACE_WITH_ID --out var/review/request-REPLACE_WITH_ID.zip
```

The pinned cohort currently contains 746 verified original-family generators. The shown filters narrow it to 277 first-tranche training generators. The cohort receipt binds its row list, catalog, canonical source and lineage file hashes, and each generator's current hash. After changing any bound source, rebuild the cohort before another pick. Omit `--cohort` to draw from ordinary catalog filters. `--id ID` selects a specific eligible generator; `--question-id ID` binds a particular versioned question from `REVIEW/questions/`. Without that flag, an existing question may be chosen by seed. Active assignments are exclusive and random selection is seeded.

The packet contains `REQUEST.md`, immutable `ASSIGNMENT.json`, a mutable local `assignment.json`, `puzzle.json`, the baseline generator, a complete copied `workspace/`, and blank `RESULTS.json`, `REVIEW.md`, and `FEEDBACK_TO_CODEX.md`. The reviewer echoes `ASSIGNMENT.json` byte for byte. The packet needs no ARCpuzzles or sibling checkout to run its supplied scripts, though Python dependencies and Racket must be installed.

## Reviewer sequence

1. Inspect the generator, canonical examples, and Racket rule. Run before checks.
2. Improve the assigned generator and, if justified, its Racket solution. Run the battery and focused checks after each change. Iterate until you have made this generator as strong as you can. Do not weaken checks to clear a failure.
3. Record remaining failures, unrun checks, before/after evidence, and why you stopped in `REVIEW.md` and `RESULTS.json`.
4. Answer the assigned question, if any, in `QUESTION_ANSWER.json` or `QUESTION_ANSWER.md`. Record that path in `RESULTS.json`.
5. **Then** write general feedback in `FEEDBACK_TO_CODEX.md`, with stable IDs (`F1: ...`, `F2: ...`) and evidence paths. Include tooling ideas even when no code patch is safe.

Return a new ZIP containing the exact `ASSIGNMENT.json`, completed `RESULTS.json`, `REVIEW.md`, and `FEEDBACK_TO_CODEX.md`. Include only those files and declared return artifacts; do not rezip the entire request packet. Put proposed patches at `patches/generator__ID.patch`, `patches/racket__ID.patch`, or a task-local tests/notes path. List every patch in `RESULTS.json` under `patches`; list check artifacts under `checks`; name an optional `question_answer`. A useful no-patch return is valid with `patches: []` and an explanation.

Patches must use `diff --git a/workspace/... b/workspace/...` paths relative to the packet root. Only the assigned generator, its canonical row, bound task-specific base authority files, and `workspace/tests/ID/` or `workspace/notes/ID/` are permitted. A simple way to create them is to run `git init`, commit the untouched packet workspace locally, edit it, then run `git diff -- workspace/<assigned-path>` for each component. The return ZIP should contain the patch files, not a modified copy of the whole workspace.

## Receive, check, assess, and integrate

```bash
arcpuzzles review intake /path/to/review_response.zip
arcpuzzles review check review-REPLACE_WITH_ID --version 1 --timeout 4000
arcpuzzles review assess review-REPLACE_WITH_ID --version 1
arcpuzzles review integrate review-REPLACE_WITH_ID --version 1 --component generator
arcpuzzles review feedback review-REPLACE_WITH_ID --version 1 --item F1 \
  --status needs_evidence --reason "Need a measured example"
arcpuzzles review close review-REPLACE_WITH_ID --status completed --note "Assessed return v1"
```

`intake` temporarily retains the original ZIP and a content-hashed receipt for triage and extraction. Identical ZIPs are idempotent; changed ZIPs get new versions. Unsafe, malformed, or unmatched returns keep a rejection or mapping reason and require an explicit disposition before cleanup. No return is silently applied. `check` applies patches only in a disposable copied workspace and keeps failed logs. It runs the generator battery and, for Racket changes, exact canonical pairs and fixed medium seeds 0, 1, and 17. The copied workspace confines file changes but is **not a security sandbox** for executing untrusted Python; inspect the reviewer and patches before running checks.

In this legacy preassigned route, `assess` reports blockers, source drift, changes, question answer provenance, and feedback items. `integrate` requires a passing check for selected changes and current source hashes. Select `generator`, `racket`, or `tests_notes` independently; omit `--component` to record an explicit no-change disposition. It writes task-local evidence but has no automatic approval hook. Current full-packet returns use the owner policy at the top of this guide. Racket changes require explicit selection. Close as `completed` only after assessment. Use `--status cancelled --note REASON` for a never-returned assignment.

Fresh ZIPs, expanded returns, check logs and candidates live temporarily under
ignored `var/review/`, with triage metadata under `REVIEW/assignments/`. Extract
useful current findings and minimal evidence into the owning generator, and
shared requests into `REVIEW/suggestions.json`; then apply the verified retention
gate above. Unclassified or unextracted evidence blocks disposal. Questions and
strategy answers are reviewed separately; no ZIP text is automatically copied
into ARC2HQ.
