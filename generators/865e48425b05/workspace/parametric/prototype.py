"""Parametric packing-axis family for palette-mask multiplication.

The canonical ``horizontal`` setting returns the selected Racket authority
byte-for-byte. ``vertical`` stacks the recolored mask copies top-to-bottom.
``dominant_axis`` first crops the color-1 mask, measures its bounding box, and
then packs copies horizontally for a wide mask or vertically for a tall mask.
The sampler deliberately uses non-square masks, so two demonstrations (one wide,
one tall) identify all three settings without relying on query answers.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Iterable

HERE = Path(__file__).resolve().parent
TASK_ID = "865e48425b05"
POLICIES = ("horizontal", "vertical", "dominant_axis")
SETTINGS = tuple({"layout_policy": value} for value in POLICIES)
DEFAULT = {"layout_policy": "horizontal"}
CANONICAL_PROGRAM = (HERE / "canonical.rkt").read_text(encoding="utf-8")
_LIMIT = 2**63 - 1
_COLORS = (2, 3, 4, 5, 6, 7, 8, 9)

# canvas_h, canvas_w, mask_h, mask_w, palette_count, placement
_DEMO_PROFILES = (
    (14, 12, 4, 6, 4, "bottom_left"),   # wide mask in a tall canvas
    (11, 18, 6, 4, 4, "top_right"),     # tall mask in a wide canvas
    (16, 18, 5, 8, 3, "center"),
    (18, 16, 8, 5, 3, "bottom_right"),
    (22, 24, 6, 9, 3, "top_left"),
    (24, 22, 9, 6, 3, "bottom_left"),
)
_QUERY_PROFILES = (
    (18, 16, 5, 8, 3, "top_right"),
    (16, 24, 8, 5, 3, "bottom_left"),
    (22, 26, 5, 6, 4, "center"),
    # Query 3 is replaced by a seed-dependent 30x30 12x14/14x12 stress case.
    (30, 30, 12, 14, 2, "bottom_right"),
)


def _integer(name: str, value: object, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be a literal integer in {low}..{high}")
    return value


def _policy(settings: object) -> str:
    if (
        type(settings) is not dict
        or set(settings) != {"layout_policy"}
        or type(settings["layout_policy"]) is not str
        or settings["layout_policy"] not in POLICIES
    ):
        raise ValueError(
            "settings must be exactly {'layout_policy': "
            "'horizontal'|'vertical'|'dominant_axis'}"
        )
    return settings["layout_policy"]


def _program_template(
    axis: str,
    *,
    gap: int = 1,
    solid: bool = False,
    reverse_palette: bool = False,
) -> str:
    if axis == "horizontal":
        horizontal_expr = "#t"
    elif axis == "vertical":
        horizontal_expr = "#f"
    elif axis == "dominant_axis":
        horizontal_expr = "(>= (cols mask) (rows mask))"
    elif axis == "minor_axis":
        horizontal_expr = "(< (cols mask) (rows mask))"
    elif axis == "canvas_axis":
        horizontal_expr = "(>= (cols g) (rows g))"
    else:  # pragma: no cover - internal guard
        raise ValueError(axis)
    palette_expr = "(reverse raw-palette)" if reverse_palette else "raw-palette"
    mask_expr = (
        "(grid-from-fn (+ (- (third bb) (first bb)) 1)\n"
        "                             (+ (- (fourth bb) (second bb)) 1)\n"
        "                 (lambda (r c) 1))"
        if solid
        else
        "(grid-from-fn (+ (- (third bb) (first bb)) 1)\n"
        "                             (+ (- (fourth bb) (second bb)) 1)\n"
        "                 (lambda (r c)\n"
        "                   (if (= (at g (+ (first bb) r) (+ (second bb) c)) 1) 1 0)))"
    )
    return f"""(rule!
  (let* ((raw-palette (filter (lambda (v) (not (= v 0))) (row g 0)))
         (palette {palette_expr})
         (bb (bbox-of-cells (find-color g 1)))
         (mask {mask_expr}))
    (define copies
      (map (lambda (color)
             (grid-from-fn (rows mask) (cols mask)
               (lambda (r c) (if (= (at mask r c) 1) color 0))))
           palette))
    (define horizontal? {horizontal_expr})
    (if horizontal?
        (let* ((out-h (rows mask))
               (out-w (+ (apply + (map cols copies)) (* {gap} (max 0 (- (length copies) 1))))))
          (let pack ([remaining copies] [left 0] [out (empty-grid out-h out-w 0)])
            (if (empty? remaining)
                out
                (let* ((p (first remaining))
                       (next (for*/fold ([acc out])
                                         ([r (in-range (rows p))]
                                          [c (in-range (cols p))])
                               (let ((v (at p r c)))
                                 (if (not (= v 0)) (set-cell acc r (+ left c) v) acc)))))
                  (pack (rest remaining) (+ left (cols p) {gap}) next)))))
        (let* ((out-h (+ (apply + (map rows copies)) (* {gap} (max 0 (- (length copies) 1)))))
               (out-w (cols mask)))
          (let pack ([remaining copies] [top 0] [out (empty-grid out-h out-w 0)])
            (if (empty? remaining)
                out
                (let* ((p (first remaining))
                       (next (for*/fold ([acc out])
                                         ([r (in-range (rows p))]
                                          [c (in-range (cols p))])
                               (let ((v (at p r c)))
                                 (if (not (= v 0)) (set-cell acc (+ top r) c v) acc)))))
                  (pack (rest remaining) (+ top (rows p) {gap}) next))))))))"""


VERTICAL_PROGRAM = _program_template("vertical")
DOMINANT_PROGRAM = _program_template("dominant_axis")


def program(settings: object) -> str:
    policy = _policy(settings)
    if policy == "horizontal":
        return CANONICAL_PROGRAM
    if policy == "vertical":
        return VERTICAL_PROGRAM
    return DOMINANT_PROGRAM


def _literal_grid(grid: object, *, minimum_rows: int = 1) -> list[list[int]]:
    if (
        type(grid) is not list
        or not minimum_rows <= len(grid) <= 30
        or type(grid[0]) is not list
        or not 1 <= len(grid[0]) <= 30
    ):
        raise ValueError("grid must be a nonempty 1..30 rectangular integer array")
    width = len(grid[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(value) is not int or not 0 <= value <= 9 for value in row)
        for row in grid
    ):
        raise ValueError("grid must be rectangular with exact ARC colors 0..9")
    return deepcopy(grid)


def _grid(grid: object) -> list[list[int]]:
    source = _literal_grid(grid, minimum_rows=3)
    palette = [value for value in source[0] if value != 0]
    if not 2 <= len(palette) <= 4 or len(set(palette)) != len(palette):
        raise ValueError("row 0 must contain 2..4 distinct nonzero palette colors")
    if any(value not in _COLORS and value != 0 for value in source[0]):
        raise ValueError("row-0 palette colors must be 2..9")
    if any(source[1]):
        raise ValueError("row 1 must be an empty separator")
    if any(value not in (0, 1) for row in source[2:] for value in row):
        raise ValueError("below the separator only background and color 1 are allowed")
    cells = {(r, c) for r in range(2, len(source)) for c, value in enumerate(source[r]) if value == 1}
    if not cells:
        raise ValueError("input needs a nonempty color-1 mask")
    remaining = set(cells)
    stack = [remaining.pop()]
    while stack:
        r, c = stack.pop()
        for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if neighbor in remaining:
                remaining.remove(neighbor)
                stack.append(neighbor)
    if remaining:
        raise ValueError("color-1 mask must be 4-connected")
    return source


def _palette(grid: list[list[int]]) -> list[int]:
    return [value for value in grid[0] if value != 0]


def _normalized_mask(grid: list[list[int]]) -> tuple[set[tuple[int, int]], int, int]:
    cells = {(r, c) for r in range(2, len(grid)) for c, value in enumerate(grid[r]) if value == 1}
    top = min(r for r, _ in cells)
    bottom = max(r for r, _ in cells)
    left = min(c for _, c in cells)
    right = max(c for _, c in cells)
    return {(r - top, c - left) for r, c in cells}, bottom - top + 1, right - left + 1


def analyze(grid: object) -> dict[str, Any]:
    source = _grid(grid)
    mask, height, width = _normalized_mask(source)
    return {
        "palette": _palette(source),
        "mask": sorted([list(cell) for cell in mask]),
        "mask_height": height,
        "mask_width": width,
        "dominant_axis": "horizontal" if width >= height else "vertical",
    }


def _pack(
    mask: Iterable[tuple[int, int]],
    height: int,
    width: int,
    palette: list[int],
    axis: str,
    *,
    gap: int = 1,
    solid: bool = False,
    reverse_palette: bool = False,
) -> list[list[int]]:
    cells = set(mask)
    if solid:
        cells = {(r, c) for r in range(height) for c in range(width)}
    colors = list(reversed(palette)) if reverse_palette else list(palette)
    if axis == "horizontal":
        out_h = height
        out_w = len(colors) * width + max(0, len(colors) - 1) * gap
        out = [[0] * out_w for _ in range(out_h)]
        for index, color in enumerate(colors):
            left = index * (width + gap)
            for r, c in cells:
                out[r][left + c] = color
    elif axis == "vertical":
        out_h = len(colors) * height + max(0, len(colors) - 1) * gap
        out_w = width
        out = [[0] * out_w for _ in range(out_h)]
        for index, color in enumerate(colors):
            top = index * (height + gap)
            for r, c in cells:
                out[top + r][c] = color
    else:  # pragma: no cover - internal guard
        raise ValueError(axis)
    if not (1 <= len(out) <= 30 and 1 <= len(out[0]) <= 30):
        raise ValueError(f"output shape {len(out)}x{len(out[0])} exceeds ARC bounds")
    return out


def _axis_for(policy: str, analysis: dict[str, Any]) -> str:
    if policy == "horizontal":
        return "horizontal"
    if policy == "vertical":
        return "vertical"
    return analysis["dominant_axis"]


def solve(grid: object, settings: object) -> list[list[int]]:
    policy = _policy(settings)
    source = _grid(grid)
    info = analyze(source)
    return _pack(
        [tuple(cell) for cell in info["mask"]],
        info["mask_height"],
        info["mask_width"],
        info["palette"],
        _axis_for(policy, info),
    )


def dependency_trace(grid: object, settings: object) -> dict[str, Any]:
    policy = _policy(settings)
    info = analyze(grid)
    return {
        "step_a": "crop the color-1 mask and measure its bbox",
        "intermediate": {
            "mask_height": info["mask_height"],
            "mask_width": info["mask_width"],
            "dominant_axis": info["dominant_axis"],
        },
        "step_b": "pack recolored copies along the selected axis",
        "selected_axis": _axis_for(policy, info),
        "why_b_depends_on_a": (
            "dominant_axis cannot choose horizontal versus vertical packing until "
            "the cropped mask dimensions are known"
        ),
    }


def _rival_solve(grid: object, settings: object, rival: str) -> list[list[int]]:
    policy = _policy(settings)
    source = _grid(grid)
    info = analyze(source)
    mask = [tuple(cell) for cell in info["mask"]]
    axis = _axis_for(policy, info)
    if rival == "minor_axis":
        axis = "vertical" if info["dominant_axis"] == "horizontal" else "horizontal"
    elif rival == "canvas_axis":
        axis = "horizontal" if len(source[0]) >= len(source) else "vertical"
    return _pack(
        mask,
        info["mask_height"],
        info["mask_width"],
        info["palette"],
        axis,
        gap=0 if rival == "no_gap" else 1,
        solid=rival == "solid_bbox",
        reverse_palette=rival == "reverse_palette",
    )


def rival_programs(settings: object) -> dict[str, str]:
    policy = _policy(settings)
    rivals = {
        f"setting_{other}": program({"layout_policy": other})
        for other in POLICIES
        if other != policy
    }
    rivals.update(
        {
            "minor_axis": _program_template("minor_axis"),
            "canvas_axis": _program_template("canvas_axis"),
            "no_gap": _program_template(policy if policy != "dominant_axis" else "dominant_axis", gap=0),
            "solid_bbox": _program_template(policy if policy != "dominant_axis" else "dominant_axis", solid=True),
            "reverse_palette": _program_template(
                policy if policy != "dominant_axis" else "dominant_axis",
                reverse_palette=True,
            ),
        }
    )
    return rivals


def rival_outputs(grid: object, settings: object) -> dict[str, list[list[int]]]:
    policy = _policy(settings)
    outputs = {
        f"setting_{other}": solve(grid, {"layout_policy": other})
        for other in POLICIES
        if other != policy
    }
    outputs.update(
        {
            name: _rival_solve(grid, settings, name)
            for name in ("minor_axis", "canvas_axis", "no_gap", "solid_bbox", "reverse_palette")
        }
    )
    return outputs


def _rng(seed: int, split: str, index: int) -> random.Random:
    digest = hashlib.sha256(
        f"{TASK_ID}:layout-policy-input-v1:{seed}:{split}:{index}".encode()
    ).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _palette_values(rng: random.Random, count: int) -> list[int]:
    colors = sorted(rng.sample(list(_COLORS), count))
    if count == 2:
        return colors[::-1]
    if count == 3:
        return [colors[2], colors[0], colors[1]]
    return [colors[2], colors[0], colors[3], colors[1]]


def _palette_columns(width: int, count: int) -> list[int]:
    if count == 2:
        return [0, width - 1]
    return [round(index * (width - 1) / (count - 1)) for index in range(count)]


def _comb_mask(height: int, width: int, rng: random.Random) -> set[tuple[int, int]]:
    if not (3 <= height <= 14 and 3 <= width <= 14 and height != width):
        raise ValueError("mask profiles must be unequal 3..14 rectangles")
    cells = {
        (r, c)
        for r in range(height)
        for c in range(width)
        if r in (0, height - 1) or c in (0, width - 1)
    }
    parity = rng.randrange(2)
    for c in range(1, width - 1):
        if c % 2 != parity:
            continue
        depth = 1 + rng.randrange(height - 2)
        for r in range(1, depth + 1):
            cells.add((r, c))
    # A side branch varies the interior without threatening connectivity.
    branch_row = 1 + rng.randrange(height - 2)
    branch_len = 1 + rng.randrange(max(1, width - 2))
    for c in range(1, min(width - 1, branch_len + 1)):
        cells.add((branch_row, c))
    return cells


def _placement(
    canvas_h: int,
    canvas_w: int,
    mask_h: int,
    mask_w: int,
    placement: str,
) -> tuple[int, int]:
    if mask_h > canvas_h - 2 or mask_w > canvas_w:
        raise ValueError("mask does not fit canvas")
    if placement == "bottom_left":
        return canvas_h - mask_h, 0
    if placement == "top_right":
        return 2, canvas_w - mask_w
    if placement == "bottom_right":
        return canvas_h - mask_h, canvas_w - mask_w
    if placement == "top_left":
        return 2, 0
    if placement == "center":
        return 2 + (canvas_h - 2 - mask_h) // 2, (canvas_w - mask_w) // 2
    raise ValueError(placement)


def _profile(seed: int, split: str, index: int) -> tuple[int, int, int, int, int, str]:
    profiles = _DEMO_PROFILES if split == "train" else _QUERY_PROFILES
    profile = profiles[index]
    if split == "test" and index == 3 and seed % 2 == 0:
        canvas_h, canvas_w, mask_h, mask_w, colors, placement = profile
        return canvas_h, canvas_w, mask_w, mask_h, colors, placement
    return profile


def sample_input(seed: int, split: str, index: int) -> list[list[int]]:
    _integer("seed", seed, 0, _LIMIT)
    if split not in ("train", "test"):
        raise ValueError("split must be 'train' or 'test'")
    maximum = len(_DEMO_PROFILES) - 1 if split == "train" else len(_QUERY_PROFILES) - 1
    _integer("index", index, 0, maximum)
    canvas_h, canvas_w, mask_h, mask_w, color_count, placement = _profile(seed, split, index)
    rng = _rng(seed, split, index)
    grid = [[0] * canvas_w for _ in range(canvas_h)]
    for column, color in zip(
        _palette_columns(canvas_w, color_count),
        _palette_values(rng, color_count),
        strict=True,
    ):
        grid[0][column] = color
    top, left = _placement(canvas_h, canvas_w, mask_h, mask_w, placement)
    for r, c in _comb_mask(mask_h, mask_w, rng):
        grid[top + r][left + c] = 1
    _grid(grid)
    # All settings must remain inside the 30x30 output bound.
    for policy in POLICIES:
        solve(grid, {"layout_policy": policy})
    return grid


def teaching_check(episode: object) -> dict[str, Any]:
    if type(episode) is not dict:
        raise ValueError("episode must be an object")
    settings = episode.get("settings")
    _policy(settings)
    train = episode.get("train")
    if type(train) is not list or len(train) < 2:
        raise ValueError("episode needs at least two demonstrations")
    refuted = {name: None for name in rival_programs(settings)}
    for index, pair in enumerate(train):
        if type(pair) is not dict or not {"input", "output"} <= set(pair):
            raise ValueError("demonstrations require input/output grids")
        expected = solve(pair["input"], settings)
        if _literal_grid(pair["output"]) != expected:
            raise ValueError("demonstration label differs from selected rule")
        for name, value in rival_outputs(pair["input"], settings).items():
            if refuted[name] is None and value != expected:
                refuted[name] = index
    surviving = sorted(name for name, index in refuted.items() if index is None)
    return {
        "status": "identified" if not surviving else "ambiguous",
        "surviving_rivals": surviving,
        "refuted_by": {name: index for name, index in refuted.items() if index is not None},
        "demonstrations": len(train),
        "used_query_answers": False,
        "limits": "Finite named rivals fitted to demonstrations only; not universal uniqueness.",
    }


def generate(seed: int, settings: object, demos: int = 3, queries: int = 4) -> dict[str, Any]:
    _integer("seed", seed, 0, _LIMIT)
    _policy(settings)
    _integer("demos", demos, 2, 6)
    _integer("queries", queries, 1, 4)
    train = []
    for index in range(demos):
        grid = sample_input(seed, "train", index)
        train.append({"input": grid, "output": solve(grid, settings)})
    test = []
    for index in range(queries):
        grid = sample_input(seed, "test", index)
        test.append({"input": grid, "output": solve(grid, settings)})
    fingerprints = [
        json.dumps(pair["input"], separators=(",", ":"))
        for pair in train + test
    ]
    if len(fingerprints) != len(set(fingerprints)):
        raise RuntimeError("constructed episode contains duplicate inputs")
    episode = {
        "task_id": TASK_ID,
        "seed": seed,
        "settings": deepcopy(settings),
        "train": train,
        "test": test,
        "program_solution": program(settings),
        "sampling": {"draws": demos + queries, "duplicate_rejections": 0},
    }
    certificate = teaching_check(episode)
    if certificate["surviving_rivals"]:
        raise RuntimeError(
            "constructed demonstrations leave declared rivals alive: "
            + ", ".join(certificate["surviving_rivals"])
        )
    episode["teaching"] = certificate
    return episode


def public_turn(episode: object, query_index: object = 0) -> dict[str, Any]:
    if type(episode) is not dict or type(episode.get("train")) is not list or type(episode.get("test")) is not list:
        raise ValueError("episode must contain train/test lists")
    test = episode["test"]
    _integer("query_index", query_index, 0, len(test) - 1)
    try:
        query = {"input": deepcopy(test[query_index]["input"])}
        if query_index == 0:
            train = [
                {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
                for pair in episode["train"]
            ]
            return {"train": train, "test": [query]}
        return {"test": [query]}
    except (KeyError, TypeError) as error:
        raise ValueError("episode pairs require valid grids") from error


__all__ = [
    "CANONICAL_PROGRAM",
    "DEFAULT",
    "POLICIES",
    "SETTINGS",
    "analyze",
    "dependency_trace",
    "generate",
    "program",
    "public_turn",
    "rival_outputs",
    "rival_programs",
    "sample_input",
    "solve",
    "teaching_check",
]
