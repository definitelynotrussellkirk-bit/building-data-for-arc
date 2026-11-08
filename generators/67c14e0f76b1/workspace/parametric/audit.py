"""Bounded adversarial audit for the 67c14e0f76b1 native family."""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Callable

_HOME = Path(__file__).resolve().parent
_ADAPTER_PATH = _HOME / "adapter.py"
_SPEC = importlib.util.spec_from_file_location(
    "_audit_67c_" + hashlib.sha256(str(_ADAPTER_PATH).encode()).hexdigest(),
    _ADAPTER_PATH,
)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError("cannot load adjacent adapter")
ADAPTER = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = ADAPTER
_SPEC.loader.exec_module(ADAPTER)

Grid = list[list[int]]
Rival = Callable[[Grid], Grid]


def _identity(grid: Grid) -> Grid:
    return deepcopy(grid)


def _mark_vertical_too(grid: Grid) -> Grid:
    output = ADAPTER.intermediate(grid)
    height, width = len(grid), len(grid[0])
    horizontal = set(ADAPTER.target_cells(grid))
    for r in range(1, height - 1):
        for c in range(width):
            if (
                grid[r][c] == 0
                and grid[r - 1][c] == 1
                and grid[r + 1][c] == 1
                and (r, c) not in horizontal
            ):
                output[r][c] = 2
    return output


def _mark_any_horizontal_span(grid: Grid) -> Grid:
    output = deepcopy(grid)
    height, width = len(grid), len(grid[0])
    for r in range(height):
        for c in range(1, width - 1):
            if grid[r][c] == 0 and 1 in grid[r][:c] and 1 in grid[r][c + 1 :]:
                output[r][c] = 2
    return output


def _recolor_first_marked(grid: Grid) -> Grid:
    stage = ADAPTER.intermediate(grid)
    components = ADAPTER.marked_components(stage)
    output = deepcopy(stage)
    for r, c in components[0]:
        output[r][c] = 8
    return output


def _fits(rival: Rival, pairs: list[dict[str, Grid]]) -> bool:
    return all(rival(pair["input"]) == pair["output"] for pair in pairs)


def _load_base():
    path = _HOME.parents[1] / "generator.py"
    spec = importlib.util.spec_from_file_location("_base_67c_audit", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load base generator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _base_pair(base, grid: Grid) -> dict[str, Grid]:
    return {"input": deepcopy(grid), "output": base.rule_mirror(grid)}


def run(seed_count: int = 64) -> dict[str, Any]:
    if type(seed_count) is not int or not 1 <= seed_count <= 4096:
        raise ValueError("seed_count must be an integer in 1..4096")
    findings: list[dict[str, Any]] = []
    survivors: list[dict[str, Any]] = []
    counts = Counter()
    selected_anchors: set[tuple[int, int]] = set()
    selected_sizes: set[int] = set()
    base = _load_base()

    for seed in range(seed_count):
        for start in range(4):
            demos = [
                _base_pair(base, base.generate(seed, start + offset, difficulty="medium"))
                for offset in range(base.EXAMPLES_NEEDED)
            ]
            query = _base_pair(
                base,
                base.generate(seed, start + base.EXAMPLES_NEEDED, difficulty="medium"),
            )
            reasons = base.lesson_identifiable(demos, query)
            counts["base_lesson_windows"] += 1
            if reasons:
                findings.append(
                    {"seed": seed, "start": start, "finding": "base_lesson_gate", "reasons": reasons}
                )

        episodes: dict[str, dict[str, Any]] = {}
        for postprocess in ("mark_only", "largest_marked"):
            setting = {"postprocess": postprocess}
            episode = ADAPTER.generate(seed, setting, 3, 4)
            short = ADAPTER.generate(seed, setting, 2, 1)
            long = ADAPTER.generate(seed, setting, 6, 4)
            episodes[postprocess] = episode
            counts["episodes"] += 1
            if short["train"] != long["train"][:2] or short["test"] != long["test"][:1]:
                findings.append({"seed": seed, "postprocess": postprocess, "finding": "prefix_instability"})
            pairs = episode["train"] + episode["test"]
            if len({repr(pair["input"]) for pair in pairs}) != len(pairs):
                findings.append({"seed": seed, "postprocess": postprocess, "finding": "duplicate_inputs"})
            for pair in pairs:
                counts["pairs"] += 1
                expected = ADAPTER.predict(pair["input"], postprocess)
                if pair["output"] != expected:
                    findings.append({"seed": seed, "postprocess": postprocess, "finding": "label_mismatch"})
                other = "largest_marked" if postprocess == "mark_only" else "mark_only"
                if ADAPTER.predict(pair["input"], other) == pair["output"]:
                    findings.append({"seed": seed, "postprocess": postprocess, "finding": "setting_not_distinguished"})
                else:
                    counts["setting_differences"] += 1
                if postprocess == "largest_marked":
                    components = ADAPTER.marked_components(ADAPTER.intermediate(pair["input"]))
                    sizes = [len(cells) for cells in components]
                    if len(components) < 3 or sizes.count(max(sizes)) != 1:
                        findings.append({"seed": seed, "postprocess": postprocess, "finding": "component_contract", "sizes": sizes})
                    else:
                        winner = max(components, key=len)
                        selected_anchors.add(min(winner))
                        selected_sizes.add(len(winner))
                    if ADAPTER.wrong_order_predict(pair["input"]) == pair["output"]:
                        findings.append({"seed": seed, "postprocess": postprocess, "finding": "wrong_order_matches"})
                    else:
                        counts["wrong_order_refutations"] += 1
            last = episode["test"][-1]["input"]
            if (len(last), len(last[0])) != (30, 30):
                findings.append({"seed": seed, "postprocess": postprocess, "finding": "missing_30x30"})
            elif sum(value != 0 for row in last for value in row) < 100:
                findings.append({"seed": seed, "postprocess": postprocess, "finding": "thin_30x30"})
            elif not any(c == 1 for _, c in ADAPTER.target_cells(last)) or not any(
                c == 28 for _, c in ADAPTER.target_cells(last)
            ):
                findings.append({"seed": seed, "postprocess": postprocess, "finding": "missing_boundary_targets"})
            else:
                counts["substantive_30x30"] += 1

            rivals: dict[str, Rival]
            if postprocess == "mark_only":
                rivals = {
                    "identity_no_mark": _identity,
                    "mark_vertical_too": _mark_vertical_too,
                    "mark_any_horizontal_span": _mark_any_horizontal_span,
                }
            else:
                rivals = {
                    "wrong_order_raw_blue": ADAPTER.wrong_order_predict,
                    "mark_only": lambda grid: ADAPTER.predict(grid, "mark_only"),
                    "recolor_first_marked": _recolor_first_marked,
                }
            for name, rival in rivals.items():
                if _fits(rival, episode["train"]):
                    survivors.append({"seed": seed, "postprocess": postprocess, "rival": name})

        ordinary_inputs = [
            pair["input"]
            for pair in episodes["mark_only"]["train"] + episodes["mark_only"]["test"]
        ]
        alternate_inputs = [
            pair["input"]
            for pair in episodes["largest_marked"]["train"] + episodes["largest_marked"]["test"]
        ]
        if ordinary_inputs != alternate_inputs:
            findings.append({"seed": seed, "finding": "settings_change_inputs"})
        else:
            counts["setting_neutral_episodes"] += 1

    if len(selected_anchors) < 3:
        findings.append({"finding": "selected_location_does_not_vary", "values": sorted(selected_anchors)})
    if len(selected_sizes) < 4:
        findings.append({"finding": "selected_size_does_not_vary", "values": sorted(selected_sizes)})

    status = "passed" if not findings and not survivors else "failed"
    return {
        "schema": "arcpuzzles-parametric-self-audit-v1",
        "task_id": "67c14e0f76b1",
        "status": status,
        "seed_count": seed_count,
        "counts": dict(sorted(counts.items())),
        "selected_anchor_count": len(selected_anchors),
        "selected_sizes": sorted(selected_sizes),
        "surviving_rivals": survivors,
        "findings": findings,
        "limitations": [
            "Finite named-rival audit; it does not prove unrestricted uniqueness or learning benefit.",
            "Protected Racket execution is established separately by authoring preflight and causal replay.",
        ],
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=64)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    report = run(args.seeds)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
