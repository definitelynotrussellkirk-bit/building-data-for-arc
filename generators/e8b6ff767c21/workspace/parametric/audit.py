"""Bounded named-rival self-audit for the e8b6ff767c21 native family."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Callable


_HOME = Path(__file__).resolve().parent
_ADAPTER_PATH = _HOME / "adapter.py"
_NAME = "_e8b6ff767c21_audit_adapter_" + hashlib.sha256(str(_ADAPTER_PATH).encode()).hexdigest()
_SPEC = importlib.util.spec_from_file_location(_NAME, _ADAPTER_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load adjacent adapter")
_ADAPTER = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = _ADAPTER
_SPEC.loader.exec_module(_ADAPTER)

Grid = list[list[int]]
Rival = Callable[[Grid], Grid]


def _blank_identity(grid: Grid) -> Grid:
    return deepcopy(grid)


def _entrance_only(grid: Grid) -> Grid:
    output = _ADAPTER.native_transform(grid, "none")
    output[1][0] = 2
    return output


def _all_open_blue(grid: Grid) -> Grid:
    output = _ADAPTER.native_transform(grid, "none")
    return [[2 if value == 0 else value for value in row] for row in output]


def _green_as_blue(grid: Grid) -> Grid:
    output = _ADAPTER.native_transform(grid, "none")
    return [[2 if value == 3 else value for value in row] for row in output]


def _straight_to_terminal(grid: Grid) -> Grid:
    """Ignore spiral walls and draw a row-then-column route to the true target."""
    output = _ADAPTER.native_transform(grid, "none")
    meta = _ADAPTER.route_metadata(grid)
    row, col = meta["entrance"]
    target_row, target_col = meta["terminal_neighbor"]
    output[row][col] = 2
    while col != target_col:
        col += 1 if target_col > col else -1
        output[row][col] = 2
    while row != target_row:
        row += 1 if target_row > row else -1
        output[row][col] = 2
    return output


def _solid_green_border(grid: Grid) -> Grid:
    height, width = len(grid), len(grid[0])
    return [
        [3 if row in (0, height - 1) or col in (0, width - 1) else 0 for col in range(width)]
        for row in range(height)
    ]


def _fits(rival: Rival, pairs: list[dict]) -> bool:
    return all(rival(pair["input"]) == pair["output"] for pair in pairs)


def run(*, seeds=(0, 17, 991)) -> dict:
    findings: list[dict] = []
    survivors: list[dict] = []
    has_30x30 = False
    episodes_checked = 0

    for seed in seeds:
        for overlay in ("none", "terminal_path"):
            episode = _ADAPTER.generate(seed, {"route_overlay": overlay}, 2, 4)
            episodes_checked += 1
            pairs = episode["train"] + episode["test"]
            has_30x30 |= any(
                len(pair["input"]) == 30 and len(pair["input"][0]) == 30
                for pair in episode["test"]
            )
            for pair in pairs:
                if pair["output"] != _ADAPTER.native_transform(pair["input"], overlay):
                    findings.append({"seed": seed, "overlay": overlay, "finding": "python_label_mismatch"})

            rivals: dict[str, Rival] = {
                "other_declared_overlay": (
                    lambda grid, other="terminal_path" if overlay == "none" else "none":
                    _ADAPTER.native_transform(grid, other)
                ),
                "blank_identity": _blank_identity,
                "solid_green_border": _solid_green_border,
                "green_as_blue": _green_as_blue,
            }
            if overlay == "terminal_path":
                rivals.update({
                    "entrance_only": _entrance_only,
                    "all_open_blue": _all_open_blue,
                    "straight_to_terminal_ignoring_walls": _straight_to_terminal,
                })
            for name, rival in rivals.items():
                if _fits(rival, episode["train"]):
                    survivors.append({"seed": seed, "overlay": overlay, "rival": name})

    return {
        "schema": "arcpuzzles-parametric-self-audit-v1",
        "task_id": "e8b6ff767c21",
        "status": "passed" if not findings and not survivors and has_30x30 else "failed",
        "episodes_checked": episodes_checked,
        "seeds": list(seeds),
        "has_30x30": has_30x30,
        "surviving_rivals": survivors,
        "findings": findings,
        "limitations": [
            "Finite named-rival audit; it does not prove unrestricted uniqueness or learning benefit.",
            "Protected Racket parity is established separately by authoring preflight and witness replay.",
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
