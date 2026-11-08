from __future__ import annotations

from collections import Counter
from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3] / "repo"
GENERATOR = ROOT / "generators/65052ae2f657/generator.py"
OUT = Path(__file__).with_name("marker_majority_probe.json")
INPUT = Path(__file__).with_name("tie_witness_input.json")

spec = spec_from_file_location("audit_65052ae2f657", GENERATOR)
module = module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)

CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def inspect(grid: list[list[int]]) -> dict:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    rooms: list[list[tuple[int, int]]] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 0 or (row, col) in seen:
                continue
            queue = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            for current_row, current_col in queue:
                cells.append((current_row, current_col))
                for delta_row, delta_col in CARDINAL:
                    point = (current_row + delta_row, current_col + delta_col)
                    if (
                        0 <= point[0] < height
                        and 0 <= point[1] < width
                        and point not in seen
                        and grid[point[0]][point[1]] == 0
                    ):
                        seen.add(point)
                        queue.append(point)
            rooms.append(cells)

    room_for_cell = {point: index for index, cells in enumerate(rooms) for point in cells}
    room_counts: list[Counter[int]] = []
    for cells in rooms:
        marker_cells: dict[tuple[int, int], int] = {}
        for row, col in cells:
            for delta_row in (-1, 0, 1):
                for delta_col in (-1, 0, 1):
                    if delta_row == 0 and delta_col == 0:
                        continue
                    marker = (row + delta_row, col + delta_col)
                    if (
                        0 <= marker[0] < height
                        and 0 <= marker[1] < width
                        and grid[marker[0]][marker[1]] not in (0, 1)
                    ):
                        marker_cells[marker] = grid[marker[0]][marker[1]]
        room_counts.append(Counter(marker_cells.values()))

    dots = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 1:
                continue
            if any(
                0 <= row + delta_row < height
                and 0 <= col + delta_col < width
                and grid[row + delta_row][col + delta_col] == 1
                for delta_row, delta_col in CARDINAL
            ):
                continue
            zero_neighbors = [
                (row + delta_row, col + delta_col)
                for delta_row, delta_col in CARDINAL
                if 0 <= row + delta_row < height
                and 0 <= col + delta_col < width
                and grid[row + delta_row][col + delta_col] == 0
            ]
            room = room_for_cell.get(zero_neighbors[0]) if zero_neighbors else None
            counts = room_counts[room] if room is not None else Counter()
            maximum = max(counts.values(), default=0)
            tied = maximum > 0 and sum(count == maximum for count in counts.values()) > 1
            dots.append(
                {
                    "cell": [row, col],
                    "room": room,
                    "marker_counts": dict(sorted(counts.items())),
                    "status": (
                        "no_adjacent_room"
                        if room is None
                        else "room_without_markers"
                        if not counts
                        else "tied_maximum"
                        if tied
                        else "unique_majority"
                    ),
                }
            )
    return {"room_count": len(rooms), "dots": dots}


summary = Counter()
first: dict[str, dict] = {}
total_samples = 0
for difficulty in ("easy", None, "hard"):
    difficulty_name = difficulty or "medium"
    for seed in range(200):
        for sample_index in range(3):
            grid = module.generate(seed, sample_index, difficulty=difficulty)
            diagnosis = inspect(grid)
            total_samples += 1
            statuses = [dot["status"] for dot in diagnosis["dots"]]
            summary["dots_total"] += len(statuses)
            for status in statuses:
                summary[f"dots_{status}"] += 1
            for status in set(statuses):
                summary[f"samples_with_{status}"] += 1
                if status not in first:
                    first[status] = {
                        "difficulty": difficulty_name,
                        "seed": seed,
                        "sample_index": sample_index,
                        "grid": grid,
                        "diagnosis": diagnosis,
                    }

payload = {
    "task_id": "65052ae2f657",
    "probe": "room marker-majority uniqueness and isolated-dot room attachment",
    "sample_policy": {"bands": ["easy", "medium", "hard"], "seeds_per_band": 200, "sample_indices": [0, 1, 2]},
    "samples": total_samples,
    "counts": dict(summary),
    "first_witnesses": first,
}
OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
INPUT.write_text(json.dumps({"input": first["tied_maximum"]["grid"]}, indent=2) + "\n")
print(json.dumps({"samples": total_samples, "counts": dict(summary)}, indent=2, sort_keys=True))
