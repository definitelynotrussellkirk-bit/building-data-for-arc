#!/usr/bin/env python3
"""Build source-bound adversarial lesson witnesses for the assigned audit targets."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

from arcpuzzles import Catalog

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT / "repo"
AUDIT_ROOT = ROOT / "checks" / "audit"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_generator(task_id: str):
    path = REPO / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_target_{task_id}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def different_cells(left: list[list[int]], right: list[list[int]]) -> list[list[int]]:
    if len(left) != len(right) or any(len(a) != len(b) for a, b in zip(left, right)):
        return [[-1, -1, len(left), len(right)]]
    return [
        [r, c, left[r][c], right[r][c]]
        for r in range(len(left))
        for c in range(len(left[0]))
        if left[r][c] != right[r][c]
    ]


def lattice_rival_cap_period_five(grid: list[list[int]]) -> list[list[int]]:
    n = len(grid)
    color = grid[0][0]
    period = min(n + 1, 5)
    line_index = period - 1
    return [
        [color if r % period == line_index or c % period == line_index else 0 for c in range(15)]
        for r in range(15)
    ]


def components(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[list[tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            cells: list[tuple[int, int]] = []
            stack = [(r, c)]
            seen.add((r, c))
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = cr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] != 0
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append(sorted(cells))
    return result


def size_rival_leave_unknown(grid: list[list[int]]) -> list[list[int]]:
    out = [row[:] for row in grid]
    mapping = {4: 1, 3: 2, 2: 3}
    for cells in components(grid):
        color = mapping.get(len(cells), grid[cells[0][0]][cells[0][1]])
        for r, c in cells:
            out[r][c] = color
    return out


def selected_outputs(task_id: str, grids: list[list[list[int]]]) -> tuple[list[list[list[int]]], dict[str, Any]]:
    result = Catalog(REPO).apply(task_id, grids, timeout=120)
    rows = result["results"]
    if not result.get("rule_hash_matches_catalog"):
        raise RuntimeError(f"{task_id}: selected rule hash does not match catalog")
    if not all(item.get("valid_output") and item.get("error") is None for item in rows):
        raise RuntimeError(f"{task_id}: selected Racket rule failed: {rows}")
    return [item["output"] for item in rows], {
        "rule_hash": result.get("rule_hash"),
        "rule_hash_matches_catalog": result.get("rule_hash_matches_catalog"),
        "cases": len(rows),
        "all_valid": True,
    }


def build_lattice() -> Path:
    task_id = "0ee277d96857"
    gen, source = load_generator(task_id)
    expected_sha = "a46ff878e8d65ece582324710805019c0d04523e872a6eb2ae37d8de94e867e3"
    actual_sha = sha256(source)
    if actual_sha != expected_sha:
        raise RuntimeError(f"{task_id}: source hash changed: {actual_sha}")

    found = None
    for seed in range(10000):
        grids = [gen.generate(seed, index) for index in range(5)]
        sides = [len(grid) for grid in grids]
        if 5 not in sides[:4] and sides[4] == 5:
            found = seed, grids, sides
            break
    if found is None:
        raise RuntimeError("no unseen-side lesson found")
    seed, grids, sides = found
    outputs, racket = selected_outputs(task_id, grids)
    rivals = [lattice_rival_cap_period_five(grid) for grid in grids]
    demo_diffs = [different_cells(outputs[i], rivals[i]) for i in range(4)]
    query_diff = different_cells(outputs[4], rivals[4])
    if any(demo_diffs) or not query_diff:
        raise RuntimeError("lattice rival did not have the required fit/disagreement")

    report = {
        "schema": "arcpuzzles-audit-counterexample-v1",
        "task_id": task_id,
        "generator_sha256": actual_sha,
        "generator_version": gen.VERSION,
        "lesson_convention": {
            "seed": seed,
            "sample_indices": [0, 1, 2, 3, 4],
            "demo_count": 4,
            "query_index": 4,
        },
        "issue": "The generator samples side independently, so four demonstrations do not guarantee coverage of side 5 even though the source comment claims n=2,3,4,5 are pinned.",
        "rival": {
            "name": "cap_period_at_five",
            "definition": "Use the intended lattice for n=2,3,4, but cap the period at 5 for n=5.",
            "why_plausible": "It extends every period observed in these demonstrations while saturating at the largest demonstrated period.",
        },
        "sides": sides,
        "pairs": [
            {"role": "demo" if i < 4 else "query", "sample_index": i, "input": grids[i], "selected_racket_output": outputs[i], "rival_output": rivals[i]}
            for i in range(5)
        ],
        "evidence": {
            "demo_difference_counts": [len(diff) for diff in demo_diffs],
            "query_difference_count": len(query_diff),
            "query_first_differences": query_diff[:40],
            "selected_racket": racket,
        },
        "limits": [
            "This proves one deterministic lesson window admits the stated rival; it does not enumerate all lesson seeds.",
            "The rival is an adversarial teaching alternative, not a claim about human solver frequency.",
        ],
    }
    out = AUDIT_ROOT / task_id / "unseen_side_lesson.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return out


def build_sizes() -> Path:
    task_id = "154382a9e3e8"
    gen, source = load_generator(task_id)
    expected_sha = "377426643a84c85adfa2e0740296ec89d5778e738d8e9372a2e4fa1c83b62d31"
    actual_sha = sha256(source)
    if actual_sha != expected_sha:
        raise RuntimeError(f"{task_id}: source hash changed: {actual_sha}")

    found = None
    for seed in range(20000):
        grids = [gen.generate(seed, index) for index in range(4)]
        if any(grid == [[0]] for grid in grids):
            continue
        sizes = [[len(cells) for cells in components(grid)] for grid in grids]
        colors = [{value for row in grid for value in row if value != 0} for grid in grids]
        demos_have_only_known = all(set(item) <= {2, 3, 4} for item in sizes[:3])
        query_others = [size for size in sizes[3] if size not in {2, 3, 4}]
        query_color = next(iter(colors[3])) if len(colors[3]) == 1 else None
        if demos_have_only_known and query_others and query_color not in {None, 5}:
            found = seed, grids, sizes, [sorted(c) for c in colors]
            break
    if found is None:
        raise RuntimeError("no missing-other-branch lesson found")
    seed, grids, sizes, colors = found
    outputs, racket = selected_outputs(task_id, grids)
    rivals = [size_rival_leave_unknown(grid) for grid in grids]
    demo_diffs = [different_cells(outputs[i], rivals[i]) for i in range(3)]
    query_diff = different_cells(outputs[3], rivals[3])
    if any(demo_diffs) or not query_diff:
        raise RuntimeError("size rival did not have the required fit/disagreement")

    report = {
        "schema": "arcpuzzles-audit-counterexample-v1",
        "task_id": task_id,
        "generator_sha256": actual_sha,
        "generator_version": gen.VERSION,
        "lesson_convention": {
            "seed": seed,
            "sample_indices": [0, 1, 2, 3],
            "demo_count": 3,
            "query_index": 3,
            "basis": "No EXAMPLES_NEEDED literal is declared, so the authoring default is three demonstrations.",
        },
        "issue": "The default path always covers sizes 2,3,4 but schedules the else branch with an independent randint(0,2), so a three-demo lesson can omit every other-size component until the query.",
        "rival": {
            "name": "recolor_only_demonstrated_sizes",
            "definition": "Recolor sizes 4→1, 3→2, 2→3; leave every other-size component in its original input color.",
            "why_plausible": "It performs exactly the three mappings demonstrated by the lesson and makes no unsupported else-branch commitment.",
        },
        "component_sizes": sizes,
        "input_colors": colors,
        "pairs": [
            {"role": "demo" if i < 3 else "query", "sample_index": i, "input": grids[i], "selected_racket_output": outputs[i], "rival_output": rivals[i]}
            for i in range(4)
        ],
        "evidence": {
            "demo_difference_counts": [len(diff) for diff in demo_diffs],
            "query_difference_count": len(query_diff),
            "query_first_differences": query_diff[:40],
            "selected_racket": racket,
        },
        "limits": [
            "This proves one deterministic lesson window admits the stated rival; it does not enumerate all lesson seeds.",
            "The rival is an adversarial teaching alternative, not a claim about human solver frequency.",
        ],
    }
    out = AUDIT_ROOT / task_id / "missing_other_branch_lesson.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return out


def main() -> int:
    paths = [build_lattice(), build_sizes()]
    for path in paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        print(json.dumps({
            "path": str(path.relative_to(ROOT)),
            "task_id": data["task_id"],
            "seed": data["lesson_convention"]["seed"],
            "demo_difference_counts": data["evidence"]["demo_difference_counts"],
            "query_difference_count": data["evidence"]["query_difference_count"],
        }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
