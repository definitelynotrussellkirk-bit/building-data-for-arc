#!/usr/bin/env bash
# Per-stage generator gate battery — shardable + resumable.
#
#   scripts/run_generator_battery.sh TASK_ID PHASE [STAGE] [FLAGS]
#
# PHASE is folded into output names: before (baseline), after (repair),
# audit (peer inspection). Audit uses the same strict policy as after and does
# not approve a generator or resolve its recorded findings.
# Without STAGE, runs every stage in order; with STAGE, runs exactly one —
# so environments with per-command caps can invoke each gate as its own
# short command. Logs land in checks/TASKID_PHASE_STAGE.log; a stage whose
# .ok marker already exists is skipped (delete the marker to re-run).
# Every failure is loud: the failing stage name and exit code are printed
# and the script exits nonzero immediately.
#
# FLAGS
#   --fresh / --force  ignore inherited .ok markers for this (task, phase)
#   --resume           import completed source-bound evidence into the journal,
#                      then restart at the first genuinely incomplete stage and
#                      exit once with an aggregate code
#   --status           read-only: rebuild checks/TASK_PHASE_battery_summary.json
#                      from markers/receipts/journal, print it, exit 0 when all
#                      stages are green or explicitly nonblocking advisories.
#                      Takes no lock and runs no gate.
#   --require-rotations-identifiable
#                      require identifiable query rotations in semantic_gate;
#                      repeat this flag on --resume / --status for that policy.
#   --schedule-census FILE --schedule-seed SEED
#                      consume a source-bound fixed-seed enumeration receipt;
#                      bytes and seed are part of the resume/status subject.
#   --keep-going       collect all stage failures in any phase while retaining
#                      a failing aggregate verdict.
#   --time-budget S    share S seconds across this native invocation, followed
#                      by bounded kill grace. Without it: 300 seconds/stage.
#
# RUNNING IT WHEN YOUR SANDBOX CAPS COMMAND TIME (the primary documented path).
# Twelve gates in one foreground command legitimately exceeds a short command
# window, and a parent killed at that boundary is what every receipt/lock/
# reconciliation mechanism below exists to survive. Prefer one of:
#
#   (a) PER-STAGE — one short command per gate, poll the summary between them:
#         for s in lint selfcheck rule_smoke defect_lint dist_gate profile_floor \
#                  semantic_gate diversity override grammar racket_lint authority_sync; do
#           bash scripts/run_generator_battery.sh TASK before "$s" --fresh
#         done
#         bash scripts/run_generator_battery.sh TASK before --status
#
#   (b) DETACHED + POLL — start it once in the background, then poll:
#         nohup bash scripts/run_generator_battery.sh TASK before --fresh \
#               > checks/TASK_before_battery.out 2>&1 &
#         bash scripts/run_generator_battery.sh TASK before --status   # repeat
#         bash scripts/run_generator_battery.sh TASK before --resume   # finish it
#
# In both cases --status is safe at any time (no lock, no writes to the
# journal) and --resume picks up exactly where the last invocation stopped.
set -u
# Non-interactive hygiene (adopted 2026-07-29, EWF-002049): sandboxes without a
# TERM make racket children print "TERM environment variable not set." and let
# terminal-aware tools (pytest) emit clear/color escapes into archived logs.
# Give every stage child a sane dumb terminal; suppress color when stdout is
# not a tty. Interactive runs keep their real TERM and colors.
if [ -z "${TERM:-}" ]; then export TERM=dumb; fi
if [ ! -t 1 ]; then export NO_COLOR=1; fi
# --fresh: ignore existing .ok markers for this (task, phase) and re-run every
# stage. A tree inherited from an earlier run can carry source-matching markers,
# and `... TASK before` then SKIPS baseline stages — producing a "baseline" that
# never ran while looking green. A fake before-battery invalidates the entire
# before/after comparison the review rests on (v13-z f0069f2752a4 WFB-701, who
# had to invent a `before_full` phase name to get a real baseline).
FRESH=0
RESUME=0
STATUS=0
KEEP_GOING_REQUESTED=0
REQUIRE_ROTATIONS=0
COMPACT_RESULTS=0
FULL_RESULTS=0
SCHEDULE_CENSUS=""
SCHEDULE_SEED=0
SCHEDULE_SHA=""
ENUMERATE_SCHEDULE=0
TIME_BUDGET=""
BUDGET_DEADLINE=""
BUDGET_EXHAUSTED=0
_args=()
while [ "$#" -gt 0 ]; do
  case "$1" in
    --fresh|--force) FRESH=1;;
    --resume) RESUME=1;;
    --status) STATUS=1;;
    --keep-going) KEEP_GOING_REQUESTED=1;;
    --require-rotations-identifiable) REQUIRE_ROTATIONS=1;;
    --enumerate-schedule-period) ENUMERATE_SCHEDULE=1;;
    --compact-results) COMPACT_RESULTS=1;;
    --full-results) FULL_RESULTS=1;;
    --time-budget)
      [ "$#" -ge 2 ] || { echo "--time-budget needs a value" >&2; exit 2; }
      TIME_BUDGET="$2"; shift;;
    --schedule-census|--schedule-seed)
      [ "$#" -ge 2 ] || { echo "$1 needs a value" >&2; exit 2; }
      if [ "$1" = --schedule-census ]; then SCHEDULE_CENSUS="$2"; else SCHEDULE_SEED="$2"; fi
      shift;;
    *) _args+=("$1");;
  esac
  shift
done
set -- ${_args+"${_args[@]}"}
if [ -n "$TIME_BUDGET" ]; then
  _budget=$(python3 -c 'import math,sys,time
try: value=float(sys.argv[1]); assert math.isfinite(value) and value>0
except (ValueError,AssertionError): raise SystemExit("--time-budget must be finite and positive")
print(format(value,".12g"),format(time.monotonic()+value,".12g"))' "$TIME_BUDGET") || exit 2
  read -r TIME_BUDGET BUDGET_DEADLINE <<< "$_budget"
fi
TASK="${1:?usage: run_generator_battery.sh TASK_ID PHASE [STAGE] [--fresh|--resume|--status]}"
PHASE="${2:?usage: run_generator_battery.sh TASK_ID PHASE [STAGE] [--fresh|--resume|--status]}"
ONLY="${3:-}"
if [ "$ENUMERATE_SCHEDULE" = 1 ]; then
  if [ -n "$SCHEDULE_CENSUS" ] || { [ -n "$ONLY" ] && [ "$ONLY" != semantic_gate ]; }; then
    echo "--enumerate-schedule-period requires semantic_gate or battery, without --schedule-census" >&2
    exit 2
  fi
  SCHEDULE_SEED=$(python3 -c 'import sys; n=int(sys.argv[1]); assert 0 <= n < 2**32; print(n)' "$SCHEDULE_SEED") || exit 2
fi
if [ -n "$SCHEDULE_CENSUS" ]; then
  if [ -n "$ONLY" ] && [ "$ONLY" != semantic_gate ]; then
    echo "--schedule-census requires semantic_gate or the whole battery" >&2
    exit 2
  fi
  SCHEDULE_SEED=$(python3 -c 'import sys; n=int(sys.argv[1]); assert 0 <= n < 2**32; print(n)' "$SCHEDULE_SEED") || exit 2
  SCHEDULE_SHA=$(python3 -c 'import hashlib,sys; print(hashlib.sha256(open(sys.argv[1], "rb").read()).hexdigest())' "$SCHEDULE_CENSUS") || exit 2
elif [ "$SCHEDULE_SEED" != 0 ] && [ "$ENUMERATE_SCHEDULE" != 1 ]; then
  echo "--schedule-seed requires --schedule-census or --enumerate-schedule-period" >&2
  exit 2
fi
if [ "$REQUIRE_ROTATIONS" = 1 ] && [ -n "$ONLY" ] && [ "$ONLY" != semantic_gate ]; then
  echo "--require-rotations-identifiable requires semantic_gate or the whole battery" >&2
  exit 2
fi
if [ "$COMPACT_RESULTS" = 1 ] && [ "$FULL_RESULTS" = 1 ]; then
  echo "--compact-results and --full-results are mutually exclusive" >&2
  exit 2
fi
if [ "$FULL_RESULTS" = 1 ] && [ -n "$ONLY" ] && [ "$ONLY" != override ]; then
  echo "--full-results requires override or the whole battery" >&2
  exit 2
fi
if [ "$COMPACT_RESULTS" = 1 ] && [ -n "$ONLY" ] && [ "$ONLY" != override ]; then
  echo "--compact-results requires override or the whole battery" >&2
  exit 2
fi
cd "$(dirname "$0")/.."
mkdir -p checks
# Racket installed by setup_racket.sh exports PATH only in its own shell;
# source its env file so noninteractive stages inherit it (EWF-000352).
[ -f checks/racket_env.sh ] && . checks/racket_env.sh
STAGES=(lint selfcheck rule_smoke defect_lint dist_gate profile_floor semantic_gate diversity override grammar racket_lint authority_sync)
# A "before" baseline EXPECTS failing stages — collect every stage's
# evidence instead of stopping at the first failure (EWF-000398/411/426).
# Any before-prefixed phase label counts (EWF-000496).
KEEP_GOING=0
case "$PHASE" in before*) KEEP_GOING=1;; esac
[ "$KEEP_GOING_REQUESTED" = 1 ] && KEEP_GOING=1
# Markers bind the generator plus every task authority consumed by a source-
# sensitive stage: canonical program_solution, selected target_code, archival
# raw_code, and the metadata that assigns those roles. A task-local source-only
# edit must invalidate cached authority/parity receipts just as a generator edit
# does (EWF-001389/001427/001429).
IFS=$'\t' read -r GEN_FILE_SHA AUTHORITY_SET_SHA GEN_SHA < <(
  python3 scripts/generator_battery_subject.py "$TASK" --tsv
) || {
  echo "LOUD: could not compute the source-bound battery subject for $TASK" >&2
  exit 2
}
# Required rotations are a different evidence subject: native --resume must
# never promote a diagnostic .ok marker, receipt or journal row to strict PASS.
if [ "$REQUIRE_ROTATIONS" = 1 ]; then
  GEN_SHA=$(python3 -c 'import hashlib,sys; print(hashlib.sha256((sys.argv[1] + "|require_rotations_identifiable=1").encode()).hexdigest()[:16])' "$GEN_SHA") || exit 2
fi
if [ -n "$SCHEDULE_CENSUS" ]; then
  GEN_SHA=$(python3 -c 'import hashlib,sys; print(hashlib.sha256((sys.argv[1] + "|schedule=" + sys.argv[2] + "|seed=" + sys.argv[3]).encode()).hexdigest()[:16])' "$GEN_SHA" "$SCHEDULE_SHA" "$SCHEDULE_SEED") || exit 2
fi
if [ "$ENUMERATE_SCHEDULE" = 1 ]; then
  GEN_SHA=$(python3 -c 'import hashlib,sys; print(hashlib.sha256((sys.argv[1] + "|enumerate_schedule_period=1|seed=" + sys.argv[2]).encode()).hexdigest()[:16])' "$GEN_SHA" "$SCHEDULE_SEED") || exit 2
fi
# Receipt mode changes the evidence subject, so native resume/status cannot
# mistake full receipts for compact receipts or reuse the reverse selection.
if [ "$COMPACT_RESULTS" = 1 ]; then
  GEN_SHA=$(python3 -c 'import hashlib,sys; print(hashlib.sha256((sys.argv[1] + "|compact_results=1").encode()).hexdigest()[:16])' "$GEN_SHA") || exit 2
fi
if [ "$FULL_RESULTS" = 1 ]; then
  GEN_SHA=$(python3 -c 'import hashlib,sys; print(hashlib.sha256((sys.argv[1] + "|full_results=1").encode()).hexdigest()[:16])' "$GEN_SHA") || exit 2
fi
if [ "$COMPACT_RESULTS" = 0 ] && [ "$FULL_RESULTS" = 0 ]; then
  GEN_SHA=$(python3 -c 'import hashlib,sys; print(hashlib.sha256((sys.argv[1] + "|override_report=summary-v1").encode()).hexdigest()[:16])' "$GEN_SHA") || exit 2
fi
LOCKDIR="checks/.lock_${TASK}_${PHASE}"
SUMMARY="checks/${TASK}_${PHASE}_battery_summary.json"
RUN_ID=""
# ONE ATOMIC BATTERY SUMMARY, rebuildable from evidence that outlives the parent.
#
# Workers were reconstructing "where did this battery get to" by hand out of
# checks/TASK_PHASE_commands.jsonl every time a sandbox killed the parent. The
# inputs for that answer are already on disk and are all SOURCE-BOUND: the .ok
# markers, the child-side .receipt files, and the journal. This function folds
# them into one artifact, written by rename(2) so a reader never sees a partial
# file, and it derives everything from those artifacts rather than from live
# shell state — which is exactly why it still works after the parent is gone.
#
# Advisory stages are counted SEPARATELY from green ones. A stage that exited
# 0 under an explicit nonblocking policy still has a finding, and folding it
# into "green" is the misreading workers reported about both NO_CONTRACT and
# canonical-profile WARN results.
#
#   $1  who generated it: stage | final | status | resume
#   $2  "print" to also render a human-readable table on stdout
battery_summary() {
  S_TASK="$TASK" S_PHASE="$PHASE" S_SUBJECT="$GEN_SHA" S_RUN_ID="$RUN_ID" \
  S_GENERATOR_FILE_SHA="$GEN_FILE_SHA" S_AUTHORITY_SET_SHA="$AUTHORITY_SET_SHA" \
  S_REQUIRE_ROTATIONS="$REQUIRE_ROTATIONS" \
  S_SCHEDULE_SHA="$SCHEDULE_SHA" S_SCHEDULE_SEED="$SCHEDULE_SEED" \
  S_ENUMERATE_SCHEDULE="$ENUMERATE_SCHEDULE" \
  S_COMPACT_RESULTS="$COMPACT_RESULTS" \
  S_STAGES="${STAGES[*]}" S_OUT="$SUMMARY" S_BY="$1" S_PRINT="${2:-}" \
  S_TIME_BUDGET="$TIME_BUDGET" S_BUDGET_EXHAUSTED="$BUDGET_EXHAUSTED" \
  S_LOCKDIR="$LOCKDIR" python3 - <<'PYEOF' || {
import datetime, json, os, shutil, sys

TERMINAL = ("finished", "recovered_finished", "interrupted")
task = os.environ["S_TASK"]
phase = os.environ["S_PHASE"]
subject = os.environ["S_SUBJECT"]
stages = os.environ["S_STAGES"].split()
out = os.environ["S_OUT"]
by = os.environ.get("S_BY") or "run"
prefix = os.path.join("checks", "%s_%s_" % (task, phase))


def slurp(path):
    with open(path, encoding="utf-8", errors="replace") as handle:
        return handle.read()


journal = prefix + "commands.jsonl"
rows, malformed = [], 0
if os.path.exists(journal):
    for line in slurp(journal).splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except ValueError:
            malformed += 1

# Lock/PID liveness FIRST (adopted 2026-07-29, EWF-002036/002040): stage
# classification needs to know whether the battery owner is alive, so a stage
# mid-execution reads "running", and "interrupted" is reserved for a dead owner.
lockdir = os.environ.get("S_LOCKDIR") or ""
live = {"lock_present": bool(lockdir) and os.path.isdir(lockdir),
        "lock_run_id": None, "lock_pid": None, "pid_alive": False}
if live["lock_present"]:
    for name, key in (("run_id", "lock_run_id"), ("pid", "lock_pid")):
        path = os.path.join(lockdir, name)
        if os.path.exists(path):
            live[key] = slurp(path).strip()
    pid = None
    if live["lock_pid"] and live["lock_pid"].isdigit():
        pid = int(live["lock_pid"])
    elif live["lock_run_id"] and live["lock_run_id"].rsplit("-", 1)[-1].isdigit():
        pid = int(live["lock_run_id"].rsplit("-", 1)[-1])
    live["lock_pid"] = pid
    if pid:
        try:
            os.kill(pid, 0)
            live["pid_alive"] = True
        except ProcessLookupError:
            live["pid_alive"] = False
        except PermissionError:      # alive, owned by someone else
            live["pid_alive"] = True
owner_running = live["pid_alive"] and by != "final"

stale, inconsistent, entries = [], [], {}
for stage in stages:
    ok_path = "%s%s.ok" % (prefix, stage)
    receipt_path = "%s%s.receipt" % (prefix, stage)
    log_path = "%s%s.log" % (prefix, stage)
    entry = {
        "status": "pending", "exit": None, "evidence": "none",
        "advisory": False, "duration_seconds": None, "timed_out": None,
        "utc_start": None, "utc_end": None, "run_id": None,
        "log": log_path if os.path.exists(log_path) else None,
    }
    # SOURCE BINDING IS THE WHOLE POINT: evidence stamped with a different
    # subject describes a different generator/rule and must never be reused.
    marker = None
    if os.path.exists(ok_path):
        marker = slurp(ok_path).strip()
        if marker != subject:
            stale.append({"stage": stage, "artifact": "ok_marker",
                          "found_sha16": marker, "expected_sha16": subject})
            marker = None
    receipt = None
    if os.path.exists(receipt_path):
        try:
            receipt = json.loads(slurp(receipt_path))
        except ValueError:
            receipt = None
            stale.append({"stage": stage, "artifact": "receipt",
                          "found_sha16": None, "expected_sha16": subject,
                          "reason": "unparseable"})
        if isinstance(receipt, dict) and receipt.get("subject_sha16") != subject:
            stale.append({"stage": stage, "artifact": "receipt",
                          "found_sha16": receipt.get("subject_sha16"),
                          "expected_sha16": subject})
            receipt = None
    starts = terms = 0
    last_terminal = None
    last_started = None
    for row in rows:
        if row.get("stage") != stage or row.get("subject_sha16") != subject:
            continue
        status = row.get("status")
        if status == "started":
            starts += 1
            last_started = row
        elif status in TERMINAL:
            terms += 1
            last_terminal = row
    dangling = starts > terms

    code = None
    if isinstance(receipt, dict):
        code = receipt.get("exit")
        entry["evidence"] = "receipt"
        entry["timed_out"] = bool(receipt.get("timed_out"))
        entry["utc_end"] = receipt.get("utc_end")
        entry["run_id"] = receipt.get("run_id")
        for key in ('timeout_seconds', 'kill_after_seconds', 'time_budget_seconds'):
            if receipt.get(key) is not None:
                entry[key] = receipt[key]
    elif marker is not None:
        code = 0
        entry["evidence"] = "ok_marker"
    elif last_terminal is not None and last_terminal.get("exit") is not None:
        code = last_terminal.get("exit")
        entry["evidence"] = "journal"
    if last_terminal is not None:
        for key in ("duration_seconds", "utc_start", "utc_end", "run_id",
                    "timed_out", "timeout_seconds", "kill_after_seconds", "time_budget_seconds"):
            if entry.get(key) is None and last_terminal.get(key) is not None:
                entry[key] = last_terminal[key]

    # RECEIPT-RECOVERED TIMING (2026-07-25). A stage whose child finished but
    # whose PARENT was killed has a complete receipt and a `started` journal row
    # — but no terminal row, so the back-fill above finds nothing and the stage
    # is reported green with utc_start and duration_seconds null. Eleven workers
    # reported some form of this in one batch; five named the null timing
    # specifically, and one asked for exactly this join ("even when a matching
    # started journal row exists", EWF-001033).
    #
    # The two halves are already on disk and simply were not joined: the
    # `started` row carries utc_start, the receipt carries utc_end. Reconstruct
    # from those rather than leaving the evidence blank — a green stage with no
    # duration is indistinguishable from one that never really ran, and these
    # summaries are the evidence a repair is judged on.
    #
    # Deliberately NOT invented: if either endpoint is missing the field stays
    # null. A fabricated duration would be worse than an absent one.
    if entry.get("utc_start") is None and last_started is not None:
        entry["utc_start"] = last_started.get("utc_start")
    if entry.get("duration_seconds") is None \
            and entry.get("utc_start") and entry.get("utc_end"):
        try:
            started_at = datetime.datetime.strptime(
                entry["utc_start"], "%Y-%m-%dT%H:%M:%SZ")
            ended_at = datetime.datetime.strptime(
                entry["utc_end"], "%Y-%m-%dT%H:%M:%SZ")
            span = (ended_at - started_at).total_seconds()
            if span >= 0:
                entry["duration_seconds"] = span
                entry["duration_source"] = "reconstructed_started_row_plus_receipt"
        except (ValueError, TypeError):
            pass                      # unparseable stamp: leave it null, loudly absent
    if entry["log"] and "ADVISORY-OK" in slurp(entry["log"]):
        entry["advisory"] = True

    if code is None:
        if dangling and owner_running:
            # The lock owner is alive and this stage has a started row with no
            # terminal evidence yet: it is EXECUTING, not interrupted
            # (EWF-002036: --status showed live stages as interrupted).
            entry["status"] = "running"
        elif dangling:
            entry["status"] = "interrupted"
        else:
            entry["status"] = "pending"
    elif code == 0:
        entry["status"] = "advisory" if entry["advisory"] else "green"
    else:
        entry["status"] = "failed"
    entry["exit"] = code
    if marker is not None and isinstance(receipt, dict) \
            and receipt.get("exit") not in (0, None):
        inconsistent.append({
            "stage": stage, "receipt_exit": receipt.get("exit"),
            "note": "a success .ok marker coexists with a FAILING child receipt "
                    "for the same source; the receipt is authoritative",
        })
    entries[stage] = entry

green = [s for s in stages if entries[s]["status"] == "green"]
advisory = [s for s in stages if entries[s]["status"] == "advisory"]
failed = [s for s in stages if entries[s]["status"] == "failed"]
interrupted = [s for s in stages if entries[s]["status"] == "interrupted"]
running = [s for s in stages if entries[s]["status"] == "running"]
pending = [s for s in stages if entries[s]["status"] == "pending"]
# What --resume would re-execute: never ran, ran but was cut off, or ran and
# failed. A failed stage is "incomplete" for resume purposes because it has no
# .ok marker and must be re-run against the repaired source. A "running" stage
# is NOT resumable — its owner is alive and executing it right now.
resumable = [s for s in stages
             if entries[s]["status"] in ("pending", "interrupted", "failed")]
unfinished = pending + interrupted + running
# `final` is written by the invocation that is itself finishing, so its own
# still-held lock must not be reported as another live run. Both facts are
# published: a reader who sees `lock_present` on a finished battery needs to be
# able to tell "still going" from "this is the run that just ended".
live_now = live["pid_alive"] and by != "final"
live["own_lock"] = bool(os.environ.get("S_RUN_ID")) \
    and live["lock_run_id"] == os.environ.get("S_RUN_ID")
live["used_for_verdict"] = live_now
if live_now and unfinished:
    verdict = "running"
elif failed:
    verdict = "failed"
elif unfinished:
    verdict = "incomplete"
elif advisory:
    verdict = "passed_with_advisories"
else:
    verdict = "all_green"

run_id = os.environ.get("S_RUN_ID") or ""
if not run_id:
    for row in reversed(rows):
        if row.get("run_id"):
            run_id = row["run_id"]
            break

note = ("%d green, %d advisory, %d failed, %d interrupted, %d pending of %d"
        % (len(green), len(advisory), len(failed), len(interrupted),
           len(pending), len(stages)))
if running:
    note += ", %d running" % len(running)
summary = {
    "schema": "generator_battery_summary/1",
    "task": task,
    "phase": phase,
    "run_id": run_id or None,
    "subject_sha16": subject,
    "battery_subject_sha16": subject,
    "require_rotations_identifiable": os.environ["S_REQUIRE_ROTATIONS"] == "1",
    "schedule_census_sha256": os.environ["S_SCHEDULE_SHA"] or None,
    "schedule_seed": int(os.environ["S_SCHEDULE_SEED"]) if os.environ["S_SCHEDULE_SHA"] or os.environ["S_ENUMERATE_SCHEDULE"] == "1" else None,
    "enumerate_schedule_period": os.environ["S_ENUMERATE_SCHEDULE"] == "1",
    "compact_results": os.environ["S_COMPACT_RESULTS"] == "1",
    "generator_file_sha256": os.environ["S_GENERATOR_FILE_SHA"],
    "authority_set_sha256": os.environ["S_AUTHORITY_SET_SHA"],
    "generated_utc": datetime.datetime.now(datetime.timezone.utc)
        .strftime("%Y-%m-%dT%H:%M:%SZ"),
    "generated_by": by,
    "verdict": verdict,
    "verdict_note": note,
    "first_failing_stage": failed[0] if failed else None,
    "first_incomplete_stage": resumable[0] if resumable else None,
    "counts": {
        "total": len(stages), "green": len(green), "advisory": len(advisory),
        "failed": len(failed), "interrupted": len(interrupted),
        "pending": len(pending), "running": len(running),
    },
    "advisory_note": "advisory stages exited 0 under an explicit nonblocking "
                     "policy; they have findings and are NOT included in "
                     "counts.green / green_stages. Read each stage log for "
                     "the advisory reason.",
    "stage_order": list(stages),
    "stages": entries,
    "green_stages": green,
    "advisory_stages": advisory,
    "failed_stages": [{"stage": s, "exit": entries[s]["exit"],
                       "log": entries[s]["log"]} for s in failed],
    "interrupted_stages": interrupted,
    "running_stages": running,
    "pending_stages": pending,
    "resumable_stages": resumable,
    "stale_evidence": stale,
    "inconsistent_evidence": inconsistent,
    "malformed_journal_lines": malformed,
    "journal": journal if os.path.exists(journal) else None,
    "live": live,
}
# Compact override diagnostics (adopted 2026-07-29, EWF-002042): a failed
# override stage used to surface only the log path, forcing readers into a
# many-thousand-line log the results JSON had already condensed. Mirror the
# dominant root causes + unknown-key verdict here.
override_results = prefix + "override_results.json"
if os.path.exists(override_results):
    try:
        override_payload = json.loads(slurp(override_results))
    except (ValueError, OSError):
        summary["override_diagnostics"] = {"error": "unreadable override_results.json"}
    else:
        top_causes = [
            {
                "count": cause.get("count"),
                "axis": cause.get("axis"),
                "category": cause.get("category"),
                "signature": cause.get("signature"),
                "minimized_witness": cause.get("minimized_witness"),
            }
            for cause in (override_payload.get("root_causes") or [])[:3]
        ]
        summary["override_diagnostics"] = {
            "status": override_payload.get("status"),
            "finding_categories": override_payload.get("finding_categories"),
            "warning_categories": override_payload.get("warning_categories"),
            "unknown_key_verdict": (
                (override_payload.get("unknown_key_probe") or {}).get("verdict")),
            "top_root_causes": top_causes,
            "source": override_results,
        }
# Selected vs archival source-sync split (adopted 2026-07-29, EWF-002052): a
# single green authority_sync stage must not conflate exact selected sync with
# lawful archival divergence — surface both statuses in the summary.
authority_sync_json = prefix + "authority_sync.json"
if os.path.exists(authority_sync_json):
    try:
        sync_payload = json.loads(slurp(authority_sync_json))
        sync_audits = sync_payload.get("audits") or (
            [sync_payload] if sync_payload.get("task_id") else [])
    except (ValueError, OSError):
        summary["authority_sync_diagnostics"] = {
            "error": "unreadable authority_sync.json"}
    else:
        summary["authority_sync_diagnostics"] = [
            {
                "task_id": audit.get("task_id"),
                "status": audit.get("status"),
                "selected_group_counts": audit.get("selected_group_counts"),
                "group_counts": audit.get("group_counts"),
                "archival_divergent": audit.get("archival_divergent"),
                "execution_parity": (
                    (audit.get("execution_parity") or {}).get("status")
                    if isinstance(audit.get("execution_parity"), dict)
                    else audit.get("execution_parity")),
                "source": authority_sync_json,
            }
            for audit in sync_audits
        ]
budget_raw = os.environ.get('S_TIME_BUDGET', '')
budget_rows = [row for row in rows if row.get('subject_sha16') == subject
               and row.get('time_budget_seconds') is not None]
budget_run = os.environ.get('S_RUN_ID') if budget_raw else (
    budget_rows[-1].get('run_id') if budget_rows else None)
summary['time_budget_seconds'] = float(budget_raw) if budget_raw else next(
    (row.get('time_budget_seconds') for row in reversed(rows)
     if row.get('subject_sha16') == subject and row.get('time_budget_seconds') is not None), None)
summary['budget_exhausted'] = os.environ.get('S_BUDGET_EXHAUSTED') == '1' or any(
    row.get('subject_sha16') == subject and row.get('run_id') == budget_run
    and row.get('budget_exhausted') is True for row in rows)
line = json.dumps(summary, indent=2)
json.loads(line)              # refuse to publish anything unparseable
# A later --status against an edited source must not erase the actual before
# summary. Preserve the prior subject under a content-addressed name before
# publishing the current-source reconstruction at the conventional path.
if by == "status" and os.path.exists(out):
    try:
        previous = json.loads(slurp(out))
    except (OSError, ValueError):
        previous = None
    previous_subject = (
        previous.get("subject_sha16") if isinstance(previous, dict) else None
    )
    if previous_subject and previous_subject != subject:
        stem, suffix = os.path.splitext(out)
        historical = "%s.subject_%s%s" % (stem, previous_subject, suffix)
        if not os.path.exists(historical):
            shutil.copyfile(out, historical)
        summary["preserved_prior_summary"] = historical
        line = json.dumps(summary, indent=2)
tmp = out + ".tmp"
with open(tmp, "w", encoding="utf-8") as handle:
    handle.write(line + "\n")
os.replace(tmp, out)          # atomic

# Stale/corrupt evidence is LOUD on every terminal write. It is suppressed for
# the per-stage refresh only so one bad marker cannot print twelve times.
if by != "stage":
    for item in stale:
        print("LOUD: ignoring stale %s for stage %s (subject %s != %s)"
              % (item["artifact"], item["stage"], item.get("found_sha16"),
                 subject), file=sys.stderr)
    for item in inconsistent:
        print("LOUD: %s: %s" % (item["stage"], item["note"]), file=sys.stderr)
    if malformed:
        print("LOUD: %d unparseable line(s) ignored in %s"
              % (malformed, journal), file=sys.stderr)

if os.environ.get("S_PRINT"):
    print("BATTERY SUMMARY  %s / %s" % (task, phase))
    print("  subject_sha16 : %s" % subject)
    print("  generator sha : %s" % os.environ["S_GENERATOR_FILE_SHA"])
    print("  authority sha : %s" % os.environ["S_AUTHORITY_SET_SHA"])
    print("  verdict       : %s  (%s)" % (verdict, note))
    for stage in stages:
        entry = entries[stage]
        print("  %-15s %-12s exit=%-5s %-5s %s"
              % (stage, entry["status"],
                 "-" if entry["exit"] is None else entry["exit"],
                 "-" if entry["duration_seconds"] is None
                 else "%ss" % entry["duration_seconds"],
                 entry["evidence"]))
    if failed:
        print("  first failing : %s (exit %s) -> %s"
              % (failed[0], entries[failed[0]]["exit"], entries[failed[0]]["log"]))
    if advisory:
        print("  advisory      : %s  (nonblocking findings — not green; read logs)"
              % ", ".join(advisory))
    print("  summary       : %s" % out)
    if resumable:
        print("  resume with   : bash scripts/run_generator_battery.sh %s %s "
              "--resume   (restarts at %s)" % (task, phase, resumable[0]))
PYEOF
    echo "LOUD: battery summary NOT written to $SUMMARY — the run's state is" \
         "unreported; rebuild it with --status." >&2
    return 1
  }
}
summary_verdict() {
  [ -f "$SUMMARY" ] || { echo "unknown"; return 0; }
  SV="$SUMMARY" python3 -c 'import json,os;print(json.load(open(os.environ["SV"])).get("verdict") or "unknown")'
}
# --status is READ-ONLY with respect to stage execution and the journal, so it
# deliberately runs BEFORE (and without) the lock: polling a battery must never
# be able to block, corrupt, or be blocked by the run it is reporting on.
if [ "$STATUS" = 1 ]; then
  if [ -n "$ONLY" ]; then
    echo "LOUD: --status reports the whole battery and takes no STAGE argument." >&2
    exit 2
  fi
  if [ "$RESUME" = 1 ]; then
    echo "LOUD: --status (report only) and --resume (execute) are mutually exclusive." >&2
    exit 2
  fi
  battery_summary status print || exit 2
  case "$(summary_verdict)" in
    all_green|passed_with_advisories) exit 0;;
    *) exit 1;;
  esac
fi
if [ "$RESUME" = 1 ] && [ "$FRESH" = 1 ]; then
  echo "LOUD: --resume (reuse source-bound evidence) contradicts --fresh (discard it)." >&2
  exit 2
fi
# ATOMIC (task_id, phase) LOCK + per-run id. Two concurrent invocations for the
# same task+phase raced over the shared .ok / .log / .log.prev / command-journal
# paths, producing duplicate started/finished rows AND spurious "recovered
# interrupted" rows even though every gate passed — reported independently by
# two workers (v13-y 8ff1ff513757, 03829f6274d2). mkdir is atomic on POSIX, so
# the loser FAILS CLOSED without touching any existing evidence.
if ! mkdir "$LOCKDIR" 2>/dev/null; then
  echo "LOUD: another battery run holds ${TASK}/${PHASE} (lock: $LOCKDIR)." >&2
  echo "      Refusing to start — a second writer corrupts the evidence journal." >&2
  echo "      If that run died, remove the lock dir and retry." >&2
  exit 3
fi
RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)-$$"
printf '%s\n' "$RUN_ID" > "$LOCKDIR/run_id"
# The pid lets --status tell "a battery is still running" apart from "a battery
# was SIGKILLed and left its lock behind" without guessing from the run_id.
printf '%s\n' "$$" > "$LOCKDIR/pid"
# Job control: each background job becomes its own process group, so an
# interrupted parent can kill the WHOLE stage subtree rather than orphaning it.
# A worker watched an orphaned override checker keep burning CPU after its
# parent died, until they killed it by hand (v13-z 2acfd448f58b WFB-701).
set -m
CHILD_PID=""
cleanup() {
  if [ -n "$CHILD_PID" ] && kill -0 "$CHILD_PID" 2>/dev/null; then
    # GRACE FIRST. Killing on the instant the parent is signalled destroys a
    # stage that was milliseconds from writing its receipt, and the run is then
    # journaled as exit 143 under a log that says PASS — reported by three
    # workers (a4f0ea66fd65 WFB-701, 056999828b88 WFB-056999001,
    # c0966960e255 WFB-002) after this trap was introduced. Sandboxes TERM the
    # parent at a fixed wall-clock boundary while the child is still healthy,
    # so a short wait converts most of those into clean completions.
    for _ in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do
      kill -0 "$CHILD_PID" 2>/dev/null || break
      command sleep 0.5
    done
    if ! kill -0 "$CHILD_PID" 2>/dev/null; then
      rm -rf "$LOCKDIR"; return 0        # finished on its own — nothing to kill
    fi
    echo "LOUD: battery interrupted — terminating active stage child group $CHILD_PID" >&2
    kill -TERM "-$CHILD_PID" 2>/dev/null || kill -TERM "$CHILD_PID" 2>/dev/null
    for _ in 1 2 3 4 5 6 7 8 9 10; do
      kill -0 "$CHILD_PID" 2>/dev/null || break
      command sleep 0.5
    done
    kill -KILL "-$CHILD_PID" 2>/dev/null || kill -KILL "$CHILD_PID" 2>/dev/null
  fi
  rm -rf "$LOCKDIR"
}
trap cleanup EXIT
handle_signal() {
  # Do not continue --keep-going into another stage after a stop request.
  # Existing child-side receipts remain authoritative if already committed.
  trap '' INT TERM
  cleanup
  CHILD_PID=""
  battery_summary final || true
  exit "$1"
}
trap 'handle_signal 130' INT
trap 'handle_signal 143' TERM
cmd_for() {
  if [[ "$TASK" == generic_* ]]; then
    case "$1" in
      lint|dist_gate|profile_floor|semantic_gate|override|authority_sync)
        echo "python3 scripts/generic_generator_gate.py $TASK $1 --seeds 20 --json-out checks/${TASK}_${PHASE}_$1.json"; return;;
      rule_smoke|racket_lint)
        echo "python3 scripts/generic_generator_gate.py $TASK $1 --seeds 40 --json-out checks/${TASK}_${PHASE}_$1.json"; return;;
      diversity)
        echo "python3 scripts/gen_diversity_probe.py --task-id $TASK --episodes 50 --no-append"; return;;
      selfcheck)
        echo "python3 scripts/generator_selfcheck.py $TASK --n 20 --timeout-sec 120 --require-selfcheck"; return;;
      defect_lint)
        echo "python3 scripts/generator_defect_lint.py $TASK --seeds 20 --bands easy,medium,hard --strict"; return;;
      grammar)
        echo "python3 scripts/grammar_gate.py"; return;;
    esac
  fi
  case "$1" in
    lint)          echo "python3 scripts/lint_generator.py $TASK --validate";;
    # --require-mutation-sensitivity: an acceptance-only self_check (rejects
    # zero generic destructive mutations) fails the stage — adopted 2026-07-29
    # from 2db1f7f0392d WFB-001; a green acceptance-only selfcheck is
    # non-probative.
    selfcheck)     echo "python3 scripts/generator_selfcheck.py $TASK --n 20 --timeout-sec 120 --require-selfcheck --require-mutation-sensitivity";;
    # --json-out is not optional: without it every worker re-ran the same 120
    # real Racket applications by hand just to obtain p95 / input-purity /
    # restart accounting for the evidence contract (v13-z a5bf62ba0593 WFB-003,
    # d40a839c7d8b). The data is already computed here; keep it as an artifact.
    rule_smoke)    echo "python3 scripts/rule_smoke.py $TASK --seeds 40 --json-out checks/${TASK}_${PHASE}_rule_smoke.json";;
    defect_lint)   echo "python3 scripts/generator_defect_lint.py $TASK --seeds 20 --bands easy,medium,hard --strict";;
    dist_gate)     echo "python3 scripts/generator_distribution_gate.py $TASK --seeds 40";;
    # Baselines collect WARN evidence without blocking, but WARN is explicitly
    # marked ADVISORY-OK so neither the console nor aggregate summary calls it
    # green. Repaired/non-before phases require a clean PASS: --strict promotes
    # strict-policy defects and --require-pass makes every remaining WARN fail.
    profile_floor) local pfj="checks/${TASK}_${PHASE}_profile_floor.json"
                   case "$PHASE" in
                     before*) echo "python3 scripts/canonical_profile_gate.py $TASK --json-out $pfj; c=\$?; if [ \$c -eq 0 ] && python3 -c \"import json,sys;a=json.load(open(sys.argv[1]))['audits'];sys.exit(0 if any(x.get('status')=='WARN' for x in a) else 1)\" $pfj; then echo 'ADVISORY-OK: canonical-profile WARN is nonblocking in a baseline, but is not green'; fi; exit \$c";;
                     *) echo "python3 scripts/canonical_profile_gate.py $TASK --strict --require-pass --min-band-support 1 --json-out $pfj";;
                   esac;;
    # The SEMANTIC companion to profile_floor (docs/SEMANTIC_GATE_CONTRACT.md).
    # profile_floor measures morphology marginals; this measures whether the
    # generated lesson identifies the RULE. Same strictness precedent: before*
    # collects baseline evidence, every other phase gates with --strict.
    #
    # --per-band 150 is measured, not guessed. The rarest LAWFUL witness cell in
    # the whole hooked corpus is 796907d6d950/template_size_6/hard at p=0.033;
    # at --per-band 12/20/30 that task WARNs ("fires in easy but never in
    # hard/medium") purely as a sampling artefact, at 60 it is clean but with
    # only 2 hits of margin, at 150 it has 7 hits and (1-p)^150 = 0.6%. Seeds
    # are pinned on (task, band, index), so a larger --per-band is a strict
    # SUPERSET of a smaller one: raising it can only ADD firings, never remove
    # them, so band-partial WARNs are monotonically non-increasing in the census
    # size. Cost measured over all 13 hooked generators: <=3.5s wall clock,
    # i.e. ~1% of the 300s per-stage cap. --lessons 12 keeps the Racket-bridge
    # half modest and still caught both genuinely-failing generators (11/12).
    #
    # NO_CONTRACT is ADVISORY, never blocking: ~3800 legacy generators declare
    # no hooks, and the gate exits 1 for a bare advisory under --strict. A stage
    # that fails for every un-migrated generator would be an unusable gate and
    # reviewers would learn to ignore it. So exit 1 is downgraded to pass ONLY
    # when every audit in the JSON is status NO_CONTRACT -- the LOUD advisory
    # still stands in the log. A real WARN (exit 1 with any non-NO_CONTRACT
    # audit) and any FAIL (exit 2) still fail the stage.
    # `--require-contract` is added in the AFTER phase only (2026-07-25). The
    # BEFORE phase must stay advisory: its job is to RECORD that the baseline
    # shipped without a contract, which is evidence, not a failure to fix.
    # The AFTER phase is the opposite — a returned candidate with no semantic
    # contract is unfinished work, and eight reviewers in one batch reported
    # that this stage printed green for exactly that state. Under
    # --require-contract the gate exits 2, so the ADVISORY-OK escape below
    # can no longer launder it.
    #
    # THE PROBE MUST RUN ON EXIT 0 AS WELL AS EXIT 1 (fixed 2026-07-25). It
    # used to fire only on exit 1, and that silently defeated the advisory
    # intent above: WITHOUT --strict, a NO_CONTRACT audit carries no errors, so
    # `generator_semantic_gate.py` returns 0, no ADVISORY-OK line is ever
    # written, and the summary files the stage under `green_stages`. The BEFORE
    # phase — the one phase whose whole job is to record "this baseline shipped
    # with no contract" — was therefore the one phase that reported it as a
    # pass.
    #
    # Two workers reported it independently in the same batch (48b7bc5c0b1e
    # WFB-001, 29a4c9396363 WFB-001) with matching evidence:
    # `154e19f36ba8_before_semantic_gate.log` says "NO_CONTRACT — hooks=none /
    # 0 pass, 1 no-contract", while `154e19f36ba8_before_battery_summary.json`
    # lists semantic_gate in green_stages with advisory_stages empty.
    #
    # It matters beyond one stage: every report headlines a before/after count
    # ("6 green -> 12 green"), so counting an unasked question as green
    # inflates the baseline and understates the repair. Exit 0 + all-NO_CONTRACT
    # now yields status `advisory`; exit 0 with a real contract stays green;
    # exit 2 under --require-contract stays failed.
    semantic_gate) local strict=""; case "$PHASE" in before*) ;; *) strict=" --strict --require-contract --require-rival-witness --require-shortcut-counterexample --rotate-query";; esac
                   if [ "$REQUIRE_ROTATIONS" = 1 ]; then strict="$strict --require-rotations-identifiable"; fi
                   if [ -n "$SCHEDULE_CENSUS" ]; then
                     local quoted_census; printf -v quoted_census '%q' "$SCHEDULE_CENSUS"
                     strict="$strict --schedule-census $quoted_census --schedule-seed $SCHEDULE_SEED"
                   fi
                   if [ "$ENUMERATE_SCHEDULE" = 1 ]; then strict="$strict --enumerate-schedule-period --schedule-seed $SCHEDULE_SEED"; fi
                   local sgj="checks/${TASK}_${PHASE}_semantic_gate.json"
                   echo "python3 scripts/generator_semantic_gate.py $TASK --per-band 200 --lessons 12$strict --json-out $sgj; c=\$?; { [ \$c -eq 0 ] || [ \$c -eq 1 ]; } && python3 -c \"import json,sys;a=json.load(open(sys.argv[1]))['audits'];sys.exit(0 if a and all(x['status']=='NO_CONTRACT' for x in a) else 1)\" $sgj && { echo 'ADVISORY-OK: no semantic contract declared -- advisory only, stage not blocking (see the LOUD line above)'; c=0; }; exit \$c";;
    diversity)     echo "python3 scripts/gen_diversity_probe.py --task-id $TASK --episodes 50 --no-append";;
    # Baselines retain legacy warning calibration, but expose a warning as an
    # advisory. A repaired/non-before generator must reject unknown keys: an
    # accepted typo makes the entire override contract unfalsifiable.
    override)      local ocj="checks/${TASK}_${PHASE}_override_results.json"
                   local occ="checks/${TASK}_${PHASE}_override_cases.json"
                   local compact=""; [ "$COMPACT_RESULTS" = 1 ] && compact=" --compact-results"; [ "$FULL_RESULTS" = 1 ] && compact=" --full-results"
                   local cases=""; [ "$COMPACT_RESULTS" = 1 ] || [ "$FULL_RESULTS" = 1 ] && cases=" --write-cases $occ"
                   case "$PHASE" in
                     before*) echo "python3 scripts/check_generator_override_contract.py $TASK --seeds 30$compact$cases --write-results $ocj; c=\$?; if [ \$c -eq 0 ] && python3 -c \"import json,sys;sys.exit(0 if json.load(open(sys.argv[1])).get('status')=='PASS_WITH_WARNINGS' else 1)\" $ocj; then echo 'ADVISORY-OK: override-contract warnings are nonblocking in a baseline, but are not green'; fi; exit \$c";;
                     *) echo "python3 scripts/check_generator_override_contract.py $TASK --seeds 30$compact --strict-unknown-key$cases --write-results $ocj";;
                   esac;;
    grammar)       echo "python3 scripts/grammar_gate.py";;
    racket_lint)   echo "python3 scripts/racket_linter.py --source canonical --task-id $TASK --show-each";;
    # SYNC_PATCH (adopted 2026-07-29, EWF-002059/002064): export
    # SYNC_PATCH=patches/racket__TASK.patch to audit the PROPOSED task-scoped
    # source sync against a staged temp copy — task-local workers reach
    # all-green without mutating the shared ledger; intake still applies +
    # replays for real.
    authority_sync) echo "python3 scripts/check_task_authority_sync.py $TASK --require-selected-exact-sync --verify-execution-parity${SYNC_PATCH:+ --patch $SYNC_PATCH} --json-out checks/${TASK}_${PHASE}_authority_sync.json";;
    *) echo ""; return 1;;
  esac
}
FAILED=()
# Turn a dangling `started` row into a terminal one. Called before every stage.
# `recovered_finished` is written ONLY when the source-bound .ok marker proves
# the child completed; otherwise the row is closed as `interrupted` with the
# status left explicitly unknown. Never invents an exit code.
reconcile_orphan() {
  local stage="$1" ok="$2" log="$3" receipt="$4"
  local index="checks/${TASK}_${PHASE}_commands.jsonl"
  [ -f "$index" ] || return 0
  local marker="" rcpt=""
  [ -f "$ok" ] && marker=$(cat "$ok" 2>/dev/null)
  [ -f "$receipt" ] && rcpt=$(cat "$receipt" 2>/dev/null)
  STAGE="$stage" INDEX="$index" LOGP="$log" MARKER="$marker" GENSHA="$GEN_SHA" \
  RECEIPT="$rcpt" OKPATH="$ok" \
  PHASE="$PHASE" TASK="$TASK" python3 - <<'PYEOF'
import json, os, datetime
index, stage = os.environ["INDEX"], os.environ["STAGE"]
started = finished = 0
for line in open(index, encoding="utf-8", errors="replace"):
    line = line.strip()
    if not line:
        continue
    try:
        row = json.loads(line)
    except ValueError:
        continue
    if row.get("stage") != stage:
        continue
    status = row.get("status")
    if status == "started":
        started += 1
    elif status in ("finished", "recovered_finished", "interrupted"):
        finished += 1
if started <= finished:
    raise SystemExit(0)
gensha = os.environ["GENSHA"]
# The CHILD's own receipt is the authority: it is renamed into place by the
# stage subshell itself, so it survives a parent kill AND records the true
# exit code — including a NONZERO one. The .ok marker only ever exists on
# success, so before receipts a completed-but-failing child was
# indistinguishable from one that never ran, and the stage was rerun.
receipt = None
try:
    receipt = json.loads(os.environ.get("RECEIPT") or "")
except ValueError:
    receipt = None
if isinstance(receipt, dict) and receipt.get("subject_sha16") == gensha:
    row = {
        "stage": stage, "phase": os.environ["PHASE"], "task": os.environ["TASK"],
        "utc_end": receipt.get("utc_end"),
        "status": "recovered_finished", "recovered": True, "from_receipt": True,
        "note": ("child-side receipt for this source: the stage ran to "
                 "completion; the parent was killed before journaling"),
        "log": os.environ["LOGP"], "subject_sha16": gensha,
        "exit": receipt.get("exit"), "timed_out": receipt.get("timed_out"),
    }
else:
    complete = os.environ.get("MARKER") and os.environ["MARKER"] == gensha
    row = {
        "stage": stage, "phase": os.environ["PHASE"], "task": os.environ["TASK"],
        "utc_end": datetime.datetime.now(datetime.timezone.utc)
            .strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": "recovered_finished" if complete else "interrupted",
        "recovered": True,
        "note": ("source-bound .ok marker matches: the child completed; the "
                 "parent was killed before journaling"
                 if complete else
                 "parent interrupted; child exit status unknown — inspect the log"),
        "log": os.environ["LOGP"], "subject_sha16": gensha,
    }
    if complete:
        row["exit"] = 0
with open(index, "a", encoding="utf-8") as handle:
    handle.write(json.dumps(row) + "\n")
# A recovered stage that genuinely succeeded must also get its .ok marker, or
# the very next run re-executes work the receipt just proved was done.
if row.get("status") == "recovered_finished" and row.get("exit") == 0:
    with open(os.environ["OKPATH"], "w", encoding="utf-8") as handle:
        handle.write(gensha)
print(f"RECONCILE {stage}: closed {started - finished} orphaned started row(s) "
      f"as {row['status']}"
      + (f" (child receipt, exit={row.get('exit')})" if row.get("from_receipt")
         else ""))
PYEOF
}
# --resume's import step, and the reason --resume is not just "run it again".
#
# reconcile_orphan (above) can only close a stage that left a dangling `started`
# row, i.e. one the parent got as far as announcing. The cases it cannot cover
# are exactly the ones workers hit: a parent killed BEFORE the provisional row,
# a journal that was never created because the kill landed in stage 1, or
# evidence carried over from an earlier invocation of the same source. Those
# stages have complete, source-bound proof on disk (a child receipt, or an .ok
# marker) and no journal row at all, so the next run silently re-executed them.
#
# This sweeps every stage once, imports that proof as an explicit
# `recovered_finished` row, and restores the .ok marker when the recovered exit
# was 0 — which is what makes the following loop restart at the first genuinely
# incomplete stage instead of at stage 1. Evidence stamped with a different
# subject is REFUSED, loudly, and the stage is left to re-run.
import_receipts() {
  I_TASK="$TASK" I_PHASE="$PHASE" I_SUBJECT="$GEN_SHA" I_RUN_ID="$RUN_ID" \
  I_STAGES="${STAGES[*]}" python3 - <<'PYEOF' || {
import datetime, json, os, sys

task = os.environ["I_TASK"]
phase = os.environ["I_PHASE"]
subject = os.environ["I_SUBJECT"]
stages = os.environ["I_STAGES"].split()
prefix = os.path.join("checks", "%s_%s_" % (task, phase))
journal = prefix + "commands.jsonl"

rows, malformed = [], 0
if os.path.exists(journal):
    with open(journal, encoding="utf-8", errors="replace") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except ValueError:
                malformed += 1
# Only a TERMINAL row that names this subject counts as "already journaled".
# An `interrupted` row does not: it explicitly records an unknown status, and
# a valid receipt supersedes it.
known = {row.get("stage") for row in rows
         if row.get("status") in ("finished", "recovered_finished")
         and row.get("subject_sha16") == subject}

now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
imported, stale, new_rows = [], [], []
for stage in stages:
    if stage in known:
        continue
    ok_path = "%s%s.ok" % (prefix, stage)
    receipt_path = "%s%s.receipt" % (prefix, stage)
    base = {"stage": stage, "phase": phase, "task": task,
            "status": "recovered_finished", "recovered": True,
            "imported_by": "resume", "run_id": os.environ["I_RUN_ID"],
            "subject_sha16": subject, "log": "%s%s.log" % (prefix, stage)}
    receipt = None
    if os.path.exists(receipt_path):
        try:
            with open(receipt_path, encoding="utf-8") as handle:
                receipt = json.loads(handle.read())
        except ValueError:
            receipt = None
            stale.append((stage, "receipt", "unparseable"))
        if isinstance(receipt, dict) and receipt.get("subject_sha16") != subject:
            stale.append((stage, "receipt", receipt.get("subject_sha16")))
            receipt = None
    if isinstance(receipt, dict):
        new_rows.append(dict(
            base, from_receipt=True, exit=receipt.get("exit"),
            timed_out=receipt.get("timed_out"), utc_end=receipt.get("utc_end"),
            note="imported by --resume from the child-side receipt for this "
                 "exact source"))
        imported.append((stage, receipt.get("exit"), "receipt"))
        continue
    marker = None
    if os.path.exists(ok_path):
        with open(ok_path, encoding="utf-8") as handle:
            marker = handle.read().strip()
        if marker != subject:
            stale.append((stage, "ok_marker", marker))
            marker = None
    if marker:
        new_rows.append(dict(
            base, from_marker=True, exit=0, utc_end=now,
            note="imported by --resume from the source-bound .ok marker"))
        imported.append((stage, 0, "ok_marker"))

if new_rows:
    with open(journal, "a", encoding="utf-8") as handle:
        for row in new_rows:
            line = json.dumps(row)
            json.loads(line)          # refuse to append anything unparseable
            handle.write(line + "\n")
for stage, code, _src in imported:
    if code == 0:
        with open("%s%s.ok" % (prefix, stage), "w", encoding="utf-8") as handle:
            handle.write(subject)

for stage, code, src in imported:
    print("RESUME-IMPORT %s: exit=%s from %s (journal row added%s)"
          % (stage, code, src, ", .ok restored" if code == 0 else ""))
for stage, artifact, found in stale:
    print("LOUD: --resume REFUSES stale %s for stage %s (subject %s != %s) — "
          "the stage will re-run" % (artifact, stage, found, subject),
          file=sys.stderr)
if malformed:
    print("LOUD: %d unparseable line(s) ignored in %s" % (malformed, journal),
          file=sys.stderr)
if not imported:
    print("RESUME-IMPORT: no completed-but-unjournaled stage evidence found")
PYEOF
    echo "LOUD: --resume receipt import FAILED — refusing to continue with an" \
         "unknown journal state." >&2
    return 1
  }
}
# Append ONE validated JSON row to the stage journal.
#
# The row used to be assembled with printf from a separately-substituted
# `cmd_json`. When that substitution came back empty the line was written
# anyway as `"cmd":,` — unparseable, and silently so: a worker found two
# corrupt rows for a stage whose own log showed a clean PASS (v13-z
# b6edfc119780 WFB-001). One json implementation builds the whole row, the
# row is parsed back before it is appended, and a journalling failure is LOUD
# instead of leaving a hole in the evidence.
#
# Fields arrive as J_* environment variables; empty ones are omitted.
journal_append() {
  local index="checks/${TASK}_${PHASE}_commands.jsonl"
  J_INDEX="$index" J_PHASE="$PHASE" J_TASK="$TASK" J_RUN_ID="$RUN_ID" \
  J_SUBJECT="$GEN_SHA" python3 - <<'PYEOF' || {
import json, os, sys

def opt(name, cast=str):
    raw = os.environ.get(name, "")
    return None if raw == "" else cast(raw)

row = {
    "stage": os.environ["J_STAGE"],
    "phase": os.environ["J_PHASE"],
    "task": os.environ["J_TASK"],
    "cmd": os.environ.get("J_CMD", ""),
    "utc_start": os.environ.get("J_UTC_START", ""),
    "status": os.environ["J_STATUS"],
    "run_id": os.environ["J_RUN_ID"],
    "subject_sha16": os.environ["J_SUBJECT"],
}
for key, env, cast in (
    ("utc_end", "J_UTC_END", str),
    ("duration_seconds", "J_DURATION", int),
    ("timeout_seconds", "J_TIMEOUT", float),
    ("kill_after_seconds", "J_KILL_AFTER", float),
    ("time_budget_seconds", "J_TIME_BUDGET", float),
    ("exit", "J_EXIT", int),
    ("log", "J_LOG", str),
):
    value = opt(env, cast)
    if value is not None:
        row[key] = value
if os.environ.get("J_TIMED_OUT", "") != "":
    row["timed_out"] = os.environ["J_TIMED_OUT"] == "true"
if os.environ.get("J_BUDGET_EXHAUSTED", ""):
    row["budget_exhausted"] = os.environ["J_BUDGET_EXHAUSTED"] == "true"
# The parent's death is recorded ALONGSIDE the gate result, never as it.
if os.environ.get("J_PARENT_SIGNAL", ""):
    row["parent_signal_exit"] = int(os.environ["J_PARENT_SIGNAL"])
    row["exit_from_child_receipt"] = True
# Backward-compatible alias kept for existing parsers.
if os.environ.get("J_STATUS") == "finished":
    row["generator_sha16"] = os.environ["J_SUBJECT"]

line = json.dumps(row)
json.loads(line)          # refuse to append anything unparseable
with open(os.environ["J_INDEX"], "a", encoding="utf-8") as handle:
    handle.write(line + "\n")
PYEOF
    echo "LOUD: battery journal append FAILED for stage '${J_STAGE:-?}'" \
         "(status ${J_STATUS:-?}) — evidence row NOT written." >&2
    return 1
  }
}

run_stage() {
  local stage="$1"
  local log="checks/${TASK}_${PHASE}_${stage}.log"
  local ok="checks/${TASK}_${PHASE}_${stage}.ok"
  local receipt="checks/${TASK}_${PHASE}_${stage}.receipt"
  # RECONCILE an orphaned `started` row before doing anything else. The
  # provisional row makes an external parent kill VISIBLE; four workers then
  # reported the follow-on problem — the orphan is never resolved, so an
  # index row stays ambiguous forever even after the stage demonstrably
  # completed (v13-y: 02fcd49e49d6, 42fb6b33deea, bd24325c2939, 5384b0fbe9e8).
  # If the .ok marker proves completion, say so explicitly; otherwise mark it
  # interrupted. Either way the row stops being a dangling `started`.
  reconcile_orphan "$stage" "$ok" "$log" "$receipt"
  # .ok markers are bound to the generator source hash (EWF-000389): a
  # marker from a previous source version never masks a re-run.
  if [ "$FRESH" = 1 ] && [ -f "$ok" ]; then
    rm -f "$ok"
    echo "FRESH $stage (--fresh: discarded inherited marker, re-running)"
  fi
  if [ -f "$ok" ] && [ "$(cat "$ok" 2>/dev/null)" = "$GEN_SHA" ]; then
    echo "SKIP  $stage (marker matches source $GEN_SHA)"
    return 0
  fi
  local cmd
  cmd=$(cmd_for "$stage") || { echo "ERROR unknown stage '$stage' (stages: ${STAGES[*]})" >&2; exit 2; }
  # A rerun after failure must not destroy the failed evidence (v13-v
  # WFB-001): rotate the prior log instead of overwriting it.
  [ -f "$log" ] && mv "$log" "$log.prev"
  echo "RUN   $stage -> ${BATTERY_DISPLAY_ROOT:-}$log"
  # Per-stage UTC timing/exit index (worker contract; EWF-000427/433/437):
  # one JSONL row per executed stage in checks/TASK_PHASE_commands.jsonl.
  # Direct native calls retain 300s/stage and 10s kill grace. Public callers
  # supply one remaining budget for the whole invocation; each stage uses
  # only what remains, with bounded kill grace before controller expiry.
  local cap=300 kill_after=10
  if [ -n "$BUDGET_DEADLINE" ]; then
    local budget_limits
    budget_limits=$(python3 -c 'import sys,time
remaining=max(0.0,float(sys.argv[1])-time.monotonic())
print(format(remaining,".12g"),format(min(10.0,remaining*.1),".12g"))' "$BUDGET_DEADLINE") || exit 2
    read -r cap kill_after <<< "$budget_limits"
    if [ "$cap" = 0 ]; then
      BUDGET_EXHAUSTED=1
      FAILED+=("$stage(time_budget)")
      J_STAGE="__budget__" J_STATUS="budget_exhausted" J_TIME_BUDGET="$TIME_BUDGET" \
        J_BUDGET_EXHAUSTED=true journal_append
      echo "TIME BUDGET exhausted before $stage; remaining stages not run" >&2
      return
    fi
  fi
  local ts0 ts1 t0 t1 code=0 timed_out=false
  echo "LIMIT $stage: ${cap}s remaining stage allowance, ${kill_after}s kill grace; total native budget=${TIME_BUDGET:-per-stage-default}"
  ts0=$(date -u +%Y-%m-%dT%H:%M:%SZ); t0=$(date +%s)
  # Provisional row BEFORE the child runs. If the host kills the parent after
  # the child finished, the completed stage still leaves a trace instead of
  # looking unexecuted — requested independently by 3 workers (v13-y
  # WFB-F678-001 / dc657616ec21 WFB-003 / e99db71ae23d WFB-601). A `started`
  # row with no matching terminal row == externally interrupted.
  J_STAGE="$stage" J_STATUS="started" J_CMD="$cmd" J_UTC_START="$ts0" \
    J_TIMEOUT="$cap" J_KILL_AFTER="$kill_after" J_TIME_BUDGET="$TIME_BUDGET" \
    journal_append
  # CHILD-SIDE TERMINAL RECEIPT (6 independent worker reports: v13-z
  # GFB-6A-001 / WFB-001 fe03db1e1459 / WFB-703 / WFB-1001 / WFB-001
  # 929a3e437ee4 / WFB-503). The parent's `finished` row is written only
  # AFTER the child returns, so a parent killed in that window loses a
  # completed stage. Here the stage subshell writes its own exit receipt and
  # renames it into place — rename(2) is atomic, so the receipt either does
  # not exist or is complete and correct. The parent below still journals
  # normally; the receipt is what reconcile_orphan reads when it cannot.
  rm -f "$receipt" "$receipt.tmp"
  # Backgrounded so `set -m` puts it in its own process group (see cleanup()),
  # then waited on immediately — behaviourally identical to a foreground run.
  bash -c '
    timeout -k "$7" "$6" bash -c "$1" >"$2" 2>&1
    c=$?
    to=false; { [ "$c" = 124 ] || [ "$c" = 137 ]; } && to=true
    # Built and validated by json.dumps, never by printf: a half-substituted
    # receipt would be worse than none, since reconcile_orphan trusts it to
    # close a stage (v13-z b6edfc119780 WFB-001).
    R_EXIT="$c" R_TO="$to" R_SUBJECT="$4" R_RUN_ID="$5" R_OUT="$3" \
    R_TIMEOUT="$6" R_KILL_AFTER="$7" R_TIME_BUDGET="$8" python3 - <<"PYEOF" \
      || echo "LOUD: stage receipt NOT written for $3 (exit was $c)" >&2
import json, os
row = {"exit": int(os.environ["R_EXIT"]),
       "utc_end": __import__("datetime").datetime.now(
           __import__("datetime").timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
       "timed_out": os.environ["R_TO"] == "true",
       "subject_sha16": os.environ["R_SUBJECT"],
       "run_id": os.environ["R_RUN_ID"],
       "timeout_seconds": float(os.environ["R_TIMEOUT"]),
       "kill_after_seconds": float(os.environ["R_KILL_AFTER"])}
if os.environ.get("R_TIME_BUDGET"):
    row["time_budget_seconds"] = float(os.environ["R_TIME_BUDGET"])
line = json.dumps(row)
json.loads(line)
tmp = os.environ["R_OUT"] + ".tmp"
with open(tmp, "w", encoding="utf-8") as handle:
    handle.write(line)
os.replace(tmp, os.environ["R_OUT"])   # atomic
PYEOF
    exit $c
  ' _ "$cmd" "$log" "$receipt" "$GEN_SHA" "$RUN_ID" "$cap" "$kill_after" "$TIME_BUDGET" &
  CHILD_PID=$!
  wait "$CHILD_PID" || code=$?
  CHILD_PID=""
  # THE CHILD'S RECEIPT OUTRANKS A PARENT-SIGNAL EXIT CODE. When the parent is
  # TERMed/INTed, `wait` returns 143/130 — which is a fact about the PARENT,
  # not about the gate. Journaling it as the stage's exit reported failures for
  # stages whose own logs said PASS (three workers, ids above). If the child
  # left a receipt for this exact subject, that receipt is what actually
  # happened; record the parent's death separately instead of overwriting the
  # gate result with it.
  local parent_signalled=""
  if { [ "$code" = 143 ] || [ "$code" = 130 ]; } && [ -f "$receipt" ]; then
    local recovered
    recovered=$(RCPT="$receipt" SUBJ="$GEN_SHA" python3 - <<'PYEOF' 2>/dev/null
import json, os
try:
    row = json.load(open(os.environ["RCPT"], encoding="utf-8"))
except Exception:
    raise SystemExit(1)
if row.get("subject_sha16") != os.environ["SUBJ"]:
    raise SystemExit(1)
print(int(row["exit"]))
PYEOF
    ) && {
      echo "NOTE  $stage: parent got signal $code but the child completed"        \
           "(receipt exit=$recovered) — recording the child's result" >&2
      parent_signalled="$code"
      code="$recovered"
    }
  fi
  ts1=$(date -u +%Y-%m-%dT%H:%M:%SZ); t1=$(date +%s)
  [ "$code" = 124 ] || [ "$code" = 137 ] && timed_out=true
  # Row fields satisfy the worker evidence contract directly (v13-x WFB:
  # duration/timeout/timed_out were previously reconstructed by hand).
  # subject_sha16 is the honest name for the generator+rule composite;
  # generator_sha16 is kept for backward-compatible parsing.
  J_STAGE="$stage" J_STATUS="finished" J_CMD="$cmd" J_UTC_START="$ts0" \
    J_UTC_END="$ts1" J_DURATION="$((t1 - t0))" J_TIMEOUT="$cap" \
    J_KILL_AFTER="$kill_after" J_TIME_BUDGET="$TIME_BUDGET" \
    J_TIMED_OUT="$timed_out" J_EXIT="$code" J_LOG="$log" \
    J_PARENT_SIGNAL="$parent_signalled" \
    journal_append
  if [ "$code" = 0 ]; then
    printf '%s' "$GEN_SHA" > "$ok"
    # Refresh the aggregate AFTER the marker lands, so a kill between stages
    # still leaves an on-disk summary that is at most one stage stale.
    battery_summary stage
    # A stage that exited 0 only because its finding was DOWNGRADED to advisory
    # must not read as PASS. `semantic_gate` exits 0 on NO_CONTRACT so the
    # ~3500 un-migrated legacy generators do not fail the gate — but the
    # console then said PASS next to a JSON saying NO_CONTRACT, and in a
    # before->after summary that reads as "semantics were evaluated and were
    # fine". Reported independently by five workers in one batch (996fc37f49d9
    # WFB-996004, 4b693000db29 WFB-003, 956425dc719c WFB-002, e245314f96d8
    # WFB-003, a5bf62ba0593 WFB-002). Same exit code, honest label.
    if grep -q "ADVISORY-OK" "$log" 2>/dev/null; then
      echo "ADVISORY  $stage (nonblocking finding — not green; read ${BATTERY_DISPLAY_ROOT:-}$log)"
    else
      echo "PASS  $stage"
    fi
  else
    echo "FAIL  $stage exit=$code — see ${BATTERY_DISPLAY_ROOT:-}$log (errors, then last lines)" >&2
    # Errors usually come first in a log; a bare tail hid the line that failed the stage.
    grep -m 5 -E '(^|[^A-Z])(ERR|ERROR)([^A-Z]|$)' "$log" >&2 || true
    tail -5 "$log" >&2
    if [ "$KEEP_GOING" = 1 ]; then
      FAILED+=("$stage:$code")
      battery_summary stage
    else
      # Fail-fast phases leave the battery here, so this IS the terminal write.
      battery_summary final
      exit "$code"
    fi
  fi
}
if [ "$RESUME" = 1 ]; then
  if [ -n "$ONLY" ]; then
    echo "LOUD: --resume restarts the whole battery at the first incomplete" \
         "stage and takes no STAGE argument." >&2
    exit 2
  fi
  echo "RESUME $TASK/$PHASE subject=$GEN_SHA run_id=$RUN_ID"
  import_receipts
fi
if [ -n "$ONLY" ]; then
  run_stage "$ONLY"
  battery_summary final
  # A failing single stage must exit nonzero even in keep-going phases
  # (EWF-000486/490): the failure was recorded, now surface it.
  if [ "${#FAILED[@]}" -gt 0 ]; then
    echo "STAGE FAILED: ${FAILED[*]}" >&2
    exit 1
  fi
else
  for s in "${STAGES[@]}"; do
    run_stage "$s"
    [ "$BUDGET_EXHAUSTED" = 1 ] && break
  done
  # ONE aggregate artifact + ONE aggregate exit code for the whole battery.
  if [ "$RESUME" = 1 ]; then battery_summary final print; else battery_summary final; fi
  echo "SUMMARY ${BATTERY_DISPLAY_ROOT:-}$SUMMARY"
  if [ "${#FAILED[@]}" -gt 0 ]; then
    if [ "$PHASE" = before ]; then
      echo "BASELINE COMPLETE with ${#FAILED[@]} failing stage(s): ${FAILED[*]} (all evidence collected)"
    elif [ "$PHASE" = audit ]; then
      echo "AUDIT CHECK FAILED: ${#FAILED[@]} failing stage(s): ${FAILED[*]} (all evidence collected)"
    else
      echo "AFTER CHECK FAILED: ${#FAILED[@]} failing stage(s): ${FAILED[*]} (all evidence collected)"
    fi
    exit 1
  fi
  case "$(summary_verdict)" in
    all_green)
      echo "ALL ${#STAGES[@]} stages green for $TASK ($PHASE)"
      ;;
    passed_with_advisories)
      echo "COMPLETE with nonblocking advisories for $TASK ($PHASE); read $SUMMARY"
      ;;
    *)
      echo "BATTERY NOT GREEN: read $SUMMARY" >&2
      exit 1
      ;;
  esac
fi
