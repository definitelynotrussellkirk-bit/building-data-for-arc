"""Native parametric adapter for ``97c9b7818f99``.

``fill_only`` is the byte-exact canonical Manhattan Voronoi fill.  The nearby
``highlight_smallest_region`` setting first constructs the same input-dependent
nearest-seed ownership partition, then counts each seed's uniquely owned cells
(including the seed), selects the unique smallest region, and recolors exactly
that region to 9.  True tie cells stay gray even when gray itself is an input
seed, so the second stage cannot be reduced to counting output colors.
"""
from __future__ import annotations

from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Iterable

TASK_ID = "97c9b7818f99"
HERE = Path(__file__).resolve().parent
MODES = ("fill_only", "highlight_smallest_region")
HYPOTHESES = MODES + (
    "highlight_largest_region",
    "highlight_second_smallest_region",
    "highlight_lowest_color",
    "highlight_highest_color",
    "highlight_smallest_seed_only",
    "highlight_smallest_bbox",
    "highlight_smallest_color_frequency",
    "euclidean_smallest_region",
    "identity",
)

# Dimensions, seed count, and whether gray is a genuine input seed.  The first
# two profiles are deliberately complementary so the minimum two-demo lesson
# exposes gray's dual role and a non-gray case.
_DEMO_PROFILES: tuple[tuple[int, int, int, bool], ...] = (
    (9, 11, 4, True),
    (10, 12, 3, False),
    (12, 14, 4, False),
    (14, 16, 3, True),
    (18, 20, 4, False),
    (22, 24, 4, True),
)
_QUERY_PROFILES: tuple[tuple[int, int, int, bool], ...] = (
    (13, 17, 3, True),
    (18, 21, 4, True),
    (24, 27, 4, False),
    (30, 30, 4, True),
)
_SEED_PALETTE = (1, 2, 3, 4, 5, 6, 7)


def _integer(value: object, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _mode(value: object) -> str:
    if type(value) is not str or value not in MODES:
        raise ValueError(f"finish must be one of {MODES!r}")
    return value


def _settings(value: object) -> dict[str, str]:
    if type(value) is not dict or set(value) != {"finish"}:
        raise ValueError("settings must contain exactly the finish key")
    return {"finish": _mode(value["finish"])}


def _copy(value: list[list[int]]) -> list[list[int]]:
    return [row[:] for row in value]


def grid(value: object) -> list[list[int]]:
    if (
        type(value) is not list
        or not 3 <= len(value) <= 30
        or type(value[0]) is not list
        or not 3 <= len(value[0]) <= 30
        or any(
            type(row) is not list
            or len(row) != len(value[0])
            or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
            for row in value
        )
    ):
        raise ValueError("grid must be rectangular 3..30 with exact integer colors 0..9")
    return value


@lru_cache(maxsize=1)
def canonical_program() -> str:
    return (HERE / "canonical.rkt").read_text(encoding="utf-8")


@lru_cache(maxsize=1)
def alternative_program() -> str:
    return (HERE / "highlight_smallest_region.rkt").read_text(encoding="utf-8")


def program(settings: object) -> str:
    selected = _settings(settings)["finish"]
    return canonical_program() if selected == "fill_only" else alternative_program()


def _seeds(source: list[list[int]]) -> list[tuple[int, int, int]]:
    return [
        (r, c, value)
        for r, row in enumerate(source)
        for c, value in enumerate(row)
        if value not in (0, 8)
    ]


def _distance(seed: tuple[int, int, int], r: int, c: int, *, squared: bool) -> int:
    dr = r - seed[0]
    dc = c - seed[1]
    return dr * dr + dc * dc if squared else abs(dr) + abs(dc)


def _partition(
    source: list[list[int]], *, squared: bool = False
) -> tuple[list[tuple[int, int, int]], dict[int, set[tuple[int, int]]], set[tuple[int, int]]]:
    seeds = _seeds(source)
    owned = {index: set() for index in range(len(seeds))}
    ties: set[tuple[int, int]] = set()
    for r in range(1, len(source) - 1):
        for c in range(1, len(source[0]) - 1):
            distances = [_distance(seed, r, c, squared=squared) for seed in seeds]
            minimum = min(distances)
            owners = [index for index, distance in enumerate(distances) if distance == minimum]
            if len(owners) == 1:
                owned[owners[0]].add((r, c))
            else:
                ties.add((r, c))
    return seeds, owned, ties


def _fill(source: list[list[int]], *, squared: bool = False) -> list[list[int]]:
    seeds, owned, ties = _partition(source, squared=squared)
    out = _copy(source)
    for index, cells in owned.items():
        color = seeds[index][2]
        for r, c in cells:
            if out[r][c] == 0:
                out[r][c] = color
    for r, c in ties:
        if out[r][c] == 0:
            out[r][c] = 5
    return out


def _ranked_regions(source: list[list[int]], *, squared: bool = False):
    seeds, owned, ties = _partition(source, squared=squared)
    ranked = sorted(
        range(len(seeds)),
        key=lambda index: (len(owned[index]), seeds[index][2]),
    )
    return seeds, owned, ties, ranked


def _highlight_owner(
    source: list[list[int]], index: int, *, squared: bool = False
) -> list[list[int]]:
    seeds, owned, _ties = _partition(source, squared=squared)
    out = _fill(source, squared=squared)
    for r, c in owned[index]:
        out[r][c] = 9
    return out


def _highlight_bbox(source: list[list[int]], index: int) -> list[list[int]]:
    seeds, owned, _ties = _partition(source)
    out = _fill(source)
    cells = owned[index]
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            out[r][c] = 9
    return out


def _color_frequency_smallest(source: list[list[int]]) -> list[list[int]]:
    filled = _fill(source)
    colors = [seed[2] for seed in _seeds(source)]
    chosen = min(
        colors,
        key=lambda color: (
            sum(value == color for row in filled for value in row),
            color,
        ),
    )
    return [[9 if value == chosen else value for value in row] for row in filled]


def transform(value: object, finish: object) -> list[list[int]]:
    selected = _mode(finish)
    source = _copy(grid(value))
    observe(source)
    if selected == "fill_only":
        return _fill(source)
    seeds, owned, _ties, ranked = _ranked_regions(source)
    del seeds, owned
    return _highlight_owner(source, ranked[0])


def _predict(value: list[list[int]], hypothesis: str) -> list[list[int]]:
    source = _copy(grid(value))
    info = observe(source)
    seeds, owned, _ties, ranked = _ranked_regions(source)
    if hypothesis == "fill_only":
        return _fill(source)
    if hypothesis == "highlight_smallest_region":
        return _highlight_owner(source, ranked[0])
    if hypothesis == "highlight_largest_region":
        return _highlight_owner(source, ranked[-1])
    if hypothesis == "highlight_second_smallest_region":
        return _highlight_owner(source, ranked[1])
    if hypothesis == "highlight_lowest_color":
        return _highlight_owner(source, min(range(len(seeds)), key=lambda i: seeds[i][2]))
    if hypothesis == "highlight_highest_color":
        return _highlight_owner(source, max(range(len(seeds)), key=lambda i: seeds[i][2]))
    if hypothesis == "highlight_smallest_seed_only":
        out = _fill(source)
        r, c, _color = seeds[ranked[0]]
        out[r][c] = 9
        return out
    if hypothesis == "highlight_smallest_bbox":
        return _highlight_bbox(source, ranked[0])
    if hypothesis == "highlight_smallest_color_frequency":
        return _color_frequency_smallest(source)
    if hypothesis == "euclidean_smallest_region":
        euclidean_seeds, _euclidean_owned, _euclidean_ties, euclidean_ranked = _ranked_regions(
            source, squared=True
        )
        del euclidean_seeds
        return _highlight_owner(source, euclidean_ranked[0], squared=True)
    if hypothesis == "identity":
        return source
    raise ValueError(f"unknown declared hypothesis {hypothesis!r}; info={info!r}")


def observe(value: object) -> dict[str, Any]:
    source = _copy(grid(value))
    h, w = len(source), len(source[0])
    if h < 7 or w < 8:
        raise ValueError("parametric grammar requires at least 7x8")
    for r in range(h):
        for c in range(w):
            boundary = r in (0, h - 1) or c in (0, w - 1)
            if boundary and source[r][c] != 8:
                raise ValueError("the complete outer border must be cyan (8)")
            if not boundary and source[r][c] == 8:
                raise ValueError("cyan (8) may appear only on the border")
    seeds = _seeds(source)
    if not 3 <= len(seeds) <= 4:
        raise ValueError("parametric grammar requires three or four seeds")
    colors = [seed[2] for seed in seeds]
    if len(set(colors)) != len(colors):
        raise ValueError("seed colors must be distinct")
    if any(color == 9 for color in colors):
        raise ValueError("color 9 is reserved for the alternative finish")
    if any(color not in _SEED_PALETTE for color in colors):
        raise ValueError("seed colors must come from 1..7 excluding cyan")
    seeds, owned, ties, ranked = _ranked_regions(source)
    region_sizes = {seeds[index][2]: len(owned[index]) for index in range(len(seeds))}
    smallest_size = len(owned[ranked[0]])
    if sum(size == smallest_size for size in region_sizes.values()) != 1:
        raise ValueError("the smallest ownership region must be unique")
    selected = seeds[ranked[0]]
    selected_cells = owned[ranked[0]]
    r0 = min(r for r, _ in selected_cells)
    r1 = max(r for r, _ in selected_cells)
    c0 = min(c for _, c in selected_cells)
    c1 = max(c for _, c in selected_cells)
    bbox_area = (r1 - r0 + 1) * (c1 - c0 + 1)
    return {
        "height": h,
        "width": w,
        "seed_count": len(seeds),
        "seeds": [list(seed) for seed in seeds],
        "seed_colors": colors,
        "includes_gray_seed": 5 in colors,
        "tie_count": len(ties),
        "region_sizes": region_sizes,
        "ranked_colors": [seeds[index][2] for index in ranked],
        "selected_color": selected[2],
        "selected_seed": list(selected),
        "selected_cells": [list(cell) for cell in sorted(selected_cells)],
        "selected_bbox_area": bbox_area,
        "selected_region_nonrectangular": bbox_area != len(selected_cells),
        "manhattan_euclidean_disagree": _fill(source) != _fill(source, squared=True),
    }


def explain_dependency(value: object) -> dict[str, object]:
    source = _copy(grid(value))
    info = observe(source)
    return {
        "step_a": "fill every empty interior cell by Manhattan-nearest seed and retain the unique-owner partition",
        "intermediate": {
            "region_sizes": {str(k): v for k, v in info["region_sizes"].items()},
            "selected_color": info["selected_color"],
            "tie_count": info["tie_count"],
        },
        "step_b": "recolor every cell uniquely owned by the smallest region's seed to 9 while preserving tie cells",
        "final": transform(source, "highlight_smallest_region"),
    }


def _rng(seed: int, split: str, index: int, purpose: str) -> random.Random:
    payload = f"97c9b7818f99-parametric-v1:{seed}:{split}:{index}:{purpose}".encode()
    return random.Random(hashlib.sha256(payload).digest())


def _zones(h: int, w: int, n_seeds: int, *, stress: bool) -> list[tuple[range, range]]:
    if stress:
        return [
            (range(1, 6), range(1, 6)),
            (range(1, 7), range(w - 6, w - 1)),
            (range(h - 6, h - 1), range(1, 7)),
            (range(h // 2 - 2, h - 5), range(w // 2 + 1, w - 5)),
        ]
    if n_seeds == 3:
        return [
            (range(1, max(2, h // 3 + 1)), range(1, max(2, w // 3 + 1))),
            (range(1, max(2, h // 2 + 1)), range(max(1, 2 * w // 3), w - 1)),
            (range(max(1, 2 * h // 3), h - 1), range(max(1, w // 3), min(w - 1, 2 * w // 3 + 1))),
        ]
    return [
        (range(1, max(2, h // 3 + 1)), range(1, max(2, w // 3 + 1))),
        (range(1, max(2, h // 3 + 2)), range(max(1, 2 * w // 3), w - 1)),
        (range(max(1, 2 * h // 3), h - 1), range(1, max(2, w // 3 + 2))),
        (range(max(1, h // 2), h - 2), range(max(1, w // 2), w - 2)),
    ]


def _sample_positions(
    h: int,
    w: int,
    n_seeds: int,
    rng: random.Random,
    *,
    stress: bool,
    require_gray_confound: bool,
) -> tuple[list[tuple[int, int]], int]:
    zones = _zones(h, w, n_seeds, stress=stress)
    for _attempt in range(2000):
        positions = [
            (rng.choice(tuple(rows)), rng.choice(tuple(cols)))
            for rows, cols in zones
        ]
        if len(set(positions)) != n_seeds:
            continue
        if min(
            abs(r1 - r2) + abs(c1 - c2)
            for index, (r1, c1) in enumerate(positions)
            for r2, c2 in positions[index + 1 :]
        ) < 3:
            continue
        provisional = [[0] * w for _ in range(h)]
        for c in range(w):
            provisional[0][c] = provisional[h - 1][c] = 8
        for r in range(h):
            provisional[r][0] = provisional[r][w - 1] = 8
        for index, (r, c) in enumerate(positions):
            provisional[r][c] = index + 1
        seeds, owned, ties, ranked = _ranked_regions(provisional)
        sizes = [len(owned[index]) for index in range(n_seeds)]
        if len(set(sizes)) != n_seeds:
            continue
        selected_owner_index = ranked[0]
        selected_position_index = positions.index(seeds[selected_owner_index][:2])
        selected_cells = owned[selected_owner_index]
        min_required = max(4, ((h - 2) * (w - 2)) // 40)
        if min(sizes) < min_required:
            continue
        if len(ties) < (10 if stress else 2):
            continue
        if selected_position_index in (0, n_seeds - 1):
            continue
        r0, r1 = min(r for r, _ in selected_cells), max(r for r, _ in selected_cells)
        c0, c1 = min(c for _, c in selected_cells), max(c for _, c in selected_cells)
        if (r1 - r0 + 1) * (c1 - c0 + 1) == len(selected_cells):
            continue
        if _fill(provisional) == _fill(provisional, squared=True):
            continue
        if stress:
            rows = [r for r, _ in positions]
            cols = [c for _, c in positions]
            if not (min(rows) <= 5 and max(rows) >= h - 6 and min(cols) <= 5 and max(cols) >= w - 6):
                continue
            if max(sizes) - min(sizes) < 20:
                continue
        # For gray-seed lessons the selected region will receive gray; enough
        # ties must inflate visible gray frequency so count-color selects a
        # different seed than the ownership table does.
        if require_gray_confound:
            gray_visible = sizes[selected_owner_index] + len(ties)
            if gray_visible <= sorted(sizes)[1]:
                continue
        return positions, selected_position_index
    raise ValueError(
        f"could not construct {h}x{w} scene with {n_seeds} seeds and required witnesses"
    )


def _assign_colors(
    n_seeds: int,
    selected_index: int,
    include_gray: bool,
    rng: random.Random,
) -> list[int]:
    if include_gray:
        if n_seeds < 3:
            raise ValueError("gray confound needs at least three seeds")
        low = rng.choice([1, 2, 3, 4])
        high = rng.choice([6, 7])
        pool = [color for color in [1, 2, 3, 4, 6, 7] if color not in (low, high)]
        others = [low, high, *rng.sample(pool, n_seeds - 3)]
        rng.shuffle(others)
        colors = others[:]
        colors.insert(selected_index, 5)
        return colors
    chosen = sorted(rng.sample([1, 2, 3, 4, 6, 7], n_seeds))
    middle_options = chosen[1:-1]
    selected_color = rng.choice(middle_options)
    remaining = [color for color in chosen if color != selected_color]
    rng.shuffle(remaining)
    colors: list[int] = []
    iterator = iter(remaining)
    for index in range(n_seeds):
        colors.append(selected_color if index == selected_index else next(iterator))
    return colors


@lru_cache(maxsize=256)
def _scene_template(seed: int, split: str, index: int) -> tuple[tuple[int, ...], ...]:
    profiles = _DEMO_PROFILES if split == "demo" else _QUERY_PROFILES
    h, w, n_seeds, include_gray = profiles[index]
    position_rng = _rng(seed, split, index, "positions")
    positions, selected_index = _sample_positions(
        h,
        w,
        n_seeds,
        position_rng,
        stress=split == "query" and index == 3,
        require_gray_confound=include_gray,
    )
    colors = _assign_colors(
        n_seeds,
        selected_index,
        include_gray,
        _rng(seed, split, index, "colors"),
    )
    out = [[0] * w for _ in range(h)]
    for c in range(w):
        out[0][c] = out[h - 1][c] = 8
    for r in range(h):
        out[r][0] = out[r][w - 1] = 8
    for (r, c), color in zip(positions, colors):
        out[r][c] = color

    info = observe(out)
    if info["selected_seed"][:2] != list(positions[selected_index]):
        raise AssertionError("color assignment changed selected geometry")
    if info["selected_color"] in (min(colors), max(colors)):
        raise AssertionError("selected color must defeat low/high-color shortcuts")
    if not info["selected_region_nonrectangular"]:
        raise AssertionError("selected region must defeat bounding-box shortcut")
    if not info["manhattan_euclidean_disagree"]:
        raise AssertionError("scene must distinguish Manhattan and Euclidean partitions")
    if include_gray and _color_frequency_smallest(out) == transform(out, "highlight_smallest_region"):
        raise AssertionError("gray lesson must defeat output-color-frequency selection")
    return tuple(tuple(row) for row in out)


def _scene(seed: int, split: str, index: int) -> list[list[int]]:
    return [list(row) for row in _scene_template(seed, split, index)]


def generate(seed: object, settings: object, demos: object, queries: object) -> dict[str, object]:
    seed = _integer(seed, "seed", 0, 2**63 - 1)
    selected = _settings(settings)
    demos = _integer(demos, "demos", 2, 6)
    queries = _integer(queries, "queries", 1, 4)
    finish = selected["finish"]

    demo_inputs = [_scene(seed, "demo", index) for index in range(6)]
    query_inputs = [_scene(seed, "query", index) for index in range(4)]
    train = [{"input": value, "output": transform(value, finish)} for value in demo_inputs[:demos]]
    test = [{"input": value, "output": transform(value, finish)} for value in query_inputs[:queries]]
    keys = [json.dumps(pair["input"], separators=(",", ":")) for pair in train + test]
    if len(keys) != len(set(keys)):
        raise ValueError("all demonstration and query inputs must be distinct")
    episode = {"train": train, "test": test, "program_solution": program(selected)}
    if certificate(train, [pair["input"] for pair in test])["survivors"] != [finish]:
        raise ValueError("constructed demonstrations do not identify the chosen setting")
    return episode


def certificate(train: object, query_inputs: object) -> dict[str, object]:
    if type(train) is not list or not 2 <= len(train) <= 6:
        raise ValueError("certificate requires 2..6 demonstrations")
    if type(query_inputs) is not list or not 1 <= len(query_inputs) <= 4:
        raise ValueError("certificate requires 1..4 query inputs")
    normalized_train: list[dict[str, list[list[int]]]] = []
    for pair in train:
        if type(pair) is not dict or not {"input", "output"} <= set(pair):
            raise ValueError("demonstrations need input and output")
        source = _copy(grid(pair["input"]))
        output = _copy(grid(pair["output"]))
        observe(source)
        normalized_train.append({"input": source, "output": output})
    normalized_queries = [_copy(grid(value)) for value in query_inputs]
    for value in normalized_queries:
        observe(value)
    survivors = [
        name
        for name in HYPOTHESES
        if all(_predict(pair["input"], name) == pair["output"] for pair in normalized_train)
    ]
    selected = survivors[0] if len(survivors) == 1 and survivors[0] in MODES else None
    disagreements: list[str] = []
    if selected:
        selected_outputs = [_predict(value, selected) for value in normalized_queries]
        for name in HYPOTHESES:
            if name == selected:
                continue
            if any(
                _predict(value, name) != expected
                for value, expected in zip(normalized_queries, selected_outputs)
            ):
                disagreements.append(name)
    return {
        "declared_hypotheses": list(HYPOTHESES),
        "survivors": survivors,
        "demonstrations": len(normalized_train),
        "queries": len(normalized_queries),
        "query_disagreements": disagreements,
        "predicted_query_sha256": [
            hashlib.sha256(
                json.dumps(_predict(value, selected), separators=(",", ":")).encode()
            ).hexdigest()
            for value in normalized_queries
        ]
        if selected
        else [],
        "scope": "Finite declared rivals checked from demonstrations only; not a proof of universal rule uniqueness.",
    }
