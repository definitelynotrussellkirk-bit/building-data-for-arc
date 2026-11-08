"""Semantic generator for ARC task a2e8d5ad83e5.

Large solid same-color components of area at least four emit a full row and
column through the floor-center of their bounding box.  A cell hit by multiple
distinct colors becomes background zero; repeated hits of one color do not
cancel.  Canonical scenes hide one to three 3x3 anchors in dense multicolor
singleton noise.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "a2e8d5ad83e5"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "79221bcc26a6"
SUMMARY = "Solid colored anchors emit center-row/column crosses; distinct-color overlaps cancel to zero."
INVARIANTS = [
    "background is literal color 0",
    "calibrated scenes contain one through four solid square anchors",
    "anchors have area at least four and are separated from noise",
    "multicolor singleton noise supplies at least eight nonzero colors",
]

PUBLIC_PROFILES = tuple(f"public_{i}" for i in range(1, 6))
GENERAL_PROFILES = (
    "one_square",
    "two_squares",
    "three_squares",
    "four_squares",
    "same_color_pair",
    "same_row_centers",
    "same_col_centers",
    "even_size_pair",
    "mixed_sizes",
    "edge_square",
    "dense_noise",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "weighted exact-public and semantic anchor/noise curricula",
        "valid": "public_1|public_2|public_3|public_4|public_5|one_square|two_squares|three_squares|four_squares|same_color_pair|same_row_centers|same_col_centers|even_size_pair|mixed_sizes|edge_square|dense_noise",
    }
}

_PUBLIC_ROWS = {
    "public_1": "00000087000000/68000000008000/00000030000000/00000006010000/00265030002220/00000006002220/00000007002220/00033300080000/00033300000000/03033300000000/00000000000800/00000000000030/00300000000000/50000030400000/00003000000000/00000000006001/00080800000000/00806700000008",
    "public_2": "0000000000090/0000000002030/0000000003000/0000900600000/7000310000000/0020044400000/0000044400009/0000044400000/9700000100100/0000000000000/0000000006000/0007000000100/0008000000000/0000008000080",
    "public_3": "000100000000000000/000000000000000000/002000000008880000/000000000708881300/004000000408880000/100700072000000000/800040000000000300/050008008000000000/000000000000001000/000666000000000040/004666000000000300/000666000000000000/000040000000003000/000000000000000000/009000000000000333/130020000000000333/000004000800000333/000000006000040000",
    "public_4": "000000007000000000/000000000000000000/000000000900000000/000090000000000000/000000888000000000/000800888000000000/000000888000000080/001002000000000000/000000000000000000/000000000000000009/000000800000777020/050000000300777000/000000000000777000/000000000000002000/000004000000000000/000000000070000004/000000000000000000",
    "public_5": "0000000000008000200/4000000000300000000/1000074440000000000/0000004440000060000/0500074440001000000/0000600000000000800/0070004000000000000/0000000000000888024/0090000000004888500/0000000000000888000/0020400000000001400/0000000200000600020/7770000080000010000/7770000000000000000/7770000000000000000/0066990040000000000/0000000000007000020/3040000000080000400/0000000500060000000",
}


def _decode(rows):
    return [[int(value) for value in row] for row in rows.split("/")]


_PUBLIC_INPUTS = {name: _decode(rows) for name, rows in _PUBLIC_ROWS.items()}
_PUBLIC_SIGNATURES = {
    tuple(map(tuple, grid)): name for name, grid in _PUBLIC_INPUTS.items()
}


def _valid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be non-empty"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["rows must be non-empty"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be ARC colors"]
    return []


def _components4(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    components = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            todo = [(row, col)]
            seen.add((row, col))
            cells = []
            while todo:
                rr, cc = todo.pop()
                cells.append((rr, cc))
                for nr, nc in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)):
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        todo.append((nr, nc))
            rows = [cell[0] for cell in cells]
            cols = [cell[1] for cell in cells]
            bbox = (min(rows), min(cols), max(rows), max(cols))
            components.append({"color": color, "cells": cells, "bbox": bbox, "size": len(cells)})
    return components


def _filled_anchors(grid):
    anchors = []
    for obj in _components4(grid):
        r1, c1, r2, c2 = obj["bbox"]
        if obj["size"] >= 4 and obj["size"] == (r2 - r1 + 1) * (c2 - c1 + 1):
            anchor = dict(obj)
            anchor["center"] = ((r1 + r2) // 2, (c1 + c2) // 2)
            anchor["shape"] = (r2 - r1 + 1, c2 - c1 + 1)
            anchors.append(anchor)
    return anchors


def rule_mirror(grid):
    errors = _valid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    anchors = _filled_anchors(grid)
    output = [list(row) for row in grid]
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            hits = {
                anchor["color"]
                for anchor in anchors
                if anchor["center"][0] == row or anchor["center"][1] == col
            }
            if len(hits) > 1:
                output[row][col] = 0
            elif len(hits) == 1:
                output[row][col] = next(iter(hits))
    return output


def _classify(anchors, noise_cells, height, width):
    count = len(anchors)
    if count == 1:
        return "one_square"
    if count == 4:
        return "four_squares"
    colors = [anchor["color"] for anchor in anchors]
    if len(set(colors)) < count:
        return "same_color_pair"
    centers = [anchor["center"] for anchor in anchors]
    if count == 2 and len({center[0] for center in centers}) == 1:
        return "same_row_centers"
    if count == 2 and len({center[1] for center in centers}) == 1:
        return "same_col_centers"
    sizes = sorted(anchor["shape"][0] for anchor in anchors)
    if count == 3 and sizes == [2, 3, 4]:
        return "mixed_sizes"
    if count == 2 and any(size % 2 == 0 for size in sizes):
        return "even_size_pair"
    if any(
        r1 == 0 or c1 == 0 or r2 == height - 1 or c2 == width - 1
        for r1, c1, r2, c2 in (anchor["bbox"] for anchor in anchors)
    ):
        return "edge_square"
    if noise_cells >= round(height * width * 0.12):
        return "dense_noise"
    return "three_squares" if count == 3 else "two_squares"


def _analysis(grid):
    errors = _valid(grid)
    result = {"errors": errors, "scene_profile": None}
    if errors:
        return result
    height, width = len(grid), len(grid[0])
    anchors = _filled_anchors(grid)
    anchor_cells = {cell for anchor in anchors for cell in anchor["cells"]}
    noise_cells = sum(
        value != 0 and (row, col) not in anchor_cells
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
    )
    if not 1 <= len(anchors) <= 4:
        errors.append(f"expected 1..4 filled anchors, found {len(anchors)}")
    if any(anchor["shape"][0] != anchor["shape"][1] for anchor in anchors):
        errors.append("calibrated anchors must be squares")
    if any(not 2 <= anchor["shape"][0] <= 5 for anchor in anchors):
        errors.append("calibrated square sizes must be 2..5")
    if noise_cells < 12:
        errors.append(f"need at least 12 distractor cells, found {noise_cells}")
    palette = {value for row in grid for value in row if value != 0}
    if len(palette) < 8:
        errors.append(f"need at least 8 nonzero colors, found {len(palette)}")
    public = _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))
    profile = public or _classify(anchors, noise_cells, height, width)
    if profile not in SCENE_PROFILES:
        errors.append("scene does not match a declared profile")
    output = rule_mirror(grid)
    result.update(
        {
            "anchors": anchors,
            "anchor_count": len(anchors),
            "anchor_colors": tuple(anchor["color"] for anchor in anchors),
            "anchor_sizes": tuple(anchor["shape"] for anchor in anchors),
            "noise_cells": noise_cells,
            "palette": tuple(sorted(palette)),
            "cancel_cells": sum(
                grid[row][col] != 0 and output[row][col] == 0
                for row in range(height)
                for col in range(width)
            ),
            "output": output,
            "scene_profile": profile,
            "errors": errors,
        }
    )
    return result


def canonical_profile_signature(grid):
    analysis = _analysis(grid)
    profile = analysis.get("scene_profile")
    return profile if not analysis["errors"] and profile in PUBLIC_PROFILES else None


def observe_overrides(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {"scene_profile": analysis["scene_profile"]}


def _band(difficulty):
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _separated(row, col, size, boxes):
    for other_row, other_col, other_size in boxes:
        if not (
            row > other_row + other_size
            or other_row > row + size
            or col > other_col + other_size
            or other_col > col + size
        ):
            return False
    return True


def _random_boxes(rng, height, width, sizes, *, allow_edge=False, distinct_centers=True):
    for _restart in range(200):
        boxes = []
        for size in sizes:
            low = 0 if allow_edge else 1
            high_row = height - size if allow_edge else height - size - 1
            high_col = width - size if allow_edge else width - size - 1
            for _ in range(200):
                row = rng.randint(low, high_row)
                col = rng.randint(low, high_col)
                center = (row + (size - 1) // 2, col + (size - 1) // 2)
                if distinct_centers and any(
                    center[0] == rr + (ss - 1) // 2 or center[1] == cc + (ss - 1) // 2
                    for rr, cc, ss in boxes
                ):
                    continue
                if _separated(row, col, size, boxes):
                    boxes.append((row, col, size))
                    break
            else:
                break
        if len(boxes) == len(sizes):
            return boxes
    raise RuntimeError("could not place separated anchors")


def _boxes_for(rng, profile, height, width, sizes):
    if profile == "same_row_centers":
        row = max(1, height // 2 - 1)
        return [(row, 1, 3), (row, width - 4, 3)]
    if profile == "same_col_centers":
        col = max(1, width // 2 - 1)
        return [(1, col, 3), (height - 4, col, 3)]
    if profile == "edge_square":
        first = (0, 1, 3)
        for _ in range(2000):
            second = (rng.randint(1, height - 4), rng.randint(1, width - 4), 3)
            if _separated(*second, [first]):
                c1 = (1, 2)
                c2 = (second[0] + 1, second[1] + 1)
                if c1[0] != c2[0] and c1[1] != c2[1]:
                    return [first, second]
        raise RuntimeError("could not place edge profile")
    return _random_boxes(
        rng,
        height,
        width,
        sizes,
        distinct_centers=profile not in ("three_squares", "four_squares", "mixed_sizes"),
    )


def _paint_noise(rng, grid, count):
    height, width = len(grid), len(grid[0])
    candidates = [(row, col) for row in range(height) for col in range(width)]
    rng.shuffle(candidates)
    colors = list(range(1, 10))
    rng.shuffle(colors)
    placed = 0
    for row, col in candidates:
        if grid[row][col] != 0:
            continue
        if any(
            0 <= nr < height and 0 <= nc < width and grid[nr][nc] != 0
            for nr, nc in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1))
        ):
            continue
        grid[row][col] = colors[placed % len(colors)]
        placed += 1
        if placed == count:
            return
    raise RuntimeError(f"could place only {placed}/{count} distractors")


def _general(rng, profile, band):
    ranges = {"easy": (12, 16), "medium": (14, 21), "hard": (18, 26)}
    low, high = ranges[band]
    height, width = rng.randint(low, high), rng.randint(low, high)
    if profile == "one_square":
        sizes = [3]
    elif profile == "three_squares":
        sizes = [3, 3, 3]
    elif profile == "four_squares":
        sizes = [2, 2, 2, 2]
    elif profile == "even_size_pair":
        sizes = [2, 4]
    elif profile == "mixed_sizes":
        sizes = [2, 3, 4]
    else:
        sizes = [3, 3]
    boxes = _boxes_for(rng, profile, height, width, sizes)
    colors = rng.sample(list(range(1, 10)), len(boxes))
    if profile == "same_color_pair":
        colors[1] = colors[0]
    grid = [[0] * width for _ in range(height)]
    for (row, col, size), color in zip(boxes, colors):
        for rr in range(row, row + size):
            for cc in range(col, col + size):
                grid[rr][cc] = color
    noise_rate = 0.13 if profile == "dense_noise" else 0.08
    _paint_noise(rng, grid, max(16, round(height * width * noise_rate)))
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - {"scene_profile"}
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    requested = overrides.get("scene_profile")
    if requested is not None and requested not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {requested!r}")
    band = _band(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    profile = requested or ctx.draw_choice(
        "scene_profile",
        list(PUBLIC_PROFILES) + [name for name in GENERAL_PROFILES for _ in range(4)],
    )
    if profile in PUBLIC_PROFILES:
        return [row[:] for row in _PUBLIC_INPUTS[profile]]
    return _general(ctx.draw_rng("layout"), profile, band)


def self_check(grid, *, difficulty=None, meta=None):
    return list(_analysis(grid)["errors"])
