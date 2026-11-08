"""Native parametric family for a1ece4864521.

The canonical setting preserves the selected Racket source byte-for-byte.  The
alternative keeps the same latent-lattice grammar but makes the inferred clean
value at each anomaly causally select its diagonal expansion route:

* inferred 0 -> paint the clean-zero mask in the 4x4 window above-left;
* inferred 8 -> paint the clean-zero mask in the 4x4 window below-right.

Inputs are independent of the private setting.  Demonstrations deliberately
cross inferred phase with binary/colored anomaly type so color and value-class
shortcuts cannot stand in for lattice reconstruction.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
from typing import Any, Callable

HERE = Path(__file__).resolve().parent
TASK_ID = "a1ece4864521"
SETTINGS = (
    {"fill_route": "below_right"},
    {"fill_route": "phase_diagonal"},
)

_GEN_PATH = HERE.parents[1] / "generator.py"
_GEN_SPEC = importlib.util.spec_from_file_location("_a1ece4864521_base_for_parametric", _GEN_PATH)
if _GEN_SPEC is None or _GEN_SPEC.loader is None:
    raise ImportError("cannot load adjacent base generator")
base = importlib.util.module_from_spec(_GEN_SPEC)
_GEN_SPEC.loader.exec_module(base)

# height, width, tile-zero count, anomaly count, geometry profile
_DEMO_PROFILES = (
    (15, 17, 10, 6, "overlap"),
    (18, 20, 13, 6, "boundary"),
    (20, 18, 16, 6, "spread"),
    (24, 25, 7, 7, "interior"),
    (27, 30, 18, 8, "boundary"),
    (30, 27, 12, 8, "spread"),
)
_QUERY_PROFILES = (
    (10, 10, 8, 4, "boundary"),
    (16, 23, 14, 6, "overlap"),
    (23, 16, 10, 7, "spread"),
    (30, 30, 15, 8, "boundary"),
)


def _integer(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _setting(settings: Any) -> str:
    if (
        type(settings) is not dict
        or set(settings) != {"fill_route"}
        or type(settings["fill_route"]) is not str
        or settings["fill_route"] not in {"below_right", "phase_diagonal"}
    ):
        raise ValueError(
            "settings must be exactly {'fill_route': 'below_right'|'phase_diagonal'}"
        )
    return settings["fill_route"]


def _grid(value: Any, name: str = "grid") -> list[list[int]]:
    if (
        type(value) is not list
        or not 5 <= len(value) <= 30
        or type(value[0]) is not list
        or not 5 <= len(value[0]) <= 30
    ):
        raise ValueError(f"{name} must have 5..30 rows and columns")
    width = len(value[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in value
    ):
        raise ValueError(f"{name} must be rectangular with exact ARC integers 0..9")
    return value


def program(settings: Any) -> str:
    route = _setting(settings)
    filename = "canonical.rkt" if route == "below_right" else "phase_diagonal.rkt"
    return (HERE / filename).read_text(encoding="utf-8")


def _rng(seed: int, split: str, index: int, attempt: int = 0) -> random.Random:
    raw = json.dumps(
        [TASK_ID, seed, split, index, attempt], separators=(",", ":")
    ).encode("utf-8")
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest(), "big"))


def _make_tile(rng: random.Random, zero_count: int) -> list[list[int]]:
    positions = list(range(25))
    rng.shuffle(positions)
    zeros = set(positions[:zero_count])
    return [[0 if row * 5 + col in zeros else 8 for col in range(5)] for row in range(5)]


def _window(
    clean: list[list[int]], row: int, col: int, direction: str, *, zero_only: bool = True
) -> list[tuple[int, int]]:
    height, width = len(clean), len(clean[0])
    if direction == "below_right":
        rows = range(row + 1, min(row + 5, height))
        cols = range(col + 1, min(col + 5, width))
    elif direction == "above_left":
        rows = range(max(0, row - 4), row)
        cols = range(max(0, col - 4), col)
    else:
        raise ValueError(f"unknown direction: {direction}")
    return [
        (rr, cc)
        for rr in rows
        for cc in cols
        if not zero_only or clean[rr][cc] == 0
    ]


def analyze_scene(grid: Any) -> dict[str, Any]:
    _grid(grid, "input")
    return base._analyze(grid)


def _direction(route: str, expected: int) -> str:
    if route == "below_right":
        return "below_right"
    return "above_left" if expected == 0 else "below_right"


def _transform_with(
    grid: Any,
    route: str,
    *,
    direction_override: Callable[[int, int, int, int, int], str] | None = None,
    mask: str = "clean_zero",
    anomaly_order: str = "forward",
    fill_mode: str = "source",
) -> list[list[int]]:
    facts = analyze_scene(grid)
    if facts.get("errors"):
        raise ValueError("invalid scene: " + "; ".join(facts["errors"]))
    clean = facts["clean"]
    output = [row[:] for row in clean]
    anomalies = list(facts["anomalies"])
    if anomaly_order == "reverse":
        anomalies.reverse()
    first_fill = None
    for index, (row, col, value, expected) in enumerate(anomalies):
        direction = (
            direction_override(index, row, col, value, expected)
            if direction_override is not None
            else _direction(route, expected)
        )
        cells = _window(clean, row, col, direction, zero_only=(mask != "all"))
        if mask == "raw_zero":
            cells = [(rr, cc) for rr, cc in _window(clean, row, col, direction, zero_only=False) if grid[rr][cc] == 0]
        fill = value if value not in (0, 8) else 8
        if first_fill is None:
            first_fill = fill
        if fill_mode == "first":
            fill = first_fill
        for rr, cc in cells:
            output[rr][cc] = fill
    return output


def transform(grid: Any, settings: Any) -> list[list[int]]:
    return _transform_with(grid, _setting(settings))


def _candidate_score(
    profile: str,
    cell: tuple[int, int],
    phase: int,
    selected: list[tuple[int, int]],
    height: int,
    width: int,
) -> tuple[int, int, int]:
    row, col = cell
    margin = min(row, col, height - 1 - row, width - 1 - col)
    if profile == "interior":
        primary = margin
    elif profile == "boundary":
        # Phase-zero sources need an above-left alternate target, so place them
        # near lower/right boundaries; phase-eight sources use below-right and
        # are driven toward upper/left boundaries.
        primary = row + col if phase == 0 else (height - 1 - row) + (width - 1 - col)
    elif profile == "spread":
        primary = min((abs(row - rr) + abs(col - cc) for rr, cc in selected), default=height + width)
    elif profile == "overlap":
        primary = -min((abs(row - rr) + abs(col - cc) for rr, cc in selected), default=0)
    else:
        raise ValueError(f"unknown profile: {profile}")
    return primary, -row, -col


def _build_scene(seed: int, split: str, index: int, profile: tuple, attempt: int) -> list[list[int]]:
    height, width, zero_count, anomaly_count, geometry = profile
    rng = _rng(seed, split, index, attempt)
    tile = _make_tile(rng, zero_count)
    clean = base._clean_grid(tile, height, width)
    candidates = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if _window(clean, row, col, "below_right")
        and (clean[row][col] == 8 or _window(clean, row, col, "above_left"))
    ]
    rng.shuffle(candidates)
    selected: list[tuple[int, int]] = []
    residues: set[tuple[int, int]] = set()
    enforce_first_phase = split == "train" and index < 2
    expected_first_phase = 0 if index % 2 == 0 else 8
    other_phase = 8 if expected_first_phase == 0 else 0
    phases = ([expected_first_phase, other_phase] * ((anomaly_count + 1) // 2))[:anomaly_count]
    for phase_index, phase in enumerate(phases):
        legal = [
            cell
            for cell in candidates
            if clean[cell[0]][cell[1]] == phase
            and (cell[0] % 5, cell[1] % 5) not in residues
            and (not enforce_first_phase or phase_index == 0 or cell > selected[0])
        ]
        if not legal:
            raise RuntimeError("no legal anomaly candidate for requested phase")
        legal.sort(
            key=lambda cell: _candidate_score(
                geometry, cell, phase, selected, height, width
            ),
            reverse=True,
        )
        chosen = legal[0]
        selected.append(chosen)
        residues.add((chosen[0] % 5, chosen[1] % 5))
    selected.sort()
    if enforce_first_phase and clean[selected[0][0]][selected[0][1]] != expected_first_phase:
        raise RuntimeError("row-major first anomaly does not cross the first-phase shortcut")

    # Each scene itself contains all four phase x anomaly-type combinations.
    kind_pattern = (
        ("binary", "colored", "colored", "binary", "binary", "colored", "colored", "binary")
        if index % 2 == 0
        else ("colored", "binary", "binary", "colored", "colored", "binary", "binary", "colored")
    )
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 9], 3)
    grid = [row[:] for row in clean]
    colored_index = 0
    for anomaly_index, (row, col) in enumerate(selected):
        kind = kind_pattern[anomaly_index]
        if kind == "binary":
            grid[row][col] = 8 if clean[row][col] == 0 else 0
        else:
            grid[row][col] = colors[colored_index % len(colors)]
            colored_index += 1

    facts = base._analyze(grid)
    if facts.get("errors") or facts.get("tile") != tile:
        raise RuntimeError("constructed scene did not preserve its latent tile")
    combos = {
        (expected, value in (0, 8))
        for _row, _col, value, expected in facts["anomalies"]
    }
    if combos != {(0, False), (0, True), (8, False), (8, True)}:
        raise RuntimeError("scene does not cross phase and anomaly type")
    if transform(grid, {"fill_route": "below_right"}) == transform(
        grid, {"fill_route": "phase_diagonal"}
    ):
        raise RuntimeError("scene does not distinguish the two settings")
    return grid


def _scene(seed: int, split: str, index: int, profile: tuple, *, attempt_base: int = 0) -> list[list[int]]:
    for offset in range(256):
        try:
            return _build_scene(seed, split, index, profile, attempt_base + offset)
        except RuntimeError:
            continue
    raise RuntimeError(f"could not construct {split}[{index}] after bounded retries")


def _demo_bank(seed: int) -> list[list[list[int]]]:
    # Search the two-example teaching prefix jointly.  This is constructive
    # lesson selection, not rejection based on the private setting: both settings
    # use exactly the same chosen inputs.
    for lesson_attempt in range(128):
        first = _scene(seed, "train", 0, _DEMO_PROFILES[0], attempt_base=lesson_attempt * 257)
        second = _scene(seed, "train", 1, _DEMO_PROFILES[1], attempt_base=lesson_attempt * 263)
        prefix = [first, second]
        if all(
            setting_survivors(
                [{"input": grid, "output": transform(grid, setting)} for grid in prefix]
            )
            == [setting]
            and rival_survivors(
                [{"input": grid, "output": transform(grid, setting)} for grid in prefix],
                setting,
            )
            == []
            for setting in SETTINGS
        ):
            rest = [
                _scene(seed, "train", index, profile)
                for index, profile in enumerate(_DEMO_PROFILES[2:], start=2)
            ]
            return prefix + rest
    raise RuntimeError("could not construct a two-demo distinguishing lesson")


def _query_bank(seed: int) -> list[list[list[int]]]:
    bank = [
        _scene(seed, "test", index, profile)
        for index, profile in enumerate(_QUERY_PROFILES)
    ]
    order = list(range(4))
    rng = _rng(seed, "query-order", 0)
    rng.shuffle(order)
    return [bank[index] for index in order]


def generate(seed: Any, settings: Any, demos: Any = 3, queries: Any = 4) -> dict[str, Any]:
    _integer(seed, 0, 2**63 - 1, "seed")
    _setting(settings)
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    demos_bank = _demo_bank(seed)
    query_bank = _query_bank(seed)
    result = {
        "task_id": TASK_ID,
        "seed": seed,
        "settings": copy.deepcopy(settings),
        "program_solution": program(settings),
        "train": [
            {"input": copy.deepcopy(grid), "output": transform(grid, settings)}
            for grid in demos_bank[:demos]
        ],
        "test": [
            {"input": copy.deepcopy(grid), "output": transform(grid, settings)}
            for grid in query_bank[:queries]
        ],
    }
    validate_episode(result, settings=settings, demos=demos, queries=queries)
    return result


def setting_survivors(train: Any) -> list[dict[str, str]]:
    if type(train) is not list:
        raise ValueError("train must be a list")
    survivors = []
    for setting in SETTINGS:
        if all(
            type(pair) is dict
            and _grid(pair.get("input"), "input")
            and _grid(pair.get("output"), "output")
            and transform(pair["input"], setting) == pair["output"]
            for pair in train
        ):
            survivors.append(copy.deepcopy(setting))
    return survivors


def _rival_fixed_above_left(grid: Any, route: str) -> list[list[int]]:
    return _transform_with(grid, route, direction_override=lambda *_: "above_left")


def _rival_binary_is_ul(grid: Any, route: str) -> list[list[int]]:
    return _transform_with(
        grid,
        route,
        direction_override=lambda _i, _r, _c, value, _expected: "above_left" if value in (0, 8) else "below_right",
    )


def _rival_colored_is_ul(grid: Any, route: str) -> list[list[int]]:
    return _transform_with(
        grid,
        route,
        direction_override=lambda _i, _r, _c, value, _expected: "below_right" if value in (0, 8) else "above_left",
    )


def _rival_coordinate_parity(grid: Any, route: str) -> list[list[int]]:
    return _transform_with(
        grid,
        route,
        direction_override=lambda _i, row, col, _value, _expected: "above_left" if (row + col) % 2 == 0 else "below_right",
    )


def _rival_first_phase(grid: Any, route: str) -> list[list[int]]:
    facts = analyze_scene(grid)
    first_expected = facts["anomalies"][0][3]
    direction = "above_left" if first_expected == 0 else "below_right"
    return _transform_with(grid, route, direction_override=lambda *_: direction)


def _rival_fixed_tile_phase(grid: Any, route: str) -> list[list[int]]:
    return _transform_with(
        grid,
        route,
        direction_override=lambda _i, row, col, _value, _expected: (
            "above_left" if base._TILE[row % 5][col % 5] == 0 else "below_right"
        ),
    )


def _rival_raw_zero(grid: Any, route: str) -> list[list[int]]:
    return _transform_with(grid, route, mask="raw_zero")


def _rival_all_cells(grid: Any, route: str) -> list[list[int]]:
    return _transform_with(grid, route, mask="all")


def _rival_reverse_order(grid: Any, route: str) -> list[list[int]]:
    return _transform_with(grid, route, anomaly_order="reverse")


def _rival_first_color(grid: Any, route: str) -> list[list[int]]:
    return _transform_with(grid, route, fill_mode="first")


RIVALS: dict[str, Callable[[Any, str], list[list[int]]]] = {
    "fixed_above_left": _rival_fixed_above_left,
    "binary_value_selects_route": _rival_binary_is_ul,
    "colored_value_selects_route": _rival_colored_is_ul,
    "coordinate_parity_selects_route": _rival_coordinate_parity,
    "first_anomaly_phase_selects_all_routes": _rival_first_phase,
    "hard_coded_canonical_tile_selects_route": _rival_fixed_tile_phase,
    "raw_input_zero_mask": _rival_raw_zero,
    "paint_entire_window": _rival_all_cells,
    "reverse_anomaly_order": _rival_reverse_order,
    "reuse_first_anomaly_color": _rival_first_color,
}


def rival_survivors(train: Any, settings: Any) -> list[str]:
    route = _setting(settings)
    survivors = []
    for name, rival in RIVALS.items():
        try:
            if all(rival(pair["input"], route) == pair["output"] for pair in train):
                survivors.append(name)
        except (ValueError, IndexError):
            continue
    return survivors


def validate_episode(episode: Any, *, settings: Any, demos: Any, queries: Any) -> None:
    route = _setting(settings)
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    if type(episode) is not dict or episode.get("program_solution") != program(settings):
        raise ValueError("episode program does not match settings")
    if episode.get("settings") != settings:
        raise ValueError("episode settings mismatch")
    seen = set()
    for split, count in (("train", demos), ("test", queries)):
        pairs = episode.get(split)
        if type(pairs) is not list or len(pairs) != count:
            raise ValueError(f"wrong {split} pair count")
        for pair in pairs:
            if type(pair) is not dict or not {"input", "output"} <= set(pair):
                raise ValueError("pair must contain input and output")
            grid = _grid(pair["input"], "input")
            _grid(pair["output"], "output")
            key = json.dumps(grid, separators=(",", ":"))
            if key in seen:
                raise ValueError("duplicate input across episode")
            seen.add(key)
            if transform(grid, settings) != pair["output"]:
                raise ValueError("stored label does not match the selected rule")
    if setting_survivors(episode["train"]) != [settings]:
        raise ValueError("demonstrations do not uniquely identify the setting")
    if rival_survivors(episode["train"], settings):
        raise ValueError("demonstrations leave a declared shortcut survivor")
