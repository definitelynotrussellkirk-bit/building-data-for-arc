"""Bounded teaching and shortcut audit for the segment-interior relay family."""
from __future__ import annotations

import argparse
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
from typing import Callable, Iterable

HERE = Path(__file__).resolve().parent


def _load_adapter():
    spec = importlib.util.spec_from_file_location("segment_parametric_adapter_audit", HERE / "adapter.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load adapter")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ADAPTER = _load_adapter()
Grid = list[list[int]]


def _mark(grid: Grid, selected: list[dict[str, object]]) -> Grid:
    out = deepcopy(grid)
    for segment in selected:
        for r, c in segment["cells"][1:-1]:
            out[r][c] = 2
    return out


def _mark_orientation(grid: Grid, orientation: str) -> Grid:
    return _mark(grid, [s for s in ADAPTER.segments(grid) if s["orientation"] == orientation])


def _same_as_controller(grid: Grid) -> Grid:
    orientation = ADAPTER.controller_orientation(grid)
    return _mark_orientation(grid, orientation)


def _longest_only(grid: Grid) -> Grid:
    found = ADAPTER.segments(grid)
    maximum = max(s["length"] for s in found)
    selected = [s for s in found if s["length"] == maximum]
    return _mark(grid, selected[:1])


def _endpoints_all(grid: Grid) -> Grid:
    out = deepcopy(grid)
    for segment in ADAPTER.segments(grid):
        for r, c in (segment["cells"][0], segment["cells"][-1]):
            out[r][c] = 2
    return out


def run_audit(seeds: Iterable[int] = range(20)) -> dict[str, object]:
    teaching_holes: list[dict[str, object]] = []
    finite_equivalences: list[dict[str, object]] = []
    rival_rejections: dict[str, int] = {}
    orientations: set[str] = set()
    minimum_30 = 10**9
    episodes = 0

    for seed in seeds:
        for scope in ADAPTER.SCOPES:
            settings = {"scope": scope}
            episode = ADAPTER.generate(int(seed), settings, demos=3, queries=4)
            episodes += 1
            for pair in episode["train"] + episode["test"]:
                orientations.add(ADAPTER.controller_orientation(pair["input"]))
                if len(pair["input"]) == 30 and len(pair["input"][0]) == 30:
                    minimum_30 = min(
                        minimum_30,
                        sum(cell == 1 for row in pair["input"] for cell in row),
                    )

            opposite = ("perpendicular_to_longest" if scope == "all_segments"
                        else "all_segments")
            rivals: dict[str, Callable[[Grid], Grid]] = {
                "opposite_setting": lambda g, other=opposite: ADAPTER.transform(g, other),
                "same_orientation_as_controller": _same_as_controller,
                "horizontal_only": lambda g: _mark_orientation(g, "horizontal"),
                "vertical_only": lambda g: _mark_orientation(g, "vertical"),
                "longest_only": _longest_only,
                "endpoints_not_interiors": _endpoints_all,
                "copy_input": deepcopy,
            }
            for name, rival in rivals.items():
                train_matches = [rival(pair["input"]) == pair["output"]
                                 for pair in episode["train"]]
                if all(train_matches):
                    query_matches = [rival(pair["input"]) == pair["output"]
                                     for pair in episode["test"]]
                    row = {"seed": int(seed), "settings": settings, "rival": name,
                           "query_matches": query_matches}
                    if all(query_matches):
                        finite_equivalences.append(row)
                    else:
                        teaching_holes.append(row)
                else:
                    rival_rejections[name] = rival_rejections.get(name, 0) + 1

    if minimum_30 == 10**9:
        minimum_30 = 0
    status = "passed" if not teaching_holes and not finite_equivalences else "failed"
    return {
        "schema": "39ad03f74acb-parametric-bounded-audit-v1",
        "status": status,
        "episodes": episodes,
        "settings": list(ADAPTER.SCOPES),
        "demos": 3,
        "queries": 4,
        "declared_rivals": sorted(rival_rejections),
        "rival_rejections": rival_rejections,
        "teaching_holes": teaching_holes,
        "finite_equivalences": finite_equivalences,
        "controller_orientations": sorted(orientations),
        "minimum_blue_cells_30x30": minimum_30,
        "limits": "Finite seeds and declared rivals only; this is not universal uniqueness.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seeds", type=int, default=20)
    args = parser.parse_args()
    report = run_audit(range(args.seeds))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "episodes": report["episodes"],
                      "teaching_holes": len(report["teaching_holes"])}))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
