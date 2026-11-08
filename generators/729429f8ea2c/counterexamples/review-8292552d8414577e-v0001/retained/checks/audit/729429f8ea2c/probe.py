#!/usr/bin/env python3
"""Reproduce the 729429f8ea2c ignored-override counterexample."""
from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path
import subprocess
import sys

TASK_ID = "729429f8ea2c"
GENERATOR_SHA256 = "09baac92aa774e87bad3317a362bc4516a1b4e5152bf6f7da6fadeaef10fd2cb"
SEED = 123
SAMPLE_INDEX = 7
DIFFICULTY = "medium"

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
REPO = ROOT / "repo"
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "shared" / "runtime"))


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def grid_sha(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(payload).hexdigest()


def main() -> int:
    module = importlib.import_module(f"generators.{TASK_ID}.generator")
    source = REPO / "generators" / TASK_ID / "generator.py"
    assert file_sha(source) == GENERATOR_SHA256

    requests = [
        ("base", {}),
        ("warm", {"palette_kind": "warm"}),
        ("cool", {"palette_kind": "cool"}),
        ("unknown", {"definitely_not_an_axis": "x"}),
    ]
    rows = []
    grids = {}
    for name, overrides in requests:
        error = None
        try:
            grid = module.generate(
                SEED,
                SAMPLE_INDEX,
                difficulty=DIFFICULTY,
                **overrides,
            )
        except Exception as exc:  # pragma: no cover - counterexample records it
            grid = None
            error = f"{type(exc).__name__}: {exc}"
        grids[name] = grid
        rows.append(
            {
                "name": name,
                "overrides": overrides,
                "error": error,
                "grid_sha256": grid_sha(grid) if grid is not None else None,
                "grid": grid,
                "self_check": module.self_check(grid, difficulty=DIFFICULTY, meta={})
                if grid is not None
                else None,
            }
        )

    input_path = HERE / "input.json"
    input_path.write_text(json.dumps(grids["base"], separators=(",", ":")) + "\n")
    racket_path = HERE / "racket.json"
    apply_argv = [
        sys.executable,
        "run_with_racket.py",
        sys.executable,
        "-m",
        "arcpuzzles",
        "apply",
        TASK_ID,
        "--input",
        "../checks/audit/729429f8ea2c/input.json",
        "--out",
        "../checks/audit/729429f8ea2c/racket.json",
    ]
    if racket_path.exists():
        racket_path.unlink()
    completed = subprocess.run(apply_argv, cwd=ROOT, text=True, capture_output=True)
    if completed.returncode != 0:
        print(completed.stdout, end="")
        print(completed.stderr, end="", file=sys.stderr)
        return completed.returncode
    racket = json.loads(racket_path.read_text())

    hashes = {row["grid_sha256"] for row in rows}
    report = {
        "schema": "arc.audit-counterexample.v1",
        "status": "REPRODUCED" if len(hashes) == 1 and all(row["error"] is None for row in rows) else "FAILED",
        "task_id": TASK_ID,
        "generator_sha256": GENERATOR_SHA256,
        "rule_hash": racket.get("executed_rule_hash") or racket.get("catalog_rule_hash"),
        "rule_source_sha256": racket.get("rule_text_sha256"),
        "seed": SEED,
        "sample_index": SAMPLE_INDEX,
        "difficulty": DIFFICULTY,
        "declared_axes": sorted(module.AXES),
        "finding": "palette_kind is advertised but ignored; an unknown key is also accepted and ignored.",
        "all_four_inputs_identical": len(hashes) == 1,
        "unknown_key_accepted": rows[-1]["error"] is None,
        "cases": rows,
        "racket_apply": racket,
        "commands": [
            {"cwd": "packet_root", "argv": ["python3", "checks/audit/729429f8ea2c/probe.py"]},
            {"cwd": "packet_root", "argv": ["python3" if arg == sys.executable else arg for arg in apply_argv]},
        ],
        "domain": {
            "self_check_clean": all(row["self_check"] == [] for row in rows),
            "documented_normal_generator_domain": True,
        },
        "comparison": {
            "base_vs_warm": grids["base"] == grids["warm"],
            "base_vs_cool": grids["base"] == grids["cool"],
            "base_vs_unknown": grids["base"] == grids["unknown"],
        },
        "note": "No semantic rival is needed: the counterexample is that distinct exact-looking API requests materialize the identical lawful input. Racket output is retained to bind that input to the selected authority.",
    }
    out_path = HERE / "override-counterexample.json"
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: report[k] for k in ("status", "task_id", "generator_sha256", "rule_hash", "all_four_inputs_identical", "unknown_key_accepted")}, indent=2))
    return 0 if report["status"] == "REPRODUCED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
