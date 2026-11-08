"""Parametric orbit-completion family for ARC task ba0c6a5828f9.

The default setting returns the exact selected canonical program.  The alternate
setting computes every source marker's in-bounds quarter-turn orbit, selects the
unique orbit with the fewest visible members, and completes only that orbit.
Input sampling is independent of the private setting and split-prefix stable.
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Iterable, Sequence


TASK_ID = "ba0c6a5828f9"
PARAMETER = "completion_scope"
SCOPES = ("all_orbits", "most_clipped")
DEFAULT_SCOPE = "all_orbits"
MIN_DEMOS, MAX_DEMOS = 2, 6
MIN_QUERIES, MAX_QUERIES = 1, 4
MAX_SEED = 2**63 - 1
HOME = Path(__file__).resolve().parent
PROGRAMS = {
    "all_orbits": (HOME / "rules/canonical.rkt").read_text(encoding="utf-8"),
    "most_clipped": (HOME / "rules/most_clipped.rkt").read_text(encoding="utf-8"),
}

Grid = list[list[int]]
Cell = tuple[int, int]

# (height, width, unique minimum visible count, marker count, include count-3 rival)
DEMO_PROFILES = (
    (7, 9, 2, 5, True),
    (9, 11, 3, 5, False),
    (12, 14, 2, 7, True),
    (16, 17, 3, 8, False),
    (20, 23, 2, 10, True),
    (25, 27, 3, 12, False),
)
QUERY_PROFILES = (
    (10, 12, 2, 6, True),
    (16, 19, 3, 8, False),
    (24, 27, 2, 12, True),
    (30, 30, 2, 16, True),
)
RIVAL_NAMES = (
    "all_orbits",
    "most_clipped",
    "least_clipped",
    "first_marker",
    "last_marker",
    "nearest_pivot",
    "farthest_pivot",
    "complete_only",
    "clipped_only",
    "first_partial",
)


def _setting(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {PARAMETER}:
        raise ValueError(f"settings must name exactly {PARAMETER!r}")
    value = settings[PARAMETER]
    if type(value) is not str or value not in SCOPES:
        raise ValueError(f"{PARAMETER} must be one of {SCOPES}")
    return value


def _integer(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def program(settings: Any) -> str:
    return PROGRAMS[_setting(settings)]


def _grid(grid: Any) -> Grid:
    if (type(grid) is not list or not 1 <= len(grid) <= 30 or type(grid[0]) is not list
            or not 1 <= len(grid[0]) <= 30):
        raise ValueError("grid must have 1..30 rows and columns")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(cell) is not int or cell not in (0, 1, 2) for cell in row)
           for row in grid):
        raise ValueError("grid must be rectangular with exact colors 0, 1, 2")
    return deepcopy(grid)


def pivot_cell(grid: Sequence[Sequence[int]]) -> Cell:
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2]
    if len(cells) != 1:
        raise ValueError(f"expected exactly one red pivot, found {len(cells)}")
    return cells[0]


def marker_cells(grid: Sequence[Sequence[int]]) -> list[Cell]:
    return [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 1]


def orbit_all(point: Cell, pivot: Cell) -> tuple[Cell, Cell, Cell, Cell]:
    r, c = point
    pr, pc = pivot
    dr, dc = r - pr, c - pc
    return ((pr + dr, pc + dc), (pr + dc, pc - dr),
            (pr - dr, pc - dc), (pr - dc, pc + dr))


def visible_orbit(point: Cell, pivot: Cell, height: int, width: int) -> tuple[Cell, ...]:
    return tuple(cell for cell in orbit_all(point, pivot)
                 if 0 <= cell[0] < height and 0 <= cell[1] < width)


def selector_info(grid: Any) -> dict[str, Any]:
    value = _grid(grid)
    pivot = pivot_cell(value)
    markers = marker_cells(value)
    if len(markers) < 2:
        raise ValueError("at least two blue markers are required")
    rows = []
    seen = set()
    for marker in markers:
        key = tuple(sorted(orbit_all(marker, pivot)))
        if key in seen:
            raise ValueError("source markers must occupy distinct rotation orbits")
        seen.add(key)
        visible = visible_orbit(marker, pivot, len(value), len(value[0]))
        rows.append({"marker": list(marker), "visible": [list(cell) for cell in visible],
                     "visible_count": len(visible), "distance2": (marker[0] - pivot[0]) ** 2 + (marker[1] - pivot[1]) ** 2})
    minimum = min(row["visible_count"] for row in rows)
    selected = [row for row in rows if row["visible_count"] == minimum]
    if len(selected) != 1:
        raise ValueError("most-clipped selector must have a unique minimum")
    return {"pivot": list(pivot), "selected": selected[0]["marker"],
            "selected_visible_count": minimum, "markers": rows}


def _paint(grid: Grid, points: Iterable[Cell]) -> Grid:
    out = deepcopy(grid)
    for r, c in points:
        if 0 <= r < len(out) and 0 <= c < len(out[0]):
            out[r][c] = 1
    return out


def _selected_markers(grid: Grid, mode: str) -> list[Cell]:
    pivot = pivot_cell(grid)
    markers = marker_cells(grid)
    if not markers:
        raise ValueError("at least one blue marker is required")
    counts = {m: len(visible_orbit(m, pivot, len(grid), len(grid[0]))) for m in markers}
    distances = {m: (m[0] - pivot[0]) ** 2 + (m[1] - pivot[1]) ** 2 for m in markers}
    if mode == "all_orbits":
        return markers
    if mode == "most_clipped":
        minimum = min(counts.values())
        chosen = [m for m in markers if counts[m] == minimum]
        if len(chosen) != 1:
            raise ValueError("most-clipped selector must have a unique minimum")
        return chosen
    if mode == "least_clipped":
        return [max(markers, key=lambda m: (counts[m], -markers.index(m)))]
    if mode == "first_marker":
        return [markers[0]]
    if mode == "last_marker":
        return [markers[-1]]
    if mode == "nearest_pivot":
        return [min(markers, key=lambda m: (distances[m], markers.index(m)))]
    if mode == "farthest_pivot":
        return [max(markers, key=lambda m: (distances[m], -markers.index(m)))]
    if mode == "complete_only":
        return [m for m in markers if counts[m] == 4]
    if mode == "clipped_only":
        return [m for m in markers if counts[m] < 4]
    if mode == "first_partial":
        partial = [m for m in markers if counts[m] < 4]
        return partial[:1]
    raise ValueError(f"unknown rival {mode!r}")


def solve_rival(grid: Any, mode: str) -> Grid:
    value = _grid(grid)
    pivot = pivot_cell(value)
    points = []
    for marker in _selected_markers(value, mode):
        points.extend(visible_orbit(marker, pivot, len(value), len(value[0])))
    return _paint(value, points)


def solve(grid: Any, settings: Any) -> Grid:
    return solve_rival(grid, _setting(settings))


def demo_rival_failures(demos: Any, settings: Any) -> list[str]:
    selected = _setting(settings)
    if type(demos) is not list or len(demos) < 1:
        raise ValueError("demos must be a nonempty list")
    failures = []
    for rival in RIVAL_NAMES:
        if rival == selected:
            continue
        if all(solve_rival(row["input"], rival) == row["output"] for row in demos):
            failures.append(rival)
    return failures


def _seed_value(seed: int, split: str, index: int, salt: int, attempt: int) -> int:
    raw = f"{TASK_ID}|{seed}|{split}|{index}|{salt}|{attempt}".encode()
    return int.from_bytes(hashlib.sha256(raw).digest()[:16], "big")


@lru_cache(maxsize=None)
def _orbit_groups(height: int, width: int, pivot: Cell) -> tuple[dict[str, Any], ...]:
    seen = set()
    result = []
    for r in range(height):
        for c in range(width):
            if (r, c) == pivot:
                continue
            full = tuple(sorted(orbit_all((r, c), pivot)))
            if full in seen:
                continue
            seen.add(full)
            visible = tuple(cell for cell in full if 0 <= cell[0] < height and 0 <= cell[1] < width)
            result.append({"key": full, "visible": visible, "count": len(visible)})
    return tuple(result)


def _required_three_count(height: int, width: int, target_count: int,
                          marker_count: int, include_three: bool) -> int:
    if not include_three or target_count == 3:
        return 0
    return 1


@lru_cache(maxsize=None)
def _feasible_pivots(height: int, width: int, target_count: int, marker_count: int,
                     include_three: bool) -> tuple[Cell, ...]:
    if (height, width, target_count, include_three) == (30, 30, 2, True):
        # Exactly one lattice step outside the central 2x2 block.  These
        # pivots admit count-2, count-3, and complete orbits while allowing a
        # source marker from the selected count-2 orbit to reach the one edge
        # unavailable to count-3/4 distractors.
        return ((13, 14), (13, 15), (14, 13), (14, 16),
                (15, 13), (15, 16), (16, 14), (16, 15))
    required_three = _required_three_count(height, width, target_count, marker_count, include_three)
    needed_full = marker_count - 1 - required_three
    candidates = []
    for pr in range(1, height - 1):
        for pc in range(1, width - 1):
            groups = _orbit_groups(height, width, (pr, pc))
            counts = {n: sum(row["count"] == n for row in groups) for n in range(1, 5)}
            if (counts[target_count] < 1 or counts[3] < required_three
                    or counts[4] < needed_full):
                continue
            candidates.append((pr, pc))
    return tuple(candidates)


def _boundary_distance(cell: Cell, height: int, width: int) -> int:
    r, c = cell
    return min(r, c, height - 1 - r, width - 1 - c)


def _choose_source(group: dict[str, Any], rng: random.Random, *, prefer_interior: bool = False) -> Cell:
    members = list(group["visible"])
    rng.shuffle(members)
    key = (lambda p: _boundary_distance(p, 10**6, 10**6)) if False else None
    if prefer_interior:
        members.sort(key=lambda p: min(p[0], p[1]), reverse=True)
    return members[0]


def _greedy_full_sources(groups: list[dict[str, Any]], count: int, chosen: list[Cell],
                         height: int, width: int, rng: random.Random) -> list[tuple[dict[str, Any], Cell]]:
    pool = [(group, source) for group in groups for source in group["visible"]]
    selected = []
    used = set()
    while len(selected) < count:
        scored = []
        existing = chosen + [source for _, source in selected]
        occupied_quadrants = {(r >= height / 2, c >= width / 2) for r, c in existing}
        for group, source in pool:
            if group["key"] in used:
                continue
            r, c = source
            quadrant = (r >= height / 2, c >= width / 2)
            spread = min(((r - rr) ** 2 + (c - cc) ** 2 for rr, cc in existing), default=height * width)
            edge = max(0, 3 - _boundary_distance(source, height, width))
            missing_quadrant = 1 if quadrant not in occupied_quadrants else 0
            anchor = int(r <= 1) + int(r >= height - 2) + int(c <= 1) + int(c >= width - 2)
            score = missing_quadrant * 100000 + anchor * 20000 + edge * 1000 + spread
            scored.append((score, rng.random(), group, source))
        if not scored:
            raise ValueError("not enough distinct complete orbit groups")
        _, _, group, source = max(scored, key=lambda row: (row[0], row[1]))
        used.add(group["key"])
        selected.append((group, source))
    return selected


def _stress_features(source: Cell, orbit_count: int, height: int, width: int) -> set[str]:
    r, c = source
    features = {f"q{int(r >= height / 2)}{int(c >= width / 2)}", f"type{orbit_count}"}
    if r <= 1:
        features.add("top")
    if r >= height - 2:
        features.add("bottom")
    if c <= 1:
        features.add("left")
    if c >= width - 2:
        features.add("right")
    return features


def _stress_sources(groups: list[dict[str, Any]], target: dict[str, Any], marker_count: int,
                    height: int, width: int, rng: random.Random) -> list[Cell] | None:
    required = {"top", "bottom", "left", "right", "q00", "q01", "q10", "q11",
                "type3", "type4"}
    targets = list(target["visible"])
    rng.shuffle(targets)
    distractors = [group for group in groups
                   if group["key"] != target["key"] and group["count"] in (3, 4)]
    for target_source in targets:
        selected: list[tuple[dict[str, Any], Cell]] = []
        used = {target["key"]}
        covered = _stress_features(target_source, 2, height, width)
        # Greedily cover the ten structural obligations.  At each step use a
        # fresh orbit and prefer the source that satisfies the most still-
        # missing obligations; random tie-breaking keeps seed variation.
        while not required <= covered and len(selected) < marker_count - 1:
            missing = required - covered
            choices = []
            for group in distractors:
                if group["key"] in used:
                    continue
                for source in group["visible"]:
                    features = _stress_features(source, group["count"], height, width)
                    gain = len(features & missing)
                    if gain:
                        edge_gain = len(features & missing & {"top", "bottom", "left", "right"})
                        choices.append((gain, edge_gain, rng.random(), group, source, features))
            if not choices:
                break
            _, _, _, group, source, features = max(
                choices, key=lambda row: (row[0], row[1], row[2]))
            used.add(group["key"])
            selected.append((group, source))
            covered.update(features)
        if not required <= covered:
            continue

        remaining = [group for group in distractors if group["key"] not in used]
        need = marker_count - 1 - len(selected)
        try:
            fill = _greedy_full_sources(
                remaining, need, [target_source] + [source for _, source in selected],
                height, width, rng)
        except ValueError:
            continue
        return [target_source] + [source for _, source in selected + fill]
    return None


def _scene_features_ok(grid: Grid, *, stress: bool) -> bool:
    info = selector_info(grid)
    counts = [row["visible_count"] for row in info["markers"]]
    if counts.count(min(counts)) != 1 or min(counts) not in (2, 3) or 4 not in counts:
        return False
    if stress:
        markers = marker_cells(grid)
        if len(markers) < 14:
            return False
        if not (min(r for r, _ in markers) <= 1 and max(r for r, _ in markers) >= len(grid) - 2
                and min(c for _, c in markers) <= 1 and max(c for _, c in markers) >= len(grid[0]) - 2):
            return False
        if {(r >= len(grid) / 2, c >= len(grid[0]) / 2) for r, c in markers} != {
                (False, False), (False, True), (True, False), (True, True)}:
            return False
    return True


def _build_scene(seed: int, split: str, index: int, salt: int,
                 profile: tuple[int, int, int, int, bool]) -> Grid:
    height, width, target_count, marker_count, include_three = profile
    pivots = _feasible_pivots(height, width, target_count, marker_count, include_three)
    if not pivots:
        raise ValueError(f"no feasible pivots for {profile}")
    for attempt in range(96):
        rng = random.Random(_seed_value(seed, split, index, salt, attempt))
        pivot = rng.choice(pivots)
        groups = list(_orbit_groups(height, width, pivot))
        targets = [row for row in groups if row["count"] == target_count]
        target = rng.choice(targets)
        if (height, width) == (30, 30):
            sources = _stress_sources(groups, target, marker_count, height, width, rng)
            if sources is None:
                continue
            grid = [[0] * width for _ in range(height)]
            grid[pivot[0]][pivot[1]] = 2
            for r, c in sources:
                grid[r][c] = 1
            try:
                if not _scene_features_ok(grid, stress=True):
                    continue
                if solve_rival(grid, "all_orbits") == solve_rival(grid, "most_clipped"):
                    continue
            except ValueError:
                continue
            return grid
        target_members = list(target["visible"])
        rng.shuffle(target_members)
        target_members.sort(key=lambda p: _boundary_distance(p, height, width), reverse=True)
        target_source = target_members[0]
        chosen_groups = {target["key"]}
        chosen_sources = [target_source]
        required_three = _required_three_count(height, width, target_count, marker_count, include_three)
        thirds = [row for row in groups if row["count"] == 3 and row["key"] not in chosen_groups]
        try:
            three_selected = _greedy_full_sources(
                thirds, required_three, chosen_sources, height, width, rng)
        except ValueError:
            continue
        chosen_groups.update(group["key"] for group, _ in three_selected)
        chosen_sources.extend(source for _, source in three_selected)
        full = [row for row in groups if row["count"] == 4 and row["key"] not in chosen_groups]
        need = marker_count - len(chosen_sources)
        try:
            full_selected = _greedy_full_sources(full, need, chosen_sources, height, width, rng)
        except ValueError:
            continue
        sources = chosen_sources + [source for _, source in full_selected]
        if len(set(sources)) != len(sources) or pivot in sources:
            continue
        grid = [[0] * width for _ in range(height)]
        grid[pivot[0]][pivot[1]] = 2
        for r, c in sources:
            grid[r][c] = 1
        try:
            if not _scene_features_ok(grid, stress=(height, width) == (30, 30)):
                continue
            if solve_rival(grid, "all_orbits") == solve_rival(grid, "most_clipped"):
                continue
        except ValueError:
            continue
        return grid
    raise ValueError(f"could not construct scene {split}[{index}] profile={profile}")


@lru_cache(maxsize=None)
def _lesson_salt(seed: int) -> int:
    for salt in range(64):
        demos = [_build_scene(seed, "train", i, salt, DEMO_PROFILES[i]) for i in range(2)]
        ok = True
        for scope in SCOPES:
            labelled = [{"input": grid, "output": solve(grid, {PARAMETER: scope})} for grid in demos]
            if demo_rival_failures(labelled, {PARAMETER: scope}):
                ok = False
                break
        if ok:
            return salt
    raise ValueError(f"could not construct a two-demo identifying lesson for seed {seed}")


def sample_inputs(seed: Any, demos: Any = 3, queries: Any = 4) -> dict[str, list[Grid]]:
    seed = _integer(seed, 0, MAX_SEED, "seed")
    demos = _integer(demos, MIN_DEMOS, MAX_DEMOS, "demos")
    queries = _integer(queries, MIN_QUERIES, MAX_QUERIES, "queries")
    salt = _lesson_salt(seed)
    train = [_build_scene(seed, "train", i, salt, DEMO_PROFILES[i]) for i in range(demos)]
    test = [_build_scene(seed, "test", i, salt, QUERY_PROFILES[i]) for i in range(queries)]
    serial = [json.dumps(grid, separators=(",", ":")) for grid in train + test]
    if len(serial) != len(set(serial)):
        raise ValueError("all demonstration and query inputs must be distinct")
    return {"train": train, "test": test}


def generate(seed: Any, settings: Any, demos: Any = 3, queries: Any = 4) -> dict[str, Any]:
    scope = _setting(settings)
    seed = _integer(seed, 0, MAX_SEED, "seed")
    demos = _integer(demos, MIN_DEMOS, MAX_DEMOS, "demos")
    queries = _integer(queries, MIN_QUERIES, MAX_QUERIES, "queries")
    sampled = sample_inputs(seed, demos, queries)
    result = {
        "train": [{"input": grid, "output": solve(grid, {PARAMETER: scope})} for grid in sampled["train"]],
        "test": [{"input": grid, "output": solve(grid, {PARAMETER: scope})} for grid in sampled["test"]],
        "program_solution": PROGRAMS[scope],
        "settings": {PARAMETER: scope},
        "seed": seed,
        "training_admitted": False,
        "variant_approved": False,
    }
    failures = demo_rival_failures(result["train"], result["settings"])
    if failures:
        raise ValueError(f"demonstrations leave named rivals alive: {failures}")
    return result


def public_turn(episode: Any, index: Any) -> dict[str, Any]:
    if type(episode) is not dict or type(index) is not int:
        raise ValueError("episode and exact integer turn index required")
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or type(test) is not list or not 0 <= index < len(test):
        raise ValueError("turn index is outside the episode")
    return {"train": [{"input": deepcopy(row["input"]), "output": deepcopy(row["output"])} for row in train],
            "test": [{"input": deepcopy(test[index]["input"])}]}


def public_turn_bytes(episode: Any, index: Any) -> bytes:
    return (json.dumps(public_turn(episode, index), sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False) + "\n").encode("utf-8")


def public_turn_id(episode: Any, index: Any) -> str:
    return hashlib.sha256(public_turn_bytes(episode, index)).hexdigest()


# Racket rivals for the bounded authoring audit. The two declared programs are
# exact files; the others share the same orbit arithmetic but change selection.
def _racket_single_selector(name: str, expression: str, *, score: str | None = None,
                            comparison: str = "<") -> str:
    score_def = ""
    if score is not None:
        score_def = f"\n      (define (score p) {score})"
    return f"""(rule!\n  (lambda (g)\n    (let* ((pivot (first (find-color g 2)))\n           (pr (first pivot))\n           (pc (second pivot))\n           (markers (find-color g 1)))\n      (define (rotations p)\n        (let* ((dr (- (first p) pr)) (dc (- (second p) pc)))\n          (list (list dr dc) (list dc (- dr))\n                (list (- dr) (- dc)) (list (- dc) dr))))\n      (define (visible-count p)\n        (length (filter (lambda (d)\n          (in-bounds? (+ pr (first d)) (+ pc (second d)) (rows g) (cols g)))\n          (rotations p)))){score_def}\n      (define selected {expression})\n      (foldl (lambda (d acc)\n        (let ((nr (+ pr (first d))) (nc (+ pc (second d))))\n          (if (in-bounds? nr nc (rows g) (cols g)) (set-cell acc nr nc 1) acc)))\n        g (rotations selected)))))\n"""


def _racket_filtered(predicate: str) -> str:
    return f"""(rule!\n  (lambda (g)\n    (let* ((pivot (first (find-color g 2)))\n           (pr (first pivot)) (pc (second pivot))\n           (markers (find-color g 1)))\n      (define (rotations p)\n        (let* ((dr (- (first p) pr)) (dc (- (second p) pc)))\n          (list (list dr dc) (list dc (- dr))\n                (list (- dr) (- dc)) (list (- dc) dr))))\n      (define (visible-count p)\n        (length (filter (lambda (d)\n          (in-bounds? (+ pr (first d)) (+ pc (second d)) (rows g) (cols g)))\n          (rotations p))))\n      (foldl (lambda (p out)\n        (foldl (lambda (d acc)\n          (let ((nr (+ pr (first d))) (nc (+ pc (second d))))\n            (if (in-bounds? nr nc (rows g) (cols g)) (set-cell acc nr nc 1) acc)))\n          out (rotations p)))\n        g (filter (lambda (p) {predicate}) markers)))))\n"""


RIVAL_PROGRAMS = {
    "all_orbits": PROGRAMS["all_orbits"],
    "most_clipped": PROGRAMS["most_clipped"],
    "least_clipped": _racket_single_selector(
        "least_clipped",
        "(foldl (lambda (p best) (if (> (visible-count p) (visible-count best)) p best)) (first markers) (rest markers))"),
    "first_marker": _racket_single_selector("first_marker", "(first markers)"),
    "last_marker": _racket_single_selector("last_marker", "(nth markers (- (length markers) 1))"),
    "nearest_pivot": _racket_single_selector(
        "nearest_pivot",
        "(foldl (lambda (p best) (if (< (score p) (score best)) p best)) (first markers) (rest markers))",
        score="(let ((dr (- (first p) pr)) (dc (- (second p) pc))) (+ (* dr dr) (* dc dc)))"),
    "farthest_pivot": _racket_single_selector(
        "farthest_pivot",
        "(foldl (lambda (p best) (if (> (score p) (score best)) p best)) (first markers) (rest markers))",
        score="(let ((dr (- (first p) pr)) (dc (- (second p) pc))) (+ (* dr dr) (* dc dc)))"),
    "complete_only": _racket_filtered("(= (visible-count p) 4)"),
    "clipped_only": _racket_filtered("(< (visible-count p) 4)"),
    "first_partial": _racket_single_selector(
        "first_partial", "(first (filter (lambda (p) (< (visible-count p) 4)) markers))"),
}
