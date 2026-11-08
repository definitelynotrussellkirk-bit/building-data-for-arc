"""Proposed episode-level rule parameters for task 8d7d1364cf11.

This module is intentionally separate from the selected canonical generator.
Two small settings preserve the source-template/dot matching structure while
varying (1) which source coordinate is aligned to a productive dot and (2)
whether the output canvas starts clear or preserves the input.  Both values are
chosen once per episode and held fixed across every demonstration and query.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from reviewer_support import find_root, load_selected_generator

TASK_ID = "8d7d1364cf11"
PROTOTYPE_VERSION = "1.0.0"
PARAMETERS = {
    "anchor_mode": ("matching_cell", "template_origin"),
    "canvas_mode": ("clear", "preserve_input"),
}
SETTING_IDS = tuple(
    f"{anchor}__{canvas}"
    for anchor in PARAMETERS["anchor_mode"]
    for canvas in PARAMETERS["canvas_mode"]
)
DEFAULT_SETTING = "matching_cell__clear"
_BANDS = ("easy", "medium", "hard")
_BG = 4

CANONICAL_PROGRAM = '(rule! (lambda (g)\n         (let ((h (rows g))\n               (w (cols g))\n               (bg 4))\n           (let ((comps (objects-multicolor g bg)))\n             (let ((shapes (filter (lambda (o) (> (obj-size o) 1)) comps))\n                   (dots (filter (lambda (o) (= (obj-size o) 1)) comps)))\n               (let ((shape-cells (flatmap (lambda (s)\n                                             (map (lambda (cell) (list s cell))\n                                                  (obj-cells s)))\n                                           shapes)))\n                 (reduce (lambda (acc dot)\n                           (let ((dp (fst (obj-cells dot)))\n                                 (dc (at g\n                                         (fst (fst (obj-cells dot)))\n                                         (snd (fst (obj-cells dot))))))\n                             (let ((matches (filter (lambda (m)\n                                                      (= (at g\n                                                             (fst (snd m))\n                                                             (snd (snd m)))\n                                                         dc))\n                                                    shape-cells)))\n                               (if (empty? matches)\n                                   acc\n                                   (let ((tmpl (fst (first matches)))\n                                         (anchor (snd (first matches))))\n                                     (let ((dr (- (fst dp) (fst anchor)))\n                                           (dcc (- (snd dp) (snd anchor))))\n                                       (reduce (lambda (a cell)\n                                                 (let ((nr (+ (fst cell) dr))\n                                                       (nc (+ (snd cell) dcc)))\n                                                   (if (in-bounds? nr nc h w)\n                                                       (set-cell a\n                                                                 nr\n                                                                 nc\n                                                                 (at g\n                                                                     (fst cell)\n                                                                     (snd cell)))\n                                                       a)))\n                                               acc\n                                               (obj-cells tmpl))))))))\n                         (grid-from-fn h w (lambda (r c) bg))\n                         dots)))))))'
_ANCHOR_NEEDLE = "(anchor (snd (first matches)))"
_ORIGIN_ANCHOR = """(anchor (let ((bb (obj-bbox (fst (first matches)))))
                                         (list (first bb) (second bb))))"""
_CANVAS_NEEDLE = "(grid-from-fn h w (lambda (r c) bg))"


def _validate_setting(setting: Any) -> str:
    if setting not in SETTING_IDS:
        raise ValueError(f"setting must be one of {SETTING_IDS}, found {setting!r}")
    return str(setting)


def parameters_for(setting: str) -> dict[str, str]:
    setting = _validate_setting(setting)
    anchor, canvas = setting.split("__", 1)
    return {"anchor_mode": anchor, "canvas_mode": canvas}


def choose_setting(seed: int) -> str:
    """Choose one hidden rule setting deterministically for a whole episode."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    return SETTING_IDS[seed % len(SETTING_IDS)]


def program_for(setting: str) -> str:
    """Materialize the exact Racket program for one bounded setting."""
    params = parameters_for(setting)
    source = CANONICAL_PROGRAM
    if params["anchor_mode"] == "template_origin":
        if source.count(_ANCHOR_NEEDLE) != 1:
            raise RuntimeError("canonical anchor form changed")
        source = source.replace(_ANCHOR_NEEDLE, _ORIGIN_ANCHOR)
    if params["canvas_mode"] == "preserve_input":
        if source.count(_CANVAS_NEEDLE) != 1:
            raise RuntimeError("canonical canvas form changed")
        source = source.replace(_CANVAS_NEEDLE, "g")
    return source


def _validate_grid(grid: Any) -> tuple[int, int]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("grid must be a nonempty rectangular list")
    width = len(grid[0])
    for row in grid:
        if not isinstance(row, list) or len(row) != width:
            raise ValueError("grid must be rectangular")
        if any(type(value) is not int or not 0 <= value <= 9 for value in row):
            raise ValueError("grid values must be ARC colors 0..9")
    return len(grid), width


def _components(grid: list[list[int]]) -> list[tuple[tuple[int, int, int], ...]]:
    """Return row-major 8-connected non-background multicolor objects."""
    height, width = _validate_grid(grid)
    seen: set[tuple[int, int]] = set()
    result: list[tuple[tuple[int, int, int], ...]] = []
    for start_r in range(height):
        for start_c in range(width):
            if grid[start_r][start_c] == _BG or (start_r, start_c) in seen:
                continue
            stack = [(start_r, start_c)]
            seen.add((start_r, start_c))
            cells: list[tuple[int, int, int]] = []
            while stack:
                row, col = stack.pop()
                cells.append((row, col, grid[row][col]))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == dc == 0:
                            continue
                        nr, nc = row + dr, col + dc
                        if (
                            0 <= nr < height
                            and 0 <= nc < width
                            and grid[nr][nc] != _BG
                            and (nr, nc) not in seen
                        ):
                            seen.add((nr, nc))
                            stack.append((nr, nc))
            result.append(tuple(sorted(cells)))
    return result


def _scene(grid: list[list[int]]) -> tuple[
    list[tuple[tuple[int, int, int], ...]],
    list[tuple[int, int, int]],
    dict[int, list[tuple[int, int, int]]],
]:
    components = _components(grid)
    shapes = [component for component in components if len(component) > 1]
    dots = [component[0] for component in components if len(component) == 1]
    matches: dict[int, list[tuple[int, int, int]]] = {}
    for shape_index, shape in enumerate(shapes):
        for row, col, color in shape:
            matches.setdefault(color, []).append((shape_index, row, col))
    return shapes, dots, matches


def apply_python(grid: list[list[int]], setting: str) -> list[list[int]]:
    """Independent Python mirror used only for authoring and tests."""
    params = parameters_for(setting)
    height, width = _validate_grid(grid)
    shapes, dots, matches = _scene(grid)
    if params["canvas_mode"] == "clear":
        output = [[_BG for _ in range(width)] for _ in range(height)]
    else:
        output = deepcopy(grid)

    for dot_r, dot_c, color in dots:
        found = matches.get(color, [])
        if not found:
            continue
        shape_index, match_r, match_c = found[0]
        shape = shapes[shape_index]
        if params["anchor_mode"] == "matching_cell":
            anchor_r, anchor_c = match_r, match_c
        else:
            anchor_r = min(row for row, _col, _value in shape)
            anchor_c = min(col for _row, col, _value in shape)
        dr, dc = dot_r - anchor_r, dot_c - anchor_c
        for row, col, value in shape:
            nr, nc = row + dr, col + dc
            if 0 <= nr < height and 0 <= nc < width:
                output[nr][nc] = value
    return output


def _pairwise_distinguishing(grid: list[list[int]]) -> bool:
    outputs = {
        setting: tuple(tuple(row) for row in apply_python(grid, setting))
        for setting in SETTING_IDS
    }
    return len(set(outputs.values())) == len(SETTING_IDS)


def build_episode(
    seed: int,
    *,
    setting: str | None = None,
    n_train: int = 3,
    n_test: int = 1,
) -> dict[str, Any]:
    """Build a complete episode with one fixed hidden setting."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(n_train) is not int or n_train < 1:
        raise ValueError("n_train must be a positive integer")
    if type(n_test) is not int or n_test < 1:
        raise ValueError("n_test must be a positive integer")
    selected = choose_setting(seed) if setting is None else _validate_setting(setting)

    root = find_root(__file__)
    generator, source_path, source_sha256 = load_selected_generator(TASK_ID, root=root)
    pairs: list[dict[str, Any]] = []
    candidate = 0
    needed = n_train + n_test
    while len(pairs) < needed and candidate < 512:
        band = _BANDS[candidate % len(_BANDS)]
        grid = generator.generate(
            seed,
            candidate,
            difficulty=band,
            n_shapes=3,
            copies_per_shape=2,
            n_decoy_dots=2,
        )
        if _pairwise_distinguishing(grid):
            pairs.append(
                {
                    "input": grid,
                    "output": apply_python(grid, selected),
                    "sampling": {
                        "seed": seed,
                        "sample_index": candidate,
                        "difficulty": band,
                        "overrides": {
                            "n_shapes": 3,
                            "copies_per_shape": 2,
                            "n_decoy_dots": 2,
                        },
                    },
                }
            )
        candidate += 1
    if len(pairs) != needed:
        raise RuntimeError(f"found only {len(pairs)} pairwise-distinguishing inputs")

    return {
        "schema": "8d7d1364cf11-parametric-episode-v1",
        "prototype_version": PROTOTYPE_VERSION,
        "task_id": TASK_ID,
        "setting_id": selected,
        "parameters": parameters_for(selected),
        "program": program_for(selected),
        "generator_source": str(source_path.relative_to(root)),
        "generator_sha256": source_sha256,
        "train": pairs[:n_train],
        "test": pairs[n_train:],
    }


def episode_errors(episode: Any) -> list[str]:
    """Validate setting constancy, labels, and declared-rival identifiability."""
    if not isinstance(episode, dict):
        return ["episode must be a mapping"]
    try:
        setting = _validate_setting(episode.get("setting_id"))
    except ValueError as exc:
        return [str(exc)]
    if episode.get("parameters") != parameters_for(setting):
        return ["episode parameters do not match setting_id"]
    if episode.get("program") != program_for(setting):
        return ["episode program does not match setting_id"]

    train, test = episode.get("train"), episode.get("test")
    if not isinstance(train, list) or not train:
        return ["episode needs at least one training pair"]
    if not isinstance(test, list) or not test:
        return ["episode needs at least one test pair"]

    errors: list[str] = []
    for split_name, pairs in (("train", train), ("test", test)):
        for index, pair in enumerate(pairs):
            if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
                errors.append(f"{split_name}[{index}] must contain input and output")
                continue
            try:
                expected = apply_python(pair["input"], setting)
            except (TypeError, ValueError) as exc:
                errors.append(f"{split_name}[{index}] invalid: {exc}")
                continue
            if pair["output"] != expected:
                errors.append(f"{split_name}[{index}] output disagrees with selected setting")
            if split_name == "train":
                for rival in SETTING_IDS:
                    if rival != setting and apply_python(pair["input"], rival) == expected:
                        errors.append(
                            f"{split_name}[{index}] does not distinguish rival {rival}"
                        )
    return errors


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Remove hidden rule values, exact program, and query answers."""
    errors = episode_errors(episode)
    if errors:
        raise ValueError("invalid episode: " + "; ".join(errors))
    return {
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": deepcopy(pair["input"])} for pair in episode["test"]],
    }
