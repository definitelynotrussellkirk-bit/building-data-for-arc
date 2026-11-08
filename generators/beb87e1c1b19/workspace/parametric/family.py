"""Matched-input transform-composition family for ``beb87e1c1b19``.

Step A infers the unique dihedral transform taking panel A's support to panel B.
That transform is applied to panel C to form an input-dependent intermediate.
The episode setting then composes original C with the intermediate by union (the
exact canonical default) or symmetric difference.
"""
from __future__ import annotations

import copy
import hashlib
import random
from typing import Any

TASK_ID = "beb87e1c1b19"
SETTINGS = ("union", "xor")
DEFAULT = "union"
TRANSFORMS = (
    "id", "rot90", "rot180", "rot270",
    "flip-h", "flip-v", "transpose", "anti-transpose",
)

# Each tuple is (height, A/B width, C width, transform).  Square panels admit
# every dihedral transform.  The final query deliberately fills a 30x30 input;
# its rectangular panels use a dimension-preserving transform.
DEMO_SPECS = (
    (3, 3, 3, "rot90"),
    (4, 4, 4, "flip-h"),
    (5, 5, 5, "rot270"),
    (6, 6, 6, "transpose"),
    (7, 7, 7, "rot180"),
    (8, 8, 8, "anti-transpose"),
)
QUERY_SPECS = (
    (5, 5, 5, "flip-v"),
    (7, 7, 7, "rot90"),
    (9, 9, 9, "rot180"),
    (30, 9, 10, "flip-h"),
)


def integer(value: object, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in [{low}, {high}]")
    return value


def setting(value: object) -> str:
    if type(value) is not str or value not in SETTINGS:
        raise ValueError("composition must be union or xor")
    return value


def grid(value: object) -> list[list[int]]:
    if (type(value) is not list or not 1 <= len(value) <= 30
            or type(value[0]) is not list or not 1 <= len(value[0]) <= 30):
        raise ValueError("grid must be a nonempty 1..30 rectangle")
    width = len(value[0])
    if any(type(row) is not list or len(row) != width
           or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
           for row in value):
        raise ValueError("grid cells must be exact integer colors 0..9")
    return value


def _binary(panel: list[list[int]]) -> list[list[int]]:
    return [[int(value != 0) for value in row] for row in panel]


def _apply_transform(panel: list[list[int]], name: str) -> list[list[int]]:
    if name not in TRANSFORMS:
        raise ValueError("unknown transform")
    h, w = len(panel), len(panel[0])
    if name == "id":
        return [row[:] for row in panel]
    if name == "rot90":
        return [[panel[h - 1 - r][c] for r in range(h)] for c in range(w)]
    if name == "rot180":
        return [[panel[h - 1 - r][w - 1 - c] for c in range(w)] for r in range(h)]
    if name == "rot270":
        return [[panel[r][w - 1 - c] for r in range(h)] for c in range(w)]
    if name == "flip-h":
        return [list(reversed(row)) for row in panel]
    if name == "flip-v":
        return [row[:] for row in reversed(panel)]
    if name == "transpose":
        return [[panel[r][c] for r in range(h)] for c in range(w)]
    # anti-transpose = rotate 180 after transpose.
    transposed = [[panel[r][c] for r in range(h)] for c in range(w)]
    th, tw = len(transposed), len(transposed[0])
    return [[transposed[th - 1 - r][tw - 1 - c] for c in range(tw)] for r in range(th)]


def _split_panels(value: object) -> list[list[list[int]]]:
    data = grid(value)
    h, w = len(data), len(data[0])
    separators = [c for c in range(w) if all(data[r][c] == 8 for r in range(h))]
    if len(separators) != 2:
        raise ValueError("expected exactly two full-height color-8 separators")
    first, second = separators
    if first <= 0 or second <= first + 1 or second >= w - 1:
        raise ValueError("separators must divide three nonempty panels")
    panels = [
        [row[:first] for row in data],
        [row[first + 1:second] for row in data],
        [row[second + 1:] for row in data],
    ]
    if any(any(cell == 8 for row in panel for cell in row) for panel in panels):
        raise ValueError("divider color 8 may not occur inside a panel")
    return panels


def _matches(a_support: list[list[int]], b_support: list[list[int]]) -> list[str]:
    return [name for name in TRANSFORMS if _apply_transform(a_support, name) == b_support]


def _analyze(value: object) -> dict[str, Any]:
    panels = _split_panels(value)
    a, b, c = panels
    matches = _matches(_binary(a), _binary(b))
    if len(matches) != 1:
        raise ValueError(f"A->B transform must be unique, got {matches}")
    transformed = _apply_transform(c, matches[0])
    if len(transformed) != len(c) or len(transformed[0]) != len(c[0]):
        raise ValueError("selected transform must preserve C dimensions")
    c_support = {(r, col) for r, row in enumerate(c) for col, cell in enumerate(row) if cell}
    t_support = {(r, col) for r, row in enumerate(transformed) for col, cell in enumerate(row) if cell}
    overlap = c_support & t_support
    exclusive = c_support ^ t_support
    if not c_support or not overlap or not exclusive:
        raise ValueError("C and transformed C must have overlap and exclusive cells")
    return {
        "panels": panels,
        "transform": matches[0],
        "transform_matches": len(matches),
        "transformed_c": transformed,
        "c_support_set": c_support,
        "t_support_set": t_support,
        "overlap_set": overlap,
        "exclusive_set": exclusive,
    }


def intermediate(value: object) -> dict[str, Any]:
    info = _analyze(value)
    panels = info["panels"]
    return {
        "transform": info["transform"],
        "transform_matches": info["transform_matches"],
        "panel_shapes": [[len(panel), len(panel[0])] for panel in panels],
        "c_support": len(info["c_support_set"]),
        "transformed_support": len(info["t_support_set"]),
        "overlap_support": len(info["overlap_set"]),
        "exclusive_support": len(info["exclusive_set"]),
    }


def _compose(c: list[list[int]], transformed: list[list[int]], mode: str) -> list[list[int]]:
    selected = setting(mode)
    result: list[list[int]] = []
    for c_row, t_row in zip(c, transformed):
        row: list[int] = []
        for original, moved in zip(c_row, t_row):
            if selected == "union":
                row.append(moved if moved else original)
            elif bool(original) ^ bool(moved):
                row.append(original or moved)
            else:
                row.append(0)
        result.append(row)
    return result


def solve(value: object, mode: str) -> list[list[int]]:
    info = _analyze(value)
    return _compose(info["panels"][2], info["transformed_c"], mode)


def solve_wrong_identity(value: object, mode: str) -> list[list[int]]:
    """Counterfactual: skip transform application and feed C itself to stage B."""
    info = _analyze(value)
    c = info["panels"][2]
    return _compose(c, c, mode)


def _rng(seed: int, split: str, index: int) -> random.Random:
    digest = hashlib.sha256(
        f"{TASK_ID}:transform-composition-v1:{seed}:{split}:{index}".encode()
    ).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _random_support(rng: random.Random, h: int, w: int, minimum: int, maximum: int) -> list[list[int]]:
    cells = [(r, c) for r in range(h) for c in range(w)]
    count = rng.randint(minimum, maximum)
    chosen = set(rng.sample(cells, count))
    return [[int((r, c) in chosen) for c in range(w)] for r in range(h)]


def _asymmetric_support(rng: random.Random, h: int, w: int, transform: str) -> list[list[int]]:
    area = h * w
    minimum = 3 if area <= 16 else max(5, area // 12)
    maximum = min(area - 2, max(minimum + 2, area // 4))
    for _ in range(512):
        support = _random_support(rng, h, w, minimum, maximum)
        target = _apply_transform(support, transform)
        if len(_matches(support, target)) == 1:
            return support
    raise RuntimeError("failed to construct a transform-identifying support")


def _query_support(rng: random.Random, h: int, w: int, transform: str) -> list[list[int]]:
    area = h * w
    minimum = 3 if area <= 16 else max(6, area // 10)
    if h == 30 and w == 10:
        minimum = 18
    maximum = min(area - 2, max(minimum + 4, area // 4))
    for _ in range(1024):
        support = _random_support(rng, h, w, minimum, maximum)
        moved = _apply_transform(support, transform)
        if len(moved) != h or len(moved[0]) != w:
            continue
        original_cells = {(r, c) for r in range(h) for c in range(w) if support[r][c]}
        moved_cells = {(r, c) for r in range(h) for c in range(w) if moved[r][c]}
        if len(original_cells & moved_cells) >= 2 and len(original_cells ^ moved_cells) >= 2:
            return support
    raise RuntimeError("failed to construct a composition-distinguishing C support")


def _recolor(support: list[list[int]], color: int) -> list[list[int]]:
    return [[color if value else 0 for value in row] for row in support]


def _scene(seed: int, split: str, index: int) -> list[list[int]]:
    specs = DEMO_SPECS if split == "demo" else QUERY_SPECS
    h, ab_width, c_width, transform = specs[index]
    rng = _rng(seed, split, index)
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 9], 3)
    a_support = _asymmetric_support(rng, h, ab_width, transform)
    b_support = _apply_transform(a_support, transform)
    c_support = _query_support(rng, h, c_width, transform)
    panels = [
        _recolor(a_support, colors[0]),
        _recolor(b_support, colors[1]),
        _recolor(c_support, colors[2]),
    ]
    width = ab_width * 2 + c_width + 2
    result = [[0 for _ in range(width)] for _ in range(h)]
    offsets = (0, ab_width + 1, 2 * ab_width + 2)
    separators = (ab_width, 2 * ab_width + 1)
    for r in range(h):
        for separator in separators:
            result[r][separator] = 8
        for panel, left in zip(panels, offsets):
            for c, value in enumerate(panel[r]):
                result[r][left + c] = value
    # Constructor postcondition: never emit an invalid or non-distinguishing scene.
    _analyze(result)
    return result


def generate(seed: object, mode: object, demos: object, queries: object) -> dict[str, Any]:
    actual_seed = integer(seed, 0, 2**63 - 1, "seed")
    selected = setting(mode)
    demo_count = integer(demos, 2, 6, "demos")
    query_count = integer(queries, 1, 4, "queries")
    train = []
    test = []
    for index in range(demo_count):
        input_grid = _scene(actual_seed, "demo", index)
        train.append({"input": input_grid, "output": solve(input_grid, selected)})
    for index in range(query_count):
        input_grid = _scene(actual_seed, "query", index)
        test.append({"input": input_grid, "output": solve(input_grid, selected)})
    return {"train": train, "test": test}
