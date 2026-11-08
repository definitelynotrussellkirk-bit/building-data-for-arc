#!/usr/bin/env python3
"""Exhaust every declared non-dimension geometry/color cross at 9x10."""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import sys
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    task = repo / "generators" / "b2387c876b95"
    sys.path[:0] = [str(repo / "src"), str(repo / "shared" / "runtime"), str(repo), str(task / "workspace")]

    from reference_probe import intended_output, load_generator, observed  # noqa: PLC0415

    generator_path = task / "generator.py"
    gen = load_generator(generator_path)
    failures: list[dict] = []
    total = 0
    for orientation, side, source, distractor_shape, color in itertools.product(
        ("vertical", "horizontal"),
        ("negative", "positive"),
        range(12),
        range(9),
        (4, 6, 7, 8, 9),
    ):
        total += 1
        requested = {
            "grid_h": 9,
            "grid_w": 10,
            "orientation": orientation,
            "source_side": side,
            "shape_variant": source,
            "distractor_color": color,
            "distractor_shape": distractor_shape,
        }
        try:
            grid = gen.generate(90410, total - 1, **requested)
            reasons = gen.self_check(grid)
            got = observed(grid, gen.SOURCE_SHAPES, gen.DISTRACTOR_SHAPES)
            mirror = gen.rule_mirror(grid)
            independent = intended_output(grid)
            if reasons or got != requested or mirror != independent:
                failures.append({
                    "case": total - 1,
                    "requested": requested,
                    "observed": got,
                    "self_check": reasons,
                    "oracle_equal": mirror == independent,
                })
        except Exception as exc:  # diagnostic must retain exact first failures
            failures.append({
                "case": total - 1,
                "requested": requested,
                "exception": f"{type(exc).__name__}: {exc}",
            })

    report = {
        "schema": "b2387c876b95-exhaustive-cross-v1",
        "task_id": "b2387c876b95",
        "generator_sha256": sha256(generator_path),
        "domain": {
            "grid_h": 9,
            "grid_w": 10,
            "orientations": 2,
            "source_sides": 2,
            "source_shapes": 12,
            "distractor_shapes": 9,
            "distractor_colors": 5,
        },
        "total": total,
        "passed": total - len(failures),
        "failed": len(failures),
        "failures": failures[:50],
        "failure_details_truncated": len(failures) > 50,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("task_id", "generator_sha256", "total", "passed", "failed")}, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
