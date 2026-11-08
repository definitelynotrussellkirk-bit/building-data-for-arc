"""Source-bound authoring core for the largest-hole color-relay family.

The default is the exact accepted canonical rule.  The alternative first finds
true-hole components, measures their total enclosed background area, and then
uses the winning component's color to select every component of that color.
Python labels are claims; native qualification independently re-executes Racket.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys
from typing import Any, Iterable


HERE = Path(__file__).resolve().parent
TASK_HOME = HERE.parents[1]
MODES = ("all_holes", "largest_hole_color_relay")
DEFAULT_MODE = "all_holes"
CANONICAL_SHA256 = "83b51fc36bb636684688017b2a9ca7cc81a2f807a5b6d1c8bb9bf31be7323d68"
DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _load_generator():
    path = TASK_HOME / "generator.py"
    spec = importlib.util.spec_from_file_location(
        "_629ec8fd452e_parametric_generator", path
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load selected generator: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


GEN = _load_generator()


def validate_settings(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"output_scope"}:
        raise ValueError("settings must contain exactly output_scope")
    mode = settings["output_scope"]
    if type(mode) is not str or mode not in MODES:
        raise ValueError("output_scope must name one supported setting")
    return mode


def program_for(mode: str) -> str:
    if mode not in MODES:
        raise ValueError("unsupported output_scope")
    name = "canonical.rkt" if mode == DEFAULT_MODE else "largest_hole_color_relay.rkt"
    text = (HERE / name).read_text(encoding="utf-8")
    if mode == DEFAULT_MODE and hashlib.sha256(text.encode()).hexdigest() != CANONICAL_SHA256:
        raise ValueError("canonical resource bytes changed")
    return text


def _frame(height: int, width: int) -> tuple[tuple[int, int], ...]:
    return tuple(
        (r, c)
        for r in range(height)
        for c in range(width)
        if r in (0, height - 1) or c in (0, width - 1)
    )


def _open_frame(height: int, width: int, selector: int) -> tuple[tuple[int, int], ...]:
    side = selector % 4
    if side == 0:
        gap = (0, 1 + (selector // 4) % (width - 2))
    elif side == 1:
        gap = (height - 1, 1 + (selector // 4) % (width - 2))
    elif side == 2:
        gap = (1 + (selector // 4) % (height - 2), 0)
    else:
        gap = (1 + (selector // 4) % (height - 2), width - 1)
    return tuple(cell for cell in _frame(height, width) if cell != gap)


def _solid(height: int, width: int) -> tuple[tuple[int, int], ...]:
    return tuple((r, c) for r in range(height) for c in range(width))


def _double_chamber(height: int, width: int) -> tuple[tuple[int, int], ...]:
    if height < 4 or width < 7 or width % 2 == 0:
        raise ValueError("double chamber needs height >=4 and odd width >=7")
    divider = width // 2
    return tuple(sorted(set(_frame(height, width)) | {(r, divider) for r in range(1, height - 1)}))


def _frame_with_tab(height: int, width: int, side: str) -> tuple[tuple[int, int], ...]:
    cells = set(_frame(height, width))
    if side == "right":
        cells.add((height // 2, width))
    elif side == "bottom":
        cells.add((height, width // 2))
    else:
        raise ValueError("tab side must be right or bottom")
    return tuple(sorted(cells))


def _place(
    grid: list[list[int]],
    occupied: set[tuple[int, int]],
    shape: Iterable[tuple[int, int]],
    top: int,
    left: int,
    color: int,
) -> None:
    height, width = len(grid), len(grid[0])
    cells = {(top + r, left + c) for r, c in shape}
    if not cells or any(not (0 <= r < height and 0 <= c < width) for r, c in cells):
        raise ValueError("profile shape is out of bounds")
    if cells & occupied:
        raise ValueError("profile shapes overlap")
    if any((r + dr, c + dc) in occupied for r, c in cells for dr, dc in DIR4):
        raise ValueError("profile components touch orthogonally")
    for r, c in cells:
        grid[r][c] = color
    occupied.update(cells)


def _spec(shape, top, left, color_role):
    return (shape, top, left, color_role)


def _profiles(selector: int):
    gap = selector * 7 + 3
    return [
        # Demo 0: the later 5x5 frame has the largest cavity, but the earlier
        # tabbed 3x10 frame is the largest foreground component.  The tab also
        # defeats a rectangular-frame-only shortcut under the canonical rule.
        (13, 19, [
            _spec(_frame_with_tab(3, 10, "right"), 1, 1, 0),
            _spec(_frame(5, 5), 6, 8, 1),
            _spec(_solid(2, 3), 1, 15, 1),
            _spec(_open_frame(3, 4, gap), 8, 1, 0),
            _spec(_solid(3, 3), 5, 15, 2),
        ]),
        # Demo 1: the first double chamber wins by total enclosed area (18),
        # while the later 5x6 frame has the larger single chamber (12 versus 9).
        # This makes the aggregation step observable without adding a demo.
        (14, 20, [
            _spec(_double_chamber(5, 9), 1, 1, 0),
            _spec(_frame(5, 6), 9, 8, 1),
            _spec(_solid(2, 4), 9, 1, 0),
            _spec(_open_frame(3, 5, gap + 1), 1, 14, 1),
            _spec(_solid(3, 3), 5, 16, 2),
        ]),
        # Demo 2: three sources; the row-major middle source wins.
        (16, 22, [
            _spec(_frame(4, 5), 1, 1, 0),
            _spec(_frame(5, 6), 1, 9, 1),
            _spec(_frame(3, 10), 10, 1, 2),
            _spec(_open_frame(3, 6, gap + 2), 10, 14, 1),
            _spec(_solid(2, 4), 6, 1, 0),
            _spec(_solid(3, 3), 6, 18, 2),
            _spec(_open_frame(4, 5, gap + 3), 1, 17, 3),
        ]),
        # Demo 3: total area across two enclosed chambers beats one large hole.
        (17, 23, [
            _spec(_frame(6, 6), 1, 1, 0),
            _spec(_double_chamber(5, 9), 9, 10, 1),
            _spec(_solid(3, 4), 1, 15, 1),
            _spec(_open_frame(4, 6, gap + 4), 10, 1, 0),
            _spec(_solid(3, 5), 5, 18, 2),
        ]),
        # Demo 4: an irregular tabbed survivor remains a true-hole source.
        (18, 24, [
            _spec(_frame_with_tab(5, 7, "right"), 2, 2, 0),
            _spec(_frame(4, 9), 11, 12, 1),
            _spec(_frame(3, 8), 1, 14, 2),
            _spec(_solid(3, 4), 11, 2, 0),
            _spec(_open_frame(5, 5, gap + 5), 5, 18, 1),
            _spec(_solid(2, 5), 16, 14, 2),
        ]),
        # Demo 5: the last source wins and broadcasts to two relay objects.
        (19, 25, [
            _spec(_frame(4, 6), 1, 1, 0),
            _spec(_frame(5, 5), 1, 10, 1),
            _spec(_frame(6, 7), 10, 15, 2),
            _spec(_solid(2, 4), 8, 1, 2),
            _spec(_open_frame(3, 5, gap + 6), 15, 1, 2),
            _spec(_solid(3, 3), 7, 10, 0),
            _spec(_open_frame(4, 5, gap + 7), 11, 7, 1),
        ]),
        # Query 0.
        (15, 20, [
            _spec(_frame(5, 5), 1, 1, 0),
            _spec(_frame(4, 8), 8, 9, 1),
            _spec(_solid(3, 4), 1, 13, 1),
            _spec(_open_frame(4, 5, gap + 8), 9, 1, 0),
            _spec(_solid(2, 3), 5, 16, 3),
        ]),
        # Query 1.
        (18, 23, [
            _spec(_double_chamber(5, 9), 1, 1, 0),
            _spec(_frame(7, 6), 9, 13, 1),
            _spec(_frame(3, 10), 1, 13, 2),
            _spec(_solid(3, 5), 9, 1, 0),
            _spec(_open_frame(4, 7, gap + 9), 14, 1, 1),
        ]),
        # Query 2: lawful content touches left and right boundaries.
        (22, 24, [
            _spec(_frame(6, 8), 1, 0, 0),
            _spec(_frame(5, 9), 1, 15, 1),
            _spec(_double_chamber(6, 11), 12, 6, 2),
            _spec(_solid(4, 4), 9, 0, 2),
            _spec(_open_frame(5, 6, gap + 10), 14, 18, 0),
            _spec(_solid(3, 5), 8, 18, 3),
        ]),
        # Query 3: substantive 30x30 boundary stress with four true-hole
        # sources, several relays/distractors, and content on rows 0 and 29.
        (30, 30, [
            _spec(_frame(8, 10), 0, 0, 0),
            _spec(_frame(6, 10), 0, 19, 1),
            _spec(_open_frame(7, 7, gap + 11), 9, 0, 4),
            _spec(_double_chamber(9, 13), 9, 9, 2),
            _spec(_solid(5, 5), 8, 25, 5),
            _spec(_frame(7, 9), 23, 0, 3),
            _spec(_solid(4, 6), 24, 13, 2),
            _spec(_open_frame(5, 8, gap + 12), 20, 22, 1),
            _spec(_solid(4, 5), 15, 25, 0),
        ]),
    ]


def scene_inputs(seed: int, demos: int, queries: int) -> tuple[list[list[list[int]]], list[list[list[int]]]]:
    if type(seed) is not int or not 0 <= seed <= 2**63 - 1:
        raise ValueError("seed must be an integer in 0..2**63-1")
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an integer in 2..6")
    if type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError("queries must be an integer in 1..4")
    rng = random.Random(f"629ec8fd452e:parametric:{seed}:palette")
    palette = rng.sample(range(1, 10), 6)
    profiles = _profiles(seed % 97)
    grids = []
    for profile_index, (height, width, specs) in enumerate(profiles):
        # Rotate the palette by profile as a setting-independent visual change.
        colors = palette[profile_index % len(palette):] + palette[:profile_index % len(palette)]
        grid = [[0 for _ in range(width)] for _ in range(height)]
        occupied: set[tuple[int, int]] = set()
        for shape, top, left, role in specs:
            _place(grid, occupied, shape, top, left, colors[role])
        analysis = GEN._analysis(grid)
        if analysis["errors"] or len(analysis["hollow"]) < 2:
            raise ValueError("internal profile did not retain multiple true-hole components")
        grids.append(grid)
    train = grids[:demos]
    test = grids[6:6 + queries]
    serialized = [json.dumps(grid, separators=(",", ":")) for grid in train + test]
    if len(serialized) != len(set(serialized)):
        raise ValueError("internal profile produced duplicate episode inputs")
    return train, test


def _component_summary(component: dict[str, Any]) -> dict[str, Any]:
    return {
        "color": component["color"],
        "bbox": list(component["bbox"]),
        "cell_count": len(component["cells"]),
        "hole_area": sum(len(region) for region in component["holes"]),
        "hole_count": len(component["holes"]),
        "has_hole": component["has_hole"],
    }


def explain(grid: list[list[int]]) -> dict[str, Any]:
    analysis = GEN._analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid input: " + "; ".join(analysis["errors"]))
    components = analysis["components"]
    hollow = [component for component in components if component["has_hole"]]
    if not hollow:
        raise ValueError("input needs at least one true-hole component")
    source = max(hollow, key=lambda component: sum(len(region) for region in component["holes"]))
    largest_component = max(components, key=lambda component: len(component["cells"]))
    return {
        "components": [_component_summary(component) for component in components],
        "hole_components": [_component_summary(component) for component in hollow],
        "largest_hole_color": source["color"],
        "largest_hole_area": sum(len(region) for region in source["holes"]),
        "first_hole_color": hollow[0]["color"],
        "largest_component_color": largest_component["color"],
    }


def transform(grid: list[list[int]], settings: dict[str, Any]) -> list[list[int]]:
    mode = validate_settings(settings)
    analysis = GEN._analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid input: " + "; ".join(analysis["errors"]))
    if mode == DEFAULT_MODE:
        return GEN.rule_true(grid)
    hollow = [component for component in analysis["components"] if component["has_hole"]]
    if not hollow:
        raise ValueError("relay mode needs a true-hole source")
    source = max(hollow, key=lambda component: sum(len(region) for region in component["holes"]))
    relay_color = source["color"]
    out = [[0 for _ in row] for row in grid]
    for component in analysis["components"]:
        if component["color"] == relay_color:
            for row, col in component["cells"]:
                out[row][col] = relay_color
    return out


def transform_skip_hole_analysis(grid: list[list[int]]) -> list[list[int]]:
    """Counterfactual: broadcast the largest foreground component's color."""
    analysis = GEN._analysis(grid)
    if analysis["errors"] or not analysis["components"]:
        raise ValueError("input needs foreground components")
    source = max(analysis["components"], key=lambda component: len(component["cells"]))
    color = source["color"]
    out = [[0 for _ in row] for row in grid]
    for component in analysis["components"]:
        if component["color"] == color:
            for row, col in component["cells"]:
                out[row][col] = color
    return out


def teaching_check(episode: dict[str, Any]) -> dict[str, Any]:
    programs = {mode: program_for(mode) for mode in MODES}
    selected = [mode for mode, program in programs.items()
                if program == episode.get("program_solution")]
    survivors = []
    for mode in MODES:
        settings = {"output_scope": mode}
        if all(transform(pair["input"], settings) == pair["output"]
               for pair in episode.get("train", [])):
            survivors.append(mode)
    return {
        "ok": len(selected) == 1 and survivors == selected,
        "selected": selected,
        "survivors": survivors,
        "basis": "demonstrations_only",
        "finite_settings": list(MODES),
    }


def generate_episode(seed: int, mode: str, demos: int, queries: int) -> dict[str, Any]:
    if mode not in MODES:
        raise ValueError("unsupported output_scope")
    train_inputs, test_inputs = scene_inputs(seed, demos, queries)
    settings = {"output_scope": mode}
    labeled = lambda grid: {"input": deepcopy(grid), "output": transform(grid, settings)}
    episode = {
        "train": [labeled(grid) for grid in train_inputs],
        "test": [labeled(grid) for grid in test_inputs],
        "program_solution": program_for(mode),
        "settings": dict(settings),
        "seed": seed,
    }
    certificate = teaching_check(episode)
    if not certificate["ok"]:
        raise ValueError("constructive demonstrations did not identify the setting")
    return episode


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    return {
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": deepcopy(pair["input"])} for pair in episode["test"]],
    }


def public_bytes(episode: dict[str, Any]) -> bytes:
    from reviewer_support import public_challenge_bytes
    return public_challenge_bytes(public_challenge(episode))


def public_filename(episode: dict[str, Any]) -> str:
    return hashlib.sha256(public_bytes(episode)).hexdigest() + ".json"
