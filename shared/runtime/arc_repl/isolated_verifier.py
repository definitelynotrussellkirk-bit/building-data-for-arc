"""Fail-closed, fresh-process ARC verifier using only the existing Racket engine.

Use verify_candidate() from generation/repair workers. No GPU or model imports.
The process/resource boundary is reliability isolation, NOT a hostile-code jail.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import tempfile

from .bounded_process import run_bounded

SCHEMA = "arc-racket-isolated-verifier-v1"


@dataclass(frozen=True)
class Limits:
    wall_seconds: float = 45.0
    step_seconds: float = 3.0
    cpu_seconds: int = 30
    memory_mb: int = 2048
    max_source_bytes: int = 32768
    max_output_bytes: int = 1024 * 1024
    max_grid_side: int = 64
    max_pairs: int = 32

    def validate(self) -> None:
        for key, value in asdict(self).items():
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
                raise ValueError(f"{key} must be finite and positive")
            if key not in {"wall_seconds", "step_seconds"} and not isinstance(value, int):
                raise ValueError(f"{key} must be an integer")


def _failure(code: str, phase: str, message: str, **extra) -> dict:
    return {"schema": SCHEMA, "status": "fail", "backend": "racket",
            "error": {"code": code, "phase": phase, "message": message[:2000]}, **extra}


def _grid(value, side: int) -> bool:
    return (isinstance(value, list) and 0 < len(value) <= side
            and isinstance(value[0], list) and 0 < len(value[0]) <= side
            and all(isinstance(row, list) and len(row) == len(value[0])
                    and all(type(cell) is int and 0 <= cell <= 9 for cell in row) for row in value))


def _request_task(task: dict, limits: Limits) -> dict:
    if not isinstance(task, dict) or not isinstance(task.get("train"), list) or not task["train"]:
        raise ValueError("At least one labeled training pair is required")
    if not isinstance(task.get("test", []), list):
        raise ValueError("test must be a list")
    if len(task["train"]) + len(task.get("test", [])) > limits.max_pairs:
        raise ValueError("Too many examples for this verifier budget")
    # Send no unknown task metadata or hidden output labels into the worker.
    clean = {"train": [], "test": []}
    for split in clean:
        for pair in task.get(split, []):
            if not isinstance(pair, dict) or not _grid(pair.get("input"), limits.max_grid_side):
                raise ValueError(f"Invalid {split} input grid")
            item = {"input": pair["input"]}
            if split == "train":
                if not _grid(pair.get("output"), limits.max_grid_side):
                    raise ValueError("Invalid training output grid")
                item["output"] = pair["output"]
            clean[split].append(item)
    return clean


def verify_candidate(task: dict, source: str, *, racket_path: str,
                     source_language: str = "legacy", limits: Limits | None = None) -> dict:
    """Return a JSON-safe receipt; infrastructure failure is never a pass.

    ``status=pass`` means every demo matches and every query output is a valid
    grid, not that the unknown rule is proven. Optional hidden_exact is computed
    only in this parent; hidden labels never enter the worker request.
    """
    limits = limits or Limits()
    try:
        limits.validate()
        if source_language not in {"legacy", "v2"}:
            raise ValueError("source_language must be legacy or v2")
        if not isinstance(source, str) or not source.strip():
            raise ValueError("Nonempty source string required")
        if len(source.encode()) > limits.max_source_bytes:
            return _failure("source_limit", "cost", "Source exceeds configured byte budget")
        clean = _request_task(task, limits)
        if not racket_path:
            raise ValueError("An explicit activated RACKET_PATH is mandatory")
        binary = Path(racket_path).resolve(strict=True)
        if not binary.is_file() or not os.access(binary, os.X_OK):
            raise ValueError("RACKET_PATH must be an executable file")
    except (OSError, ValueError, TypeError) as exc:
        return _failure("invalid_request", "preflight", str(exc))
    if os.environ.get("ARC_FORCE_PYTHON_EVAL"):
        return _failure("backend_conflict", "preflight", "ARC_FORCE_PYTHON_EVAL conflicts with Racket-only verification")
    if os.environ.get("ARC_REPL_SKIP_BANK_HELPERS", "").lower() not in {"", "0", "false", "no"}:
        return _failure("semantics_conflict", "preflight", "ARC_REPL_SKIP_BANK_HELPERS changes the protected namespace")
    if os.name != "posix":
        return _failure("unsupported_platform", "preflight", "POSIX resource/process-group controls required")
    candidate_id = hashlib.sha256((source_language + "\0" + source).encode()).hexdigest()
    request = {"task": clean, "source": source, "source_language": source_language,
               "limits": asdict(limits), "candidate_id": candidate_id}
    env = dict(os.environ)
    env["RACKET_PATH"] = str(binary)
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1])
    # Keep numpy import costs and address-space use bounded per worker.
    for name in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
        env[name] = "1"
    with tempfile.TemporaryDirectory(prefix="arc-candidate-") as work:
        env["TMPDIR"] = work
        try:
            result = run_bounded([sys.executable, "-m", "arc_repl.isolated_verifier", "--worker"],
                                 input_text=json.dumps(request), env=env, cwd=work,
                                 timeout=limits.wall_seconds, max_output_bytes=limits.max_output_bytes)
        except (OSError, RuntimeError) as exc:
            return _failure("worker_start", "infrastructure", str(exc), candidate_id=candidate_id)
    process_info = {"worker_pid": result.pid, "seconds": result.seconds,
                    "returncode": result.returncode, "binary": str(binary)}
    if result.failure:
        return _failure(result.failure, "resource", "Worker exceeded parent-enforced budget",
                        candidate_id=candidate_id, process=process_info)
    if result.returncode:
        return _failure("worker_exit", "resource_or_runtime", result.stderr[-2000:] or f"Worker exited {result.returncode}",
                        candidate_id=candidate_id, process=process_info)
    try:
        report = json.loads(result.stdout)
        if (not isinstance(report, dict) or report.get("schema") != SCHEMA
                or report.get("candidate_id") != candidate_id or report.get("backend") != "racket"
                or report.get("binary") != str(binary) or report.get("status") not in {"pass", "fail"}):
            raise ValueError("Worker receipt identity/schema mismatch")
        if report["status"] == "pass":
            outputs = report.get("test_outputs")
            training = report.get("train_outputs")
            if (not isinstance(outputs, list) or len(outputs) != len(clean["test"])
                    or not all(_grid(g, limits.max_grid_side) for g in outputs)
                    or training != [p["output"] for p in clean["train"]]):
                raise ValueError("Worker success receipt has incomplete/incorrect grids")
            labels = [p.get("output") for p in task.get("test", [])]
            report["hidden_exact"] = outputs == labels if labels and all(g is not None for g in labels) else None
        elif not isinstance(report.get("error"), dict):
            raise ValueError("Failed receipt lacks an error")
    except (ValueError, TypeError) as exc:
        return _failure("protocol_error", "protocol", str(exc), candidate_id=candidate_id, process=process_info)
    report["process"] = process_info
    return report


def _limit_process(limits: Limits) -> dict:
    import resource
    settings = [("address_space_bytes", resource.RLIMIT_AS, limits.memory_mb * 1024 * 1024),
                ("cpu_seconds", resource.RLIMIT_CPU, limits.cpu_seconds),
                ("file_bytes", resource.RLIMIT_FSIZE, limits.max_output_bytes),
                ("core_bytes", resource.RLIMIT_CORE, 0)]
    effective = {}
    for name, key, requested in settings:
        _, hard = resource.getrlimit(key)
        cap = requested if hard == resource.RLIM_INFINITY else min(requested, hard)
        resource.setrlimit(key, (cap, cap))
        effective[name] = list(resource.getrlimit(key))
    return effective


def _worker(request: dict) -> dict:
    limits = Limits(**request["limits"])
    limits.validate()
    identity = {"candidate_id": request["candidate_id"], "binary": os.environ.get("RACKET_PATH"),
                "worker_pid": os.getpid()}
    phase = "resource_setup"
    executor = None
    try:
        effective = _limit_process(limits)
        identity["effective_rlimits"] = effective
        phase = "syntax"
        source = request["source"]
        if request["source_language"] == "v2":
            from .v2 import compile_source, V2CompileError
            try:
                source = compile_source(source).racket_source
            except V2CompileError as exc:
                return _failure(exc.code, exc.phase, str(exc), **identity)
        else:
            from .parser import parse_all, Symbol, tokenize
            tokens = tokenize(source)
            if len(tokens) > 4096:
                return _failure("node_limit", "cost", "Legacy token budget exceeded", **identity)
            forms = parse_all(source)
            if len(forms) != 1 or not isinstance(forms[0], list) or len(forms[0]) != 2 or forms[0][0] != Symbol("rule!"):
                return _failure("rule_wrapper", "syntax", "Exactly one (rule! expression) is required", **identity)
        from .executor import ArcExecutor
        from .builtins import Grid, _unwrap
        phase = "executor_init"
        executor = ArcExecutor(request["task"], auto_scan_on_load=False, use_racket=True)
        if executor._bridge is None or not executor.use_racket:
            return _failure("backend_mismatch", phase, "Racket required", **identity)
        identity["racket_pid"] = executor._bridge._proc.pid
        executor._bridge.timeout = limits.step_seconds
        phase = "rule_load"
        observation = executor.step(source)
        if observation.startswith("ERROR"):
            return _failure("rule_error", phase, observation, **identity)
        training, predictions = [], []
        for split, destination in (("train", training), ("test", predictions)):
            for index, pair in enumerate(request["task"][split]):
                phase = f"{split}:{index}"
                grid = Grid(pair["input"])
                # Invoke the exact application path used by test!/apply! once
                # per example; do not change the protected evaluator itself.
                output = _unwrap(executor._apply_rule(grid))
                if not _grid(output, limits.max_grid_side):
                    return _failure("malformed_output", phase, "Expected a nonempty rectangular ARC color grid", **identity)
                if _unwrap(grid) != pair["input"]:
                    return _failure("input_mutation", phase, "Rule mutated its input", **identity)
                destination.append(output)
                if split == "train" and output != pair["output"]:
                    return _failure("demo_mismatch", phase, "Exact training-grid mismatch", **identity)
        return {"schema": SCHEMA, "status": "pass", "backend": "racket", **identity,
                "train_outputs": training, "test_outputs": predictions,
                "input_purity": True, "limits": asdict(limits)}
    except MemoryError:
        return _failure("memory_limit", phase, "Worker exhausted its address-space budget", **identity)
    except (SyntaxError, RecursionError) as exc:
        return _failure("syntax_error", phase, str(exc), **identity)
    except Exception as exc:
        message = str(exc)
        code = "timeout" if "timed out" in message.lower() else "runtime_error"
        return _failure(code, phase, message, **identity)
    finally:
        if executor is not None:
            executor.close()


def main() -> int:
    if sys.argv[1:] != ["--worker"]:
        print("Use verify_candidate() from Python, or the harness Racket audit command.", file=sys.stderr)
        return 2
    try:
        request = json.loads(sys.stdin.read(4 * 1024 * 1024))
        report = _worker(request)
    except Exception as exc:
        report = _failure("invalid_worker_request", "protocol", str(exc))
    print(json.dumps(report, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
