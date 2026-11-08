"""Source-bound reproducer for review-23d35f89d6394ad3 audit findings."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2] / "repo"
OUT = Path(__file__).resolve().parent


def load(task: str):
    path = ROOT / f"generators/{task}/generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task}", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def grid_digest(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def call(module: Any, **kwargs: Any) -> dict[str, Any]:
    try:
        grid = module.generate(**kwargs)
        return {
            "status": "accepted",
            "shape": [len(grid), len(grid[0])],
            "grid_sha256": grid_digest(grid),
            "self_check": module.self_check(grid) if hasattr(module, "self_check") else None,
        }
    except Exception as exc:  # evidence should retain unexpected behavior
        return {"status": "rejected", "exception": type(exc).__name__, "message": str(exc)}


def main() -> None:
    f_task = "f3672f3f540b"
    f, f_path = load(f_task)
    f_calls = {
        "default": call(f, seed=0, sample_index=3, difficulty="easy"),
        "grid_h_10": call(f, seed=0, sample_index=3, difficulty="easy", grid_h=10),
        "grid_h_16": call(f, seed=0, sample_index=3, difficulty="easy", grid_h=16),
    }
    f_evidence = {
        "schema": "audit_reproduction/1",
        "task_id": f_task,
        "source_sha256": hashlib.sha256(f_path.read_bytes()).hexdigest(),
        "finding": "Advertised exact grid_h overrides are accepted but ignored.",
        "calls": f_calls,
        "assertions": {
            "requested_10_observed_8": f_calls["grid_h_10"].get("shape", [None])[0] == 8,
            "requested_16_observed_8": f_calls["grid_h_16"].get("shape", [None])[0] == 8,
            "both_overrides_equal_default": len({
                f_calls[name].get("grid_sha256") for name in f_calls
            }) == 1,
        },
        "official_check": "checks/audit/f3672f3f540b-override/checks/f3672f3f540b_audit_override.log",
    }
    (OUT / f"{f_task}-probe.json").write_text(
        json.dumps(f_evidence, indent=2, sort_keys=True) + "\n"
    )

    d_task = "d546d87fec58"
    d, d_path = load(d_task)
    invalid_calls = {
        "seed_bool": dict(seed=True, sample_index=0, difficulty="easy"),
        "seed_float": dict(seed=1.75, sample_index=0, difficulty="easy"),
        "seed_string": dict(seed="1", sample_index=0, difficulty="easy"),
        "sample_index_bool": dict(seed=1, sample_index=True, difficulty="easy"),
        "sample_index_negative": dict(seed=1, sample_index=-1, difficulty="easy"),
    }
    d_results = {name: call(d, **kwargs) for name, kwargs in invalid_calls.items()}
    d_evidence = {
        "schema": "audit_reproduction/1",
        "task_id": d_task,
        "source_sha256": hashlib.sha256(d_path.read_bytes()).hexdigest(),
        "finding": "generate accepts non-literal seed/sample_index scalars and negative sample_index.",
        "calls": [
            {"name": name, "arguments": invalid_calls[name], "result": d_results[name]}
            for name in invalid_calls
        ],
        "assertions": {
            "all_invalid_calls_accepted": all(
                result["status"] == "accepted" for result in d_results.values()
            )
        },
        "official_check": "checks/audit/d546d87fec58-defect/checks/d546d87fec58_audit_defect_lint.log",
    }
    (OUT / f"{d_task}-probe.json").write_text(
        json.dumps(d_evidence, indent=2, sort_keys=True) + "\n"
    )

    print(json.dumps({
        f_task: f_evidence["assertions"],
        d_task: d_evidence["assertions"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
