"""Protected-Racket finite self-audit for the wall-scope lessons."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

from arcpuzzles.parametric_worker import _local_imports, _real_evaluator
from reviewer_support import find_root


HERE = Path(__file__).resolve().parent
TASK_ID = "85d01dd02c6d"
SETTINGS = (
    {"wall_scope": "every_wall"},
    {"wall_scope": "axis_dividers"},
)


def _load_prototype():
    path = HERE / "prototype.py"
    name = "_audit_85d01dd02c6d_" + hashlib.sha256(str(path).encode()).hexdigest()[:16]
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PROTO = _load_prototype()


def _quadrants(grid: list[list[int]]) -> list[int]:
    height, width = len(grid), len(grid[0])
    mid_r, mid_c = height // 2, width // 2
    quadrants = (
        (range(1, mid_r), range(1, mid_c)),
        (range(1, mid_r), range(mid_c, width - 1)),
        (range(mid_r, height - 1), range(1, mid_c)),
        (range(mid_r, height - 1), range(mid_c, width - 1)),
    )
    return [sum(grid[row][col] != 0 for row in rows for col in cols) for rows, cols in quadrants]


def _mismatches(left: list[list[int]], right: list[list[int]]) -> int:
    return sum(a != b for row_a, row_b in zip(left, right, strict=True) for a, b in zip(row_a, row_b, strict=True))


def build_report(
    *,
    seeds: tuple[int, ...] = (0, 17),
    demos: int = 2,
    queries: int = 4,
    execute_racket: bool = True,
) -> dict[str, Any]:
    if not execute_racket:
        raise ValueError("the retained self-audit requires protected Racket execution")
    root = find_root(__file__)
    runtime = root / "shared" / "runtime"
    episodes: list[dict[str, Any]] = []
    ambiguous: list[dict[str, Any]] = []
    labels_checked = 0
    with _local_imports(runtime, HERE):
        apply, identity, bridge = _real_evaluator(runtime)
        try:
            for seed in seeds:
                for settings in SETTINGS:
                    episode = PROTO.generate(seed, settings, demos=demos, queries=queries)
                    pairs = episode["train"] + episode["test"]
                    selected_program = PROTO.program(settings)
                    selected_outputs = [apply(selected_program, pair["input"]) for pair in pairs]
                    selected_labels_match = all(
                        output == pair["output"] for output, pair in zip(selected_outputs, pairs, strict=True)
                    )
                    labels_checked += len(pairs)
                    rivals = []
                    for name, rival_program in PROTO.rival_programs(settings).items():
                        rival_outputs = [apply(rival_program, pair["input"]) for pair in pairs]
                        demo_mismatches = sum(
                            _mismatches(output, pair["output"])
                            for output, pair in zip(rival_outputs[:demos], episode["train"], strict=True)
                        )
                        query_mismatches = sum(
                            _mismatches(output, pair["output"])
                            for output, pair in zip(rival_outputs[demos:], episode["test"], strict=True)
                        )
                        row = {
                            "name": name,
                            "program_sha256": hashlib.sha256(rival_program.encode()).hexdigest(),
                            "demo_mismatches": demo_mismatches,
                            "query_mismatches": query_mismatches,
                            "survives_demonstrations": demo_mismatches == 0,
                        }
                        rivals.append(row)
                        if demo_mismatches == 0 and query_mismatches > 0:
                            ambiguous.append({"seed": seed, "settings": settings, "rival": name})
                    episodes.append(
                        {
                            "seed": seed,
                            "settings": settings,
                            "selected_program_sha256": hashlib.sha256(selected_program.encode()).hexdigest(),
                            "selected_labels_match": selected_labels_match,
                            "demonstration_analyses": [PROTO.analyze_scene(pair["input"]) for pair in episode["train"]],
                            "rivals": rivals,
                        }
                    )
        finally:
            bridge.close()
    large = PROTO.generate(seeds[-1], SETTINGS[0], demos=demos, queries=4)["test"][-1]["input"]
    return {
        "schema": "arcpuzzles-ray-wall-scope-self-audit-v1",
        "task_id": TASK_ID,
        "scope": {
            "seeds": list(seeds),
            "settings": list(SETTINGS),
            "demos": demos,
            "queries": queries,
            "rivals": ["other_wall_scope", "ignore_all_internal_walls", "one_seed_suffices"],
        },
        "racket": identity,
        "labels_checked": labels_checked,
        "episodes": episodes,
        "ambiguous_rivals": ambiguous,
        "large_query": {
            "shape": [len(large), len(large[0])],
            "nonzero_cells": sum(value != 0 for row in large for value in row),
            "interior_nonzero_by_quadrant": _quadrants(large),
            "analysis": PROTO.analyze_scene(large),
        },
        "limits": "Finite rivals and two seeds only; this does not prove uniqueness against every program.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--demos", type=int, default=2)
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 17])
    args = parser.parse_args(argv)
    report = build_report(seeds=tuple(args.seeds), demos=args.demos, queries=args.queries)
    path = Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "passed" if not report["ambiguous_rivals"] else "ambiguous",
        "labels_checked": report["labels_checked"],
        "episodes": len(report["episodes"]),
        "out": str(path),
    }, sort_keys=True))
    return 0 if not report["ambiguous_rivals"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
