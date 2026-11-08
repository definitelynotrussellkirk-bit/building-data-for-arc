"""Matched-input parametric family for ARC task ``e14a91c50791``.

``bbox_only`` is the byte-exact canonical rule: group red components by shape
up to rotation and fill every member of the unique odd-frequency class's
bounding box orange.

``largest_orange_cluster`` performs that exact step A, then recomputes the
four-connected orange components created by the fills and recolors the unique
largest orange cluster blue.  Two target boxes are constructed to become
connected only after their missing cells are filled, while a third equal-shape
target remains isolated.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Iterable

TASK_ID = "e14a91c50791"
PARAMETER = "finish"
SETTINGS = ("bbox_only", "largest_orange_cluster")
DEFAULT = {PARAMETER: SETTINGS[0]}
MIN_DEMOS = 2
MAX_DEMOS = 6
MIN_QUERIES = 1
MAX_QUERIES = 4
MAX_SEED = 2**63 - 1
HOME = Path(__file__).resolve().parent
PROGRAM_FILES = {
    SETTINGS[0]: HOME / "canonical.rkt",
    SETTINGS[1]: HOME / "largest_orange_cluster.rkt",
}
CARDINALS = ((-1, 0), (1, 0), (0, -1), (0, 1))

# The first two profiles deliberately reverse whether the isolated orange box
# or the merged pair appears first in row-major order.  This makes two demos
# refute a first/last-component shortcut without increasing demonstration cost.
TRAIN_PROFILES = (
    (13, 13, 0, False),
    (15, 17, 1, True),
    (17, 15, 2, False),
    (20, 20, 3, True),
    (24, 26, 0, False),
    (26, 24, 1, True),
)
QUERY_PROFILES = (
    (14, 18, 2, True),
    (18, 22, 3, False),
    (26, 26, 1, True),
    (30, 30, 0, False),
)

TARGET_A = ((0, 0), (0, 1), (1, 0))
TARGET_B = ((0, 1), (1, 0), (1, 1))
DISTRACTOR_BASES = (
    ((0, 0), (0, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 1)),
    ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0)),
)


def _exact_int(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer; bool is forbidden")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in [{low}, {high}]")
    return value


def _finish(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {PARAMETER}:
        raise ValueError(f"settings must contain exactly {PARAMETER!r}")
    value = settings[PARAMETER]
    if type(value) is not str or value not in SETTINGS:
        raise ValueError(f"{PARAMETER} must be one of {SETTINGS!r}")
    return value


def program(settings: Any) -> str:
    return PROGRAM_FILES[_finish(settings)].read_text(encoding="utf-8")


def _grid(value: Any) -> tuple[int, int]:
    if type(value) is not list or not value or type(value[0]) is not list or not value[0]:
        raise ValueError("grid must be a nonempty list of nonempty rows")
    width = len(value[0])
    if len(value) > 30 or width > 30:
        raise ValueError("grid dimensions must not exceed 30")
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or cell not in (0, 2) for cell in row)
        for row in value
    ):
        raise ValueError("input must be rectangular with exact integer colors 0 or 2")
    return len(value), width


def _norm(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    if not cells:
        return ()
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _rotate_cw(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = _norm(cells)
    height = max(r for r, _ in cells) + 1
    return _norm((c, height - 1 - r) for r, c in cells)


def _rotate(cells: Iterable[tuple[int, int]], turns: int) -> tuple[tuple[int, int], ...]:
    out = _norm(cells)
    for _ in range(turns % 4):
        out = _rotate_cw(out)
    return out


def _rotation_key(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    current = _norm(cells)
    variants = []
    for _ in range(4):
        variants.append(current)
        current = _rotate_cw(current)
    return min(variants)


def _components(grid: list[list[int]], color: int) -> list[frozenset[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    remaining = {(r, c) for r in range(height) for c in range(width) if grid[r][c] == color}
    result: list[frozenset[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        cells = {start}
        while stack:
            r, c = stack.pop()
            for dr, dc in CARDINALS:
                q = (r + dr, c + dc)
                if q in remaining:
                    remaining.remove(q)
                    cells.add(q)
                    stack.append(q)
        result.append(frozenset(cells))
    result.sort(key=lambda cells: min(cells))
    return result


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = tuple(cells)
    return (
        min(r for r, _ in cells),
        min(c for _, c in cells),
        max(r for r, _ in cells),
        max(c for _, c in cells),
    )


def analyze(value: Any, *, exact_orientation: bool = False) -> dict[str, Any]:
    _grid(value)
    red = _components(value, 2)
    if not red:
        raise ValueError("scene must contain red components")
    groups: dict[tuple[tuple[int, int], ...], list[frozenset[tuple[int, int]]]] = {}
    for cells in red:
        key = _norm(cells) if exact_orientation else _rotation_key(cells)
        groups.setdefault(key, []).append(cells)
    odd = [key for key, values in groups.items() if len(values) % 2 == 1]
    if len(odd) != 1:
        raise ValueError("scene must contain exactly one odd-frequency class")
    return {"red_components": red, "groups": groups, "odd_key": odd[0]}


def canonical_intermediate(value: Any, *, exact_orientation: bool = False) -> list[list[int]]:
    scene = analyze(value, exact_orientation=exact_orientation)
    out = deepcopy(value)
    for cells in scene["groups"][scene["odd_key"]]:
        r1, c1, r2, c2 = _bbox(cells)
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                out[r][c] = 7
    return out


def _largest(cells_list: list[frozenset[tuple[int, int]]]) -> frozenset[tuple[int, int]]:
    if not cells_list:
        raise ValueError("no component to select")
    ordered = sorted(cells_list, key=lambda cells: (-len(cells), min(cells)))
    if len(ordered) > 1 and len(ordered[0]) == len(ordered[1]):
        raise ValueError("largest component must be unique")
    return ordered[0]


def _finish_cluster(intermediate: list[list[int]], selector: str = "largest") -> list[list[int]]:
    orange = _components(intermediate, 7)
    if selector == "largest":
        selected = _largest(orange)
    elif selector == "first":
        selected = orange[0]
    elif selector == "last":
        selected = orange[-1]
    else:
        raise ValueError(selector)
    out = deepcopy(intermediate)
    for r, c in selected:
        out[r][c] = 4
    return out


def solve(value: Any, settings: Any) -> list[list[int]]:
    finish = _finish(settings)
    intermediate = canonical_intermediate(value)
    if finish == SETTINGS[0]:
        return intermediate
    return _finish_cluster(intermediate, "largest")


def wrong_intermediate_solve(value: Any) -> list[list[int]]:
    """Counterfactual: select one source target before the fills can merge."""
    scene = analyze(value)
    targets = sorted(scene["groups"][scene["odd_key"]], key=min)
    selected = targets[0]
    out = canonical_intermediate(value)
    r1, c1, r2, c2 = _bbox(selected)
    for r in range(r1, r2 + 1):
        for c in range(c1, c2 + 1):
            out[r][c] = 4
    return out


def _all_orange_to_blue(value: Any) -> list[list[int]]:
    return [[4 if cell == 7 else cell for cell in row] for row in canonical_intermediate(value)]


def _exact_orientation_output(value: Any, settings: Any) -> list[list[int]]:
    # Plausible wrong rule: count exact orientations rather than rotation classes,
    # and fill every exact-orientation class with odd multiplicity.  Unlike the
    # selected grammar this rival can have several odd classes, so it must remain
    # total rather than reusing ``analyze``'s one-odd-class invariant.
    _grid(value)
    groups: dict[tuple[tuple[int, int], ...], list[frozenset[tuple[int, int]]]] = {}
    for cells in _components(value, 2):
        groups.setdefault(_norm(cells), []).append(cells)
    out = deepcopy(value)
    for values in groups.values():
        if len(values) % 2 == 0:
            continue
        for cells in values:
            r1, c1, r2, c2 = _bbox(cells)
            for r in range(r1, r2 + 1):
                for c in range(c1, c2 + 1):
                    out[r][c] = 7
    if _finish(settings) == SETTINGS[0]:
        return out
    orange = _components(out, 7)
    if not orange:
        return out
    selected = sorted(orange, key=lambda cells: (-len(cells), min(cells)))[0]
    result = deepcopy(out)
    for r, c in selected:
        result[r][c] = 4
    return result


def rival_outputs(value: Any, settings: Any) -> dict[str, list[list[int]]]:
    finish = _finish(settings)
    other = SETTINGS[1] if finish == SETTINGS[0] else SETTINGS[0]
    intermediate = canonical_intermediate(value)
    return {
        "other_setting": solve(value, {PARAMETER: other}),
        "mark_all_orange": _all_orange_to_blue(value),
        "first_orange_component": _finish_cluster(intermediate, "first"),
        "last_orange_component": _finish_cluster(intermediate, "last"),
        "wrong_intermediate": wrong_intermediate_solve(value),
        "exact_orientation_parity": _exact_orientation_output(value, settings),
    }


def teaching_check(episode: Any) -> dict[str, Any]:
    if type(episode) is not dict:
        raise ValueError("episode must be an object")
    settings = episode.get("settings")
    _finish(settings)
    train = episode.get("train")
    if type(train) is not list or not MIN_DEMOS <= len(train) <= MAX_DEMOS:
        raise ValueError("episode must contain two through six demonstrations")
    per_demo = []
    names: set[str] = set()
    for pair in train:
        if type(pair) is not dict or set(pair) < {"input", "output"}:
            raise ValueError("demonstrations require input/output")
        if solve(pair["input"], settings) != pair["output"]:
            raise ValueError("demonstration label differs from selected rule")
        outputs = rival_outputs(pair["input"], settings)
        per_demo.append(outputs)
        names.update(outputs)
    survivors = sorted(
        name for name in names
        if all(outputs[name] == pair["output"] for outputs, pair in zip(per_demo, train, strict=True))
    )
    return {
        "status": "identified" if not survivors else "ambiguous",
        "surviving_rivals": survivors,
        "demonstrations": len(train),
        "used_query_answers": False,
        "limits": "Finite named rivals fitted to demonstrations only; not universal uniqueness.",
    }


def dependency_trace(value: Any, settings: Any) -> dict[str, Any]:
    finish = _finish(settings)
    intermediate = canonical_intermediate(value)
    orange = _components(intermediate, 7)
    sizes = sorted((len(cells) for cells in orange), reverse=True)
    return {
        "setting": {PARAMETER: finish},
        "step_a": "group red components up to rotation and fill the unique odd-frequency class bounding boxes orange",
        "intermediate": intermediate,
        "step_b": "recompute orange components and recolor the unique largest connected orange cluster blue",
        "why_b_depends_on_a": "two separate red target objects become one larger component only after their missing bbox cells are filled by step A",
        "orange_components": len(orange),
        "largest_orange_cells": sizes[0],
        "smallest_orange_cells": sizes[-1],
    }


def _rng(seed: int, split: str, index: int) -> random.Random:
    raw = f"{TASK_ID}|orange-cluster-v2|{seed}|{split}|{index}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest()[:16], "big"))


def _shift(cells: Iterable[tuple[int, int]], top: int, left: int) -> frozenset[tuple[int, int]]:
    return frozenset((top + r, left + c) for r, c in cells)


def _rotate_group(groups: list[tuple[tuple[int, int], ...]], turns: int):
    all_cells = [(gi, r, c) for gi, group in enumerate(groups) for r, c in group]
    h = max(r for _, r, _ in all_cells) + 1
    w = max(c for _, _, c in all_cells) + 1
    rotated: list[list[tuple[int, int]]] = [[] for _ in groups]
    for gi, r, c in all_cells:
        rr, cc = r, c
        hh, ww = h, w
        for _ in range(turns % 4):
            rr, cc = cc, hh - 1 - rr
            hh, ww = ww, hh
        rotated[gi].append((rr, cc))
    min_r = min(r for group in rotated for r, _ in group)
    min_c = min(c for group in rotated for _, c in group)
    return [tuple(sorted((r - min_r, c - min_c) for r, c in group)) for group in rotated]


def _can_place(cells: frozenset[tuple[int, int]], occupied: set[tuple[int, int]], h: int, w: int, forbidden: set[tuple[int, int]]) -> bool:
    if any(not (0 <= r < h and 0 <= c < w) or (r, c) in occupied or (r, c) in forbidden for r, c in cells):
        return False
    return not any((r + dr, c + dc) in occupied for r, c in cells for dr, dc in CARDINALS)


def _place_component(base: tuple[tuple[int, int], ...], h: int, w: int, occupied: set[tuple[int, int]], forbidden: set[tuple[int, int]], rng: random.Random) -> frozenset[tuple[int, int]]:
    shape = _rotate(base, rng.randrange(4))
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    candidates = [(r, c) for r in range(h - sh + 1) for c in range(w - sw + 1)]
    rng.shuffle(candidates)
    for top, left in candidates:
        cells = _shift(shape, top, left)
        if _can_place(cells, occupied, h, w, forbidden):
            return cells
    raise RuntimeError("unable to place separated distractor component")


def sample_input(seed: int, split: str, index: int) -> list[list[int]]:
    _exact_int("seed", seed, 0, MAX_SEED)
    if split not in ("train", "test"):
        raise ValueError("split must be 'train' or 'test'")
    profiles = TRAIN_PROFILES if split == "train" else QUERY_PROFILES
    _exact_int("index", index, 0, len(profiles) - 1)
    h, w, turns, cluster_first = profiles[index]
    rng = _rng(seed, split, index)

    pair_groups = [TARGET_A, tuple((r, c + 2) for r, c in TARGET_B)]
    pair_a, pair_b = _rotate_group(pair_groups, turns)
    pair_h = max(r for group in (pair_a, pair_b) for r, _ in group) + 1
    pair_w = max(c for group in (pair_a, pair_b) for _, c in group) + 1
    if cluster_first:
        pair_top, pair_left = 1, 1
        iso_top, iso_left = h - 4, w - 4
    else:
        pair_top, pair_left = h - pair_h - 2, w - pair_w - 2
        iso_top, iso_left = 1, 1
    target1 = _shift(pair_a, pair_top, pair_left)
    target2 = _shift(pair_b, pair_top, pair_left)
    isolated_shape = _rotate(TARGET_A, turns)
    target3 = _shift(isolated_shape, iso_top, iso_left)

    # The two cluster objects remain separate red components but their 2x2
    # bboxes touch. The isolated object shares target1's exact orientation.
    occupied = set(target1 | target2 | target3)
    if len(_components([[2 if (r, c) in occupied else 0 for c in range(w)] for r in range(h)], 2)) != 3:
        raise RuntimeError("target construction merged before stage A")
    forbidden: set[tuple[int, int]] = set()
    for cells in (target1, target2, target3):
        r1, c1, r2, c2 = _bbox(cells)
        forbidden.update((r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1))

    components = [target1, target2, target3]
    for base in DISTRACTOR_BASES:
        for _ in range(2):
            cells = _place_component(base, h, w, occupied, forbidden, rng)
            components.append(cells)
            occupied.update(cells)

    grid = [[0 for _ in range(w)] for _ in range(h)]
    for cells in components:
        for r, c in cells:
            grid[r][c] = 2

    scene = analyze(grid)
    counts = sorted(len(values) for values in scene["groups"].values())
    if counts != [2, 2, 2, 3]:
        raise RuntimeError(f"constructed class multiplicities changed: {counts}")
    intermediate = canonical_intermediate(grid)
    orange = _components(intermediate, 7)
    if sorted(map(len, orange)) != [4, 8]:
        raise RuntimeError("stage A did not create the intended 4/8 orange clusters")
    return grid


def generate(seed: int, settings: Any, demos: int = 3, queries: int = 4) -> dict[str, Any]:
    _exact_int("seed", seed, 0, MAX_SEED)
    _finish(settings)
    _exact_int("demos", demos, MIN_DEMOS, MAX_DEMOS)
    _exact_int("queries", queries, MIN_QUERIES, MAX_QUERIES)
    train = [
        {"input": (grid := sample_input(seed, "train", index)), "output": solve(grid, settings)}
        for index in range(demos)
    ]
    test = [
        {"input": (grid := sample_input(seed, "test", index)), "output": solve(grid, settings)}
        for index in range(queries)
    ]
    fingerprints = [json.dumps(pair["input"], separators=(",", ":")) for pair in train + test]
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
        raise RuntimeError("constructed demonstrations leave declared rivals alive: " + ", ".join(certificate["surviving_rivals"]))
    episode["teaching"] = certificate
    return episode


def public_turn(episode: Any, query_index: Any = 0) -> dict[str, Any]:
    if type(episode) is not dict or type(episode.get("train")) is not list or type(episode.get("test")) is not list:
        raise ValueError("episode must contain train/test lists")
    test = episode["test"]
    _exact_int("query_index", query_index, 0, len(test) - 1)
    query = {"input": deepcopy(test[query_index]["input"])}
    if query_index == 0:
        return {
            "train": [{"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])} for pair in episode["train"]],
            "test": [query],
        }
    return {"test": [query]}


__all__ = [
    "DEFAULT", "SETTINGS", "analyze", "canonical_intermediate", "dependency_trace",
    "generate", "program", "public_turn", "rival_outputs", "sample_input", "solve",
    "teaching_check", "wrong_intermediate_solve",
]
