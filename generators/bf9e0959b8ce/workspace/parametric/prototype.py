"""Native-ready parametric family for ``bf9e0959b8ce``.

The default ``canonical`` mode is the exact selected separator-keyed routing
rule.  The alternative ``near_count_relay`` mode adds a genuine second stage:

A. Route every source dot by the canonical key comparison.
Intermediate. Count the dots now present on the near edge (1, 2, or 3).
B. Order the far-edge routed dots by their aligned coordinate, select the
   intermediate-th candidate, and relay that dot one cell inward.

The same deterministic inputs are used for both modes.  Six demonstration
profiles and four independent query profiles are generated up front, so
requesting fewer demonstrations or queries only takes a stable prefix.  The
last query is a substantive 30x30 boundary case.
"""
from collections import Counter
from copy import deepcopy
from dataclasses import dataclass
import hashlib
from pathlib import Path
import random
from typing import Any

TASK_ID = "bf9e0959b8ce"
PARAMETER_NAME = "rule_mode"
ALLOWED_MODES = ("canonical", "near_count_relay")
DEFAULT_MODE = "canonical"
PROTOTYPE_VERSION = "2.0.0"

HERE = Path(__file__).resolve().parent
CANONICAL_PATH = HERE / "canonical.rkt"
RELAY_PATH = HERE / "near_count_relay.rkt"


@dataclass(frozen=True)
class Profile:
    height: int
    width: int
    orientation: str
    match_count: int
    boundary: bool = False


DEMO_PROFILES = (
    Profile(10, 12, "row", 1),
    Profile(12, 10, "col", 2),
    Profile(14, 16, "row", 3),
    Profile(16, 14, "col", 1),
    Profile(18, 20, "row", 2),
    Profile(22, 24, "col", 3),
)
QUERY_PROFILES = (
    Profile(13, 15, "col", 3),
    Profile(20, 18, "row", 2),
    Profile(26, 28, "col", 1),
    Profile(30, 30, "row", 3, boundary=True),
)


def _exact_int(value: object, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _mode_from_settings(settings: object) -> str:
    if type(settings) is not dict or set(settings) != {PARAMETER_NAME}:
        raise ValueError(f"settings must contain exactly {PARAMETER_NAME!r}")
    mode = settings[PARAMETER_NAME]
    if type(mode) is not str or mode not in ALLOWED_MODES:
        raise ValueError(f"{PARAMETER_NAME} must be one of {ALLOWED_MODES!r}")
    return mode


def _grid(value: object) -> list[list[int]]:
    if (
        type(value) is not list
        or not 1 <= len(value) <= 30
        or type(value[0]) is not list
        or not 1 <= len(value[0]) <= 30
        or any(
            type(row) is not list
            or len(row) != len(value[0])
            or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
            for row in value
        )
    ):
        raise ValueError("grid must be rectangular 1..30 with exact integer colors 0..9")
    return [row[:] for row in value]


def program(settings: object) -> str:
    """Return the exact complete Racket program for one declared setting."""
    mode = _mode_from_settings(settings)
    path = CANONICAL_PATH if mode == "canonical" else RELAY_PATH
    return path.read_text(encoding="utf-8")


def _most_common(values: list[int]) -> int:
    if not values:
        raise ValueError("cannot take mode of an empty collection")
    counts = Counter(values)
    peak = max(counts.values())
    return min(value for value, count in counts.items() if count == peak)


def analyze(value: object) -> dict[str, Any]:
    """Parse the admitted separator/key/source grammar and expose relay roles."""
    grid = _grid(value)
    h, w = len(grid), len(grid[0])
    background = _most_common([cell for row in grid for cell in row])
    full_rows = [
        r
        for r, row in enumerate(grid)
        if row[0] != background and all(cell == row[0] for cell in row)
    ]
    full_cols = [
        c
        for c in range(w)
        if grid[0][c] != background
        and all(grid[r][c] == grid[0][c] for r in range(h))
    ]
    if len(full_rows) + len(full_cols) != 1:
        raise ValueError(
            f"expected exactly one non-background uniform separator, found rows={full_rows}, cols={full_cols}"
        )

    if full_rows:
        orientation = "row"
        separator = full_rows[0]
        if not 3 <= separator <= h - 2:
            raise ValueError("row separator leaves insufficient source/key space")
        source_cells = [grid[r][c] for r in range(separator) for c in range(w)]
        source_bg = _most_common(source_cells)
        dots = sorted(
            (
                (r, c, grid[r][c])
                for r in range(separator)
                for c in range(w)
                if grid[r][c] != source_bg
            ),
            key=lambda item: item[1],
        )
        key_index = separator + 1
        near, far, relay = separator - 1, 0, 1
        aligned = [grid[key_index][c] for _, c, _ in dots]
        aligned_coords = [c for _, c, _ in dots]
        source_lines = {r for r, _, _ in dots}
    else:
        orientation = "col"
        separator = full_cols[0]
        if not 1 <= separator <= w - 4:
            raise ValueError("column separator leaves insufficient key/source space")
        source_cells = [
            grid[r][c]
            for r in range(h)
            for c in range(separator + 1, w)
        ]
        source_bg = _most_common(source_cells)
        dots = sorted(
            (
                (r, c, grid[r][c])
                for r in range(h)
                for c in range(separator + 1, w)
                if grid[r][c] != source_bg
            ),
            key=lambda item: item[0],
        )
        key_index = separator - 1
        near, far, relay = separator + 1, w - 1, w - 2
        aligned = [grid[r][key_index] for r, _, _ in dots]
        aligned_coords = [r for r, _, _ in dots]
        source_lines = {c for _, c, _ in dots}

    if len(dots) != 6:
        raise ValueError(f"admitted grammar requires exactly six source dots, found {len(dots)}")
    if len(set(aligned_coords)) != len(aligned_coords):
        raise ValueError("source dots must use distinct aligned coordinates")
    if any(value == source_bg for value in aligned):
        raise ValueError("each source dot needs a visible aligned key value")

    match_flags = [dot[2] == key for dot, key in zip(dots, aligned, strict=True)]
    match_count = sum(match_flags)
    nonmatch_count = len(dots) - match_count
    if match_count not in (1, 2, 3) or nonmatch_count < 3:
        raise ValueError("admitted grammar requires 1..3 matches and at least three mismatches")
    if len(source_lines) < 2:
        raise ValueError("source dots must span at least two movement-axis lines")

    far_candidates = [
        (coord, dot[2])
        for coord, dot, matches in zip(aligned_coords, dots, match_flags, strict=True)
        if not matches
    ]
    return {
        "height": h,
        "width": w,
        "background": background,
        "source_bg": source_bg,
        "orientation": orientation,
        "separator_index": separator,
        "key_index": key_index,
        "near": near,
        "far": far,
        "relay": relay,
        "dots": dots,
        "aligned_values": aligned,
        "match_flags": match_flags,
        "match_count": match_count,
        "nonmatch_count": nonmatch_count,
        "n_dots": len(dots),
        "source_line_count": len(source_lines),
        "far_candidates": far_candidates,
    }


def canonical_transform(value: object) -> list[list[int]]:
    grid = _grid(value)
    info = analyze(grid)
    out = [row[:] for row in grid]
    for dot, key in zip(info["dots"], info["aligned_values"], strict=True):
        r, c, color = dot
        out[r][c] = info["source_bg"]
        destination = info["near"] if color == key else info["far"]
        if info["orientation"] == "row":
            out[destination][c] = color
        else:
            out[r][destination] = color
    return out


def _edge_candidates(stage_a: list[list[int]], info: dict[str, Any], edge: int) -> list[tuple[int, int]]:
    if info["orientation"] == "row":
        return [
            (c, stage_a[edge][c])
            for c in range(info["width"])
            if stage_a[edge][c] != info["source_bg"]
        ]
    return [
        (r, stage_a[r][edge])
        for r in range(info["height"])
        if stage_a[r][edge] != info["source_bg"]
    ]


def relay_with_forced_count(value: object, forced_count: object) -> list[list[int]]:
    """Execute stage B with an explicit intermediate, for bounded ablations."""
    grid = _grid(value)
    info = analyze(grid)
    stage_a = canonical_transform(grid)
    far_candidates = _edge_candidates(stage_a, info, info["far"])
    count = _exact_int(forced_count, "forced_count", 1, len(far_candidates))
    coord, color = far_candidates[count - 1]
    out = [row[:] for row in stage_a]
    if info["orientation"] == "row":
        out[info["far"]][coord] = info["source_bg"]
        out[info["relay"]][coord] = color
    else:
        out[coord][info["far"]] = info["source_bg"]
        out[coord][info["relay"]] = color
    return out


def explain_relay(value: object) -> dict[str, Any]:
    grid = _grid(value)
    info = analyze(grid)
    stage_a = canonical_transform(grid)
    near_candidates = _edge_candidates(stage_a, info, info["near"])
    far_candidates = _edge_candidates(stage_a, info, info["far"])
    near_count = len(near_candidates)
    if not 1 <= near_count <= len(far_candidates):
        raise ValueError("near count cannot select a far-edge candidate")
    selected = far_candidates[near_count - 1]
    final = relay_with_forced_count(grid, near_count)
    return {
        "stage_a": stage_a,
        "near_count": near_count,
        "near_candidates": near_candidates,
        "far_candidates": far_candidates,
        "selected_far_candidate": selected,
        "final": final,
    }


def transform(value: object, mode: object) -> list[list[int]]:
    if type(mode) is not str or mode not in ALLOWED_MODES:
        raise ValueError(f"mode must be one of {ALLOWED_MODES!r}")
    return canonical_transform(value) if mode == "canonical" else explain_relay(value)["final"]


def _rng(seed: int, domain: str, index: int) -> random.Random:
    digest = hashlib.sha256(f"{TASK_ID}:{PROTOTYPE_VERSION}:{seed}:{domain}:{index}".encode()).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _aligned_positions(extent: int, profile: Profile, rng: random.Random) -> list[int]:
    if profile.boundary:
        values = [0, extent // 6, extent // 3, extent // 2, (5 * extent) // 7, extent - 1]
        if len(set(values)) != 6:
            raise ValueError("boundary profile did not produce six unique aligned coordinates")
        return sorted(values)
    return sorted(rng.sample(range(extent), 6))


def _scene(seed: int, domain: str, index: int, profile: Profile) -> list[list[int]]:
    rng = _rng(seed, domain, index)
    h, w = profile.height, profile.width
    colors = list(range(10))
    background = rng.choice(list(range(1, 10)))
    colors.remove(background)
    separator_color = rng.choice([color for color in colors if color != 0])
    colors.remove(separator_color)
    signal_colors = rng.sample(colors, 6)
    grid = [[background for _ in range(w)] for _ in range(h)]

    if profile.orientation == "row":
        separator = max(4, min(h - 3, h // 2))
        for c in range(w):
            grid[separator][c] = separator_color
        key_index = separator + 1
        legal_source_lines = list(range(2, separator))
        aligned_positions = _aligned_positions(w, profile, rng)
    elif profile.orientation == "col":
        separator = max(2, min(w - 4, w // 2 - 1))
        for r in range(h):
            grid[r][separator] = separator_color
        key_index = separator - 1
        legal_source_lines = list(range(separator + 1, w - 2))
        aligned_positions = _aligned_positions(h, profile, rng)
    else:
        raise ValueError(f"unknown orientation: {profile.orientation}")

    if len(legal_source_lines) < 2:
        raise ValueError("profile leaves fewer than two legal source lines")
    source_lines = [legal_source_lines[i % len(legal_source_lines)] for i in range(6)]
    rng.shuffle(source_lines)

    # Boundary profiles keep both extreme aligned coordinates in the mismatch
    # set, so the final 30x30 query exercises both output-edge corners.
    candidate_match_indices = list(range(1, 5)) if profile.boundary else list(range(6))
    match_indices = set(rng.sample(candidate_match_indices, profile.match_count))
    if profile.boundary:
        match_indices.discard(0)
        match_indices.discard(5)
        while len(match_indices) < profile.match_count:
            match_indices.add(1 + len(match_indices))

    # Shuffle colors independently of geometric order so candidate identity is
    # not encoded by a fixed palette position.
    rng.shuffle(signal_colors)
    for i, (aligned, source_line, dot_color) in enumerate(
        zip(aligned_positions, source_lines, signal_colors, strict=True)
    ):
        if i in match_indices:
            key_color = dot_color
        else:
            key_color = signal_colors[(i + 1) % len(signal_colors)]
            if key_color == dot_color:
                key_color = signal_colors[(i + 2) % len(signal_colors)]
        if profile.orientation == "row":
            grid[source_line][aligned] = dot_color
            grid[key_index][aligned] = key_color
        else:
            grid[aligned][source_line] = dot_color
            grid[aligned][key_index] = key_color

    info = analyze(grid)
    if info["match_count"] != profile.match_count:
        raise AssertionError("constructed scene lost its requested match count")
    return grid


def _pair(seed: int, domain: str, index: int, profile: Profile, mode: str) -> dict[str, Any]:
    grid = _scene(seed, domain, index, profile)
    return {"input": grid, "output": transform(grid, mode)}


def generate(seed: object, settings: object, demos: object, queries: object) -> dict[str, Any]:
    """Return a deterministic private labeled episode for native qualification."""
    seed = _exact_int(seed, "seed", 0, 2**63 - 1)
    demos = _exact_int(demos, "demos", 2, 6)
    queries = _exact_int(queries, "queries", 1, 4)
    mode = _mode_from_settings(settings)

    all_demos = [
        _pair(seed, "demo", index, profile, mode)
        for index, profile in enumerate(DEMO_PROFILES)
    ]
    all_queries = [
        _pair(seed, "query", index, profile, mode)
        for index, profile in enumerate(QUERY_PROFILES)
    ]
    return {
        "train": all_demos[:demos],
        "test": all_queries[:queries],
        "program_solution": program({PARAMETER_NAME: mode}),
    }



def public_batch(episode: object) -> dict[str, Any]:
    """Project all stored query inputs for canonical content-hashed export."""
    if type(episode) is not dict or not isinstance(episode.get("train"), list) or not isinstance(episode.get("test"), list):
        raise ValueError("episode must contain train and test lists")
    return {
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": deepcopy(pair["input"])} for pair in episode["test"]],
    }

def public_challenge(episode: object, *, query_index: object) -> dict[str, Any]:
    """Project one query turn without answers, settings, program, or count hint."""
    if type(episode) is not dict or not isinstance(episode.get("train"), list) or not isinstance(episode.get("test"), list):
        raise ValueError("episode must contain train and test lists")
    query_index = _exact_int(query_index, "query_index", 0, len(episode["test"]) - 1)
    return {
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": deepcopy(episode["test"][query_index]["input"])}],
    }
