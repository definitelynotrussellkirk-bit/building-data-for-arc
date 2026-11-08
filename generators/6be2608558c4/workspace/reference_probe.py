#!/usr/bin/env python3
"""Portable schedule, oracle, and shortcut probe for generator 6be2608558c4.

This script intentionally derives the task answer from pixels instead of using
private generator helpers.  It can be imported by focused tests or run directly:

    python3 workspace/reference_probe.py --out probe.json \
        --counterexample-out ../counterexamples/fixed-middle-shortcut.json

A "start" is a literal sample_index at the beginning of a four-pair sliding
window.  Every pair in every window is held out once, matching rotate-query
lesson assembly while also checking arbitrary cyclic starts.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import inspect
import json
from pathlib import Path
import sys
from types import ModuleType
from typing import Iterable, Sequence

TASK_ID = "6be2608558c4"
HERE = Path(__file__).resolve()
REPO = HERE.parents[3]
for path in (REPO / "shared" / "runtime", REPO / "src", REPO):
    if path.is_dir() and str(path) not in sys.path:
        sys.path.insert(0, str(path))


def load_generator(path: Path | None = None) -> ModuleType:
    source = path or HERE.parent.parent / "generator.py"
    spec = importlib.util.spec_from_file_location(f"probe_generator_{TASK_ID}", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator from {source}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _components(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    work = deepcopy(grid)
    for row in range(min(5, len(work))):
        for col in range(min(5, len(work[0]))):
            work[row][col] = 0
    height, width = len(work), len(work[0])
    seen: set[tuple[int, int]] = set()
    found: list[list[tuple[int, int]]] = []
    for start_row in range(height):
        for start_col in range(width):
            if work[start_row][start_col] == 0 or (start_row, start_col) in seen:
                continue
            stack = [(start_row, start_col)]
            seen.add((start_row, start_col))
            cells: list[tuple[int, int]] = []
            while stack:
                row, col = stack.pop()
                cells.append((row, col))
                for next_row, next_col in (
                    (row - 1, col),
                    (row + 1, col),
                    (row, col - 1),
                    (row, col + 1),
                ):
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if (next_row, next_col) in seen or work[next_row][next_col] == 0:
                        continue
                    seen.add((next_row, next_col))
                    stack.append((next_row, next_col))
            found.append(sorted(cells))
    return found


def _shape(cells: Iterable[tuple[int, int]]) -> tuple[frozenset[tuple[int, int]], int, int]:
    points = tuple(cells)
    if not points:
        raise ValueError("empty shape")
    min_row = min(row for row, _ in points)
    min_col = min(col for _, col in points)
    normalized = frozenset((row - min_row, col - min_col) for row, col in points)
    height = max(row for row, _ in normalized) + 1
    width = max(col for _, col in normalized) + 1
    return normalized, height, width


def _exemplar_shape(grid: list[list[int]]):
    cells = [
        (row, col)
        for row in range(5)
        for col in range(5)
        if grid[row][col] != 0
    ]
    return _shape(cells)


def independent_rule(grid: list[list[int]]) -> list[list[int]]:
    exemplar, _, _ = _exemplar_shape(grid)
    matches = [cells for cells in _components(grid) if _shape(cells)[0] == exemplar]
    if len(matches) != 1:
        raise ValueError(f"expected one exact shape match, found {len(matches)}")
    shape, height, width = _shape(matches[0])
    return [
        [2 if (row, col) in shape else 0 for col in range(width)]
        for row in range(height)
    ]


def _grid_digest(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _record_issue(issues: list[dict], kind: str, **context) -> None:
    issues.append({"kind": kind, **context})


def audit_schedule(
    generator: ModuleType,
    *,
    seeds: Sequence[int] = (0, 19, 8731),
    starts: Iterable[int] = range(30),
    bands: Sequence[str] = ("easy", "medium", "hard"),
) -> dict:
    """Exhaust sliding windows and every legal held-out query rotation."""
    starts = tuple(starts)
    issues: list[dict] = []
    profiles: Counter[str] = Counter()
    unique_inputs: set[str] = set()
    lessons = rotations = pairs = 0

    competitors = getattr(generator, "LESSON_COMPETITORS", {})
    for band in bands:
        for seed in seeds:
            for start in starts:
                lesson = []
                lessons += 1
                for sample_index in range(start, start + 4):
                    pairs += 1
                    try:
                        grid = generator.generate(seed, sample_index, difficulty=band)
                    except Exception as exc:
                        _record_issue(
                            issues,
                            "generation_error",
                            band=band,
                            seed=seed,
                            sample_index=sample_index,
                            error=repr(exc),
                        )
                        lesson = []
                        break
                    unique_inputs.add(_grid_digest(grid))
                    check_errors = list(generator.self_check(grid))
                    if check_errors:
                        _record_issue(
                            issues,
                            "self_check_rejection",
                            band=band,
                            seed=seed,
                            sample_index=sample_index,
                            errors=check_errors,
                        )
                    try:
                        truth = independent_rule(grid)
                    except Exception as exc:
                        _record_issue(
                            issues,
                            "independent_oracle_error",
                            band=band,
                            seed=seed,
                            sample_index=sample_index,
                            error=repr(exc),
                        )
                        lesson = []
                        break
                    if generator.rule_mirror(grid) != truth:
                        _record_issue(
                            issues,
                            "python_mirror_disagrees",
                            band=band,
                            seed=seed,
                            sample_index=sample_index,
                        )

                    exemplar, ex_h, ex_w = _exemplar_shape(grid)
                    component_shapes = [_shape(cells) for cells in _components(grid)]
                    expected_signature = (len(exemplar), ex_h, ex_w)
                    signatures = [(len(shape), h, w) for shape, h, w in component_shapes]
                    if len(component_shapes) != 3 or any(
                        signature != expected_signature for signature in signatures
                    ):
                        _record_issue(
                            issues,
                            "signature_curriculum_broken",
                            band=band,
                            seed=seed,
                            sample_index=sample_index,
                            expected=list(expected_signature),
                            observed=[list(signature) for signature in signatures],
                        )
                    if len({shape for shape, _, _ in component_shapes}) != 3:
                        _record_issue(
                            issues,
                            "body_shapes_not_distinct",
                            band=band,
                            seed=seed,
                            sample_index=sample_index,
                        )
                    matches = [
                        index for index, (shape, _, _) in enumerate(component_shapes)
                        if shape == exemplar
                    ]
                    declared_profile = generator.schedule_profile(seed, sample_index, band)
                    profiles[str(declared_profile)] += 1
                    if matches != [declared_profile]:
                        _record_issue(
                            issues,
                            "schedule_profile_mismatch",
                            band=band,
                            seed=seed,
                            sample_index=sample_index,
                            declared=declared_profile,
                            matches=matches,
                        )
                    lesson.append({"input": grid, "output": truth})

                if len(lesson) != 4:
                    continue
                for query_index in range(4):
                    rotations += 1
                    query = lesson[query_index]
                    demos = [pair for index, pair in enumerate(lesson) if index != query_index]
                    hook_errors = list(generator.lesson_identifiable(demos, query))
                    if hook_errors:
                        _record_issue(
                            issues,
                            "lesson_hook_rejection",
                            band=band,
                            seed=seed,
                            start=start,
                            query_index=query_index,
                            errors=hook_errors,
                        )
                    for name, competitor in competitors.items():
                        try:
                            survives = all(
                                competitor(pair["input"]) == pair["output"] for pair in demos
                            )
                            changes_query = competitor(query["input"]) != query["output"]
                        except Exception as exc:
                            _record_issue(
                                issues,
                                "competitor_error",
                                band=band,
                                seed=seed,
                                start=start,
                                query_index=query_index,
                                competitor=name,
                                error=repr(exc),
                            )
                            continue
                        if survives and changes_query:
                            _record_issue(
                                issues,
                                "surviving_competitor",
                                band=band,
                                seed=seed,
                                start=start,
                                query_index=query_index,
                                competitor=name,
                            )

    return {
        "task_id": TASK_ID,
        "generator_version": getattr(generator, "VERSION", None),
        "rule_hash": getattr(generator, "RULE_HASH", None),
        "bands": list(bands),
        "seeds": list(seeds),
        "starts": list(starts),
        "lessons": lessons,
        "pairs_materialized": pairs,
        "rotations": rotations,
        "unique_inputs": len(unique_inputs),
        "profile_counts": dict(sorted(profiles.items())),
        "competitors": sorted(competitors),
        "issues": issues,
        "status": "pass" if not issues else "fail",
    }


def fixed_middle_counterexample(
    generator: ModuleType,
    *,
    seed: int = 0,
    band: str = "medium",
) -> dict:
    """Return the first scheduled lawful grid that refutes always-middle."""
    rival_name = "always_middle_component"
    competitor = generator.LESSON_COMPETITORS[rival_name]
    for sample_index in range(12):
        grid = generator.generate(seed, sample_index, difficulty=band)
        truth = independent_rule(grid)
        rival_output = competitor(grid)
        if rival_output != truth:
            source_path = Path(inspect.getsourcefile(generator) or "")
            source_sha256 = (
                hashlib.sha256(source_path.read_bytes()).hexdigest()
                if source_path.is_file()
                else None
            )
            return {
                "task_id": TASK_ID,
                "generator_version": getattr(generator, "VERSION", None),
                "rule_hash": getattr(generator, "RULE_HASH", None),
                "generator_sha256": source_sha256,
                "seed": seed,
                "sample_index": sample_index,
                "difficulty": band,
                "schedule_profile": generator.schedule_profile(seed, sample_index, band),
                "rival": rival_name,
                "input": grid,
                "truth": truth,
                "rival_output": rival_output,
                "self_check": list(generator.self_check(grid)),
            }
    raise RuntimeError("no always-middle counterexample found in the first 12 profiles")


def _parse_ints(text: str) -> tuple[int, ...]:
    return tuple(int(part.strip()) for part in text.split(",") if part.strip())


def _parse_starts(text: str) -> tuple[int, ...]:
    if ":" not in text:
        return _parse_ints(text)
    parts = [int(part) if part else None for part in text.split(":")]
    if not 2 <= len(parts) <= 3:
        raise ValueError("starts range must be START:STOP or START:STOP:STEP")
    start, stop = parts[:2]
    step = parts[2] if len(parts) == 3 else 1
    return tuple(range(start or 0, stop if stop is not None else 0, step or 1))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path, default=None)
    parser.add_argument("--seeds", default="0,19,8731")
    parser.add_argument("--starts", default="0:30")
    parser.add_argument("--bands", default="easy,medium,hard")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--counterexample-out", type=Path)
    args = parser.parse_args(argv)

    generator = load_generator(args.generator)
    report = audit_schedule(
        generator,
        seeds=_parse_ints(args.seeds),
        starts=_parse_starts(args.starts),
        bands=tuple(part.strip() for part in args.bands.split(",") if part.strip()),
    )
    rendered = json.dumps(report, indent=2, sort_keys=True)
    print(rendered)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered + "\n", encoding="utf-8")
    if args.counterexample_out:
        witness = fixed_middle_counterexample(generator)
        args.counterexample_out.parent.mkdir(parents=True, exist_ok=True)
        args.counterexample_out.write_text(
            json.dumps(witness, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return 0 if not report["issues"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
