"""Episode-fixed rotations of the canonical directional color compass."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

TASK_ID = "c792bb147617"
ORIENTATIONS = ("canonical", "rotate_cw", "rotate_180", "rotate_ccw")
DIRECTION_COLORS = {
    "canonical": {"up": 2, "left": 7, "right": 6, "down": 8},
    "rotate_cw": {"up": 7, "left": 8, "right": 2, "down": 6},
    "rotate_180": {"up": 8, "left": 6, "right": 7, "down": 2},
    "rotate_ccw": {"up": 6, "left": 2, "right": 8, "down": 7},
}

_REPO = Path(__file__).resolve().parents[4]
_CANONICAL = _REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"


def _orientation(value: object) -> str:
    if type(value) is not str or value not in ORIENTATIONS:
        raise ValueError("orientation must be one of: " + ", ".join(ORIENTATIONS))
    return value


def _canonical_program() -> str:
    programs: set[str] = set()
    for line in _CANONICAL.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            program = row.get("program_solution")
            if isinstance(program, str):
                programs.add(program)
    if len(programs) != 1:
        raise ValueError(f"expected one exact canonical program for {TASK_ID}, found {len(programs)}")
    return programs.pop()


def program_for(orientation: str) -> str:
    """Materialize exact Racket for one declared orientation."""
    orientation = _orientation(orientation)
    program = _canonical_program()
    if orientation == "canonical":
        return program
    mapping = DIRECTION_COLORS[orientation]
    replacements = {
        "(hash-set! result (list (- r 1) c) 2)":
            f"(hash-set! result (list (- r 1) c) {mapping['up']})",
        "(hash-set! result (list r (- c 1)) 7)":
            f"(hash-set! result (list r (- c 1)) {mapping['left']})",
        "(hash-set! result (list r (+ c 1)) 6)":
            f"(hash-set! result (list r (+ c 1)) {mapping['right']})",
        "(hash-set! result (list (+ r 1) c) 8)":
            f"(hash-set! result (list (+ r 1) c) {mapping['down']})",
    }
    for original, replacement in replacements.items():
        if program.count(original) != 1:
            raise ValueError(f"canonical program shape changed at {original!r}")
        program = program.replace(original, replacement)
    return program


def transform(grid: list[list[int]], orientation: str) -> list[list[int]]:
    """Apply one palette orientation using the canonical row-major write order."""
    orientation = _orientation(orientation)
    if (
        type(grid) is not list
        or not grid
        or type(grid[0]) is not list
        or not grid[0]
        or any(type(row) is not list or len(row) != len(grid[0]) for row in grid)
    ):
        raise ValueError("grid must be a non-empty rectangular list of lists")
    if any(type(cell) is not int or not 0 <= cell <= 9 for row in grid for cell in row):
        raise ValueError("grid cells must be exact integer colors 0..9")

    source = [row[:] for row in grid]
    output = [row[:] for row in source]
    height, width = len(source), len(source[0])
    colors = DIRECTION_COLORS[orientation]
    anchors = [
        (row, col)
        for row, values in enumerate(source)
        for col, value in enumerate(values)
        if value == 1
    ]
    for row, col in anchors:
        if row > 0:
            output[row - 1][col] = colors["up"]
        if col > 0:
            output[row][col - 1] = colors["left"]
        if col < width - 1:
            output[row][col + 1] = colors["right"]
        if row < height - 1:
            output[row + 1][col] = colors["down"]
    return output


_INPUT_PROFILES = (
    (8, 8, 4, "none"),
    (10, 10, 8, "some"),
    (12, 9, 6, "some"),
    (6, 16, 2, "none"),
    (16, 6, 8, "some"),
    (9, 13, 5, "none"),
    (14, 11, 7, "some"),
    (7, 15, 3, "none"),
    (15, 7, 4, "some"),
    (11, 16, 6, "none"),
    (16, 12, 5, "some"),
    (13, 8, 8, "none"),
    (8, 14, 7, "some"),
    (12, 16, 3, "none"),
    (16, 9, 6, "some"),
    (10, 15, 2, "none"),
)
_BASE_GENERATOR = None


def _integer(value: object, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in {low}..{high}; bool is forbidden")
    return value


def _base_generator():
    global _BASE_GENERATOR
    if _BASE_GENERATOR is None:
        source = _REPO / "generators" / TASK_ID / "generator.py"
        name = "_palette_rotation_base_" + hashlib.sha256(str(source).encode()).hexdigest()
        spec = importlib.util.spec_from_file_location(name, source)
        if spec is None or spec.loader is None:
            raise ImportError(f"cannot load selected generator from {source}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _BASE_GENERATOR = module
    return _BASE_GENERATOR


def _input_seed(seed: int, slot: int) -> int:
    digest = hashlib.sha256(f"palette-rotation-input-v1:{seed}:{slot}".encode()).digest()
    return int.from_bytes(digest[:8], "big") & (2**63 - 1)


def _episode_inputs(seed: int, count: int) -> list[list[list[int]]]:
    generator = _base_generator()
    inputs = []
    for slot, (height, width, n_blues, edge_mode) in enumerate(_INPUT_PROFILES[:count]):
        grid = generator.generate(
            _input_seed(seed, slot),
            slot,
            grid_h=height,
            grid_w=width,
            n_blues=n_blues,
            edge_mode=edge_mode,
        )
        if generator.self_check(grid) != []:
            raise ValueError(f"selected generator produced an invalid profile at slot {slot}")
        inputs.append(grid)
    keys = {json.dumps(grid, separators=(",", ":")) for grid in inputs}
    if len(keys) != count:
        raise RuntimeError("profile schedule produced duplicate inputs")
    return inputs


def generate_episode(seed: int, orientation: str, *, demos: int = 3, queries: int = 4) -> dict:
    """Generate one fixed-orientation episode with setting-neutral distinct inputs."""
    seed = _integer(seed, "seed", 0, 2**63 - 1)
    orientation = _orientation(orientation)
    demos = _integer(demos, "demos", 2, 8)
    queries = _integer(queries, "queries", 1, 8)
    inputs = _episode_inputs(seed, demos + queries)
    pairs = [{"input": grid, "output": transform(grid, orientation)} for grid in inputs]
    return {
        "train": pairs[:demos],
        "test": pairs[demos:],
        "program_solution": program_for(orientation),
    }


def surviving_orientations(demos: list[dict]) -> tuple[str, ...]:
    """Return declared settings consistent with labeled demonstrations only."""
    if type(demos) is not list or not demos:
        raise ValueError("at least one labeled demonstration is required")
    survivors = []
    for orientation in ORIENTATIONS:
        if all(
            isinstance(pair, dict)
            and "input" in pair
            and "output" in pair
            and transform(pair["input"], orientation) == pair["output"]
            for pair in demos
        ):
            survivors.append(orientation)
    return tuple(survivors)
