"""Parametric majority-summary family for 59d146376904.

``spatial`` is the exact canonical rule. ``majority_count_desc`` first finds
both the majority color and its count in each equal quadrant, uses the four
counts to derive an input-dependent quadrant ranking, then emits the majority
colors in that ranked order. Protected Racket remains the retained label
source; ``transform`` is an independent Python mirror for authoring checks.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from functools import cache
import hashlib
import itertools
import json
from pathlib import Path
import random
from typing import Any, Callable, Iterable

from reviewer_support import canonical_path, find_root

TASK_ID = "59d146376904"
PARAMETER = "summary_order"
ORDERS = ("spatial", "majority_count_desc")
DEFAULT_SETTINGS = {PARAMETER: "spatial"}
SETTINGS = [{PARAMETER: value} for value in ORDERS]
MIN_DEMOS = 2
MAX_DEMOS = 6
QUERY_COUNT = 4
MAX_SEED = 2**63 - 1
ROOT = find_root(__file__)
HOME = Path(__file__).resolve().parent
RANKED_PROGRAM = HOME / "ranked.rkt"

# rank_order lists quadrant indices from highest to lowest majority count.
_TRAIN_PROFILES = (
    (8, 10, (2, 0, 3, 1), True),
    (8, 10, (1, 3, 0, 2), True),
    (6, 6, (3, 1, 2, 0), False),
    (12, 14, (0, 2, 1, 3), False),
    (18, 20, (3, 0, 1, 2), True),
    (24, 26, (1, 2, 3, 0), False),
)
_QUERY_PROFILES = (
    (6, 8, (0, 3, 1, 2), False),
    (14, 12, (2, 1, 3, 0), True),
    (22, 24, (1, 0, 2, 3), False),
    (30, 30, (3, 2, 0, 1), True),
)
_MAJOR_ASSIGNMENTS = (
    (3, 0, 2, 1),
    (1, 3, 0, 2),
    (2, 0, 3, 1),
    (0, 2, 1, 3),
    (3, 1, 0, 2),
    (1, 0, 3, 2),
    (2, 3, 1, 0),
    (0, 3, 2, 1),
    (1, 2, 0, 3),
    (3, 2, 1, 0),
)


def _exact_int(name: str, value: Any, lo: int, hi: int) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer; bool is forbidden")
    if not lo <= value <= hi:
        raise ValueError(f"{name} must be in [{lo}, {hi}]")
    return value


def _settings(settings: Any) -> dict[str, str]:
    if type(settings) is not dict or set(settings) != {PARAMETER}:
        raise ValueError(f"settings must contain exactly {PARAMETER!r}")
    value = settings[PARAMETER]
    if type(value) is not str or value not in ORDERS:
        raise ValueError(f"{PARAMETER} must be one of {ORDERS!r}")
    return {PARAMETER: value}


@cache
def canonical_program(*, root: Path = ROOT) -> str:
    programs = set()
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                source = row.get("program_solution")
                if type(source) is not str or not source.strip():
                    raise ValueError("canonical record has no Racket program")
                programs.add(source)
    if len(programs) != 1:
        raise ValueError(f"expected one canonical program for {TASK_ID}, got {len(programs)}")
    return programs.pop()


def program(settings: Any) -> str:
    chosen = _settings(settings)[PARAMETER]
    return canonical_program() if chosen == "spatial" else RANKED_PROGRAM.read_text(encoding="utf-8")


def _grid(grid: Any) -> tuple[int, int]:
    if type(grid) is not list or not 6 <= len(grid) <= 30 or type(grid[0]) is not list:
        raise ValueError("grid must be a literal list with 6..30 rows")
    width = len(grid[0])
    if not 6 <= width <= 30:
        raise ValueError("grid must have 6..30 columns")
    if len(grid) % 2 or width % 2:
        raise ValueError("grid dimensions must be even")
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in grid
    ):
        raise ValueError("grid must be rectangular with exact integer ARC colors 0..9")
    return len(grid), width


def _entry(values: list[int]) -> dict[str, int]:
    counts = Counter(value for value in values if value != 0)
    if not counts:
        raise ValueError("each quadrant needs nonzero cells")
    ordered = sorted(counts.items(), key=lambda item: (-item[1], -item[0]))
    winner, count = ordered[0]
    runner_up = ordered[1][1] if len(ordered) > 1 else 0
    if count <= runner_up:
        raise ValueError("each quadrant needs a unique nonzero majority")
    return {
        "majority_color": winner,
        "majority_count": count,
        "runner_up_count": runner_up,
        "background_count": values.count(0),
        "nonzero_count": sum(value != 0 for value in values),
        "distinct_nonzero": len(counts),
        "top_left": values[0],
        "first_nonzero": next(value for value in values if value != 0),
        "highest_nonzero": max(counts),
    }


def analyze_input(grid: Any) -> dict[str, Any]:
    height, width = _grid(grid)
    qh, qw = height // 2, width // 2
    quadrants = []
    values_by_quadrant = []
    for index, (r0, c0) in enumerate(((0, 0), (0, qw), (qh, 0), (qh, qw))):
        values = [grid[row][col] for row in range(r0, r0 + qh) for col in range(c0, c0 + qw)]
        item = _entry(values)
        item.update({"index": index, "area": len(values), "origin": (r0, c0)})
        quadrants.append(item)
        values_by_quadrant.append(values)
    colors = [item["majority_color"] for item in quadrants]
    counts = [item["majority_count"] for item in quadrants]
    if len(set(colors)) != 4:
        raise ValueError("the four quadrant majority colors must be distinct")
    if len(set(counts)) != 4:
        raise ValueError("ranked family inputs need four distinct majority counts")
    rank = tuple(sorted(range(4), key=lambda index: (-counts[index], index)))
    global_counts = Counter(value for row in grid for value in row if value != 0)
    return {
        "height": height,
        "width": width,
        "quadrant_height": qh,
        "quadrant_width": qw,
        "quadrants": quadrants,
        "majority_rank": rank,
        "global_counts": dict(global_counts),
        "values": values_by_quadrant,
    }


def _output_from_order(facts: dict[str, Any], order: Iterable[int], extractor: str = "majority_color") -> list[list[int]]:
    colors = [facts["quadrants"][index][extractor] for index in order]
    return [colors[:2], colors[2:]]


def transform(grid: Any, settings: Any) -> list[list[int]]:
    chosen = _settings(settings)[PARAMETER]
    facts = analyze_input(grid)
    order = range(4) if chosen == "spatial" else facts["majority_rank"]
    return _output_from_order(facts, order)


def _rng(seed: int, split: str, index: int, label: str) -> random.Random:
    body = f"{TASK_ID}|majority-rank-v1|{seed}|{split}|{index}|{label}".encode()
    return random.Random(int(hashlib.sha256(body).hexdigest(), 16))


def _levels(area: int) -> list[int]:
    available = list(range(area // 2 + 1, area))
    if len(available) < 4:
        raise ValueError("quadrant area must provide four distinct strict-majority counts")
    n = len(available)
    indices = [0, (n - 1) // 3, (2 * (n - 1)) // 3, n - 1]
    # Small domains can duplicate rounded thirds; choose the first four unique
    # values while preserving the full span.
    chosen = []
    for index in [*indices, *range(n)]:
        value = available[index]
        if value not in chosen:
            chosen.append(value)
        if len(chosen) == 4:
            break
    return sorted(chosen, reverse=True)


def _counts_by_quadrant(area: int, rank_order: tuple[int, ...]) -> list[int]:
    values = _levels(area)
    result = [0] * 4
    for count, quadrant in zip(values, rank_order):
        result[quadrant] = count
    return result


def _profile(split: str, index: int):
    profiles = _TRAIN_PROFILES if split == "train" else _QUERY_PROFILES
    _exact_int("index", index, 0, len(profiles) - 1)
    return profiles[index]


def sample_input(seed: int, split: str, index: int) -> list[list[int]]:
    _exact_int("seed", seed, 0, MAX_SEED)
    if split not in {"train", "test"}:
        raise ValueError("split must be 'train' or 'test'")
    height, width, rank_order, full_nonzero = _profile(split, index)
    qh, qw = height // 2, width // 2
    area = qh * qw
    majority_counts = _counts_by_quadrant(area, rank_order)

    palette_rng = _rng(seed, split, index, "palette")
    palette = list(range(1, 10))
    palette_rng.shuffle(palette)
    base_colors = sorted(palette[:4])
    profile_index = index if split == "train" else len(_TRAIN_PROFILES) + index
    assignment = _MAJOR_ASSIGNMENTS[profile_index]
    majors = [base_colors[position] for position in assignment]
    decoys = [color for color in palette if color not in majors]
    boost_quadrant = rank_order[-1]
    boost_color = majors[boost_quadrant]

    grid = [[0 for _ in range(width)] for _ in range(height)]
    origins = ((0, 0), (0, qw), (qh, 0), (qh, qw))
    # The two-example minimum crosses nuisance statistics deliberately.  These
    # totals make nonzero density and majority margin disagree with both the
    # spatial order and the intended majority-count ranking.
    teaching_nonzero_totals = {
        0: (20, 19, 20, 15),
        1: (18, 20, 14, 19),
    }
    teaching_runner_counts = {
        0: (4, 2, 1, 1),
        1: (5, 1, 1, 3),
    }
    runner_patterns = (
        (1, 99, 2, 1),
        (99, 1, 3, 2),
        (2, 1, 99, 3),
        (3, 2, 1, 99),
    )
    pattern = runner_patterns[profile_index % len(runner_patterns)]
    for quadrant, (r0, c0) in enumerate(origins):
        major = majors[quadrant]
        major_count = majority_counts[quadrant]
        remainder = area - major_count
        if split == "train" and index in teaching_nonzero_totals:
            nonzero_remainder = teaching_nonzero_totals[index][quadrant] - major_count
            runner_target = teaching_runner_counts[index][quadrant]
        else:
            if full_nonzero:
                nonzero_remainder = remainder
            else:
                zeros = min(max(1, (quadrant + profile_index) % 4), max(1, remainder - 1))
                nonzero_remainder = max(1, remainder - zeros)
            requested = pattern[quadrant]
            runner_target = min(nonzero_remainder, requested if requested != 99 else nonzero_remainder)
            # At most eight non-major ARC colors are available. Raise the
            # per-color cap when necessary so the requested nonzero remainder
            # is representable without indexing past that finite palette.
            minimum_feasible_cap = (nonzero_remainder + 7) // 8
            runner_target = max(1, minimum_feasible_cap, runner_target)
        if not (1 <= runner_target <= nonzero_remainder <= remainder):
            raise AssertionError((quadrant, major_count, nonzero_remainder, runner_target, remainder))

        candidates = []
        for color in [boost_color, *decoys, *majors, *range(1, 10)]:
            if color != major and color not in candidates:
                candidates.append(color)
        minority_values = [candidates[0]] * runner_target
        remaining = nonzero_remainder - runner_target
        color_index = 1
        while remaining:
            take = min(runner_target, remaining)
            minority_values.extend([candidates[color_index]] * take)
            remaining -= take
            color_index += 1
        values = (
            [major] * major_count
            + minority_values
            + [0] * (area - major_count - nonzero_remainder)
        )
        rng = _rng(seed, split, index, f"quadrant-{quadrant}")
        rng.shuffle(values)
        # A non-major top-left cell defeats first-cell/corner extraction. The
        # multiset, and therefore every intended count, is unchanged.
        nonmajor_index = next(i for i, value in enumerate(values) if value != major and value != 0)
        values[0], values[nonmajor_index] = values[nonmajor_index], values[0]
        cells = [(r0 + dr, c0 + dc) for dr in range(qh) for dc in range(qw)]
        for (row, col), value in zip(cells, values):
            grid[row][col] = value

    facts = analyze_input(grid)
    if facts["majority_rank"] != rank_order:
        raise AssertionError((facts["majority_rank"], rank_order))
    return grid


def digest_grid(grid: Any) -> str:
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def _rank_by(facts: dict[str, Any], key: Callable[[dict[str, Any]], Any], reverse: bool) -> tuple[int, ...]:
    return tuple(sorted(range(4), key=lambda index: (key(facts["quadrants"][index]), index), reverse=reverse))


def _fixed_permutation(grid: Any, permutation: tuple[int, ...]) -> list[list[int]]:
    return _output_from_order(analyze_input(grid), permutation)


def _rival_rules(settings: Any) -> dict[str, Callable[[Any], list[list[int]]]]:
    selected = _settings(settings)[PARAMETER]
    rivals: dict[str, Callable[[Any], list[list[int]]]] = {}
    intended_order = lambda facts: tuple(range(4)) if selected == "spatial" else facts["majority_rank"]

    for permutation in itertools.permutations(range(4)):
        if selected == "spatial" and permutation == (0, 1, 2, 3):
            continue
        rivals["fixed-permutation:" + "".join(map(str, permutation))] = (
            lambda grid, p=permutation: _fixed_permutation(grid, p)
        )

    if selected == "spatial":
        rivals["rank:majority-count-desc"] = lambda grid: _output_from_order(analyze_input(grid), analyze_input(grid)["majority_rank"])
    else:
        rivals["spatial"] = lambda grid: _output_from_order(analyze_input(grid), range(4))

    rank_specs = {
        "majority-count-asc": (lambda item: item["majority_count"], False),
        "majority-color-desc": (lambda item: item["majority_color"], True),
        "majority-color-asc": (lambda item: item["majority_color"], False),
        "nonzero-count-desc": (lambda item: item["nonzero_count"], True),
        "nonzero-count-asc": (lambda item: item["nonzero_count"], False),
        "runner-up-desc": (lambda item: item["runner_up_count"], True),
        "runner-up-asc": (lambda item: item["runner_up_count"], False),
        "margin-desc": (lambda item: item["majority_count"] - item["runner_up_count"], True),
        "margin-asc": (lambda item: item["majority_count"] - item["runner_up_count"], False),
        "distinct-colors-desc": (lambda item: item["distinct_nonzero"], True),
        "distinct-colors-asc": (lambda item: item["distinct_nonzero"], False),
    }
    for name, (key, reverse) in rank_specs.items():
        rivals["rank:" + name] = lambda grid, k=key, rev=reverse: _output_from_order(
            analyze_input(grid), _rank_by(analyze_input(grid), k, rev)
        )

    def global_order(grid, reverse=True):
        facts = analyze_input(grid)
        return tuple(
            sorted(
                range(4),
                key=lambda index: (facts["global_counts"][facts["quadrants"][index]["majority_color"]], index),
                reverse=reverse,
            )
        )

    rivals["rank:global-frequency-desc"] = lambda grid: _output_from_order(analyze_input(grid), global_order(grid, True))
    rivals["rank:global-frequency-asc"] = lambda grid: _output_from_order(analyze_input(grid), global_order(grid, False))

    for extractor in ("top_left", "first_nonzero", "highest_nonzero"):
        rivals[f"extract:{extractor}:spatial"] = lambda grid, ex=extractor: _output_from_order(analyze_input(grid), range(4), ex)
        rivals[f"extract:{extractor}:intended-order"] = lambda grid, ex=extractor: _output_from_order(
            analyze_input(grid), intended_order(analyze_input(grid)), ex
        )
    return rivals


RIVAL_SCOPE_LIMITS = (
    "Finite named-rival bank: fixed permutations, count/color/global/density/runner-up/margin rankings, "
    "and corner/first/highest-color extractors. It does not prove uniqueness against arbitrary programs."
)


def lesson_rival_survivors(demos: Iterable[dict[str, Any]], settings: Any) -> list[str]:
    pairs = list(demos)
    if not pairs:
        raise ValueError("at least one demonstration is required")
    survivors = []
    for name, rival in _rival_rules(settings).items():
        try:
            if all(rival(pair["input"]) == pair["output"] for pair in pairs):
                survivors.append(name)
        except (ValueError, KeyError, IndexError, TypeError):
            continue
    return sorted(survivors)


def query_changing_survivors(episode: dict[str, Any], settings: Any) -> list[dict[str, Any]]:
    rows = []
    for name, rival in _rival_rules(settings).items():
        try:
            if not all(rival(pair["input"]) == pair["output"] for pair in episode["train"]):
                continue
            disagreements = [
                index for index, pair in enumerate(episode["test"])
                if rival(pair["input"]) != pair["output"]
            ]
            if disagreements:
                rows.append({"rival": name, "query_disagreements": disagreements})
        except (ValueError, KeyError, IndexError, TypeError):
            continue
    return rows


def generate(seed: int, settings: Any, demos: int = 3, queries: int = 4) -> dict[str, Any]:
    seed = _exact_int("seed", seed, 0, MAX_SEED)
    demos = _exact_int("demos", demos, MIN_DEMOS, MAX_DEMOS)
    queries = _exact_int("queries", queries, QUERY_COUNT, QUERY_COUNT)
    chosen = _settings(settings)
    train_inputs = [sample_input(seed, "train", index) for index in range(demos)]
    test_inputs = [sample_input(seed, "test", index) for index in range(queries)]
    all_inputs = [*train_inputs, *test_inputs]
    digests = [digest_grid(grid) for grid in all_inputs]
    if len(digests) != len(set(digests)):
        raise RuntimeError("all demonstration and query inputs must be distinct")
    train = [{"input": grid, "output": transform(grid, chosen)} for grid in train_inputs]
    test = [{"input": grid, "output": transform(grid, chosen)} for grid in test_inputs]
    survivors = lesson_rival_survivors(train, chosen)
    if survivors:
        raise RuntimeError(f"teaching lesson leaves declared rivals: {survivors}")
    return {
        "train": train,
        "test": test,
        "program_solution": program(chosen),
        "settings": deepcopy(chosen),
    }


def public_turn(episode: dict[str, Any], query_index: int) -> dict[str, Any]:
    query_index = _exact_int("query_index", query_index, 0, QUERY_COUNT - 1)
    train = episode.get("train")
    test = episode.get("test")
    if type(train) is not list or type(test) is not list or len(test) != QUERY_COUNT:
        raise ValueError("episode must contain a four-query bank")
    return {
        "train": deepcopy(train),
        "test": [{"input": deepcopy(test[query_index]["input"])}],
    }
