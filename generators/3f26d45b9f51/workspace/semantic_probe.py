#!/usr/bin/env python3
"""Reproduce 3f26d45b9f51's nearest-pair counterexample and stress its public axes."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import random
import sys
from collections import Counter
from pathlib import Path
from typing import Any

TASK_ID = "3f26d45b9f51"
TASK_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = TASK_DIR.parents[1]


def _bootstrap_reviewer_support() -> None:
    """Make the task-local probe runnable both in-source and in portable runtimes."""
    for ancestor in (TASK_DIR, *TASK_DIR.parents):
        for candidate in (ancestor, ancestor / "shared" / "runtime"):
            if (candidate / "reviewer_support.py").is_file():
                sys.path.insert(0, str(candidate))
                return
    raise RuntimeError("could not locate reviewer_support.py from semantic_probe.py")


_bootstrap_reviewer_support()
from reviewer_support import canonical_pairs, find_root  # noqa: E402


def load_generator():
    path = TASK_DIR / "generator.py"
    spec = importlib.util.spec_from_file_location(f"probe_{TASK_ID}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def first_differences(left, right, limit: int = 20):
    out = []
    for r, (lrow, rrow) in enumerate(zip(left, right)):
        for c, (lv, rv) in enumerate(zip(lrow, rrow)):
            if lv != rv:
                out.append([r, c, lv, rv])
                if len(out) >= limit:
                    return out
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seeds", type=int, default=3)
    args = parser.parse_args()

    gen, source = load_generator()
    source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    fixture_path = TASK_DIR / "counterexamples" / "nearest_pair_only.json"
    fixture = json.loads(fixture_path.read_text())
    grid = fixture["input"]
    intended = gen._solve_python(grid)
    rival = gen.SEMANTIC_RIVALS["nearest_pair_only"](grid)

    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    canonical_fit = [
        gen.SEMANTIC_RIVALS["nearest_pair_only"](pair["input"]) == pair["output"]
        for pair in pairs
    ]

    failures: list[dict[str, Any]] = []
    rival_equal_counts: Counter[str] = Counter()
    dividers: Counter[int] = Counter()
    marker_counts: Counter[int] = Counter()
    cases = 0
    for band in ("easy", "medium", "hard"):
        for K in (7, 8, 9):
            for n_colors in (2, 3, 4):
                for seed in range(args.seeds):
                    for index in range(gen.LESSON_SCHEDULE_PERIOD):
                        cases += 1
                        label = {"band": band, "K": K, "n_colors": n_colors, "seed": seed, "index": index}
                        try:
                            candidate = gen.generate(seed, index, difficulty=band, K=K, n_colors=n_colors)
                            info = gen._analyze(candidate)
                            expected = gen._solve_python(candidate)
                            dividers[info["divider"]] += 1
                            marker_counts[max(map(len, info["markers"].values()))] += 1
                            checks = {
                                "self_check": gen.self_check(candidate) == [],
                                "strict": gen.strict_canonical_like(candidate) == [],
                                "axes": gen.observe_overrides(candidate) == {"K": K, "n_colors": n_colors},
                                "three_collinear": gen._w_three_collinear(candidate),
                            }
                            for name in (
                                "row_only",
                                "column_only",
                                "bounding_box_fill",
                                "drop_unconnected_markers",
                                "nearest_pair_only",
                            ):
                                equal = gen.SEMANTIC_RIVALS[name](candidate) == expected
                                rival_equal_counts[name] += int(equal)
                                checks[f"refutes_{name}"] = not equal
                            fixed_equal = gen.SEMANTIC_RIVALS["fixed_divider_one"](candidate) == expected
                            rival_equal_counts["fixed_divider_one"] += int(fixed_equal)
                            checks["fixed_divider_expected_relation"] = fixed_equal == (info["divider"] == 1)
                            if not all(checks.values()):
                                failures.append({**label, "checks": checks})
                        except Exception as exc:  # keep exact failing axis tuple
                            failures.append({**label, "exception": f"{type(exc).__name__}: {exc}"})

    coercion = []
    for kwargs in (
        {"K": "7", "n_colors": 3},
        {"K": 7.5, "n_colors": 3},
        {"K": True, "n_colors": 3},
        {"K": 7, "n_colors": "3"},
        {"K": 7, "n_colors": 2.9},
        {"K": 7, "n_colors": False},
    ):
        try:
            gen.generate(0, 0, difficulty="easy", **kwargs)
        except Exception as exc:
            coercion.append({"kwargs": kwargs, "rejected": True, "error": f"{type(exc).__name__}: {exc}"})
        else:
            coercion.append({"kwargs": kwargs, "rejected": False})

    report = {
        "task_id": TASK_ID,
        "generator_sha256": source_sha,
        "generator_version": gen.VERSION,
        "canonical_pairs": len(pairs),
        "nearest_pair_only_fits_canonical": canonical_fit,
        "counterexample": {
            "fixture": str(fixture_path.relative_to(REPO_ROOT)),
            "self_check": gen.self_check(grid),
            "strict_canonical_like": gen.strict_canonical_like(grid),
            "intended_matches_fixture": intended == fixture["intended"],
            "rival_matches_fixture": rival == fixture["nearest_pair_only"],
            "difference_count": sum(a != b for ar, br in zip(intended, rival) for a, b in zip(ar, br)),
            "first_differences": first_differences(rival, intended),
        },
        "axis_stress": {
            "seed_count": args.seeds,
            "schedule_residues": gen.LESSON_SCHEDULE_PERIOD,
            "cases": cases,
            "failures": failures,
            "divider_counts": dict(sorted(dividers.items())),
            "maximum_markers_per_color_counts": dict(sorted(marker_counts.items())),
            "rival_equal_counts": dict(sorted(rival_equal_counts.items())),
        },
        "coercion_cases": coercion,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "generator_sha256": source_sha,
        "cases": cases,
        "failures": len(failures),
        "canonical_fit": canonical_fit,
        "counterexample_difference_count": report["counterexample"]["difference_count"],
        "all_non_integer_axes_rejected": all(item["rejected"] for item in coercion),
    }, indent=2))
    return 0 if not failures and all(canonical_fit) and report["counterexample"]["difference_count"] > 0 and all(item["rejected"] for item in coercion) else 1


if __name__ == "__main__":
    raise SystemExit(main())
