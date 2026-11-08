from __future__ import annotations

import hashlib
import json
from collections import deque
from pathlib import Path
import sys
from typing import Iterable

WORK = Path(__file__).resolve().parents[2]
ROOT = WORK / "repo"
sys.path.insert(0, str(ROOT / "shared/runtime"))

from reviewer_support import canonical_pairs, find_root, load_selected_generator  # noqa: E402


def sha_grid(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(payload).hexdigest()


def differences(expected: list[list[int]], actual: list[list[int]]) -> list[dict[str, int]]:
    assert len(expected) == len(actual)
    rows = []
    for row, (erow, arow) in enumerate(zip(expected, actual)):
        assert len(erow) == len(arow)
        for col, (evalue, avalue) in enumerate(zip(erow, arow)):
            if evalue != avalue:
                rows.append({"row": row, "col": col, "intended": evalue, "rival": avalue})
    return rows


def components4(grid: list[list[int]], color: int) -> list[list[tuple[int, int]]]:
    remaining = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == color
    }
    components: list[list[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        queue: deque[tuple[int, int]] = deque([start])
        component: list[tuple[int, int]] = []
        while queue:
            row, col = queue.popleft()
            component.append((row, col))
            for other in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                if other in remaining:
                    remaining.remove(other)
                    queue.append(other)
        components.append(sorted(component))
    return sorted(components, key=min)


def bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = list(cells)
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return min(rows), min(cols), max(rows), max(cols)


def perimeter(box: tuple[int, int, int, int]) -> set[tuple[int, int]]:
    row0, col0, row1, col1 = box
    return {
        (row, col)
        for row in range(row0, row1 + 1)
        for col in range(col0, col1 + 1)
        if row in (row0, row1) or col in (col0, col1)
    }


def complete_frames(grid: list[list[int]]) -> list[tuple[int, int, int, int]]:
    frames = []
    for component in components4(grid, 5):
        box = bbox(component)
        if perimeter(box) <= set(component):
            frames.append(box)
    return frames


def frame_markers_scan_order(
    grid: list[list[int]], box: tuple[int, int, int, int]
) -> list[tuple[str, int, int]]:
    height, width = len(grid), len(grid[0])
    row0, col0, row1, col1 = box
    markers: list[tuple[str, int, int]] = []
    if row0 > 0:
        markers.extend(("top", row0 - 1, col) for col in range(col0 + 1, col1) if grid[row0 - 1][col] == 7)
    if row1 < height - 1:
        markers.extend(("bottom", row1 + 1, col) for col in range(col0 + 1, col1) if grid[row1 + 1][col] == 7)
    if col0 > 0:
        markers.extend(("left", row, col0 - 1) for row in range(row0 + 1, row1) if grid[row][col0 - 1] == 7)
    if col1 < width - 1:
        markers.extend(("right", row, col1 + 1) for row in range(row0 + 1, row1) if grid[row][col1 + 1] == 7)
    return markers


def first_marker_rival(grid: list[list[int]]) -> list[list[int]]:
    result = [row[:] for row in grid]
    for row0, col0, row1, col1 in complete_frames(grid):
        markers = frame_markers_scan_order(grid, (row0, col0, row1, col1))
        if not markers:
            continue
        side, marker_row, marker_col = markers[0]
        if side in ("top", "bottom"):
            for row in range(row0 + 1, row1):
                result[row][marker_col] = 3
        else:
            for col in range(col0 + 1, col1):
                result[marker_row][col] = 3
    return result


def color_bbox(grid: list[list[int]], color: int) -> tuple[int, int, int, int]:
    cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == color
    ]
    if not cells:
        raise ValueError(f"missing color {color}")
    return bbox(cells)


def overlap_output(grid: list[list[int]]) -> list[list[int]]:
    top2, left2, bottom2, right2 = color_bbox(grid, 2)
    top3, left3, bottom3, right3 = color_bbox(grid, 3)
    top = max(top2, top3)
    left = max(left2, left3)
    bottom = min(bottom2, bottom3)
    right = min(right2, right3)
    result = [[0] * len(grid[0]) for _ in grid]
    if top <= bottom and left <= right:
        for row in range(top, bottom + 1):
            for col in range(left, right + 1):
                result[row][col] = 8
    return result


def north2_south3_rival(grid: list[list[int]]) -> list[list[int]]:
    # Shortcut: color 2 is assumed to be the northern rectangle and color 3
    # the southern rectangle. The horizontal intersection is still measured.
    _top2, left2, bottom2, right2 = color_bbox(grid, 2)
    top3, left3, _bottom3, right3 = color_bbox(grid, 3)
    top = top3
    bottom = bottom2
    left = max(left2, left3)
    right = min(right2, right3)
    result = [[0] * len(grid[0]) for _ in grid]
    if top <= bottom and left <= right:
        for row in range(top, bottom + 1):
            for col in range(left, right + 1):
                result[row][col] = 8
    return result


def build_a0(root: Path) -> None:
    directory = WORK / "checks/audit/a0c6005765ee"
    generation = json.loads((directory / "generation.json").read_text())
    receipt = json.loads((directory / "racket.json").read_text())
    grids = json.loads((directory / "inputs.json").read_text())
    generator, source, digest = load_selected_generator("a0c6005765ee", root=root)
    assert digest == generation["generator_sha256"] == receipt["generator_sha256"]
    assert len(grids) == len(receipt["results"]) == 4

    comparisons = []
    for offset, (grid, row) in enumerate(zip(grids, receipt["results"])):
        assert grid == row["input"]
        rival = first_marker_rival(grid)
        diff = differences(row["output"], rival)
        comparisons.append(
            {
                "sample_index": generation["sample_indices"][offset],
                "profile": generation["profiles"][offset],
                "validator_errors": generator.self_check(grid),
                "input_sha256": row["input_sha256"],
                "racket_output_sha256": row["output_sha256"],
                "rival_output_sha256": sha_grid(rival),
                "rival_matches_racket": not diff,
                "difference_count": len(diff),
            }
        )

    query_index = 3
    query_row = receipt["results"][query_index]
    query_grid = grids[query_index]
    query_rival = first_marker_rival(query_grid)
    query_diff = differences(query_row["output"], query_rival)
    assert all(item["rival_matches_racket"] for item in comparisons[:3])
    assert query_diff

    report = {
        "schema": "arc-audit-finding/1",
        "task_id": "a0c6005765ee",
        "kind": "reproduced teaching shortcut",
        "generator_source": str(source.relative_to(root)),
        "generator_sha256": digest,
        "executed_rule_hash": receipt["executed_rule_hash"],
        "rule_hash_matches_catalog": receipt["rule_hash_matches_catalog"],
        "seed": generation["seed"],
        "difficulty": generation["difficulty"],
        "sample_indices": generation["sample_indices"],
        "lesson_policy": "same seed, four consecutive production samples; first three are demonstrations and fourth is query",
        "demo_profiles": generation["profiles"][:3],
        "query_profile": generation["profiles"][3],
        "rival": "For each complete color-5 frame, project only the first color-7 marker found in top/bottom/left/right scan order.",
        "comparison": comparisons,
        "rival_fits_all_demos": all(item["rival_matches_racket"] for item in comparisons[:3]),
        "rival_changes_query": bool(query_diff),
        "query": {
            "sample_index": generation["sample_indices"][query_index],
            "validator_errors": generator.self_check(query_grid),
            "input": query_grid,
            "racket_output": query_row["output"],
            "rival_output": query_rival,
            "differences": query_diff,
        },
        "apply_command": {
            "cwd": ".",
            "argv": [
                "python3", "run_with_racket.py", "python3", "-m", "arcpuzzles", "apply",
                "a0c6005765ee", "--input", "../checks/audit/a0c6005765ee/inputs.json",
                "--out", "../checks/audit/a0c6005765ee/racket.json",
            ],
        },
        "target_modified": False,
        "conclusion": "The current source reproduces the prior unresolved finding: a three-demo production lesson can omit a multi-marker witness, so the first-marker shortcut fits every demonstration and changes seven query cells.",
    }
    (directory / "report.json").write_text(json.dumps(report, indent=2) + "\n")


def build_600(root: Path) -> None:
    directory = WORK / "checks/audit/600284beb8e4"
    receipt = json.loads((directory / "racket.json").read_text())
    grid = json.loads((directory / "input.json").read_text())
    row = receipt["results"][0]
    generator, source, digest = load_selected_generator("600284beb8e4", root=root)
    assert digest == receipt["generator_sha256"]
    assert grid == row["input"]
    intended = overlap_output(grid)
    rival = north2_south3_rival(grid)
    assert row["output"] == intended
    diff = differences(intended, rival)
    assert diff

    canonical = canonical_pairs("600284beb8e4", root=root)
    canonical_rows = []
    for pair in canonical:
        pair_rival = north2_south3_rival(pair["input"])
        canonical_rows.append(
            {
                "split": pair["split"],
                "pair_index": pair["pair_index"],
                "bbox_2": list(color_bbox(pair["input"], 2)),
                "bbox_3": list(color_bbox(pair["input"], 3)),
                "rival_matches_canonical_output": pair_rival == pair["output"],
            }
        )
    assert all(item["rival_matches_canonical_output"] for item in canonical_rows)

    production_count = 0
    validator_failures = 0
    rival_mismatches = 0
    role_order_failures = 0
    unique_inputs: set[str] = set()
    ranges = {}
    for difficulty in ("easy", "medium", "hard"):
        ranges[difficulty] = {"seed": 0, "sample_indices": [0, 199]}
        for sample_index in range(200):
            sample = generator.generate(0, sample_index, difficulty=difficulty)
            production_count += 1
            unique_inputs.add(sha_grid(sample))
            if generator.self_check(sample, difficulty=difficulty):
                validator_failures += 1
            top2, _left2, bottom2, _right2 = color_bbox(sample, 2)
            top3, _left3, bottom3, _right3 = color_bbox(sample, 3)
            if not (top2 <= top3 and bottom2 <= bottom3):
                role_order_failures += 1
            if north2_south3_rival(sample) != overlap_output(sample):
                rival_mismatches += 1

    report = {
        "schema": "arc-audit-finding/1",
        "task_id": "600284beb8e4",
        "kind": "reproduced distribution shortcut",
        "generator_source": str(source.relative_to(root)),
        "generator_sha256": digest,
        "executed_rule_hash": receipt["executed_rule_hash"],
        "rule_hash_matches_catalog": receipt["rule_hash_matches_catalog"],
        "rival": "Assume color 2 is always the northern rectangle and color 3 the southern rectangle; fill rows from color-3 top through color-2 bottom over the measured horizontal bbox intersection.",
        "canonical_comparison": canonical_rows,
        "rival_fits_all_canonical_pairs": all(item["rival_matches_canonical_output"] for item in canonical_rows),
        "production_probe": {
            "ranges": ranges,
            "requested_samples": production_count,
            "unique_inputs": len(unique_inputs),
            "validator_failures": validator_failures,
            "role_order_failures": role_order_failures,
            "rival_mismatches": rival_mismatches,
            "result": "The current sampler always placed color 2 north of color 3, so the shortcut matched the true bbox intersection on every sampled input.",
        },
        "counterexample": {
            "construction": "9x12; color-3 border bbox rows 1..5 cols 2..7; color-2 border bbox rows 3..7 cols 4..10",
            "documented_invariants_satisfied": [
                "one color-2 rectangular border",
                "one color-3 rectangular border",
                "non-empty bounding-box intersection",
            ],
            "validator_errors": generator.self_check(grid),
            "current_sampler_emits_role_reversal": False,
            "input": grid,
            "racket_output": row["output"],
            "rival_output": rival,
            "differences": diff,
        },
        "apply_command": {
            "cwd": ".",
            "argv": [
                "python3", "run_with_racket.py", "python3", "-m", "arcpuzzles", "apply",
                "600284beb8e4", "--input", "../checks/audit/600284beb8e4/input.json",
                "--out", "../checks/audit/600284beb8e4/racket.json",
            ],
        },
        "target_modified": False,
        "conclusion": "The rule itself handles reversed vertical roles, but the generator never teaches that color roles are geometric rather than fixed. The accepted invariant-satisfying reversal makes the shortcut visibly wrong.",
    }
    (directory / "report.json").write_text(json.dumps(report, indent=2) + "\n")


def main() -> None:
    root = find_root(ROOT)
    build_a0(root)
    build_600(root)


if __name__ == "__main__":
    main()
