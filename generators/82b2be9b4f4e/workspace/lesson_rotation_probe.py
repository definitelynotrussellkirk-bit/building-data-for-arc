#!/usr/bin/env python3
"""Audit complete lesson windows under every cyclic query rotation.

This is independent review tooling, not a label authority.  It computes the
selected-object output with a small Python component oracle, iterates the
rivals actually declared by CANONICAL_SHORTCUTS and LESSON_COMPETITORS, and
checks that every three-demo view of four consecutive samples refutes each
canonical-fitting rival.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

TASK = "82b2be9b4f4e"
HOME = Path(__file__).resolve().parents[1]
ROOT = Path(__file__).resolve().parents[3]
RUNTIME = ROOT / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

from reviewer_support import canonical_pairs, find_root  # noqa: E402


def load_generator():
    path = HOME / "generator.py"
    spec = importlib.util.spec_from_file_location(f"rotation_probe_{TASK}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def components(grid, color, *, skip=frozenset()):
    h, w = len(grid), len(grid[0])
    seen = set(skip)
    result = []
    for r in range(h):
        for c in range(w):
            if (r, c) in seen or grid[r][c] != color:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = set()
            while stack:
                cr, cc = stack.pop()
                cells.add((cr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    point = (cr + dr, cc + dc)
                    if (
                        0 <= point[0] < h
                        and 0 <= point[1] < w
                        and point not in seen
                        and grid[point[0]][point[1]] == color
                    ):
                        seen.add(point)
                        stack.append(point)
            result.append(cells)
    return result


def reference_output(grid):
    """Independent mirror: clear key, largest keyed component, crop, 2x."""
    work = deepcopy(grid)
    key_pos = (len(work) - 1, 0)
    key = work[key_pos[0]][key_pos[1]]
    work[key_pos[0]][key_pos[1]] = 0
    matches = components(work, key)
    if not matches:
        raise ValueError("no keyed-color object")
    winner = max(matches, key=len)
    rows = [r for r, _ in winner]
    cols = [c for _, c in winner]
    r0, r1, c0, c1 = min(rows), max(rows), min(cols), max(cols)
    crop = [row[c0 : c1 + 1] for row in work[r0 : r1 + 1]]
    return [
        [value for value in row for _ in range(2)]
        for row in crop
        for _ in range(2)
    ]


def matching_component_count(grid):
    key_pos = (len(grid) - 1, 0)
    key = grid[key_pos[0]][key_pos[1]]
    return len(components(grid, key, skip=frozenset({key_pos})))


def digest(value):
    blob = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode()).hexdigest()


def declared_rivals(module):
    result = {}
    errors = []
    for attribute in ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS"):
        declaration = getattr(module, attribute, None)
        if not isinstance(declaration, dict):
            errors.append(f"{attribute} must be a dict")
            continue
        for name, fn in declaration.items():
            qualified = f"{attribute}:{name}"
            if not isinstance(name, str) or not callable(fn):
                errors.append(f"{qualified} must be callable")
            else:
                result[qualified] = fn
    return result, errors


def run_probe(module, *, seeds, period):
    rivals, errors = declared_rivals(module)
    report = {
        "schema": f"{TASK}-lesson-rotation-probe-v1",
        "task_id": TASK,
        "generator_sha256": hashlib.sha256((HOME / "generator.py").read_bytes()).hexdigest(),
        "test_source_sha256": hashlib.sha256((HOME / "tests/test_generator.py").read_bytes()).hexdigest(),
        "seeds_per_band_start": seeds,
        "start_period": period,
        "bands": ["easy", "medium", "hard"],
        "rivals": sorted(rivals),
        "racket_executed": False,
        "oracle": "independent Python connected-components/crop/upscale mirror",
        "errors": errors,
        "canonical_rival_fit": {},
        "per_band": {},
    }

    canonical = canonical_pairs(TASK, root=find_root(__file__))
    for name, rival in sorted(rivals.items()):
        fit = 0
        rival_errors = []
        for index, pair in enumerate(canonical):
            try:
                fit += int(rival(deepcopy(pair["input"])) == pair["output"])
            except Exception as exc:  # pragma: no cover - evidence path
                rival_errors.append(f"pair {index}: {type(exc).__name__}: {exc}")
        report["canonical_rival_fit"][name] = {
            "pairs": len(canonical),
            "fits": fit,
            "errors": rival_errors,
        }
        if rival_errors or fit != len(canonical):
            errors.append(f"{name} is not a canonical-fitting shortcut")

    all_inputs = set()
    for band in report["bands"]:
        counts = Counter()
        profiles = Counter()
        examples = []
        min_witnesses_after_rotation = None
        for seed in range(seeds):
            for start in range(period):
                window = []
                for offset in range(4):
                    sample_index = start + offset
                    grid = module.generate(seed, sample_index, difficulty=band)
                    counts["generated_pairs"] += 1
                    if grid != module.generate(seed, sample_index, difficulty=band):
                        errors.append(f"nondeterministic {band=} {seed=} {sample_index=}")
                    findings = list(module.self_check(deepcopy(grid)) or [])
                    strict = list(module.strict_canonical_like(deepcopy(grid)) or [])
                    if findings or strict:
                        errors.append(
                            f"validator failure {band=} {seed=} {sample_index=}: "
                            f"self={findings} strict={strict}"
                        )
                    reference_output(grid)
                    all_inputs.add(digest(grid))
                    profiles[module.schedule_profile(seed, sample_index, band)] += 1
                    window.append(grid)

                witness_counts = [matching_component_count(grid) == 2 for grid in window]
                counts["windows"] += 1
                counts["windows_with_two_or_more_witnesses"] += int(sum(witness_counts) >= 2)
                for query_index in range(4):
                    counts["rotations"] += 1
                    demos = [grid for index, grid in enumerate(window) if index != query_index]
                    query = window[query_index]
                    retained = sum(
                        matching_component_count(grid) == 2 for grid in demos
                    )
                    if min_witnesses_after_rotation is None:
                        min_witnesses_after_rotation = retained
                    else:
                        min_witnesses_after_rotation = min(
                            min_witnesses_after_rotation, retained
                        )
                    for name, rival in sorted(rivals.items()):
                        try:
                            survives = all(
                                rival(deepcopy(grid)) == reference_output(grid)
                                for grid in demos
                            )
                            query_agrees = (
                                rival(deepcopy(query)) == reference_output(query)
                            )
                        except Exception as exc:
                            errors.append(
                                f"{name} raised {band=} {seed=} {start=} "
                                f"{query_index=}: {type(exc).__name__}: {exc}"
                            )
                            continue
                        counts[f"{name}:survived_demos"] += int(survives)
                        counts[f"{name}:ambiguous"] += int(survives and not query_agrees)
                        if survives and len(examples) < 8:
                            examples.append(
                                {
                                    "rival": name,
                                    "seed": seed,
                                    "start": start,
                                    "query_index": query_index,
                                    "query_has_witness": matching_component_count(query) == 2,
                                    "window_component_counts": [
                                        matching_component_count(grid) for grid in window
                                    ],
                                }
                            )
        band_report = {
            **dict(counts),
            "profile_counts": dict(sorted(profiles.items())),
            "minimum_witnesses_in_any_rotated_demo_set": min_witnesses_after_rotation,
            "survival_examples": examples,
        }
        report["per_band"][band] = band_report
        for name in rivals:
            survived = counts[f"{name}:survived_demos"]
            if survived:
                errors.append(f"{band}: {name} survived {survived} rotated demo sets")
        if counts["windows_with_two_or_more_witnesses"] != counts["windows"]:
            errors.append(f"{band}: a four-pair window had fewer than two witnesses")

    report["unique_inputs"] = len(all_inputs)
    report["passed"] = not errors
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seeds", type=int, default=100)
    parser.add_argument("--period", type=int, default=4)
    args = parser.parse_args()
    if args.seeds < 1 or args.period < 1:
        parser.error("--seeds and --period must be positive")
    report = run_probe(load_generator(), seeds=args.seeds, period=args.period)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "passed": report["passed"],
                "generator_sha256": report["generator_sha256"],
                "unique_inputs": report["unique_inputs"],
                "per_band": {
                    band: {
                        "windows": row["windows"],
                        "rotations": row["rotations"],
                        "minimum_witnesses": row[
                            "minimum_witnesses_in_any_rotated_demo_set"
                        ],
                    }
                    for band, row in report["per_band"].items()
                },
                "errors": report["errors"][:10],
            },
            indent=2,
        )
    )
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
