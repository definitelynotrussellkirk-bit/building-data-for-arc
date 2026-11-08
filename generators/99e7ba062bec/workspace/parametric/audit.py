"""Bounded adversarial self-audit for the transform-application family."""
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
_NAME = "_audit_adapter_99_" + hashlib.sha256(str(_ADAPTER_PATH).encode()).hexdigest()
_SPEC = importlib.util.spec_from_file_location(_NAME, _ADAPTER_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError("cannot load adjacent adapter")
_ADAPTER = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = _ADAPTER
_SPEC.loader.exec_module(_ADAPTER)

Grid = list[list[int]]
Rival = Callable[[Grid], Grid]
_CODES = tuple(range(1, 8))
_INVERSE = {2: 4, 4: 2}


def _apply(grid: Grid, code: int) -> Grid:
    if code == 1:
        return [row[:] for row in grid]
    if code == 2:
        return [list(column) for column in zip(*grid[::-1])]
    if code == 3:
        return [row[::-1] for row in grid[::-1]]
    if code == 4:
        return [list(column) for column in zip(*grid)][::-1]
    if code == 5:
        return [row[::-1] for row in grid]
    if code == 6:
        return [row[:] for row in grid[::-1]]
    if code == 7:
        return [list(column) for column in zip(*grid)]
    raise ValueError(f"unknown transform code: {code!r}")


def _crop(grid: Grid) -> Grid:
    cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]
    if not cells:
        return []
    row0 = min(row for row, _ in cells)
    row1 = max(row for row, _ in cells)
    col0 = min(col for _, col in cells)
    col1 = max(col for _, col in cells)
    return [values[col0 : col1 + 1] for values in grid[row0 : row1 + 1]]


def _bands(grid: Grid) -> list[tuple[int, int]]:
    bands: list[tuple[int, int]] = []
    column = 0
    width = len(grid[0])
    while column < width:
        while column < width and all(row[column] == 0 for row in grid):
            column += 1
        if column >= width:
            break
        start = column
        while column < width and any(row[column] != 0 for row in grid):
            column += 1
        bands.append((start, column))
    return bands


def _panels(grid: Grid) -> list[Grid]:
    return [_crop([row[start:stop] for row in grid]) for start, stop in _bands(grid)]


def _mask(grid: Grid) -> Grid:
    return [[int(value != 0) for value in row] for row in grid]


def _infer(grid: Grid) -> int:
    panels = _panels(grid)
    if len(panels) != 3:
        raise ValueError("expected exactly three panels")
    a, b, _ = panels
    matches = [
        code
        for code in _CODES
        if _crop(_apply(_mask(a), code)) == _mask(b)
    ]
    if len(matches) != 1:
        raise ValueError(f"expected one A-to-B transform, got {matches!r}")
    return matches[0]


def _solve(grid: Grid, application: str) -> Grid:
    panels = _panels(grid)
    code = _infer(grid)
    if application == "inverse":
        code = _INVERSE.get(code, code)
    return _crop(_apply(panels[2], code))


def _fixed(code: int) -> Rival:
    return lambda grid: _crop(_apply(_panels(grid)[2], code))


def _copy_panel(index: int) -> Rival:
    return lambda grid: deepcopy(_panels(grid)[index])


def _recolor_ab(base: Rival) -> Rival:
    def solve(grid: Grid) -> Grid:
        panels = _panels(grid)
        ab_color = next(value for row in panels[0] for value in row if value)
        return [[ab_color if value else 0 for value in row] for row in base(grid)]

    return solve


def _fits(rival: Rival, pairs: list[dict]) -> bool:
    return all(rival(pair["input"]) == pair["output"] for pair in pairs)


def run(*, seeds=(0, 17, 991)) -> dict:
    findings: list[dict] = []
    survivors: list[dict] = []
    has_30x30 = False
    episodes_checked = 0

    for seed in seeds:
        generated: dict[str, dict] = {}
        for application in ("forward", "inverse"):
            episode = _ADAPTER.generate(seed, {"application": application}, 2, 4)
            generated[application] = episode
            episodes_checked += 1
            all_pairs = episode["train"] + episode["test"]
            has_30x30 = has_30x30 or any(
                len(pair["input"]) == 30 and len(pair["input"][0]) == 30
                for pair in episode["test"]
            )

            if not all(_solve(pair["input"], application) == pair["output"] for pair in all_pairs):
                findings.append(
                    {"seed": seed, "application": application, "finding": "label_mismatch"}
                )

            inferred = [_infer(pair["input"]) for pair in episode["train"]]
            if inferred != [2, 4]:
                findings.append(
                    {
                        "seed": seed,
                        "application": application,
                        "finding": "minimum_demos_do_not_expose_quarter_turn_pair",
                        "observed": inferred,
                    }
                )

            rivals: dict[str, Rival] = {
                "forward": lambda grid: _solve(grid, "forward"),
                "inverse": lambda grid: _solve(grid, "inverse"),
                "copy_A": _copy_panel(0),
                "copy_B": _copy_panel(1),
                "copy_C": _copy_panel(2),
                "forward_recolored_like_AB": _recolor_ab(lambda grid: _solve(grid, "forward")),
                "inverse_recolored_like_AB": _recolor_ab(lambda grid: _solve(grid, "inverse")),
            }
            rivals.update({f"fixed_transform_{code}": _fixed(code) for code in _CODES})
            for name, rival in rivals.items():
                if name == application:
                    continue
                if _fits(rival, episode["train"]):
                    survivors.append(
                        {"seed": seed, "application": application, "rival": name}
                    )

            # Structural checks against accidental teaching shortcuts.
            for pair_index, pair in enumerate(all_pairs):
                panels = _panels(pair["input"])
                if len(panels) != 3:
                    findings.append(
                        {
                            "seed": seed,
                            "application": application,
                            "pair": pair_index,
                            "finding": "panel_count",
                        }
                    )
                    continue
                a_color = next(value for row in panels[0] for value in row if value)
                c_color = next(value for row in panels[2] for value in row if value)
                if a_color == c_color:
                    findings.append(
                        {
                            "seed": seed,
                            "application": application,
                            "pair": pair_index,
                            "finding": "shared_AB_and_C_color",
                        }
                    )
                if _mask(panels[2]) in [_crop(_apply(_mask(panels[0]), code)) for code in _CODES]:
                    findings.append(
                        {
                            "seed": seed,
                            "application": application,
                            "pair": pair_index,
                            "finding": "C_in_A_orbit",
                        }
                    )

        if [pair["input"] for pair in generated["forward"]["train"] + generated["forward"]["test"]] != [
            pair["input"] for pair in generated["inverse"]["train"] + generated["inverse"]["test"]
        ]:
            findings.append({"seed": seed, "finding": "settings_change_inputs"})

    return {
        "schema": "arcpuzzles-parametric-self-audit-v1",
        "task_id": "99e7ba062bec",
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
