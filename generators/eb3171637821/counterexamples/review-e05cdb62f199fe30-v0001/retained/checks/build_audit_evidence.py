from __future__ import annotations

import importlib.util
import json
import sys
import types
from pathlib import Path
from typing import Any

PACKET = Path(__file__).resolve().parents[1]
REPO = PACKET / "repo"
RUNTIME = REPO / "shared" / "runtime"
sys.path.insert(0, str(RUNTIME))
scripts_package = types.ModuleType("scripts")
scripts_package.__path__ = [str(REPO / "shared" / "tools")]
sys.modules.setdefault("scripts", scripts_package)

from puzzle_generators import runner  # noqa: E402


def load_generator(task_id: str):
    path = REPO / "generators" / task_id / "generator.py"
    package_name = f"puzzle_generators.per_puzzle.{task_id}"
    module_name = package_name + ".generator"
    package = types.ModuleType(package_name)
    package.__path__ = [str(path.parent)]
    sys.modules[package_name] = package
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def apply_racket(task_id: str, grid: list[list[int]]) -> list[list[int]]:
    canonical = next(
        json.loads(line)
        for line in (REPO / "shared" / "data" / "canonical" / "puzzles.jsonl").read_text().splitlines()
        if json.loads(line).get("task_id") == task_id
    )
    callable_text = runner.wrap_rule(canonical["program_solution"])
    bridge, fn_name = runner._open_bridge_with_rule(callable_text)
    try:
        return runner._apply_rule(bridge, fn_name, [row[:] for row in grid])
    finally:
        bridge.shutdown()


def canonical_pairs(task_id: str):
    row = next(
        json.loads(line)
        for line in (REPO / "shared" / "data" / "canonical" / "puzzles.jsonl").read_text().splitlines()
        if json.loads(line).get("task_id") == task_id
    )
    pairs = row["train"] + (row["test"] if isinstance(row["test"], list) else [row["test"]])
    return pairs


def grid(value: Any) -> list[list[int]]:
    if value and isinstance(value[0], str):
        return [[int(cell) for cell in row] for row in value]
    return [list(row) for row in value]


def eb_band_rule(g: list[list[int]]) -> list[list[int]]:
    """Independent transcription: count contiguous non-divider bands."""
    height, width = len(g), len(g[0])
    colors = sorted({value for row in g for value in row})
    divider = next(
        color
        for color in colors
        if any(all(g[row][col] == color for col in range(width)) for row in range(height))
        and any(all(g[row][col] == color for row in range(height)) for col in range(width))
    )
    cell = next(color for color in colors if color != divider)
    full_rows = {row for row in range(height) if all(g[row][col] == divider for col in range(width))}
    full_cols = {col for col in range(width) if all(g[row][col] == divider for row in range(height))}
    row_bands = sum(row not in full_rows and (row == 0 or row - 1 in full_rows) for row in range(height))
    col_bands = sum(col not in full_cols and (col == 0 or col - 1 in full_cols) for col in range(width))
    return [[cell] * col_bands for _ in range(row_bands)]


def eb_line_count_rival(g: list[list[int]]) -> list[list[int]]:
    height, width = len(g), len(g[0])
    colors = sorted({value for row in g for value in row})
    divider = next(
        color
        for color in colors
        if any(all(g[row][col] == color for col in range(width)) for row in range(height))
        and any(all(g[row][col] == color for row in range(height)) for col in range(width))
    )
    cell = next(color for color in colors if color != divider)
    full_rows = [row for row in range(height) if all(g[row][col] == divider for col in range(width))]
    full_cols = [col for col in range(width) if all(g[row][col] == divider for row in range(height))]
    return [[cell] * (len(full_cols) + 1) for _ in range(len(full_rows) + 1)]


def descending_connect_rival(g: list[list[int]]) -> list[list[int]]:
    positions: dict[int, list[tuple[int, int]]] = {}
    for row, line in enumerate(g):
        for col, value in enumerate(line):
            if value:
                positions.setdefault(value, []).append((row, col))
    out = [line[:] for line in g]
    for color in sorted(positions, reverse=True):
        cells = positions[color]
        if len(cells) != 2:
            continue
        a, b = cells
        if a[0] == b[0]:
            for col in range(min(a[1], b[1]), max(a[1], b[1]) + 1):
                out[a[0]][col] = color
        elif a[1] == b[1]:
            for row in range(min(a[0], b[0]), max(a[0], b[0]) + 1):
                out[row][a[1]] = color
    return out


eb_id = "eb3171637821"
eb = load_generator(eb_id)
eb_thick = [[5] * 6 for _ in range(6)]
for row in (2, 3):
    eb_thick[row] = [8] * 6
for row in range(6):
    eb_thick[row][3] = 8

eb_generated = 0
eb_adjacent_dividers = 0
eb_boundary_dividers = 0
eb_rival_matches = 0
for band_index, band in enumerate(("easy", "medium", "hard")):
    for index in range(200):
        generated = eb.generate(100_000 * (band_index + 1) + index, index * 13 + 7, difficulty=band)
        eb_generated += 1
        height, width = len(generated), len(generated[0])
        colors = sorted({value for row in generated for value in row})
        divider = next(
            color for color in colors
            if any(all(generated[row][col] == color for col in range(width)) for row in range(height))
            and any(all(generated[row][col] == color for row in range(height)) for col in range(width))
        )
        full_rows = [row for row in range(height) if all(generated[row][col] == divider for col in range(width))]
        full_cols = [col for col in range(width) if all(generated[row][col] == divider for row in range(height))]
        if any(b == a + 1 for a, b in zip(full_rows, full_rows[1:])) or any(
            b == a + 1 for a, b in zip(full_cols, full_cols[1:])
        ):
            eb_adjacent_dividers += 1
        if 0 in full_rows or height - 1 in full_rows or 0 in full_cols or width - 1 in full_cols:
            eb_boundary_dividers += 1
        official = eb_band_rule(generated)
        rival = eb_line_count_rival(generated)
        if rival == official:
            eb_rival_matches += 1

eb_canonical = canonical_pairs(eb_id)
eb_canonical_rival_matches = sum(
    eb_line_count_rival(grid(pair["input"])) == grid(pair["output"])
    for pair in eb_canonical
)
eb_canonical_details = []
for index, pair in enumerate(eb_canonical):
    canonical_input = grid(pair["input"])
    canonical_output = grid(pair["output"])
    height, width = len(canonical_input), len(canonical_input[0])
    colors = sorted({value for row in canonical_input for value in row})
    divider = next(
        color for color in colors
        if any(all(canonical_input[row][col] == color for col in range(width)) for row in range(height))
        and any(all(canonical_input[row][col] == color for row in range(height)) for col in range(width))
    )
    full_rows = [row for row in range(height) if all(canonical_input[row][col] == divider for col in range(width))]
    full_cols = [col for col in range(width) if all(canonical_input[row][col] == divider for row in range(height))]
    eb_canonical_details.append({
        "pair_index": index,
        "output_shape": [len(canonical_output), len(canonical_output[0])],
        "line_count_shortcut_shape": [len(full_rows) + 1, len(full_cols) + 1],
        "full_divider_rows": full_rows,
        "full_divider_cols": full_cols,
        "boundary_divider": 0 in full_rows or height - 1 in full_rows or 0 in full_cols or width - 1 in full_cols,
    })

connect_id = "17c625cd9cdd"
connect = load_generator(connect_id)
crossing = [[0] * 6 for _ in range(6)]
crossing[2][0] = crossing[2][5] = 2
crossing[0][3] = crossing[5][3] = 3
connect_generated = 0
connect_overlap_count = 0
connect_rival_matches = 0
for band_index, band in enumerate(("easy", "medium", "hard")):
    for index in range(200):
        generated = connect.generate(400_000 * (band_index + 1) + index, index * 17 + 9, difficulty=band)
        connect_generated += 1
        targets = connect._target_info(generated)
        segments = [entry[4] for entry in targets]
        if any(first & second for i, first in enumerate(segments) for second in segments[:i]):
            connect_overlap_count += 1
        official = connect._mirror(generated)
        if descending_connect_rival(generated) == official:
            connect_rival_matches += 1

connect_canonical = canonical_pairs(connect_id)
connect_canonical_rival_matches = sum(
    descending_connect_rival(grid(pair["input"])) == grid(pair["output"])
    for pair in connect_canonical
)

evidence = {
    "schema": "manual-audit-evidence-v1",
    eb_id: {
        "possible_shortcut": "number of full divider lines plus one, instead of number of non-divider bands",
        "canonical_matches": f"{eb_canonical_rival_matches}/{len(eb_canonical)}",
        "generated_matches": f"{eb_rival_matches}/{eb_generated}",
        "generated_with_adjacent_full_divider_lines": f"{eb_adjacent_dividers}/{eb_generated}",
        "generated_with_boundary_full_divider_lines": f"{eb_boundary_dividers}/{eb_generated}",
        "canonical_pair_details": eb_canonical_details,
        "counterexample_input": eb_thick,
        "selected_racket_output": apply_racket(eb_id, eb_thick),
        "independent_band_rule_output": eb_band_rule(eb_thick),
        "shortcut_output": eb_line_count_rival(eb_thick),
        "self_check_errors": eb.self_check(eb_thick),
    },
    connect_id: {
        "possible_shortcut": "connect in descending color order (or lower-color-wins at intersections), because all taught spans are disjoint",
        "canonical_matches": f"{connect_canonical_rival_matches}/{len(connect_canonical)}",
        "generated_matches": f"{connect_rival_matches}/{connect_generated}",
        "generated_with_overlapping_connectable_spans": f"{connect_overlap_count}/{connect_generated}",
        "counterexample_input": crossing,
        "selected_racket_output": apply_racket(connect_id, crossing),
        "shortcut_output": descending_connect_rival(crossing),
        "self_check_errors": connect.self_check(crossing),
        "intersection": {"row": 2, "col": 3},
    },
}

out = PACKET / "checks" / "audit-manual-evidence.json"
assert eb_rival_matches == eb_generated
assert connect_rival_matches == connect_generated
assert apply_racket(eb_id, eb_thick) == eb_band_rule(eb_thick)

out.write_text(json.dumps(evidence, indent=2) + "\n")
print(out)
print(json.dumps(evidence, indent=2))
