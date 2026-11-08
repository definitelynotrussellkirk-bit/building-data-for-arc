from __future__ import annotations
import hashlib, importlib.util, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT / "repo"
sys.path.insert(0, str(REPO / "shared/runtime"))


def load(tid):
    path = REPO / "generators" / tid / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{tid}", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module, path


def grid_hash(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def rule_hash(tid):
    path = REPO / "shared/data/canonical/puzzles.jsonl"
    for line in path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == tid:
            return hashlib.sha256(" ".join(row["program_solution"].split()).encode()).hexdigest()[:12]
    raise KeyError(tid)


def run_case(module, seed, sample_index, difficulty, overrides):
    try:
        grid = module.generate(seed, sample_index, difficulty=difficulty, **overrides)
    except Exception as exc:
        return {"status": "raised", "type": type(exc).__name__, "message": str(exc)}
    return {
        "status": "returned",
        "sha256": grid_hash(grid),
        "shape": [len(grid), len(grid[0])],
        "self_check": module.self_check(grid),
        "grid": grid,
    }


def main():
    configurations = {
        "e078230e5469": {
            "seed": 19,
            "sample_index": 3,
            "difficulty": "medium",
            "cases": {
                "baseline": {},
                "invalid_transform": {"transform": "bogus"},
                "palette_warm": {"palette_kind": "warm"},
                "palette_cool": {"palette_kind": "cool"},
                "unknown_axis": {"typo_axis": 123},
                "legal_global_size_rejected_in_easy": {"square_size": 6, "__difficulty": "easy"},
            },
        },
        "134c37edbf82": {
            "seed": 41,
            "sample_index": 6,
            "difficulty": "medium",
            "cases": {
                "baseline": {},
                "palette_warm": {"palette_kind": "warm"},
                "palette_cool": {"palette_kind": "cool"},
                "unknown_axis": {"typo_axis": 123},
                "legal_global_height_rejected_in_easy": {"grid_h": 18, "__difficulty": "easy"},
                "legal_global_width_rejected_in_hard": {"grid_w": 12, "__difficulty": "hard"},
            },
        },
    }
    report = {
        "schema": "arc-audit-override-contract-v1",
        "command": ["python3", "checks/audit/override_contract_probe.py"],
        "cwd": "packet_root",
        "tasks": {},
    }
    for tid, config in configurations.items():
        module, path = load(tid)
        task = {
            "generator_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "version": module.VERSION,
            "rule_hash": rule_hash(tid),
            "seed": config["seed"],
            "sample_index": config["sample_index"],
            "default_difficulty": config["difficulty"],
            "cases": {},
        }
        for name, raw in config["cases"].items():
            overrides = dict(raw)
            difficulty = overrides.pop("__difficulty", config["difficulty"])
            task["cases"][name] = {
                "difficulty": difficulty,
                "overrides": overrides,
                "result": run_case(module, config["seed"], config["sample_index"], difficulty, overrides),
            }
        report["tasks"][tid] = task
    out = ROOT / "checks/audit/override_contract_probe.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
