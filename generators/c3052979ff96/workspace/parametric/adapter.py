"""Native causal parametric family for ``c3052979ff96``.

``rotation_only`` is the exact canonical authority. ``relay_hit_color`` keeps
that rotation as step A, reads the unique color-5/6/7 cue orthogonally adjacent
to the rotated footprint as an input-dependent intermediate, then recolors
the cue and that color's separate payload as step B. Both settings use identical inputs.
"""
from __future__ import annotations

from collections import deque
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Iterable

from reviewer_support import canonical_path, find_root, load_selected_generator


TASK_ID = "c3052979ff96"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
MODES = ("rotation_only", "relay_hit_color")
HYPOTHESES = MODES + (
    "relay_fixed_role_0",
    "relay_fixed_role_1",
    "relay_fixed_role_2",
    "relay_code_role",
    "relay_quadrant_role",
    "relay_largest_payload",
    "relay_all_colors",
    "relay_first_target_cell",
    "rotation_code_one_clockwise",
    "relay_code_one_clockwise",
)
COLORS = (5, 6, 7)

# Connected payloads; sizes are intentionally varied so "pick the largest"
# cannot stand in for the hit-color relay.
_BAR3 = ((0, 0), (0, 1), (0, 2))
_BAR4 = ((0, 0), (0, 1), (0, 2), (0, 3))
_VBAR4 = ((0, 0), (1, 0), (2, 0), (3, 0))
_L5 = ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2))
_PLUS5 = ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1))
_BAR6 = tuple((0, col) for col in range(6))
_ZIG6 = ((0, 0), (0, 1), (1, 1), (1, 2), (2, 2), (2, 3))
_TOP10 = tuple((0, col) for col in range(10))
_RIGHT10 = tuple((row, 0) for row in range(10))
_BOTTOM_L11 = tuple((0, col) for col in range(6)) + tuple(
    (row, 0) for row in range(1, 6)
)


def _profile(
    height: int,
    width: int,
    code: int,
    shape_id: int,
    quadrant: int,
    relay_role: int,
    cue_index: int,
    payload_shapes: tuple[tuple[tuple[int, int], ...], ...],
    payload_slots: tuple[str, str, str],
    decoy_slots: tuple[str, str, str],
    control_slot: str = "bottom_right",
) -> dict[str, Any]:
    return {
        "height": height,
        "width": width,
        "code": code,
        "shape_id": shape_id,
        "quadrant": quadrant,
        "relay_role": relay_role,
        "cue_index": cue_index,
        "payload_shapes": payload_shapes,
        "payload_slots": payload_slots,
        "decoy_slots": decoy_slots,
        "control_slot": control_slot,
    }


# The first two demonstrations intentionally share code and source quadrant but
# hit different colors.  Thus code-only and source-location-only selectors fail
# before any query labels are consulted.
_DEMO_PROFILES = (
    _profile(
        12,
        14,
        1,
        2,
        2,
        0,
        1,
        (_BAR3, _BAR6, _L5),
        ("top_left", "top_right", "bottom_left"),
        ("left_mid", "right_mid", "bottom_mid"),
    ),
    _profile(
        14,
        14,
        1,
        4,
        2,
        2,
        0,
        (_BAR6, _BAR3, _VBAR4),
        ("bottom_left", "top_right", "top_left"),
        ("left_mid", "top_mid", "right_mid"),
    ),
    _profile(
        16,
        18,
        3,
        8,
        0,
        1,
        2,
        (_PLUS5, _ZIG6, _BAR4),
        ("top_right", "bottom_left", "bottom_right"),
        ("top_mid", "right_mid", "left_mid"),
    ),
    _profile(
        18,
        20,
        4,
        9,
        1,
        0,
        3,
        (_L5, _BAR4, _BAR6),
        ("right_mid", "top_left", "bottom_left"),
        ("bottom_mid", "left_mid", "top_mid"),
    ),
    _profile(
        22,
        24,
        3,
        5,
        3,
        2,
        1,
        (_ZIG6, _PLUS5, _BAR3),
        ("top_left", "bottom_right", "right_mid"),
        ("bottom_mid", "top_mid", "left_mid"),
    ),
    _profile(
        24,
        26,
        4,
        6,
        0,
        1,
        2,
        (_BAR4, _L5, _BAR6),
        ("bottom_left", "right_mid", "top_right"),
        ("left_mid", "bottom_mid", "top_mid"),
    ),
)

_QUERY_PROFILES = (
    _profile(
        13,
        17,
        3,
        3,
        1,
        1,
        1,
        (_L5, _BAR4, _BAR6),
        ("top_left", "bottom_right", "top_right"),
        ("left_mid", "top_mid", "bottom_mid"),
    ),
    _profile(
        18,
        20,
        4,
        7,
        3,
        0,
        2,
        (_PLUS5, _BAR6, _BAR3),
        ("bottom_left", "top_right", "right_mid"),
        ("top_mid", "left_mid", "bottom_mid"),
    ),
    _profile(
        22,
        24,
        2,
        8,
        0,
        2,
        3,
        (_BAR6, _L5, _ZIG6),
        ("top_right", "bottom_left", "bottom_right"),
        ("right_mid", "top_mid", "left_mid"),
    ),
    _profile(
        30,
        30,
        1,
        9,
        2,
        1,
        2,
        (_TOP10, _RIGHT10, _BOTTOM_L11),
        ("top_mid", "right_mid", "bottom_left"),
        ("left_mid", "top_mid", "bottom_mid"),
        "bottom_right",
    ),
)


def _integer(value: Any, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _mode(value: Any) -> str:
    if type(value) is not str or value not in MODES:
        raise ValueError("rule_mode must be rotation_only or relay_hit_color")
    return value


def _settings(value: Any) -> str:
    if type(value) is not dict or set(value) != {"rule_mode"}:
        raise ValueError("only the rule_mode setting is declared")
    return _mode(value["rule_mode"])


def grid(value: Any) -> list[list[int]]:
    if (
        type(value) is not list
        or not 1 <= len(value) <= 30
        or type(value[0]) is not list
        or not 1 <= len(value[0]) <= 30
        or any(
            type(row) is not list
            or len(row) != len(value[0])
            or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
            for row in value
        )
    ):
        raise ValueError(
            "grid must be rectangular 1..30 with exact integer colors 0..9"
        )
    return value


@lru_cache(maxsize=1)
def canonical_program() -> str:
    programs = {
        row["program_solution"]
        for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines()
        if (row := json.loads(line))["task_id"] == TASK_ID
    }
    if len(programs) != 1:
        raise ValueError("require one exact canonical authority")
    return programs.pop()


def program(settings: Any) -> str:
    selected = _settings(settings)
    if selected == "rotation_only":
        return canonical_program()
    return (HERE / "relay_hit_color.rkt").read_text(encoding="utf-8")


@lru_cache(maxsize=1)
def _source_module():
    module, _source, _sha256 = load_selected_generator(TASK_ID, root=ROOT)
    return module


def _components(value: list[list[int]], color: int) -> list[set[tuple[int, int]]]:
    remaining = {
        (row, col)
        for row, values in enumerate(value)
        for col, cell in enumerate(values)
        if cell == color
    }
    result: list[set[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        component = {start}
        queue = deque([start])
        while queue:
            row, col = queue.popleft()
            for drow, dcol in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                point = (row + drow, col + dcol)
                if point in remaining:
                    remaining.remove(point)
                    component.add(point)
                    queue.append(point)
        result.append(component)
    return sorted(result, key=lambda cells: min(cells))


def observe(value: Any) -> dict[str, Any]:
    source_grid = grid(value)
    source_components = _components(source_grid, 8)
    pivots = [
        (row, col)
        for row, values in enumerate(source_grid)
        for col, cell in enumerate(values)
        if cell == 9
    ]
    controls = [
        (row, col, cell)
        for row, values in enumerate(source_grid)
        for col, cell in enumerate(values)
        if 1 <= cell <= 4
    ]
    if len(source_components) != 1:
        raise ValueError("scene must contain one connected color-8 source")
    if len(pivots) != 1:
        raise ValueError("scene must contain one color-9 pivot")
    if len(controls) != 1:
        raise ValueError("scene must contain one control cell in 1..4")

    source = source_components[0]
    pivot = pivots[0]
    code = controls[0][2]
    target = [
        _source_module()._rotate_point(pivot, point, code)
        for point in sorted(source)
    ]
    if any(
        not (0 <= row < len(source_grid) and 0 <= col < len(source_grid[0]))
        for row, col in target
    ):
        raise ValueError("rotated footprint must remain in bounds")
    boundary_hits = []
    for row, values in enumerate(source_grid):
        for col, cell in enumerate(values):
            if cell not in COLORS:
                continue
            adjacent = [
                index
                for index, (target_row, target_col) in enumerate(target)
                if abs(row - target_row) + abs(col - target_col) == 1
            ]
            if adjacent:
                boundary_hits.append((adjacent, (row, col), cell))
    if len(boundary_hits) != 1:
        raise ValueError(
            "rotated footprint must have exactly one adjacent color-5/6/7 cue"
        )
    adjacent, cue_cell, relay_color = boundary_hits[0]
    if len(adjacent) != 1:
        raise ValueError("relay cue must be adjacent to exactly one target cell")
    cue_index = adjacent[0]

    color_counts = {
        color: sum(cell == color for row in source_grid for cell in row)
        for color in COLORS
    }
    if any(count < 4 for count in color_counts.values()):
        raise ValueError("each relay color needs one cue and a substantive payload")
    for color in COLORS:
        if len(_components(source_grid, color)) < 2:
            raise ValueError("each relay color must have separate cue and payload components")
    quadrant = _source_module()._strict_quadrant(source, pivot)
    if quadrant is None:
        raise ValueError("source must lie in one strict pivot quadrant")

    return {
        "height": len(source_grid),
        "width": len(source_grid[0]),
        "source": [list(point) for point in sorted(source)],
        "pivot": list(pivot),
        "code": code,
        "source_quadrant": quadrant,
        "target": [list(point) for point in target],
        "cue_target_index": cue_index,
        "cue_cell": list(cue_cell),
        "relay_color": relay_color,
        "color_counts": color_counts,
    }


def _paint(
    value: Any,
    colors: Iterable[int],
    target: Iterable[Iterable[int]] | None = None,
) -> list[list[int]]:
    state = observe(value)
    selected = set(colors)
    selected_target = state["target"] if target is None else [list(point) for point in target]
    output = [row[:] for row in value]
    for row, col in selected_target:
        if not (0 <= row < len(output) and 0 <= col < len(output[0])):
            raise ValueError("paint target must remain in bounds")
        output[row][col] = 2
    if selected:
        for row, values in enumerate(value):
            for col, cell in enumerate(values):
                if cell in selected:
                    output[row][col] = 2
    return output


def _target_for_code(state: dict[str, Any], code: int) -> list[list[int]]:
    pivot = tuple(state["pivot"])
    return [
        list(_source_module()._rotate_point(pivot, tuple(point), code))
        for point in state["source"]
    ]


def transform(value: Any, mode: Any) -> list[list[int]]:
    selected = _mode(mode)
    state = observe(value)
    colors: tuple[int, ...] = ()
    if selected == "relay_hit_color":
        colors = (state["relay_color"],)
    return _paint(value, colors)


def predict(value: Any, hypothesis: Any) -> list[list[int]]:
    if type(hypothesis) is not str or hypothesis not in HYPOTHESES:
        raise ValueError("unknown declared hypothesis")
    if hypothesis in MODES:
        return transform(value, hypothesis)
    state = observe(value)
    if hypothesis.startswith("relay_fixed_role_"):
        color = COLORS[int(hypothesis.rsplit("_", 1)[1])]
        return _paint(value, (color,))
    if hypothesis == "relay_code_role":
        return _paint(value, (COLORS[(state["code"] - 1) % len(COLORS)],))
    if hypothesis == "relay_quadrant_role":
        return _paint(value, (COLORS[state["source_quadrant"] % len(COLORS)],))
    if hypothesis == "relay_largest_payload":
        color = max(COLORS, key=lambda item: (state["color_counts"][item], -item))
        return _paint(value, (color,))
    if hypothesis == "relay_all_colors":
        return _paint(value, COLORS)
    if hypothesis == "relay_first_target_cell":
        colors = (state["relay_color"],) if state["cue_target_index"] == 0 else ()
        return _paint(value, colors)
    if hypothesis in {"rotation_code_one_clockwise", "relay_code_one_clockwise"}:
        wrong_target = (
            _target_for_code(state, 2) if state["code"] == 1 else state["target"]
        )
        colors = (state["relay_color"],) if hypothesis.startswith("relay_") else ()
        return _paint(value, colors, wrong_target)
    raise AssertionError("unhandled declared hypothesis")


def _sha256_grid(value: list[list[int]]) -> str:
    return hashlib.sha256(
        json.dumps(value, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def certificate(train: Any, query_inputs: Any) -> dict[str, Any]:
    if type(train) is not list or not 2 <= len(train) <= 6:
        raise ValueError("two through six demonstrations are required")
    if type(query_inputs) is not list or len(query_inputs) != 4:
        raise ValueError("exactly four query inputs are required")
    for pair in train:
        if type(pair) is not dict or set(pair) != {"input", "output"}:
            raise ValueError("each demonstration must contain input and output")
        grid(pair["input"])
        grid(pair["output"])
        observe(pair["input"])
    for value in query_inputs:
        grid(value)
        observe(value)

    survivors = [
        hypothesis
        for hypothesis in HYPOTHESES
        if all(predict(pair["input"], hypothesis) == pair["output"] for pair in train)
    ]
    if len(survivors) != 1 or survivors[0] not in MODES:
        raise ValueError(
            "demonstrations do not identify one setting against declared rivals: "
            + repr(survivors)
        )
    predictions = [predict(value, survivors[0]) for value in query_inputs]
    return {
        "declared_hypotheses": list(HYPOTHESES),
        "survivors": survivors,
        "demos": len(train),
        "queries": len(query_inputs),
        "demo_codes": [observe(pair["input"])["code"] for pair in train],
        "demo_relay_colors": [
            observe(pair["input"])["relay_color"] for pair in train
        ],
        "query_codes": [observe(value)["code"] for value in query_inputs],
        "query_relay_colors": [observe(value)["relay_color"] for value in query_inputs],
        "predicted_query_sha256": [_sha256_grid(value) for value in predictions],
        "scope": (
            "Finite declared rivals. The first two demonstrations share code and "
            "source quadrant but hit different cue colors; payload sizes and cue "
            "positions also vary."
        ),
    }


def _shape_size(shape: tuple[tuple[int, int], ...]) -> tuple[int, int]:
    return 1 + max(row for row, _ in shape), 1 + max(col for _, col in shape)


def _slot_anchor(
    slot: str, height: int, width: int, shape: tuple[tuple[int, int], ...]
) -> tuple[int, int]:
    shape_height, shape_width = _shape_size(shape)
    middle_row = max(0, (height - shape_height) // 2)
    middle_col = max(0, (width - shape_width) // 2)
    slots = {
        "top_left": (0, 0),
        "top_mid": (0, middle_col),
        "top_right": (0, width - shape_width),
        "left_mid": (middle_row, 0),
        "center": (middle_row, middle_col),
        "right_mid": (middle_row, width - shape_width),
        "bottom_left": (height - shape_height, 0),
        "bottom_mid": (height - shape_height, middle_col),
        "bottom_right": (height - shape_height, width - shape_width),
    }
    try:
        return slots[slot]
    except KeyError as exc:
        raise ValueError(f"unknown placement slot {slot!r}") from exc


def _candidate_cells(
    anchor: tuple[int, int], shape: tuple[tuple[int, int], ...]
) -> tuple[tuple[int, int], ...]:
    return tuple((anchor[0] + row, anchor[1] + col) for row, col in shape)


def _place_shape(
    value: list[list[int]],
    shape: tuple[tuple[int, int], ...],
    color: int,
    slot: str,
    forbidden: set[tuple[int, int]],
    rng: random.Random,
) -> tuple[tuple[int, int], ...]:
    height, width = len(value), len(value[0])
    shape_height, shape_width = _shape_size(shape)
    preferred = _slot_anchor(slot, height, width, shape)
    candidates: list[tuple[tuple[int, int], tuple[tuple[int, int], ...]]] = []
    for anchor_row in range(height - shape_height + 1):
        for anchor_col in range(width - shape_width + 1):
            cells = _candidate_cells((anchor_row, anchor_col), shape)
            cell_set = set(cells)
            if any(point in forbidden or value[point[0]][point[1]] != 0 for point in cells):
                continue
            touches_same = False
            for row, col in cells:
                for drow, dcol in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    other = (row + drow, col + dcol)
                    if other in cell_set:
                        continue
                    if (
                        0 <= other[0] < height
                        and 0 <= other[1] < width
                        and value[other[0]][other[1]] == color
                    ):
                        touches_same = True
                        break
                if touches_same:
                    break
            if touches_same:
                continue
            boundary_misses = 0
            if slot.startswith("top_") and anchor_row != 0:
                boundary_misses += 1
            if slot.startswith("bottom_") and anchor_row != height - shape_height:
                boundary_misses += 1
            if slot.endswith("_left") and anchor_col != 0:
                boundary_misses += 1
            if slot.endswith("_right") and anchor_col != width - shape_width:
                boundary_misses += 1
            if slot == "left_mid" and anchor_col != 0:
                boundary_misses += 1
            if slot == "right_mid" and anchor_col != width - shape_width:
                boundary_misses += 1
            distance = abs(anchor_row - preferred[0]) + abs(anchor_col - preferred[1])
            candidates.append(((boundary_misses, distance), cells))
    if not candidates:
        raise RuntimeError(f"cannot place color-{color} shape in slot {slot}")
    best_score = min(score for score, _cells in candidates)
    best = [cells for score, cells in candidates if score == best_score]
    cells = rng.choice(best)
    for row, col in cells:
        value[row][col] = color
    return cells


def _choose_geometry(
    rng: random.Random, profile: dict[str, Any]
) -> tuple[tuple[int, int], tuple[tuple[int, int], ...], tuple[tuple[int, int], ...]]:
    candidates = _source_module()._geometry_candidates(
        profile["height"],
        profile["width"],
        profile["shape_id"],
        profile["code"],
        profile["quadrant"],
    )
    if profile["code"] == 1:
        # Identity examples must also give the declared clockwise shortcut a
        # lawful alternative footprint; otherwise the rival is undefined
        # rather than visibly wrong.
        candidates = [
            item
            for item in candidates
            if all(
                0 <= rotated[0] < profile["height"]
                and 0 <= rotated[1] < profile["width"]
                for rotated in (
                    _source_module()._rotate_point(item[0], point, 2)
                    for point in item[1]
                )
            )
        ]
    if not candidates:
        raise RuntimeError("profile has no lawful core geometry")
    center_row = (profile["height"] - 1) / 2
    center_col = (profile["width"] - 1) / 2
    scored = sorted(
        candidates,
        key=lambda item: (
            abs(item[0][0] - center_row) + abs(item[0][1] - center_col),
            item,
        ),
    )
    pool = scored[: min(12, len(scored))]
    return rng.choice(pool)


def _scene(
    seed: int,
    label: str,
    index: int,
    profile: dict[str, Any],
    role_colors: tuple[int, int, int],
) -> list[list[int]]:
    digest = hashlib.sha256(
        f"{TASK_ID}-relay-scene-v1:{seed}:{label}:{index}".encode("ascii")
    ).digest()
    rng = random.Random(digest)
    height, width = profile["height"], profile["width"]
    value = [[0] * width for _ in range(height)]
    pivot, source, target = _choose_geometry(rng, profile)
    value[pivot[0]][pivot[1]] = 9
    for row, col in source:
        value[row][col] = 8

    selected_role = profile["relay_role"]
    selected_color = role_colors[selected_role]
    target_set = set(target)
    desired_index = profile["cue_index"] % len(target)
    cue_options: list[tuple[int, tuple[int, int]]] = []
    for offset in range(len(target)):
        target_index = (desired_index + offset) % len(target)
        target_row, target_col = target[target_index]
        local = []
        for drow, dcol in ((0, 1), (1, 0), (0, -1), (-1, 0)):
            point = (target_row + drow, target_col + dcol)
            if not (0 <= point[0] < height and 0 <= point[1] < width):
                continue
            if point in target_set or point == pivot or point in source:
                continue
            if value[point[0]][point[1]] != 0:
                continue
            adjacent = sum(
                abs(point[0] - row) + abs(point[1] - col) == 1
                for row, col in target
            )
            if adjacent == 1:
                local.append((target_index, point))
        if local:
            cue_options = local
            break
    if not cue_options:
        raise RuntimeError("cannot place an unambiguous adjacent relay cue")
    cue_index, cue = rng.choice(cue_options)
    value[cue[0]][cue[1]] = selected_color

    target_boundary = {
        (row + drow, col + dcol)
        for row, col in target
        for drow, dcol in ((1, 0), (-1, 0), (0, 1), (0, -1))
        if 0 <= row + drow < height and 0 <= col + dcol < width
    }
    forbidden = set(source) | target_set | target_boundary | {pivot}
    for role, color in enumerate(role_colors):
        _place_shape(
            value,
            profile["payload_shapes"][role],
            color,
            profile["payload_slots"][role],
            forbidden,
            rng,
        )
    for role, color in enumerate(role_colors):
        if role == selected_role:
            continue
        _place_shape(
            value,
            ((0, 0),),
            color,
            profile["decoy_slots"][role],
            forbidden,
            rng,
        )

    _place_shape(
        value,
        ((0, 0),),
        profile["code"],
        profile["control_slot"],
        forbidden,
        rng,
    )
    state = observe(value)
    if state["relay_color"] != selected_color:
        raise AssertionError("constructed relay cue does not match selected role")
    if state["cue_target_index"] != cue_index:
        raise AssertionError("constructed relay cue index changed")
    return value


def _role_colors(seed: int) -> tuple[int, int, int]:
    rng = random.Random(
        hashlib.sha256(f"{TASK_ID}-relay-palette-v1:{seed}".encode("ascii")).digest()
    )
    colors = list(COLORS)
    rng.shuffle(colors)
    return tuple(colors)  # type: ignore[return-value]


def _pair(value: list[list[int]], mode: str) -> dict[str, list[list[int]]]:
    return {"input": value, "output": transform(value, mode)}


def _inputs(seed: int, demos: int) -> tuple[list[list[list[int]]], list[list[list[int]]]]:
    role_colors = _role_colors(seed)
    train = [
        _scene(seed, "demo", index, profile, role_colors)
        for index, profile in enumerate(_DEMO_PROFILES[:demos])
    ]
    test = [
        _scene(seed, "query", index, profile, role_colors)
        for index, profile in enumerate(_QUERY_PROFILES)
    ]
    visible = [json.dumps(value, separators=(",", ":")) for value in train + test]
    if len(visible) != len(set(visible)):
        raise AssertionError("profile construction produced duplicate inputs")
    return train, test


def generate(seed: Any, settings: Any, demos: Any, queries: Any) -> dict[str, Any]:
    _integer(seed, "seed", 0, 2**63 - 1)
    _integer(demos, "demos", 2, 6)
    _integer(queries, "queries", 4, 4)
    selected = _settings(settings)
    train_inputs, query_inputs = _inputs(seed, demos)

    for mode in MODES:
        teaching = [_pair(value, mode) for value in train_inputs]
        proof = certificate(teaching, query_inputs)
        if proof["survivors"] != [mode]:
            raise AssertionError("teaching inputs do not identify both rule modes")

    return {
        "train": [_pair(value, selected) for value in train_inputs],
        "test": [_pair(value, selected) for value in query_inputs],
        "program_solution": program(settings),
    }
