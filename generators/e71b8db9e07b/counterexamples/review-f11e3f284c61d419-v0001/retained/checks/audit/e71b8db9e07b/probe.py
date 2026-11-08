from __future__ import annotations

import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

TASK_ID = "e71b8db9e07b"
ROOT = find_root(__file__)
GEN, SOURCE_PATH, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
HERE = Path(__file__).resolve().parent

REQUEST = {
    "grid_h": 28,
    "grid_w": 28,
    "proto_size": 7,
    "n_match": 3,
    "n_distract": 3,
}
SEED = 20261007
SAMPLE_INDEX = 11
DIFFICULTY = "medium"
CARD = ((-1, 0), (1, 0), (0, -1), (0, 1))


def components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in CARD:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append((color, cells))
    return result


def bbox(cells):
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return max(rows) - min(rows) + 1, max(cols) - min(cols) + 1


def is_frame(cells):
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    r0, r1, c0, c1 = min(rows), max(rows), min(cols), max(cols)
    expected = {
        (r, c)
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
        if r in (r0, r1) or c in (c0, c1)
    }
    return set(cells) == expected


def summarize(grid):
    comps = components(grid)
    proto = [(color, cells) for color, cells in comps if color != 5]
    frames = [cells for color, cells in comps if color == 5 and is_frame(cells)]
    proto_bbox = bbox(proto[0][1]) if len(proto) == 1 else None
    matches = 0
    distractors = 0
    for cells in frames:
        fh, fw = bbox(cells)
        interior = (fh - 2, fw - 2)
        if interior == proto_bbox:
            matches += 1
        else:
            distractors += 1
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "prototype_object_count": len(proto),
        "prototype_cell_count": len(proto[0][1]) if len(proto) == 1 else None,
        "prototype_bbox": list(proto_bbox) if proto_bbox else None,
        "matching_frames": matches,
        "distractor_frames": distractors,
    }


def main():
    grid = GEN.generate(
        SEED,
        SAMPLE_INDEX,
        difficulty=DIFFICULTY,
        **REQUEST,
    )
    actual = summarize(grid)
    errors = GEN.self_check(grid, difficulty=DIFFICULTY, meta={"overrides": REQUEST})
    helpful = {}
    base = GEN.generate(SEED, SAMPLE_INDEX, difficulty=DIFFICULTY)
    for texture in GEN.HELPFUL_TEXTURES:
        helpful[texture] = GEN.generate(
            SEED, SAMPLE_INDEX, difficulty=DIFFICULTY, texture=texture
        ) == base
    report = {
        "schema": "arcpuzzles-audit-generator-contract-v1",
        "task_id": TASK_ID,
        "generator_path": str(Path(SOURCE_PATH).relative_to(ROOT)),
        "generator_sha256": SOURCE_SHA256,
        "seed": SEED,
        "sample_index": SAMPLE_INDEX,
        "difficulty": DIFFICULTY,
        "requested_overrides": REQUEST,
        "actual": actual,
        "request_honored": {
            "grid_h": actual["grid_h"] == REQUEST["grid_h"],
            "grid_w": actual["grid_w"] == REQUEST["grid_w"],
            "proto_size": actual["prototype_cell_count"] == REQUEST["proto_size"],
            "n_match": actual["matching_frames"] == REQUEST["n_match"],
            "n_distract": actual["distractor_frames"] == REQUEST["n_distract"],
        },
        "self_check_errors": errors,
        "helpful_texture_byte_identical_to_base": helpful,
        "input": grid,
    }
    (HERE / "input.json").write_text(json.dumps(grid, indent=2) + "\n")
    (HERE / "probe.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
