#!/usr/bin/env python3
"""Findings-only probes for the two immutable audit targets."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import types
from pathlib import Path

PACKET_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PACKET_ROOT / "repo"
SHARED = REPO_ROOT / "shared"
sys.path.insert(0, str(SHARED / "runtime"))
scripts_package = types.ModuleType("scripts")
scripts_package.__path__ = [str(SHARED / "tools")]
sys.modules.setdefault("scripts", scripts_package)

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule


def load_generator(task_id: str):
    path = REPO_ROOT / f"generators/{task_id}/generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_row(task_id: str) -> dict:
    path = SHARED / "data/canonical/puzzles.jsonl"
    for line in path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == task_id:
            return row
    raise KeyError(task_id)


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, separators=(",", ":")).encode()).hexdigest()[:16]


def grid_literal(grid: list[list[int]]) -> str:
    rows = " ".join("(" + " ".join(map(str, row)) + ")" for row in grid)
    return f"'({rows})"


def apply_rule(src: str, grid: list[list[int]]) -> list[list[int]]:
    bridge = RacketBridge(max_calls_before_restart=16)
    try:
        return bridge.eval_text(f"({wrap_rule(src)} {grid_literal(grid)})")
    finally:
        bridge.shutdown()


def audit_a5() -> dict:
    task_id = "a5b0638997f5"
    gen = load_generator(task_id)
    canonical = canonical_row(task_id)
    generated_legend_lengths = []
    sample_hashes = []
    for difficulty in ("easy", "medium", "hard"):
        for seed in range(8):
            for sample_index in range(4):
                grid = gen.generate(seed, sample_index, difficulty=difficulty)
                generated_legend_lengths.append(
                    len([v for v in grid[0] if v not in (0, 5)])
                )
                sample_hashes.append(digest(grid))
    canonical_legend_lengths = [
        len([v for v in pair["input"][0] if v not in (0, 5)])
        for pair in [*canonical["train"], *canonical["test"]]
    ]
    override_outputs = {
        kind: gen.generate(11, 2, difficulty="medium", palette_kind=kind)
        for kind in gen.PALETTE_KINDS
    }
    texture_outputs = {
        kind: gen.generate(11, 2, difficulty="medium", texture=kind)
        for kind in gen.HELPFUL_TEXTURES
    }
    return {
        "task_id": task_id,
        "sample_count": len(generated_legend_lengths),
        "sample_seed_range": [0, 7],
        "sample_index_range": [0, 3],
        "difficulties": ["easy", "medium", "hard"],
        "generator_sha256": hashlib.sha256(
            (REPO_ROOT / f"generators/{task_id}/generator.py").read_bytes()
        ).hexdigest(),
        "generated_legend_lengths": sorted(set(generated_legend_lengths)),
        "canonical_legend_lengths": canonical_legend_lengths,
        "palette_kind_output_hashes": {k: digest(v) for k, v in override_outputs.items()},
        "palette_kind_unique_outputs": len({digest(v) for v in override_outputs.values()}),
        "helpful_texture_output_hashes": {k: digest(v) for k, v in texture_outputs.items()},
        "helpful_texture_unique_outputs": len({digest(v) for v in texture_outputs.values()}),
        "unique_generated_inputs": len(set(sample_hashes)),
    }


def audit_b27() -> dict:
    task_id = "b27ef5e054f4"
    gen = load_generator(task_id)
    canonical = canonical_row(task_id)
    generated = []
    collision_witnesses = 0
    for difficulty in ("easy", "medium", "hard"):
        for seed in range(16):
            for sample_index in range(6):
                grid = gen.generate(seed, sample_index, difficulty=difficulty)
                generated.append(digest(grid))
                by_col: dict[int, int] = {}
                for r, row in enumerate(grid):
                    for c, value in enumerate(row):
                        if value == 2:
                            by_col[c] = by_col.get(c, 0) + 1
                if any(count >= 2 for count in by_col.values()):
                    collision_witnesses += 1

    adversarial = [
        [0, 0, 2, 0, 2],
        [0, 0, 0, 0, 0],
        [0, 0, 2, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 5, 0, 0],
    ]
    self_check = gen.self_check(adversarial, difficulty="medium")
    output = apply_rule(canonical["program_solution"], adversarial)
    red_input = [[r, c] for r, row in enumerate(adversarial) for c, v in enumerate(row) if v == 2]
    red_output = [[r, c] for r, row in enumerate(output) for c, v in enumerate(row) if v == 2]
    return {
        "task_id": task_id,
        "sample_count": len(generated),
        "sample_seed_range": [0, 15],
        "sample_index_range": [0, 5],
        "difficulties": ["easy", "medium", "hard"],
        "generator_sha256": hashlib.sha256(
            (REPO_ROOT / f"generators/{task_id}/generator.py").read_bytes()
        ).hexdigest(),
        "unique_generated_inputs": len(set(generated)),
        "generated_same_column_red_collision_witnesses": collision_witnesses,
        "adversarial_input": adversarial,
        "adversarial_input_sha256_16": digest(adversarial),
        "adversarial_self_check": self_check,
        "adversarial_red_input_positions": red_input,
        "adversarial_red_output_positions": red_output,
        "adversarial_output": output,
        "stack_created_above_blocker": [4, 2] in red_output and [5, 2] in red_output,
    }


def main() -> int:
    report = {
        "schema": "arc-audit-probes-v1",
        "a5b0638997f5": audit_a5(),
        "b27ef5e054f4": audit_b27(),
    }
    out = PACKET_ROOT / "checks/audit_probes.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(out)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
