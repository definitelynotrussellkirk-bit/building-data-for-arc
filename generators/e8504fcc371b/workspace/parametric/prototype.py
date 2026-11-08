"""Matched-input commanded-ray family with a sequential border continuation.

The canonical setting paints the command-selected ray from the seed to the
border.  The alternate has a real A -> intermediate -> B dependency: step A
traces that ray and returns its border endpoint and length; step B starts after
the endpoint in clockwise perimeter order and paints the same number of cells.
Python constructs deterministic claims while native qualification re-executes
both exact programs through protected Racket.
"""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any

TASK_ID = "e8504fcc371b"
HERE = Path(__file__).resolve().parent
MODES = ("straight_to_border", "border_hook")
PROGRAM_FILES = {
    "straight_to_border": "canonical.rkt",
    "border_hook": "border_hook.rkt",
}
DEMO_SHAPES = ((10, 14), (14, 10), (16, 18), (18, 16), (22, 24), (26, 22))
QUERY_SHAPES = ((8, 12), (16, 20), (23, 27), (30, 30))
DIRS = {
    1: (-1, 0),
    2: (1, 0),
    3: (0, -1),
    4: (0, 1),
}


def _integer(value: Any, name: str, low: int | None = None, high: int | None = None) -> int:
    if type(value) is not int:
        raise ValueError(f"{name} must be an exact integer")
    if low is not None and value < low:
        raise ValueError(f"{name} must be at least {low}")
    if high is not None and value > high:
        raise ValueError(f"{name} must be at most {high}")
    return value


def _settings(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"trail_mode"}:
        raise ValueError("settings must contain exactly trail_mode")
    mode = settings["trail_mode"]
    if type(mode) is not str or mode not in MODES:
        raise ValueError("trail_mode must be straight_to_border or border_hook")
    return mode


def _grid(grid: Any) -> list[list[int]]:
    if (
        type(grid) is not list
        or not 1 <= len(grid) <= 30
        or type(grid[0]) is not list
        or not 1 <= len(grid[0]) <= 30
    ):
        raise ValueError("grid must have 1..30 rows and columns")
    width = len(grid[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in grid
    ):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    return grid


def program(settings: dict[str, str]) -> str:
    mode = _settings(settings)
    return (HERE / PROGRAM_FILES[mode]).read_text(encoding="utf-8")


def perimeter(grid: list[list[int]]) -> list[tuple[int, int]]:
    """Clockwise perimeter, starting at the upper-left corner exactly once."""
    source = _grid(grid)
    height, width = len(source), len(source[0])
    if height < 2 or width < 2:
        raise ValueError("perimeter needs at least a 2x2 grid")
    cells = [(0, col) for col in range(width)]
    cells.extend((row, width - 1) for row in range(1, height))
    cells.extend((height - 1, col) for col in range(width - 2, -1, -1))
    cells.extend((row, 0) for row in range(height - 2, 0, -1))
    if len(cells) != 2 * height + 2 * width - 4 or len(cells) != len(set(cells)):
        raise AssertionError("perimeter enumeration is malformed")
    return cells


def scene_facts(grid: list[list[int]]) -> dict[str, Any]:
    """Parse the intentionally narrow two-marker input grammar."""
    source = _grid(grid)
    commands = [
        (row, col, source[row][col])
        for row in range(len(source))
        for col in range(len(source[0]))
        if source[row][col] in DIRS
    ]
    seeds = [
        (row, col, source[row][col])
        for row in range(len(source))
        for col in range(len(source[0]))
        if source[row][col] in (5, 6, 7, 8, 9)
    ]
    nonzero = sum(cell != 0 for row in source for cell in row)
    if len(commands) != 1 or len(seeds) != 1 or nonzero != 2:
        raise ValueError("input must contain exactly one command and one seed marker")
    command_row, command_col, code = commands[0]
    seed_row, seed_col, seed_color = seeds[0]
    drow, dcol = DIRS[code]
    cells: list[tuple[int, int]] = []
    row, col = seed_row + drow, seed_col + dcol
    while 0 <= row < len(source) and 0 <= col < len(source[0]):
        cells.append((row, col))
        row += drow
        col += dcol
    if len(cells) < 2:
        raise ValueError("commanded ray must contain at least two cells")
    if (command_row, command_col) in cells:
        raise ValueError("command marker may not lie on the commanded ray")
    if any(source[row][col] != 0 for row, col in cells):
        raise ValueError("commanded ray must be zero in the input")
    if drow:
        relation = "behind_seed" if command_col == seed_col and (command_row - seed_row) * drow < 0 else "off_axis" if command_col != seed_col else None
    else:
        relation = "behind_seed" if command_row == seed_row and (command_col - seed_col) * dcol < 0 else "off_axis" if command_row != seed_row else None
    if relation is None:
        raise ValueError("command must be behind the seed or off the movement axis")
    return {
        "shape": [len(source), len(source[0])],
        "code": code,
        "seed_color": seed_color,
        "seed": [seed_row, seed_col],
        "command": [command_row, command_col],
        "command_relation": relation,
        "ray_length": len(cells),
        "endpoint": list(cells[-1]),
    }


def ray_cells(grid: list[list[int]]) -> list[tuple[int, int]]:
    facts = scene_facts(grid)
    seed_row, seed_col = facts["seed"]
    drow, dcol = DIRS[facts["code"]]
    return [
        (seed_row + drow * step, seed_col + dcol * step)
        for step in range(1, facts["ray_length"] + 1)
    ]


def intermediate_value(grid: list[list[int]]) -> dict[str, Any]:
    """Step A: trace the commanded ray and return endpoint plus length."""
    facts = scene_facts(grid)
    return {"endpoint": list(facts["endpoint"]), "ray_length": facts["ray_length"]}


def hook_cells(grid: list[list[int]], length: int | None = None) -> list[tuple[int, int]]:
    """Step B's clockwise cells immediately after the ray endpoint."""
    source = _grid(grid)
    intermediate = intermediate_value(source)
    if length is None:
        length = intermediate["ray_length"]
    _integer(length, "length", 1)
    border = perimeter(source)
    if length >= len(border):
        raise ValueError("hook length must be shorter than the perimeter")
    endpoint = tuple(intermediate["endpoint"])
    try:
        start = border.index(endpoint)
    except ValueError as exc:  # defensive; a traced ray always ends on border
        raise ValueError("ray endpoint is not on the perimeter") from exc
    return [border[(start + offset) % len(border)] for offset in range(1, length + 1)]


def transform(grid: list[list[int]], settings: dict[str, str]) -> list[list[int]]:
    """Pure Python label claim matching the two exact Racket programs."""
    mode = _settings(settings)
    source = _grid(grid)
    facts = scene_facts(source)
    cells = ray_cells(source)
    if mode == "border_hook":
        cells += hook_cells(source, facts["ray_length"])
    output = deepcopy(source)
    for row, col in cells:
        if output[row][col] == 0:
            output[row][col] = facts["seed_color"]
    return output


def changed_cells(source: list[list[int]], output: list[list[int]]) -> set[tuple[int, int]]:
    left, right = _grid(source), _grid(output)
    if (len(left), len(left[0])) != (len(right), len(right[0])):
        raise ValueError("source and output shapes differ")
    return {
        (row, col)
        for row in range(len(left))
        for col in range(len(left[0]))
        if left[row][col] != right[row][col]
    }


def _ray_length(stream: str, index: int, axis: int) -> int:
    if stream == "train":
        raw = (2, axis // 2, axis - 3, 3, axis // 2 + 1, axis - 4)[index]
    elif stream == "test":
        raw = (3, axis // 2, axis - 4, axis - 5)[index]
    else:
        raise ValueError("stream must be train or test")
    return max(2, min(axis - 2, raw))


def _perpendicular_coordinate(code: int, height: int, width: int) -> int:
    # Clockwise travel from an endpoint moves right/down/left/up for commands
    # up/right/down/left.  Bias the endpoint toward the preceding side so long
    # rays plus hooks span both dimensions in the 30x30 stress case.
    if code == 1:
        return max(1, min(width - 2, width // 5))
    if code == 2:
        return max(1, min(width - 2, width - 1 - width // 5))
    if code == 3:
        return max(1, min(height - 2, height - 1 - height // 5))
    return max(1, min(height - 2, height // 5))


def sample_input(seed: int, stream: str, index: int, height: int, width: int) -> list[list[int]]:
    """Build a setting-independent two-marker scene with controlled geometry."""
    _integer(seed, "seed", 0, 2**63 - 1)
    _integer(index, "index", 0)
    _integer(height, "height", 4, 30)
    _integer(width, "width", 4, 30)
    if stream not in ("train", "test"):
        raise ValueError("stream must be train or test")
    limit = len(DEMO_SHAPES) if stream == "train" else len(QUERY_SHAPES)
    if index >= limit:
        raise ValueError("index exceeds the finite stream schedule")

    stream_offset = 0 if stream == "train" else 2
    code = ((seed + index + stream_offset) % 4) + 1
    seed_color = 5 + ((3 * seed + index + stream_offset) % 5)
    axis = height if code in (1, 2) else width
    length = _ray_length(stream, index, axis)
    perpendicular = _perpendicular_coordinate(code, height, width)
    if code == 1:
        seed_row, seed_col = length, perpendicular
    elif code == 2:
        seed_row, seed_col = height - 1 - length, perpendicular
    elif code == 3:
        seed_row, seed_col = perpendicular, length
    else:
        seed_row, seed_col = perpendicular, width - 1 - length

    grid = [[0 for _ in range(width)] for _ in range(height)]
    grid[seed_row][seed_col] = seed_color
    drow, dcol = DIRS[code]
    relation = ("behind_seed", "off_axis")[(index + stream_offset) % 2]
    if relation == "behind_seed":
        command_row, command_col = seed_row - drow, seed_col - dcol
    elif code in (1, 2):
        command_row = seed_row
        command_col = seed_col + 1 if seed_col + 1 < width else seed_col - 1
    else:
        command_row = seed_row + 1 if seed_row + 1 < height else seed_row - 1
        command_col = seed_col
    if grid[command_row][command_col] != 0:
        raise AssertionError("command collided with seed")
    grid[command_row][command_col] = code

    facts = scene_facts(grid)
    if facts["ray_length"] != length or facts["command_relation"] != relation:
        raise AssertionError("sampler failed to realize scheduled facts")
    selected_hook = set(hook_cells(grid, length))
    if (command_row, command_col) in selected_hook or (seed_row, seed_col) in selected_hook:
        raise AssertionError("marker collided with the border continuation")
    return grid


def generate(seed: int, settings: dict[str, str], demos: int, queries: int) -> dict[str, Any]:
    """Native adapter contract: deterministic, matched and count-independent."""
    _integer(seed, "seed", 0, 2**63 - 1)
    mode = _settings(settings)
    _integer(demos, "demos", 2, 6)
    _integer(queries, "queries", 1, 4)
    result: dict[str, Any] = {
        "train": [],
        "test": [],
        "program_solution": program(settings),
        "settings": {"trail_mode": mode},
        "seed": seed,
        "prototype": True,
    }
    seen: set[str] = set()
    for split, shapes in (("train", DEMO_SHAPES[:demos]), ("test", QUERY_SHAPES[:queries])):
        for index, (height, width) in enumerate(shapes):
            grid = sample_input(seed, split, index, height, width)
            digest = json.dumps(grid, separators=(",", ":"))
            if digest in seen:
                raise ValueError("deterministic sampler produced duplicate inputs")
            seen.add(digest)
            result[split].append({"input": grid, "output": transform(grid, settings)})
    return result


def _hook_program(hook_length: str) -> str:
    return f"""(rule!
  (let* ((cmd-cell (last (filter (lambda (cell) (member (third cell) (list 1 2 3 4)))
                                 (grid-cells g))))
         (seed-cell (last (filter (lambda (cell)
                                    (and (not (= (third cell) 0))
                                         (not (member (third cell) (list 1 2 3 4)))))
                                  (grid-cells g))))
         (code (third cmd-cell))
         (color (third seed-cell))
         (sr (first seed-cell))
         (sc (second seed-cell))
         (delta (cond [(= code 1) (list -1 0)]
                      [(= code 2) (list 1 0)]
                      [(= code 3) (list 0 -1)]
                      [else (list 0 1)]))
         (dr (first delta))
         (dc (second delta))
         (ray-length (cond [(= code 1) sr]
                           [(= code 2) (- (- (rows g) 1) sr)]
                           [(= code 3) sc]
                           [else (- (- (cols g) 1) sc)]))
         (end-r (+ sr (* dr ray-length)))
         (end-c (+ sc (* dc ray-length)))
         (perimeter
          (append
           (for/list ([c (in-range 0 (cols g))]) (list 0 c))
           (for/list ([r (in-range 1 (rows g))]) (list r (- (cols g) 1)))
           (for/list ([c (in-range (- (cols g) 2) -1 -1)]) (list (- (rows g) 1) c))
           (for/list ([r (in-range (- (rows g) 2) 0 -1)]) (list r 0))))
         (end-index
          (cond [(= end-r 0) end-c]
                [(= end-c (- (cols g) 1)) (+ (- (cols g) 1) end-r)]
                [(= end-r (- (rows g) 1))
                 (+ (- (cols g) 1) (- (rows g) 1) (- (- (cols g) 1) end-c))]
                [else
                 (+ (- (cols g) 1) (- (rows g) 1) (- (cols g) 1)
                    (- (- (rows g) 1) end-r))]))
         (ray-cells
          (for/list ([k (in-range 1 (+ ray-length 1))])
            (list (+ sr (* dr k)) (+ sc (* dc k)))))
         (hook-length {hook_length})
         (hook-cells
          (for/list ([k (in-range 1 (+ hook-length 1))])
            (list-ref perimeter (modulo (+ end-index k) (length perimeter)))))
         (paint-cells* (append ray-cells hook-cells)))
    (for/fold ([out g]) ([cell (in-list paint-cells*)])
      (let ((r (first cell)) (c (second cell)))
        (if (= (at out r c) 0) (set-cell out r c color) out)))))"""


def counterfactual_program(length: int) -> str:
    """Wrong-intermediate ablation: force B to use a fixed hook length."""
    _integer(length, "length", 1, 30)
    return _hook_program(str(length))


class RacketEngine:
    """Small protected-Racket test helper; native worker remains authoritative."""

    def __init__(self) -> None:
        self.bridge = None
        self._wrapped: dict[str, str] = {}

    def __enter__(self):
        from arc_repl.racket_bridge import RacketBridge

        self.bridge = RacketBridge(timeout=60)
        identity = self.bridge.runtime_identity
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            self.bridge.close()
            self.bridge = None
            raise ValueError("tests require the protected Racket backend")
        return self

    def __exit__(self, exc_type, exc, traceback):
        if self.bridge is not None:
            self.bridge.close()
            self.bridge = None

    def apply(self, source: str, grid: list[list[int]]) -> list[list[int]]:
        if self.bridge is None:
            raise RuntimeError("RacketEngine must be used as a context manager")
        _grid(grid)
        from puzzle_generators.rule_wrap import wrap_rule

        wrapped = self._wrapped.setdefault(source, wrap_rule(source))
        literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
        return _grid(self.bridge.eval_text(f"({wrapped} {literal})"))


def verify_episode(episode: dict[str, Any], *, engine: RacketEngine | None = None) -> dict[str, Any]:
    """Bounded demonstration-only setting identification and query checks."""
    if type(episode) is not dict:
        raise ValueError("episode must be an object")
    mode = _settings(episode.get("settings"))
    expected_program = program({"trail_mode": mode})
    if episode.get("program_solution") != expected_program:
        raise ValueError("episode program does not match settings")
    normalized: dict[str, list[dict[str, list[list[int]]]]] = {}
    for split in ("train", "test"):
        pairs = episode.get(split)
        if type(pairs) is not list or not pairs:
            raise ValueError(f"episode {split} must be a nonempty list")
        normalized[split] = []
        for pair in pairs:
            if type(pair) is not dict or not {"input", "output"} <= set(pair):
                raise ValueError("each pair needs input and output")
            source = deepcopy(_grid(pair["input"]))
            scene_facts(source)
            output = deepcopy(_grid(pair["output"]))
            if (len(source), len(source[0])) != (len(output), len(output[0])):
                raise ValueError("pair input and output shapes differ")
            normalized[split].append({"input": source, "output": output})
    digests = [
        json.dumps(pair["input"], separators=(",", ":"))
        for pairs in normalized.values()
        for pair in pairs
    ]
    if len(digests) != len(set(digests)):
        raise ValueError("all episode inputs must be distinct")

    owned = engine is None
    runtime = RacketEngine().__enter__() if owned else engine
    try:
        survivors = []
        for candidate in MODES:
            settings = {"trail_mode": candidate}
            if all(
                runtime.apply(program(settings), pair["input"]) == pair["output"]
                for pair in normalized["train"]
            ):
                survivors.append(settings)
        chosen = {"trail_mode": mode}
        if survivors != [chosen]:
            raise ValueError("demonstrations do not identify the selected setting")
        checks = []
        for index, pair in enumerate(normalized["test"]):
            actual = runtime.apply(expected_program, pair["input"])
            if actual != pair["output"]:
                raise ValueError(f"query label mismatch at index {index}")
            checks.append({"index": index, "identified_from_demonstrations": True})
        return {"fit_scope": "demonstrations_only", "survivors": survivors, "query_checks": checks}
    finally:
        if owned:
            runtime.__exit__(None, None, None)
