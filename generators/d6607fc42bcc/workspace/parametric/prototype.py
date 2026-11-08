"""Projection-depth rule family for d6607fc42bcc.

The canonical setting paints one exterior row.  The alternative first locates
an interior dot, computes its distance from the notched edge, and uses that
input-derived distance as the number of full-width exterior rows to paint.
Inputs are setting-independent; Python labels are authoring claims until native
qualification replays every pair through protected Racket.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import random

from reviewer_support import public_challenge_bytes, public_challenge_id


HERE = Path(__file__).resolve().parent
HOME = HERE.parents[1]
TASK_ID = "d6607fc42bcc"
DEPTH_MODES = ("one", "dot_offset")

# Each frame is (height, opening, dot-to-opening depth, min_width, max_width).
# The occupied vertical interval includes the frame and its full dot-depth
# projection, so every generated input is lawful under both settings.
_DEMOS = (
    (12, 14, ((8, "top", 2, 7, 9),)),
    (16, 18, ((7, "bottom", 4, 8, 10),)),
    (18, 20, ((6, "top", 3, 7, 9), (6, "bottom", 2, 8, 10))),
    (21, 23, ((9, "bottom", 3, 9, 12),)),
    (24, 26, ((7, "top", 2, 8, 11), (7, "top", 4, 10, 13))),
    (27, 29, ((8, "bottom", 5, 11, 14), (6, "top", 3, 9, 12))),
)
_QUERIES = (
    (13, 17, ((7, "top", 3, 8, 10),)),
    (19, 22, ((7, "bottom", 2, 9, 11), (6, "top", 3, 8, 10))),
    (26, 28, ((9, "top", 4, 11, 14), (8, "bottom", 3, 10, 13))),
    (30, 30, ((9, "top", 5, 13, 16), (8, "bottom", 5, 12, 15))),
)
_SHORTCUTS = (
    "fixed_two",
    "no_exterior_bar",
    "bar_only",
    "opposite_edge_distance",
    "interior_height",
    "nearest_edge_distance",
)


def _load_generator():
    path = HOME / "generator.py"
    spec = importlib.util.spec_from_file_location(
        "_d660_parametric_geometry_" + hashlib.sha256(str(path).encode()).hexdigest(),
        path,
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEN = _load_generator()


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _mode(settings):
    if (
        type(settings) is not dict
        or set(settings) != {"projection_depth"}
        or type(settings["projection_depth"]) is not str
        or settings["projection_depth"] not in DEPTH_MODES
    ):
        raise ValueError(
            "settings must be exactly {'projection_depth': 'one'|'dot_offset'}"
        )
    return settings["projection_depth"]


def program(settings):
    mode = _mode(settings)
    name = "canonical.rkt" if mode == "one" else "dot_offset.rkt"
    return (HERE / name).read_text(encoding="utf-8")


def _derived_seed(seed, split, index):
    raw = json.dumps(
        [TASK_ID, "projection-input-v1", seed, split, index],
        separators=(",", ":"),
    ).encode()
    return int.from_bytes(hashlib.sha256(raw).digest()[:8], "big") & (2**63 - 1)


def _slack_parts(total, count, rng):
    parts = [0] * count
    for _ in range(total):
        parts[rng.randrange(count)] += 1
    return parts


def _flip(grid, *, vertical=False, horizontal=False):
    out = [row[:] for row in grid]
    if vertical:
        out.reverse()
    if horizontal:
        out = [list(reversed(row)) for row in out]
    return out


def sample_input(seed, index, *, split):
    _integer(seed, 0, 2**63 - 1, "seed")
    profiles = _DEMOS if split == "train" else _QUERIES if split == "test" else None
    if profiles is None:
        raise ValueError("split must be train or test")
    _integer(index, 0, len(profiles) - 1, "index")
    h, w, frame_specs = profiles[index]
    rng = random.Random(_derived_seed(seed, split, index))
    ext_heights = [fh + depth for fh, _, depth, _, _ in frame_specs]
    required = sum(ext_heights) + max(0, len(frame_specs) - 1)
    if required > h:
        raise AssertionError("profile does not fit its canvas")
    margins = _slack_parts(h - required, len(frame_specs) + 1, rng)
    starts = []
    cursor = margins[0]
    for frame_index, ext_height in enumerate(ext_heights):
        starts.append(cursor)
        cursor += ext_height
        if frame_index + 1 < len(frame_specs):
            cursor += 1 + margins[frame_index + 1]

    grid = [[0] * w for _ in range(h)]
    colors = rng.sample(range(2, 10), len(frame_specs))
    for frame_index, ((fh, opening, depth, min_width, max_width), ext_start) in enumerate(
        zip(frame_specs, starts)
    ):
        fw = rng.randint(min_width, min(max_width, w))
        c0 = rng.randint(0, w - fw)
        r0 = ext_start + depth if opening == "top" else ext_start
        notch = rng.randint(1, fw - 2)
        dot_rel_row = depth if opening == "top" else fh - 1 - depth
        GEN._draw_notched_frame(
            grid,
            r0,
            c0,
            fh,
            fw,
            opening=opening,
            notch_rel_col=notch,
            dot_rel_row=dot_rel_row,
            dot_rel_col=notch,
            dot_color=colors[frame_index],
        )

    # Nuisance symmetries preserve the distance relation and source semantics.
    return _flip(
        grid,
        vertical=bool(rng.randrange(2)),
        horizontal=bool(rng.randrange(2)),
    )


def _depth(frame, dot_r, strategy, grid_h):
    r0, _, r1, _ = frame["bbox"]
    opening = frame["opening"]
    toward_opening = dot_r - r0 if opening == "top" else r1 - dot_r
    toward_closed = r1 - dot_r if opening == "top" else dot_r - r0
    if strategy == "one":
        return 1
    if strategy == "dot_offset":
        return toward_opening
    if strategy == "fixed_two":
        return 2
    if strategy == "no_exterior_bar":
        return 0
    if strategy == "opposite_edge_distance":
        return toward_closed
    if strategy == "interior_height":
        return r1 - r0 - 1
    if strategy == "nearest_edge_distance":
        return min(toward_opening, toward_closed)
    raise ValueError(f"unknown depth strategy: {strategy}")


def _render(grid, strategy, *, fill_interior=True):
    g = deepcopy(grid)
    out = deepcopy(g)
    h = len(g)
    frames = GEN._u_frame_records(g)
    if not frames or any(len(frame["dots"]) != 1 for frame in frames):
        raise ValueError("input must contain exact notched frames with one interior dot")
    for frame in frames:
        r0, c0, r1, c1 = frame["bbox"]
        dot_r, _, color = frame["dots"][0]
        if fill_interior:
            for r in range(r0 + 1, r1):
                for c in range(c0 + 1, c1):
                    if out[r][c] == 0:
                        out[r][c] = color
            edge_r = r0 if frame["opening"] == "top" else r1
            for c in range(c0 + 1, c1):
                if g[edge_r][c] == 0:
                    out[edge_r][c] = color
        depth = _depth(frame, dot_r, strategy, h)
        if frame["opening"] == "top":
            rows = range(max(0, r0 - depth), r0)
        else:
            rows = range(r1 + 1, min(h, r1 + 1 + depth))
        for r in rows:
            for c in range(c0, c1 + 1):
                out[r][c] = color
    return out


def claimed_output(grid, settings):
    return _render(grid, _mode(settings))


def shortcut_output(grid, name):
    if name not in _SHORTCUTS:
        raise ValueError(f"unknown shortcut: {name}")
    if name == "bar_only":
        return _render(grid, "dot_offset", fill_interior=False)
    return _render(grid, name)


def generate(seed, settings, demos=3, queries=4):
    _integer(seed, 0, 2**63 - 1, "seed")
    _mode(settings)
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    result = {"train": [], "test": [], "program_solution": program(settings)}
    seen = set()
    for split, count in (("train", demos), ("test", queries)):
        for index in range(count):
            grid = sample_input(seed, index, split=split)
            key = json.dumps(grid, separators=(",", ":"))
            if key in seen:
                raise ValueError(f"duplicate input at {split}[{index}]")
            seen.add(key)
            result[split].append(
                {"input": grid, "output": claimed_output(grid, settings)}
            )
    result["sampling"] = {"draws": demos + queries, "duplicate_rejections": 0}
    return result


def teaching_certificate(episode):
    if type(episode) is not dict or type(episode.get("train")) is not list:
        raise ValueError("episode must contain demonstrations")
    survivors = []
    rejected = {}
    for mode in DEPTH_MODES:
        settings = {"projection_depth": mode}
        mismatch = next(
            (
                index
                for index, pair in enumerate(episode["train"])
                if claimed_output(pair["input"], settings) != pair["output"]
            ),
            None,
        )
        if mismatch is None:
            survivors.append(settings)
        else:
            rejected[mode] = mismatch
    shortcut_survivors = []
    shortcut_rejected = {}
    for name in _SHORTCUTS:
        mismatch = next(
            (
                index
                for index, pair in enumerate(episode["train"])
                if shortcut_output(pair["input"], name) != pair["output"]
            ),
            None,
        )
        if mismatch is None:
            shortcut_survivors.append(name)
        else:
            shortcut_rejected[name] = mismatch
    return {
        "survivors": survivors,
        "rejected_by_demo": rejected,
        "shortcut_survivors": shortcut_survivors,
        "shortcut_rejected_by_demo": shortcut_rejected,
        "query_answers_used": False,
    }


def frame_intermediates(grid):
    rows = []
    for frame in GEN._u_frame_records(grid):
        r0, c0, r1, c1 = frame["bbox"]
        dot_r, dot_c, color = frame["dots"][0]
        depth = dot_r - r0 if frame["opening"] == "top" else r1 - dot_r
        rows.append(
            {
                "bbox": [r0, c0, r1, c1],
                "opening": frame["opening"],
                "dot": [dot_r, dot_c, color],
                "dot_to_notch_distance": depth,
            }
        )
    return rows


def visible_turn(episode, index):
    _integer(index, 0, len(episode["test"]) - 1, "query index")
    return public_challenge_bytes(
        {"train": episode["train"], "test": [episode["test"][index]]}
    )


def public_identity(episode):
    return public_challenge_id(episode)
