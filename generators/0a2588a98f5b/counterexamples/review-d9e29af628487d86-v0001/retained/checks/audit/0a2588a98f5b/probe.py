from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

TASK_ID = "0a2588a98f5b"
OUT_DIR = Path("../checks/audit") / TASK_ID
GEN_PATH = Path("generators") / TASK_ID / "generator.py"
CANONICAL = Path("shared/data/canonical/puzzles.jsonl")


def load_generator():
    spec = importlib.util.spec_from_file_location(f"audit_{TASK_ID}", GEN_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_row() -> dict:
    for line in CANONICAL.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise FileNotFoundError(f"canonical row missing for {TASK_ID}")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def header_count(grid: list[list[int]]) -> int:
    return sum(value == 1 for value in grid[0])


GEN = load_generator()


def call_probe(**kwargs):
    try:
        grid = GEN.generate("audit-override-seed", 0, **kwargs)
        return {
            "status": "returned",
            "shape": [len(grid), len(grid[0])],
            "header_count": header_count(grid),
            "self_check": GEN.self_check(grid),
        }
    except Exception as exc:
        return {
            "status": "raised",
            "exception": type(exc).__name__,
            "message": str(exc),
        }


# Generate a lawful asymmetric body, then spell that same request using the
# canonical four-blue header rather than this sampler's noncanonical code 0.
code0 = GEN.generate("audit-code4-seed", 0, texture="code0")
code4 = copy.deepcopy(code0)
code4[0] = [0 for _ in code4[0]]
for column in range(4):
    code4[0][column] = 1

row = canonical_row()
OUT_DIR.mkdir(parents=True, exist_ok=True)
(OUT_DIR / "code4-input.json").write_text(json.dumps(code4, indent=2) + "\n")

report = {
    "schema": "arcpuzzles-audit-probe-preapply-v1",
    "task_id": TASK_ID,
    "generator_sha256": sha256(GEN_PATH),
    "canonical_written_solution": row.get("written_solution"),
    "declared_axes": GEN.AXES,
    "override_probes": {
        "declared_integer_zero": call_probe(symmetry_code=0, texture="plain"),
        "string_zero_coercion": call_probe(symmetry_code="0", texture="plain"),
        "forced_texture_overrides_code": call_probe(symmetry_code=3, texture="code0"),
        "unknown_axis": call_probe(unknown_axis=1),
        "lawful_dimension_outside_easy_band": call_probe(
            difficulty="easy", grid_h=18, grid_w=20
        ),
    },
    "canonical_code4_boundary": {
        "input_path": f"checks/audit/{TASK_ID}/code4-input.json",
        "header_count": header_count(code4),
        "self_check": GEN.self_check(code4),
        "python_mirror_output": GEN._mirror(code4),
    },
    "apply_command": {
        "cwd": "repo",
        "argv": [
            "python3", "-m", "arcpuzzles", "apply", TASK_ID,
            "--input", f"../checks/audit/{TASK_ID}/code4-input.json",
            "--check-generator-domain",
            "--out", f"../checks/audit/{TASK_ID}/code4-racket.json",
        ],
    },
}
(OUT_DIR / "probe-preapply.json").write_text(
    json.dumps(report, indent=2, sort_keys=True) + "\n"
)
print(json.dumps({
    "generator_sha256": report["generator_sha256"],
    "header_count": report["canonical_code4_boundary"]["header_count"],
    "self_check": report["canonical_code4_boundary"]["self_check"],
}, sort_keys=True))
