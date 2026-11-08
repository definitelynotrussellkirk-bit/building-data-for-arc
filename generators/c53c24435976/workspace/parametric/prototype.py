"""Source-bound command-chain family for ARC task c53c24435976.

The canonical setting applies the command at input (0,0) to the tight crop.
The nearby chained setting first performs that exact canonical step, then reads
stage one's top-left corner as a second command and transforms the intermediate
again.  All retained labels are independently re-executed through protected
Racket by native qualification; the Python mirror exists for construction,
certificate checks, and adversarial probes only.
"""
from __future__ import annotations

import copy
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import random
from typing import Callable

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
TASK_ID = "c53c24435976"
PARAMETERS = {"command_chain": ["outer_only", "outer_then_corner"]}
DEFAULT = {"command_chain": "outer_only"}
CHAINED = {"command_chain": "outer_then_corner"}
SETTINGS = (DEFAULT, CHAINED)
DEMO_LIMITS = (2, 6)
QUERY_COUNT = 4

_CANONICAL = (HERE / "canonical.rkt").read_text(encoding="utf-8")
_CHAINED = (HERE / "chained.rkt").read_text(encoding="utf-8")

_DEMO_PROFILES = (
    ((8, 9), (3, 4)),
    ((9, 8), (4, 3)),
    ((12, 13), (5, 7)),
    ((13, 12), (7, 5)),
    ((18, 20), (12, 14)),
    ((20, 18), (14, 12)),
)
_QUERY_PROFILES = (
    ((9, 12), (4, 7)),
    ((14, 15), (8, 9)),
    ((24, 26), (20, 22)),
    ((30, 30), (29, 29)),
)
_OUTER_PAIRS = ((1, 3), (2, 4), (3, 2), (4, 3))
_INNER_PAIRS = ((2, 4), (3, 1), (4, 1), (1, 2))


def _integer(value: object, lo: int, hi: int, name: str) -> int:
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError(f"{name} must be an exact integer in {lo}..{hi}")
    return value


def _settings(settings: object) -> dict[str, str]:
    if type(settings) is not dict or set(settings) != {"command_chain"}:
        raise ValueError("settings must name exactly command_chain")
    value = settings["command_chain"]
    if type(value) is not str or value not in PARAMETERS["command_chain"]:
        raise ValueError("command_chain must be 'outer_only' or 'outer_then_corner'")
    return {"command_chain": value}


def _grid(value: object) -> list[list[int]]:
    if (type(value) is not list or not 1 <= len(value) <= 30
            or type(value[0]) is not list or not 1 <= len(value[0]) <= 30):
        raise ValueError("grid must be rectangular with 1..30 rows and columns")
    width = len(value[0])
    if any(type(row) is not list or len(row) != width
           or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
           for row in value):
        raise ValueError("grid must contain exact integer ARC colors 0..9")
    return value


def program(settings: object) -> str:
    return _CANONICAL if _settings(settings) == DEFAULT else _CHAINED


def digest(value: object) -> str:
    data = json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _rng(seed: int, domain: str, index: int = 0, attempt: int = 0) -> random.Random:
    token = [TASK_ID, "command-chain-v1", seed, domain, index, attempt]
    return random.Random(int(digest(token), 16))


def _crop(grid: list[list[int]]) -> list[list[int]]:
    _grid(grid)
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
             if value != 0 and (r, c) != (0, 0)]
    if not cells:
        raise ValueError("input needs nonzero cropped content besides the outer command")
    r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
    c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
    return [row[c0:c1 + 1] for row in grid[r0:r1 + 1]]


def _rot_cw(grid: list[list[int]]) -> list[list[int]]:
    h, w = len(grid), len(grid[0])
    return [[grid[h - 1 - r][c] for r in range(h)] for c in range(w)]


def _rot_180(grid: list[list[int]]) -> list[list[int]]:
    return [list(reversed(row)) for row in reversed(grid)]


def _flip_lr(grid: list[list[int]]) -> list[list[int]]:
    return [list(reversed(row)) for row in grid]


def _flip_ud(grid: list[list[int]]) -> list[list[int]]:
    return [row[:] for row in reversed(grid)]


def apply_code(grid: list[list[int]], code: int) -> list[list[int]]:
    _grid(grid)
    if code == 1:
        return _rot_cw(grid)
    if code == 2:
        return _rot_180(grid)
    if code == 3:
        return _flip_lr(grid)
    return _flip_ud(grid)


def stage_one(grid: list[list[int]]) -> list[list[int]]:
    _grid(grid)
    command = grid[0][0]
    if command not in (1, 2, 3, 4):
        raise ValueError("outer command must be 1..4")
    return apply_code(_crop(grid), command)


def selected_inner_command(intermediate: list[list[int]]) -> int:
    _grid(intermediate)
    command = intermediate[0][0]
    if command not in (1, 2, 3, 4):
        raise ValueError("transformed top-left corner must be an inner command 1..4")
    return command


def transform(grid: list[list[int]], settings: object) -> list[list[int]]:
    chosen = _settings(settings)
    intermediate = stage_one(grid)
    if chosen == DEFAULT:
        return intermediate
    return apply_code(intermediate, selected_inner_command(intermediate))


def skip_outer_transform(grid: list[list[int]]) -> list[list[int]]:
    """Counterfactual: skip A and read the untransformed crop's top-left."""
    crop = _crop(grid)
    return apply_code(crop, selected_inner_command(crop))


def wrong_order_transform(grid: list[list[int]]) -> list[list[int]]:
    """Counterfactual: apply the source-corner command before the outer command."""
    crop = _crop(grid)
    first = apply_code(crop, selected_inner_command(crop))
    return apply_code(first, grid[0][0])


def _corner_command(crop: list[list[int]], name: str) -> int:
    coords = {"tl": (0, 0), "tr": (0, -1), "bl": (-1, 0), "br": (-1, -1)}
    command = crop[coords[name][0]][coords[name][1]]
    if command not in (1, 2, 3, 4):
        raise ValueError("all crop corners must contain commands 1..4")
    return command


def _statistical_commands(intermediate: list[list[int]]) -> dict[str, int]:
    """Plausible color-frequency/rank selectors that must not fit the lesson."""
    _grid(intermediate)
    commands = [value for row in intermediate for value in row if 1 <= value <= 4]
    if len(commands) < 2:
        raise ValueError("intermediate needs at least two command-colored cells")
    counts = Counter(commands)
    maximum = max(counts.values())
    minimum = min(counts.values())
    modes = [value for value, count in counts.items() if count == maximum]
    rares = [value for value, count in counts.items() if count == minimum]
    center = intermediate[len(intermediate) // 2][len(intermediate[0]) // 2]
    return {
        "stat_mode_min": min(modes),
        "stat_mode_max": max(modes),
        "stat_rare_min": min(rares),
        "stat_rare_max": max(rares),
        "stat_last_command": commands[-1],
        "stat_second_command": commands[1],
        "stat_center_or4": center if 1 <= center <= 4 else 4,
        "stat_count_mod4": (len(commands) - 1) % 4 + 1,
    }


def shortcut_outputs(grid: list[list[int]], settings: object) -> dict[str, list[list[int]]]:
    """Finite, task-relevant shortcut attacks used to construct/check lessons."""
    chosen = _settings(settings)
    crop = _crop(grid)
    intermediate = stage_one(grid)
    if chosen == DEFAULT:
        outputs = {"ignore_outer_identity": copy.deepcopy(crop),
                   "shape_top_left_command": apply_code(crop, _corner_command(crop, "tl")),
                   "chained_variant": transform(grid, CHAINED)}
        outputs.update({f"fixed_outer_{code}": apply_code(crop, code) for code in (1, 2, 3, 4)})
        outputs.update({name: apply_code(crop, command)
                        for name, command in _statistical_commands(intermediate).items()})
        return outputs
    outputs = {
        "outer_only": intermediate,
        "outer_twice": apply_code(intermediate, grid[0][0]),
        "skip_outer": skip_outer_transform(grid),
        "wrong_order": wrong_order_transform(grid),
    }
    outputs.update({f"fixed_inner_{code}": apply_code(intermediate, code)
                    for code in (1, 2, 3, 4)})
    outputs.update({f"inner_from_source_{corner}":
                    apply_code(intermediate, _corner_command(crop, corner))
                    for corner in ("tl", "tr", "bl", "br")})
    outputs.update({name: apply_code(intermediate, command)
                    for name, command in _statistical_commands(intermediate).items()})
    return outputs


def _selected_source_corner(outer_command: int) -> str:
    return {1: "bl", 2: "br", 3: "tr", 4: "bl"}[outer_command]


def _corner_values(outer_command: int, inner_command: int,
                   rng: random.Random) -> dict[str, int]:
    names = ["tl", "tr", "bl", "br"]
    values = [1, 2, 3, 4]
    rng.shuffle(values)
    selected = _selected_source_corner(outer_command)
    selected_index = names.index(selected)
    inner_index = values.index(inner_command)
    values[selected_index], values[inner_index] = values[inner_index], values[selected_index]
    return dict(zip(names, values))


def _object_matrix(seed: int, domain: str, index: int, attempt: int,
                   size: tuple[int, int], outer_command: int,
                   inner_command: int, *, object_key: str | None = None) -> list[list[int]]:
    h, w = size
    if h < 3 or w < 3:
        raise ValueError("object matrix must be at least 3x3")
    key = object_key or domain
    rng = _rng(seed, key, index, attempt)
    corners = _corner_values(outer_command, inner_command, rng)
    grid = [[0] * w for _ in range(h)]
    grid[0][0], grid[0][-1] = corners["tl"], corners["tr"]
    grid[-1][0], grid[-1][-1] = corners["bl"], corners["br"]

    # Dense enough for realistic stress, but with holes and code-colored decoys.
    density = 0.58 if h * w <= 24 else 0.39 if h * w >= 300 else 0.46
    palette = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    for r in range(h):
        for c in range(w):
            if (r, c) in ((0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)):
                continue
            # A deterministic skewed backbone prevents thin/symmetric accidents.
            backbone = (c == (2 * r + 1) % w or r == (3 * c + 2) % h
                        or (r == h // 2 and c % 3 != 1))
            if backbone or rng.random() < density:
                grid[r][c] = palette[rng.randrange(len(palette))]

    # Explicit asymmetric landmarks; these also challenge first/last-cell shortcuts.
    landmarks = [(0, min(2, w - 2), 8), (min(2, h - 2), 0, 7),
                 (h - 1, max(1, w - 3), 6), (max(1, h - 3), w - 1, 9)]
    for r, c, value in landmarks:
        if (r, c) not in ((0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)):
            grid[r][c] = value
    return grid


def _embed(matrix: list[list[int]], canvas: tuple[int, int], position: tuple[int, int],
           outer_command: int) -> list[list[int]]:
    _grid(matrix)
    h, w = canvas
    top, left = position
    mh, mw = len(matrix), len(matrix[0])
    if not (1 <= top <= h - mh and 1 <= left <= w - mw):
        raise ValueError("object placement must fit below/right of the outer command")
    grid = [[0] * w for _ in range(h)]
    grid[0][0] = outer_command
    for r, row in enumerate(matrix):
        for c, value in enumerate(row):
            grid[top + r][left + c] = value
    return grid


def _commands(seed: int, domain: str, index: int) -> tuple[int, int]:
    if domain == "demo":
        choice = seed % len(_OUTER_PAIRS)
        outer_prefix = _OUTER_PAIRS[choice]
        inner_prefix = _INNER_PAIRS[choice]
        remaining_outer = [v for v in (1, 2, 3, 4) if v not in outer_prefix]
        remaining_inner = [v for v in (1, 2, 3, 4) if v not in inner_prefix]
        outer = (*outer_prefix, *remaining_outer, outer_prefix[0], outer_prefix[1])[index]
        inner = (*inner_prefix, *remaining_inner, inner_prefix[1], inner_prefix[0])[index]
    else:
        shift = seed % 4
        outers = (1, 3, 2, 4)
        inners = (4, 1, 3, 2)
        outer = outers[(index + shift) % 4]
        inner = inners[(index + 2 * shift) % 4]
        if inner == outer:
            inner = (inner % 4) + 1
    return outer, inner


def _position(seed: int, domain: str, index: int, attempt: int,
              canvas: tuple[int, int], size: tuple[int, int]) -> tuple[int, int]:
    h, w = canvas
    mh, mw = size
    if domain == "query" and index == 3:
        return 1, 1
    rng = _rng(seed, domain + "-position", index, attempt)
    choices = [(1, 1), (1, w - mw), (h - mh, 1), (h - mh, w - mw)]
    if index % 2:
        choices.append((rng.randint(1, h - mh), rng.randint(1, w - mw)))
    return choices[(seed + index + attempt) % len(choices)]


def _scene(seed: int, domain: str, index: int, *, attempt: int = 0,
           outer_command: int | None = None, inner_command: int | None = None,
           canvas: tuple[int, int] | None = None, size: tuple[int, int] | None = None,
           position: tuple[int, int] | None = None,
           object_key: str | None = None) -> list[list[int]]:
    profiles = _DEMO_PROFILES if domain == "demo" else _QUERY_PROFILES
    default_canvas, default_size = profiles[index]
    canvas = canvas or default_canvas
    size = size or default_size
    default_outer, default_inner = _commands(seed, domain, index)
    outer_command = default_outer if outer_command is None else outer_command
    inner_command = default_inner if inner_command is None else inner_command
    if outer_command not in (1, 2, 3, 4) or inner_command not in (1, 2, 3, 4):
        raise ValueError("outer and inner commands must be 1..4")
    matrix = _object_matrix(seed, domain, index, attempt, size, outer_command,
                            inner_command, object_key=object_key)
    position = position or _position(seed, domain, index, attempt, canvas, size)
    grid = _embed(matrix, canvas, position, outer_command)
    intermediate = stage_one(grid)
    transforms = [apply_code(intermediate, code) for code in (1, 2, 3, 4)]
    if len({digest(value) for value in transforms}) != 4:
        raise ValueError("generated intermediate does not distinguish all commands")
    chained = transform(grid, CHAINED)
    if (chained == intermediate or chained == skip_outer_transform(grid)
            or chained == wrong_order_transform(grid)):
        raise ValueError("generated scene collapses a required sequential distinction")
    return grid


def _candidate(seed: int, domain: str, index: int, start_attempt: int = 0) -> list[list[int]]:
    for attempt in range(start_attempt, start_attempt + 128):
        try:
            return _scene(seed, domain, index, attempt=attempt)
        except ValueError:
            continue
    raise RuntimeError(f"unable to construct valid {domain} scene {index}")


def _covers_shortcuts(grids: list[list[list[int]]], settings: dict[str, str]) -> bool:
    chosen = [transform(grid, settings) for grid in grids]
    names = set(shortcut_outputs(grids[0], settings))
    if any(set(shortcut_outputs(grid, settings)) != names for grid in grids[1:]):
        raise RuntimeError("shortcut set changed between scenes")
    return all(any(shortcut_outputs(grid, settings)[name] != output
                   for grid, output in zip(grids, chosen)) for name in names)


def _demo_schedule(seed: int) -> list[list[list[int]]]:
    first = [_candidate(seed, "demo", 0, offset) for offset in range(0, 32)]
    second = [_candidate(seed, "demo", 1, offset) for offset in range(0, 32)]
    selected: tuple[list[list[int]], list[list[int]]] | None = None
    for left in first:
        for right in second:
            pair = [left, right]
            if all(_covers_shortcuts(pair, setting) for setting in SETTINGS):
                selected = left, right
                break
        if selected is not None:
            break
    if selected is None:
        raise RuntimeError("could not construct a two-demo shortcut-separating lesson")
    return [*selected, *[_candidate(seed, "demo", index) for index in range(2, 6)]]


def certify(episode: dict, execute: Callable[[str, list[list[int]]], list[list[int]]] | None = None) -> dict:
    if type(episode) is not dict:
        raise ValueError("episode must be an object")
    chosen = _settings(episode.get("settings"))
    if episode.get("program_solution") != program(chosen):
        raise ValueError("program does not match fixed episode settings")
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or type(test) is not list:
        raise ValueError("episode must contain train/test lists")
    _integer(len(train), DEMO_LIMITS[0], DEMO_LIMITS[1], "demos")
    if len(test) != QUERY_COUNT:
        raise ValueError("queries must contain exactly four pairs")
    pairs = train + test
    inputs = []
    for pair in pairs:
        if type(pair) is not dict or not {"input", "output"} <= set(pair):
            raise ValueError("each pair needs input and output")
        _grid(pair["input"])
        _grid(pair["output"])
        inputs.append(digest(pair["input"]))
    if len(inputs) != len(set(inputs)):
        raise ValueError("all demonstration and query inputs must be distinct")

    apply = execute or (lambda source, grid: transform(
        grid, next(setting for setting in SETTINGS if program(setting) == source)))
    demo_refutations = []
    survivors = []
    for setting in SETTINGS:
        predictions = [apply(program(setting), pair["input"]) for pair in train]
        disagreements = [index for index, (prediction, pair) in enumerate(zip(predictions, train))
                         if prediction != pair["output"]]
        demo_refutations.append({"settings": setting, "disagreeing_demo_indices": disagreements})
        if not disagreements:
            survivors.append(setting)
    if survivors != [chosen]:
        raise ValueError(f"demonstrations do not identify selected command-chain setting: {survivors}")

    shortcut_names = set(shortcut_outputs(train[0]["input"], chosen))
    shortcut_refutations = {}
    for name in sorted(shortcut_names):
        disagreements = [index for index, pair in enumerate(train)
                         if shortcut_outputs(pair["input"], chosen)[name] != pair["output"]]
        shortcut_refutations[name] = disagreements
    surviving_shortcuts = [name for name, indices in shortcut_refutations.items() if not indices]
    if surviving_shortcuts:
        raise ValueError(f"shortcut rivals survive every demonstration: {surviving_shortcuts}")

    query_records = []
    for pair in test:
        actual = apply(program(chosen), pair["input"])
        if actual != pair["output"]:
            raise ValueError("query label disagrees with fixed setting")
        query_records.append({"input_sha256": digest(pair["input"]),
                              "output_sha256": digest(pair["output"])})
    return {"scope": "two declared settings plus task-relevant finite shortcut attacks",
            "racket_checked": execute is not None,
            "survivors": survivors,
            "demo_refutations": demo_refutations,
            "shortcut_refutations": shortcut_refutations,
            "surviving_shortcuts": surviving_shortcuts,
            "queries": query_records}


def generate(seed: int, settings: object, demos: int = 3, queries: int = 4) -> dict:
    _integer(seed, 0, 2 ** 63 - 1, "seed")
    _integer(demos, DEMO_LIMITS[0], DEMO_LIMITS[1], "demos")
    if type(queries) is not int or queries != QUERY_COUNT:
        raise ValueError("queries must be the exact integer 4")
    chosen = _settings(settings)
    demo_inputs = _demo_schedule(seed)[:demos]
    query_inputs = [_candidate(seed, "query", index) for index in range(QUERY_COUNT)]
    train = [{"input": grid, "output": transform(grid, chosen)} for grid in demo_inputs]
    test = [{"input": grid, "output": transform(grid, chosen)} for grid in query_inputs]
    episode = {"schema": "c53c24435976-command-chain-parametric-v1",
               "task_id": TASK_ID, "seed": seed, "settings": chosen,
               "train": train, "test": test,
               "program_solution": program(chosen),
               "program_sha256": hashlib.sha256(program(chosen).encode()).hexdigest()}
    episode["certificate"] = certify(episode)
    return episode


def public_turn(episode: dict, index: int) -> dict:
    _integer(index, 0, 3, "query index")
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or type(test) is not list or len(test) != 4:
        raise ValueError("episode must retain four controller-side queries")
    return {"train": [{"input": copy.deepcopy(pair["input"]),
                       "output": copy.deepcopy(pair["output"])} for pair in train],
            "test": [{"input": copy.deepcopy(test[index]["input"])}]}


def crossed_controls(seed: int) -> dict[str, list[list[list[int]]]]:
    _integer(seed, 0, 2 ** 63 - 1, "seed")
    common = dict(domain="demo", index=0, outer_command=1,
                  canvas=(12, 13), size=(5, 6), position=(3, 4),
                  object_key="cross-inner")
    inner_pair = None
    for attempt in range(128):
        try:
            inner_a = _scene(seed, inner_command=2, attempt=attempt, **common)
            inner_b = _scene(seed, inner_command=4, attempt=attempt, **common)
        except ValueError:
            continue
        if transform(inner_a, CHAINED) != transform(inner_b, CHAINED):
            inner_pair = inner_a, inner_b
            break
    if inner_pair is None:
        raise RuntimeError("could not construct a shared crossed inner-command control")
    inner_a, inner_b = inner_pair

    nuisance_pair = None
    for attempt in range(128):
        try:
            nuisance_a = _scene(seed, "demo", 1, attempt=attempt,
                                outer_command=3, inner_command=2,
                                canvas=(10, 11), size=(5, 6), position=(2, 3),
                                object_key="cross-nuisance")
        except ValueError:
            continue
        matrix = _crop(nuisance_a)
        nuisance_b = _embed(matrix, (18, 20), (9, 11), 3)
        if (stage_one(nuisance_a) == stage_one(nuisance_b)
                and transform(nuisance_a, CHAINED) == transform(nuisance_b, CHAINED)
                and transform(nuisance_a, CHAINED) != stage_one(nuisance_a)):
            nuisance_pair = nuisance_a, nuisance_b
            break
    if nuisance_pair is None:
        raise RuntimeError("could not construct a shared canvas/position nuisance control")
    nuisance_a, nuisance_b = nuisance_pair
    return {"vary_inner_command": [inner_a, inner_b],
            "vary_canvas_and_position": [nuisance_a, nuisance_b]}


class RacketRunner:
    """One live protected bridge for bounded evidence; never a Python fallback."""
    def __enter__(self):
        from arc_repl.racket_bridge import RacketBridge
        self.bridge = RacketBridge()
        self.identity = self.bridge.runtime_identity
        if self.identity.get("backend") != "racket" or self.identity.get("protected") is not True:
            self.bridge.close()
            raise RuntimeError("live protected Racket backend required")
        self.cache: dict[str, str] = {}
        return self

    def __call__(self, source: str, grid: list[list[int]]) -> list[list[int]]:
        from puzzle_generators.rule_wrap import wrap_rule
        _grid(grid)
        if source not in self.cache:
            self.cache[source] = wrap_rule(source)
        literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
        return self.bridge.eval_text(f"({self.cache[source]} {literal})")

    def __exit__(self, *exc):
        self.bridge.close()
