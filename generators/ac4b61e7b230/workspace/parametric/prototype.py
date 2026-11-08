"""Native parametric family for input-derived red-object translation."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from functools import lru_cache
import hashlib
import json
import random
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
TASK_HOME = HERE.parent.parent
ROOT = next(parent for parent in HERE.parents if (parent / "shared/runtime").is_dir())
RUNTIME_ROOT = ROOT if (ROOT / "RUNTIME_MANIFEST.json").is_file() else ROOT / "shared/runtime"
TASK_ID = "ac4b61e7b230"
VERSION = "1.0.0-native"
MODES = ("all_separated_axes", "dominant_gap_axis")
sys.path.insert(0, str(RUNTIME_ROOT))

from reviewer_support import canonical_path, load_selected_generator


def text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def object_sha256(value) -> str:
    return text_sha256(json.dumps(value, sort_keys=True, separators=(",", ":")))


@dataclass(frozen=True)
class Parameters:
    translation_mode: str = "all_separated_axes"

    def __post_init__(self):
        if type(self.translation_mode) is not str:
            raise TypeError("translation_mode must be a string")
        if self.translation_mode not in MODES:
            raise ValueError(f"translation_mode must be one of {MODES}")

    def as_dict(self) -> dict[str, str]:
        return {"translation_mode": self.translation_mode}


DEFAULT = Parameters()
ALL_PARAMETERS = tuple(Parameters(mode) for mode in MODES)


def _validate_seed(seed: int) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be a literal integer")
    if seed < 0:
        raise ValueError("seed must be nonnegative")


def _derived_seed(seed: int, namespace: str) -> int:
    return int(text_sha256(f"{TASK_ID}:{VERSION}:{namespace}:{seed}"), 16) % (2**63)


@lru_cache(maxsize=1)
def canonical_program() -> str:
    programs = set()
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            if TASK_ID not in line:
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                programs.add(row["program_solution"])
    if len(programs) != 1:
        raise ValueError(f"expected one canonical program, found {len(programs)}")
    return programs.pop()


_OLD_BINDINGS = """(let* ((dr (if (< r2a r1b)
                                                  (- (- r1b r2a) 1)
                                                  (if (> r1a r2b) (- (+ r2b 1) r1a) 0)))
                                          (dc (if (< c2a c1b)
                                                  (- (- c1b c2a) 1)
                                                  (if (> c1a c2b) (- (+ c2b 1) c1a) 0)))
                                          (blank (cellmap g (r c v) 0))"""
_NEW_BINDINGS = """(let* ((raw-dr (if (< r2a r1b)
                                                      (- (- r1b r2a) 1)
                                                      (if (> r1a r2b) (- (+ r2b 1) r1a) 0)))
                                          (raw-dc (if (< c2a c1b)
                                                      (- (- c1b c2a) 1)
                                                      (if (> c1a c2b) (- (+ c2b 1) c1a) 0)))
                                          (abs-dr (if (< raw-dr 0) (- 0 raw-dr) raw-dr))
                                          (abs-dc (if (< raw-dc 0) (- 0 raw-dc) raw-dc))
                                          (dr (if (>= abs-dr abs-dc) raw-dr 0))
                                          (dc (if (>= abs-dr abs-dc) 0 raw-dc))
                                          (blank (cellmap g (r c v) 0))"""


def materialize_rule(parameters: Parameters = DEFAULT) -> str:
    if not isinstance(parameters, Parameters):
        raise TypeError("parameters must be Parameters")
    source = canonical_program()
    if parameters == DEFAULT:
        return source
    if source.count(_OLD_BINDINGS) != 1:
        raise ValueError("canonical translation binding shape changed")
    return source.replace(_OLD_BINDINGS, _NEW_BINDINGS)


@lru_cache(maxsize=1)
def _generator_record():
    return load_selected_generator(TASK_ID, root=ROOT)


def generator():
    module, path, loaded_hash = _generator_record()
    if hashlib.sha256(path.read_bytes()).hexdigest() != loaded_hash:
        raise RuntimeError("selected generator changed during this process")
    return module


def _validate_counts(demo_count: int, query_count: int) -> tuple[int, int]:
    if type(demo_count) is not int:
        raise TypeError("demo_count must be a literal integer")
    if type(query_count) is not int:
        raise TypeError("query_count must be a literal integer")
    if not 2 <= demo_count <= 6:
        raise ValueError("demo_count must be in 2..6")
    if not 1 <= query_count <= 4:
        raise ValueError("query_count must be in 1..4")
    return demo_count, query_count


def _selected_translation(dr: int, dc: int, parameters: Parameters) -> tuple[int, int]:
    if parameters.translation_mode == "all_separated_axes":
        return dr, dc
    if abs(dr) >= abs(dc):
        return dr, 0
    return 0, dc


def python_mirror(grid, parameters: Parameters = DEFAULT) -> list[list[int]]:
    if not isinstance(parameters, Parameters):
        raise TypeError("parameters must be Parameters")
    analysis = generator()._analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid task grid: " + "; ".join(analysis["errors"]))
    dr, dc = _selected_translation(*analysis["translation"], parameters)
    height, width = len(grid), len(grid[0])
    shifted = {(row + dr, col + dc) for row, col in analysis["red"]}
    if any(not 0 <= row < height or not 0 <= col < width for row, col in shifted):
        raise ValueError("selected translation leaves the grid")
    if shifted & analysis["cyan"]:
        raise ValueError("selected translation overlaps cyan")
    output = [[0] * width for _ in range(height)]
    for row, col in analysis["cyan"]:
        output[row][col] = 8
    for row, col in shifted:
        output[row][col] = 2
    return output


@dataclass(frozen=True)
class SceneSpec:
    relation: tuple[int, int]
    row_gap: int
    col_gap: int
    red_shapes: tuple[str, ...]
    cyan_shapes: tuple[str, ...]


DEMONSTRATION_SPECS = (
    # Column-dominant: rules out row-only and smaller-gap shortcuts.
    SceneSpec((-1, -1), 2, 6, ("tee5", "ell5"), ("zig5", "u7")),
    # Equal magnitudes with negative motion: teaches the row tie-break and sign.
    SceneSpec((1, 1), 5, 5, ("stair7", "u7"), ("plus5", "tee5")),
    SceneSpec((-1, 1), 7, 3, ("zig5", "ell5"), ("square2", "u7")),
    SceneSpec((-1, 0), 4, 0, ("u7", "tee5"), ("stair7", "plus5")),
    SceneSpec((0, -1), 0, 5, ("ell5", "zig5"), ("tee5", "u7")),
    SceneSpec((1, -1), 3, 6, ("plus5", "stair7"), ("ell5", "tee5")),
)
QUERY_SPECS = (
    SceneSpec((1, -1), 7, 3, ("tee5", "stair7"), ("u7", "zig5")),
    SceneSpec((-1, 1), 2, 7, ("u7", "ell5"), ("plus5", "stair7")),
    SceneSpec((1, 0), 6, 0, ("zig5", "tee5"), ("stair7", "u7")),
)


def _shape_size(shape) -> tuple[int, int]:
    return max(row for row, _ in shape) + 1, max(col for _, col in shape) + 1


def _axis_layout(first_size: int, second_size: int, relation: int, gap: int, rng):
    if relation < 0:
        return 0, first_size + gap, first_size + gap + second_size
    if relation > 0:
        return second_size + gap, 0, second_size + gap + first_size
    span = max(first_size, second_size)
    if first_size <= second_size:
        return rng.randint(0, second_size - first_size), 0, span
    return 0, rng.randint(0, first_size - second_size), span


def _scene(seed: int, index: int, spec: SceneSpec) -> list[list[int]]:
    rng = random.Random(_derived_seed(seed, f"scene:{index}"))
    shapes = generator()._SHAPES
    red_shape = shapes[rng.choice(spec.red_shapes)]
    cyan_shape = shapes[rng.choice(spec.cyan_shapes)]
    red_h, red_w = _shape_size(red_shape)
    cyan_h, cyan_w = _shape_size(cyan_shape)
    red_row, cyan_row, used_h = _axis_layout(
        red_h, cyan_h, spec.relation[0], spec.row_gap, rng
    )
    red_col, cyan_col, used_w = _axis_layout(
        red_w, cyan_w, spec.relation[1], spec.col_gap, rng
    )
    top, bottom = rng.randint(1, 3), rng.randint(1, 3)
    left, right = rng.randint(1, 3), rng.randint(1, 3)
    height, width = top + used_h + bottom, left + used_w + right
    grid = [[0] * width for _ in range(height)]
    for row, col in red_shape:
        grid[top + red_row + row][left + red_col + col] = 2
    for row, col in cyan_shape:
        grid[top + cyan_row + row][left + cyan_col + col] = 8
    errors = generator().self_check(grid)
    if errors:
        raise AssertionError("invalid constructed scene: " + "; ".join(errors))
    analysis = generator()._analysis(grid)
    if analysis["relation"] != spec.relation:
        raise AssertionError("constructed relation drifted")
    expected = (
        spec.row_gap if spec.relation[0] < 0 else -spec.row_gap if spec.relation[0] > 0 else 0,
        spec.col_gap if spec.relation[1] < 0 else -spec.col_gap if spec.relation[1] > 0 else 0,
    )
    if analysis["translation"] != expected:
        raise AssertionError(f"constructed translation {analysis['translation']} != {expected}")
    return grid


def _stress30(seed: int) -> list[list[int]]:
    """A dense 30x30 equal-gap scene touching all four boundaries."""
    del seed
    grid = [[0] * 30 for _ in range(30)]
    red = {
        (row, col)
        for row in range(8)
        for col in range(9)
        if not (2 <= row <= 5 and col == 4)
    }
    cyan = {
        (21 + row, 22 + col)
        for row in range(9)
        for col in range(8)
        if not (row == 4 and 2 <= col <= 5)
    }
    for row, col in red:
        grid[row][col] = 2
    for row, col in cyan:
        grid[row][col] = 8
    errors = generator().self_check(grid)
    if errors:
        raise AssertionError("invalid 30x30 stress scene: " + "; ".join(errors))
    analysis = generator()._analysis(grid)
    if analysis["translation"] != (13, 13):
        raise AssertionError("30x30 stress translation drifted")
    return grid


def _build_input_pool(seed: int) -> tuple[list, list, list[dict]]:
    _validate_seed(seed)
    input_seed = _derived_seed(seed, "inputs")
    demonstrations = [
        _scene(input_seed, index, spec)
        for index, spec in enumerate(DEMONSTRATION_SPECS)
    ]
    queries = [
        _scene(input_seed, 100 + index, spec)
        for index, spec in enumerate(QUERY_SPECS)
    ] + [_stress30(input_seed)]
    all_inputs = demonstrations + queries
    keys = [object_sha256(grid) for grid in all_inputs]
    if len(set(keys)) != 10:
        raise AssertionError("native input pool contains duplicates")
    signatures = {
        parameters.translation_mode: tuple(
            object_sha256(python_mirror(grid, parameters))
            for grid in demonstrations[:2]
        )
        for parameters in ALL_PARAMETERS
    }
    if len(set(signatures.values())) != len(ALL_PARAMETERS):
        raise AssertionError("first two demonstrations do not identify both settings")
    draws = [
        {"split": "train", "index": index, "relation": list(spec.relation),
         "row_gap": spec.row_gap, "col_gap": spec.col_gap}
        for index, spec in enumerate(DEMONSTRATION_SPECS)
    ] + [
        {"split": "test", "index": index, "relation": list(spec.relation),
         "row_gap": spec.row_gap, "col_gap": spec.col_gap}
        for index, spec in enumerate(QUERY_SPECS)
    ] + [{"split": "test", "index": 3, "profile": "stress30", "row_gap": 13, "col_gap": 13}]
    return demonstrations, queries, draws


def sample_inputs(seed: int, *, demo_count: int, query_count: int) -> dict:
    demo_count, query_count = _validate_counts(demo_count, query_count)
    demonstrations, queries, draws = _build_input_pool(seed)
    return {
        "demonstrations": deepcopy(demonstrations[:demo_count]),
        "queries": deepcopy(queries[:query_count]),
        "draws": deepcopy(draws),
    }


def public_challenge(episode: dict, *, revealed_queries: int = 1) -> dict:
    if type(revealed_queries) is not int or not 1 <= revealed_queries <= len(episode.get("test", [])):
        raise ValueError("revealed_queries must be within the available query count")
    return {
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [
            {"input": deepcopy(pair["input"])}
            for pair in episode["test"][:revealed_queries]
        ],
    }
