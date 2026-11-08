#!/usr/bin/env python3
"""Standalone finite probe for 961add4a2688.

The probe intentionally derives the frame, output, override observations, and
lesson verdicts outside generator.py.  It exhausts the public override product
and all query rotations of consecutive five-pair schedule windows, dynamically
reading the generator's current LESSON_COMPETITORS rather than pinning a copied
rival list.
"""
from __future__ import annotations

import argparse
from itertools import product
import importlib.util
import json
from pathlib import Path
from typing import Any, Iterable, Sequence

TASK_ID = "961add4a2688"
HOME = Path(__file__).resolve().parents[1]
PROFILES = {
    "canonical_8x9_p6": (8, 9, 6),
    "canonical_9x10_p8": (9, 10, 8),
    "canonical_9x11_p8": (9, 11, 8),
    "canonical_10x10_p6": (10, 10, 6),
}
PATTERNS = ("separate", "stacked", "mixed")
POSITIONS = ("top_left", "center", "bottom_right")


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        f"probe_generator_{TASK_ID}", HOME / "generator.py"
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load selected generator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _frame(grid: Sequence[Sequence[int]]) -> tuple[int, int, int, int]:
    cells = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 8}
    if not cells:
        raise ValueError("no color-8 frame")
    r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
    c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
    border = {
        (r, c)
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
        if r in (r0, r1) or c in (c0, c1)
    }
    if cells != border:
        raise ValueError("color-8 cells are not exactly one border")
    return r0, c0, r1, c1


def independent_rule(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Apply the visible frame/column rule without calling generator helpers."""
    r0, c0, r1, c1 = _frame(grid)
    out = [[0 for _ in row] for row in grid]
    for r in range(r0, r1 + 1):
        out[r][c0] = 8
        out[r][c1] = 8
    for c in range(c0, c1 + 1):
        out[r0][c] = 8
        out[r1][c] = 8
    for c in range(c0 + 1, c1):
        values = [grid[r][c] for r in range(r0 + 1, r1) if grid[r][c] != 0]
        for offset, value in enumerate(values):
            out[r0 + 1 + offset][c] = value
    return out


def independent_observe(grid: Sequence[Sequence[int]]) -> dict[str, Any]:
    """Recover all four exact controls from pixels only."""
    h, w = len(grid), len(grid[0])
    palette_size = len({value for row in grid for value in row})
    signature = (h, w, palette_size)
    profile_hits = [name for name, expected in PROFILES.items() if expected == signature]
    if len(profile_hits) != 1:
        raise ValueError(f"ambiguous scene profile for {signature}")

    r0, c0, r1, c1 = _frame(grid)
    columns = {
        c: [grid[r][c] for r in range(r0 + 1, r1) if grid[r][c] != 0]
        for c in range(c0 + 1, c1)
        if any(grid[r][c] != 0 for r in range(r0 + 1, r1))
    }
    counts = [len(values) for values in columns.values()]
    if counts and all(count == 1 for count in counts):
        pattern = "separate"
    elif counts and all(count >= 2 for count in counts):
        pattern = "stacked"
    elif any(count >= 2 for count in counts) and any(count == 1 for count in counts):
        pattern = "mixed"
    else:
        raise ValueError(f"ambiguous column pattern for counts={counts}")

    frame_h, frame_w = r1 - r0 + 1, c1 - c0 + 1
    anchors = {
        "top_left": (0, 0),
        "center": ((h - frame_h) // 2, (w - frame_w) // 2),
        "bottom_right": (h - frame_h, w - frame_w),
    }
    position_hits = [name for name, origin in anchors.items() if origin == (r0, c0)]
    if len(position_hits) != 1:
        raise ValueError(f"ambiguous frame position at {(r0, c0)} with anchors={anchors}")

    return {
        "scene_profile": profile_hits[0],
        "n_markers": sum(counts),
        "column_pattern": pattern,
        "frame_position": position_hits[0],
    }


def _failure(kind: str, **details: Any) -> dict[str, Any]:
    return {"kind": kind, **details}


def run_probe(
    *,
    seed: int = 20261008,
    starts: int = 8,
    bands: Iterable[str] = ("easy", "medium", "hard"),
) -> dict[str, Any]:
    gen = _load_generator()
    bands = tuple(bands)
    failures: list[dict[str, Any]] = []
    override_cases = 0
    lessons = 0
    rotations = 0
    rival_rotation_checks = 0

    for band, profile, n_markers, pattern, position in product(
        bands, PROFILES, (6, 7), PATTERNS, POSITIONS
    ):
        override_cases += 1
        kwargs = {
            "scene_profile": profile,
            "n_markers": n_markers,
            "column_pattern": pattern,
            "frame_position": position,
        }
        try:
            grid = gen.generate(seed, override_cases, difficulty=band, **kwargs)
            observed = independent_observe(grid)
            if observed != kwargs:
                failures.append(
                    _failure(
                        "override_mismatch",
                        band=band,
                        requested=kwargs,
                        observed=observed,
                    )
                )
            if independent_rule(grid) != gen.rule_mirror(grid):
                failures.append(
                    _failure("oracle_mismatch", band=band, requested=kwargs)
                )
        except Exception as exc:  # retain every exact failure in the report
            failures.append(
                _failure(
                    "override_exception",
                    band=band,
                    requested=kwargs,
                    error=f"{type(exc).__name__}: {exc}",
                )
            )

    rivals = dict(gen.LESSON_COMPETITORS)
    for band in bands:
        for start in range(starts):
            lessons += 1
            pairs = []
            for offset in range(5):
                grid = gen.generate(seed + start, start + offset, difficulty=band)
                pairs.append({"input": grid, "output": independent_rule(grid)})
            for query_index, query in enumerate(pairs):
                rotations += 1
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                reasons = gen.lesson_identifiable(demos, query)
                if reasons:
                    failures.append(
                        _failure(
                            "lesson_hook",
                            band=band,
                            start=start,
                            query_index=query_index,
                            reasons=reasons,
                        )
                    )
                for name, rival in rivals.items():
                    rival_rotation_checks += 1
                    try:
                        refuted = any(
                            rival(pair["input"]) != pair["output"] for pair in demos
                        )
                    except Exception as exc:
                        failures.append(
                            _failure(
                                "rival_exception",
                                band=band,
                                start=start,
                                query_index=query_index,
                                rival=name,
                                error=f"{type(exc).__name__}: {exc}",
                            )
                        )
                        continue
                    if not refuted:
                        failures.append(
                            _failure(
                                "surviving_rival",
                                band=band,
                                start=start,
                                query_index=query_index,
                                rival=name,
                            )
                        )

    return {
        "schema": "961add4a2688-curriculum-probe-v1",
        "task_id": TASK_ID,
        "seed": seed,
        "bands": list(bands),
        "starts": starts,
        "declared_rivals": sorted(rivals),
        "status": "passed" if not failures else "failed",
        "summary": {
            "override_cases": override_cases,
            "lessons": lessons,
            "rotations": rotations,
            "rival_rotation_checks": rival_rotation_checks,
        },
        "failures": failures,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=20261008)
    parser.add_argument("--starts", type=int, default=8)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    report = run_probe(seed=args.seed, starts=args.starts)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(text, end="")
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
