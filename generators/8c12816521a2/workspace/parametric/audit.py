"""Bounded learnability and protected-Racket label audit for 8c12816521a2.

The named rivals are finite, explicit shortcuts, not a universal uniqueness
claim.  Rival fitting reads demonstrations only; query answers are used solely
to verify the selected Racket program.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

HOME = Path(__file__).resolve().parent
ROOT = HOME.parents[3]
TASK = "8c12816521a2"
RIVALS = (
    "other_anchor",
    "fixed_count_one",
    "global_max_count",
    "yellow_count",
    "all_lanes",
    "no_green",
    "wrong_tip",
    "no_transpose",
)


def _load_prototype():
    path = HOME / "prototype.py"
    name = "_arc_8c12816521a2_audit_" + hashlib.sha256(str(path).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load prototype: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _transpose(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid)]


def _facts(grid: list[list[int]]) -> dict[str, Any]:
    source = [row[:] for row in grid]
    horizontal = any(all(value == 8 for value in row) for row in source)
    normalized = _transpose(source) if horizontal else source
    height, width = len(normalized), len(normalized[0])
    separators = [
        col for col in range(width)
        if all(normalized[row][col] == 8 for row in range(height))
    ]
    if len(separators) != 1:
        raise ValueError("audit inputs require exactly one normalized separator")
    separator = separators[0]
    left = sum(value == 4 for row in normalized for value in row[:separator])
    right = sum(value == 4 for row in normalized for value in row[separator + 1 :])
    yellow_left = left > right
    lanes = []
    for row in normalized:
        yellow_range = range(separator) if yellow_left else range(separator + 1, width)
        red_range = range(separator + 1, width) if yellow_left else range(separator)
        yellow = [col for col in yellow_range if row[col] == 4]
        red_count = sum(row[col] == 2 for col in red_range)
        lanes.append({"yellow": yellow, "red_count": red_count})
    return {
        "source": source,
        "normalized": normalized,
        "horizontal": horizontal,
        "height": height,
        "width": width,
        "separator": separator,
        "yellow_left": yellow_left,
        "lanes": lanes,
    }


def _anchor_cell(anchor: str, yellow_left: bool, separator: int, width: int,
                 count: int, col: int) -> int | None:
    if yellow_left:
        if col <= separator:
            return None
        if anchor == "far_edge":
            return 2 if col >= width - count else 8
        return 2 if col < separator + count + 1 else 8
    if col >= separator:
        return None
    if anchor == "far_edge":
        return 2 if col < count else 8
    return 2 if col >= separator - count else 8


def _render(grid: list[list[int]], anchor: str, rival: str | None = None) -> list[list[int]]:
    facts = _facts(grid)
    if rival == "no_transpose" and facts["horizontal"]:
        return deepcopy(facts["source"])
    normalized = facts["normalized"]
    separator = facts["separator"]
    yellow_left = facts["yellow_left"]
    width = facts["width"]
    global_max = max(lane["red_count"] for lane in facts["lanes"])
    output = []
    for row_index, values in enumerate(normalized):
        lane = facts["lanes"][row_index]
        yellow = lane["yellow"]
        triggered = bool(yellow)
        if not triggered and rival != "all_lanes":
            output.append(values[:])
            continue
        if rival == "fixed_count_one":
            count = 1
        elif rival == "global_max_count":
            count = global_max
        elif rival == "yellow_count":
            count = len(yellow)
        else:
            count = lane["red_count"]
        row = []
        for col, value in enumerate(values):
            if not triggered:
                relocated = _anchor_cell(anchor, yellow_left, separator, width, count, col)
                row.append(value if relocated is None else relocated)
                continue
            recolor = value == 4
            if rival == "no_green":
                recolor = False
            elif rival == "wrong_tip" and recolor:
                tip = yellow[0] if yellow_left else yellow[-1]
                recolor = col == tip
            if recolor:
                new_value = 3
            elif col == separator:
                new_value = 8
            elif yellow_left and col < separator and col > yellow[-1]:
                new_value = 4
            elif not yellow_left and col > separator and col < yellow[0]:
                new_value = 4
            else:
                relocated = _anchor_cell(anchor, yellow_left, separator, width, count, col)
                new_value = value if relocated is None else relocated
            row.append(new_value)
        output.append(row)
    return _transpose(output) if facts["horizontal"] else output


def rival_output(grid: list[list[int]], anchor: str, rival: str) -> list[list[int]]:
    if rival not in RIVALS:
        raise ValueError(f"unknown rival: {rival}")
    if rival == "other_anchor":
        anchor = "separator_edge" if anchor == "far_edge" else "far_edge"
        rival = None
    return _render(grid, anchor, rival)


def _features(grids: list[list[list[int]]]) -> list[str]:
    names: set[str] = set()
    for grid in grids:
        facts = _facts(grid)
        names.add("horizontal" if facts["horizontal"] else "vertical")
        names.add("yellow_left" if facts["yellow_left"] else "yellow_right")
        triggered = [lane for lane in facts["lanes"] if lane["yellow"]]
        if len({lane["red_count"] for lane in triggered}) > 1:
            names.add("mixed_red_counts")
        if any(len(lane["yellow"]) > 1 for lane in triggered):
            names.add("multi_yellow")
        if len(triggered) < len(facts["lanes"]):
            names.add("nontrigger_lanes")
    return sorted(names)


def teaching_audit(seed: int, anchor: str, demos: int = 2) -> dict[str, Any]:
    prototype = _load_prototype()
    episode = prototype.generate(seed, {"red_anchor": anchor}, demos, 4)
    rejected: dict[str, list[int]] = {}
    survivors = []
    for rival in RIVALS:
        mismatches = [
            index
            for index, pair in enumerate(episode["train"])
            if rival_output(pair["input"], anchor, rival) != pair["output"]
        ]
        rejected[rival] = mismatches
        if not mismatches:
            survivors.append(rival)
    return {
        "seed": seed,
        "settings": {"red_anchor": anchor},
        "demos": demos,
        "queries": 4,
        "query_answers_used": False,
        "rejected_by_demo": rejected,
        "survivors": survivors,
        "demo_features": _features([pair["input"] for pair in episode["train"]]),
        "scope": "finite named rivals on demonstrations only; no universal identifiability claim",
    }


def _sha_json(value: Any) -> str:
    body = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(body).hexdigest()


def run(output: Path) -> dict[str, Any]:
    if output.exists() or output.is_symlink():
        raise FileExistsError(f"refusing existing evidence destination: {output}")
    output.mkdir(parents=True)
    prototype = _load_prototype()
    reports = [teaching_audit(seed, anchor, 2)
               for seed in (0, 17) for anchor in prototype.ANCHORS]
    if any(report["survivors"] for report in reports):
        raise AssertionError("a named shortcut survived the two-demo lesson")

    sys.path[:0] = [str(ROOT / "src"), str(ROOT / "shared/runtime")]
    from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator

    executions = []
    bridge = None
    with _local_imports(ROOT / "shared/runtime", HOME):
        apply, identity, bridge = _real_evaluator(ROOT / "shared/runtime")
        try:
            for seed in (0, 17):
                for anchor in prototype.ANCHORS:
                    episode = prototype.generate(seed, {"red_anchor": anchor}, 2, 4)
                    chosen = episode["program_solution"]
                    other_anchor = "separator_edge" if anchor == "far_edge" else "far_edge"
                    other = prototype.program({"red_anchor": other_anchor})
                    other_rejections = []
                    for split in ("train", "test"):
                        for index, pair in enumerate(episode[split]):
                            actual = _grid(apply(chosen, deepcopy(pair["input"])))
                            if actual != pair["output"]:
                                raise AssertionError(f"selected Racket label mismatch: {seed}/{anchor}/{split}/{index}")
                            executions.append({
                                "seed": seed,
                                "settings": {"red_anchor": anchor},
                                "split": split,
                                "pair_index": index,
                                "shape": [len(pair["input"]), len(pair["input"][0])],
                                "input_sha256": _sha_json(pair["input"]),
                                "output_sha256": _sha_json(actual),
                            })
                    for index, pair in enumerate(episode["train"]):
                        if _grid(apply(other, deepcopy(pair["input"]))) != pair["output"]:
                            other_rejections.append(index)
                    if not other_rejections:
                        raise AssertionError(f"declared rival survived protected Racket demos: {seed}/{anchor}")
                    matching = next(report for report in reports
                                    if report["seed"] == seed and report["settings"]["red_anchor"] == anchor)
                    matching["declared_rival_racket_rejected_by_demo"] = other_rejections
        finally:
            if bridge is not None:
                bridge.close()

    sources = {}
    for name in ("prototype.py", "adapter.py", "promotion.json", "canonical.rkt",
                 "separator_edge.rkt", "wrong_count_one.rkt", "audit.py"):
        path = HOME / name
        sources[path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    report = {
        "schema": "8c12816521a2-red-anchor-self-review-v1",
        "status": "passed",
        "task_id": TASK,
        "scope": "finite two-setting and seven-shortcut demo audit; selected labels and declared rival executed in protected Racket",
        "limits": "No universal uniqueness or training-gain claim.",
        "query_answers_used_for_rival_selection": False,
        "sources": sources,
        "runtime": identity,
        "teaching": reports,
        "selected_racket_executions": executions,
        "racket_evaluations": len(executions) + len(reports) * 2,
        "actual_30x30_selected_executions": sum(row["shape"] == [30, 30] for row in executions),
    }
    (output / "self_review.json").write_text(
        json.dumps(report, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    )
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    report = run(args.out)
    print(json.dumps({
        "status": report["status"],
        "teaching_cases": len(report["teaching"]),
        "racket_evaluations": report["racket_evaluations"],
        "actual_30x30_selected_executions": report["actual_30x30_selected_executions"],
        "report": str(args.out / "self_review.json"),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
