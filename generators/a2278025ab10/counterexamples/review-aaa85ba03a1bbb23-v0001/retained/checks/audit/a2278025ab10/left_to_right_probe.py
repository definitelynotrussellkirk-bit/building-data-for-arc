from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Iterable

PACKET_ROOT = Path(__file__).resolve().parents[3]
REPO = PACKET_ROOT / "repo"
sys.path.insert(0, str(REPO / "shared" / "runtime"))
GENERATOR_PATH = REPO / "generators" / "a2278025ab10" / "generator.py"
CANONICAL_PATH = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
OUT = PACKET_ROOT / "checks" / "audit" / "a2278025ab10"

spec = importlib.util.spec_from_file_location("audit_a227", GENERATOR_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


def bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = list(cells)
    return (
        min(r for r, _ in cells),
        min(c for _, c in cells),
        max(r for r, _ in cells),
        max(c for _, c in cells),
    )


def color_cells(grid: list[list[int]], color: int) -> list[tuple[int, int]]:
    return [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]


def component_record(grid: list[list[int]], color: int) -> dict:
    cells = color_cells(grid, color)
    r1, c1, r2, c2 = bbox(cells)
    offsets = sorted((r - r1, c - c1) for r, c in cells)
    return {
        "color": color,
        "bbox": [r1, c1, r2, c2],
        "height": r2 - r1 + 1,
        "width": c2 - c1 + 1,
        "center_col2": c1 + c2,
        "offsets": offsets,
    }


def left_to_right_rival(grid: list[list[int]]) -> list[list[int]]:
    """Pair kth non-frame crop from the left with kth frame from the left."""
    output = [row[:] for row in grid]
    component_colors = sorted({v for row in grid for v in row if v not in (0, 1, 2, 3)})
    components = [component_record(grid, color) for color in component_colors]
    frames = []
    for color in (1, 2, 3):
        cells = color_cells(grid, color)
        if not cells:
            raise ValueError(f"missing frame color {color}")
        r1, c1, r2, c2 = bbox(cells)
        frames.append({"color": color, "bbox": [r1, c1, r2, c2], "center_col2": c1 + c2})

    for record in components:
        for r, c in color_cells(grid, record["color"]):
            output[r][c] = 0

    components.sort(key=lambda item: (item["center_col2"], item["bbox"][0], item["color"]))
    frames.sort(key=lambda item: (item["center_col2"], item["bbox"][0], item["color"]))
    if len(components) != len(frames):
        raise ValueError("rival requires exactly three components and frames")

    for component, frame in zip(components, frames):
        fr1, fc1, fr2, fc2 = frame["bbox"]
        interior_h = fr2 - fr1 - 1
        interior_w = fc2 - fc1 - 1
        top = fr1 + 1 + (interior_h - component["height"]) // 2
        left = fc1 + 1 + (interior_w - component["width"]) // 2
        for dr, dc in component["offsets"]:
            output[top + dr][left + dc] = component["color"]
    return output


def canonical_row() -> dict:
    for line in CANONICAL_PATH.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == "a2278025ab10":
            return row
    raise RuntimeError("canonical row missing")


canonical = canonical_row()
canonical_pairs = [*canonical.get("train", []), *canonical.get("test", [])]
canonical_fit = [left_to_right_rival(pair["input"]) == pair["output"] for pair in canonical_pairs]
if not all(canonical_fit):
    raise AssertionError(f"rival did not fit canonical pairs: {canonical_fit}")

chosen = None
for seed in range(1, 200):
    for sample_index in range(40):
        try:
            grid = module.generate(seed, sample_index, difficulty="medium")
        except ValueError:
            continue
        rival = left_to_right_rival(grid)
        # The selected authority is applied outside this script. Choose a case where
        # positional pairing maps at least one crop to a different frame color than
        # its hole-count family: generated builders are solid/ring/double-ring in
        # colors sorted by construction order, but component colors are randomized.
        component_colors = sorted({v for row in grid for v in row if v not in (0, 1, 2, 3)})
        components = sorted(
            [component_record(grid, color) for color in component_colors],
            key=lambda item: (item["center_col2"], item["bbox"][0], item["color"]),
        )
        frames = sorted(
            [
                {
                    "color": color,
                    "bbox": list(bbox(color_cells(grid, color))),
                    "center_col2": sum(bbox(color_cells(grid, color))[1::2]),
                }
                for color in (1, 2, 3)
            ],
            key=lambda item: (item["center_col2"], item["bbox"][0], item["color"]),
        )
        positional_mapping = [(c["color"], f["color"]) for c, f in zip(components, frames)]
        # Count 4-connected zero regions in the crop that do not touch its boundary.
        intended_mapping = []
        for c in components:
            occupied = set(map(tuple, c["offsets"]))
            unseen = {
                (r, col)
                for r in range(c["height"])
                for col in range(c["width"])
                if (r, col) not in occupied
            }
            holes = 0
            while unseen:
                start = unseen.pop()
                stack = [start]
                touches_boundary = False
                while stack:
                    r, col = stack.pop()
                    if r in (0, c["height"] - 1) or col in (0, c["width"] - 1):
                        touches_boundary = True
                    for nxt in ((r - 1, col), (r + 1, col), (r, col - 1), (r, col + 1)):
                        if nxt in unseen:
                            unseen.remove(nxt)
                            stack.append(nxt)
                if not touches_boundary:
                    holes += 1
            intended_mapping.append((c["color"], holes + 1))
        if sorted(positional_mapping) != sorted(intended_mapping):
            chosen = {
                "seed": seed,
                "sample_index": sample_index,
                "difficulty": "medium",
                "input": grid,
                "rival_output": rival,
                "positional_mapping": positional_mapping,
                "intended_mapping": intended_mapping,
                "self_check": module.self_check(grid),
            }
            break
    if chosen:
        break

if chosen is None:
    raise AssertionError("no positional counterexample found")

(OUT / "input.json").write_text(json.dumps(chosen["input"], indent=2) + "\n")
(OUT / "rival.json").write_text(json.dumps(chosen["rival_output"], indent=2) + "\n")
metadata = {
    "schema": "audit-positional-rival-v1",
    "task_id": "a2278025ab10",
    "generator_sha256": hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest(),
    "canonical_pairs_checked": len(canonical_pairs),
    "canonical_fit": canonical_fit,
    "rival": "sort the three lower non-frame crops and the three frames left-to-right; center the kth crop in the kth frame",
    **{k: v for k, v in chosen.items() if k not in ("input", "rival_output")},
}
(OUT / "probe.json").write_text(json.dumps(metadata, indent=2) + "\n")
print(json.dumps(metadata, indent=2))
