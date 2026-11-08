#!/usr/bin/env python3
"""Independent audit probe for 929a3e437ee4.

Loads the public generator, checks whether the adversarial input belongs to its
self-check domain, and evaluates the largest-connected-component rival.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from collections import defaultdict, deque
from pathlib import Path

HERE = Path(__file__).resolve().parent
PACKET = HERE.parents[2]
GEN_PATH = PACKET / "repo" / "generators" / "929a3e437ee4" / "generator.py"
INPUT_PATH = HERE / "input.json"
RACKET_PATH = HERE / "racket.json"
OUT_PATH = HERE / "counterexample.json"


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("audit_generator_929", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def largest_components(grid: list[list[int]]) -> dict[int, int]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    largest: dict[int, int] = defaultdict(int)
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            q = deque([(r, c)])
            seen.add((r, c))
            size = 0
            while q:
                rr, cc = q.popleft()
                size += 1
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        q.append((nr, nc))
            largest[color] = max(largest[color], size)
    return dict(largest)


def rival_output(grid: list[list[int]]) -> tuple[list[list[int]], dict[int, int]]:
    scores = largest_components(grid)
    best = max(scores.values())
    winners = [color for color, score in scores.items() if score == best]
    leftmost = {
        color: min(c for r, row in enumerate(grid) for c, value in enumerate(row) if value == color)
        for color in winners
    }
    winners.sort(key=lambda color: leftmost[color])
    return [[color for color in winners] for _ in range(best)], scores


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    module = load_module(GEN_PATH)
    grid = json.loads(INPUT_PATH.read_text())
    racket = json.loads(RACKET_PATH.read_text())
    actual = racket["results"][0]["output"]
    rival, component_scores = rival_output(grid)
    counts: dict[int, int] = defaultdict(int)
    for row in grid:
        for value in row:
            if value:
                counts[value] += 1
    errors = module.self_check(grid, difficulty="hard", meta={})
    report = {
        "schema": "arcpuzzles-audit-counterexample-v1",
        "task_id": "929a3e437ee4",
        "generator_sha256": sha256(GEN_PATH),
        "rule_hash": racket["executed_rule_hash"],
        "input_sha256": racket["results"][0]["input_sha256"],
        "input": grid,
        "actual_racket_output": actual,
        "rival_name": "largest_connected_component_count_instead_of_total_color_count",
        "rival_output": rival,
        "total_color_counts": {str(k): v for k, v in sorted(counts.items())},
        "largest_component_counts": {str(k): v for k, v in sorted(component_scores.items())},
        "outputs_differ": actual != rival,
        "generator_self_check_errors": errors,
        "belongs_to_documented_generator_domain": not errors,
        "domain_note": (
            "The exact input is outside the documented generator domain because color 2 has two "
            "4-connected components. It demonstrates that the single-component restriction prevents "
            "generated lessons from distinguishing total color count from largest-component count."
        ),
        "supported_racket_evidence": "checks/audit/929a3e437ee4/racket.json",
        "command": [
            "python3", "run_with_racket.py", "python3",
            "../checks/audit/929a3e437ee4/probe.py"
        ],
        "cwd": "packet_root",
    }
    if report["generator_sha256"] != "a187a88c3a47215c5ea74928f3dcea6327074e01724eb2b62154d65a13b089f0":
        raise SystemExit("unexpected generator bytes")
    if not report["outputs_differ"]:
        raise SystemExit("counterexample did not distinguish rival")
    if report["belongs_to_documented_generator_domain"]:
        raise SystemExit("adversarial input unexpectedly passed target self_check")
    OUT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "output": str(OUT_PATH),
        "actual": actual,
        "rival": rival,
        "self_check_errors": errors,
    }, indent=2))


if __name__ == "__main__":
    main()
