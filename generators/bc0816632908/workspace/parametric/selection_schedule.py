#!/usr/bin/env python3
"""Task-local period/phase rule prototype for ARC task bc0816632908.

The selected production generator and canonical rule remain unchanged.  This
prototype varies only which positions in the left-to-right component order are
recolored:

    component_index % period == phase

The setting is selected once per episode and is shared by all demonstrations
and the query.  The canonical default is ``period=3, phase=0``.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any, Iterable, Sequence

from reviewer_support import canonical_path, find_root, load_selected_generator


TASK_ID = "bc0816632908"
ALLOWED_SETTINGS = ((2, 0), (2, 1), (3, 0), (3, 1))
DEFAULT_SETTING = (3, 0)
DEMO_INDICES = (0, 1, 2)
QUERY_INDEX = 3
DIFFICULTY = "medium"
_NEIGHBORS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def normalized_hash(source: str) -> str:
    """Return the packet's 12-hex whitespace-normalized rule hash."""
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _digest(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _validate_setting(period: Any, phase: Any) -> tuple[int, int]:
    if type(period) is not int or type(phase) is not int:
        raise TypeError("period and phase must be literal integers")
    setting = (period, phase)
    if setting not in ALLOWED_SETTINGS:
        allowed = ", ".join(f"({p},{q})" for p, q in ALLOWED_SETTINGS)
        raise ValueError(f"unsupported (period, phase)={setting}; allowed: {allowed}")
    return setting


def _canonical_source(*, root: Path) -> str:
    with canonical_path(root).open(encoding="utf-8") as handle:
        for raw in handle:
            if not raw.strip():
                continue
            row = json.loads(raw)
            if row.get("task_id") == TASK_ID:
                source = row.get("program_solution")
                if not source:
                    raise ValueError(f"{TASK_ID}: canonical rule is missing")
                return str(source)
    raise FileNotFoundError(f"{TASK_ID}: canonical task row not found")


def racket_source(*, period: int, phase: int, root: Path | str) -> str:
    """Materialize one complete Racket rule for the bounded setting."""
    period, phase = _validate_setting(period, phase)
    canonical = _canonical_source(root=Path(root))
    if (period, phase) == DEFAULT_SETTING:
        return canonical

    needle = "(zero? (remainder i 3))"
    if canonical.count(needle) != 1:
        raise ValueError("canonical selection condition changed unexpectedly")
    condition = (
        f"(zero? (remainder i {period}))"
        if phase == 0
        else f"(= (remainder i {period}) {phase})"
    )
    return canonical.replace(needle, condition, 1)


def _coerce_grid(grid: Any) -> list[list[int]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must be a non-empty row sequence")
    if not all(isinstance(row, (list, tuple)) for row in grid):
        raise ValueError("every row must be a sequence")
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        raise ValueError("grid must be non-empty and rectangular")
    out: list[list[int]] = []
    for row in grid:
        converted: list[int] = []
        for value in row:
            if type(value) is not int or not 0 <= value <= 9:
                raise ValueError(f"invalid ARC cell {value!r}")
            converted.append(value)
        out.append(converted)
    return out


def _foreground_components(grid: Sequence[Sequence[int]]) -> list[tuple[tuple[int, int], ...]]:
    """Match ``objects g 2`` for the prototype's generated two-color inputs."""
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[tuple[tuple[int, int], ...]] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 2 or (row, col) in seen:
                continue
            color = grid[row][col]
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                current = stack.pop()
                cells.append(current)
                cr, cc = current
                for dr, dc in _NEIGHBORS:
                    nr, nc = cr + dr, cc + dc
                    nxt = (nr, nc)
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and nxt not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add(nxt)
                        stack.append(nxt)
            components.append(tuple(sorted(cells)))
    return sorted(
        components,
        key=lambda cells: (
            min(col for _row, col in cells),
            min(row for row, _col in cells),
        ),
    )


def python_output(grid: Any, *, period: int, phase: int) -> list[list[int]]:
    """Independent Python mirror for tests and prototype evidence."""
    period, phase = _validate_setting(period, phase)
    converted = _coerce_grid(grid)
    output = [row[:] for row in converted]
    for index, component in enumerate(_foreground_components(converted)):
        if index % period == phase:
            for row, col in component:
                output[row][col] = 4
    return output


def _racket_literal(value: Any) -> str:
    if isinstance(value, list):
        return "(" + " ".join(_racket_literal(item) for item in value) + ")"
    if type(value) is not int or not 0 <= value <= 9:
        raise ValueError(f"not an ARC literal: {value!r}")
    return str(value)


def _callable_racket_source(source: str) -> str:
    stripped = source.strip()
    prefix = "(rule! "
    if not stripped.startswith(prefix) or not stripped.endswith(")"):
        raise ValueError("expected a plain (rule! <lambda>) program")
    callable_source = stripped[len(prefix) : -1].strip()
    if not callable_source.startswith("(lambda "):
        raise ValueError("prototype rule body must be a lambda")
    return callable_source


def racket_outputs(source: str, grids: list[list[list[int]]]) -> list[list[list[int]]]:
    """Execute the exact materialized rule through the bundled Racket bridge."""
    from arc_repl.racket_bridge import RacketBridge

    callable_source = _callable_racket_source(source)
    with RacketBridge() as bridge:
        bridge.eval_text(f"(define prototype-rule {callable_source})")
        result = bridge.eval_text(f"(map prototype-rule '{_racket_literal(grids)})")
    if not isinstance(result, list) or len(result) != len(grids):
        raise RuntimeError("unexpected Racket result shape")
    return result


def _episode_inputs(module: Any, *, seed: int) -> list[list[list[int]]]:
    return [
        module.generate(seed, index, difficulty=DIFFICULTY)
        for index in (*DEMO_INDICES, QUERY_INDEX)
    ]


def _setting_name(setting: tuple[int, int]) -> str:
    return f"period{setting[0]}_phase{setting[1]}"


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _manifest(root: Path) -> dict[str, Any]:
    rows = []
    for path in sorted(p for p in root.rglob("*") if p.is_file() and p.name != "manifest.json"):
        rows.append(
            {
                "path": path.relative_to(root).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
    return {"schema": "bc0816632908-parametric-manifest-v1", "files": rows}


def build_evidence(*, root: Path, out: Path, seeds: dict[tuple[int, int], int]) -> dict[str, Any]:
    module, source_path, source_sha256 = load_selected_generator(TASK_ID, root=root)
    sources = {
        setting: racket_source(period=setting[0], phase=setting[1], root=root)
        for setting in ALLOWED_SETTINGS
    }
    if normalized_hash(sources[DEFAULT_SETTING]) != module.RULE_HASH:
        raise AssertionError("canonical default no longer matches selected RULE_HASH")

    workspace = Path(__file__).resolve().parent
    rule_dir = workspace / "racket"
    rule_dir.mkdir(parents=True, exist_ok=True)
    for setting, source in sources.items():
        (rule_dir / f"{_setting_name(setting)}.rkt").write_text(source, encoding="utf-8")

    private_episodes: dict[str, Any] = {}
    public_episodes: dict[str, Any] = {}
    distinction: dict[str, Any] = {}

    for setting in ALLOWED_SETTINGS:
        seed = seeds[setting]
        inputs = _episode_inputs(module, seed=seed)
        source = sources[setting]
        racket = racket_outputs(source, inputs)
        python = [
            python_output(grid, period=setting[0], phase=setting[1])
            for grid in inputs
        ]
        if racket != python:
            raise AssertionError(f"{setting}: Python/Racket output mismatch")

        rival_rows: dict[str, Any] = {}
        for rival in ALLOWED_SETTINGS:
            if rival == setting:
                continue
            rival_outputs = [
                python_output(grid, period=rival[0], phase=rival[1])
                for grid in inputs
            ]
            differing_demos = [
                index
                for index, official, predicted in zip(DEMO_INDICES, racket[:-1], rival_outputs[:-1])
                if official != predicted
            ]
            query_differs = racket[-1] != rival_outputs[-1]
            if not differing_demos:
                raise AssertionError(f"{setting}: demonstrations do not refute rival {rival}")
            if not query_differs:
                raise AssertionError(f"{setting}: query does not distinguish rival {rival}")
            rival_rows[_setting_name(rival)] = {
                "differing_demonstration_indices": differing_demos,
                "query_differs": query_differs,
            }

        name = _setting_name(setting)
        demonstrations = [
            {
                "sample_index": index,
                "input": grid,
                "output": output,
                "input_sha256": _digest(grid),
                "output_sha256": _digest(output),
            }
            for index, grid, output in zip(DEMO_INDICES, inputs[:-1], racket[:-1])
        ]
        query = {
            "sample_index": QUERY_INDEX,
            "input": inputs[-1],
            "output": racket[-1],
            "input_sha256": _digest(inputs[-1]),
            "output_sha256": _digest(racket[-1]),
        }
        private_episodes[name] = {
            "setting": {"period": setting[0], "phase": setting[1]},
            "seed": seed,
            "difficulty": DIFFICULTY,
            "racket_rule_hash": normalized_hash(source),
            "racket_rule_sha256": hashlib.sha256(source.encode()).hexdigest(),
            "demonstrations": demonstrations,
            "query": query,
        }
        public_episodes[name] = {
            "train": [
                {"input": row["input"], "output": row["output"]}
                for row in demonstrations
            ],
            "test": [{"input": query["input"]}],
        }
        distinction[name] = rival_rows

    workspace_examples = {
        "schema": "bc0816632908-parametric-public-episodes-v1",
        "episodes": public_episodes,
        "note": "Query outputs and hidden period/phase settings are intentionally omitted.",
    }
    _write_json(workspace / "examples.json", workspace_examples)

    out.mkdir(parents=True, exist_ok=True)
    for setting, source in sources.items():
        (out / "rules" / f"{_setting_name(setting)}.rkt").parent.mkdir(parents=True, exist_ok=True)
        (out / "rules" / f"{_setting_name(setting)}.rkt").write_text(source, encoding="utf-8")
    _write_json(out / "private" / "episodes.json", private_episodes)
    _write_json(out / "public" / "episodes.json", workspace_examples)

    summary = {
        "schema": "bc0816632908-parametric-evidence-v1",
        "status": "pass",
        "task_id": TASK_ID,
        "prototype_status": "proposed",
        "parameter_contract": {
            "period": {"allowed": [2, 3], "default": 3},
            "phase": {"allowed": [0, 1], "default": 0},
            "allowed_joint_settings": [
                {"period": period, "phase": phase}
                for period, phase in ALLOWED_SETTINGS
            ],
            "selection_rule": "component_index % period == phase",
            "chosen_once_per_episode": True,
        },
        "canonical_default": {
            "setting": {"period": 3, "phase": 0},
            "normalized_rule_hash": normalized_hash(sources[DEFAULT_SETTING]),
            "selected_rule_hash": module.RULE_HASH,
            "exact_canonical_text": sources[DEFAULT_SETTING] == _canonical_source(root=root),
        },
        "selected_generator": {
            "path": str(source_path),
            "sha256": source_sha256,
        },
        "episodes": {
            name: {
                "seed": row["seed"],
                "setting": row["setting"],
                "rule_sha256": row["racket_rule_sha256"],
                "demonstration_count": len(row["demonstrations"]),
                "query_input_sha256": row["query"]["input_sha256"],
            }
            for name, row in private_episodes.items()
        },
        "rival_distinction": distinction,
        "command": {
            "cwd": os.getcwd(),
            "argv": sys.argv,
        },
        "limitations": [
            "This prototype does not modify the selected production generator or canonical rule.",
            "Evidence covers four bounded settings and four complete episodes, not every seed.",
            "The input sampler remains the selected generator; only the executed component-selection schedule varies.",
            "Public challenge files omit hidden settings and query answers by design.",
        ],
    }
    _write_json(out / "summary.json", summary)
    _write_json(out / "manifest.json", _manifest(out))
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed-base", type=int, default=8730)
    args = parser.parse_args(argv)
    if args.seed_base < 0:
        raise ValueError("seed-base must be non-negative")
    root = find_root(__file__)
    seeds = {
        setting: args.seed_base + index
        for index, setting in enumerate(ALLOWED_SETTINGS)
    }
    summary = build_evidence(root=root, out=args.out, seeds=seeds)
    print(
        json.dumps(
            {
                "status": summary["status"],
                "out": str(args.out),
                "settings": list(summary["episodes"]),
                "canonical_rule_hash": summary["canonical_default"]["normalized_rule_hash"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
