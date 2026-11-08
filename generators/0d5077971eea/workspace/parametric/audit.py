"""Bounded adversarial self-audit for the native row-header family."""
from __future__ import annotations

from copy import deepcopy
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Callable

_HOME = Path(__file__).resolve().parent
_ADAPTER_PATH = _HOME / "adapter.py"
_NAME = "_audit_adapter_0d_" + hashlib.sha256(str(_ADAPTER_PATH).encode()).hexdigest()
_SPEC = importlib.util.spec_from_file_location(_NAME, _ADAPTER_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError("cannot load adjacent adapter")
_ADAPTER = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = _ADAPTER
_SPEC.loader.exec_module(_ADAPTER)

Grid = list[list[int]]
Rival = Callable[[Grid], Grid]


def _row_local(grid: Grid) -> Grid:
    return [
        [row[0] if c > 0 and value == 8 and row[0] != 0 else value
         for c, value in enumerate(row)]
        for row in grid
    ]


def _eligible(grid: Grid) -> list[tuple[int, int, int]]:
    return [
        (sum(value == 8 for value in row[1:]), r, row[0])
        for r, row in enumerate(grid)
        if row[0] not in (0, 8) and any(value == 8 for value in row[1:])
    ]


def _paint_all(grid: Grid, color: int) -> Grid:
    return [
        [color if c > 0 and value == 8 else value for c, value in enumerate(row)]
        for row in grid
    ]


def _densest(grid: Grid) -> Grid:
    rows = _eligible(grid)
    peak = max(count for count, _, _ in rows)
    winners = [(r, color) for count, r, color in rows if count == peak]
    if len(winners) != 1:
        raise ValueError("expected one densest eligible row")
    return _paint_all(grid, winners[0][1])


def _first_eligible_global(grid: Grid) -> Grid:
    rows = sorted(_eligible(grid), key=lambda item: item[1])
    return _paint_all(grid, rows[0][2])


def _source_row_only(grid: Grid) -> Grid:
    rows = _eligible(grid)
    peak = max(count for count, _, _ in rows)
    winners = [(r, color) for count, r, color in rows if count == peak]
    if len(winners) != 1:
        raise ValueError("expected one densest eligible row")
    source_row, color = winners[0]
    output = deepcopy(grid)
    output[source_row] = [
        color if c > 0 and value == 8 else value
        for c, value in enumerate(output[source_row])
    ]
    return output


def _fixed_color(color: int) -> Rival:
    return lambda grid: _paint_all(grid, color)


def _fits(rival: Rival, pairs: list[dict]) -> bool:
    return all(rival(pair["input"]) == pair["output"] for pair in pairs)


def run(*, seeds=(0, 17, 991)) -> dict:
    findings: list[dict] = []
    survivors: list[dict] = []
    has_30x30 = False
    episodes_checked = 0

    for seed in seeds:
        for policy, correct in (("row_local", _row_local), ("densest_source", _densest)):
            episode = _ADAPTER.generate(seed, {"header_policy": policy}, 2, 4)
            episodes_checked += 1
            pairs = episode["train"] + episode["test"]
            has_30x30 = has_30x30 or any(
                len(pair["input"]) == 30 and len(pair["input"][0]) == 30
                for pair in episode["test"]
            )
            if not all(correct(pair["input"]) == pair["output"] for pair in pairs):
                findings.append({"seed": seed, "policy": policy, "finding": "label_mismatch"})

            first_color = _eligible(episode["train"][0]["input"])[0][2]
            densest_rows = _eligible(episode["train"][0]["input"])
            peak = max(item[0] for item in densest_rows)
            fixed_dense_color = next(color for count, _, color in densest_rows if count == peak)
            rivals = {
                "row_local": _row_local,
                "densest_source": _densest,
                "first_eligible_global": _first_eligible_global,
                "source_row_only": _source_row_only,
                "fixed_first_eligible_color": _fixed_color(first_color),
                "fixed_first_densest_color": _fixed_color(fixed_dense_color),
            }
            for name, rival in rivals.items():
                if name == policy:
                    continue
                if _fits(rival, episode["train"]):
                    survivors.append({"seed": seed, "policy": policy, "rival": name})

            if len({_eligible(pair["input"])[0][2] for pair in episode["train"]}) < 1:
                findings.append({"seed": seed, "policy": policy, "finding": "missing_headers"})
            selected_colors = []
            for pair in episode["train"]:
                rows = _eligible(pair["input"])
                peak = max(item[0] for item in rows)
                selected_colors.append(next(color for count, _, color in rows if count == peak))
            if len(set(selected_colors)) != len(selected_colors):
                findings.append({"seed": seed, "policy": policy, "finding": "fixed_selected_color"})

    return {
        "schema": "arcpuzzles-parametric-self-audit-v1",
        "task_id": "0d5077971eea",
        "status": "passed" if not findings and not survivors and has_30x30 else "failed",
        "episodes_checked": episodes_checked,
        "seeds": list(seeds),
        "has_30x30": has_30x30,
        "surviving_rivals": survivors,
        "findings": findings,
        "limitations": [
            "Finite named-rival audit; it does not prove unrestricted uniqueness or learning benefit.",
            "Racket execution is established separately by native qualification and witness replay.",
        ],
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    report = run()
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
