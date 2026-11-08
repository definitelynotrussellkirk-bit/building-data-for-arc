"""Source-bound parametric prototype for dc0a7662670b.

The canonical setting is the exact selected Racket rule.  The alternate setting
preserves its perimeter ordering and adds a causal relay:

A. rank all same-color components by true exposed-edge perimeter, then color;
intermediate. measure the crop width of the first ranked component;
B. recolor the component at that 1-based rank to color 8 while packing.

Input sampling is independent of the setting.  The first two demonstrations use
selector widths 2 and 3, which distinguish both declared settings and every
bounded rival below.  The fourth query is a dense, boundary-spanning 30x30 case.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Iterable

TASK_ID = "dc0a7662670b"
HERE = Path(__file__).resolve().parent
MODES = ("canonical", "winner_width_relay")
DEFAULT_MODE = "canonical"
PROGRAM_PATHS = {
    "canonical": HERE / "canonical.rkt",
    "winner_width_relay": HERE / "winner_width_relay.rkt",
}
COUNTERFACTUAL_PATH = HERE / "winner_height_counterfactual.rkt"

Grid = list[list[int]]
Cells = tuple[tuple[int, int], ...]
PALETTE = (1, 2, 3, 4, 5, 6, 7, 9)

# All regular scenes contain five distinct-color components.  The winner always
# has perimeter 12 but width 1, 2 or 3.  The six-cell rectangle below has lower
# perimeter (10) yet larger area, so it also refutes area-as-rank shortcuts.
WINNERS: dict[int, Cells] = {
    1: tuple((row, 0) for row in range(5)),
    2: ((0, 0), (0, 1), (1, 0), (2, 0), (2, 1)),
    3: ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2)),
}
REGULAR_SHAPES: dict[str, Cells] = {
    "second": tuple((row, col) for row in range(2) for col in range(3)),
    "tie_low": ((0, 0), (0, 1), (1, 0), (1, 1)),
    "tie_high": ((0, 0), (1, 0), (1, 1)),
    "tail": ((0, 0), (0, 1)),
}

# A 30x30 stress scene with 64 nonzero cells and seven ranked components.
# The width-2 winner is a nine-cell tree polyomino with perimeter 20 and height 7.
STRESS_SHAPES: dict[str, Cells] = {
    "winner": (
        (0, 0), (1, 0), (2, 0), (2, 1), (3, 1),
        (4, 1), (5, 1), (5, 0), (6, 0),
    ),
    "second": tuple((row, col) for row in range(4) for col in range(4)),
    "third": tuple((row, col) for row in range(3) for col in range(4)),
    "tie_low": tuple((row, col) for row in range(3) for col in range(3)),
    "tie_high": tuple((row, col) for row in range(2) for col in range(4)),
    "sixth": tuple((row, col) for row in range(2) for col in range(3)),
    "seventh": tuple((row, col) for row in range(2) for col in range(2)),
}

DEMO_SPECS = (
    (2, 10, 11),
    (3, 11, 13),
    (1, 12, 14),
    (2, 13, 15),
    (3, 14, 16),
    (1, 10, 16),
)
QUERY_SPECS = (
    (1, 11, 12, "regular"),
    (2, 14, 16, "regular"),
    (3, 20, 22, "regular"),
    (2, 30, 30, "stress"),
)


def _literal_int(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be a literal integer in {low}..{high}")
    return value


def validate_settings(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"mode"}:
        raise ValueError("settings must contain exactly the mode key")
    mode = settings["mode"]
    if type(mode) is not str or mode not in MODES:
        raise ValueError(f"mode must be one of {list(MODES)}")
    return mode


def program_for(settings: Any) -> str:
    return PROGRAM_PATHS[validate_settings(settings)].read_text(encoding="utf-8")


def counterfactual_program() -> str:
    return COUNTERFACTUAL_PATH.read_text(encoding="utf-8")


def _rng(seed: int, *parts: object) -> random.Random:
    payload = json.dumps([seed, *parts], sort_keys=True, separators=(",", ":"))
    value = int.from_bytes(hashlib.sha256(payload.encode("utf-8")).digest()[:16], "big")
    return random.Random(value)


def _normalize(cells: Iterable[tuple[int, int]]) -> Cells:
    cells = tuple(cells)
    row0 = min(row for row, _ in cells)
    col0 = min(col for _, col in cells)
    return tuple(sorted((row - row0, col - col0) for row, col in cells))


def _transform(cells: Cells, code: int) -> Cells:
    transformed = _normalize(cells)
    if code >= 4:
        transformed = _normalize((row, -col) for row, col in transformed)
    for _ in range(code % 4):
        transformed = _normalize((col, -row) for row, col in transformed)
    return transformed


def _dimension(cells: Cells) -> tuple[int, int]:
    return max(row for row, _ in cells) + 1, max(col for _, col in cells) + 1


def _perimeter(cells: Iterable[tuple[int, int]]) -> int:
    occupied = set(cells)
    return sum(
        (row + drow, col + dcol) not in occupied
        for row, col in occupied
        for drow, dcol in ((1, 0), (-1, 0), (0, 1), (0, -1))
    )


def _grid(value: Any) -> Grid:
    if type(value) is not list or not 1 <= len(value) <= 30:
        raise ValueError("grid must have 1..30 rows")
    if type(value[0]) is not list or not 1 <= len(value[0]) <= 30:
        raise ValueError("grid must have 1..30 columns")
    width = len(value[0])
    out: Grid = []
    for row in value:
        if type(row) is not list or len(row) != width:
            raise ValueError("grid must be rectangular")
        if any(type(cell) is not int or not 0 <= cell <= 9 for cell in row):
            raise ValueError("grid cells must be literal integer ARC colors 0..9")
        out.append(list(row))
    return out


def _components(grid: Grid) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    records: list[dict[str, Any]] = []
    for start_row in range(height):
        for start_col in range(width):
            color = grid[start_row][start_col]
            if color == 0 or (start_row, start_col) in seen:
                continue
            stack = [(start_row, start_col)]
            seen.add((start_row, start_col))
            cells: list[tuple[int, int]] = []
            while stack:
                row, col = stack.pop()
                cells.append((row, col))
                for drow, dcol in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = row + drow, col + dcol
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == color
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            rows = [row for row, _ in cells]
            cols = [col for _, col in cells]
            r0, r1, c0, c1 = min(rows), max(rows), min(cols), max(cols)
            occupied = set(cells)
            crop = [
                [grid[row][col] if (row, col) in occupied else 0 for col in range(c0, c1 + 1)]
                for row in range(r0, r1 + 1)
            ]
            records.append(
                {
                    "color": color,
                    "cells": tuple(sorted(cells)),
                    "size": len(cells),
                    "perimeter": _perimeter(cells),
                    "bbox": (r0, c0, r1, c1),
                    "bbox_perimeter": 2 * ((r1 - r0 + 1) + (c1 - c0 + 1)),
                    "crop": crop,
                    "height": len(crop),
                    "width": len(crop[0]),
                }
            )
    return records


def _pack(ranked: list[dict[str, Any]], selector: int | None = None) -> Grid:
    if not ranked:
        raise ValueError("at least one nonzero component is required")
    out_height = sum(item["height"] for item in ranked) + len(ranked) - 1
    out_width = max(item["width"] for item in ranked)
    if out_height > 30 or out_width > 30:
        raise ValueError("packed output exceeds ARC's 30x30 limit")
    out = [[0] * out_width for _ in range(out_height)]
    top = 0
    for rank, item in enumerate(ranked, 1):
        for row_index, row in enumerate(item["crop"]):
            for col_index, value in enumerate(row):
                if value != 0:
                    out[top + row_index][col_index] = 8 if rank == selector else value
        top += item["height"] + 1
    return out


def analyze(value: Any) -> dict[str, Any]:
    grid = _grid(value)
    records = _components(grid)
    if len(records) < 3:
        raise ValueError("parametric grammar needs at least three components")
    if len({item["color"] for item in records}) != len(records):
        raise ValueError("parametric grammar uses one distinct color per component")
    if any(item["color"] == 8 for item in records):
        raise ValueError("input color 8 is reserved for the relay output")
    ranked = sorted(records, key=lambda item: (-item["perimeter"], item["color"]))
    spatial = sorted(records, key=lambda item: (item["bbox"][0], item["bbox"][1]))
    return {
        "grid": grid,
        "ranked": ranked,
        "spatial": spatial,
        "winner_width": ranked[0]["width"],
        "winner_height": ranked[0]["height"],
        "canonical": _pack(ranked),
    }


def _with_selector(value: Any, selector: int | None) -> Grid:
    facts = analyze(value)
    return _pack(facts["ranked"], selector)


def transform(value: Any, settings: Any) -> Grid:
    mode = validate_settings(settings)
    facts = analyze(value)
    if mode == "canonical":
        return deepcopy(facts["canonical"])
    selector = facts["winner_width"]
    if not 1 <= selector <= len(facts["ranked"]):
        raise ValueError("winner width is not a valid ranked selector")
    return _pack(facts["ranked"], selector)


def transform_height_counterfactual(value: Any) -> Grid:
    facts = analyze(value)
    return _pack(facts["ranked"], facts["winner_height"])


def highlighted_rank(output: Any, facts: dict[str, Any]) -> int | None:
    grid = _grid(output)
    top = 0
    highlighted: list[int] = []
    for rank, item in enumerate(facts["ranked"], 1):
        values = [
            grid[top + row][col]
            for row, crop_row in enumerate(item["crop"])
            for col, original in enumerate(crop_row)
            if original != 0
        ]
        if values and all(value == 8 for value in values):
            highlighted.append(rank)
        top += item["height"] + 1
    if len(highlighted) > 1:
        raise ValueError("more than one crop is highlighted")
    return highlighted[0] if highlighted else None


def _assign_regular_colors(rng: random.Random) -> dict[str, int]:
    chosen = sorted(rng.sample(list(PALETTE), 5))
    return {
        "second": chosen[0],
        "tie_low": chosen[1],
        "tail": chosen[2],
        "tie_high": chosen[3],
        "winner": chosen[4],
    }


def _regular_scene(seed: int, token: str, selector: int, height: int, width: int) -> Grid:
    if selector not in WINNERS:
        raise ValueError("regular selector must be 1, 2 or 3")
    rng = _rng(seed, "regular", token, selector, height, width)
    colors = _assign_regular_colors(rng)

    # Winner transforms preserve its width; other components use the full
    # dihedral group.  The second component deliberately remains a 2x3 rectangle.
    winner = WINNERS[selector]
    if rng.randrange(2):
        winner = _normalize((-row, col) for row, col in winner)
    if rng.randrange(2):
        winner = _normalize((row, -col) for row, col in winner)
    items = {
        "winner": {"cells": winner, "color": colors["winner"]},
        "second": {"cells": REGULAR_SHAPES["second"], "color": colors["second"]},
        "tie_low": {
            "cells": _transform(REGULAR_SHAPES["tie_low"], rng.randrange(8)),
            "color": colors["tie_low"],
        },
        "tie_high": {
            "cells": _transform(REGULAR_SHAPES["tie_high"], rng.randrange(8)),
            "color": colors["tie_high"],
        },
        "tail": {
            "cells": _transform(REGULAR_SHAPES["tail"], rng.randrange(8)),
            "color": colors["tail"],
        },
    }

    slots = ["tl", "tr", "center", "bl", "br"]
    winner_slot = {1: "center", 2: "br", 3: "bl"}[selector]
    assignment = {"second": "tl", "winner": winner_slot}
    free_slots = [slot for slot in slots if slot not in assignment.values()]
    free_roles = ["tie_low", "tie_high", "tail"]
    rng.shuffle(free_roles)
    assignment.update(dict(zip(free_roles, free_slots)))

    grid = [[0] * width for _ in range(height)]
    occupied: set[tuple[int, int]] = set()
    for role, slot in assignment.items():
        cells = items[role]["cells"]
        shape_h, shape_w = _dimension(cells)
        coordinates = {
            "tl": (0, 0),
            "tr": (0, width - shape_w),
            "center": ((height - shape_h) // 2, (width - shape_w) // 2),
            "bl": (height - shape_h, 0),
            "br": (height - shape_h, width - shape_w),
        }
        top, left = coordinates[slot]
        translated = {(top + row, left + col) for row, col in cells}
        if translated & occupied:
            raise AssertionError("regular placement collision")
        if any(
            (row + drow, col + dcol) in occupied
            for row, col in translated
            for drow, dcol in ((1, 0), (-1, 0), (0, 1), (0, -1))
        ):
            raise AssertionError("regular placement merges components")
        for row, col in translated:
            grid[row][col] = items[role]["color"]
        occupied.update(translated)

    facts = analyze(grid)
    if facts["winner_width"] != selector or len(facts["ranked"]) != 5:
        raise AssertionError("regular scene does not realize its selector")
    return grid


def _stress_scene(seed: int, token: str) -> Grid:
    rng = _rng(seed, "stress", token)
    chosen = sorted(rng.sample(list(PALETTE), 7))
    colors = {
        "second": chosen[0],
        "tie_low": chosen[1],
        "sixth": chosen[2],
        "seventh": chosen[3],
        "tie_high": chosen[4],
        "third": chosen[5],
        "winner": chosen[6],
    }
    shapes = dict(STRESS_SHAPES)
    winner = shapes["winner"]
    if rng.randrange(2):
        winner = _normalize((row, -col) for row, col in winner)
    shapes["winner"] = winner
    placements = {
        "winner": (0, 0),
        "second": (0, 26),
        "third": (10, 13),
        "tie_low": (27, 0),
        "tie_high": (28, 26),
        "sixth": (14, 0),
        "seventh": (14, 28),
    }
    grid = [[0] * 30 for _ in range(30)]
    occupied: set[tuple[int, int]] = set()
    for role, (top, left) in placements.items():
        translated = {(top + row, left + col) for row, col in shapes[role]}
        if translated & occupied:
            raise AssertionError("stress placement collision")
        if any(
            (row + drow, col + dcol) in occupied
            for row, col in translated
            for drow, dcol in ((1, 0), (-1, 0), (0, 1), (0, -1))
        ):
            raise AssertionError("stress placement merges components")
        for row, col in translated:
            grid[row][col] = colors[role]
        occupied.update(translated)
    facts = analyze(grid)
    if facts["winner_width"] != 2 or facts["winner_height"] != 7:
        raise AssertionError("stress scene lost its causal selector")
    if len(facts["ranked"]) != 7:
        raise AssertionError("stress scene must have seven components")
    return grid


def _input(seed: int, split: str, index: int) -> Grid:
    if split == "train":
        selector, height, width = DEMO_SPECS[index]
        return _regular_scene(seed, f"train:{index}", selector, height, width)
    selector, height, width, profile = QUERY_SPECS[index]
    if profile == "stress":
        return _stress_scene(seed, f"test:{index}")
    return _regular_scene(seed, f"test:{index}", selector, height, width)


def generate_episode(seed: Any, settings: Any, demos: Any = 3, queries: Any = 4) -> dict[str, Any]:
    seed = _literal_int(seed, 0, 2**63 - 1, "seed")
    demos = _literal_int(demos, 2, 6, "demos")
    queries = _literal_int(queries, 1, 4, "queries")
    mode = validate_settings(settings)
    normalized = {"mode": mode}
    train = [
        {"input": (grid := _input(seed, "train", index)), "output": transform(grid, normalized)}
        for index in range(demos)
    ]
    test = [
        {"input": (grid := _input(seed, "test", index)), "output": transform(grid, normalized)}
        for index in range(queries)
    ]
    serialized = [json.dumps(pair["input"], separators=(",", ":")) for pair in train + test]
    if len(serialized) != len(set(serialized)):
        raise AssertionError("episode inputs must be distinct")
    return {"train": train, "test": test, "program_solution": program_for(normalized)}


def public_turn(episode: Any, query_index: Any) -> dict[str, Any]:
    if type(episode) is not dict:
        raise ValueError("episode must be an object")
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or not train or type(test) is not list or not test:
        raise ValueError("episode must contain nonempty train and test lists")
    query_index = _literal_int(query_index, 0, len(test) - 1, "query_index")
    return {
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in train
        ],
        "test": [{"input": deepcopy(test[query_index]["input"])}],
    }


def public_bytes(episode: Any, query_index: Any) -> bytes:
    challenge = public_turn(episode, query_index)
    return (
        json.dumps(challenge, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode("utf-8")


def public_id(episode: Any, query_index: Any) -> str:
    return hashlib.sha256(public_bytes(episode, query_index)).hexdigest()


def _selector_output(grid: Grid, selector: int | None) -> Grid:
    return _pack(analyze(grid)["ranked"], selector)


def rival_outputs(grid: Grid) -> dict[str, Grid]:
    facts = analyze(grid)
    spatial_selector = facts["spatial"][0]["width"]
    area_winner = sorted(
        facts["ranked"], key=lambda item: (-item["size"], item["color"])
    )[0]
    bbox_winner = sorted(
        facts["ranked"], key=lambda item: (-item["bbox_perimeter"], item["color"])
    )[0]
    return {
        "canonical": _pack(facts["ranked"]),
        "winner_width_relay": _pack(facts["ranked"], facts["winner_width"]),
        "winner_height_relay": _pack(facts["ranked"], facts["winner_height"]),
        "fixed_rank_1": _pack(facts["ranked"], 1),
        "fixed_rank_2": _pack(facts["ranked"], 2),
        "fixed_rank_3": _pack(facts["ranked"], 3),
        "spatial_first_width": _pack(facts["ranked"], spatial_selector),
        "largest_area_width": _pack(facts["ranked"], area_winner["width"]),
        "largest_bbox_perimeter_width": _pack(facts["ranked"], bbox_winner["width"]),
        "highlight_all": [
            [8 if value != 0 else 0 for value in row] for row in _pack(facts["ranked"])
        ],
    }


def finite_rival_audit(seed: int, demos: int = 2, queries: int = 4) -> dict[str, Any]:
    rows = []
    failures = []
    for mode in MODES:
        episode = generate_episode(seed, {"mode": mode}, demos, queries)
        all_names = sorted(rival_outputs(episode["train"][0]["input"]))
        for rival in all_names:
            if rival == mode:
                continue
            demo_mismatches = [
                index
                for index, pair in enumerate(episode["train"])
                if rival_outputs(pair["input"])[rival] != pair["output"]
            ]
            query_mismatches = [
                index
                for index, pair in enumerate(episode["test"])
                if rival_outputs(pair["input"])[rival] != pair["output"]
            ]
            survives = not demo_mismatches
            query_changing = bool(query_mismatches)
            rows.append(
                {
                    "mode": mode,
                    "rival": rival,
                    "demo_mismatch_indices": demo_mismatches,
                    "query_mismatch_indices": query_mismatches,
                    "survives_demonstrations": survives,
                    "changes_a_query": query_changing,
                }
            )
            if survives and query_changing:
                failures.append(f"{mode}: {rival} fits demos but changes a query")
    return {
        "schema": "dc0a7662670b-finite-rival-audit-v1",
        "seed": seed,
        "demos": demos,
        "queries": queries,
        "rows": rows,
        "failures": failures,
        "status": "pass" if not failures else "fail",
        "limits": "Finite named-rival audit; arbitrary programs are not exhausted.",
    }


def causal_witness(seed: int = 71) -> dict[str, Any]:
    grid = _input(_literal_int(seed, 0, 2**63 - 1, "seed"), "test", 3)
    facts = analyze(grid)
    actual = _pack(facts["ranked"], facts["winner_width"])
    counterfactual = _pack(facts["ranked"], facts["winner_height"])
    changed = sum(
        left != right
        for left_row, right_row in zip(actual, counterfactual)
        for left, right in zip(left_row, right_row)
    )
    return {
        "schema": "dc0a7662670b-causal-witness-v1",
        "task_id": TASK_ID,
        "settings": {"mode": "winner_width_relay"},
        "step_a": "rank_components_by_true_perimeter_then_color",
        "intermediate_name": "winner_crop_width",
        "actual_intermediate": facts["winner_width"],
        "counterfactual_intermediate": facts["winner_height"],
        "step_b": "recolor_the_width_ranked_crop_to_8",
        "why_b_depends_on_a": (
            "The highlighted rank is the width of the first component after the "
            "canonical perimeter/color ranking; neither the winner nor the selected "
            "rank is known before step A."
        ),
        "ablation": "wrong_intermediate_use_winner_height",
        "input": grid,
        "input_shape": [len(grid), len(grid[0])],
        "program": program_for({"mode": "winner_width_relay"}),
        "program_output": actual,
        "counterfactual_program": counterfactual_program(),
        "counterfactual_output": counterfactual,
        "changed_cells": changed,
        "replay_status": "python_constructed_pending_racket_replay",
    }
