"""Constructive finite hole-selection family for task 24bb2221ca5c.

Inputs are generated independently of the hidden ``fill_policy``.  Every
mandatory scene contains three closed same-color components with deliberately
separated topology statistics plus one open side-gap control:

* a one-hole component with the greatest enclosed area;
* a larger-bbox dense component with two tiny holes;
* a second one-hole ring reusing the first component's color; and
* a side-gap frame whose interior is exterior-connected and must stay empty.

Python outputs are private label claims.  Native qualification and ``audit.py``
execute the exact materialized programs through the protected Racket runtime.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
from pathlib import Path
import random
from typing import Any


TASK_ID = "24bb2221ca5c"
POLICIES = ("all", "largest_hole_area", "most_holes")
DEMO_SHAPES = ((14, 18), (16, 20), (18, 22), (20, 24), (22, 26), (24, 28))
QUERY_SHAPES = ((17, 21), (21, 25), (25, 27), (30, 30))
HERE = Path(__file__).resolve().parent


def _load_exact(path: Path, prefix: str):
    source = path.read_bytes()
    name = prefix + hashlib.sha256(str(path).encode() + source).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load exact source {path}")
    module = importlib.util.module_from_spec(spec)
    exec(compile(source, str(path), "exec"), module.__dict__)
    return module


RULES = _load_exact(HERE / "rules.py", "_24bb_parametric_rules_")
GENERATOR = _load_exact(HERE.parent.parent / "generator.py", "_24bb_generator_")


def _integer(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _rng(seed: int, role: str, index: int) -> random.Random:
    material = f"{TASK_ID}:hole-selection-v1:{seed}:{role}:{index}".encode("ascii")
    return random.Random(int.from_bytes(hashlib.sha256(material).digest(), "big"))


def _perimeter(top: int, left: int, height: int, width: int) -> set[tuple[int, int]]:
    bottom, right = top + height - 1, left + width - 1
    return {
        (row, col)
        for row in range(top, bottom + 1)
        for col in range(left, right + 1)
        if row in (top, bottom) or col in (left, right)
    }


def _solid(top: int, left: int, height: int, width: int) -> set[tuple[int, int]]:
    return {
        (row, col)
        for row in range(top, top + height)
        for col in range(left, left + width)
    }


def _paint(grid: list[list[int]], cells: set[tuple[int, int]], color: int) -> None:
    height, width = len(grid), len(grid[0])
    if not cells:
        raise RuntimeError("constructive motif must contain cells")
    for row, col in cells:
        if not (0 <= row < height and 0 <= col < width):
            raise RuntimeError("constructive motif escaped its ARC canvas")
        if grid[row][col] != 0:
            raise RuntimeError("constructive motifs unexpectedly overlap")
    for row, col in cells:
        grid[row][col] = color


def _large_area_component(
    top: int,
    left: int,
    height: int,
    width: int,
    *,
    nonrectangular_hole: bool,
    corner: int,
) -> set[tuple[int, int]]:
    if nonrectangular_hole:
        cells = _solid(top, left, height, width)
        inner_bottom = top + height - 2
        vertical = {(row, left + 1) for row in range(top + 1, inner_bottom + 1)}
        horizontal = {
            (inner_bottom, col) for col in range(left + 1, left + width - 1)
        }
        cells.difference_update(vertical | horizontal)
        return cells

    cells = _perimeter(top, left, height, width)
    corners = (
        (top, left),
        (top, left + width - 1),
        (top + height - 1, left),
        (top + height - 1, left + width - 1),
    )
    cells.remove(corners[corner % len(corners)])
    return cells


def _multi_hole_bbox_rival(
    top: int, left: int, height: int, width: int
) -> set[tuple[int, int]]:
    cells = _solid(top, left, height, width)
    # Two separated regions totaling five cells.  This component still has the
    # most holes, but the one-hole ring below has the smallest total hole area.
    first_region = {(top + 1, left + 1), (top + 1, left + 2)}
    second_region = {
        (top + height - 2, left + width - 2),
        (top + height - 2, left + width - 3),
        (top + height - 3, left + width - 2),
    }
    cells.difference_update(first_region | second_region)
    return cells


def _scene(seed: int, role: str, index: int) -> list[list[int]]:
    shapes = DEMO_SHAPES if role == "demo" else QUERY_SHAPES
    height, width = shapes[index]
    rng = _rng(seed, role, index)
    colors = rng.sample(range(1, 10), 3)
    large_color, multi_color, open_color = colors
    grid = [[0 for _ in range(width)] for _ in range(height)]

    row_split, col_split = height // 2, width // 2
    top_height, right_width = row_split, width - col_split - 1
    bottom_height, left_width = height - row_split - 1, col_split

    # Top-left: largest enclosed area.  It touches the left border and is
    # always smaller in bbox area than the dense top-right component.
    large_height = top_height - 1
    large_width = left_width - 2
    large_top, large_left = (0 if index % 2 else 1), 0
    nonrectangular = (role == "demo" and index % 3 == 1) or (
        role == "query" and index in (1, 3)
    )
    large_cells = _large_area_component(
        large_top,
        large_left,
        large_height,
        large_width,
        nonrectangular_hole=nonrectangular,
        corner=rng.randrange(4),
    )
    _paint(grid, large_cells, large_color)

    # Top-right: the largest bbox, but only two singleton holes.  It touches
    # the top and right canvas borders and therefore defeats border-skip and
    # largest-bbox shortcuts while remaining a valid closed component.
    multi_top, multi_left = (1 if index % 2 else 0), col_split + 1
    multi_height, multi_width = top_height - 1, right_width
    multi_cells = _multi_hole_bbox_rival(
        multi_top, multi_left, multi_height, multi_width
    )
    _paint(grid, multi_cells, multi_color)

    # Bottom-left: another closed component in the large component's color.
    # This forces component-local handling instead of merging by color.
    ring_height = ring_width = 4
    ring_top, ring_left = height - ring_height, 0
    ring_cells = _perimeter(ring_top, ring_left, ring_height, ring_width)
    # Sparse connected arms make this component's bbox the largest without
    # adding another hole or increasing its enclosed area.
    ring_cells.update((row, ring_left) for row in range(row_split + 1, ring_top + 1))
    ring_cells.update((ring_top, col) for col in range(ring_left, col_split))
    _paint(grid, ring_cells, large_color)

    # Bottom-right: a side gap opens the interior under 4-connectivity.
    open_height = min(8, bottom_height)
    open_width = min(9, right_width)
    open_top, open_left = height - open_height, width - open_width
    open_cells = _perimeter(open_top, open_left, open_height, open_width)
    open_cells.remove((open_top, open_left + open_width // 2))
    _paint(grid, open_cells, open_color)

    profiles = component_profiles(grid)
    closed = [profile for profile in profiles if profile["hole_count"]]
    if len(closed) != 3:
        raise RuntimeError(f"constructive scene lost a closed component: {profiles}")
    area_order = sorted(closed, key=lambda p: p["hole_area"], reverse=True)
    count_order = sorted(closed, key=lambda p: p["hole_count"], reverse=True)
    bbox_order = sorted(closed, key=lambda p: p["bbox_area"], reverse=True)
    if not (
        area_order[0]["hole_area"] > area_order[1]["hole_area"]
        and count_order[0]["hole_count"] > count_order[1]["hole_count"]
        and len({
            area_order[0]["component_index"],
            count_order[0]["component_index"],
            bbox_order[0]["component_index"],
        }) == 3
        and any(profile["side_gap"] and not profile["hole_count"] for profile in profiles)
    ):
        raise RuntimeError("constructive topology statistics are no longer separated")
    return grid


def _rectangular(region: set[tuple[int, int]]) -> bool:
    if not region:
        return False
    rows = [row for row, _ in region]
    cols = [col for _, col in region]
    return len(region) == (max(rows) - min(rows) + 1) * (max(cols) - min(cols) + 1)


def component_profiles(grid: list[list[int]]) -> list[dict[str, Any]]:
    """Return grid-derived topology diagnostics in component reading order."""
    error = GENERATOR._valid_grid_shape(grid)
    if error:
        raise ValueError(error)
    height, width = len(grid), len(grid[0])
    result = []
    for index, (color, cells) in enumerate(GENERATOR._component_cells(grid)):
        row0, col0, row1, col1 = GENERATOR._bbox(cells)
        border = GENERATOR._perimeter(row0, col0, row1, col1)
        missing = border - cells
        corners = {
            (row0, col0),
            (row0, col1),
            (row1, col0),
            (row1, col1),
        }
        regions = GENERATOR._component_hole_regions(cells)
        result.append(
            {
                "component_index": index,
                "color": color,
                "cell_count": len(cells),
                "bbox": [row0, col0, row1, col1],
                "bbox_area": (row1 - row0 + 1) * (col1 - col0 + 1),
                "hole_count": len(regions),
                "hole_area": sum(len(region) for region in regions),
                "rectangular_holes": [_rectangular(region) for region in regions],
                "corner_gap": len(missing) == 1 and next(iter(missing)) in corners,
                "side_gap": len(missing) == 1 and next(iter(missing)) not in corners,
                "touches_canvas_border": any(
                    row in (0, height - 1) or col in (0, width - 1)
                    for row, col in cells
                ),
            }
        )
    return result


def transform(grid: list[list[int]], policy: str) -> list[list[int]]:
    """Independent Python diagnostic mirror of one declared fixed rule."""
    if type(policy) is not str or policy not in POLICIES:
        raise ValueError("fill_policy must be all, largest_hole_area, or most_holes")
    error = GENERATOR._valid_grid_shape(grid)
    if error:
        raise ValueError(error)
    candidates = []
    for color, cells in GENERATOR._component_cells(grid):
        regions = GENERATOR._component_hole_regions(cells)
        if regions:
            holes = set().union(*regions)
            candidates.append((color, holes, regions))

    output = deepcopy(grid)
    if policy == "all":
        selected = candidates
    elif not candidates:
        selected = []
    elif policy == "largest_hole_area":
        selected = [max(candidates, key=lambda item: len(item[1]))]
    else:
        selected = [max(candidates, key=lambda item: len(item[2]))]
    for color, holes, _regions in selected:
        for row, col in holes:
            output[row][col] = color
    return output


def sample_inputs(seed: int, *, demos: int = 3, queries: int = 4) -> dict[str, list]:
    """Return stable independent prefixes from the full bounded scene pools."""
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, len(DEMO_SHAPES), "demos")
    _integer(queries, 1, len(QUERY_SHAPES), "queries")
    return {
        "train": [_scene(seed, "demo", index) for index in range(demos)],
        "test": [_scene(seed, "query", index) for index in range(queries)],
    }


def generate(seed: int, settings: dict, demos: int = 3, queries: int = 4) -> dict:
    """Build one private fixed-setting episode with Python label claims."""
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, len(DEMO_SHAPES), "demos")
    _integer(queries, 1, len(QUERY_SHAPES), "queries")
    exact_program = RULES.program(settings)
    policy = settings["fill_policy"]
    inputs = sample_inputs(seed, demos=demos, queries=queries)
    train = [
        {"input": grid, "output": transform(grid, policy)} for grid in inputs["train"]
    ]
    test = [
        {"input": grid, "output": transform(grid, policy)} for grid in inputs["test"]
    ]
    survivors = [
        candidate
        for candidate in POLICIES
        if all(
            transform(pair["input"], candidate) == pair["output"] for pair in train
        )
    ]
    if survivors != [policy]:
        raise RuntimeError(
            f"constructed demonstrations do not identify {policy}: {survivors}"
        )
    return {"train": train, "test": test, "program_solution": exact_program}


def public_turn(episode: dict, query_index: int = 0) -> dict:
    """Expose demonstrations and exactly one masked query input."""
    if (
        type(episode) is not dict
        or type(episode.get("train")) is not list
        or type(episode.get("test")) is not list
    ):
        raise ValueError("episode must contain train and test lists")
    if type(query_index) is not int or not 0 <= query_index < len(episode["test"]):
        raise ValueError("query_index must identify one available query")
    return {
        "train": deepcopy(episode["train"]),
        "test": [{"input": deepcopy(episode["test"][query_index]["input"])}],
    }
