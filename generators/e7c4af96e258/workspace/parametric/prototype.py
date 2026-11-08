"""Source-bound parametric family for marker-matched red-shape stamping.

The input sampler is independent of the hidden setting. Stage A enumerates all
D4 marker matches as candidate red footprints. Stage B either emits every
candidate (the exact canonical default) or selects only the farthest non-source
candidate. The first two demonstrations are chosen jointly so a finite family
of plausible positional and distance shortcuts cannot fit the visible lesson.
``nearest.rkt`` remains the protected wrong-intermediate counterfactual.
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import hashlib
import importlib.util
import json
from pathlib import Path
import random
from typing import Any, Sequence

TASK_ID = "e7c4af96e258"
HERE = Path(__file__).resolve().parent
POLICIES = ("all_matches", "farthest_match")
DEMO_SHAPES = ((18, 20), (20, 22), (17, 21), (19, 22), (18, 21), (20, 22))
QUERY_SHAPES = ((13, 15), (17, 20), (24, 26), (30, 30))
TEACHING_SELECTORS = (
    "all_matches",
    "farthest_match",
    "nearest_non_source",
    "first_match",
    "last_match",
    "topmost_match",
    "bottommost_match",
    "leftmost_match",
    "rightmost_match",
    "farthest_centroid",
    "farthest_manhattan",
    "farthest_bbox_origin",
)
_TEACHING_VARIANTS = 96


def _load_base():
    path = HERE.parents[1] / "generator.py"
    spec = importlib.util.spec_from_file_location("_marker_base_generator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load task-local base generator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_BASE = _load_base()


def _integer(value: Any, label: str, minimum: int | None = None, maximum: int | None = None) -> int:
    if type(value) is not int:
        raise ValueError(f"{label} must be an exact integer")
    if minimum is not None and value < minimum or maximum is not None and value > maximum:
        raise ValueError(f"{label} must be in {minimum}..{maximum}")
    return value


def _setting(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"target_policy"}:
        raise ValueError("settings must contain exactly target_policy")
    value = settings["target_policy"]
    if type(value) is not str or value not in POLICIES:
        raise ValueError("target_policy must be all_matches or farthest_match")
    return value


def _grid(grid: Any) -> list[list[int]]:
    if type(grid) is not list or not 1 <= len(grid) <= 30:
        raise ValueError("grid must have 1..30 rows")
    if type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30:
        raise ValueError("grid must have 1..30 columns")
    width = len(grid[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in grid
    ):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    return grid


def program(settings: Any) -> str:
    policy = _setting(settings)
    name = "canonical.rkt" if policy == "all_matches" else "farthest.rkt"
    return (HERE / name).read_text(encoding="utf-8")


def counterfactual_program(selector: str) -> str:
    if selector != "nearest_non_source":
        raise ValueError("counterfactual selector must be nearest_non_source")
    return (HERE / "nearest.rkt").read_text(encoding="utf-8")


@lru_cache(maxsize=256)
def _candidate_footprints_payload(payload: str) -> tuple[tuple[tuple[int, int], ...], ...]:
    return _BASE._candidate_footprints(json.loads(payload))


def candidate_footprints(grid: Sequence[Sequence[int]]) -> tuple[tuple[tuple[int, int], ...], ...]:
    _grid(grid)
    payload = json.dumps(grid, separators=(",", ":"))
    return _candidate_footprints_payload(payload)


def _source_cells(grid: Sequence[Sequence[int]]) -> tuple[tuple[int, int], ...]:
    return tuple(
        sorted((r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2)
    )


def _source_bbox_origin(grid: Sequence[Sequence[int]]) -> tuple[int, int]:
    cells = _source_cells(grid)
    if not cells:
        raise ValueError("input needs a red source")
    return min(r for r, _ in cells), min(c for _, c in cells)


def _candidate_score(grid: Sequence[Sequence[int]], candidate: Sequence[tuple[int, int]]) -> int:
    r0, c0 = _source_bbox_origin(grid)
    return sum((r - r0) ** 2 + (c - c0) ** 2 for r, c in candidate)


def _centroid_score(grid: Sequence[Sequence[int]], candidate: Sequence[tuple[int, int]]) -> float:
    source = _source_cells(grid)
    sr = sum(r for r, _ in source) / len(source)
    sc = sum(c for _, c in source) / len(source)
    cr = sum(r for r, _ in candidate) / len(candidate)
    cc = sum(c for _, c in candidate) / len(candidate)
    return (cr - sr) ** 2 + (cc - sc) ** 2


def _manhattan_score(grid: Sequence[Sequence[int]], candidate: Sequence[tuple[int, int]]) -> int:
    r0, c0 = _source_bbox_origin(grid)
    return sum(abs(r - r0) + abs(c - c0) for r, c in candidate)


def _bbox_origin_score(grid: Sequence[Sequence[int]], candidate: Sequence[tuple[int, int]]) -> int:
    r0, c0 = _source_bbox_origin(grid)
    rr = min(r for r, _ in candidate)
    cc = min(c for _, c in candidate)
    return (rr - r0) ** 2 + (cc - c0) ** 2


def _selected_candidates(
    grid: Sequence[Sequence[int]], selector: str
) -> list[tuple[tuple[int, int], ...]]:
    candidates = list(candidate_footprints(grid))
    source = _source_cells(grid)
    if selector == "all_matches":
        return candidates
    selectable = [candidate for candidate in candidates if candidate != source]
    if not selectable:
        return []
    if selector == "farthest_match":
        return [max(selectable, key=lambda candidate: _candidate_score(grid, candidate))]
    if selector == "nearest_non_source":
        return [min(selectable, key=lambda candidate: _candidate_score(grid, candidate))]
    if selector == "first_match":
        return [min(selectable)]
    if selector == "last_match":
        return [max(selectable)]
    if selector == "topmost_match":
        return [min(selectable, key=lambda candidate: (min(r for r, _ in candidate), candidate))]
    if selector == "bottommost_match":
        return [max(selectable, key=lambda candidate: (max(r for r, _ in candidate), candidate))]
    if selector == "leftmost_match":
        return [min(selectable, key=lambda candidate: (min(c for _, c in candidate), candidate))]
    if selector == "rightmost_match":
        return [max(selectable, key=lambda candidate: (max(c for _, c in candidate), candidate))]
    if selector == "farthest_centroid":
        return [max(selectable, key=lambda candidate: _centroid_score(grid, candidate))]
    if selector == "farthest_manhattan":
        return [max(selectable, key=lambda candidate: _manhattan_score(grid, candidate))]
    if selector == "farthest_bbox_origin":
        return [max(selectable, key=lambda candidate: _bbox_origin_score(grid, candidate))]
    raise ValueError("unknown selector")


def transform_with_selector(grid: list[list[int]], selector: str) -> list[list[int]]:
    source = _source_cells(_grid(grid))
    selected = _selected_candidates(grid, selector)
    stamped = {cell for candidate in selected for cell in candidate}
    output = deepcopy(grid)
    for r, c in source:
        if (r, c) not in stamped:
            output[r][c] = 0
    for r, c in stamped:
        if output[r][c] == 0:
            output[r][c] = 2
    return output


def transform(grid: list[list[int]], settings: Any) -> list[list[int]]:
    return transform_with_selector(grid, _setting(settings))


def teaching_certificate(train: Any, settings: Any) -> dict[str, Any]:
    """Fit a finite named shortcut family using demonstrations only."""
    selected = _setting(settings)
    if type(train) is not list or not 2 <= len(train) <= 6:
        raise ValueError("teaching requires 2..6 demonstrations")
    for pair in train:
        if type(pair) is not dict or not {"input", "output"} <= set(pair):
            raise ValueError("each teaching pair needs input and output")
        _grid(pair["input"])
        _grid(pair["output"])

    survivors: list[str] = []
    rejected: dict[str, int] = {}
    for selector in TEACHING_SELECTORS:
        mismatches = [
            index
            for index, pair in enumerate(train)
            if transform_with_selector(pair["input"], selector) != pair["output"]
        ]
        if mismatches:
            rejected[selector] = mismatches[0]
        else:
            survivors.append(selector)
    return {
        "schema": "e7c4af96e258-finite-teaching-certificate-v1",
        "fit_scope": "demonstrations_only",
        "selected": selected,
        "survivors": survivors,
        "declared_shortcuts": list(TEACHING_SELECTORS),
        "rejected_by_demonstration": rejected,
        "limits": "Finite named shortcut family only; not uniqueness over arbitrary programs.",
    }


def _rng(seed: int, stream: str, index: int, attempt: int) -> random.Random:
    payload = json.dumps([seed, stream, index, attempt], separators=(",", ":")).encode()
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest(), "big"))


def sample_input(seed: int, stream: str, index: int, height: int, width: int) -> list[list[int]]:
    _integer(seed, "seed", 0, 2**63 - 1)
    _integer(index, "index", 0)
    _integer(height, "height", 13, 30)
    _integer(width, "width", 13, 30)
    if type(stream) is not str or not stream:
        raise ValueError("stream must be a nonempty string")
    for attempt in range(512):
        grid = _BASE._place_scene(height, width, 2, _rng(seed, stream, index, attempt))
        if grid is None:
            continue
        candidates = list(candidate_footprints(grid))
        source = _source_cells(grid)
        selectable = [candidate for candidate in candidates if candidate != source]
        if len(selectable) != 2:
            continue
        scores = [_candidate_score(grid, candidate) for candidate in selectable]
        if len(set(scores)) != 2:
            continue
        if transform_with_selector(grid, "farthest_match") == transform_with_selector(
            grid, "nearest_non_source"
        ):
            continue
        return grid
    raise RuntimeError(f"could not construct a distinctive {height}x{width} marker scene")


def _teaching_stream(variant: int) -> str:
    return "train" if variant == 0 else f"train-teaching-{variant}"


def _fitting_selectors(grid: list[list[int]], selected: str) -> set[str]:
    expected = transform_with_selector(grid, selected)
    return {
        selector
        for selector in TEACHING_SELECTORS
        if transform_with_selector(grid, selector) == expected
    }


@lru_cache(maxsize=128)
def _teaching_demo_payload(seed: int) -> tuple[str, str]:
    """Cache immutable JSON so callers never share mutable lesson grids."""
    first_pool: list[list[list[int]]] = []
    second_pool: list[list[list[int]]] = []
    first_fits: list[set[str]] = []
    second_fits: list[set[str]] = []
    for variant in range(_TEACHING_VARIANTS):
        stream = _teaching_stream(variant)
        first = sample_input(seed, stream, 0, *DEMO_SHAPES[0])
        first_pool.append(first)
        first_fits.append(_fitting_selectors(first, "farthest_match"))
        second = sample_input(seed, stream, 1, *DEMO_SHAPES[1])
        second_pool.append(second)
        second_fits.append(_fitting_selectors(second, "farthest_match"))

        for first_index, fits in enumerate(first_fits):
            if fits & second_fits[-1] == {"farthest_match"}:
                return tuple(
                    json.dumps(grid, separators=(",", ":"))
                    for grid in (first_pool[first_index], second)
                )
        for second_index, fits in enumerate(second_fits[:-1]):
            if first_fits[-1] & fits == {"farthest_match"}:
                return tuple(
                    json.dumps(grid, separators=(",", ":"))
                    for grid in (first, second_pool[second_index])
                )
    raise RuntimeError("could not construct two demonstrations that reject declared shortcuts")


def _teaching_demo_inputs(seed: int) -> list[list[list[int]]]:
    return [json.loads(payload) for payload in _teaching_demo_payload(seed)]


def generate(seed: int, settings: Any, demos: int, queries: int) -> dict[str, Any]:
    _integer(seed, "seed", 0, 2**63 - 1)
    selected = _setting(settings)
    _integer(demos, "demos", 2, 6)
    _integer(queries, "queries", 1, 4)
    result: dict[str, Any] = {
        "train": [],
        "test": [],
        "program_solution": program(settings),
        "settings": dict(settings),
        "seed": seed,
        "prototype": True,
    }
    seen: set[str] = set()
    teaching_inputs = _teaching_demo_inputs(seed)
    for index, (height, width) in enumerate(DEMO_SHAPES[:demos]):
        grid = (
            teaching_inputs[index]
            if index < 2
            else sample_input(seed, "train", index, height, width)
        )
        key = json.dumps(grid, separators=(",", ":"))
        if key in seen:
            raise RuntimeError("deterministic sampler produced duplicate inputs")
        seen.add(key)
        result["train"].append({"input": grid, "output": transform_with_selector(grid, selected)})
    for index, (height, width) in enumerate(QUERY_SHAPES[:queries]):
        grid = sample_input(seed, "test", index, height, width)
        key = json.dumps(grid, separators=(",", ":"))
        if key in seen:
            raise RuntimeError("deterministic sampler produced duplicate inputs")
        seen.add(key)
        result["test"].append({"input": grid, "output": transform_with_selector(grid, selected)})

    certificate = teaching_certificate(result["train"], settings)
    if certificate["survivors"] != [selected]:
        raise RuntimeError(
            "minimum lesson did not uniquely identify selected policy: "
            + repr(certificate["survivors"])
        )
    result["certificate"] = certificate
    return result
