"""Compare new generation with the retained predecessor runner in local snapshots."""
from __future__ import annotations

from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import nullcontext
import json
import math
from pathlib import Path
import sys
import tempfile
import threading
from typing import Any

from .catalog import Catalog, sha256
from .datasets import _dump, _identity
from .runtime import GenerationFailure, generate_in_runtime, prepare_runtime, run_process

_LOCAL = threading.local()


def _initialize(catalog: Catalog, directory: Path, task_ids: list[str]) -> None:
    """One copied snapshot per worker; every generator still executes in a new process."""
    stage = directory / str(threading.get_ident())
    prepare_runtime(catalog, stage, task_ids=task_ids)
    _LOCAL.stage = stage


def _one(catalog: Catalog, row: dict[str, Any], seed: int, difficulty: str,
         timeout: float) -> dict[str, Any]:
    result: dict[str, Any] = {"id": row["id"], "kind": row["kind"], "approved": row["approved"],
                              "generator_sha256": row["generator_sha256"], "seed": seed,
                              "difficulty": difficulty}
    with nullcontext(_LOCAL.stage) as stage:
        result["worker_sha256"] = sha256(stage / "arcpuzzles_worker.py")
        try:
            episode, = generate_in_runtime(stage, row, count=1, seed=seed, difficulty=difficulty,
                                            n_train=1, n_test=1, timeout=timeout)
            result["current"] = {"passed": True, "pair_hash": _identity({"train": episode["train"], "test": episode["test"]}),
                                 "rule_hash": episode["executed_rule_hash"], "rejections": episode["rejections"]}
        except (ValueError, RuntimeError) as exc:
            result["current"] = {"passed": False, "error": type(exc).__name__, "reason": str(exc)}
            if isinstance(exc, GenerationFailure):
                result["current"]["process"] = exc.run
        request = {"mode": "legacy_compare", "task_id": row["id"], "seed": seed,
                   "difficulty": difficulty, "n_train": 1, "n_test": 1}
        _dump(stage / "request.json", request)
        run = run_process([sys.executable, "-E", "-s", str(stage / "arcpuzzles_worker.py")], stage, timeout=timeout)
        if run["exit_code"] or run["timed_out"]:
            result["legacy"] = {"passed": False, "process": run}
        else:
            original = json.loads((stage / "legacy_result.json").read_text())
            result["legacy"] = {"passed": True, "pair_hash": _identity({"train": original["train"], "test": original["test"]}),
                                "rule_hash": original["rule_hash"], "rule_file": original["rule_file"]}
        current, legacy = result["current"], result["legacy"]
        if current["passed"] and legacy["passed"]:
            result["comparison"] = "equal" if current["pair_hash"] == legacy["pair_hash"] else "different"
        elif current["passed"]:
            result["comparison"] = "current_only"
        elif legacy["passed"]:
            result["comparison"] = "legacy_only"
        else:
            result["comparison"] = "both_failed"
    return result


def census(catalog: Catalog, output: str | Path, *, seed: int = 17, difficulty: str = "medium",
           filters: dict[str, Any] | None = None, workers: int = 4, timeout: float = 15,
           limit: int | None = None) -> dict[str, Any]:
    """Retain every outcome. Matching two pairs is compatibility evidence, not approval."""
    if type(workers) is not int or not 1 <= workers <= 8:
        raise ValueError("workers must be between 1 and 8")
    if difficulty not in {"easy", "medium", "hard"}:
        raise ValueError("Invalid difficulty")
    if type(seed) is not int or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("seed must be an integer and timeout must be finite and positive")
    rows = catalog.query(**dict(filters or {}, has_generator=True), limit=limit)
    if not rows:
        raise ValueError("No generators selected")
    root = Path(output).resolve()
    root.mkdir(parents=True, exist_ok=False)
    _dump(root / "plan.json", {"seed": seed, "difficulty": difficulty, "timeout_per_route": timeout,
                              "generators": [r["id"] for r in rows], "workers": workers})
    counts: Counter[str] = Counter()
    approved_counts: Counter[str] = Counter()
    with tempfile.TemporaryDirectory(prefix="arcpuzzles-census-") as directory, \
            (root / "results.jsonl").open("x") as handle, \
            ThreadPoolExecutor(max_workers=workers, initializer=_initialize,
                               initargs=(catalog, Path(directory), [r["id"] for r in rows])) as pool:
        futures = {pool.submit(_one, catalog, row, seed, difficulty, timeout): row for row in rows}
        try:
            for completed, future in enumerate(as_completed(futures), 1):
                try:
                    result = future.result()
                except Exception as exc:
                    result = {"id": futures[future]["id"], "approved": futures[future]["approved"],
                              "comparison": "infrastructure_error", "error": type(exc).__name__, "reason": str(exc)}
                counts[result["comparison"]] += 1
                if result["approved"]:
                    approved_counts[result["comparison"]] += 1
                handle.write(json.dumps(result) + "\n")
                handle.flush()
                summary = {"schema": "arcpuzzles-generation-census-v1", "completed": completed, "requested": len(rows),
                           "status": "complete" if completed == len(rows) else "running", "counts": dict(counts),
                           "approved_counts": dict(approved_counts), "scope": "one seed, one difficulty, one train and one test pair",
                           "baseline": "retained predecessor runner and authorities in this repository; no predecessor execution"}
                _dump(root / "summary.json", summary)
                if completed % 50 == 0 or completed == len(rows):
                    print(f"Census {completed}/{len(rows)}: {dict(counts)}", flush=True)
        except BaseException:
            for future in futures:
                future.cancel()
            raise
    return summary
