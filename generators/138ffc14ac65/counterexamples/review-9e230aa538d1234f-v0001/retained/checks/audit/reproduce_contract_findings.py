#!/usr/bin/env python3
"""Reproduce the two assigned audit findings without private runner imports."""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

PACKET_ROOT = Path(__file__).resolve().parents[2]
REPO = PACKET_ROOT / "repo"
for path in (REPO, REPO / "src", REPO / "shared" / "runtime"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))


def digest_grid(grid: Any) -> str:
    payload = json.dumps(grid, separators=(",", ":"), sort_keys=False).encode()
    return hashlib.sha256(payload).hexdigest()


def load(task_id: str):
    path = REPO / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def capture_call(module: Any, *, difficulty: str, overrides: dict[str, Any]) -> dict[str, Any]:
    try:
        grid = module.generate(1, 0, difficulty=difficulty, **overrides)
    except Exception as exc:  # exact public-call behavior is the evidence
        return {"status": "raised", "type": type(exc).__name__, "message": str(exc)}
    return {
        "status": "returned",
        "shape": [len(grid), len(grid[0])],
        "grid_sha256": digest_grid(grid),
        "self_check": module.self_check(grid),
    }


def audit_94ac5008ffdb() -> dict[str, Any]:
    task_id = "94ac5008ffdb"
    module, path = load(task_id)
    source = path.read_text(encoding="utf-8")
    texture_outputs = {
        texture: capture_call(module, difficulty="medium", overrides={"texture": texture})
        for texture in module.HELPFUL_TEXTURES
    }
    degenerate = module.generate(1, 0, difficulty="medium", texture="missing_color")
    return {
        "schema": "arcpuzzles-audit-contract-repro-v1",
        "task_id": task_id,
        "generator_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "command": ["python3", "checks/audit/reproduce_contract_findings.py"],
        "cwd": "packet_root",
        "top_level_self_check_definitions": sum(
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "self_check"
            for node in ast.parse(source).body
        ),
        "helpful_texture_outputs": texture_outputs,
        "distinct_helpful_texture_grids": len(
            {item.get("grid_sha256") for item in texture_outputs.values() if item["status"] == "returned"}
        ),
        "missing_color_self_check_with_matching_meta": module.self_check(
            degenerate, meta={"texture": "missing_color"}
        ),
        "finding": (
            "All four advertised helpful texture values are behaviorally identical for the exact same "
            "seed/index, and the later duplicate self_check overrides the earlier degenerate-texture bypass."
        ),
    }


def audit_138ffc14ac65() -> dict[str, Any]:
    task_id = "138ffc14ac65"
    module, path = load(task_id)
    texture_outputs = {
        texture: capture_call(module, difficulty="medium", overrides={"texture": texture})
        for texture in module.HELPFUL_TEXTURES
    }
    override_calls = {
        "easy_grid_h_14": capture_call(module, difficulty="easy", overrides={"grid_h": 14}),
        "easy_seed_count_8": capture_call(module, difficulty="easy", overrides={"seed_count": 8}),
        "easy_seed_count_1": capture_call(module, difficulty="easy", overrides={"seed_count": 1}),
    }
    return {
        "schema": "arcpuzzles-audit-contract-repro-v1",
        "task_id": task_id,
        "generator_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "command": ["python3", "checks/audit/reproduce_contract_findings.py"],
        "cwd": "packet_root",
        "declared_axis_domains": {
            "grid_h": module.AXES["grid_h"]["valid"],
            "seed_count": module.AXES["seed_count"]["valid"],
        },
        "override_calls": override_calls,
        "helpful_texture_outputs": texture_outputs,
        "distinct_helpful_texture_grids": len(
            {item.get("grid_sha256") for item in texture_outputs.values() if item["status"] == "returned"}
        ),
        "finding": (
            "Publicly declared grid_h and seed_count values crash in easy mode, and all four "
            "advertised helpful texture values are behaviorally identical for the exact same seed/index."
        ),
    }


def main() -> int:
    results = [audit_94ac5008ffdb(), audit_138ffc14ac65()]
    for result in results:
        out = PACKET_ROOT / "checks" / "audit" / result["task_id"] / "contract_repro.json"
        out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(results, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
