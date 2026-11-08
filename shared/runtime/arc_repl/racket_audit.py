"""CPU-only deployment gate for portable Racket, concurrency and failure isolation.

python -m arc_repl.racket_audit --bundle /path/racket-bundle --out audit.json
Add --require-kaggle-mount on Kaggle. Local permission-mode tests are controls,
not evidence about the currently uploaded dataset.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import hashlib
import json
import multiprocessing
import os
from pathlib import Path
import subprocess
import time

from .isolated_verifier import Limits, verify_candidate
from .runtime_activation import activate_bundle, tree_sha256
from .bounded_process import run_bounded


def _identity(g):
    return [row[:] for row in g]


def _flip(g):
    return [list(reversed(row)) for row in g]


def _transpose(g):
    return [list(row) for row in zip(*g)]


def _task(transform, seed=0):
    a = [[(1+seed)%10, 2, 0], [3, (4+seed)%10, 5]]
    b = [[(6+seed)%10, 7], [8, (9+seed)%10], [1, 2]]
    return {"train": [{"input": a, "output": transform(a)}],
            "test": [{"input": b, "output": transform(b)}]}


def _spawn_probe(queue):
    binary = os.environ.get("RACKET_PATH", "")
    try:
        result = subprocess.run([binary, "-e", '(displayln (getenv "RACKET_PATH"))'],
                                capture_output=True, text=True, timeout=15)
        queue.put({"pid": os.getpid(), "environment": binary,
                   "racket_environment": result.stdout.strip(), "returncode": result.returncode})
    except Exception as exc:
        queue.put({"pid": os.getpid(), "error": str(exc)})


def run_audit(bundle: Path, cache: Path, *, workers: int = 4,
              require_kaggle_mount: bool = False) -> dict:
    if not 1 <= workers <= 8:
        raise ValueError("Use between 1 and 8 CPU-only verifier workers")
    bundle = Path(bundle).resolve()
    started = time.monotonic()
    report = {"schema": "arc-racket-deployment-audit-v1", "cases": [], "limitations": [
        "POSIX per-process limits and process-group cleanup are reliability controls, not a hostile-code sandbox.",
        "Memory rejection tests insufficient startup budget, not a complete in-flight allocation stress test.",
        "This bounded fixture suite does not establish parity for the entire ARC rule corpus."]}
    try:
        before = tree_sha256(bundle)
        binary = activate_bundle(bundle, cache)
        mount_readonly = bool(os.statvfs(bundle).f_flag & getattr(os, "ST_RDONLY", 1))
        uploaded_mount = bundle.is_relative_to(Path("/kaggle/input")) and mount_readonly
        report["runtime"] = {"source": str(bundle), "binary": str(binary), "tree_sha256": before,
                             "mount_readonly": mount_readonly, "uploaded_mount_tested": uploaded_mount,
                             "version": subprocess.check_output([str(binary), "--version"], text=True).strip()}
        here = Path(__file__).resolve().parent
        report["semantics"] = {
            "executor_sha256": hashlib.sha256((here / "executor.py").read_bytes()).hexdigest(),
            "bridge_sha256": hashlib.sha256((here / "racket_bridge.py").read_bytes()).hexdigest(),
            "prelude_tree_sha256": tree_sha256(here / "racket_prelude"),
            "python": os.sys.version,
            "skip_bank_helpers": os.environ.get("ARC_REPL_SKIP_BANK_HELPERS"),
            "force_python": os.environ.get("ARC_FORCE_PYTHON_EVAL"),
        }
        limits = Limits()
        cases = []
        for name, transform, legacy, v2 in (
            ("identity", _identity, "(rule! (lambda (g) g))", "(rule! input)"),
            ("flip", _flip, "(rule! (lambda (g) (flip-lr g)))", "(rule! (mirror input LR))"),
            ("transpose", _transpose, "(rule! (lambda (g) (transpose g)))", "(rule! (transpose input))")):
            for language, rule in (("legacy", legacy), ("v2", v2)):
                for seed in (0, 3):
                    cases.append((f"{name}_{language}_{seed}", _task(transform, seed), rule, language, limits, "pass", None))
        cases += [
            ("syntax", _task(_identity), "(rule! (lambda (g) g)", "legacy", limits, "fail", {"syntax_error"}),
            ("v2_cost", _task(_identity), "(rule! (scale-up input 17))", "v2", limits, "fail", {"E_SCALE_BOUND"}),
            ("scalar_output", _task(_identity), "(rule! (lambda (g) 7))", "legacy", limits, "fail", {"malformed_output"}),
            ("empty_output", _task(_identity), "(rule! (lambda (g) (list)))", "legacy", limits, "fail", {"malformed_output"}),
            ("wrong_demo", _task(_flip), "(rule! (lambda (g) g))", "legacy", limits, "fail", {"demo_mismatch"}),
            ("finite_sleep_timeout", _task(_identity), "(rule! (lambda (g) (begin (sleep 0.3) g)))", "legacy", replace(limits, step_seconds=0.05), "fail", {"timeout"}),
            ("memory_startup_budget", _task(_identity), "(rule! (lambda (g) g))", "legacy", replace(limits, memory_mb=16), "fail", None),
        ]
        def execute(case):
            name, task, source, language, budget, status, codes = case
            result = verify_candidate(task, source, racket_path=str(binary), source_language=language, limits=budget)
            passed = (result["status"] == status and (status != "pass" or result.get("hidden_exact") is True)
                      and (codes is None or result.get("error", {}).get("code") in codes))
            return {"name": name, "passed": passed, "expected_status": status, "result": result}
        with ThreadPoolExecutor(max_workers=workers) as pool:
            report["cases"] = list(pool.map(execute, cases))
        # A failed candidate must not poison a subsequent fresh worker.
        recovery = verify_candidate(_task(_flip), "(rule! (lambda (g) (flip-lr g)))", racket_path=str(binary))
        report["cases"].append({"name": "post_failure_recovery", "passed": recovery.get("hidden_exact") is True, "result": recovery})
        ctx = multiprocessing.get_context("spawn")
        queue = ctx.Queue()
        children = [ctx.Process(target=_spawn_probe, args=(queue,)) for _ in range(workers)]
        for child in children:
            child.start()
        spawn_rows = []
        try:
            for _ in children:
                spawn_rows.append(queue.get(timeout=25))
        finally:
            for child in children:
                child.join(timeout=3)
                if child.is_alive():
                    child.terminate(); child.join(timeout=3)
            queue.close(); queue.join_thread()
        report["spawn_propagation"] = spawn_rows
        report["cases"].append({"name": "spawn_environment", "passed": len(spawn_rows) == workers and all(
            x.get("environment") == str(binary) == x.get("racket_environment") and x.get("returncode") == 0 for x in spawn_rows)})
        # Namespace checks use trusted setup, not a sandbox-escape fixture.
        from .executor import ArcExecutor
        with ArcExecutor(_task(_identity), use_racket=True) as first:
            first._bridge.eval_text("(define review-local-marker 7)")
            with ArcExecutor(_task(_identity), use_racket=True) as second:
                absent = False
                try:
                    second._bridge.eval_text("review-local-marker")
                except Exception as exc:
                    absent = "undefined" in str(exc) or "unbound" in str(exc)
                report["cases"].append({"name": "independent_namespaces", "passed": absent,
                                         "pids": [first._bridge._proc.pid, second._bridge._proc.pid]})
        quiet = run_bounded([os.sys.executable, "-c", "import time; time.sleep(0.3)"], timeout=0.05)
        report["cases"].append({"name": "quiet_parent_timeout", "passed": quiet.failure == "timeout", "seconds": quiet.seconds})
        after = tree_sha256(bundle)
        report["cases"].append({"name": "source_unchanged", "passed": before == after})
        successes = [x["result"] for x in report["cases"] if x.get("result", {}).get("status") == "pass"]
        report["cases"].append({"name": "unique_candidate_processes", "passed": len(successes) == len({x["worker_pid"] for x in successes}) == len({x["racket_pid"] for x in successes}), "successful_candidates": len(successes)})
        report["passed"] = sum(x["passed"] for x in report["cases"])
        report["total"] = len(report["cases"])
        controls_pass = report["passed"] == report["total"]
        report["status"] = "pass" if controls_pass and uploaded_mount else "partial" if controls_pass else "fail"
        report["gate_pass"] = controls_pass and (uploaded_mount or not require_kaggle_mount)
        if not uploaded_mount:
            report["limitations"].append("Actual uploaded read-only Kaggle bundle not verified: this is a local runtime control.")
    except Exception as exc:
        report.update(status="fail", gate_pass=False, error={"type": type(exc).__name__, "message": str(exc)})
    report["seconds"] = time.monotonic() - started
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--cache", type=Path, default=Path("/tmp/arc-racket-audit-cache"))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--require-kaggle-mount", action="store_true")
    args = parser.parse_args()
    report = run_audit(args.bundle, args.cache, workers=args.workers, require_kaggle_mount=args.require_kaggle_mount)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": report["status"], "gate_pass": report["gate_pass"], "passed": report.get("passed"), "total": report.get("total"), "out": str(args.out)}))
    return 0 if report["gate_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
