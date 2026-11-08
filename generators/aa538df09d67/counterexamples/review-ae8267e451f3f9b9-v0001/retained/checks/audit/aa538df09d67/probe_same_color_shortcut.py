from __future__ import annotations

import hashlib
import json
from pathlib import Path

from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK_ID = "aa538df09d67"
ROOT = find_root(__file__)
GENERATOR, SOURCE, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
HERE = Path(__file__).resolve().parent


def components(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    result = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                current = stack.pop()
                cells.append(current)
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    neighbor = (current[0] + dr, current[1] + dc)
                    if (
                        0 <= neighbor[0] < height
                        and 0 <= neighbor[1] < width
                        and neighbor not in seen
                        and grid[neighbor[0]][neighbor[1]] == color
                    ):
                        seen.add(neighbor)
                        stack.append(neighbor)
            result.append((color, cells))
    return result


def per_color_global_bbox(grid):
    height, width = len(grid), len(grid[0])
    output = [[0] * width for _ in range(height)]
    colors = sorted({value for row in grid for value in row if value != 0})
    for color in colors:
        cells = [
            (row, col)
            for row, values in enumerate(grid)
            for col, value in enumerate(values)
            if value == color
        ]
        row0 = min(row for row, _ in cells)
        row1 = max(row for row, _ in cells)
        col0 = min(col for _, col in cells)
        col1 = max(col for _, col in cells)
        for col in range(col0, col1 + 1):
            output[row0][col] = color
            output[row1][col] = color
        for row in range(row0, row1 + 1):
            output[row][col0] = color
            output[row][col1] = color
    return output


def main():
    canonical = canonical_pairs(TASK_ID, root=ROOT)
    fit = [per_color_global_bbox(pair["input"]) == pair["output"] for pair in canonical]
    by_band = {}
    repeated_total = 0
    for band_index, band in enumerate(("easy", "medium", "hard")):
        repeated = 0
        for index in range(500):
            grid = GENERATOR.generate(
                880000 + band_index * 10000 + index,
                index,
                difficulty=band,
            )
            counts = {}
            for color, _ in components(grid):
                counts[color] = counts.get(color, 0) + 1
            if any(count > 1 for count in counts.values()):
                repeated += 1
        repeated_total += repeated
        by_band[band] = {"draws": 500, "repeated_color_component_draws": repeated}

    witness = json.loads((HERE / "input.json").read_text(encoding="utf-8"))
    rival = per_color_global_bbox(witness)
    (HERE / "rival.json").write_text(json.dumps(rival, indent=2) + "\n", encoding="utf-8")
    report = {
        "schema": "audit-aa538df09d67-same-color-shortcut-v2",
        "task_id": TASK_ID,
        "generator_sha256": SOURCE_SHA256,
        "generator_path": SOURCE.relative_to(ROOT).as_posix(),
        "canonical_pairs": len(canonical),
        "canonical_rival_matches": sum(fit),
        "canonical_fit_vector": fit,
        "sampled_draws": 1500,
        "by_band": by_band,
        "repeated_color_component_draws": repeated_total,
        "witness_validator_reasons": GENERATOR.self_check(witness),
        "witness_component_colors": [color for color, _ in components(witness)],
        "rival": "paint one global bounding-box border per nonzero color",
        "input_sha256": hashlib.sha256((HERE / "input.json").read_bytes()).hexdigest(),
        "rival_sha256": hashlib.sha256((HERE / "rival.json").read_bytes()).hexdigest(),
    }
    (HERE / "probe.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
