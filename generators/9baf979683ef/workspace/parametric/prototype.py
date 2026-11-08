"""Divider reflection with an episode-fixed receiver post-action.

The canonical setting preserves the exact selected Racket source.  The alternate
setting first executes that mirror, then finds the unique color-9 receiver
component touched by a newly mirrored source cell and recolors the entire
receiver with the touching source color.
"""
from __future__ import annotations

from collections import deque
import copy
import hashlib
from pathlib import Path
import random
from typing import Any, Iterable


TASK_ID = "9baf979683ef"
ACTIONS = ("preserve", "absorb_color")
SOURCE_COLORS = (1, 2, 3, 4, 6, 7, 8)
CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
CANONICAL_PATH = Path(__file__).with_name("canonical.rkt")
CANONICAL = CANONICAL_PATH.read_text(encoding="utf-8")

# The first two demonstrations deliberately swap both receiver-size and
# horizontal-position ranks.  This constructively refutes common shortcuts at
# the minimum supported demonstration count.
TRAIN_PROFILES = (
    # height, width, target size, horizontal rank, decoy sizes, source count
    (9, 15, 2, "leftmost", (4, 6), 8),
    (10, 17, 7, "rightmost", (1, 3), 10),
    (11, 18, 4, "leftmost", (2, 7), 12),
    (12, 19, 3, "rightmost", (5, 8), 14),
    (14, 21, 8, "leftmost", (2, 5), 17),
    (16, 23, 5, "rightmost", (2, 9), 20),
)
TEST_PROFILES = (
    (10, 16, 3, "leftmost", (5, 7), 11),
    (13, 20, 9, "rightmost", (2, 4), 15),
    (18, 25, 6, "leftmost", (3, 9, 11), 21),
    (30, 30, 10, "rightmost", (2, 4, 7), 28),
)


def _integer(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _action(settings: Any) -> str:
    if (
        type(settings) is not dict
        or set(settings) != {"receiver_action"}
        or type(settings["receiver_action"]) is not str
        or settings["receiver_action"] not in ACTIONS
    ):
        raise ValueError(
            "settings must be exactly {'receiver_action': 'preserve'|'absorb_color'}"
        )
    return settings["receiver_action"]


def _body(source: str) -> str:
    if not source.startswith("(rule! ") or not source.endswith(")"):
        raise ValueError("canonical source is not one outer rule! form")
    return source[len("(rule! ") : -1]


def program(settings: dict[str, Any]) -> str:
    """Return complete exact Racket source for one declared setting."""
    action = _action(settings)
    if action == "preserve":
        return CANONICAL
    canonical_body = _body(CANONICAL)
    return f"""(rule! (let* ((intermediate {canonical_body})
                    (h (rows intermediate))
                    (w (cols intermediate))
                    (source-color?
                     (lambda (v)
                       (and (not (= v 0)) (not (= v 5)) (not (= v 9)))))
                    (touch-color
                     (lambda (obj)
                       (find-first
                        (lambda (color)
                          (and (source-color? color)
                               (for/or ((p (in-list (obj-cells obj))))
                                 (for/or ((d (in-list cardinal-deltas)))
                                   (let ((r (+ (first p) (first d)))
                                         (c (+ (second p) (second d))))
                                     (and (in-bounds? r c h w)
                                          (= (at intermediate r c) color)))))))
                        (grid-colors intermediate)))))
               (for/fold ((out intermediate))
                         ((obj (in-list
                                (filter (lambda (o) (= (obj-color o) 9))
                                        (objects intermediate 0)))))
                 (let ((color (touch-color obj)))
                   (if color
                       (paint-cells out (obj-cells obj) color)
                       out)))))"""


def _rng(seed: int, split: str, index: int, purpose: str) -> random.Random:
    material = f"{TASK_ID}/receiver-v1/{seed}/{split}/{index}/{purpose}".encode("ascii")
    return random.Random(int.from_bytes(hashlib.sha256(material).digest(), "big"))


def _neighbors(cell: tuple[int, int]) -> Iterable[tuple[int, int]]:
    r, c = cell
    for dr, dc in CARDINAL:
        yield r + dr, c + dc


def _connected_components(cells: set[tuple[int, int]]) -> list[set[tuple[int, int]]]:
    unseen = set(cells)
    result: list[set[tuple[int, int]]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        component = {start}
        queue = deque([start])
        while queue:
            cell = queue.popleft()
            for neighbor in _neighbors(cell):
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    component.add(neighbor)
                    queue.append(neighbor)
        result.append(component)
    return result


def _target_component(
    height: int,
    width: int,
    divider: int,
    size: int,
    horizontal_rank: str,
) -> tuple[set[tuple[int, int]], tuple[int, int], tuple[int, int]]:
    if horizontal_rank == "rightmost":
        contact_col = width - 1
        target_height = size
        contact_row = max(0, (height - target_height) // 2)
        cells = {(contact_row + i, contact_col) for i in range(size)}
    else:
        contact_col = divider + 3
        target_height = (size + 1) // 2
        contact_row = max(0, min(height - target_height, height // 2 - target_height // 2))
        cells = {
            (contact_row + i // 2, contact_col + i % 2)
            for i in range(size)
        }
    mirror_anchor = contact_row, contact_col - 1
    source_anchor = contact_row, 2 * divider - mirror_anchor[1]
    if not (0 <= source_anchor[1] < divider):
        raise ValueError("profile cannot place the source anchor")
    return cells, mirror_anchor, source_anchor


def _shape_variants(size: int) -> list[set[tuple[int, int]]]:
    variants = [
        {(i, 0) for i in range(size)},
        {(0, i) for i in range(size)},
        {(i // 2, i % 2) for i in range(size)},
    ]
    unique: list[set[tuple[int, int]]] = []
    seen = set()
    for cells in variants:
        key = tuple(sorted(cells))
        if key not in seen:
            seen.add(key)
            unique.append(cells)
    return unique


def _translate(shape: set[tuple[int, int]], row: int, col: int) -> set[tuple[int, int]]:
    return {(row + r, col + c) for r, c in shape}


def _adjacent_or_overlap(a: set[tuple[int, int]], b: set[tuple[int, int]]) -> bool:
    if a & b:
        return True
    return any(neighbor in b for cell in a for neighbor in _neighbors(cell))


def _decoy_candidates(
    *,
    height: int,
    width: int,
    divider: int,
    size: int,
    horizontal_rank: str,
    target: set[tuple[int, int]],
    mirror_cells: set[tuple[int, int]],
) -> list[set[tuple[int, int]]]:
    candidates: list[set[tuple[int, int]]] = []
    target_min = min(c for _, c in target)
    target_max = max(c for _, c in target)
    for shape in _shape_variants(size):
        shape_h = max(r for r, _ in shape) + 1
        shape_w = max(c for _, c in shape) + 1
        for row in range(height - shape_h + 1):
            for col in range(divider + 1, width - shape_w + 1):
                cells = _translate(shape, row, col)
                if horizontal_rank == "leftmost" and min(c for _, c in cells) <= target_min:
                    continue
                if horizontal_rank == "rightmost" and max(c for _, c in cells) >= target_max:
                    continue
                if _adjacent_or_overlap(cells, target):
                    continue
                if _adjacent_or_overlap(cells, mirror_cells):
                    continue
                candidates.append(cells)
    return candidates


def _place_decoys(
    *,
    height: int,
    width: int,
    divider: int,
    sizes: tuple[int, ...],
    horizontal_rank: str,
    target: set[tuple[int, int]],
    mirror_cells: set[tuple[int, int]],
    rng: random.Random,
) -> list[set[tuple[int, int]]]:
    """Place all decoys with a bounded backtracking search.

    A one-pass greedy draw can consume the only footprint needed by the next
    receiver.  Joint placement makes each declared profile total while retaining
    deterministic seed-controlled geometry.
    """
    ordered = sorted(sizes, reverse=True)
    candidate_lists = []
    for size in ordered:
        candidates = _decoy_candidates(
            height=height,
            width=width,
            divider=divider,
            size=size,
            horizontal_rank=horizontal_rank,
            target=target,
            mirror_cells=mirror_cells,
        )
        rng.shuffle(candidates)
        if not candidates:
            raise ValueError(f"could not place decoy receiver of size {size}")
        candidate_lists.append(candidates)

    selected: list[set[tuple[int, int]]] = []

    def search(index: int, occupied: set[tuple[int, int]]) -> bool:
        if index == len(candidate_lists):
            return True
        for component in candidate_lists[index]:
            if _adjacent_or_overlap(component, occupied):
                continue
            selected.append(component)
            if search(index + 1, occupied | component):
                return True
            selected.pop()
        return False

    if not search(0, set(target)):
        raise ValueError(f"could not jointly place decoy receivers {tuple(ordered)}")
    return selected


def _profile(split: str, index: int) -> tuple[int, int, int, str, tuple[int, ...], int]:
    profiles = TRAIN_PROFILES if split == "train" else TEST_PROFILES
    return profiles[index]


def sample_input(seed: int, split: str, index: int) -> list[list[int]]:
    """Construct one setting-neutral scene without retries."""
    _integer(seed, 0, 2**63 - 1, "seed")
    if type(split) is not str or split not in ("train", "test"):
        raise ValueError("split must be 'train' or 'test'")
    maximum = len(TRAIN_PROFILES) - 1 if split == "train" else len(TEST_PROFILES) - 1
    _integer(index, 0, maximum, "index")
    height, width, target_size, horizontal_rank, decoy_sizes, source_count = _profile(split, index)
    divider = width // 2
    target, mirror_anchor, source_anchor = _target_component(
        height, width, divider, target_size, horizontal_rank
    )

    source_cells = {source_anchor}
    # A short line toward the divider makes the mirror operation visually
    # explicit while keeping only its far endpoint adjacent to the receiver.
    for step in range(1, 3):
        cell = source_anchor[0], source_anchor[1] + step
        mirror = cell[0], 2 * divider - cell[1]
        if cell[1] < divider and not _adjacent_or_overlap({mirror}, target):
            source_cells.add(cell)

    # Reserve the receiver geometry before filling the source field.  Future
    # mirrored cells are then sampled around those reserved components, instead
    # of letting a dense random mirror field make receiver placement impossible.
    primary_mirrors = {(row, 2 * divider - col) for row, col in source_cells}
    receiver_components = [set(target)]
    receiver_components.extend(
        _place_decoys(
            height=height,
            width=width,
            divider=divider,
            sizes=decoy_sizes,
            horizontal_rank=horizontal_rank,
            target=target,
            mirror_cells=primary_mirrors,
            rng=_rng(seed, split, index, "decoys"),
        )
    )
    receivers = set().union(*receiver_components)

    legal_min = max(0, 2 * divider - (width - 1))
    candidates = [
        (row, col)
        for row in range(height)
        for col in range(legal_min, divider)
        if (row, col) not in source_cells
        and not _adjacent_or_overlap({(row, 2 * divider - col)}, receivers)
    ]
    rng = _rng(seed, split, index, "source")
    rng.shuffle(candidates)

    # Guarantee meaningful boundary content before filling the remaining spread.
    boundary_candidates = [
        cell
        for cell in candidates
        if cell[0] in (0, height - 1) or cell[1] == legal_min
    ]
    for cell in boundary_candidates[: min(3, source_count - len(source_cells))]:
        source_cells.add(cell)
        candidates.remove(cell)
    for cell in candidates:
        if len(source_cells) >= source_count:
            break
        source_cells.add(cell)
    if len(source_cells) != source_count:
        raise ValueError("profile cannot realize requested source count")

    mirror_cells = {(row, 2 * divider - col) for row, col in source_cells}
    if mirror_anchor not in mirror_cells:
        raise ValueError("anchor reflection was lost")

    grid = [[0 for _ in range(width)] for _ in range(height)]
    for row in range(height):
        grid[row][divider] = 5
    for row, col in receivers:
        grid[row][col] = 9

    contact_palette = (1, 3, 6, 2, 7, 4, 8)
    contact_color = contact_palette[(seed + index + (0 if split == "train" else 3)) % len(contact_palette)]
    color_rng = _rng(seed, split, index, "colors")
    palette = list(SOURCE_COLORS)
    color_rng.shuffle(palette)
    ordered = sorted(source_cells)
    for position, (row, col) in enumerate(ordered):
        grid[row][col] = contact_color if (row, col) == source_anchor else palette[position % len(palette)]

    errors = domain_errors(grid)
    if errors:
        raise ValueError("internal receiver scene failure: " + "; ".join(errors))
    return grid


def _basic_analysis(grid: Any) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        return ["grid must be a non-empty list of non-empty rows"], {}
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        return ["grid must be rectangular"], {}
    height = len(grid)
    if not (1 <= height <= 30 and 1 <= width <= 30):
        errors.append("grid dimensions must be in 1..30")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        errors.append("grid values must be exact integer ARC colors 0..9")
        return errors, {"height": height, "width": width}
    dividers = [
        col for col in range(width) if all(grid[row][col] == 5 for row in range(height))
    ]
    if len(dividers) != 1:
        errors.append(f"expected one full-height color-5 divider, got {dividers}")
        return errors, {"height": height, "width": width}
    divider = dividers[0]
    if any(grid[r][c] == 5 for r in range(height) for c in range(width) if c != divider):
        errors.append("color 5 may occur only in the divider")
    source = {
        (r, c)
        for r in range(height)
        for c in range(divider)
        if grid[r][c] not in (0, 5)
    }
    if any(grid[r][c] == 9 for r, c in source):
        errors.append("source cells may not use receiver color 9")
    if len(source) < 6:
        errors.append("need at least six source cells")
    right_nonzero = {
        (r, c)
        for r in range(height)
        for c in range(divider + 1, width)
        if grid[r][c] != 0
    }
    if any(grid[r][c] != 9 for r, c in right_nonzero):
        errors.append("initial right-side content must consist only of color-9 receivers")
    mirror_cells = set()
    for r, c in source:
        mc = 2 * divider - c
        if not 0 <= mc < width:
            errors.append(f"reflection of {(r, c)} is out of bounds")
            continue
        mirror_cells.add((r, mc))
        if grid[r][mc] != 0:
            errors.append(f"reflection target {(r, mc)} is not empty")
    receiver_cells = {(r, c) for r, c in right_nonzero if grid[r][c] == 9}
    components = _connected_components(receiver_cells)
    if len(components) < 3:
        errors.append("need at least three separate receiver components")
    if len({len(component) for component in components}) != len(components):
        errors.append("receiver component sizes must be distinct")
    return errors, {
        "height": height,
        "width": width,
        "divider": divider,
        "source": source,
        "mirror_cells": mirror_cells,
        "receiver_components": components,
    }


def _mirror_without_validation(grid: list[list[int]], analysis: dict[str, Any]) -> list[list[int]]:
    result = [row[:] for row in grid]
    divider = analysis["divider"]
    for row, col in analysis["source"]:
        result[row][2 * divider - col] = grid[row][col]
    return result


def _contact_info(
    intermediate: list[list[int]], analysis: dict[str, Any]
) -> list[tuple[set[tuple[int, int]], set[int], set[tuple[int, int]]]]:
    result = []
    mirrors = analysis["mirror_cells"]
    for component in analysis["receiver_components"]:
        adjacent_mirrors = {
            neighbor
            for cell in component
            for neighbor in _neighbors(cell)
            if neighbor in mirrors
        }
        colors = {intermediate[r][c] for r, c in adjacent_mirrors}
        result.append((component, colors, adjacent_mirrors))
    return result


def domain_errors(grid: Any) -> list[str]:
    errors, analysis = _basic_analysis(grid)
    if errors:
        return errors
    intermediate = _mirror_without_validation(grid, analysis)
    touched = [entry for entry in _contact_info(intermediate, analysis) if entry[1]]
    if len(touched) != 1:
        errors.append(f"expected one contacted receiver, got {len(touched)}")
    elif len(touched[0][1]) != 1:
        errors.append("contacted receiver must see exactly one mirrored source color")
    return errors


def _analysis(grid: list[list[int]]) -> tuple[dict[str, Any], list[list[int]], tuple]:
    errors, analysis = _basic_analysis(grid)
    if errors:
        raise ValueError("invalid receiver scene: " + "; ".join(errors))
    intermediate = _mirror_without_validation(grid, analysis)
    touched = [entry for entry in _contact_info(intermediate, analysis) if entry[1]]
    if len(touched) != 1 or len(touched[0][1]) != 1:
        raise ValueError("invalid receiver contact structure")
    return analysis, intermediate, touched[0]


def mirror(grid: list[list[int]]) -> list[list[int]]:
    analysis, intermediate, _ = _analysis(grid)
    del analysis
    return intermediate


def transform(grid: list[list[int]], action: str) -> list[list[int]]:
    if type(action) is not str or action not in ACTIONS:
        raise ValueError(f"unknown receiver action: {action!r}")
    _, intermediate, (target, colors, _) = _analysis(grid)
    if action == "preserve":
        return intermediate
    color = next(iter(colors))
    result = [row[:] for row in intermediate]
    for row, col in target:
        result[row][col] = color
    return result


def observables(grid: list[list[int]]) -> dict[str, Any]:
    analysis, intermediate, (target, colors, adjacent) = _analysis(grid)
    components = analysis["receiver_components"]
    sizes = sorted(len(component) for component in components)
    size = len(target)
    size_rank = "smallest" if size == sizes[0] else "largest" if size == sizes[-1] else "middle"
    positions = sorted(min(c for _, c in component) for component in components)
    target_position = min(c for _, c in target)
    horizontal_rank = (
        "leftmost"
        if target_position == positions[0]
        else "rightmost"
        if target_position == positions[-1]
        else "middle"
    )
    return {
        "height": analysis["height"],
        "width": analysis["width"],
        "divider": analysis["divider"],
        "source_count": len(analysis["source"]),
        "receiver_count": len(components),
        "receiver_sizes": sizes,
        "target_size": size,
        "target_size_rank": size_rank,
        "target_horizontal_rank": horizontal_rank,
        "contact_color": next(iter(colors)),
        "contact_cells": sorted(adjacent),
        "selected_receiver_cells": sorted(target),
        "touches_right_boundary": any(c == analysis["width"] - 1 for _, c in target),
        "intermediate": intermediate,
    }


def _recolor_cells(grid: list[list[int]], cells: Iterable[tuple[int, int]], color: int) -> list[list[int]]:
    result = [row[:] for row in grid]
    for row, col in cells:
        result[row][col] = color
    return result


def rival_output(grid: list[list[int]], name: str) -> list[list[int]]:
    analysis, intermediate, (target, colors, adjacent) = _analysis(grid)
    color = next(iter(colors))
    components = analysis["receiver_components"]
    if name == "all_receivers":
        return _recolor_cells(intermediate, set().union(*components), color)
    if name == "contact_cell_only":
        cells = {
            cell
            for cell in target
            if any(neighbor in adjacent for neighbor in _neighbors(cell))
        }
        return _recolor_cells(intermediate, cells, color)
    if name == "fixed_color_two":
        return _recolor_cells(intermediate, target, 2)
    if name == "largest_receiver":
        chosen = max(components, key=lambda component: (len(component), sorted(component)))
        return _recolor_cells(intermediate, chosen, color)
    if name == "smallest_receiver":
        chosen = min(components, key=lambda component: (len(component), sorted(component)))
        return _recolor_cells(intermediate, chosen, color)
    if name in ("leftmost_receiver", "nearest_divider"):
        chosen = min(components, key=lambda component: (min(c for _, c in component), sorted(component)))
        return _recolor_cells(intermediate, chosen, color)
    raise ValueError(f"unknown rival: {name!r}")


RIVAL_NAMES = (
    "all_receivers",
    "contact_cell_only",
    "fixed_color_two",
    "largest_receiver",
    "leftmost_receiver",
    "nearest_divider",
    "smallest_receiver",
)


def teaching_report(
    demos: list[dict[str, Any]], queries: list[dict[str, Any]], selected: str
) -> dict[str, Any]:
    if type(selected) is not str or selected not in ACTIONS:
        raise ValueError("selected action is invalid")
    for split_name, pairs in (("demonstration", demos), ("query", queries)):
        if type(pairs) is not list or not pairs:
            raise ValueError(f"{split_name} pairs must be non-empty")
        for pair in pairs:
            if type(pair) is not dict or set(pair) < {"input", "output"}:
                raise ValueError(f"{split_name} pair is malformed")
            if pair["output"] != transform(pair["input"], selected):
                raise ValueError(f"{split_name} label does not match selected action")

    setting_survivors = [
        action
        for action in ACTIONS
        if all(transform(pair["input"], action) == pair["output"] for pair in demos)
    ]
    rival_rows = {}
    for name in RIVAL_NAMES:
        demo_disagreements = [
            index
            for index, pair in enumerate(demos)
            if rival_output(pair["input"], name) != pair["output"]
        ]
        query_disagreements = [
            index
            for index, pair in enumerate(queries)
            if rival_output(pair["input"], name) != pair["output"]
        ]
        rival_rows[name] = {
            "matches_all_demonstrations": not demo_disagreements,
            "demonstration_disagreements": demo_disagreements,
            "query_disagreements": query_disagreements,
        }
    surviving_rivals = [
        name for name, row in rival_rows.items() if row["matches_all_demonstrations"]
    ]
    query_ambiguities = [
        {"kind": "setting", "name": action}
        for action in setting_survivors
        if action != selected
        and any(transform(pair["input"], action) != pair["output"] for pair in queries)
    ] + [
        {"kind": "rival", "name": name}
        for name in surviving_rivals
        if rival_rows[name]["query_disagreements"]
    ]
    return {
        "selected_setting": selected,
        "surviving_settings": setting_survivors,
        "tested_rivals": list(RIVAL_NAMES),
        "surviving_rivals": surviving_rivals,
        "query_ambiguities": query_ambiguities,
        "rivals": rival_rows,
    }


def generate(seed: int, settings: dict[str, Any], demos: int, queries: int) -> dict[str, Any]:
    """Generate independent-count pairs with four stable controller-side queries."""
    _integer(seed, 0, 2**63 - 1, "seed")
    action = _action(settings)
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    train = []
    test = []
    for split, count, target in (("train", demos, train), ("test", queries, test)):
        for index in range(count):
            grid = sample_input(seed, split, index)
            target.append({"input": grid, "output": transform(grid, action)})
    return {
        "seed": seed,
        "settings": {"receiver_action": action},
        "train": train,
        "test": test,
        "program_solution": program({"receiver_action": action}),
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Return the model-visible projection: demos labeled, queries input-only."""
    return {
        "train": [
            {"input": copy.deepcopy(pair["input"]), "output": copy.deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": copy.deepcopy(pair["input"])} for pair in episode["test"]],
    }


def _apply_b_to_intermediate(
    original: list[list[int]], intermediate: list[list[int]]
) -> tuple[list[list[int]], list[tuple[int, int]]]:
    """Apply B to the actual source-colored contacts in ``intermediate``.

    Counterfactual intermediates may omit the mirrored cells predicted from the
    original input.  Inspecting those predicted coordinates would treat an empty
    zero as a contact and would not match the standalone Racket B program.
    """
    errors, analysis = _basic_analysis(original)
    if errors:
        raise ValueError("invalid original scene")
    height = len(intermediate)
    width = len(intermediate[0])
    touched = []
    for component in analysis["receiver_components"]:
        adjacent = {
            neighbor
            for cell in component
            for neighbor in _neighbors(cell)
            if 0 <= neighbor[0] < height
            and 0 <= neighbor[1] < width
            and intermediate[neighbor[0]][neighbor[1]] not in (0, 5, 9)
        }
        colors = {intermediate[row][col] for row, col in adjacent}
        if colors:
            touched.append((component, colors, adjacent))
    if len(touched) != 1 or len(touched[0][1]) != 1:
        return [row[:] for row in intermediate], []
    target, colors, _ = touched[0]
    return _recolor_cells(intermediate, target, next(iter(colors))), sorted(target)


def causal_witness(seed: int = 0) -> dict[str, Any]:
    grid = sample_input(seed, "train", 0)
    analysis, intermediate, (target, _, adjacent) = _analysis(grid)
    final_output, selected = _apply_b_to_intermediate(grid, intermediate)
    skip_a_output, _ = _apply_b_to_intermediate(grid, [row[:] for row in grid])
    wrong = [row[:] for row in intermediate]
    contact = min(adjacent)
    wrong[contact[0]][contact[1]] = 0
    wrong_intermediate_output, _ = _apply_b_to_intermediate(grid, wrong)
    return {
        "schema": "arcpuzzles-sequential-witness-v1",
        "task_id": TASK_ID,
        "settings": {"receiver_action": "absorb_color"},
        "step_a": "mirror every left-side source cell across the divider",
        "intermediate_description": "the mirrored copy creates the only source-color contact with one color-9 receiver",
        "step_b": "recolor the contacted receiver component with the adjacent mirrored color",
        "why_b_depends_on_a": "before A, no receiver touches a source color; deleting the mirrored contact prevents receiver selection",
        "input": grid,
        "intermediate": intermediate,
        "selected_receiver_cells": selected or sorted(target),
        "final_output": final_output,
        "skip_a_output": skip_a_output,
        "wrong_intermediate": wrong,
        "wrong_intermediate_output": wrong_intermediate_output,
        "program": program({"receiver_action": "absorb_color"}),
    }
