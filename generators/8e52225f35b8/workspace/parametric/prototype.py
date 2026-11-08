"""Native parametric closure-order family for ARC task 8e52225f35b8.

The default setting is byte-for-byte the accepted canonical rule.  The nearby
setting changes only the order of the two genuinely stateful closure passes:
row→column versus column→row.  Generated lessons share the same inputs across
settings, identify the selected order from two demonstrations, and retain the
canonical final operation (cells covered by at least two panel closures).
"""
from __future__ import annotations

import copy
import hashlib
import json
import random
from pathlib import Path
from typing import Callable, Iterable, Sequence

TASK_ID = "8e52225f35b8"
ORDERS = ("row_then_column", "column_then_row")
SETTINGS = tuple({"closure_order": order} for order in ORDERS)
RIVAL_NAMES = (
    "wrong_order",
    "first_axis_only",
    "second_axis_only",
    "bbox_per_panel",
    "all_panel_intersection",
    "global_close",
    "raw_mark_majority",
    "first_demo_mask",
)

_CANONICAL_PATH = Path(__file__).with_name("canonical.rkt")
_CANONICAL = _CANONICAL_PATH.read_text(encoding="utf-8")
_CANONICAL_FORM = "(define (double-close cells) (col-close (row-close cells)))"
_ALTERNATE_FORM = "(define (double-close cells) (row-close (col-close cells)))"
if _CANONICAL.count(_CANONICAL_FORM) != 1:
    raise RuntimeError("canonical program does not contain the expected unique closure form")

Grid = list[list[int]]
Cell = tuple[int, int]
Settings = dict[str, str]


def digest(value: object) -> str:
    """Stable content digest used for uniqueness and public-evidence checks."""
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _exact_int(value: object, *, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}; bool is forbidden")
    return value


def _settings(value: object) -> Settings:
    if type(value) is not dict or set(value) != {"closure_order"}:
        raise ValueError("settings must name exactly closure_order")
    order = value["closure_order"]
    if type(order) is not str or order not in ORDERS:
        raise ValueError(f"closure_order must be one of {ORDERS!r}")
    return {"closure_order": order}


def _grid(value: object, *, name: str = "grid") -> Grid:
    if type(value) is not list or not 1 <= len(value) <= 30:
        raise ValueError(f"{name} must have 1..30 rows")
    if type(value[0]) is not list or not 1 <= len(value[0]) <= 30:
        raise ValueError(f"{name} must have 1..30 columns")
    width = len(value[0])
    result: Grid = []
    for row in value:
        if type(row) is not list or len(row) != width:
            raise ValueError(f"{name} must be rectangular")
        if any(type(cell) is not int or not 0 <= cell <= 9 for cell in row):
            raise ValueError(f"{name} cells must be exact integer ARC colors 0..9")
        result.append(list(row))
    return result


def _split_panels(value: object) -> tuple[Grid, list[tuple[int, int]], list[set[Cell]]]:
    grid = _grid(value)
    height, width = len(grid), len(grid[0])
    separator_columns = {
        column
        for column in range(width)
        if all(grid[row][column] == 9 for row in range(height))
    }
    if not separator_columns:
        raise ValueError("input needs full-height color-9 panel separators")

    bounds: list[tuple[int, int]] = []
    column = 0
    while column < width:
        if column in separator_columns:
            column += 1
            continue
        left = column
        while column < width and column not in separator_columns:
            column += 1
        bounds.append((left, column))

    if len(bounds) != 3:
        raise ValueError(f"parametric grammar requires exactly three panels, found {len(bounds)}")
    panel_widths = [right - left for left, right in bounds]
    if len(set(panel_widths)) != 1 or panel_widths[0] != 9:
        raise ValueError("parametric grammar requires three equal nine-column panels")

    cells_by_panel: list[set[Cell]] = []
    for panel_index, (left, right) in enumerate(bounds):
        cells: set[Cell] = set()
        for row in range(height):
            for global_column in range(left, right):
                color = grid[row][global_column]
                if color not in (0, 2):
                    raise ValueError(
                        f"panel {panel_index} may contain only background 0 and motif color 2"
                    )
                if color == 2:
                    cells.add((row, global_column - left))
        if not cells:
            raise ValueError(f"panel {panel_index} motif is empty")
        cells_by_panel.append(cells)

    # A 9 outside a full-height separator would have failed the panel-color check.
    return grid, bounds, cells_by_panel


def _row_close(cells: Iterable[Cell]) -> set[Cell]:
    cells = set(cells)
    rows: dict[int, list[int]] = {}
    for row, column in cells:
        rows.setdefault(row, []).append(column)
    return {
        (row, column)
        for row, columns in rows.items()
        for column in range(min(columns), max(columns) + 1)
    }


def _column_close(cells: Iterable[Cell]) -> set[Cell]:
    cells = set(cells)
    columns: dict[int, list[int]] = {}
    for row, column in cells:
        columns.setdefault(column, []).append(row)
    return {
        (row, column)
        for column, rows in columns.items()
        for row in range(min(rows), max(rows) + 1)
    }


def _first_close(cells: Iterable[Cell], order: str) -> set[Cell]:
    return _row_close(cells) if order == "row_then_column" else _column_close(cells)


def _second_close(cells: Iterable[Cell], order: str) -> set[Cell]:
    return _column_close(cells) if order == "row_then_column" else _row_close(cells)


def _double_close(cells: Iterable[Cell], order: str) -> set[Cell]:
    return _second_close(_first_close(cells, order), order)


def _counts(sets: Sequence[set[Cell]]) -> dict[Cell, int]:
    counts: dict[Cell, int] = {}
    for cells in sets:
        for cell in cells:
            counts[cell] = counts.get(cell, 0) + 1
    return counts


def _mask(height: int, width: int, cells: Iterable[Cell], color: int = 8) -> Grid:
    selected = set(cells)
    return [
        [color if (row, column) in selected else 0 for column in range(width)]
        for row in range(height)
    ]


def _majority_from_cells(
    cells_by_panel: Sequence[set[Cell]], height: int, width: int, order: str
) -> Grid:
    closures = [_double_close(cells, order) for cells in cells_by_panel]
    counts = _counts(closures)
    return _mask(height, width, (cell for cell, count in counts.items() if count >= 2))


def program(settings: object) -> str:
    """Return exact Racket source for one declared setting."""
    order = _settings(settings)["closure_order"]
    if order == "row_then_column":
        return _CANONICAL
    alternate = _CANONICAL.replace(_CANONICAL_FORM, _ALTERNATE_FORM)
    if alternate == _CANONICAL or alternate.count(_ALTERNATE_FORM) != 1:
        raise RuntimeError("failed to construct the single-form closure-order variant")
    return alternate


def intermediate(value: object, settings: object) -> list[Grid]:
    """Return the private, input-dependent first-pass state for every panel."""
    grid, bounds, cells_by_panel = _split_panels(value)
    order = _settings(settings)["closure_order"]
    height, panel_width = len(grid), bounds[0][1] - bounds[0][0]
    return [
        _mask(height, panel_width, _first_close(cells, order), color=2)
        for cells in cells_by_panel
    ]


def transform(value: object, settings: object) -> Grid:
    """Apply the selected two-pass closure and panel-majority rule in Python."""
    grid, bounds, cells_by_panel = _split_panels(value)
    order = _settings(settings)["closure_order"]
    return _majority_from_cells(
        cells_by_panel,
        len(grid),
        bounds[0][1] - bounds[0][0],
        order,
    )


def _base_motifs(height: int) -> list[set[Cell]]:
    # A exposes cells created only by row→column; B exposes cells created only
    # by column→row. D is a common rectangle whose closure reaches the bottom.
    a = {(0, 0), (0, 2), (3, 1)}
    b = {(4, 3), (6, 3), (5, 6)}
    d = {(7, 7), (7, 8), (height - 1, 7), (height - 1, 8)}
    # A two-mark shelf in panel 2 is output-neutral (the same row is already
    # covered by panels 0 and 1), but makes the scene use every local column.
    # It is deliberately incomplete, so it cannot create A's vertical stem.
    shelf = {(0, 0), (0, 2)}
    return [a | d, a | b | d, b | d | shelf]


def _safe_decoys(height: int) -> list[Cell]:
    panels = _base_motifs(height)
    baseline = {
        order: _majority_from_cells(panels, height, 9, order)
        for order in ORDERS
    }
    candidates: list[Cell] = []
    for cell in ((row, column) for row in range(height) for column in range(9)):
        if cell in panels[0]:
            continue
        trial = [set(panel) for panel in panels]
        trial[0].add(cell)
        if all(
            _majority_from_cells(trial, height, 9, order) == baseline[order]
            for order in ORDERS
        ):
            reachable = set().union(
                _double_close(trial[0], "row_then_column"),
                _double_close(trial[0], "column_then_row"),
            )
            # Panels 1 and 2 already reach all nine local columns. Require the
            # decoy to make panel 0 reach at least seven, so every stress seed
            # uses at least 25 of the 27 non-separator columns.
            if len({column for _row, column in reachable}) >= 7:
                candidates.append(cell)
    if not candidates:
        raise RuntimeError(f"no output-neutral decoy exists for height {height}")
    return candidates


def _orient(cells: Iterable[Cell], height: int, *, flip_lr: bool, flip_ud: bool) -> set[Cell]:
    return {
        (
            height - 1 - row if flip_ud else row,
            8 - column if flip_lr else column,
        )
        for row, column in cells
    }


def _scene(seed: int, index: int, *, height: int, separators: tuple[int, int]) -> Grid:
    if height < 9 or height > 30 or any(type(width) is not int or width < 1 for width in separators):
        raise ValueError("invalid scene geometry")
    total_width = 27 + sum(separators)
    if total_width > 30:
        raise ValueError("scene exceeds the 30-column ARC limit")

    panels = _base_motifs(height)
    candidates = _safe_decoys(height)
    chooser_seed = int.from_bytes(
        hashlib.sha256(f"{seed}:{index}:{height}:decoy".encode()).digest()[:8], "big"
    )
    decoy = candidates[random.Random(chooser_seed).randrange(len(candidates))]
    panels[0] = set(panels[0]) | {decoy}

    # The first two demonstrations deliberately have equal dimensions and
    # opposite horizontal orientation, defeating a memorized first output.
    flip_lr = bool((seed + index) & 1)
    flip_ud = bool(((seed >> (index % 16)) ^ (index * 3)) & 1)
    panels = [
        _orient(panel, height, flip_lr=flip_lr, flip_ud=flip_ud)
        for panel in panels
    ]

    grid = [[0 for _ in range(total_width)] for _ in range(height)]
    left = 0
    for panel_index, cells in enumerate(panels):
        for row, column in cells:
            grid[row][left + column] = 2
        left += 9
        if panel_index < 2:
            for separator_column in range(left, left + separators[panel_index]):
                for row in range(height):
                    grid[row][separator_column] = 9
            left += separators[panel_index]
    return grid


_TRAIN_HEIGHTS = (9, 9, 12, 15, 18, 21)
_QUERY_HEIGHTS = (10, 14, 22, 30)


def _all_scenes(seed: int) -> tuple[list[Grid], list[Grid]]:
    train = [
        _scene(seed, index, height=height, separators=(1, 1))
        for index, height in enumerate(_TRAIN_HEIGHTS)
    ]
    query = [
        _scene(
            seed,
            100 + index,
            height=height,
            separators=(1, 2) if index == len(_QUERY_HEIGHTS) - 1 else (1, 1),
        )
        for index, height in enumerate(_QUERY_HEIGHTS)
    ]
    return train, query


def _bbox(cells: set[Cell]) -> set[Cell]:
    rows = [row for row, _ in cells]
    columns = [column for _, column in cells]
    return {
        (row, column)
        for row in range(min(rows), max(rows) + 1)
        for column in range(min(columns), max(columns) + 1)
    }


def _threshold_mask(
    sets: Sequence[set[Cell]], height: int, width: int, threshold: int
) -> Grid:
    counts = _counts(sets)
    return _mask(height, width, (cell for cell, count in counts.items() if count >= threshold))


def _rival_output(
    name: str,
    value: object,
    settings: object,
    *,
    first_demo_output: Grid,
) -> Grid:
    grid, bounds, cells_by_panel = _split_panels(value)
    order = _settings(settings)["closure_order"]
    height, width = len(grid), bounds[0][1] - bounds[0][0]
    if name == "wrong_order":
        other = ORDERS[1] if order == ORDERS[0] else ORDERS[0]
        return _majority_from_cells(cells_by_panel, height, width, other)
    if name == "first_axis_only":
        return _threshold_mask(
            [_first_close(cells, order) for cells in cells_by_panel], height, width, 2
        )
    if name == "second_axis_only":
        second = _column_close if order == "row_then_column" else _row_close
        return _threshold_mask([second(cells) for cells in cells_by_panel], height, width, 2)
    if name == "bbox_per_panel":
        return _threshold_mask([_bbox(cells) for cells in cells_by_panel], height, width, 2)
    if name == "all_panel_intersection":
        closures = [_double_close(cells, order) for cells in cells_by_panel]
        return _threshold_mask(closures, height, width, len(cells_by_panel))
    if name == "global_close":
        combined: set[Cell] = set().union(*cells_by_panel)
        return _mask(height, width, _double_close(combined, order))
    if name == "raw_mark_majority":
        return _threshold_mask(cells_by_panel, height, width, 2)
    if name == "first_demo_mask":
        return copy.deepcopy(first_demo_output)
    raise ValueError(f"unknown rival {name!r}")


def _pair(value: Grid, settings: Settings) -> dict[str, Grid]:
    return {"input": copy.deepcopy(value), "output": transform(value, settings)}


def generate(seed: object, settings: object, demos: object = 2, queries: object = 4) -> dict:
    """Generate a deterministic lesson with private labels and a certificate."""
    seed = _exact_int(seed, name="seed", low=0, high=2**63 - 1)
    selected = _settings(settings)
    demos = _exact_int(demos, name="demos", low=2, high=6)
    queries = _exact_int(queries, name="queries", low=4, high=4)
    train_bank, query_bank = _all_scenes(seed)
    episode = {
        "schema": "arcpuzzles-parametric-episode-v1",
        "task_id": TASK_ID,
        "seed": seed,
        "settings": selected,
        "train": [_pair(grid, selected) for grid in train_bank[:demos]],
        "test": [_pair(grid, selected) for grid in query_bank[:queries]],
        "program_solution": program(selected),
    }
    episode["certificate"] = certify(episode)
    return episode


def certify(
    episode: object,
    execute: Callable[[str, Grid], Grid] | None = None,
) -> dict:
    """Fail closed, then prove demo-only finite identification and rival refutation."""
    if type(episode) is not dict:
        raise ValueError("episode must be an object")
    selected = _settings(episode.get("settings"))
    expected_program = program(selected)
    if episode.get("program_solution") != expected_program:
        raise ValueError("episode program does not match its declared setting")

    train = episode.get("train")
    test = episode.get("test")
    if type(train) is not list or not 2 <= len(train) <= 6:
        raise ValueError("episode needs 2..6 demonstrations")
    if type(test) is not list or len(test) != 4:
        raise ValueError("episode needs exactly four queries")

    normalized: list[tuple[Grid, Grid]] = []
    for split_name, pairs in (("train", train), ("test", test)):
        for index, pair in enumerate(pairs):
            if type(pair) is not dict or not {"input", "output"} <= set(pair):
                raise ValueError(f"{split_name}[{index}] must contain input and output grids")
            normalized.append(
                (
                    _grid(pair["input"], name=f"{split_name}[{index}].input"),
                    _grid(pair["output"], name=f"{split_name}[{index}].output"),
                )
            )

    input_digests = [digest(input_grid) for input_grid, _ in normalized]
    if len(input_digests) != len(set(input_digests)):
        raise ValueError("all demonstration and query inputs must be distinct")

    # Label integrity is checked for every private pair, but setting survival is
    # computed only from demonstrations below.
    for input_grid, output_grid in normalized:
        if transform(input_grid, selected) != output_grid:
            raise ValueError("episode label does not match the declared setting")

    train_pairs = normalized[: len(train)]
    survivors: list[Settings] = []
    for candidate in SETTINGS:
        source = program(candidate)
        predictions = [
            _grid(execute(source, input_grid), name="executed output")
            if execute is not None
            else transform(input_grid, candidate)
            for input_grid, _ in train_pairs
        ]
        if all(prediction == label for prediction, (_, label) in zip(predictions, train_pairs)):
            survivors.append(copy.deepcopy(candidate))
    if survivors != [selected]:
        raise ValueError(f"demonstrations do not uniquely identify the setting: {survivors!r}")

    first_demo_output = train_pairs[0][1]
    refuted: list[str] = []
    for rival in RIVAL_NAMES:
        predictions = [
            _rival_output(
                rival,
                input_grid,
                selected,
                first_demo_output=first_demo_output,
            )
            for input_grid, _ in train_pairs
        ]
        if not any(prediction != label for prediction, (_, label) in zip(predictions, train_pairs)):
            raise ValueError(f"demonstrations fail to refute rival {rival}")
        refuted.append(rival)

    if execute is not None:
        # Also replay all selected-setting private labels under protected Racket.
        for input_grid, output_grid in normalized:
            observed = _grid(execute(expected_program, input_grid), name="executed output")
            if observed != output_grid:
                raise ValueError("protected Racket label replay failed")

    return {
        "schema": "arcpuzzles-parametric-certificate-v1",
        "survivors": survivors,
        "demo_count": len(train),
        "query_count": len(test),
        "extra_refutations": refuted,
        "racket_checked": execute is not None,
        "input_digest": digest(input_digests),
    }


def public_turn(episode: object, query_index: object) -> dict:
    """Project an episode to the first/public challenge surface for one query."""
    if type(episode) is not dict:
        raise ValueError("episode must be an object")
    query_index = _exact_int(query_index, name="query_index", low=0, high=3)
    train = episode.get("train")
    test = episode.get("test")
    if type(train) is not list or type(test) is not list or query_index >= len(test):
        raise ValueError("episode does not contain the requested query")
    public_train = []
    for index, pair in enumerate(train):
        if type(pair) is not dict or not {"input", "output"} <= set(pair):
            raise ValueError(f"train[{index}] is malformed")
        public_train.append(
            {
                "input": _grid(pair["input"], name=f"train[{index}].input"),
                "output": _grid(pair["output"], name=f"train[{index}].output"),
            }
        )
    query = test[query_index]
    if type(query) is not dict or "input" not in query:
        raise ValueError(f"test[{query_index}] is malformed")
    return {
        "train": public_train,
        "test": [{"input": _grid(query["input"], name=f"test[{query_index}].input")}],
    }


def execute_rule(source: object, value: object, bridge=None) -> Grid:
    """Execute exact rule text through the checkout's protected Racket bridge."""
    if type(source) is not str or not source.strip():
        raise ValueError("source must be nonempty Racket text")
    grid = _grid(value)
    from puzzle_generators.rule_wrap import wrap_rule
    from arc_repl.racket_bridge import RacketBridge

    literal = "'(" + " ".join(
        "(" + " ".join(str(cell) for cell in row) + ")" for row in grid
    ) + ")"
    expression = f"({wrap_rule(source)} {literal})"
    if bridge is not None:
        return _grid(bridge.eval_text(expression), name="Racket output")
    with RacketBridge(timeout=60) as owned_bridge:
        return _grid(owned_bridge.eval_text(expression), name="Racket output")


def analyze_scene(value: object) -> dict[str, int]:
    """Return structural metrics used by tests, probes, and evidence manifests."""
    grid, bounds, cells_by_panel = _split_panels(value)
    height = len(grid)
    closures_by_order = {
        order: [_double_close(cells, order) for cells in cells_by_panel]
        for order in ORDERS
    }
    outputs = {
        order: {
            cell
            for cell, count in _counts(closures).items()
            if count >= 2
        }
        for order, closures in closures_by_order.items()
    }
    occupied_global: set[Cell] = set()
    for (left, _right), panel_cells in zip(bounds, cells_by_panel):
        # Use both orders so the metric measures all causally reachable content.
        local = set().union(
            _double_close(panel_cells, "row_then_column"),
            _double_close(panel_cells, "column_then_row"),
        )
        occupied_global.update((row, left + column) for row, column in local)

    return {
        "height": height,
        "width": len(grid[0]),
        "panel_count": len(bounds),
        "mark_count": sum(len(cells) for cells in cells_by_panel),
        "occupied_rows": len({row for row, _ in occupied_global}),
        "occupied_columns": len({column for _, column in occupied_global}),
        "order_disagreement_cells": len(
            outputs["row_then_column"] ^ outputs["column_then_row"]
        ),
        "row_then_column_exactly_two": sum(
            count == 2 for count in _counts(closures_by_order["row_then_column"]).values()
        ),
        "column_then_row_exactly_two": sum(
            count == 2 for count in _counts(closures_by_order["column_then_row"]).values()
        ),
    }
