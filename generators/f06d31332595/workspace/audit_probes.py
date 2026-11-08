#!/usr/bin/env python3
"""Reproduce the two assignment-level adversarial audit counterexamples.

Run from the packet root through the Racket wrapper:

    python3 run_with_racket.py python3 \
      generators/f06d31332595/workspace/audit_probes.py

The script does not modify either audit target. It writes compact, hash-bound
JSON evidence under ``../checks/audit`` (relative to the repository runtime).
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import types
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
PACKET_ROOT = REPO.parent
RUNTIME = REPO / "shared/runtime"
TOOLS = REPO / "shared/tools"
OUT_DIR = PACKET_ROOT / "checks/audit"
sys.path.insert(0, str(RUNTIME))

# The packet stores this parser under shared/tools while rule_wrap imports its
# full-repository package name. Install a process-local alias; no files change.
scripts_pkg = types.ModuleType("scripts")
scripts_pkg.__path__ = []
sys.modules.setdefault("scripts", scripts_pkg)
comment_spec = importlib.util.spec_from_file_location(
    "scripts.comment_solutions", TOOLS / "comment_solutions.py"
)
if comment_spec is None or comment_spec.loader is None:
    raise RuntimeError("cannot load shared/tools/comment_solutions.py")
comment_module = importlib.util.module_from_spec(comment_spec)
sys.modules["scripts.comment_solutions"] = comment_module
comment_spec.loader.exec_module(comment_module)

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule


def load_module(task_id: str):
    path = REPO / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def load_rule(relative_path: str) -> tuple[str, Path]:
    path = REPO / relative_path
    raw = json.loads(path.read_text(encoding="utf-8"))["racket_target"]["raw_code"]
    return raw, path


def apply_racket(raw_rule: str, grid) -> list[list[int]]:
    bridge = RacketBridge()
    try:
        bridge.eval_text(f"(define audit_rule {wrap_rule(raw_rule)})")
        bridge.define_grid("audit_input", grid)
        return bridge.eval_text("(audit_rule audit_input)")
    finally:
        bridge.shutdown()


def normalized_hash12(raw_rule: str) -> str:
    return hashlib.sha256(" ".join(raw_rule.split()).encode()).hexdigest()[:12]


def write_74e83caa0660() -> dict:
    task = "74e83caa0660"
    module, generator_path = load_module(task)
    raw_rule, rule_path = load_rule(
        "shared/data/base/solutions/banks/ad4abc25f505/"
        "easy_70_expand_diagonal_pairs_into_xs__74e83caa0660.json"
    )
    seed, sample_index, difficulty = 17, 9, "medium"
    one = module.generate(seed, sample_index, difficulty=difficulty, n_pairs=1)
    eight = module.generate(seed, sample_index, difficulty=difficulty, n_pairs=8)
    default = module.generate(seed, sample_index, difficulty=difficulty)
    if not one == eight == default:
        raise AssertionError("n_pairs unexpectedly changed the generated grid")

    counts = Counter(value for row in one for value in row if value != 0)
    if len(counts) <= 1 or set(counts.values()) != {2}:
        raise AssertionError(f"probe seed did not expose multiple pairs: {counts}")
    actual = apply_racket(raw_rule, one)

    first_color = next(value for row in one for value in row if value != 0)
    cells = [
        (row, col)
        for row, values in enumerate(one)
        for col, value in enumerate(values)
        if value == first_color
    ]
    r0, r1 = min(row for row, _ in cells), max(row for row, _ in cells)
    c0, c1 = min(col for _, col in cells), max(col for _, col in cells)
    rival = [[0 for _ in row] for row in one]
    for offset in range(r1 - r0 + 1):
        rival[r0 + offset][c0 + offset] = first_color
        rival[r0 + offset][c1 - offset] = first_color
    if rival == actual:
        raise AssertionError("override-contract rival did not disagree")

    record = {
        "schema": "arcpuzzles-audit-counterexample-v1",
        "task_id": task,
        "finding": (
            "declared n_pairs axis is inert because generate consumes keyed "
            "label pairs instead of n_pairs"
        ),
        "generator_path": str(generator_path.relative_to(REPO)),
        "generator_sha256": hashlib.sha256(generator_path.read_bytes()).hexdigest(),
        "rule_source_path": str(rule_path.relative_to(REPO)),
        "rule_normalized_hash12": normalized_hash12(raw_rule),
        "probe_cwd": "packet_root",
        "runtime_cwd": "repo",
        "probe_command": [
            "python3", "run_with_racket.py", "python3",
            "generators/f06d31332595/workspace/audit_probes.py",
        ],
        "counterexample": {
            "seed": seed,
            "sample_index": sample_index,
            "difficulty": difficulty,
            "overrides_compared": [{"n_pairs": 1}, {"n_pairs": 8}, {}],
            "all_three_inputs_identical": True,
            "active_color_counts": dict(sorted(counts.items())),
            "observed_pair_count": len(counts),
            "requested_pair_count": 1,
            "validator_findings": module.self_check(one),
            "belongs_to_documented_normal_domain": True,
            "belongs_to_requested_override_subdomain": False,
            "input_grid": one,
            "actual_racket_output": actual,
            "rival_name": (
                "override-contract projection: expand only the first color "
                "pair as n_pairs=1 requests"
            ),
            "rival_output": rival,
        },
    }
    path = OUT_DIR / f"{task}-inert-n-pairs-axis.json"
    path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return {"path": str(path.relative_to(PACKET_ROOT)), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def max_distinct_rival(module, grid):
    analysis = module._analysis(grid)
    distinct = [len(record["counts"]) for record in analysis["chambers"]]
    winner = distinct.index(max(distinct))
    chamber = analysis["chambers"][winner]
    color = chamber["ordered_counts"][0][0]
    output = [row[:] for row in grid]
    for row, col in chamber["cells"]:
        if output[row][col] == 0:
            output[row][col] = color
    return output, winner, distinct


def write_6ecd8be24495() -> dict:
    task = "6ecd8be24495"
    module, generator_path = load_module(task)
    raw_rule, rule_path = load_rule(
        "shared/data/base/solutions/banks/8edfaf6db623/M104__6ecd8be24495.json"
    )

    draws = 3000
    correct = unique = unique_correct = 0
    for index in range(draws):
        difficulty = ("easy", "medium", "hard")[index % 3]
        grid = module.generate(100000 + index, index * 17 + 3, difficulty=difficulty)
        analysis = module._analysis(grid)
        distinct = [len(record["counts"]) for record in analysis["chambers"]]
        candidates = [i for i, value in enumerate(distinct) if value == max(distinct)]
        unique += int(len(candidates) == 1)
        unique_correct += int(
            len(candidates) == 1 and candidates[0] == analysis["winner_rank"]
        )
        correct += int(candidates[0] == analysis["winner_rank"])

    lesson_counts = {}
    for length in (3, 4, 5):
        survived = total = 0
        for seed in range(100):
            for start in range(20):
                total += 1
                survives = True
                for offset in range(length):
                    grid = module.generate(seed, start + offset, difficulty="medium")
                    analysis = module._analysis(grid)
                    distinct = [
                        len(record["counts"]) for record in analysis["chambers"]
                    ]
                    if distinct.index(max(distinct)) != analysis["winner_rank"]:
                        survives = False
                        break
                survived += int(survives)
        lesson_counts[str(length)] = {
            "survives": survived,
            "total": total,
            "rate": survived / total,
        }

    index = 45
    seed = 100000 + index
    sample_index = index * 17 + 3
    difficulty = ("easy", "medium", "hard")[index % 3]
    grid = module.generate(seed, sample_index, difficulty=difficulty)
    analysis = module._analysis(grid)
    rival_output, rival_rank, distinct = max_distinct_rival(module, grid)
    actual_python = module.expected_output(grid)
    actual_racket = apply_racket(raw_rule, grid)
    if actual_racket != actual_python:
        raise AssertionError("Python mirror disagrees with Racket authority")
    if rival_rank == analysis["winner_rank"] or rival_output == actual_racket:
        raise AssertionError("selected max-distinct counterexample no longer disagrees")

    record = {
        "schema": "arcpuzzles-audit-counterexample-v1",
        "task_id": task,
        "finding": (
            "max-distinct-colors shortcut is strongly correlated with the "
            "true most-total-seeds chamber"
        ),
        "generator_path": str(generator_path.relative_to(REPO)),
        "generator_sha256": hashlib.sha256(generator_path.read_bytes()).hexdigest(),
        "rule_source_path": str(rule_path.relative_to(REPO)),
        "rule_normalized_hash12": normalized_hash12(raw_rule),
        "probe_cwd": "packet_root",
        "runtime_cwd": "repo",
        "probe_command": [
            "python3", "run_with_racket.py", "python3",
            "generators/f06d31332595/workspace/audit_probes.py",
        ],
        "census": {
            "draws": draws,
            "seed_rule": (
                "seed=100000+i; sample_index=i*17+3; "
                "band=(easy,medium,hard)[i%3]"
            ),
            "first_max_distinct_correct": correct,
            "first_max_distinct_rate": correct / draws,
            "unique_max_distinct": unique,
            "unique_max_distinct_is_true_winner": unique_correct,
            "lesson_windows_medium": lesson_counts,
        },
        "counterexample": {
            "seed": seed,
            "sample_index": sample_index,
            "difficulty": difficulty,
            "overrides": {},
            "validator_findings": module.self_check(grid),
            "belongs_to_documented_domain": True,
            "true_winner_rank": analysis["winner_rank"],
            "rival_winner_rank": rival_rank,
            "seed_totals": [
                record["seed_total"] for record in analysis["chambers"]
            ],
            "distinct_color_counts": distinct,
            "input_grid": grid,
            "actual_racket_output": actual_racket,
            "rival_name": (
                "first chamber with the most distinct seed colors; fill with "
                "its local majority"
            ),
            "rival_output": rival_output,
        },
    }
    path = OUT_DIR / f"{task}-max-distinct-shortcut.json"
    path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return {"path": str(path.relative_to(PACKET_ROOT)), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    result = {
        "74e83caa0660": write_74e83caa0660(),
        "6ecd8be24495": write_6ecd8be24495(),
    }
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
