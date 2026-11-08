"""Reproduce the 0cb23f5660c9 invisible-rotation lesson shortcut."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from reviewer_support import load_selected_generator

TASK_ID = "0cb23f5660c9"
SEED = 2127
DIFFICULTY = "easy"
SAMPLE_INDICES = [0, 1, 2, 3]


def canonical_json(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def selected_component(grid):
    height, width = len(grid), len(grid[0])
    color = grid[0][0]
    seen = {(0, 0)}
    components = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != color or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            component = []
            while stack:
                r, c = stack.pop()
                component.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    rr, cc = r + dr, c + dc
                    if (
                        0 <= rr < height
                        and 0 <= cc < width
                        and grid[rr][cc] == color
                        and (rr, cc) not in seen
                    ):
                        seen.add((rr, cc))
                        stack.append((rr, cc))
            if len(component) > 1:
                components.append(component)
    if len(components) != 1:
        raise AssertionError(f"expected one selected component, got {len(components)}")
    return components[0]


def crop_component(grid, component):
    rows = [row for row, _ in component]
    cols = [col for _, col in component]
    r1, r2 = min(rows), max(rows)
    c1, c2 = min(cols), max(cols)
    return [list(grid[row][c1 : c2 + 1]) for row in range(r1, r2 + 1)]


def rotate_clockwise(grid):
    return [list(row) for row in zip(*grid[::-1])]


def main() -> None:
    repo = Path.cwd()
    out = repo.parent / "checks" / "audit" / TASK_ID
    generator, source_path, source_sha256 = load_selected_generator(TASK_ID, root=repo)
    inputs = [
        generator.generate(SEED, index, difficulty=DIFFICULTY)
        for index in SAMPLE_INDICES
    ]
    checks = [generator.self_check(grid) for grid in inputs]
    if any(checks):
        raise AssertionError(f"generated inputs failed self_check: {checks}")

    crops = [crop_component(grid, selected_component(grid)) for grid in inputs]
    rotated = [rotate_clockwise(crop) for crop in crops]
    symmetric = [crop == answer for crop, answer in zip(crops, rotated)]
    if symmetric != [True, True, True, False]:
        raise AssertionError(f"unexpected symmetry signature: {symmetric}")

    out.mkdir(parents=True, exist_ok=True)
    (out / "input.json").write_text(json.dumps(inputs, indent=2) + "\n")
    (out / "rival.json").write_text(json.dumps(crops, indent=2) + "\n")
    receipt = {
        "schema": "0cb23f5660c9-invisible-rotation-probe-v1",
        "task_id": TASK_ID,
        "generator_source": str(source_path.relative_to(repo)),
        "generator_sha256": source_sha256,
        "seed": SEED,
        "difficulty": DIFFICULTY,
        "sample_indices": SAMPLE_INDICES,
        "self_check": checks,
        "input_sha256": [hashlib.sha256(canonical_json(grid)).hexdigest() for grid in inputs],
        "identity_crop_sha256": [
            hashlib.sha256(canonical_json(crop)).hexdigest() for crop in crops
        ],
        "rotation_visible": [not value for value in symmetric],
        "lesson_claim": (
            "identity crop matches the first three selected-shape outputs because "
            "their crops are 90-degree symmetric; the fourth crop is asymmetric"
        ),
    }
    (out / "generation.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
