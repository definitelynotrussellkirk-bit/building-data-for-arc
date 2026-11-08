#!/usr/bin/env python3
"""Bounded sampler and crossed-control stress for 70913cf98cee.

This is intentionally task-local and reusable by later reviewers.  It checks the
entire declared count surface without protected execution (the separate native
smoke/preflight owns that), and records two crossed controls:

* change only an unmapped nuisance color while preserving the post-A destination
  topology; and
* remove the source half of a created mixed domino at the same coordinates,
  changing the intermediate and therefore B's action on the destination half.
"""
from __future__ import annotations

import argparse
from collections import deque
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any


def _load_family():
    source = Path(__file__).with_name("family.py")
    name = "_sampler_family_" + hashlib.sha256(source.read_bytes()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, source)
    if spec is None or spec.loader is None:
        raise ImportError(source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


F = _load_family()
Grid = list[list[int]]


def _pairs(grid: Grid) -> list[tuple[int, int]]:
    values = [value for value in grid[0] if value]
    return list(zip(values[::2], values[1::2]))


def _components(grid: Grid, color: int) -> list[set[tuple[int, int]]]:
    remaining = {
        (r, c)
        for r in range(2, len(grid))
        for c in range(len(grid[0]))
        if grid[r][c] == color
    }
    found: list[set[tuple[int, int]]] = []
    while remaining:
        start = remaining.pop()
        component = {start}
        queue = deque([start])
        while queue:
            r, c = queue.popleft()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nxt = (r + dr, c + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    component.add(nxt)
                    queue.append(nxt)
        found.append(component)
    return found


def _signature(grid: Grid) -> tuple[Any, ...]:
    mapped = F.apply_python(grid, "direct")
    return tuple(
        tuple(sorted((len(component), tuple(sorted(component)))
                     for component in _components(mapped, destination)))
        for _source, destination in _pairs(grid)
    )


def _digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _has_created_and_destroyed(grid: Grid) -> tuple[bool, bool]:
    mapped = F.apply_python(grid, "direct")
    created = False
    destroyed = False
    for source, destination in _pairs(grid):
        for component in _components(mapped, destination):
            original_values = {grid[r][c] for r, c in component}
            if len(component) == 2 and original_values == {source, destination}:
                created = True
        for source_component in _components(grid, source):
            if len(source_component) != 2:
                continue
            containing = next(
                component for component in _components(mapped, destination)
                if source_component <= component
            )
            if len(containing) > 2:
                destroyed = True
    return created, destroyed


def _teaching_coverage(grid: Grid) -> dict[str, Any]:
    legend = _pairs(grid)
    mapped = F.apply_python(grid, "direct")
    orientations: dict[int, set[str]] = {}
    diagonal_singletons = False
    for _source, destination in legend:
        cells: list[tuple[int, int]] = []
        axes: set[str] = set()
        for component in _components(mapped, destination):
            if len(component) == 1:
                cells.append(next(iter(component)))
            elif len(component) == 2:
                rows = {r for r, _c in component}
                axes.add("h" if len(rows) == 1 else "v")
        diagonal_singletons |= any(
            abs(r1 - r2) == 1 and abs(c1 - c2) == 1
            for i, (r1, c1) in enumerate(cells)
            for r2, c2 in cells[i + 1:]
        )
        orientations[destination] = axes
    created, destroyed = _has_created_and_destroyed(grid)
    return {
        "legend_pairs": len(legend),
        "all_destinations_qualify": all(orientations.values()),
        "orientations": sorted(set().union(*orientations.values())),
        "diagonal_singleton_trap": diagonal_singletons,
        "created_post_a_domino": created,
        "destroyed_pre_a_domino": destroyed,
    }


def _nuisance_control(grid: Grid) -> None:
    header = {value for row in grid[:1] for value in row if value}
    body = {value for row in grid[2:] for value in row if value}
    neutral = sorted(body - header)
    unused = sorted(set(range(1, 10)) - header - body)
    if len(neutral) != 1 or not unused:
        raise AssertionError("3-pair anchor must expose one neutral and one unused color")
    changed = copy.deepcopy(grid)
    old, new = neutral[0], unused[0]
    for row in changed[2:]:
        for c, value in enumerate(row):
            if value == old:
                row[c] = new
    if changed == grid or _signature(changed) != _signature(grid):
        raise AssertionError("nuisance mutation changed the intended intermediate")
    before = F.apply_python(grid, "cycle_dominoes")
    after = F.apply_python(changed, "cycle_dominoes")
    for r in range(len(grid)):
        for c in range(len(grid[0])):
            if grid[r][c] != old and before[r][c] != after[r][c]:
                raise AssertionError("nuisance color influenced a rule-relevant cell")


def _intermediate_control(grid: Grid) -> None:
    mapped = F.apply_python(grid, "direct")
    selected = None
    for source, destination in _pairs(grid):
        for component in _components(mapped, destination):
            if len(component) != 2:
                continue
            src_cells = [(r, c) for r, c in component if grid[r][c] == source]
            dst_cells = [(r, c) for r, c in component if grid[r][c] == destination]
            if len(src_cells) == len(dst_cells) == 1:
                selected = (src_cells[0], dst_cells[0], destination)
                break
        if selected:
            break
    if selected is None:
        raise AssertionError("missing mixed created domino")
    source_cell, destination_cell, destination = selected
    changed = copy.deepcopy(grid)
    changed[source_cell[0]][source_cell[1]] = 0
    if _signature(changed) == _signature(grid):
        raise AssertionError("intervention did not change the intermediate")
    before = F.apply_python(grid, "cycle_dominoes")
    after = F.apply_python(changed, "cycle_dominoes")
    r, c = destination_cell
    if before[r][c] == destination or after[r][c] != destination or before[r][c] == after[r][c]:
        raise AssertionError("B did not depend on the changed post-A component")


def _expect_value_error(fn) -> None:
    try:
        fn()
    except ValueError:
        return
    raise AssertionError("invalid contract call was accepted")


def run(seeds: int) -> dict[str, Any]:
    if type(seeds) is not int or not 1 <= seeds <= 10000:
        raise ValueError("seeds must be an integer in 1..10000")

    settings = ({"postprocess": "direct"}, {"postprocess": "cycle_dominoes"})
    unique_inputs: set[str] = set()
    unique_episodes: set[str] = set()
    size_counts: dict[str, int] = {}
    max_body_nonzero = 0
    min_large_body_nonzero = 10**9
    min_lesson_checks = 0
    crossed_controls = 0
    all_quadrants = 0
    right_edge = 0
    bottom_edge = 0

    for seed in range(seeds):
        direct = F.generate(seed, settings[0], 6, 4)
        alternate = F.generate(seed, settings[1], 6, 4)
        if [p["input"] for split in ("train", "test") for p in direct[split]] != [
            p["input"] for split in ("train", "test") for p in alternate[split]
        ]:
            raise AssertionError("settings changed episode inputs")
        short = F.generate(seed, settings[1], 2, 1)
        if short["train"] != alternate["train"][:2] or short["test"] != alternate["test"][:1]:
            raise AssertionError("count slicing changed bank prefixes")

        inputs = [p["input"] for split in ("train", "test") for p in direct[split]]
        if len({_digest(grid) for grid in inputs}) != 10:
            raise AssertionError("episode contains duplicate inputs")
        unique_episodes.add(_digest(inputs))

        for split in ("train", "test"):
            for index, (base_pair, alt_pair) in enumerate(zip(direct[split], alternate[split])):
                grid = base_pair["input"]
                if base_pair["output"] != F.apply_python(grid, "direct"):
                    raise AssertionError("direct label mismatch")
                if alt_pair["output"] != F.apply_python(grid, "cycle_dominoes"):
                    raise AssertionError("alternate label mismatch")
                if base_pair["output"] == alt_pair["output"]:
                    raise AssertionError("paired settings do not differ")
                if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
                    raise AssertionError("non-ARC grid value")
                if any(grid[1]):
                    raise AssertionError("separator row is not blank")
                key = f"{len(grid)}x{len(grid[0])}"
                size_counts[key] = size_counts.get(key, 0) + 1
                unique_inputs.add(_digest(grid))
                max_body_nonzero = max(max_body_nonzero, sum(value != 0 for row in grid[2:] for value in row))

        for pair in alternate["train"][:2]:
            coverage = _teaching_coverage(pair["input"])
            if not (
                coverage["legend_pairs"] >= 3
                and coverage["all_destinations_qualify"]
                and coverage["orientations"] == ["h", "v"]
                and coverage["diagonal_singleton_trap"]
                and coverage["created_post_a_domino"]
                and coverage["destroyed_pre_a_domino"]
            ):
                raise AssertionError({"seed": seed, "coverage": coverage})
            min_lesson_checks += 1

        three_pair = next(pair["input"] for pair in alternate["train"][:2] if len(_pairs(pair["input"])) == 3)
        _nuisance_control(three_pair)
        _intermediate_control(three_pair)
        crossed_controls += 2

        large = next(pair["input"] for pair in alternate["test"] if len(pair["input"]) == 30)
        body_nonzero = sum(value != 0 for row in large[2:] for value in row)
        min_large_body_nonzero = min(min_large_body_nonzero, body_nonzero)
        if body_nonzero < 60:
            raise AssertionError("30x30 scene is padding rather than substantive content")
        quadrants = [False, False, False, False]
        for r in range(2, 30):
            for c in range(30):
                if large[r][c]:
                    quadrants[(r >= 16) * 2 + (c >= 15)] = True
        if all(quadrants):
            all_quadrants += 1
        else:
            raise AssertionError("30x30 scene misses a quadrant")
        if any(large[r][-1] for r in range(2, 30)):
            right_edge += 1
        else:
            raise AssertionError("30x30 scene misses right boundary")
        if any(large[-1]):
            bottom_edge += 1
        else:
            raise AssertionError("30x30 scene misses bottom boundary")

        # Freshness/alias check on one representative object per seed.
        regenerated = F.generate(seed, settings[0], 6, 4)
        original = direct["train"][0]["input"][0][0]
        direct["train"][0]["input"][0][0] = 0 if original else 1
        if regenerated == direct:
            raise AssertionError("generation reused mutable episode state")

    invalid_calls = [
        lambda: F.generate(True, settings[0], 2, 4),
        lambda: F.generate(-1, settings[0], 2, 4),
        lambda: F.generate(2**63, settings[0], 2, 4),
        lambda: F.generate(0, settings[0], 1, 4),
        lambda: F.generate(0, settings[0], 7, 4),
        lambda: F.generate(0, settings[0], True, 4),
        lambda: F.generate(0, settings[0], 2, 0),
        lambda: F.generate(0, settings[0], 2, 5),
        lambda: F.generate(0, settings[0], 2, True),
        lambda: F.generate(0, {}, 2, 4),
        lambda: F.generate(0, {"postprocess": "direct", "extra": 1}, 2, 4),
        lambda: F.generate(0, {"postprocess": True}, 2, 4),
        lambda: F.generate(0, {"postprocess": "unknown"}, 2, 4),
    ]
    for call in invalid_calls:
        _expect_value_error(call)

    return {
        "schema": "70913cf98cee-sampler-stress-v1",
        "status": "passed",
        "seeds": seeds,
        "full_episodes": seeds * 2,
        "generated_pairs_checked": seeds * 20,
        "minimum_demo_checks": min_lesson_checks,
        "crossed_controls": crossed_controls,
        "invalid_contract_calls_rejected": len(invalid_calls),
        "unique_episode_input_banks": len(unique_episodes),
        "unique_inputs": len(unique_inputs),
        "size_counts": dict(sorted(size_counts.items())),
        "thirty_by_thirty": {
            "scenes": seeds,
            "minimum_body_nonzero": min_large_body_nonzero,
            "all_quadrants": all_quadrants,
            "right_edge_contacts": right_edge,
            "bottom_edge_contacts": bottom_edge,
        },
        "maximum_body_nonzero": max_body_nonzero,
        "limits": "Finite deterministic seed sweep; protected Racket is covered by separate smoke and qualification receipts.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=256)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = run(args.seeds)
    raw = json.dumps(report, sort_keys=True, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(raw)
    print(raw, end="")


if __name__ == "__main__":
    main()
