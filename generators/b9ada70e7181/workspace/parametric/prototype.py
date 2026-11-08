"""Native candidate for chamber-dependent stable gravity.

``all_down`` is the exact canonical program.  In ``chamber_parity`` mode,
step A counts all non-wall pebbles in each wall-delimited chamber and derives a
chamber direction (even -> up, odd -> down).  Step B stable-packs every column
of that chamber toward the derived edge.  Inputs are sampled independently of
the hidden episode setting and include crossed controls that separate chamber
parity from per-column counts and fixed-direction shortcuts.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import random
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
TASK_ID = "b9ada70e7181"
GRAVITY_POLICIES = ("all_down", "chamber_parity")
DEFAULT_SETTINGS = {"gravity_policy": "all_down"}
PARAMETERS = {"gravity_policy": list(GRAVITY_POLICIES)}
DEMO_LIMITS = (2, 6)
QUERY_LIMITS = (4, 4)
CANONICAL_PROGRAM = (HERE / "canonical.rkt").read_text(encoding="utf-8")
PARITY_PROGRAM = (HERE / "parity.rkt").read_text(encoding="utf-8")
PALETTE = (1, 2, 3, 4, 5, 6, 7, 9)

# Distinct sizes make accidental duplicate inputs impossible while still varying
# wall count, density and aspect ratio.  The last query is a substantive 30x30.
_DEMO_PROFILES = (
    (8, 11, 2),
    (9, 13, 3),
    (10, 14, 2),
    (11, 16, 3),
    (12, 18, 3),
    (14, 20, 3),
)
_QUERY_PROFILES = (
    (7, 12, 2),
    (13, 17, 3),
    (22, 25, 3),
    (30, 30, 3),
)

RIVAL_POLICIES = {
    "all_down": (
        "all_up",
        "reverse_down",
        "chamber_parity",
        "per_column_parity",
        "chamber_index_parity",
        "reverse_chamber_index_parity",
    ),
    "chamber_parity": (
        "all_down",
        "all_up",
        "per_column_parity",
        "nonempty_column_parity",
        "first_column_parity",
        "chamber_index_parity",
        "reverse_chamber_index_parity",
        "chamber_width_parity",
        "left_boundary_parity",
        "occupied_rows_parity",
        "top_row_parity",
        "bottom_row_parity",
        "first_color_parity",
        "color_sum_parity",
        "unique_colors_parity",
        "max_color_parity",
        "reverse_parity",
    ),
}


def _integer(value: object, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _settings(value: object) -> dict[str, str]:
    if type(value) is not dict or set(value) != {"gravity_policy"}:
        raise ValueError("settings must name exactly gravity_policy")
    policy = value["gravity_policy"]
    if type(policy) is not str or policy not in GRAVITY_POLICIES:
        raise ValueError(f"gravity_policy must be one of {GRAVITY_POLICIES}")
    return {"gravity_policy": policy}


def _grid(value: object) -> list[list[int]]:
    if (
        type(value) is not list
        or not 1 <= len(value) <= 30
        or type(value[0]) is not list
        or not 1 <= len(value[0]) <= 30
    ):
        raise ValueError("grid must have 1..30 rows and columns")
    width = len(value[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in value
    ):
        raise ValueError("grid must be rectangular with exact integer ARC colors")
    return [row[:] for row in value]


def program(settings: object) -> str:
    selected = _settings(settings)
    return CANONICAL_PROGRAM if selected == DEFAULT_SETTINGS else PARITY_PROGRAM


def _digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _rng(seed: int, split: str, index: int) -> random.Random:
    return random.Random(int(_digest([TASK_ID, "chamber-parity-v1", seed, split, index]), 16))


def _wall_layout(width: int, wall_count: int, rng: random.Random) -> tuple[list[int], list[tuple[int, int]]]:
    chamber_count = wall_count + 1
    # The first two chambers need three columns for an exact shared two-stack,
    # a protected singleton control, and a filler column.  Others need two.
    minimums = [3, 3] + [2] * (chamber_count - 2)
    available = width - wall_count
    if sum(minimums) > available:
        raise ValueError("profile is too narrow for crossed chamber controls")
    widths = minimums[:]
    # Keep the first two crossed-control chambers geometrically identical.  All
    # spare width goes to later chambers, which still vary freely with the seed.
    for _ in range(available - sum(widths)):
        widths[rng.randrange(2, chamber_count)] += 1
    walls: list[int] = []
    chambers: list[tuple[int, int]] = []
    cursor = 0
    for index, chamber_width in enumerate(widths):
        chambers.append((cursor, cursor + chamber_width - 1))
        cursor += chamber_width
        if index < wall_count:
            walls.append(cursor)
            cursor += 1
    if cursor != width:
        raise AssertionError((cursor, width, widths, walls))
    return walls, chambers


def _target_parities(seed: int, split: str, index: int, chamber_count: int) -> list[int]:
    """Choose scene-local chamber parities without encoding them by chamber rank.

    The first two chambers always have opposite parity so their identical stack
    profiles are a crossed control.  At the minimum two-demo lesson, chamber
    ranks 0/1 change parity while rank 2 stays fixed; this simultaneously defeats
    a static rank lookup and a rule that counts only chamber 0 then extrapolates
    fixed relative directions to the remaining chambers.
    """
    if chamber_count < 3:
        raise ValueError("crossed controls require at least three chambers")
    rng = _rng(seed, f"{split}-parity", index)
    if split == "demo" and index in (0, 1):
        base = _rng(seed, "demo-parity-pair", 0).randrange(2)
        if index == 0:
            parities = [base, 1 - base, 0]
        else:
            parities = [1 - base, base, 0, 1]
    else:
        first = rng.randrange(2)
        parities = [first, 1 - first]
    while len(parities) < chamber_count:
        parities.append(rng.randrange(2))
    return parities[:chamber_count]


def _target_counts(height: int, parities: list[int]) -> list[int]:
    # Counts are separated by two so parity is the only branch signal while
    # larger canvases still carry more content without approaching capacity.
    even_base = min(14, max(6, 2 * (height // 4)))
    if even_base % 2:
        even_base += 1
    return [
        (8 + parity) if index < 2 else (even_base + parity)
        for index, parity in enumerate(parities)
    ]


def _choose_colors(rng: random.Random, count: int) -> list[int]:
    colors: list[int] = []
    while len(colors) < count:
        candidate = rng.choice(PALETTE)
        if len(colors) < 2 and candidate in colors:
            continue
        colors.append(candidate)
    return colors


def _build_scene(seed: int, split: str, index: int) -> list[list[int]]:
    profiles = _DEMO_PROFILES if split == "demo" else _QUERY_PROFILES
    if not 0 <= index < len(profiles):
        raise ValueError(f"unsupported {split} index {index}")
    height, width, wall_count = profiles[index]
    rng = _rng(seed, split, index)
    walls, chambers = _wall_layout(width, wall_count, rng)
    grid = [[0] * width for _ in range(height)]
    for wall in walls:
        for row in range(height):
            grid[row][wall] = 8

    shared_rows = (1, height - 2)
    parities = _target_parities(seed, split, index, len(chambers))
    targets = _target_counts(height, parities)
    duplicate_base = rng.choice((1, 2, 3))
    even_duplicate = 2 * duplicate_base
    omitted = rng.choice([
        color for color in PALETTE if color not in {duplicate_base, even_duplicate}
    ])
    common_control_colors = [color for color in PALETTE if color != omitted]
    rng.shuffle(common_control_colors)
    control_colors = {
        8: common_control_colors + [even_duplicate],
        9: common_control_colors + [duplicate_base, duplicate_base],
    }
    control_singleton_row = height // 2
    control_filler_candidates = [
        row
        for row in range(1, height - 1)
        if row != shared_rows[0]
    ]
    control_filler_rows = [
        0,
        height - 1,
        *rng.sample(control_filler_candidates, 3),
    ]
    for chamber_index, ((left, right), target) in enumerate(zip(chambers, targets)):
        width_here = right - left + 1
        if chamber_index < 2:
            if width_here != 3 or target not in (8, 9):
                raise AssertionError((chamber_index, width_here, target))
            stack_col, singleton_col, filler_col = left, left + 1, right
            positions = [
                (shared_rows[0], stack_col),
                (shared_rows[1], stack_col),
                (control_singleton_row, singleton_col),
                *((row, filler_col) for row in control_filler_rows),
            ]
            colors = control_colors[target]
            for (row, column), color in zip(positions, colors[:8]):
                grid[row][column] = color
            if target == 9:
                # The 8-cell and 9-cell color multisets have the same exact sum,
                # unique-color set and maximum.  The extra cell also reuses an
                # occupied row, so only total pebble-count parity changes.
                grid[shared_rows[0]][filler_col] = colors[8]
            actual = sum(
                grid[row][column] not in (0, 8)
                for row in range(height)
                for column in range(left, right + 1)
            )
            if actual != target:
                raise AssertionError((chamber_index, actual, target))
            continue

        stack_col = left if chamber_index < 2 else (right if chamber_index == len(chambers) - 1 else left)
        upper = 1 + (seed + index + chamber_index) % max(1, height // 3)
        lower = height - 2 - (seed + 2 * index + chamber_index) % max(1, height // 4)
        if upper >= lower:
            upper, lower = 1, height - 2
        stack_rows = (upper, lower)
        colors = _choose_colors(rng, target)
        grid[stack_rows[0]][stack_col] = colors[0]
        grid[stack_rows[1]][stack_col] = colors[1]
        placed = {(stack_rows[0], stack_col), (stack_rows[1], stack_col)}

        forbidden_columns = {stack_col}
        remaining = target - len(placed)
        filler_columns = [c for c in range(left, right + 1) if c not in forbidden_columns]
        if not filler_columns:
            raise ValueError("crossed-control chamber has no filler column")
        available = [
            (row, column)
            for column in filler_columns
            for row in range(height)
            if (row, column) not in placed
        ]
        if remaining > len(available):
            raise ValueError("profile does not have enough filler capacity")

        forced: list[tuple[int, int]] = []
        if chamber_index == 0:
            forced.append((0, filler_columns[0]))
        if chamber_index == len(chambers) - 1:
            forced.append((height - 1, filler_columns[-1]))
        for position in forced:
            if remaining and position in available and position not in placed:
                row, column = position
                grid[row][column] = colors[len(placed)]
                placed.add(position)
                available.remove(position)
                remaining -= 1
        for row, column in rng.sample(available, remaining):
            grid[row][column] = colors[len(placed)]
            placed.add((row, column))

        actual = sum(
            grid[row][column] not in (0, 8)
            for row in range(height)
            for column in range(left, right + 1)
        )
        if actual != target:
            raise AssertionError((chamber_index, actual, target))
        if width_here < 2:
            raise AssertionError("zero-width/one-column chamber escaped layout")

    report = analyze_scene(grid)
    if {chamber["count"] % 2 for chamber in report["chambers"]} != {0, 1}:
        raise AssertionError("scene lost mixed chamber parity")
    if not report["opposite_parity_shared_stack_profiles"]:
        raise AssertionError("scene lost crossed stack profile")
    if not report["mixed_column_count_chambers"]:
        raise AssertionError("scene lost mixed column-count control")
    return grid


def sample_input(seed: int, split: str, index: int) -> list[list[int]]:
    _integer(seed, 0, 2**63 - 1, "seed")
    if split not in {"demo", "query"}:
        raise ValueError("split must be demo or query")
    return _build_scene(seed, split, index)


def _walls_and_chambers(grid: list[list[int]]) -> tuple[list[int], list[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    walls = [column for column in range(width) if all(grid[row][column] == 8 for row in range(height))]
    if not 2 <= len(walls) <= 3:
        raise ValueError(f"expected 2..3 full-height color-8 walls, got {walls}")
    edges = [-1] + walls + [width]
    chambers = [(left + 1, right - 1) for left, right in zip(edges, edges[1:])]
    if any(left > right for left, right in chambers):
        raise ValueError("wall layout contains an empty chamber")
    return walls, chambers


def derive_chamber_states(grid: object, policy: str) -> list[dict[str, Any]]:
    normalized = _grid(grid)
    if policy not in GRAVITY_POLICIES:
        raise ValueError(f"unsupported policy {policy}")
    _walls, chambers = _walls_and_chambers(normalized)
    states = []
    for left, right in chambers:
        count = sum(
            normalized[row][column] not in (0, 8)
            for row in range(len(normalized))
            for column in range(left, right + 1)
        )
        direction = "down" if policy == "all_down" or count % 2 else "up"
        states.append({"left": left, "right": right, "count": count, "direction": direction})
    return states


def pack_columns(grid: object, states: object, *, reverse_order: bool = False) -> list[list[int]]:
    normalized = _grid(grid)
    if type(states) is not list or not states:
        raise ValueError("states must be a nonempty chamber-state list")
    height, width = len(normalized), len(normalized[0])
    walls, chambers = _walls_and_chambers(normalized)
    if len(states) != len(chambers):
        raise ValueError("state count does not match chamber count")
    output = [[0] * width for _ in range(height)]
    for wall in walls:
        for row in range(height):
            output[row][wall] = 8
    for expected, state in zip(chambers, states):
        if type(state) is not dict or (state.get("left"), state.get("right")) != expected:
            raise ValueError("state bounds do not match the input chambers")
        direction = state.get("direction")
        if direction not in {"up", "down"}:
            raise ValueError("state direction must be up or down")
        for column in range(expected[0], expected[1] + 1):
            values = [normalized[row][column] for row in range(height) if normalized[row][column] not in (0, 8)]
            if reverse_order:
                values = list(reversed(values))
            start = 0 if direction == "up" else height - len(values)
            for offset, value in enumerate(values):
                output[start + offset][column] = value
    return output


def transform(grid: object, settings: object) -> list[list[int]]:
    selected = _settings(settings)
    normalized = _grid(grid)
    states = derive_chamber_states(normalized, selected["gravity_policy"])
    return pack_columns(normalized, states)


def _rival_states(grid: list[list[int]], rival: str) -> tuple[list[dict[str, Any]], bool]:
    walls, chambers = _walls_and_chambers(grid)
    del walls
    parity = derive_chamber_states(grid, "chamber_parity")
    reverse = rival in {"reverse_down", "reverse_parity"}
    states: list[dict[str, Any]] = []
    for index, ((left, right), correct) in enumerate(zip(chambers, parity)):
        column_counts = [
            sum(grid[row][column] not in (0, 8) for row in range(len(grid)))
            for column in range(left, right + 1)
        ]
        if rival in {"all_down", "reverse_down"}:
            direction = "down"
        elif rival == "all_up":
            direction = "up"
        elif rival in {"chamber_parity", "reverse_parity"}:
            direction = correct["direction"]
        elif rival == "per_column_parity":
            # This is represented separately in transform_rival because a single
            # chamber state cannot encode different directions per column.
            direction = "down"
        elif rival == "nonempty_column_parity":
            direction = "up" if sum(count > 0 for count in column_counts) % 2 == 0 else "down"
        elif rival == "first_column_parity":
            direction = "up" if column_counts[0] % 2 == 0 else "down"
        elif rival == "chamber_index_parity":
            direction = "up" if index % 2 == 0 else "down"
        elif rival == "reverse_chamber_index_parity":
            direction = "down" if index % 2 == 0 else "up"
        else:
            cells = [
                (row, column, grid[row][column])
                for row in range(len(grid))
                for column in range(left, right + 1)
                if grid[row][column] not in (0, 8)
            ]
            values = [value for _row, _column, value in cells]
            if rival == "chamber_width_parity":
                metric = right - left + 1
            elif rival == "left_boundary_parity":
                metric = left
            elif rival == "occupied_rows_parity":
                metric = len({row for row, _column, _value in cells})
            elif rival == "top_row_parity":
                metric = min(row for row, _column, _value in cells)
            elif rival == "bottom_row_parity":
                metric = max(row for row, _column, _value in cells)
            elif rival == "first_color_parity":
                metric = min(cells)[2]
            elif rival == "color_sum_parity":
                metric = sum(values)
            elif rival == "unique_colors_parity":
                metric = len(set(values))
            elif rival == "max_color_parity":
                metric = max(values)
            else:
                raise ValueError(f"unknown rival {rival}")
            direction = "up" if metric % 2 == 0 else "down"
        states.append({"left": left, "right": right, "count": correct["count"], "direction": direction})
    return states, reverse


def transform_rival(grid: object, rival: str) -> list[list[int]]:
    normalized = _grid(grid)
    if rival == "per_column_parity":
        height, width = len(normalized), len(normalized[0])
        walls, chambers = _walls_and_chambers(normalized)
        output = [[0] * width for _ in range(height)]
        for wall in walls:
            for row in range(height):
                output[row][wall] = 8
        for left, right in chambers:
            for column in range(left, right + 1):
                values = [normalized[row][column] for row in range(height) if normalized[row][column] not in (0, 8)]
                direction = "up" if len(values) % 2 == 0 else "down"
                start = 0 if direction == "up" else height - len(values)
                for offset, value in enumerate(values):
                    output[start + offset][column] = value
        return output
    states, reverse = _rival_states(normalized, rival)
    return pack_columns(normalized, states, reverse_order=reverse)


def analyze_scene(grid: object) -> dict[str, Any]:
    normalized = _grid(grid)
    walls, chambers = _walls_and_chambers(normalized)
    height = len(normalized)
    rows_by_profile: dict[tuple[int, ...], list[tuple[int, int]]] = {}
    chamber_rows: list[dict[str, Any]] = []
    nonpalindromic = 0
    mixed: list[int] = []
    for index, (left, right) in enumerate(chambers):
        columns = []
        count = 0
        for column in range(left, right + 1):
            cells = [(row, normalized[row][column]) for row in range(height) if normalized[row][column] not in (0, 8)]
            values = [value for _row, value in cells]
            count += len(values)
            columns.append({"column": column, "count": len(values), "rows": [row for row, _ in cells], "values": values})
            if len(values) >= 2 and values != list(reversed(values)):
                nonpalindromic += 1
            if len(values) == 2:
                profile = tuple(row for row, _ in cells)
                rows_by_profile.setdefault(profile, []).append((index, count))
        nonzero_counts = {column["count"] for column in columns if column["count"]}
        if len(nonzero_counts) >= 2:
            mixed.append(index)
        chamber_rows.append({
            "index": index,
            "left": left,
            "right": right,
            "count": count,
            "direction": "up" if count % 2 == 0 else "down",
            "columns": columns,
        })
    shared = []
    for profile, occurrences in rows_by_profile.items():
        indices = {index for index, _partial in occurrences}
        if len(indices) < 2:
            continue
        parities = {chamber_rows[index]["count"] % 2 for index in indices}
        if parities == {0, 1}:
            shared.append({"rows": list(profile), "chambers": sorted(indices)})
    return {
        "height": len(normalized),
        "width": len(normalized[0]),
        "walls": walls,
        "chambers": chamber_rows,
        "opposite_parity_shared_stack_profiles": shared,
        "mixed_column_count_chambers": mixed,
        "nonpalindromic_stack_count": nonpalindromic,
    }


def _threshold_shortcuts(train: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return simple monotone chamber-metric rules fitting every demonstration.

    A parity task is not taught if all observed odd chambers merely lie above a
    scalar threshold and all even chambers below it (or vice versa).  Check both
    the intended total count and a color-value aggregate that previously acted as
    a proxy for count in the minimum lesson.
    """
    metric_rows: dict[str, list[tuple[int, str]]] = {
        "count": [],
        "color_sum": [],
    }
    for pair in train:
        report = analyze_scene(pair["input"])
        for chamber in report["chambers"]:
            values = [
                value
                for column in chamber["columns"]
                for value in column["values"]
            ]
            metric_rows["count"].append((chamber["count"], chamber["direction"]))
            metric_rows["color_sum"].append((sum(values), chamber["direction"]))

    survivors: list[dict[str, Any]] = []
    for metric, rows in metric_rows.items():
        values = sorted({value for value, _direction in rows})
        cuts = [
            values[0] - 0.5,
            *[(left + right) / 2 for left, right in zip(values, values[1:])],
            values[-1] + 0.5,
        ]
        for cut in cuts:
            for low_is_up in (True, False):
                def predict(value: int) -> str:
                    up = (value <= cut) == low_is_up
                    return "up" if up else "down"

                if all(predict(value) == direction for value, direction in rows):
                    survivors.append({
                        "metric": metric,
                        "cut": cut,
                        "low_is_up": low_is_up,
                    })
    return survivors


def _datum(grid: list[list[int]]) -> str:
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def execute_rule(source: str, grid: object, *, bridge: Any | None = None) -> list[list[int]]:
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    normalized = _grid(grid)
    own = bridge is None
    bridge = RacketBridge(timeout=60) if own else bridge
    try:
        return _grid(bridge.eval_text(f"({wrap_rule(source)} {_datum(normalized)})"))
    finally:
        if own:
            bridge.close()


def certify(episode: object) -> dict[str, Any]:
    if type(episode) is not dict:
        raise ValueError("episode must be a dictionary")
    selected = _settings(episode.get("settings"))
    if episode.get("program_solution") != program(selected):
        raise ValueError("program does not match selected setting")
    train, test = episode.get("train"), episode.get("test")
    if (
        type(train) is not list
        or type(test) is not list
        or not DEMO_LIMITS[0] <= len(train) <= DEMO_LIMITS[1]
        or len(test) != QUERY_LIMITS[0]
    ):
        raise ValueError("episode needs 2..6 demonstrations and exactly four queries")
    for split, pairs in (("train", train), ("test", test)):
        for index, pair in enumerate(pairs):
            if type(pair) is not dict or transform(pair.get("input"), selected) != pair.get("output"):
                raise ValueError(f"label mismatch in {split}[{index}]")
    input_keys = [_digest(pair["input"]) for pair in train + test]
    if len(input_keys) != len(set(input_keys)):
        raise ValueError("all episode inputs must be distinct")
    declared_survivors = [
        {"gravity_policy": candidate}
        for candidate in GRAVITY_POLICIES
        if all(transform(pair["input"], {"gravity_policy": candidate}) == pair["output"] for pair in train)
    ]
    if declared_survivors != [selected]:
        raise ValueError(f"declared setting is not uniquely taught: {declared_survivors}")
    surviving_rivals = [
        rival
        for rival in RIVAL_POLICIES[selected["gravity_policy"]]
        if all(transform_rival(pair["input"], rival) == pair["output"] for pair in train)
    ]
    if surviving_rivals:
        raise ValueError(f"shortcut rivals survive demonstrations: {surviving_rivals}")
    threshold_shortcuts = (
        _threshold_shortcuts(train)
        if selected["gravity_policy"] == "chamber_parity"
        else []
    )
    if threshold_shortcuts:
        raise ValueError(f"threshold shortcut survives demonstrations: {threshold_shortcuts}")
    return {
        "demo_only": True,
        "declared_survivors": declared_survivors,
        "rejected_rivals": list(RIVAL_POLICIES[selected["gravity_policy"]]),
        "rejected_episode_shortcuts": (
            ["count_threshold", "color_sum_threshold"]
            if selected["gravity_policy"] == "chamber_parity"
            else []
        ),
        "query_count": len(test),
    }


def generate(seed: int, settings: object, demos: int = 3, queries: int = 4) -> dict[str, Any]:
    seed = _integer(seed, 0, 2**63 - 1, "seed")
    demos = _integer(demos, DEMO_LIMITS[0], DEMO_LIMITS[1], "demos")
    queries = _integer(queries, QUERY_LIMITS[0], QUERY_LIMITS[1], "queries")
    selected = _settings(settings)
    train_inputs = [sample_input(seed, "demo", index) for index in range(demos)]
    query_inputs = [sample_input(seed, "query", index) for index in range(queries)]
    keys = [_digest(grid) for grid in train_inputs + query_inputs]
    if len(keys) != len(set(keys)):
        raise ValueError("all demonstration and query inputs must be distinct")
    episode = {
        "schema": f"{TASK_ID}-chamber-parity-parametric-v1",
        "task_id": TASK_ID,
        "seed": seed,
        "settings": selected,
        "train": [{"input": grid, "output": transform(grid, selected)} for grid in train_inputs],
        "test": [{"input": grid, "output": transform(grid, selected)} for grid in query_inputs],
        "program_solution": program(selected),
    }
    episode["certificate"] = certify(episode)
    return episode
