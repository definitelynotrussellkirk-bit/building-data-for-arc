"""Native halo-depth family for ARC generator 603bd7fff5df.

The episode parameter is the number of rows retained above and below the gray
side-marker bounding box.  Depth one is the exact selected canonical program;
depths zero and two preserve the same gray-bbox reasoning while changing the
crop extent.  Inputs are matched across settings and query prefixes are stable.
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import hashlib
import importlib.util
from pathlib import Path
import os
import random
from typing import Any, Callable

from reviewer_support import find_root

TASK_ID = "603bd7fff5df"
PROTOTYPE_VERSION = "2.0.0"
HALO_DEPTHS = (0, 1, 2)
DEFAULT_HALO_DEPTH = 1
MIN_DEMOS = 2
MAX_DEMOS = 6
MIN_QUERIES = 1
MAX_QUERIES = 4
HERE = Path(__file__).resolve().parent
_PROGRAM_PATHS = {
    0: HERE / "halo-depth-0.rkt",
    1: HERE / "canonical.rkt",
    2: HERE / "halo-depth-2.rkt",
}
CANONICAL_PROGRAM = _PROGRAM_PATHS[DEFAULT_HALO_DEPTH].read_text(encoding="utf-8")
_BANDS = ("easy", "medium", "hard")

STEP_A = "locate every gray side marker and compute their bounding box"
INTERMEDIATE = "gray_bbox=(top,left,bottom,right)"
STEP_B = "expand the bbox row interval by the episode halo_depth and extract its bbox columns"
WHY_B_DEPENDS_ON_A = (
    "the output row and column coordinates are functions of the input-derived gray bbox; "
    "without that bbox the crop location cannot be selected"
)


def _integer(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _validate_halo_depth(halo_depth: Any) -> int:
    if type(halo_depth) is not int:
        raise TypeError("halo_depth must be an integer (not bool)")
    if halo_depth not in HALO_DEPTHS:
        raise ValueError(f"halo_depth must be one of {HALO_DEPTHS}")
    return halo_depth


def _settings(settings: Any) -> int:
    if type(settings) is not dict or set(settings) != {"halo_depth"}:
        raise ValueError("settings must contain only halo_depth")
    return _validate_halo_depth(settings["halo_depth"])


def choose_halo_depth(seed: int) -> int:
    _integer(seed, 0, 2**63 - 1, "seed")
    return HALO_DEPTHS[seed % len(HALO_DEPTHS)]


def program_for(halo_depth: Any) -> str:
    depth = _validate_halo_depth(halo_depth)
    return _PROGRAM_PATHS[depth].read_text(encoding="utf-8")


def program(settings: Any) -> str:
    return program_for(_settings(settings))


def normalized_program_hash(halo_depth: Any) -> str:
    return hashlib.sha256(" ".join(program_for(halo_depth).split()).encode()).hexdigest()


def _validate_grid(grid: Any) -> tuple[int, int]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("grid must be a nonempty rectangular list")
    width = len(grid[0])
    if not 1 <= len(grid) <= 30 or not 1 <= width <= 30:
        raise ValueError("grid dimensions must be in 1..30")
    for row in grid:
        if not isinstance(row, list) or len(row) != width:
            raise ValueError("grid must be rectangular")
        if any(type(value) is not int or not 0 <= value <= 9 for value in row):
            raise ValueError("grid values must be exact ARC colors 0..9")
    return len(grid), width


def gray_bbox(grid: list[list[int]]) -> tuple[int, int, int, int]:
    _validate_grid(grid)
    cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 5
    ]
    if not cells:
        raise ValueError("grid must contain gray side markers")
    return (
        min(row for row, _ in cells),
        min(col for _, col in cells),
        max(row for row, _ in cells),
        max(col for _, col in cells),
    )


# Compatibility alias for the earlier task-local prototype.
_gray_bbox = gray_bbox


def _crop(grid: list[list[int]], top: int, left: int, bottom: int, right: int) -> list[list[int]]:
    if top < 0 or left < 0 or bottom >= len(grid) or right >= len(grid[0]) or top > bottom or left > right:
        raise ValueError("crop bounds fall outside the grid")
    return [list(row[left : right + 1]) for row in grid[top : bottom + 1]]


def _apply_with_bbox(
    grid: list[list[int]], halo_depth: int, bbox: tuple[int, int, int, int]
) -> list[list[int]]:
    depth = _validate_halo_depth(halo_depth)
    top, left, bottom, right = bbox
    return _crop(grid, top - depth, left, bottom + depth, right)


def apply_python(grid: list[list[int]], halo_depth: Any) -> list[list[int]]:
    """Independent Python mirror used for generation and finite audits."""
    depth = _validate_halo_depth(halo_depth)
    _validate_grid(grid)
    return _apply_with_bbox(grid, depth, gray_bbox(grid))


def _outputs_are_distinct(grid: list[list[int]]) -> bool:
    return len({tuple(map(tuple, apply_python(grid, d))) for d in HALO_DEPTHS}) == len(HALO_DEPTHS)


def _hash_int(*parts: object) -> int:
    payload = ":".join(map(str, parts)).encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


@lru_cache(maxsize=1)
def _load_episode_generator():
    """Load the exact selected generator while respecting the portable runner."""
    default_source = Path(__file__).resolve().parents[2] / "generator.py"
    source_path = Path(os.environ.get("GENERATOR_UNDER_TEST", default_source)).resolve()
    if not source_path.is_file():
        raise FileNotFoundError(f"selected generator source is missing: {source_path}")
    source_sha256 = hashlib.sha256(source_path.read_bytes()).hexdigest()
    spec = importlib.util.spec_from_file_location(
        f"parametric_generator_{TASK_ID}_{source_sha256[:12]}", source_path
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load selected generator from {source_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    root = find_root(__file__)
    try:
        source_label = str(source_path.relative_to(root))
    except ValueError:
        source_label = str(source_path)
    return module, source_label, source_sha256


def _add_outer_halo_evidence(grid: list[list[int]], token: int) -> list[list[int]]:
    result = deepcopy(grid)
    top, left, bottom, right = gray_bbox(result)
    if top < 2 or bottom + 2 >= len(result):
        raise ValueError("candidate lacks two-row vertical margin")
    interior = list(range(left + 1, right))
    if not interior:
        raise ValueError("gray box has no interior column")
    result[top - 2][interior[token % len(interior)]] = 8
    result[bottom + 2][interior[-1 - (token % len(interior))]] = 8
    # Force a blue decoy outside the gray columns so nonzero-bbox and full-width
    # shortcuts cannot accidentally agree with any declared halo depth.
    outside_col = right + 1 if right + 1 < len(result[0]) else left - 1
    if outside_col < 0:
        raise ValueError("candidate has no column outside the gray bbox")
    decoy_row = top + (token % (bottom - top + 1))
    if result[decoy_row][outside_col] == 5:
        decoy_row = top - 2
    result[decoy_row][outside_col] = 8
    return result


def _source_input(seed: int, split: str, index: int) -> list[list[int]]:
    generator, _label, _sha = _load_episode_generator()
    split_offset = 0 if split == "train" else 101
    for attempt in range(128):
        token = split_offset + index * 17 + attempt
        draw_seed = _hash_int(TASK_ID, "input-v2", seed, split, index, attempt) % (2**63)
        sample_index = _hash_int("sample", seed, split, index, attempt) % 100000
        band = _BANDS[(index + attempt) % len(_BANDS)]
        profile = generator.SCENE_PROFILES[(index + split_offset + attempt) % len(generator.SCENE_PROFILES)]
        placement = generator.PLACEMENTS[(2 * index + split_offset + attempt) % len(generator.PLACEMENTS)]
        style = generator.SIDE_STYLES[(index + 2 * split_offset + attempt) % len(generator.SIDE_STYLES)]
        grid = generator.generate(
            draw_seed,
            sample_index,
            difficulty=band,
            scene_profile=profile,
            placement=placement,
            side_style=style,
        )
        try:
            grid = _add_outer_halo_evidence(grid, token)
            if generator.self_check(grid) or not _outputs_are_distinct(grid):
                continue
        except ValueError:
            continue
        return grid
    raise RuntimeError(f"could not construct a lawful {split}[{index}] input")


def _stress_input(seed: int) -> list[list[int]]:
    """A real 30x30 boundary/density case in the same {0,5,8} grammar."""
    rng = random.Random(_hash_int(TASK_ID, "stress-v2", seed))
    height = width = 30
    top = 4 + rng.randrange(3)
    box_h = 17 + rng.randrange(3)
    bottom = top + box_h - 1
    left = 3 + rng.randrange(3)
    box_w = 19 + rng.randrange(3)
    right = left + box_w - 1
    if bottom + 2 >= height or right >= width:
        raise RuntimeError("invalid stress dimensions")
    grid = [[0 for _ in range(width)] for _ in range(height)]

    style = ("full", "gapped", "corners")[seed % 3]
    for row, col in ((top, left), (top, right), (bottom, left), (bottom, right)):
        grid[row][col] = 5
    if style == "full":
        for row in range(top, bottom + 1):
            grid[row][left] = grid[row][right] = 5
    elif style == "gapped":
        for offset, row in enumerate(range(top + 1, bottom)):
            grid[row][left if offset % 2 == 0 else right] = 5

    for row in range(top, bottom + 1):
        for col in range(left + 1, right):
            if (row * 7 + col * 11 + seed) % 7 in (0, 1):
                grid[row][col] = 8
    for ring, row in enumerate((top - 2, top - 1, bottom + 1, bottom + 2)):
        for col in range(left + 1 + ring % 2, right, 3):
            grid[row][col] = 8
    # Distributed distractors outside the crop columns and row span.
    for row in range(1, height - 1, 4):
        for col in (0, 1, width - 2, width - 1):
            if (row + col + seed) % 3:
                grid[row][col] = 8
    for col in range(2, width - 2, 5):
        if grid[1][col] == 0:
            grid[1][col] = 8
        if grid[height - 2][col] == 0:
            grid[height - 2][col] = 8

    if not _outputs_are_distinct(grid):
        raise RuntimeError("stress input does not distinguish halo depths")
    return grid


@lru_cache(maxsize=8192)
def _input_frozen(seed: int, split: str, index: int) -> tuple[tuple[int, ...], ...]:
    if split not in ("train", "test"):
        raise ValueError("split must be train or test")
    grid = _stress_input(seed) if split == "test" and index == 3 else _source_input(seed, split, index)
    return tuple(tuple(row) for row in grid)


def _input(seed: int, split: str, index: int) -> list[list[int]]:
    # Cache immutable source grids, then return fresh lists so callers cannot
    # contaminate later episodes or matched-setting generation.
    return [list(row) for row in _input_frozen(seed, split, index)]


def _build(seed: int, depth: int, demos: int, queries: int) -> dict[str, Any]:
    generator, source_label, source_sha256 = _load_episode_generator()
    del generator
    train = [
        {"input": _input(seed, "train", index), "output": None, "sampling": {"split": "train", "index": index}}
        for index in range(demos)
    ]
    test = [
        {"input": _input(seed, "test", index), "output": None, "sampling": {"split": "test", "index": index}}
        for index in range(queries)
    ]
    for pair in train + test:
        pair["output"] = apply_python(pair["input"], depth)
    identities = [tuple(map(tuple, pair["input"])) for pair in train + test]
    if len(identities) != len(set(identities)):
        raise RuntimeError("generated demonstration/query inputs are not distinct")
    return {
        "schema": "603bd7fff5df-parametric-episode-v2",
        "prototype_version": PROTOTYPE_VERSION,
        "task_id": TASK_ID,
        "seed": seed,
        "settings": {"halo_depth": depth},
        "halo_depth": depth,
        "program": program_for(depth),
        "program_solution": program_for(depth),
        "generator_source": source_label,
        "generator_sha256": source_sha256,
        "train": train,
        "test": test,
    }


def generate(seed: Any, settings: Any, demos: Any, queries: Any) -> dict[str, Any]:
    seed = _integer(seed, 0, 2**63 - 1, "seed")
    depth = _settings(settings)
    demos = _integer(demos, MIN_DEMOS, MAX_DEMOS, "demos")
    queries = _integer(queries, MIN_QUERIES, MAX_QUERIES, "queries")
    return _build(seed, depth, demos, queries)


def build_episode(
    seed: int,
    *,
    halo_depth: int | None = None,
    n_train: int = 3,
    n_test: int = 1,
) -> dict[str, Any]:
    """Compatibility wrapper retained for the original prototype tests/tools."""
    seed = _integer(seed, 0, 2**63 - 1, "seed")
    depth = choose_halo_depth(seed) if halo_depth is None else _validate_halo_depth(halo_depth)
    n_train = _integer(n_train, 1, MAX_DEMOS, "n_train")
    n_test = _integer(n_test, 1, MAX_QUERIES, "n_test")
    return _build(seed, depth, n_train, n_test)


def _bbox_for_color(grid: list[list[int]], color: int) -> tuple[int, int, int, int] | None:
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]
    if not cells:
        return None
    return min(r for r, _ in cells), min(c for _, c in cells), max(r for r, _ in cells), max(c for _, c in cells)


def _rival_full_width(grid: list[list[int]]) -> list[list[int]]:
    top, _left, bottom, _right = gray_bbox(grid)
    return _crop(grid, top - 1, 0, bottom + 1, len(grid[0]) - 1)


def _rival_nonzero_bbox(grid: list[list[int]]) -> list[list[int]]:
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 0]
    return _crop(
        grid,
        min(r for r, _ in cells),
        min(c for _, c in cells),
        max(r for r, _ in cells),
        max(c for _, c in cells),
    )


def _rival_blue_bbox(grid: list[list[int]]) -> list[list[int]]:
    bbox = _bbox_for_color(grid, 8)
    if bbox is None:
        return [[0]]
    return _crop(grid, *bbox)


def _rival_top_only(grid: list[list[int]]) -> list[list[int]]:
    top, left, bottom, right = gray_bbox(grid)
    return _crop(grid, top - 2, left, bottom, right)


def _rival_bottom_only(grid: list[list[int]]) -> list[list[int]]:
    top, left, bottom, right = gray_bbox(grid)
    return _crop(grid, top, left, bottom + 2, right)


PLAUSIBLE_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "full_width_one_row_halo": _rival_full_width,
    "nonzero_bbox": _rival_nonzero_bbox,
    "blue_bbox": _rival_blue_bbox,
    "two_rows_above_only": _rival_top_only,
    "two_rows_below_only": _rival_bottom_only,
}


def teaching_certificate(episode: dict[str, Any]) -> dict[str, Any]:
    train = episode.get("train")
    if not isinstance(train, list) or not train:
        raise ValueError("episode needs demonstrations")
    setting_survivors = [
        depth
        for depth in HALO_DEPTHS
        if all(apply_python(pair["input"], depth) == pair["output"] for pair in train)
    ]
    rival_survivors = [
        name
        for name, rival in PLAUSIBLE_RIVALS.items()
        if all(rival(pair["input"]) == pair["output"] for pair in train)
    ]
    return {
        "setting_survivors": setting_survivors,
        "plausible_rival_survivors": rival_survivors,
    }


def episode_errors(episode: Any) -> list[str]:
    if not isinstance(episode, dict):
        return ["episode must be a mapping"]
    try:
        depth = _validate_halo_depth(episode.get("halo_depth"))
    except (TypeError, ValueError) as exc:
        return [str(exc)]
    if episode.get("program") != program_for(depth):
        return ["episode program does not match halo_depth"]
    train, test = episode.get("train"), episode.get("test")
    if not isinstance(train, list) or not train or not isinstance(test, list) or not test:
        return ["episode needs nonempty train and test lists"]
    errors: list[str] = []
    for split, pairs in (("train", train), ("test", test)):
        for index, pair in enumerate(pairs):
            if not isinstance(pair, dict) or not {"input", "output"} <= set(pair):
                errors.append(f"{split}[{index}] must contain input and output")
                continue
            try:
                expected = apply_python(pair["input"], depth)
            except (TypeError, ValueError) as exc:
                errors.append(f"{split}[{index}] invalid: {exc}")
                continue
            if pair["output"] != expected:
                errors.append(f"{split}[{index}] output disagrees with halo_depth")
            if not _outputs_are_distinct(pair["input"]):
                errors.append(f"{split}[{index}] does not distinguish halo depths")
    if train and teaching_certificate(episode) != {
        "setting_survivors": [depth],
        "plausible_rival_survivors": [],
    }:
        errors.append("visible demonstrations do not uniquely teach the selected setting and rivals")
    return errors


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    return {
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": deepcopy(pair["input"])} for pair in episode["test"]],
    }


def public_turn(episode: dict[str, Any], query_index: Any) -> dict[str, Any]:
    query_index = _integer(query_index, 0, len(episode["test"]) - 1, "query_index")
    return {
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": deepcopy(episode["test"][query_index]["input"])}],
    }


def _counterfactual_program(depth: int) -> str:
    depth = _validate_halo_depth(depth)
    top_expr = "wrong-top" if depth == 0 else f"(- wrong-top {depth})"
    bottom_expr = "wrong-bottom" if depth == 0 else f"(+ wrong-bottom {depth})"
    return f"""(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((fives (find-color g 5))
                  (rs (map first fives))
                  (cs (map second fives))
                  (wrong-top (+ (min-list rs) 1))
                  (wrong-bottom (- (max-list rs) 1))
                  (r1 {top_expr})
                  (c1 (min-list cs))
                  (r2 {bottom_expr})
                  (c2 (max-list cs)))
             (subgrid g r1 c1 r2 c2)))))"""


def dependency_case(seed: int = 91, halo_depth: int = 2) -> dict[str, Any]:
    seed = _integer(seed, 0, 2**63 - 1, "seed")
    depth = _validate_halo_depth(halo_depth)
    grid = _input(seed, "test", 3)
    correct_bbox = gray_bbox(grid)
    wrong_bbox = (correct_bbox[0] + 1, correct_bbox[1], correct_bbox[2] - 1, correct_bbox[3])
    return {
        "step_a": STEP_A,
        "intermediate": INTERMEDIATE,
        "step_b": STEP_B,
        "why_b_depends_on_a": WHY_B_DEPENDS_ON_A,
        "input": grid,
        "settings": {"halo_depth": depth},
        "correct_intermediate": list(correct_bbox),
        "wrong_intermediate": list(wrong_bbox),
        "program": program_for(depth),
        "counterfactual_program": _counterfactual_program(depth),
        "output": _apply_with_bbox(grid, depth, correct_bbox),
        "counterfactual_output": _apply_with_bbox(grid, depth, wrong_bbox),
        "ablation": "wrong_intermediate",
    }
