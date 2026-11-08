# Resume reviewer checks and inspect override cost

These are reviewer authoring helpers, not additional maintainer intake gates.

## Isolated Python prerequisites

Task-test staging sets `PYTHONNOUSERSITE=1`. A `pytest` installation in the
user site can work in your shell and still be unavailable to the checker.
New packets provide `python3 review.py python-check` from the outer folder:
it reports the interpreter, import paths and versions with user-site imports
disabled, installs nothing, and exits nonzero for missing/old prerequisites.
If it reports `ready: true`, keep that interpreter for `review.py` commands;
there is no need to create another environment. An existing venv should be
checked with `WORK/.venv/bin/python review.py python-check` before selecting it.
This is a setup diagnostic, not a qualification or acceptance check.

New packets bundle pinned pytest wheels. If only pytest is missing, create
`WORK/.venv` with `python3 -m venv --system-site-packages WORK/.venv`, then run
`WORK/.venv/bin/python review.py python-install-tests` from the outer folder.
The installer verifies every wheel and uses pip with `--no-index`; rerun
`WORK/.venv/bin/python review.py python-check` afterward. NumPy, Pillow and pip
are not bundled. A plain venv also works when those dependencies are provided
separately. This never installs into the system interpreter.

Owner cache retrieval, before packaging when network is available:
`PYTHONPATH=src python3 -m arcpuzzles.review_python_wheels fetch`.
The builder includes the verified `var/review/python-wheels/` cache automatically;
it does not download during a release. The packet manifest records exact wheel
hashes/bytes and whether this pytest-only cache is present. Older/source-only
packets without the cache continue to require a ready interpreter or dependency
installation from another available cache.

If no available interpreter has the prerequisites, install them in a clean
virtual environment. For older packets without `python-check`, inspect imports
using that same interpreter:

```bash
PYTHONNOUSERSITE=1 /path/to/venv/bin/python -m pip install 'pytest>=8' 'numpy>=1.26' 'Pillow>=10'
PYTHONNOUSERSITE=1 /path/to/venv/bin/python -c 'import pytest, numpy, PIL; print(pytest.__file__, numpy.__file__, PIL.__file__)'
```

Run the checker with that interpreter. Keep its existing import isolation;
an unavailable prerequisite is an infrastructure failure, not a generator
test failure.

Task checks collect `generators/TASK/tests/`, the exact existing frozen
`generators/TASK/test_generator_TASK.py`, and matching mapped legacy fixtures.
A copy mapped from the same library source runs once; distinct source files
remain separate even if their bytes match. Other generator-root test filenames
are not added implicitly. The receipt lists selected roots and omitted mirrors.
Frozen fixture failures and portability errors remain visible and cannot be
replaced by passing new tests. Reviewers leave frozen files unchanged; the
maintainer handles their migration.

### Optional owner-side portability repair

Before issuing new packets, the owner can preview narrow loader migrations:

```bash
arcpuzzles review migrate-tests TASK --check --out var/test-migration.json
arcpuzzles review migrate-tests TASK --apply var/test-migration.json
arcpuzzles check TASK --stage task_tests --out var/checks/portable-task
```

The preview contains exact source hashes and a patch. Explicit apply refuses
changed sources, preserves original test bytes under `var/test-portability/`,
and changes only recognized task-owned test loaders. It replaces fixed-depth
canonical-ledger paths with `canonical_path(find_root(__file__))` and exact
module-level generator imports with `load_selected_generator`. Assertions and
canonical contents remain intact. Other private `scripts.*` imports require
manual API review; an empty proposal is not a portable-test pass.

This is an owner convenience, not another reviewer duty or an automatic runtime
rewrite. Apply is refused inside issued packets, whose fixtures remain frozen.
Replay the affected task tests after applying; migration itself runs no tests
and grants no generator approval.

## Combined peer audit

```bash
arcpuzzles check TASK --stage audit --timeout 1800 --out var/checks/peer-audit
```

The explicit `audit` preset runs portable task tests, then the native strict
`semantic_gate`, on **one staged source snapshot**. It sets `phase: audit` and
retains both outcomes in `result.json` under `audit_stages`, the pytest XML,
semantic report/log, source manifest and evidence hashes. Failing task tests do
not suppress the semantic stage while execution time remains. Missing tests,
all-skipped tests, missing semantic evidence and `NO_CONTRACT` advisories cannot
produce a passing aggregate. The native gate keeps its existing finite scope;
passing the preset does not establish all-seed correctness.

Read `result.json.audit_summary` or `checks/TASK_audit_summary.json` for the
requested two-stage outcome. It lists `expected_stages`, completed stages,
`preset_complete`, `passed`, the controller status and source binding.
`preset_complete` means both requested stages terminated without timeout;
missing/all-skipped tests or a non-green semantic gate still yield `passed: false`.
Source changes and interruptions have explicit nonpassing verdicts. The separate
`TASK_audit_battery_summary.json` describes the full twelve-stage battery: its
unrequested stages remain pending and do not make the two-stage preset incomplete.

`--timeout` is shared by the two subprocess stages, after prerequisite checks
and snapshot preparation. A timed-out first stage prevents the second stage.
The native gate uses the remaining allowance instead of a fixed stage cap.
Source changes inside the staged tree invalidate the aggregate; an interrupted caller retains
completed-stage evidence. Choose a new output directory to retry: this preset
does not support `--resume`, `--battery`, or a different phase. For resume, use
the battery workflow below. Add `--require-rotations-identifiable` when the audit
requires query-rotation ambiguity, warnings and errors to fail the semantic gate.

This command is optional. It neither changes generator approval nor resolves
an audit finding; retain the conclusion in the assigned target's audit section.

## Individual stages and battery resume

```bash
arcpuzzles check TASK --battery --phase after --timeout 4000 --out var/checks/revision
# After an interruption, using the same library sources and runtime settings:
arcpuzzles check TASK --battery --resume --timeout 4000 --out var/checks/revision
```

Resume inherits the saved phase; explicitly supplying a different phase fails.
The timeout may increase. The selected source, canonical/rule authority and
shared-tool manifest must match exactly, as must the saved controller, Python,
Racket path/executable, PYTHONHASHSEED and authority patch settings. Older
checkpoints without these settings require a fresh output directory. Source
changes require a fresh output directory; resume never blesses changed bytes.

The disposable runtime is reconstructed from current matching library sources.
Only checkpoint files with matching recorded SHA256 are restored. Missing or
changed stage evidence invalidates its cached completion. A missing log also
invalidates completion. An unassignable corrupt artifact invalidates all stages
conservatively. Native battery reconciliation reuses completed stages and reruns
failed or incomplete stages; advisories retain their original distinction.
Lock directories, PID files and inherited `racket_env.sh` are never restored.
The current caller's `RACKET_PATH` remains authoritative.

Every resumed attempt archives the previous result, source manifest, progress
and checks under `OUT/attempts/0001/` (then `0002/`, etc.). Failures remain
available even after a successful retry. `OUT/result.json` records invalidated
stages and the latest outcome. Concurrent public writers are rejected by a
kernel file lock; the empty sibling lock file can remain after the process
exits and does not mean it is still running. Resume is currently battery-only.
If the original run used `--require-rotations-identifiable`, repeat that flag
when resuming. It is bound into the saved settings and native checkpoint subject;
a diagnostic run cannot supply a strict rotation success. A policy change requires
a fresh output directory.

### Execution time allowance

For native checks, public `--timeout` reserves the smaller of 20 seconds or
20% of that allowance for termination and terminal evidence. The remaining
time is shared across the selected native stages. Each stage receives only
the time still available, followed by at most 10 seconds of kill grace (or
10% of its remaining allowance, whichever is smaller). The audit preset
computes this from its shared allowance after task tests.

`result.json.execution_timeouts` records the caller and native limits;
native receipts/journal rows record the actual stage cap and grace. A native
timeout makes the public result `timed_out: true`, even when its controller
has time to save evidence. Stages not reached remain pending. Increasing a
timeout changes execution allowance, not what a semantic pass establishes.

Direct `run_generator_battery.sh` calls without `--time-budget` retain the
300-second per-stage cap and 10-second kill grace. `--time-budget SECONDS`
instead supplies one total native allowance; `--status` reconstructs the
last invocation's recorded allowance and exhaustion state. A resumed run's
new allowance does not erase the earlier stopped attempt.

### Foreground interruption and liveness

On Linux, ordinary foreground checks handle TERM/INT and stop their dedicated
subprocess session, including separate Bash and GNU timeout process groups.
Cleanup allows three seconds for TERM, then three seconds for the battery
parent to save its aggregate after stubborn descendants are killed. The shell
does not start another stage after a stop request. Already committed child
receipts and completed stages retain their original outcomes; an unfinished
stage and the controller aggregate are marked `interrupted` through atomic file
replacement. Audit presets retain their completed first stage and mark only
the active stage interrupted. TERM exits 143; INT exits 130.

For a clean battery interruption, stderr prints a shell-quoted **Resume:**
command. `result.json` also retains `resume_argv`, including the interpreter,
library, module/Racket paths, original timeout, phase and policy flags. Schedule
receipts use their checkpoint copy instead of relying on the original file.

The recipe also preserves the original `PATH` with the selected Racket executable
directory first. Gates that call `racket` by name therefore use the same pin as
the runner's explicit `RACKET_PATH`, even from a different caller environment.
This directory also precedes a bundled `racket` launcher in the Python
environment; Python subprocesses still use the selected Python environment.

For `--enumerate-schedule-period`, the command binds its fixed `--schedule-seed`
and retains a full `.schedule-census.json` beside the semantic report. This
receipt is checkpointed after each lesson: an interrupted census has incomplete
coverage. Resuming reruns the unfinished semantic stage on the exact snapshot;
it does not claim that a partial census was complete or resume individual rows.
Run the command in the same environment; source/settings validation still
applies. Other presets require a fresh output directory.

```bash
arcpuzzles check-status --out var/checks/revision
```

This reads the checkpoint and current Linux process identities without writing
files or signalling processes. PID birth ticks prevent a reused PID from
counting as the original controller. A checkpoint left `running` by a dead
controller is reported as `controller_lost_child_alive` if its child session
still has live processes, or `parent_interrupted_unclean` otherwise. Legacy or
unsupported identities report `liveness_unknown`. The process-table probe
first checks that `/proc/self/stat` and `/proc/<current PID>/stat` identify the
caller consistently; some sandboxes cannot provide that view. These states
cannot resume automatically: inspect surviving descendants, preserve the old evidence, then
use a fresh output directory. SIGKILL and a host loss cannot save a final
checkpoint. Custom caller signal handlers and HTTP worker threads remain under
their caller's control; descendants that deliberately start a new session are
outside the subprocess-session cleanup contract.

## Managed detached batteries

```bash
arcpuzzles check-run start TASK --phase after --timeout 4000
arcpuzzles check-run status RUN_ID
arcpuzzles check-run wait RUN_ID --wait-seconds 30
arcpuzzles check-run resume RUN_ID
```

The stable run ID addresses `var/check-runs/RUN_ID/`. The detached supervisor
survives caller exit and uses the existing exact-source battery checkpoint
engine. `stage_failed`, `stage_timeout`, and `parent_interrupted` are separate
states; attempts retain their earlier outcomes and logs. Resume rejects source
changes and concurrent work. A supervisor killed without cleanup is reported
as `parent_interrupted_unclean`, with resume disabled because descendants may
still be running. No processes are killed by status, wait or resume. Wait is
bounded to at most 60 seconds per invocation.
An unavailable or inconsistent process-table view reports `liveness_unknown`
for a nonterminal supervisor record, with resume disabled. Terminal worker
records retain their recorded outcome independently of this liveness probe.

## Override reports

Every override check prints a flushed PLAN before its first draw: axis probe
sizes, full and selected case counts, bands, seeds, matrix draw count, and the
maximum extra replay and unknown-key calls. PROGRESS prints every 1,000 matrix
draws and at completion. `--progress-every N` changes that interval. Counts are
work estimates, not a wall-time estimate, and no arbitrary draw limit is imposed.

The default is a root-cause summary: counts, one minimized witness per root
cause, source/checker/manifest hashes, settings, and an exact replay recipe.
`report_mode` is `summary`; `findings_complete` and `cases_complete` are false.
`finding_count` and root-cause counts retain the full failure population even
though duplicate details are omitted. The full case-result hash is retained.
Default battery invocations also omit the redundant full case-matrix artifact.

Use `arcpuzzles check TASK --stage override --full-results --out NEW` for every
passing/failing case and raw finding. `--compact-results` preserves the earlier
compatibility format: every failed case and every raw finding is retained,
with successful cases omitted. It is not the root-cause summary format.
The same flags are available directly in a prepared runtime:

```bash
python scripts/check_generator_override_contract.py TASK --seeds 30 \
  --full-results --write-results checks/override-full.json
```

All three modes execute the same verification. Complete-case consumers must
request `--full-results`; summary consumers should use counts and root causes.
Modes are bound into checkpoint settings. Smaller receipts do not reduce the
checker's in-memory storage or number of draws.

Raw findings, representative findings and minimized witnesses carry the exact
`sample_index` and `generate_call` (seed, sample index, difficulty and overrides)
for a draw. Use these arguments together to replay the finding: the index can
change the generated scene even with the same seed. Static and aggregate findings
have `generate_call: null`; they do not identify one reproducing draw. The
unknown-key probe records its own draw arguments separately from the matrix.


## Resource preflight and exact assignment recovery

Disk/memory capacity preflight has been removed from new review packets at the
owner's request. No resource guard or predicted-headroom threshold is required.
The temporary October 23 storage study requests only four counter snapshots;
when `storage_study` is present in the issued manifest, follow the
[return guide](../src/arcpuzzles/review_full_packet_files/RETURN-GUIDE.md#temporary-storage-comparison)
before full extraction. It ends October 30 UTC or after 16 reports, does not
scan other sessions and never blocks a review.
Use normal extraction into a new folder:

```sh
python3 -m zipfile -e SEND-THIS-ARCpuzzles-review.zip /path/new-review
cd /path/new-review
python3 review.py verify
python3 review.py start
python3 review.py duties
```

`verify` checks packet content hashes. It does not measure free memory or disk.
An actual extraction or runtime failure remains a failure: retain its command,
exit status and useful partial work, then continue in a writable location.

For an actual byte/inode failure, `python3 review.py storage --label 'Astra Pro fresh'`
is an optional read-only diagnostic. It needs only the outer `review.py`, with no
`WORK/`, dependencies or installation. Run the same file before extraction in a
fresh comparison chat (for example GPT-5.6 Pro); retain both JSON outputs. Labels
are supplied by the reviewer, not independently verified model identities.
The report records filesystem capacity, available bytes and file slots, device
identities and the current process's mount namespace. Repeated paths can refer
to the same storage and must not be added together. Different mount namespaces
can expose different `/tmp` or `/dev/shm`; a healthy measurement in another
process does not establish capacity in the process doing the work.

If useful, add `--owned-root /specific/working-directory` for a bounded metadata
count of a directory you have identified as your own. This never follows symlinks
or crosses filesystem devices, and marks budget-limited counts as incomplete.
It refuses broad system/workspace roots. It does not identify unrelated workspace
owners or guarantee that reported allocations can be reclaimed.

Cleanup belongs in the affected environment. First preserve changed source,
assignment journals and useful evidence. Remove only confirmed disposable copies
you own, then compare both byte and inode counters before and after. Removing one
large file can free bytes while freeing only one inode; redundant extracted trees
can occupy many inodes. Do not delete other sessions, runtime installations or
system files. If the initial environment is already nearly full and its usage is
outside your owned files, report that starting state rather than repeatedly
extracting, installing tools or scanning protected session histories. No capacity
threshold, cleanup action or preflight is part of the required reviewer workflow.

For a restart, preserve the existing extracted workspace, including `WORK/`,
its hidden `.review/` directory, assignment contracts, baseline files and work.
Run `python3 review.py start` there again; an interrupted draw resumes its
journaled assignment and a completed draw stays the same. Do not delete the
journal to get another task. If the workspace or seed is lost, report the review
as blocked; do not fabricate a replacement assignment or completed duties.

Old packet versions and their source-bound recovery records stay unchanged.
The legacy helper remains in the owner checkout for those records; it is not
bundled, recommended or invoked by the new review workflow.
