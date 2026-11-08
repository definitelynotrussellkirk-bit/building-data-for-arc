"""Native finite parametric family for ARC generator e3f1bc75d654.

The default ``target_basis=template_interior`` is the exact canonical rule:
find the sole patterned template, keep every frame with the same interior size,
and copy the template pattern at its original relative coordinates.

The nearby ``target_basis=pattern_bbox`` setting adds a real input-dependent
composition. Step A finds the template pattern and derives its minimal bounding
box plus normalized crop. Step B uses those derived dimensions to select a
separate empty frame, then stamps the normalized crop there. The target cannot
be selected before Step A has produced the bounding-box dimensions.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Callable


TASK_ID = "e3f1bc75d654"
PARAMETER_NAME = "target_basis"
TARGET_BASES = ("template_interior", "pattern_bbox")
DEFAULT_SETTINGS = {PARAMETER_NAME: "template_interior"}
SHORTCUTS = (
    "template_extent_crop",
    "transposed_bbox",
    "bbox_area_only",
    "bbox_horizontal_flip",
    "bbox_union_template",
    "unnormalized_pattern",
)

_HOME = Path(__file__).resolve().parent
CANONICAL_PROGRAM = (_HOME / "canonical.rkt").read_text(encoding="utf-8")
PATTERN_BBOX_PROGRAM = (_HOME / "pattern-bbox.rkt").read_text(encoding="utf-8")

# Six stable demonstration slots and four stable query slots. Requested counts
# select prefixes independently, so query inputs never move when demo count does.
_DEMO_PROFILES = (
    {"grid": (20, 24), "template": (4, 5), "crop": (2, 3), "anchor": "br", "extra": (1, 4)},
    {"grid": (21, 26), "template": (5, 4), "crop": (3, 2), "anchor": "tr", "extra": (1, 5)},
    {"grid": (22, 26), "template": (5, 5), "crop": (2, 4), "anchor": "bl", "extra": (1, 3)},
    {"grid": (24, 29), "template": (6, 5), "crop": (3, 4), "anchor": "br", "extra": (2, 5)},
    {"grid": (25, 29), "template": (5, 6), "crop": (4, 2), "anchor": "tr", "extra": (1, 5)},
    {"grid": (27, 29), "template": (6, 6), "crop": (2, 5), "anchor": "bl", "extra": (3, 3)},
)
_QUERY_PROFILES = (
    {"grid": (20, 26), "template": (4, 6), "crop": (2, 4), "anchor": "tr", "extra": (1, 3)},
    {"grid": (23, 27), "template": (6, 4), "crop": (3, 2), "anchor": "bl", "extra": (1, 5)},
    {"grid": (26, 29), "template": (5, 6), "crop": (3, 5), "anchor": "br", "extra": (2, 2)},
    {"grid": (30, 30), "template": (6, 6), "crop": (4, 3), "anchor": "tr", "extra": (1, 6)},
)

_TARGET_H = "                  (target-h crop-h)"
_TARGET_W = "                  (target-w crop-w)"
_SELECTOR = "                          (and (= ih target-h) (= iw target-w))"
_TARGET_DR = "                            (let ((target-dr (- (first cell) p-rmin))"
_TARGET_DC = "                                  (target-dc (- (second cell) p-cmin)))"


def _validate_settings(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {PARAMETER_NAME}:
        raise ValueError(f"settings must contain exactly {PARAMETER_NAME}")
    value = settings[PARAMETER_NAME]
    if type(value) is not str or value not in TARGET_BASES:
        raise ValueError(f"{PARAMETER_NAME} must be one of {TARGET_BASES}")
    return value


def _exact_int(value: Any, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def program(settings: Any) -> str:
    basis = _validate_settings(settings)
    return CANONICAL_PROGRAM if basis == "template_interior" else PATTERN_BBOX_PROGRAM


def _guarded_replace(source: str, old: str, new: str) -> str:
    if source.count(old) != 1:
        raise ValueError(f"Racket source guard failed for {old!r}")
    return source.replace(old, new, 1)


def counterfactual_program(kind: str = "template_extent") -> str:
    """Return a protected-Racket wrong-intermediate program for causal replay."""
    if kind != "template_extent":
        raise ValueError("only template_extent is a retained counterfactual")
    source = _guarded_replace(PATTERN_BBOX_PROGRAM, _TARGET_H, "                  (target-h t-ih)")
    return _guarded_replace(source, _TARGET_W, "                  (target-w t-iw)")


def rival_programs() -> dict[str, str]:
    """Materialize six executable nearby rules used by the bounded self-audit."""
    programs: dict[str, str] = {}
    programs["template_extent_crop"] = counterfactual_program()

    source = _guarded_replace(PATTERN_BBOX_PROGRAM, _TARGET_H, "                  (target-h crop-w)")
    programs["transposed_bbox"] = _guarded_replace(
        source, _TARGET_W, "                  (target-w crop-h)"
    )
    programs["bbox_area_only"] = _guarded_replace(
        PATTERN_BBOX_PROGRAM,
        _SELECTOR,
        "                          (= (* ih iw) (* target-h target-w))",
    )
    programs["bbox_horizontal_flip"] = _guarded_replace(
        PATTERN_BBOX_PROGRAM,
        _TARGET_DC,
        "                                  (target-dc (- crop-w 1 (- (second cell) p-cmin))))",
    )
    programs["bbox_union_template"] = _guarded_replace(
        PATTERN_BBOX_PROGRAM,
        _SELECTOR,
        "                          (or (and (= ih target-h) (= iw target-w))\n"
        "                              (and (= ih t-ih) (= iw t-iw)))",
    )
    source = _guarded_replace(
        PATTERN_BBOX_PROGRAM,
        _TARGET_DR,
        "                            (let ((target-dr (first cell))",
    )
    programs["unnormalized_pattern"] = _guarded_replace(
        source,
        _TARGET_DC,
        "                                  (target-dc (second cell)))",
    )
    return programs


def _validate_grid(grid: Any) -> list[list[int]]:
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


def _boxes_touch(left: tuple[int, int, int, int], right: tuple[int, int, int, int]) -> bool:
    lr0, lc0, lr1, lc1 = left
    rr0, rc0, rr1, rc1 = right
    rows_separated = lr1 + 1 < rr0 or rr1 + 1 < lr0
    cols_separated = lc1 + 1 < rc0 or rc1 + 1 < lc0
    return not (rows_separated or cols_separated)


def analyze_scene(grid: Any) -> dict[str, Any]:
    """Parse the admitted frame grammar independently of the production analyzer."""
    grid = _validate_grid(grid)
    height, width = len(grid), len(grid[0])
    errors: list[str] = []
    by_color: dict[int, list[tuple[int, int]]] = {}
    for row, values in enumerate(grid):
        for col, color in enumerate(values):
            if color:
                by_color.setdefault(color, []).append((row, col))
    if not 3 <= len(by_color) <= 9:
        errors.append(f"expected 3..9 nonzero frame colors, found {len(by_color)}")

    frames: list[dict[str, Any]] = []
    for color, cells in sorted(by_color.items()):
        rows = [row for row, _ in cells]
        cols = [col for _, col in cells]
        r0, r1 = min(rows), max(rows)
        c0, c1 = min(cols), max(cols)
        frame_h, frame_w = r1 - r0 + 1, c1 - c0 + 1
        if frame_h < 3 or frame_w < 3:
            errors.append(f"color {color} has bbox {frame_h}x{frame_w}, not a frame")
            continue
        border = {
            (row, col)
            for row in range(r0, r1 + 1)
            for col in range(c0, c1 + 1)
            if row in (r0, r1) or col in (c0, c1)
        }
        if any(grid[row][col] != color for row, col in border):
            errors.append(f"color {color} has an incomplete frame border")
            continue
        foreign = [
            (row, col)
            for row in range(r0 + 1, r1)
            for col in range(c0 + 1, c1)
            if grid[row][col] not in (0, color)
        ]
        if foreign:
            errors.append(f"color {color} frame contains foreign interior cells")
            continue
        pattern = [
            (row - r0 - 1, col - c0 - 1)
            for row in range(r0 + 1, r1)
            for col in range(c0 + 1, c1)
            if grid[row][col] == color
        ]
        frames.append(
            {
                "color": color,
                "bbox": (r0, c0, r1, c1),
                "frame_h": frame_h,
                "frame_w": frame_w,
                "interior": (frame_h - 2, frame_w - 2),
                "pattern": pattern,
                "pattern_count": len(pattern),
            }
        )

    for index, left in enumerate(frames):
        for right in frames[index + 1 :]:
            if _boxes_touch(left["bbox"], right["bbox"]):
                errors.append(
                    f"frames {left['color']} and {right['color']} touch or overlap"
                )

    templates = [frame for frame in frames if frame["pattern_count"]]
    if len(templates) != 1:
        errors.append(f"expected exactly one patterned template, found {len(templates)}")
        return {
            "errors": errors,
            "grid_h": height,
            "grid_w": width,
            "frames": frames,
            "templates": templates,
        }
    template = templates[0]
    interior_h, interior_w = template["interior"]
    if template["pattern_count"] >= interior_h * interior_w:
        errors.append("template pattern must be non-solid")
    if not any(
        row in (0, interior_h - 1) or col in (0, interior_w - 1)
        for row, col in template["pattern"]
    ):
        errors.append("template pattern must touch the frame through an interior edge")
    matching = [frame for frame in frames if frame["interior"] == template["interior"]]
    distractors = [frame for frame in frames if frame["interior"] != template["interior"]]
    if not 2 <= len(matching) <= 4:
        errors.append(f"expected 2..4 template-size frames, found {len(matching)}")
    if not 1 <= len(distractors) <= 3:
        errors.append(f"expected 1..3 distractors, found {len(distractors)}")
    if any(frame is not template and frame["pattern_count"] for frame in frames):
        errors.append("only the template may contain an interior pattern")
    return {
        "errors": errors,
        "grid_h": height,
        "grid_w": width,
        "frames": frames,
        "templates": templates,
        "template": template,
        "matching": matching,
        "distractors": distractors,
    }


def pattern_bbox_intermediate(grid: list[list[int]]) -> dict[str, Any]:
    """Step A: derive the crop that Step B uses to select its receiver."""
    facts = analyze_scene(grid)
    if facts["errors"]:
        raise ValueError("invalid parametric scene: " + "; ".join(facts["errors"]))
    pattern = facts["template"]["pattern"]
    rows = [row for row, _ in pattern]
    cols = [col for _, col in pattern]
    row0, row1 = min(rows), max(rows)
    col0, col1 = min(cols), max(cols)
    crop_shape = (row1 - row0 + 1, col1 - col0 + 1)
    normalized = sorted((row - row0, col - col0) for row, col in pattern)
    targets = [frame for frame in facts["frames"] if frame["interior"] == crop_shape]
    return {
        "pattern_bbox": (row0, col0, row1, col1),
        "crop_shape": crop_shape,
        "normalized_pattern": normalized,
        "target_frames": targets,
    }


def _blank(height: int, width: int) -> list[list[int]]:
    return [[0 for _ in range(width)] for _ in range(height)]


def _draw_frame(
    grid: list[list[int]], r0: int, c0: int, r1: int, c1: int, color: int
) -> None:
    for col in range(c0, c1 + 1):
        grid[r0][col] = color
        grid[r1][col] = color
    for row in range(r0, r1 + 1):
        grid[row][c0] = color
        grid[row][c1] = color


def _render(
    grid: list[list[int]],
    selected: list[dict[str, Any]],
    cells: list[tuple[int, int]],
    *,
    flip_horizontal: bool = False,
    raw_offsets: bool = False,
) -> list[list[int]]:
    facts = analyze_scene(grid)
    output = _blank(facts["grid_h"], facts["grid_w"])
    width = max((col for _, col in cells), default=-1) + 1
    for frame in selected:
        r0, c0, r1, c1 = frame["bbox"]
        _draw_frame(output, r0, c0, r1, c1, frame["color"])
        for row, col in cells:
            target_row = row
            target_col = width - 1 - col if flip_horizontal else col
            if raw_offsets:
                target_row, target_col = row, col
            out_row, out_col = r0 + 1 + target_row, c0 + 1 + target_col
            if 0 <= out_row < len(output) and 0 <= out_col < len(output[0]):
                output[out_row][out_col] = frame["color"]
    return output


def transform(grid: list[list[int]], settings: Any) -> list[list[int]]:
    basis = _validate_settings(settings)
    facts = analyze_scene(grid)
    if facts["errors"]:
        raise ValueError("invalid parametric scene: " + "; ".join(facts["errors"]))
    if basis == "template_interior":
        return _render(grid, facts["matching"], list(facts["template"]["pattern"]))
    intermediate = pattern_bbox_intermediate(grid)
    if len(intermediate["target_frames"]) != 1:
        raise ValueError("pattern_bbox requires one unique crop-sized receiver")
    return _render(
        grid,
        intermediate["target_frames"],
        list(intermediate["normalized_pattern"]),
    )


def shortcut_output(grid: list[list[int]], shortcut: str) -> list[list[int]]:
    facts = analyze_scene(grid)
    if facts["errors"]:
        raise ValueError("invalid parametric scene: " + "; ".join(facts["errors"]))
    intermediate = pattern_bbox_intermediate(grid)
    crop_h, crop_w = intermediate["crop_shape"]
    crop = list(intermediate["normalized_pattern"])
    if shortcut == "template_extent_crop":
        return _render(grid, facts["matching"], crop)
    if shortcut == "transposed_bbox":
        selected = [frame for frame in facts["frames"] if frame["interior"] == (crop_w, crop_h)]
        return _render(grid, selected, crop)
    if shortcut == "bbox_area_only":
        selected = [
            frame
            for frame in facts["frames"]
            if frame["interior"][0] * frame["interior"][1] == crop_h * crop_w
        ]
        return _render(grid, selected, crop)
    if shortcut == "bbox_horizontal_flip":
        return _render(grid, intermediate["target_frames"], crop, flip_horizontal=True)
    if shortcut == "bbox_union_template":
        selected = [
            frame
            for frame in facts["frames"]
            if frame["interior"] in (intermediate["crop_shape"], facts["template"]["interior"])
        ]
        return _render(grid, selected, crop)
    if shortcut == "unnormalized_pattern":
        return _render(
            grid,
            intermediate["target_frames"],
            list(facts["template"]["pattern"]),
            raw_offsets=True,
        )
    raise ValueError(f"unknown shortcut: {shortcut}")


def _rng(seed: int, split: str, index: int) -> random.Random:
    digest = hashlib.sha256(f"{TASK_ID}:bbox-v2:{seed}:{split}:{index}".encode()).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _motif(height: int, width: int, corner: str) -> list[tuple[int, int]]:
    row = 0 if corner[0] == "t" else height - 1
    col = 0 if corner[1] == "l" else width - 1
    cells = {(row, c) for c in range(width)} | {(r, col) for r in range(height)}
    return sorted(cells)


def _anchor_offset(
    template_shape: tuple[int, int], crop_shape: tuple[int, int], anchor: str
) -> tuple[int, int]:
    th, tw = template_shape
    ch, cw = crop_shape
    return (0 if anchor[0] == "t" else th - ch, 0 if anchor[1] == "l" else tw - cw)


def _build_input(seed: int, split: str, index: int) -> list[list[int]]:
    profiles = _DEMO_PROFILES if split == "train" else _QUERY_PROFILES
    profile = profiles[index]
    height, width = profile["grid"]
    template_shape = profile["template"]
    crop_shape = profile["crop"]
    transpose_shape = (crop_shape[1], crop_shape[0])
    extra_shape = profile["extra"]
    roles = [
        {"kind": "template", "interior": template_shape},
        {"kind": "receiver", "interior": template_shape},
        {"kind": "receiver", "interior": template_shape},
        {"kind": "bbox_target", "interior": crop_shape},
        {"kind": "transpose_decoy", "interior": transpose_shape},
        {"kind": "extra_decoy", "interior": extra_shape},
    ]
    rng = _rng(seed, split, index)
    rng.shuffle(roles)
    colors = rng.sample(range(1, 10), len(roles))
    max_h = max(role["interior"][0] + 2 for role in roles)
    max_w = max(role["interior"][1] + 2 for role in roles)
    if height < 2 * max_h + 1 or width < 3 * max_w + 2:
        raise ValueError("profile cannot separate its frames")
    slots = (
        ("top", "left"),
        ("top", "middle"),
        ("top", "right"),
        ("bottom", "left"),
        ("bottom", "middle"),
        ("bottom", "right"),
    )
    grid = _blank(height, width)
    placed: list[dict[str, Any]] = []
    for role, color, (vertical, horizontal) in zip(roles, colors, slots, strict=True):
        frame_h, frame_w = role["interior"][0] + 2, role["interior"][1] + 2
        row0 = 0 if vertical == "top" else height - frame_h
        if horizontal == "left":
            col0 = 0
        elif horizontal == "middle":
            col0 = max_w + 1
        else:
            col0 = width - frame_w
        _draw_frame(grid, row0, col0, row0 + frame_h - 1, col0 + frame_w - 1, color)
        placed.append({**role, "color": color, "row0": row0, "col0": col0})

    template = next(role for role in placed if role["kind"] == "template")
    anchor = profile["anchor"]
    crop_row0, crop_col0 = _anchor_offset(template_shape, crop_shape, anchor)
    corners = ("tl", "tr", "bl", "br")
    motif = _motif(*crop_shape, corners[rng.randrange(len(corners))])
    for row, col in motif:
        grid[template["row0"] + 1 + crop_row0 + row][
            template["col0"] + 1 + crop_col0 + col
        ] = template["color"]

    facts = analyze_scene(grid)
    if facts["errors"]:
        raise ValueError("constructed invalid scene: " + "; ".join(facts["errors"]))
    intermediate = pattern_bbox_intermediate(grid)
    if intermediate["crop_shape"] != crop_shape or len(intermediate["target_frames"]) != 1:
        raise ValueError("constructed scene lost its unique bbox target")
    if not any(frame["interior"] == transpose_shape for frame in facts["frames"]):
        raise ValueError("constructed scene lost its transpose decoy")
    return grid


def generate(seed: int, settings: Any, demos: int, queries: int) -> dict[str, Any]:
    """Generate one setting-neutral episode with independently requested counts."""
    _exact_int(seed, "seed", 0, 2**63 - 1)
    _exact_int(demos, "demos", 2, 6)
    _exact_int(queries, "queries", 1, 4)
    basis = _validate_settings(settings)
    selected = {PARAMETER_NAME: basis}
    train_inputs = [_build_input(seed, "train", index) for index in range(demos)]
    test_inputs = [_build_input(seed, "test", index) for index in range(queries)]
    train = [{"input": grid, "output": transform(grid, selected)} for grid in train_inputs]
    test = [{"input": grid, "output": transform(grid, selected)} for grid in test_inputs]
    return {"train": train, "test": test, "program_solution": program(selected)}


def lesson_certificate(
    train: list[dict[str, Any]], query_inputs: list[list[list[int]]]
) -> dict[str, Any]:
    """Fit settings and six bounded shortcuts using demonstrations only."""
    settings = [{PARAMETER_NAME: value} for value in TARGET_BASES]
    surviving_settings = [
        setting
        for setting in settings
        if all(transform(pair["input"], setting) == pair["output"] for pair in train)
    ]
    surviving_shortcuts = [
        name
        for name in SHORTCUTS
        if all(shortcut_output(pair["input"], name) == pair["output"] for pair in train)
    ]
    if len(surviving_settings) == 1:
        selected_output: Callable[[list[list[int]]], list[list[int]]] = lambda grid: transform(
            grid, surviving_settings[0]
        )
        rejected: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
            f"setting:{setting[PARAMETER_NAME]}": (
                lambda grid, s=setting: transform(grid, s)
            )
            for setting in settings
            if setting not in surviving_settings
        }
        rejected.update(
            {
                f"shortcut:{name}": (
                    lambda grid, n=name: shortcut_output(grid, n)
                )
                for name in SHORTCUTS
            }
        )
        query_disagreements = {
            name: any(candidate(grid) != selected_output(grid) for grid in query_inputs)
            for name, candidate in rejected.items()
        }
    else:
        query_disagreements = {}
    return {
        "surviving_settings": surviving_settings,
        "surviving_shortcuts": surviving_shortcuts,
        "query_disagreements": query_disagreements,
        "query_outputs_consulted": False,
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    return {
        "train": [
            {
                "input": copy.deepcopy(pair["input"]),
                "output": copy.deepcopy(pair["output"]),
            }
            for pair in episode["train"]
        ],
        "test": [{"input": copy.deepcopy(pair["input"])} for pair in episode["test"]],
    }


def public_bytes(episode: dict[str, Any]) -> bytes:
    return (
        json.dumps(
            public_challenge(episode),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        + "\n"
    ).encode("utf-8")


def public_id(episode: dict[str, Any]) -> str:
    return hashlib.sha256(public_bytes(episode)).hexdigest()


def sequential_public_turns(episode: dict[str, Any]) -> list[dict[str, Any]]:
    """Reveal exactly one query input per turn with no future-count hint."""
    turns = []
    for index, pair in enumerate(episode["test"]):
        one = {"train": episode["train"], "test": [pair]}
        challenge = public_challenge(one)
        body = (
            json.dumps(
                challenge,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            )
            + "\n"
        ).encode("utf-8")
        turns.append(
            {
                "turn": index + 1,
                "challenge_id": hashlib.sha256(body).hexdigest(),
                "challenge": challenge,
            }
        )
    return turns
