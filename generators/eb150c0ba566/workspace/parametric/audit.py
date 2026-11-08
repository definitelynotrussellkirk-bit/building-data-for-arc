"""Bounded named-rival self-audit for the eb150c0ba566 native family."""
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
_NAME = "_eb150c0ba566_audit_adapter_" + hashlib.sha256(str(_ADAPTER_PATH).encode()).hexdigest()
_SPEC = importlib.util.spec_from_file_location(_NAME, _ADAPTER_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load adjacent adapter")
_ADAPTER = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = _ADAPTER
_SPEC.loader.exec_module(_ADAPTER)

Grid = list[list[int]]
Rival = Callable[[Grid], Grid]


def _prototype(grid: Grid, color: int) -> Grid:
    left = 0 if color == 2 else 4
    return [row[left:left + 3] for row in grid[:3]]


def _stamp_policy(grid: Grid, *, shape_policy: str, clear_workspace: bool, paint_seed_color: bool = True) -> Grid:
    h, w = len(grid), len(grid[0])
    output = deepcopy(grid) if not clear_workspace else [
        row[:] if r < 4 else [0] * w for r, row in enumerate(grid)
    ]
    proto2, proto3 = _prototype(grid, 2), _prototype(grid, 3)
    for row in range(4, h):
        for col in range(w):
            seed = grid[row][col]
            if seed not in (2, 3):
                continue
            if shape_policy == "matching":
                shape_color = seed
            elif shape_policy == "opposite_shape":
                shape_color = 5 - seed
            elif shape_policy == "always_proto2":
                shape_color = 2
            elif shape_policy == "always_proto3":
                shape_color = 3
            else:
                raise ValueError(shape_policy)
            mask = proto2 if shape_color == 2 else proto3
            paint = seed if paint_seed_color else shape_color
            for dr in range(3):
                for dc in range(3):
                    if mask[dr][dc] == shape_color:
                        output[row + dr][col + dc] = paint
    return output


def _header_only(grid: Grid) -> Grid:
    width = len(grid[0])
    return [row[:] if r < 4 else [0] * width for r, row in enumerate(grid)]


def _fits(rival: Rival, pairs: list[dict]) -> bool:
    return all(rival(pair["input"]) == pair["output"] for pair in pairs)


def run(*, seeds=(0, 17, 991)) -> dict:
    findings: list[dict] = []
    survivors: list[dict] = []
    has_30x30 = False
    episodes_checked = 0

    for seed in seeds:
        for policy in ("matching", "opposite_shape"):
            episode = _ADAPTER.generate(seed, {"prototype_policy": policy}, 2, 4)
            episodes_checked += 1
            pairs = episode["train"] + episode["test"]
            has_30x30 |= any(
                len(pair["input"]) == 30 and len(pair["input"][0]) == 30
                for pair in episode["test"]
            )
            for pair in pairs:
                if pair["output"] != _ADAPTER.native_transform(pair["input"], policy):
                    findings.append({"seed": seed, "policy": policy, "finding": "python_label_mismatch"})

            rivals: dict[str, Rival] = {
                "other_declared_policy": (
                    lambda grid, p="opposite_shape" if policy == "matching" else "matching":
                    _ADAPTER.native_transform(grid, p)
                ),
                "identity": deepcopy,
                "header_only": _header_only,
                "monotone_no_clear": (
                    lambda grid, p=policy: _stamp_policy(grid, shape_policy=p, clear_workspace=False)
                ),
                "always_proto2": (
                    lambda grid: _stamp_policy(grid, shape_policy="always_proto2", clear_workspace=True)
                ),
                "always_proto3": (
                    lambda grid: _stamp_policy(grid, shape_policy="always_proto3", clear_workspace=True)
                ),
            }
            if policy == "opposite_shape":
                rivals["opposite_shape_painted_with_shape_color"] = (
                    lambda grid: _stamp_policy(
                        grid,
                        shape_policy="opposite_shape",
                        clear_workspace=True,
                        paint_seed_color=False,
                    )
                )
            for name, rival in rivals.items():
                if _fits(rival, episode["train"]):
                    survivors.append({"seed": seed, "policy": policy, "rival": name})

    return {
        "schema": "arcpuzzles-parametric-self-audit-v1",
        "task_id": "eb150c0ba566",
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
