#!/usr/bin/env python3
"""Source-bound lesson census for generator 7c7f1f574a18.

This probe deliberately does not call ``generator.rule_true``.  It recomputes
components, bbox-gap topology, and left/right docking independently, then scores
the generator's *actual* witness and competitor declarations.  The output is a
reproducible JSON artifact suitable for future review agents.
"""
from __future__ import annotations

import argparse
from collections import Counter, deque
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
from typing import Any


TASK_ID = "7c7f1f574a18"
HERE = Path(__file__).resolve()
TASK_HOME = HERE.parents[1]
ROOT = HERE.parents[3]
for _path in (ROOT, ROOT / "shared/runtime"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))
DEFAULT_GENERATOR = TASK_HOME / "generator.py"
DIRECTIONS = ((-1, 0), (1, 0), (0, -1), (0, 1))
BANDS = ("easy", "medium", "hard")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _grid_sha(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":"), sort_keys=False).encode()
    return hashlib.sha256(payload).hexdigest()


def _load_generator(path: Path):
    spec = importlib.util.spec_from_file_location("reviewed_7c7f1f574a18", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_row() -> dict[str, Any]:
    path = ROOT / "shared/data/canonical/puzzles.jsonl"
    for line in path.open():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise RuntimeError(f"canonical task {TASK_ID} not found")


def _normalize(grid: Any) -> list[list[int]]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        raise ValueError("not a non-empty list grid")
    width = len(grid[0])
    if not width or any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("not rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("non-ARC cell")
    return [list(row) for row in grid]


def _background(grid: list[list[int]]) -> int:
    counts = Counter(value for row in grid for value in row)
    maximum = max(counts.values())
    winners = [color for color, count in counts.items() if count == maximum]
    if len(winners) != 1:
        raise ValueError("tied modal background")
    return winners[0]


def _gap_regions(cells: set[tuple[int, int]], box: tuple[int, int, int, int]):
    top, left, bottom, right = box
    unseen = {
        (row, col)
        for row in range(top, bottom + 1)
        for col in range(left, right + 1)
        if (row, col) not in cells
    }
    regions = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        queue = deque([start])
        region = {start}
        boundary = False
        while queue:
            row, col = queue.popleft()
            boundary |= row in (top, bottom) or col in (left, right)
            for drow, dcol in DIRECTIONS:
                nxt = row + drow, col + dcol
                if nxt in unseen:
                    unseen.remove(nxt)
                    region.add(nxt)
                    queue.append(nxt)
        regions.append((region, boundary))
    return regions


def _objects(grid: list[list[int]]) -> tuple[int, list[dict[str, Any]]]:
    background = _background(grid)
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    found = []
    for row in range(height):
        for col in range(width):
            start = (row, col)
            color = grid[row][col]
            if color == background or start in seen:
                continue
            seen.add(start)
            queue = deque([start])
            cells = set()
            while queue:
                point = queue.popleft()
                cells.add(point)
                for drow, dcol in DIRECTIONS:
                    nxt = point[0] + drow, point[1] + dcol
                    nr, nc = nxt
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and nxt not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add(nxt)
                        queue.append(nxt)
            rows = [r for r, _ in cells]
            cols = [c for _, c in cells]
            box = min(rows), min(cols), max(rows), max(cols)
            gaps = _gap_regions(cells, box)
            closed = not gaps or any(not boundary for _region, boundary in gaps)
            found.append(
                {
                    "cells": cells,
                    "box": box,
                    "width": box[3] - box[1] + 1,
                    "closed": closed,
                }
            )
    found.sort(key=lambda item: (item["box"][0], item["box"][1]))
    return background, found


def independent_output(grid: Any) -> list[list[int]]:
    source = _normalize(grid)
    background, objects = _objects(source)
    height, width = len(source), len(source[0])
    output = [[background] * width for _ in range(height)]
    for obj in objects:
        source_left = obj["box"][1]
        destination = 0 if obj["closed"] else width - obj["width"]
        color = 2 if obj["closed"] else 3
        for row, col in obj["cells"]:
            output[row][destination + col - source_left] = color
    return output


def _domain_update(domain: dict[str, list[int]], grid: list[list[int]]) -> None:
    background, objects = _objects(grid)
    values = {
        "height": len(grid),
        "width": len(grid[0]),
        "components": len(objects),
        "palette_size": len({value for row in grid for value in row}),
        "foreground_colors": len({value for row in grid for value in row if value != background}),
        "max_object_cells": max(len(obj["cells"]) for obj in objects),
    }
    for key, value in values.items():
        domain.setdefault(key, []).append(value)


def run_census(generator_path: Path, lessons_per_band: int) -> dict[str, Any]:
    gen = _load_generator(generator_path)
    competitors = dict(getattr(gen, "LESSON_COMPETITORS", {}))
    witnesses = dict(getattr(gen, "SEMANTIC_WITNESSES", {}))
    examples = int(getattr(gen, "EXAMPLES_NEEDED", 3))
    if examples < 2:
        raise RuntimeError("EXAMPLES_NEEDED must be at least two")

    canonical = _canonical_row()
    canonical_pairs = list(canonical.get("train", [])) + list(canonical.get("test", []))
    canonical_matches = sum(
        independent_output(pair["input"]) == pair.get("output")
        for pair in canonical_pairs
    )

    unique_global: set[str] = set()
    rival_disagreements = Counter({name: 0 for name in competitors})
    witness_firings = Counter({name: 0 for name in witnesses})
    invalid_inputs = 0
    strict_inputs = 0
    unidentifiable = 0
    domain: dict[str, list[int]] = {}
    band_reports: dict[str, Any] = {}
    total_inputs = 0

    for band_index, band in enumerate(BANDS):
        unique_band: set[str] = set()
        band_invalid = 0
        band_unidentifiable = 0
        band_strict = 0
        for lesson in range(lessons_per_band):
            seed = 700_000 + 10_000 * band_index + lesson
            start_index = lesson * (examples + 1)
            pairs = []
            for offset in range(examples + 1):
                grid = gen.generate(seed, start_index + offset, difficulty=band)
                expected = independent_output(grid)
                issues = gen.self_check(grid)
                invalid_inputs += bool(issues)
                band_invalid += bool(issues)
                strict = gen.strict_canonical_like(grid) == []
                strict_inputs += strict
                band_strict += strict
                digest = _grid_sha(grid)
                unique_global.add(digest)
                unique_band.add(digest)
                _domain_update(domain, grid)
                for name, witness in witnesses.items():
                    witness_firings[name] += bool(witness(grid))
                for name, competitor in competitors.items():
                    rival_disagreements[name] += competitor(grid) != expected
                pairs.append({"input": grid, "output": expected})
                total_inputs += 1
            problems = gen.lesson_identifiable(pairs[:-1], pairs[-1])
            unidentifiable += bool(problems)
            band_unidentifiable += bool(problems)
        band_reports[band] = {
            "lessons": lessons_per_band,
            "inputs": lessons_per_band * (examples + 1),
            "unique_inputs": len(unique_band),
            "invalid_inputs": band_invalid,
            "strict_inputs": band_strict,
            "unidentifiable_lessons": band_unidentifiable,
        }

    domain_limits = {
        key: {"min": min(values), "max": max(values)}
        for key, values in sorted(domain.items())
    }
    all_rivals_refuted = all(count == total_inputs for count in rival_disagreements.values())
    status = "pass" if (
        canonical_matches == len(canonical_pairs)
        and invalid_inputs == 0
        and unidentifiable == 0
        and all_rivals_refuted
        and all(count == total_inputs for count in witness_firings.values())
    ) else "fail"

    return {
        "schema": "7c7f1f574a18-semantic-census-v1",
        "status": status,
        "task_id": TASK_ID,
        "generator_sha256": _sha(generator_path),
        "tool_sha256": _sha(HERE),
        "sampler": {
            "bands": list(BANDS),
            "lessons_per_band": lessons_per_band,
            "demos_per_lesson": examples,
            "inputs_per_lesson": examples + 1,
            "seed_formula": "700000 + 10000*band_index + lesson_index",
            "sample_index_formula": "lesson_index*(demos+1) + offset",
            "labels": "independent Python topology oracle; Racket parity is checked separately by the battery",
        },
        "lessons": lessons_per_band * len(BANDS),
        "inputs": total_inputs,
        "unique_inputs": len(unique_global),
        "invalid_inputs": invalid_inputs,
        "strict_inputs": strict_inputs,
        "unidentifiable_lessons": unidentifiable,
        "canonical_pairs": len(canonical_pairs),
        "canonical_oracle_matches": canonical_matches,
        "rival_disagreements": dict(sorted(rival_disagreements.items())),
        "witness_firings": dict(sorted(witness_firings.items())),
        "domain_limits": domain_limits,
        "bands": band_reports,
        "limitations": (
            "Finite evidence against the generator's declared rival family; "
            "not a proof of universal ARC identifiability."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lessons-per-band", type=int, default=100)
    parser.add_argument("--generator", type=Path, default=None)
    parser.add_argument("--json-out", type=Path, required=True)
    args = parser.parse_args()
    if args.lessons_per_band < 1:
        parser.error("--lessons-per-band must be positive")
    generator_path = Path(
        args.generator
        or os.environ.get("GENERATOR_UNDER_TEST", "")
        or DEFAULT_GENERATOR
    ).resolve()
    report = run_census(generator_path, args.lessons_per_band)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    args.json_out.write_text(encoded)
    print(json.dumps(report, sort_keys=True, separators=(",", ":")))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
