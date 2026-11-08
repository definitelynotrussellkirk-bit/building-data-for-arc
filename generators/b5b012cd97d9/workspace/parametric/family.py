"""Native count-and-pack family for ARC task b5b012cd97d9.

The canonical setting packs the largest non-background mass and the next
largest repeated mass.  The alternative first derives the largest mass's
square side, then uses that input-dependent number as the count of the
secondary color to pack.  Inputs are shared across settings; native
qualification re-executes every claim through the adjacent Racket programs.
"""
from __future__ import annotations

from collections import Counter, deque
from copy import deepcopy
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import random
from typing import Any, Iterable

from reviewer_support import public_challenge_bytes

TASK_ID = "b5b012cd97d9"
VERSION = "big-side-secondary-relay-v1"
SECONDARY_SETTINGS = ("next_repeated", "big_side_relay")
DEFAULT_SECONDARY = "next_repeated"
HERE = Path(__file__).resolve().parent

_PROGRAM_FILES = {
    "next_repeated": "canonical.rkt",
    "big_side_relay": "big_side_relay.rkt",
}

# The first two demonstrations are constructive teaching cases.  Later
# profiles broaden counts, optional-singleton behavior, zero roles, geometry,
# and scale without changing the demonstrated setting.
_DEMO_PROFILES = (
    {
        "name": "teach_side4",
        "height": 8,
        "width": 8,
        "big_side": 4,
        "canonical_count": 9,
        "extras": (),
        "singleton": True,
        "layout": "teach_side4",
        "fixed_colors": {
            "background": 7,
            "big": 4,
            "canonical": 5,
            "relay": 0,
            "single": 1,
        },
    },
    {
        "name": "teach_side9",
        "height": 17,
        "width": 17,
        "big_side": 9,
        "canonical_count": 36,
        "extras": (25, 16, 4),
        "singleton": False,
        "layout": "teach_side9",
        "fixed_colors": {
            "background": 8,
            "big": 2,
            "canonical": 5,
            "relay": 6,
            "extra_25": 0,
            "extra_16": 9,
            "extra_4": 1,
        },
    },
    {
        "name": "zero_big_side9",
        "height": 17,
        "width": 19,
        "big_side": 9,
        "canonical_count": 49,
        "extras": (25, 4),
        "singleton": True,
        "zero_role": "big",
        "layout": "scatter",
    },
    {
        "name": "compact_side4",
        "height": 12,
        "width": 14,
        "big_side": 4,
        "canonical_count": 9,
        "extras": (),
        "singleton": False,
        "zero_role": "canonical",
        "layout": "scatter",
    },
    {
        "name": "relay_zero_side9",
        "height": 18,
        "width": 18,
        "big_side": 9,
        "canonical_count": 36,
        "extras": (25, 4),
        "singleton": True,
        "zero_role": "relay",
        "layout": "boundary",
    },
    {
        "name": "large_side16",
        "height": 30,
        "width": 30,
        "big_side": 16,
        "canonical_count": 64,
        "extras": (49, 25, 9, 4),
        "singleton": False,
        "zero_role": "extra_25",
        "layout": "boundary",
    },
)

_QUERY_PROFILES = (
    {
        "name": "transfer_side4",
        "height": 10,
        "width": 12,
        "big_side": 4,
        "canonical_count": 9,
        "extras": (),
        "singleton": False,
        "zero_role": "relay",
        "layout": "scatter",
    },
    {
        "name": "singleton_side9",
        "height": 18,
        "width": 20,
        "big_side": 9,
        "canonical_count": 36,
        "extras": (25, 4),
        "singleton": True,
        "zero_role": "single",
        "layout": "scatter",
    },
    {
        "name": "boundary_side9",
        "height": 23,
        "width": 17,
        "big_side": 9,
        "canonical_count": 49,
        "extras": (25, 16, 4),
        "singleton": False,
        "zero_role": "big",
        "layout": "boundary",
    },
    {
        "name": "stress_side16",
        "height": 30,
        "width": 30,
        "big_side": 16,
        "canonical_count": 81,
        "extras": (49, 25, 9, 4),
        "singleton": True,
        "zero_role": "extra_49",
        "layout": "boundary",
    },
)

RIVAL_POLICIES = (
    "next_repeated",
    "big_side_relay",
    "smallest_repeated",
    "fixed_four",
    "fixed_nine",
    "median_repeated",
    "second_smallest",
    "color_low",
    "color_high",
    "zero_preferred",
    "foreground_color_count",
    "earliest_first",
    "latest_last",
    "most_components",
    "fewest_components",
    "largest_bbox",
    "smallest_bbox",
    "highest_density",
    "lowest_density",
)


def _strict_int(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def validate_settings(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"secondary"}:
        raise ValueError("settings must contain exactly secondary")
    secondary = settings["secondary"]
    if type(secondary) is not str or secondary not in SECONDARY_SETTINGS:
        raise ValueError("secondary must be next_repeated or big_side_relay")
    return secondary


def _validate_request(seed: Any, settings: Any, demos: Any, queries: Any) -> str:
    _strict_int("seed", seed, 0, 2**63 - 1)
    _strict_int("demos", demos, 2, 6)
    _strict_int("queries", queries, 1, 4)
    return validate_settings(settings)


def program(settings: Any) -> str:
    secondary = validate_settings(settings)
    return (HERE / _PROGRAM_FILES[secondary]).read_text(encoding="utf-8")


def _rng(seed: int, *parts: Any) -> random.Random:
    payload = json.dumps([VERSION, seed, *parts], sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(payload.encode("utf-8")).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _role_counts(profile: dict[str, Any]) -> dict[str, int]:
    big_side = profile["big_side"]
    result = {
        "big": big_side * big_side,
        "canonical": profile["canonical_count"],
        "relay": big_side,
    }
    for count in profile["extras"]:
        result[f"extra_{count}"] = count
    if profile["singleton"]:
        result["single"] = 1
    values = list(result.values())
    if len(values) != len(set(values)):
        raise ValueError(f"profile {profile['name']} has duplicate role counts")
    if not all(math.isqrt(value) ** 2 == value for key, value in result.items() if key != "single"):
        raise ValueError(f"profile {profile['name']} has a nonsquare repeated role")
    if profile["canonical_count"] <= big_side:
        raise ValueError("canonical secondary must exceed the relay count")
    if max(value for key, value in result.items() if key != "big") >= result["big"]:
        raise ValueError("big role must be the unique largest foreground mass")
    return result


def _colors(profile: dict[str, Any], seed: int, role_counts: dict[str, int]) -> dict[str, int]:
    fixed = profile.get("fixed_colors")
    roles = ["background", *role_counts]
    if fixed is not None:
        if set(fixed) != set(roles) or len(set(fixed.values())) != len(fixed):
            raise ValueError("fixed palette does not match roles")
        return dict(fixed)

    zero_role = profile.get("zero_role")
    if zero_role is not None and zero_role not in role_counts:
        raise ValueError("zero_role must name a foreground role")
    result: dict[str, int] = {}
    if zero_role is not None:
        result[zero_role] = 0
    remaining = [role for role in roles if role not in result]
    palette = list(range(1, 10))
    rng = _rng(seed, profile["name"], "palette")
    rng.shuffle(palette)
    if len(remaining) > len(palette):
        raise ValueError("profile requires too many nonzero colors")
    result.update(zip(remaining, palette))
    if result["background"] == 0:
        raise ValueError("background must be nonzero")
    return result


def _block(top: int, left: int, height: int, width: int) -> list[tuple[int, int]]:
    return [(row, col) for row in range(top, top + height) for col in range(left, left + width)]


def _teaching_positions(profile: dict[str, Any], seed: int) -> dict[str, list[tuple[int, int]]]:
    if profile["layout"] == "teach_side4":
        return {
            "canonical": _block(0, 0, 3, 3),
            "relay": [(0, 7), (2, 5), (3, 3), (7, 0)],
            "single": [(7, 2)],
        }
    if profile["layout"] != "teach_side9":
        return {}

    positions: dict[str, list[tuple[int, int]]] = {
        "relay": _block(0, 0, 3, 3),
        "extra_25": _block(4, 4, 5, 5),
        "extra_16": _block(10, 0, 4, 4),
        "extra_4": _block(14, 5, 2, 2),
    }
    occupied = {cell for cells in positions.values() for cell in cells}
    candidates = [
        (row, col)
        for row in range(0, 17, 2)
        for col in range(0, 17, 2)
        if (row, col) not in occupied
    ]
    anchors = [(0, 4), (0, 16), (16, 4), (16, 16)]
    chosen = list(anchors)
    remaining = [cell for cell in candidates if cell not in chosen]
    _rng(seed, profile["name"], "canonical-spread").shuffle(remaining)
    chosen.extend(remaining[: 36 - len(chosen)])
    if len(chosen) != 36:
        raise RuntimeError("could not construct teaching spread")
    positions["canonical"] = chosen
    return positions


def _perimeter(height: int, width: int) -> list[tuple[int, int]]:
    result = [(0, col) for col in range(width)]
    result.extend((row, width - 1) for row in range(1, height))
    if height > 1:
        result.extend((height - 1, col) for col in range(width - 2, -1, -1))
    if width > 1:
        result.extend((row, 0) for row in range(height - 2, 0, -1))
    return result


def _generic_anchors(profile: dict[str, Any], roles: list[str], seed: int) -> dict[str, list[tuple[int, int]]]:
    height, width = profile["height"], profile["width"]
    boundary = _perimeter(height, width)
    if profile["layout"] == "boundary":
        preferred = [
            (0, 0),
            (0, width - 1),
            (height - 1, 0),
            (height - 1, width - 1),
            (0, width // 2),
            (height - 1, width // 2),
            (height // 2, 0),
            (height // 2, width - 1),
        ]
        remaining = [cell for cell in boundary if cell not in preferred]
        _rng(seed, profile["name"], "boundary-anchors").shuffle(remaining)
        pool = preferred + remaining
    else:
        pool = [
            (0, 0),
            (height - 1, width - 1),
            (0, width - 1),
            (height - 1, 0),
            (height // 2, width // 2),
            (height // 2, 0),
            (0, width // 2),
            (height - 1, width // 2),
        ]
        pool.extend(cell for cell in boundary if cell not in pool)
    return {role: [pool[index]] for index, role in enumerate(roles)}


def _render_profile(profile: dict[str, Any], seed: int) -> list[list[int]]:
    height, width = profile["height"], profile["width"]
    role_counts = _role_counts(profile)
    colors = _colors(profile, seed, role_counts)
    foreground_total = sum(role_counts.values())
    background_count = height * width - foreground_total
    if background_count <= role_counts["big"]:
        raise ValueError(f"profile {profile['name']} lacks a unique modal background")

    grid = [[colors["background"] for _ in range(width)] for _ in range(height)]
    positions = _teaching_positions(profile, seed)
    if not positions:
        positions = _generic_anchors(profile, list(role_counts), seed)

    occupied: set[tuple[int, int]] = set()
    for role, cells in positions.items():
        if role not in role_counts:
            raise ValueError(f"unknown placed role {role}")
        if len(cells) > role_counts[role]:
            raise ValueError(f"too many fixed cells for {role}")
        for cell in cells:
            row, col = cell
            if not (0 <= row < height and 0 <= col < width) or cell in occupied:
                raise ValueError(f"invalid or overlapping fixed cell {cell}")
            occupied.add(cell)
            grid[row][col] = colors[role]

    all_cells = [(row, col) for row in range(height) for col in range(width)]
    for role, count in role_counts.items():
        fixed = len(positions.get(role, ()))
        needed = count - fixed
        if needed <= 0:
            continue
        available = [cell for cell in all_cells if cell not in occupied]
        rng = _rng(seed, profile["name"], role, "fill")
        rng.shuffle(available)
        chosen = available[:needed]
        if len(chosen) != needed:
            raise RuntimeError(f"not enough cells for {profile['name']}:{role}")
        for row, col in chosen:
            occupied.add((row, col))
            grid[row][col] = colors[role]

    analysis = analyze(grid)
    if analysis["background"] != colors["background"]:
        raise RuntimeError("constructed background does not match Racket mode")
    if analysis["big"]["count"] != role_counts["big"]:
        raise RuntimeError("constructed big mass drifted")
    if analysis["canonical_secondary"]["count"] != role_counts["canonical"]:
        raise RuntimeError("constructed canonical secondary drifted")
    if analysis["relay"]["count"] != role_counts["relay"]:
        raise RuntimeError("constructed relay mass drifted")
    return grid


def _strict_grid(grid: Any) -> list[list[int]]:
    if type(grid) is not list or not 1 <= len(grid) <= 30:
        raise ValueError("grid must have 1..30 rows")
    if type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30:
        raise ValueError("grid must have 1..30 columns")
    width = len(grid[0])
    result = []
    for row in grid:
        if type(row) is not list or len(row) != width:
            raise ValueError("grid must be rectangular")
        if any(type(cell) is not int or not 0 <= cell <= 9 for cell in row):
            raise ValueError("grid cells must be exact ARC colors")
        result.append(list(row))
    return result


def _component_count(grid: list[list[int]], color: int) -> int:
    height, width = len(grid), len(grid[0])
    cells = {(row, col) for row in range(height) for col in range(width) if grid[row][col] == color}
    count = 0
    while cells:
        count += 1
        start = cells.pop()
        queue = deque([start])
        while queue:
            row, col = queue.popleft()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nxt = row + dr, col + dc
                if nxt in cells:
                    cells.remove(nxt)
                    queue.append(nxt)
    return count


def analyze(grid: Any) -> dict[str, Any]:
    source = _strict_grid(grid)
    height, width = len(source), len(source[0])
    counts = Counter(cell for row in source for cell in row)
    nonzero = {color: count for color, count in counts.items() if color != 0}
    if not nonzero:
        raise ValueError("grid needs a nonzero background")
    maximum = max(nonzero.values())
    backgrounds = [color for color, count in nonzero.items() if count == maximum]
    if len(backgrounds) != 1:
        raise ValueError("nonzero mode must be unique")
    background = backgrounds[0]

    records = []
    for color in sorted(counts):
        if color == background:
            continue
        cells = [(row, col) for row in range(height) for col in range(width) if source[row][col] == color]
        rows = [row for row, _ in cells]
        cols = [col for _, col in cells]
        bbox_area = (max(rows) - min(rows) + 1) * (max(cols) - min(cols) + 1)
        records.append({
            "color": color,
            "count": len(cells),
            "first": min(cells),
            "last": max(cells),
            "bbox": (min(rows), min(cols), max(rows), max(cols)),
            "bbox_area": bbox_area,
            "components": _component_count(source, color),
            "density": Fraction(len(cells), bbox_area),
        })
    if not records:
        raise ValueError("grid needs foreground colors")
    big_count = max(record["count"] for record in records)
    bigs = [record for record in records if record["count"] == big_count]
    if len(bigs) != 1:
        raise ValueError("big mass must be unique")
    big = bigs[0]
    big_side = math.isqrt(big_count)
    if big_side * big_side != big_count:
        raise ValueError("big mass must be a positive square")
    candidates = [record for record in records if record is not big and record["count"] > 1]
    if not candidates:
        raise ValueError("grid needs a repeated secondary mass")
    canonical = sorted(candidates, key=lambda record: (-record["count"], record["color"]))[0]
    relays = [record for record in candidates if record["count"] == big_side]
    if len(relays) != 1:
        raise ValueError("grid needs exactly one big-side relay mass")
    singles = [record for record in records if record["count"] == 1]
    if len(singles) > 1:
        raise ValueError("grid admits at most one singleton")
    return {
        "grid": source,
        "height": height,
        "width": width,
        "counts": dict(counts),
        "background": background,
        "background_count": counts[background],
        "records": records,
        "role_count": len(records),
        "big": big,
        "big_side": big_side,
        "canonical_secondary": canonical,
        "relay": relays[0],
        "secondary_candidates": candidates,
        "single": singles[0] if singles else None,
    }


def _select_secondary(info: dict[str, Any], policy: str) -> dict[str, Any]:
    candidates = list(info["secondary_candidates"])
    canonical = info["canonical_secondary"]
    relay = info["relay"]
    ascending = sorted(candidates, key=lambda record: (record["count"], record["color"]))
    if policy == "next_repeated":
        return canonical
    if policy == "big_side_relay":
        return relay
    if policy == "smallest_repeated":
        return ascending[0]
    if policy == "fixed_four":
        return next((record for record in candidates if record["count"] == 4), canonical)
    if policy == "fixed_nine":
        return next((record for record in candidates if record["count"] == 9), canonical)
    if policy == "median_repeated":
        return ascending[len(ascending) // 2]
    if policy == "second_smallest":
        return ascending[min(1, len(ascending) - 1)]
    if policy == "color_low":
        return min(candidates, key=lambda record: record["color"])
    if policy == "color_high":
        return max(candidates, key=lambda record: record["color"])
    if policy == "zero_preferred":
        return next((record for record in candidates if record["color"] == 0), canonical)
    if policy == "foreground_color_count":
        target = len(info["records"])
        return next((record for record in candidates if record["count"] == target), canonical)
    if policy == "earliest_first":
        return min(candidates, key=lambda record: (record["first"], -record["count"], record["color"]))
    if policy == "latest_last":
        return max(candidates, key=lambda record: (record["last"], record["count"], -record["color"]))
    if policy == "most_components":
        return max(candidates, key=lambda record: (record["components"], record["count"], -record["color"]))
    if policy == "fewest_components":
        return min(candidates, key=lambda record: (record["components"], -record["count"], record["color"]))
    if policy == "largest_bbox":
        return max(candidates, key=lambda record: (record["bbox_area"], record["count"], -record["color"]))
    if policy == "smallest_bbox":
        return min(candidates, key=lambda record: (record["bbox_area"], -record["count"], record["color"]))
    if policy == "highest_density":
        return max(candidates, key=lambda record: (record["density"], record["count"], -record["color"]))
    if policy == "lowest_density":
        return min(candidates, key=lambda record: (record["density"], -record["count"], record["color"]))
    raise ValueError(f"unknown secondary policy: {policy}")


def _pack(info: dict[str, Any], small: dict[str, Any]) -> list[list[int]]:
    big = info["big"]
    single = info["single"]
    big_side = info["big_side"]
    small_side = math.isqrt(small["count"])
    if small_side * small_side != small["count"]:
        raise ValueError("selected secondary count must be a square")
    out_height = max(big_side, small_side + int(single is not None))
    small_col = 2 if single is not None else 0
    big_col = small_col + small_side + 1
    out_width = big_col + big_side
    if out_height > 30 or out_width > 30:
        raise ValueError("packed output exceeds ARC bounds")
    small_row = out_height - small_side
    output = [[info["background"] for _ in range(out_width)] for _ in range(out_height)]
    for row in range(big_side):
        for col in range(big_col, big_col + big_side):
            output[row][col] = big["color"]
    for row in range(small_row, out_height):
        for col in range(small_col, small_col + small_side):
            output[row][col] = small["color"]
    if single is not None:
        output[-1][0] = single["color"]
    return output


def solve_rival(grid: Any, policy: str) -> list[list[int]]:
    if policy not in RIVAL_POLICIES:
        raise ValueError(f"unknown rival policy: {policy}")
    info = analyze(grid)
    return _pack(info, _select_secondary(info, policy))


def solve_python(grid: Any, secondary: str) -> list[list[int]]:
    if secondary not in SECONDARY_SETTINGS:
        raise ValueError("unknown secondary setting")
    return solve_rival(grid, secondary)


def teaching_report(demo_inputs: Iterable[Any]) -> dict[str, Any]:
    inputs = [_strict_grid(grid) for grid in demo_inputs]
    if not inputs:
        raise ValueError("teaching report needs at least one demonstration")
    survivors: dict[str, list[str]] = {}
    harmful = []
    for setting in SECONDARY_SETTINGS:
        expected = [solve_python(grid, setting) for grid in inputs]
        matches = [
            policy
            for policy in RIVAL_POLICIES
            if all(solve_rival(grid, policy) == answer for grid, answer in zip(inputs, expected))
        ]
        survivors[setting] = matches
        for policy in matches:
            if policy != setting:
                harmful.append({"setting": setting, "rival": policy})
    return {"demonstrations": len(inputs), "survivors": survivors, "harmful_survivors": harmful}


def sample_inputs(seed: Any, *, demos: Any = 3, queries: Any = 4) -> list[list[list[int]]]:
    _strict_int("seed", seed, 0, 2**63 - 1)
    _strict_int("demos", demos, 2, 6)
    _strict_int("queries", queries, 1, 4)
    demo_pool = [_render_profile(profile, seed) for profile in _DEMO_PROFILES]
    report = teaching_report(demo_pool[:2])
    expected = {setting: [setting] for setting in SECONDARY_SETTINGS}
    if report["survivors"] != expected:
        raise RuntimeError(f"constructive teaching cases drifted: {report}")
    query_pool = [_render_profile(profile, seed) for profile in _QUERY_PROFILES]
    selected = demo_pool[:demos] + query_pool[:queries]
    identities = [json.dumps(grid, separators=(",", ":")) for grid in selected]
    if len(identities) != len(set(identities)):
        raise RuntimeError("generated duplicate inputs")
    return deepcopy(selected)


def generate(seed: Any, settings: Any, demos: Any, queries: Any) -> dict[str, Any]:
    secondary = _validate_request(seed, settings, demos, queries)
    inputs = sample_inputs(seed, demos=demos, queries=queries)
    pairs = [
        {"input": grid, "output": solve_python(grid, secondary)}
        for grid in inputs
    ]
    return {
        "schema": "arcpuzzles-count-pack-parametric-v1",
        "task_id": TASK_ID,
        "seed": seed,
        "settings": {"secondary": secondary},
        "train": deepcopy(pairs[:demos]),
        "test": deepcopy(pairs[demos:]),
        "program_solution": program({"secondary": secondary}),
    }


def public_turn(episode: Any, query_index: Any = 0) -> dict[str, Any]:
    if not isinstance(episode, dict):
        raise ValueError("episode must be a dictionary")
    tests = episode.get("test")
    if type(query_index) is not int or type(tests) is not list or not 0 <= query_index < len(tests):
        raise ValueError("query_index must identify one available query")
    visible = {"train": episode.get("train"), "test": [tests[query_index]]}
    return json.loads(public_challenge_bytes(visible))


def sequential_witness_input() -> list[list[int]]:
    return sample_inputs(0, demos=2, queries=1)[1]
