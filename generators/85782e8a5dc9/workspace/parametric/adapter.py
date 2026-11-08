"""Native adapter for applying the inferred framed transform once or twice."""
from __future__ import annotations

from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random
from typing import Any

from reviewer_support import canonical_path, find_root


TASK_ID = "85782e8a5dc9"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
APPLICATIONS = ("once", "twice")
_TRANSFORMS = (
    "identity",
    "rot90",
    "rot180",
    "transpose",
    "flip_lr",
    "flip_ud",
    "anti_transpose",
)
_ALL_D4 = _TRANSFORMS + ("rot270",)
_INVERSE = {
    "identity": "identity",
    "rot90": "rot270",
    "rot180": "rot180",
    "rot270": "rot90",
    "transpose": "transpose",
    "flip_lr": "flip_lr",
    "flip_ud": "flip_ud",
    "anti_transpose": "anti_transpose",
}
HYPOTHESES = APPLICATIONS + (
    "zero",
    "three",
    "inverse",
    "fixed_rot90_once",
    "fixed_rot180_once",
    "fixed_rot90_twice",
    "fixed_rot180_twice",
    "copy_b",
    "occupancy_once",
    "occupancy_twice",
)
_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)

# The first two scenes alone identify either setting against every declared
# finite rival.  Later scenes broaden transform, size, and boundary coverage.
_DEMO_SPECS = (
    ("color_key_rot90", 5, 5, "rot90"),
    ("generic", 4, 4, "flip_lr"),
    ("generic", 6, 6, "rot180"),
    ("generic", 5, 5, "transpose"),
    ("generic", 7, 7, "flip_ud"),
    ("generic", 6, 6, "anti_transpose"),
)
_QUERY_SPECS = (
    ("generic", 4, 4, "rot90"),
    ("generic", 5, 5, "transpose"),
    ("generic", 7, 7, "anti_transpose"),
    ("stress30", 28, 7, "flip_lr"),
)


def _integer(value: object, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _applications(value: object) -> str:
    if type(value) is not str or value not in APPLICATIONS:
        raise ValueError("applications must be once or twice")
    return value


def _settings(settings: object) -> str:
    if type(settings) is not dict or set(settings) != {"applications"}:
        raise ValueError("declare exactly applications=once|twice")
    return _applications(settings["applications"])


def grid(value: object) -> list[list[int]]:
    if (
        type(value) is not list
        or not 3 <= len(value) <= 30
        or type(value[0]) is not list
        or not 3 <= len(value[0]) <= 30
        or any(
            type(row) is not list
            or len(row) != len(value[0])
            or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
            for row in value
        )
    ):
        raise ValueError("grid must be rectangular 3..30 with exact integer colors 0..9")
    return value


@lru_cache(maxsize=1)
def canonical_program() -> str:
    programs = {
        row["program_solution"]
        for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines()
        if (row := json.loads(line))["task_id"] == TASK_ID
    }
    if len(programs) != 1:
        raise ValueError("require one exact selected canonical program")
    return programs.pop()


def program(settings: dict[str, object]) -> str:
    applications = _settings(settings)
    if applications == "once":
        return canonical_program()
    return (HERE / "double_transfer.rkt").read_text(encoding="utf-8")


def _map_pattern(value: list[list[int]], name: str) -> list[list[int]]:
    if type(value) is not list or not value or type(value[0]) is not list or not value[0]:
        raise ValueError("pattern must be a non-empty rectangular grid")
    height = len(value)
    width = len(value[0])
    if any(type(row) is not list or len(row) != width for row in value):
        raise ValueError("pattern must be rectangular")
    if name in ("rot90", "rot270", "transpose", "anti_transpose"):
        output = [[0] * height for _ in range(width)]
    else:
        output = [[0] * width for _ in range(height)]
    for row in range(height):
        for col in range(width):
            if name == "identity":
                target = row, col
            elif name == "rot90":
                target = col, height - 1 - row
            elif name == "rot180":
                target = height - 1 - row, width - 1 - col
            elif name == "rot270":
                target = width - 1 - col, row
            elif name == "transpose":
                target = col, row
            elif name == "flip_lr":
                target = row, width - 1 - col
            elif name == "flip_ud":
                target = height - 1 - row, col
            elif name == "anti_transpose":
                target = width - 1 - col, height - 1 - row
            else:
                raise ValueError(f"unknown transform: {name}")
            output[target[0]][target[1]] = value[row][col]
    return output


def _apply(value: list[list[int]], name: str, count: int) -> list[list[int]]:
    output = [row[:] for row in value]
    for _ in range(count):
        output = _map_pattern(output, name)
    return output


def _split_panels(value: list[list[int]]) -> list[list[list[int]]]:
    height = len(value)
    width = len(value[0])
    panels: list[list[list[int]]] = []
    col = 0
    while col < width:
        if all(value[row][col] == 0 for row in range(height)):
            col += 1
            continue
        stop = col
        while stop < width and not all(value[row][stop] == 0 for row in range(height)):
            stop += 1
        panels.append([row[col:stop] for row in value])
        col = stop + 1
    return panels


def _inside_frame(panel: list[list[int]]) -> list[list[int]]:
    height = len(panel)
    width = len(panel[0]) if panel else 0
    if height < 3 or width < 3 or any(len(row) != width for row in panel):
        raise ValueError("each panel must be a rectangular frame of size at least 3x3")
    if (
        any(cell != 5 for cell in panel[0])
        or any(cell != 5 for cell in panel[-1])
        or any(row[0] != 5 or row[-1] != 5 for row in panel)
    ):
        raise ValueError("each panel must have a complete color-5 frame")
    return [row[1:-1] for row in panel[1:-1]]


def observe(value: list[list[int]]) -> dict[str, Any]:
    grid(value)
    panels = _split_panels(value)
    if len(panels) != 3:
        raise ValueError("scene must contain exactly three framed panels")
    a, b, c = (_inside_frame(panel) for panel in panels)
    matches = [name for name in _TRANSFORMS if _map_pattern(a, name) == b]
    if len(matches) != 1 or matches[0] == "identity":
        raise ValueError("A:B must identify exactly one supported non-identity transform")
    return {
        "a": a,
        "b": b,
        "c": c,
        "transform": matches[0],
        "panel_shapes": tuple((len(panel), len(panel[0])) for panel in panels),
    }


def transform(value: list[list[int]], applications: str) -> list[list[int]]:
    applications = _applications(applications)
    observed = observe(value)
    return _apply(observed["c"], observed["transform"], 1 if applications == "once" else 2)


def _mask(value: list[list[int]]) -> list[list[int]]:
    return [[int(cell != 0) for cell in row] for row in value]


def _occupancy_transform(observed: dict[str, Any]) -> str:
    a = _mask(observed["a"])
    b = _mask(observed["b"])
    return next((name for name in _TRANSFORMS if _map_pattern(a, name) == b), "identity")


def predict(value: list[list[int]], hypothesis: str) -> list[list[int]]:
    observed = observe(value)
    c = observed["c"]
    inferred = observed["transform"]
    if hypothesis in APPLICATIONS:
        return _apply(c, inferred, 1 if hypothesis == "once" else 2)
    if hypothesis == "zero":
        return [row[:] for row in c]
    if hypothesis == "three":
        return _apply(c, inferred, 3)
    if hypothesis == "inverse":
        return _map_pattern(c, _INVERSE[inferred])
    if hypothesis == "fixed_rot90_once":
        return _apply(c, "rot90", 1)
    if hypothesis == "fixed_rot180_once":
        return _apply(c, "rot180", 1)
    if hypothesis == "fixed_rot90_twice":
        return _apply(c, "rot90", 2)
    if hypothesis == "fixed_rot180_twice":
        return _apply(c, "rot180", 2)
    if hypothesis == "copy_b":
        return [row[:] for row in observed["b"]]
    if hypothesis == "occupancy_once":
        return _apply(c, _occupancy_transform(observed), 1)
    if hypothesis == "occupancy_twice":
        return _apply(c, _occupancy_transform(observed), 2)
    raise ValueError(f"unknown declared hypothesis: {hypothesis}")


def _rng(seed: int, stream: str, index: int) -> random.Random:
    digest = hashlib.sha256(f"{TASK_ID}-parametric-v1:{seed}:{stream}:{index}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _key(value: list[list[int]]) -> str:
    return hashlib.sha256(json.dumps(value, separators=(",", ":")).encode()).hexdigest()


def _random_pattern(
    rng: random.Random,
    height: int,
    width: int,
    *,
    dense: bool,
    require_full_d4: bool,
) -> list[list[int]]:
    probability = 0.48 if dense else 0.34
    minimum = 64 if dense else max(5, min(12, height * width // 3))
    names = _ALL_D4 if require_full_d4 else _TRANSFORMS
    for _attempt in range(128):
        value = [
            [rng.choice(_COLORS) if rng.random() < probability else 0 for _ in range(width)]
            for _ in range(height)
        ]
        if sum(cell != 0 for row in value for cell in row) < minimum:
            continue
        signatures = {_key(_map_pattern(value, name)) for name in names}
        if len(signatures) == len(names):
            return value
    raise ValueError("could not construct a transform-asymmetric pattern")


def _color_key_rot90(rng: random.Random) -> list[list[int]]:
    value = [[0] * 5 for _ in range(5)]
    outer = ((0, 1), (1, 4), (4, 3), (3, 0))
    inner = ((1, 1), (1, 3), (3, 3), (3, 1))
    colors = list(_COLORS)
    rng.shuffle(colors)
    for point, color in zip(outer + inner, colors):
        value[point[0]][point[1]] = color
    if len({_key(_map_pattern(value, name)) for name in _ALL_D4}) != len(_ALL_D4):
        raise AssertionError("color-keyed teaching pattern unexpectedly has a colored symmetry")
    if _mask(_map_pattern(value, "rot90")) != _mask(value):
        raise AssertionError("color-keyed teaching support must hide the quarter turn from occupancy")
    return value


def _render(a: list[list[int]], b: list[list[int]], c: list[list[int]], *, stress30: bool) -> list[list[int]]:
    if not (len(a) == len(b) == len(c) and len(a[0]) == len(b[0]) == len(c[0])):
        raise ValueError("all three interiors must have matching dimensions")
    interior_h = len(a)
    interior_w = len(a[0])
    panel_h = interior_h + 2
    panel_w = interior_w + 2
    width = 3 * panel_w + 2
    target_width = 30 if stress30 else width
    if panel_h > 30 or target_width > 30 or width > target_width:
        raise ValueError("render exceeds the 30x30 authoring boundary")
    value = [[0] * target_width for _ in range(panel_h)]
    for index, pattern in enumerate((a, b, c)):
        start = index * (panel_w + 1)
        stop = start + panel_w - 1
        for col in range(start, stop + 1):
            value[0][col] = value[-1][col] = 5
        for row in range(panel_h):
            value[row][start] = value[row][stop] = 5
        for row in range(interior_h):
            value[row + 1][start + 1 : stop] = pattern[row][:]
    return value


def _scene(seed: int, stream: str, index: int, spec: tuple[str, int, int, str]) -> list[list[int]]:
    profile, height, width, name = spec
    rng = _rng(seed, stream, index)
    if profile == "color_key_rot90":
        a = _color_key_rot90(rng)
    else:
        a = _random_pattern(
            rng,
            height,
            width,
            dense=profile == "stress30",
            require_full_d4=height == width,
        )
    b = _map_pattern(a, name)
    c = _random_pattern(
        rng,
        height,
        width,
        dense=profile == "stress30",
        require_full_d4=height == width,
    )
    value = _render(a, b, c, stress30=profile == "stress30")
    observed = observe(value)
    if observed["transform"] != name:
        raise AssertionError("constructed scene did not retain its intended transform")
    if transform(value, "once") == transform(value, "twice"):
        raise AssertionError("scene must distinguish one application from two")
    return value


def generate(seed: int, settings: dict[str, object], demos: int, queries: int) -> dict[str, object]:
    _integer(seed, "seed", 0, 2**63 - 1)
    applications = _settings(settings)
    _integer(demos, "demos", 2, 6)
    _integer(queries, "queries", 1, 4)
    demo_inputs = [_scene(seed, "demo", index, spec) for index, spec in enumerate(_DEMO_SPECS[:demos])]
    query_inputs = [_scene(seed, "query", index, spec) for index, spec in enumerate(_QUERY_SPECS[:queries])]
    all_inputs = demo_inputs + query_inputs
    if len({_key(value) for value in all_inputs}) != len(all_inputs):
        raise ValueError("distinct input budget exhausted; no partial episode")
    train = [{"input": value, "output": transform(value, applications)} for value in demo_inputs]
    test = [{"input": value, "output": transform(value, applications)} for value in query_inputs]
    return {"train": train, "test": test, "program_solution": program(settings)}


def certificate(train: list[dict[str, object]], query_inputs: list[list[list[int]]]) -> dict[str, object]:
    if type(train) is not list or not 2 <= len(train) <= 6:
        raise ValueError("two through six demonstrations are required")
    if type(query_inputs) is not list or not 1 <= len(query_inputs) <= 4:
        raise ValueError("one through four query inputs are required")
    for pair in train:
        if type(pair) is not dict or set(pair) < {"input", "output"}:
            raise ValueError("each demonstration needs input and output")
        grid(pair["input"])
        if type(pair["output"]) is not list:
            raise ValueError("demonstration output must be a grid")
    for value in query_inputs:
        grid(value)
        observe(value)
    survivors = [
        hypothesis
        for hypothesis in HYPOTHESES
        if all(predict(pair["input"], hypothesis) == pair["output"] for pair in train)
    ]
    if len(survivors) != 1 or survivors[0] not in APPLICATIONS:
        raise ValueError("demonstrations do not identify one application count against declared rivals")
    witness = train[0]["input"]
    observed = observe(witness)
    count = 1 if survivors[0] == "once" else 2
    correct = _apply(observed["c"], observed["transform"], count)
    wrong = _apply(observed["c"], "rot180", count)
    predictions = [predict(value, survivors[0]) for value in query_inputs]
    return {
        "declared_hypotheses": list(HYPOTHESES),
        "survivors": survivors,
        "demos": len(train),
        "queries": len(query_inputs),
        "predicted_query_sha256": [_key(value) for value in predictions],
        "causal_witness": {
            "input_sha256": _key(witness),
            "step_a": "infer the unique colored transform mapping framed interior A to B",
            "intermediate": "transform",
            "inferred_transform": observed["transform"],
            "step_b": f"apply the inferred transform to C {count} time(s)",
            "wrong_intermediate": "rot180",
            "correct_output_sha256": _key(correct),
            "wrong_intermediate_output_sha256": _key(wrong),
        },
        "scope": "Finite declared rivals only; query answers were not provided to the certificate.",
    }
