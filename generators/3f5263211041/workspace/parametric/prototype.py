"""Matched-input direct-gallery / transformed-width relay lessons.

``direct`` is the byte-exact selected canonical program. ``width_relay`` keeps
its keyed-library lookup and transform vocabulary, but treats the first
instruction as a controller: transform that selected pattern (A), measure the
resulting width (the input-dependent intermediate, always 2 or 3), then use it
to choose the second or third of three payload instructions (B).  The first
payload is a visible distractor.  Inputs are independent of the hidden setting.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Callable

from reviewer_support import find_root, load_selected_generator, public_challenge_bytes

TASK_ID = "3f5263211041"
VERSION = "width-relay-v1"
HERE = Path(__file__).resolve().parent
MODES = ("direct", "width_relay")
PROGRAM_PATHS = {
    "direct": HERE / "canonical.rkt",
    "width_relay": HERE / "width_relay.rkt",
}

_BASE, _BASE_PATH, _BASE_SHA256 = load_selected_generator(TASK_ID, root=find_root(__file__))

# Frame top/left coordinates.  Every scene leaves a blank row before the final
# two control rows; the 30x30 case uses both horizontal edges and deep rows.
_PROFILES: dict[str, tuple[int, int, tuple[tuple[int, int], ...]]] = {
    "minimum": (10, 17, ((1, 0), (1, 6), (1, 12))),
    "compact": (14, 21, ((1, 0), (3, 8), (5, 16))),
    "wide": (16, 30, ((1, 0), (4, 12), (7, 25))),
    "tall": (30, 17, ((1, 0), (11, 6), (21, 12))),
    "square24": (24, 24, ((1, 0), (8, 9), (15, 19))),
    "stress30": (30, 30, ((1, 0), (12, 13), (21, 25))),
    "medium19": (12, 19, ((1, 0), (2, 7), (3, 14))),
    "medium27": (18, 27, ((1, 0), (6, 11), (9, 22))),
    "deep23": (26, 23, ((1, 0), (10, 9), (17, 18))),
}
_DEMO_PROFILES = ("minimum", "compact", "wide", "tall", "square24", "stress30")
_QUERY_PROFILES = ("medium19", "medium27", "deep23", "stress30")
_CONTROL_SHAPE = {1: 0, 2: 1, 3: 2}  # each is a non-square 2x3 or 3x2 crop
_PALETTES = ("default", "warm", "cool", "varied")


def _mode(settings: Any) -> str:
    if (
        type(settings) is not dict
        or set(settings) != {"gallery_mode"}
        or type(settings["gallery_mode"]) is not str
        or settings["gallery_mode"] not in MODES
    ):
        raise ValueError("settings must contain exactly gallery_mode=direct or width_relay")
    return settings["gallery_mode"]


def _integer(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _rng(seed: int, split: str, index: int, label: str) -> random.Random:
    raw = f"{TASK_ID}:{VERSION}:{seed}:{split}:{index}:{label}".encode("utf-8")
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest()[:16], "big"))


def program(settings: dict[str, Any]) -> str:
    return PROGRAM_PATHS[_mode(settings)].read_text(encoding="utf-8")


def _parts(grid: list[list[int]]) -> tuple[dict[str, Any], list[list[list[int]]]]:
    facts = _BASE._analysis(deepcopy(grid))
    if facts["errors"]:
        raise ValueError("invalid gallery input: " + "; ".join(facts["errors"]))
    if len(facts["selectors"]) != 4 or len(facts["transforms"]) != 4:
        raise ValueError("parametric gallery inputs require exactly four instructions")
    parts = []
    for key, code in zip(facts["selectors"], facts["transforms"]):
        pattern = facts["key_to_frame"][key]["pattern"]
        parts.append(_BASE._apply_transform(pattern, code))
    return facts, parts


def analyze_input(grid: list[list[int]]) -> dict[str, Any]:
    facts, parts = _parts(grid)
    control = parts[0]
    frame = facts["key_to_frame"][facts["selectors"][0]]
    return {
        "relay_width": len(control[0]),
        "control_height": len(control),
        "raw_control_width": len(frame["pattern"][0]),
        "raw_control_height": len(frame["pattern"]),
        "control_key": facts["selectors"][0],
        "control_transform": facts["transforms"][0],
        "payload_count": 3,
        "input_shape": [len(grid), len(grid[0])],
    }


def solve_direct(grid: list[list[int]]) -> list[list[int]]:
    return _BASE.rule_mirror(deepcopy(grid))


def _solve_payload_index(grid: list[list[int]], payload_index: int, *, include_control: bool = True) -> list[list[int]]:
    if type(payload_index) is not int or not 0 <= payload_index <= 2:
        raise ValueError("payload_index must be an exact integer in 0..2")
    _, parts = _parts(grid)
    selected = parts[1:][payload_index]
    return _BASE._hstack_center([parts[0], selected] if include_control else [selected])


def solve_with_intermediate(grid: list[list[int]], intermediate: int) -> list[list[int]]:
    if type(intermediate) is not int or intermediate not in (2, 3):
        raise ValueError("relay intermediate must be exactly 2 or 3")
    # Width 2 selects payload index 1; width 3 selects payload index 2.
    return _solve_payload_index(grid, intermediate - 1)


def solve_width_relay(grid: list[list[int]]) -> list[list[int]]:
    return solve_with_intermediate(grid, analyze_input(grid)["relay_width"])


def solve_python(grid: list[list[int]], settings: dict[str, Any]) -> list[list[int]]:
    mode = _mode(settings)
    return solve_direct(grid) if mode == "direct" else solve_width_relay(grid)


def _copy_frame_block(
    source: list[list[int]], frame: dict[str, Any], target: list[list[int]], top: int, left: int
) -> None:
    source_key_row = frame["top"] - 1
    for r in range(source_key_row, frame["bottom"] + 1):
        for c in range(frame["left"], frame["right"] + 1):
            value = source[r][c]
            if value:
                target[top - 1 + (r - source_key_row)][left + (c - frame["left"])] = value


def _code_positions(width: int) -> tuple[int, int, int, int]:
    values = (1, width // 3, (2 * width) // 3, width - 2)
    if len(set(values)) != 4 or not all(0 <= value < width for value in values):
        raise AssertionError(f"profile width cannot host four code columns: {width}")
    return tuple(sorted(values))


def _input_for(seed: int, split: str, index: int) -> list[list[int]]:
    profiles = _DEMO_PROFILES if split == "demo" else _QUERY_PROFILES
    profile = profiles[index]
    height, width, placements = _PROFILES[profile]
    desired_width = 2 if index % 2 == 0 else 3
    rng = _rng(seed, split, index, "scene")
    # Force the controller to rotate in every scene: library 3 has a 2x3
    # controller (raw width 3) for desired width 2; libraries 1/2 have 3x2
    # controllers (raw width 2) for desired width 3.  This constructively
    # refutes the plausible shortcut that uses width before transformation.
    library = 3 if desired_width == 2 else 1 + rng.randrange(2)
    palette = _PALETTES[rng.randrange(len(_PALETTES))]
    # Even sample indices force the source generator's anti-shortcut key legend
    # (left-to-right keys 3,4,2), while the frame identities still vary.
    base_seed = rng.randrange(2**31)
    source = _BASE.generate(
        base_seed,
        2 * (index + (0 if split == "demo" else 16)),
        difficulty="hard",
        library=library,
        program=5,
        palette_kind=palette,
    )
    source_facts = _BASE._analysis(source)
    if source_facts["errors"]:
        raise AssertionError("selected generator emitted malformed source: " + "; ".join(source_facts["errors"]))
    target = [[0 for _ in range(width)] for _ in range(height)]
    for frame, (top, left) in zip(sorted(source_facts["frames"], key=lambda row: row["left"]), placements):
        _copy_frame_block(source, frame, target, top, left)

    relocated = _BASE._analysis(target)
    # The program has not been written yet; only use the visible library facts.
    if len(relocated["frames"]) != 3:
        raise AssertionError("frame relocation failed")
    key_for_shape = {frame["shape_index"]: frame["key"] for frame in relocated["frames"]}
    control_shape = _CONTROL_SHAPE[library]
    control_frame = next(frame for frame in relocated["frames"] if frame["shape_index"] == control_shape)
    raw_h = len(control_frame["pattern"])
    raw_w = len(control_frame["pattern"][0])
    if raw_h == desired_width and raw_w != desired_width:
        control_code = 6
    else:
        raise AssertionError((library, control_shape, raw_h, raw_w, desired_width))

    others = [shape for shape in range(3) if shape != control_shape]
    rng.shuffle(others)
    payload_shapes = [control_shape, others[0], others[1]]
    payload_codes = [5, 6, 7]
    rng.shuffle(payload_codes)
    instructions = [(control_shape, control_code), *zip(payload_shapes, payload_codes)]
    for column, (shape, code) in zip(_code_positions(width), instructions):
        target[-2][column] = key_for_shape[shape]
        target[-1][column] = code

    errors = _BASE.self_check(target)
    if errors:
        raise AssertionError("constructed parametric input is invalid: " + "; ".join(errors))
    facts = analyze_input(target)
    if facts["relay_width"] != desired_width or facts["control_height"] == desired_width:
        raise AssertionError(f"controller is not a non-square width-{desired_width} witness: {facts}")
    return target


def _fixed_position_parts(grid: list[list[int]]) -> list[list[list[int]]]:
    facts = _BASE._analysis(grid)
    if facts["errors"]:
        raise ValueError("invalid gallery input: " + "; ".join(facts["errors"]))
    left_to_right = sorted(facts["frames"], key=lambda frame: frame["left"])
    fixed = {2: 0, 3: 1, 4: 2}
    result = []
    for selector, code in zip(facts["selectors"], facts["transforms"]):
        if selector not in fixed:
            raise ValueError("fixed-position rival only supports keys 2,3,4")
        result.append(_BASE._apply_transform(left_to_right[fixed[selector]]["pattern"], code))
    return result


def _fixed_position_direct(grid: list[list[int]]) -> list[list[int]]:
    return _BASE._hstack_center(_fixed_position_parts(grid))


def _fixed_position_relay(grid: list[list[int]]) -> list[list[int]]:
    parts = _fixed_position_parts(grid)
    return _BASE._hstack_center([parts[0], parts[1:][len(parts[0][0]) - 1]])


def _ignore_transforms(grid: list[list[int]]) -> list[list[int]]:
    facts, _ = _parts(grid)
    return _BASE._hstack_center([deepcopy(facts["key_to_frame"][key]["pattern"]) for key in facts["selectors"]])


def _rivals(mode: str) -> dict[str, Callable[[list[list[int]]], list[list[int]]]]:
    if mode == "direct":
        return {
            "other_setting_width_relay": solve_width_relay,
            "fixed_key_positions": _fixed_position_direct,
            "ignore_transforms": _ignore_transforms,
            "reverse_gallery": lambda grid: _BASE._hstack_center(list(reversed(_parts(grid)[1]))),
        }
    return {
        "other_setting_direct": solve_direct,
        "height_instead_of_width": lambda grid: solve_with_intermediate(
            grid, analyze_input(grid)["control_height"]
        ),
        "raw_width_before_transform": lambda grid: solve_with_intermediate(
            grid, analyze_input(grid)["raw_control_width"]
        ),
        "always_width_2": lambda grid: solve_with_intermediate(grid, 2),
        "always_width_3": lambda grid: solve_with_intermediate(grid, 3),
        "first_payload": lambda grid: _solve_payload_index(grid, 0),
        "omit_control": lambda grid: _solve_payload_index(
            grid, analyze_input(grid)["relay_width"] - 1, include_control=False
        ),
        "fixed_key_positions": _fixed_position_relay,
    }


def teaching_check(episode: dict[str, Any], settings: dict[str, Any]) -> dict[str, Any]:
    mode = _mode(settings)
    if type(episode) is not dict or type(episode.get("train")) is not list or type(episode.get("test")) is not list:
        raise ValueError("episode must contain train and test lists")
    if not episode["train"] or not episode["test"]:
        raise ValueError("teaching check requires demonstrations and queries")
    for pair in episode["train"] + episode["test"]:
        if pair["output"] != solve_python(pair["input"], settings):
            raise ValueError("episode label disagrees with selected Python rule")
    eliminated: dict[str, list[int]] = {}
    survivors: list[str] = []
    rivals = _rivals(mode)
    for name, solver in rivals.items():
        differences = [
            index
            for index, pair in enumerate(episode["train"])
            if solver(deepcopy(pair["input"])) != pair["output"]
        ]
        if differences:
            eliminated[name] = differences
        else:
            survivors.append(name)
    harmful = [
        name
        for name in survivors
        if any(_rivals(mode)[name](deepcopy(pair["input"])) != pair["output"] for pair in episode["test"])
    ]
    return {
        "fit_uses": "demonstrations_only",
        "rivals_tested": len(rivals),
        "eliminated": eliminated,
        "survivors": survivors,
        "harmful_survivors": harmful,
        "limits": "Finite named deterministic rivals only; not a proof of unique induction.",
    }


def generate(
    seed: int,
    settings: dict[str, Any],
    demos: int = 3,
    queries: int = 4,
) -> dict[str, Any]:
    _integer("seed", seed, 0, 2**63 - 1)
    mode = _mode(settings)
    _integer("demos", demos, 2, 6)
    _integer("queries", queries, 1, 4)
    normalized = {"gallery_mode": mode}
    train_inputs = [_input_for(seed, "demo", index) for index in range(demos)]
    test_inputs = [_input_for(seed, "query", index) for index in range(queries)]
    serialized = [json.dumps(grid, separators=(",", ":")) for grid in train_inputs + test_inputs]
    if len(serialized) != len(set(serialized)):
        raise AssertionError("constructed episode contains duplicate inputs")
    episode = {
        "train": [
            {"input": grid, "output": solve_python(grid, normalized)} for grid in train_inputs
        ],
        "test": [
            {"input": grid, "output": solve_python(grid, normalized)} for grid in test_inputs
        ],
        "program_solution": program(normalized),
        "settings": normalized,
        "seed": seed,
        "source_generator_sha256": _BASE_SHA256,
    }
    report = teaching_check(episode, normalized)
    if report["harmful_survivors"]:
        raise AssertionError(f"visible demonstrations leave harmful rivals: {report}")
    return episode


def public_view(episode: dict[str, Any], query_index: int = 0) -> dict[str, Any]:
    if type(query_index) is not int or not 0 <= query_index < len(episode.get("test", [])):
        raise ValueError("query_index is outside the stored query range")
    visible = {"train": episode["train"], "test": [episode["test"][query_index]]}
    return json.loads(public_challenge_bytes(visible))
