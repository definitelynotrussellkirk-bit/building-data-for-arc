"""Independent geometry oracle and source-bound probes for e8fb1b5bedfe.

This module is test/review tooling, not label authority.  The selected Racket
program remains authoritative; these helpers independently reconstruct the
visible frame-ranking rule so regressions can be caught before invoking Racket.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Iterable

TASK_ID = "e8fb1b5bedfe"
HOME = Path(__file__).resolve().parents[1]
REPO = HOME.parents[1]


def load_generator(path: str | Path | None = None):
    source = Path(path or HOME / "generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_e8fb1b5bedfe", source)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_row() -> dict:
    path = REPO / "shared/data/canonical/puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise ValueError(f"canonical task {TASK_ID} is absent")


def canonical_pairs() -> list[dict]:
    row = canonical_row()
    test = row.get("test", [])
    if isinstance(test, dict):
        test = [test]
    return list(row.get("train", [])) + list(test)


def normalized_rule_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def base_authority_path() -> Path:
    return REPO / "shared/data/base/solutions/banks/e352836528da/H5__e8fb1b5bedfe.json"


def frame_components(grid: list[list[int]]) -> list[dict]:
    """Return 4-connected color-4 components with their bounding boxes."""
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    frames: list[dict] = []
    for sr in range(h):
        for sc in range(w):
            if grid[sr][sc] != 4 or (sr, sc) in seen:
                continue
            todo = [(sr, sc)]
            seen.add((sr, sc))
            cells = {(sr, sc)}
            for r, c in todo:
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] == 4
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        cells.add((nr, nc))
                        todo.append((nr, nc))
            rows = [r for r, _ in cells]
            cols = [c for _, c in cells]
            r0, r1, c0, c1 = min(rows), max(rows), min(cols), max(cols)
            frames.append(
                {
                    "bbox": (r0, c0, r1, c1),
                    "cells": cells,
                    "height": r1 - r0 + 1,
                    "width": c1 - c0 + 1,
                    "area": (r1 - r0 - 1) * (c1 - c0 - 1),
                }
            )
    return sorted(frames, key=lambda f: f["bbox"])


def validate_frame_grid(grid: list[list[int]]) -> list[str]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return ["expected a nonempty grid"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["ragged grid"]
    errors: list[str] = []
    if any(type(value) is not int or value not in (0, 4) for row in grid for value in row):
        errors.append("input colors must be 0 and 4")
    frames = frame_components(grid)
    if not 2 <= len(frames) <= 4:
        errors.append(f"expected 2..4 frames, found {len(frames)}")
    areas: list[int] = []
    for frame in frames:
        r0, c0, r1, c1 = frame["bbox"]
        if frame["height"] < 3 or frame["width"] < 3:
            errors.append("frame smaller than 3x3")
            continue
        border = {
            (r, c)
            for r in range(r0, r1 + 1)
            for c in range(c0, c1 + 1)
            if r in (r0, r1) or c in (c0, c1)
        }
        if frame["cells"] != border:
            errors.append("color-4 component is not a hollow rectangle")
        if any(grid[r][c] != 0 for r in range(r0 + 1, r1) for c in range(c0 + 1, c1)):
            errors.append("frame interior is not empty")
        areas.append(frame["area"])
    if len(areas) != len(set(areas)):
        errors.append("interior areas are not distinct")
    return errors


def _fill(out: list[list[int]], frame: dict, color: int) -> None:
    r0, c0, r1, c1 = frame["bbox"]
    for r in range(r0 + 1, r1):
        for c in range(c0 + 1, c1):
            out[r][c] = color


def expected_output(grid: list[list[int]]) -> list[list[int]]:
    errors = validate_frame_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    frames = frame_components(grid)
    ranked = sorted(frames, key=lambda f: f["area"])
    out = deepcopy(grid)
    _fill(out, ranked[0], 2)
    _fill(out, ranked[-1], 8)
    return out


def fixed_3x3_smallest_output(grid: list[list[int]]) -> list[list[int]]:
    """Plausible public-data shortcut: the red frame is always exactly 3x3."""
    frames = frame_components(grid)
    out = deepcopy(grid)
    small = next((frame for frame in frames if (frame["height"], frame["width"]) == (3, 3)), None)
    if small is not None:
        _fill(out, small, 2)
    _fill(out, max(frames, key=lambda f: f["area"]), 8)
    return out


def widest_is_largest_output(grid: list[list[int]]) -> list[list[int]]:
    """Plausible public-data shortcut: largest means widest, not largest area."""
    frames = frame_components(grid)
    out = deepcopy(grid)
    _fill(out, min(frames, key=lambda f: f["area"]), 2)
    widest = max(frames, key=lambda f: (f["width"], -f["bbox"][0], -f["bbox"][1]))
    _fill(out, widest, 8)
    return out


def fill_all_non_small_output(grid: list[list[int]]) -> list[list[int]]:
    """Wrong branch rule: color every frame except the smallest cyan."""
    ranked = sorted(frame_components(grid), key=lambda f: f["area"])
    out = deepcopy(grid)
    _fill(out, ranked[0], 2)
    for frame in ranked[1:]:
        _fill(out, frame, 8)
    return out


def observed(grid: list[list[int]], profile_dims: dict[str, tuple[int, int]]) -> dict:
    dims = (len(grid), len(grid[0]))
    matches = [name for name, value in profile_dims.items() if tuple(value) == dims]
    if len(matches) != 1:
        raise ValueError(f"grid dimensions {dims} do not identify one scene profile")
    return {"scene_profile": matches[0], "n_frames": len(frame_components(grid))}


def lesson_survivors(demos: Iterable[dict], competitors: dict[str, object]) -> list[str]:
    survivors = []
    for name, rule in competitors.items():
        if all(rule(deepcopy(demo["input"])) == demo["output"] for demo in demos):
            survivors.append(name)
    return sorted(survivors)


def _grid_key(grid: list[list[int]]) -> str:
    return json.dumps(grid, separators=(",", ":"))


def build_report(gen, *, lessons_per_band: int = 120, seed_base: int = 810_000) -> dict:
    """Build the reproducible source-bound lesson and distribution report.

    Each band is one deterministic sample stream.  Lesson start ``i`` uses
    stream positions ``i:i+3`` as demonstrations and position ``i+3`` as the
    query, so adjacent lessons intentionally overlap.  The report separates
    4*lesson references from generated coordinates and unique grid values.
    """
    if lessons_per_band < 1:
        raise ValueError("lessons_per_band must be positive")

    canonical = canonical_pairs()
    shortcuts = dict(getattr(gen, "CANONICAL_SHORTCUTS", {}))
    competitors = dict(getattr(gen, "LESSON_COMPETITORS", {}))
    witnesses = dict(getattr(gen, "SEMANTIC_WITNESSES", {}))
    cycle = tuple(getattr(gen, "SCHEDULE_PROFILES", ()))
    if not cycle:
        raise ValueError("generator must declare a nonempty SCHEDULE_PROFILES cycle")

    canonical_fit = {}
    for name, rival in sorted(shortcuts.items()):
        fits = sum(
            rival(deepcopy(pair["input"])) == pair["output"]
            for pair in canonical
        )
        canonical_fit[name] = {"fits": fits, "total": len(canonical)}

    rows = {}
    for band_index, band in enumerate(("easy", "medium", "hard")):
        stream_seed = seed_base + band_index * 10_000
        stream_length = lessons_per_band + 3
        grids = [
            gen.generate(stream_seed, sample_index, difficulty=band)
            for sample_index in range(stream_length)
        ]
        outputs = [expected_output(grid) for grid in grids]

        shortcut_disagreements = Counter()
        competitor_disagreements = Counter()
        for grid, truth in zip(grids, outputs):
            for name, rival in shortcuts.items():
                if rival(deepcopy(grid)) != truth:
                    shortcut_disagreements[name] += 1
            for name, rival in competitors.items():
                if rival(deepcopy(grid)) != truth:
                    competitor_disagreements[name] += 1

        survivor_counts = Counter()
        query_disagreements = Counter()
        witness_demo_coverage = Counter()
        gate_errors = []
        unidentified = 0
        for start in range(lessons_per_band):
            demos = [
                {"input": grids[index], "output": outputs[index]}
                for index in range(start, start + 3)
            ]
            query = {"input": grids[start + 3], "output": outputs[start + 3]}
            survivors = lesson_survivors(demos, competitors)
            survivor_counts.update(survivors)
            unidentified += bool(survivors)
            for name, rival in competitors.items():
                if rival(deepcopy(query["input"])) != query["output"]:
                    query_disagreements[name] += 1
            for name, witness in witnesses.items():
                if any(witness(demo["input"]) for demo in demos):
                    witness_demo_coverage[name] += 1
            for reason in gen.lesson_identifiable(demos, query):
                gate_errors.append({"start": start, "reason": reason})

        rows[band] = {
            "stream_seed": stream_seed,
            "lesson_windows": lessons_per_band,
            "grid_references": lessons_per_band * 4,
            "generated_sample_coordinates": stream_length,
            "unique_inputs": len({_grid_key(grid) for grid in grids}),
            "duplicate_inputs": stream_length - len({_grid_key(grid) for grid in grids}),
            "sample_index_range": [0, stream_length - 1],
            "cyclic_start_counts": dict(
                Counter(cycle[start % len(cycle)] for start in range(lessons_per_band))
            ),
            "frame_counts": dict(Counter(len(frame_components(grid)) for grid in grids)),
            "scene_profiles": dict(
                Counter(gen.observe_overrides(grid)["scene_profile"] for grid in grids)
            ),
            "semantic_profiles": dict(
                Counter(gen.schedule_profile(stream_seed, index, band) for index in range(stream_length))
            ),
            "shortcut_disagreements_on_generated_inputs": dict(shortcut_disagreements),
            "competitor_disagreements_on_generated_inputs": dict(competitor_disagreements),
            "competitor_query_disagreements": dict(query_disagreements),
            "lesson_competitor_survivals": dict(survivor_counts),
            "unidentified_lessons": unidentified,
            "lesson_identifiable_gate_errors": gate_errors,
            "witness_demo_coverage": dict(witness_demo_coverage),
            "self_check_failures": sum(bool(gen.self_check(grid)) for grid in grids),
            "strict_profile_failures": sum(bool(gen.strict_canonical_like(grid)) for grid in grids),
        }

    profile_dims = {
        name: list(dims)
        for name, dims in sorted(getattr(gen, "SCENE_PROFILE_DIMS", {}).items())
    }
    report = {
        "schema": "e8fb1b5bedfe-review-probe-v2",
        "task_id": TASK_ID,
        "generator_sha256": hashlib.sha256(Path(gen.__file__).read_bytes()).hexdigest(),
        "canonical_rule_hash": normalized_rule_hash(canonical_row()["program_solution"]),
        "domain_limits": {
            "input_colors": [0, 4],
            "output_colors_added": [2, 8],
            "scene_profiles": profile_dims,
            "frame_count": [2, 4],
            "frame_side_length": [3, 6],
            "distinct_interior_areas": True,
            "separated_hollow_rectangles": True,
            "schedule_profiles": list(cycle),
            "examples_needed": getattr(gen, "EXAMPLES_NEEDED", None),
        },
        "sampler": {
            "seed_base": seed_base,
            "seed_formula": "seed_base + band_index*10000 (one fixed seed stream per band)",
            "sample_indexes": [0, lessons_per_band + 2],
            "lesson_start_indexes": [0, lessons_per_band - 1],
            "lessons_per_band": lessons_per_band,
            "bands": ["easy", "medium", "hard"],
            "lesson_assembly": {
                "demos": [0, 1, 2],
                "query": 3,
                "overlapping_windows": True,
            },
            "schedule_cycle_length": len(cycle),
        },
        "canonical_pairs": len(canonical),
        "canonical_shortcuts": sorted(shortcuts),
        "canonical_shortcut_fit": canonical_fit,
        "lesson_competitors": sorted(competitors),
        "bands": rows,
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument(
        "--per-band",
        type=int,
        default=120,
        help="overlapping 3-demo+1-query lesson windows per difficulty band",
    )
    parser.add_argument("--seed-base", type=int, default=810_000)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    gen = load_generator(args.generator)
    report = build_report(gen, lessons_per_band=args.per_band, seed_base=args.seed_base)
    raw = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(raw)
    else:
        print(raw, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
