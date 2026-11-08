#!/usr/bin/env python3
"""Fast deterministic regression probe for fc999420d3aa.

This is deliberately smaller than the Racket-backed battery/census. It gives a
future reviewer one command for the historical defect, exact-axis corners, and
all rotations of the small teaching schedule.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import importlib.util
import itertools
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve()
GENERATOR = HERE.parents[1] / "generator.py"


def _find_repo_root() -> Path:
    for parent in HERE.parents:
        if (parent / "shared" / "runtime" / "reviewer_support.py").is_file():
            return parent
    raise RuntimeError("could not locate portable repository root")


RUNTIME = _find_repo_root() / "shared" / "runtime"
sys.path.insert(0, str(RUNTIME))

from reviewer_support import canonical_pairs, find_root  # noqa: E402


def load_generator():
    spec = importlib.util.spec_from_file_location("fc999420d3aa_review_probe", GENERATOR)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {GENERATOR}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def pair(gen, grid):
    return {"input": deepcopy(grid), "output": gen.rule_mirror(grid)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    gen = load_generator()
    root = find_root(HERE)

    canonical = canonical_pairs(gen.TASK_ID, root=root)
    shortcut_fit = {
        name: sum(rival(deepcopy(item["input"])) == item["output"] for item in canonical)
        for name, rival in gen.CANONICAL_SHORTCUTS.items()
    }

    audited = gen.generate(810_027, 27, difficulty="easy")
    audited_colors = [audited[r][c] for r, c, _ in gen._firing_centers(audited)]

    boundary_cases = 0
    for difficulty in (None, "easy", "medium", "hard"):
        for h, w, n in itertools.product((5, 18), (5, 20), (1, 2)):
            requested = {"grid_h": h, "grid_w": w, "n_motifs": n}
            grid = gen.generate(221, 17, difficulty=difficulty, **requested)
            assert gen.strict_canonical_like(grid) == []
            assert gen.observe_overrides(grid) == requested
            boundary_cases += 1

    rotation_checks = 0
    for difficulty in (None, "easy", "medium", "hard"):
        for start in range(12):
            pairs = [pair(gen, gen.generate(51_000 + start, start + offset,
                                            difficulty=difficulty))
                     for offset in range(4)]
            for query_index in range(4):
                demos = [item for index, item in enumerate(pairs) if index != query_index]
                assert gen.lesson_identifiable(demos, pairs[query_index]) == []
                rotation_checks += 1

    report = {
        "task_id": gen.TASK_ID,
        "version": gen.VERSION,
        "generator_path": str(GENERATOR),
        "canonical_pairs": len(canonical),
        "canonical_shortcut_fit": shortcut_fit,
        "audited_seed": {
            "seed": 810027,
            "sample_index": 27,
            "difficulty": "easy",
            "target_colors": audited_colors,
            "distinct": len(audited_colors) == len(set(audited_colors)) == 2,
        },
        "exact_axis_boundary_cases": boundary_cases,
        "cyclic_rotation_checks": rotation_checks,
        "status": "pass",
        "limits": "Python-mirror diagnostic only; use the Racket-backed census for labels.",
    }
    text = json.dumps(report, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
