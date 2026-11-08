#!/usr/bin/env python3
"""Isolated rule-parameter prototype for ARC task 1a92a12bac06.

The selected production generator and canonical authority remain unchanged.  This
prototype chooses two small hidden parameters once per episode:

* ``fill_side``: recolor the top or bottom part of each red vertical bar.
* ``rounding``: recolor floor(height / 2) or ceil(height / 2) cells.

The canonical/default setting is ``bottom`` + ``floor``.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge

TASK_ID = "1a92a12bac06"
PROTOTYPE_VERSION = "1.0.0"
ALLOWED_FILL_SIDES = ("bottom", "top")
ALLOWED_ROUNDINGS = ("floor", "ceil")
DEFAULT_FILL_SIDE = "bottom"
DEFAULT_ROUNDING = "floor"
ALL_SETTINGS = tuple(
    (fill_side, rounding)
    for fill_side in ALLOWED_FILL_SIDES
    for rounding in ALLOWED_ROUNDINGS
)

# Exact selected canonical program text.  program_for(bottom, floor) returns
# this byte-for-byte so the default prototype setting is the original rule.
_CANONICAL_PROGRAM = """(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((all-objs (objects g 0))
                  (red-bars (filter (lambda (o) (= 2 (obj-color o))) all-objs)))
             (reduce (lambda (grid bar)
                       (let* ((cells (obj-cells bar))
                              (rs (map first cells))
                              (r1 (min-list rs))
                              (r2 (max-list rs))
                              (bar-h (+ 1 (- r2 r1)))
                              (half-h (quotient bar-h 2))
                              (cyan-start (- r2 (- half-h 1))))
                         (reduce (lambda (gr cell)
                                   (let ((r (first cell))
                                         (c (second cell)))
                                     (if (>= r cyan-start) (set-cell gr r c 8) gr)))
                                 grid
                                 cells)))
                     g
                     red-bars)))))"""

_GENERATOR = None


def _validate_setting(fill_side: str, rounding: str) -> tuple[str, str]:
    if fill_side not in ALLOWED_FILL_SIDES:
        raise ValueError(
            f"fill_side must be one of {ALLOWED_FILL_SIDES}, got {fill_side!r}"
        )
    if rounding not in ALLOWED_ROUNDINGS:
        raise ValueError(
            f"rounding must be one of {ALLOWED_ROUNDINGS}, got {rounding!r}"
        )
    return fill_side, rounding


def choose_setting(seed: int) -> tuple[str, str]:
    """Choose one deterministic hidden setting for the whole episode."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    digest = hashlib.sha256(f"{TASK_ID}|half-bar-parameters|{seed}".encode()).digest()
    return ALL_SETTINGS[digest[0] % len(ALL_SETTINGS)]


def _load_generator():
    global _GENERATOR
    if _GENERATOR is not None:
        return _GENERATOR
    path = Path(__file__).resolve().parents[2] / "generator.py"
    spec = importlib.util.spec_from_file_location("task_1a92a12bac06_generator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load selected generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _GENERATOR = module
    return module


def _red_components(grid: list[list[int]]) -> list[set[tuple[int, int]]]:
    pending = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 2
    }
    components: list[set[tuple[int, int]]] = []
    while pending:
        start = min(pending)
        pending.remove(start)
        stack = [start]
        cells = {start}
        while stack:
            row, col = stack.pop()
            for nxt in (
                (row - 1, col),
                (row + 1, col),
                (row, col - 1),
                (row, col + 1),
            ):
                if nxt in pending:
                    pending.remove(nxt)
                    cells.add(nxt)
                    stack.append(nxt)
        components.append(cells)
    return sorted(components, key=min)


def apply_python(
    grid: list[list[int]], fill_side: str, rounding: str
) -> list[list[int]]:
    """Independent Python mirror; retained labels are still derived by Racket."""
    fill_side, rounding = _validate_setting(fill_side, rounding)
    output = copy.deepcopy(grid)
    for cells in _red_components(grid):
        rows = [row for row, _ in cells]
        top, bottom = min(rows), max(rows)
        height = bottom - top + 1
        fill_height = height // 2 if rounding == "floor" else (height + 1) // 2
        if fill_side == "bottom":
            selected = {(row, col) for row, col in cells if row >= bottom - fill_height + 1}
        else:
            selected = {(row, col) for row, col in cells if row <= top + fill_height - 1}
        for row, col in selected:
            output[row][col] = 8
    return output


def program_for(fill_side: str, rounding: str) -> str:
    """Materialize the exact Racket rule for one parameter setting."""
    fill_side, rounding = _validate_setting(fill_side, rounding)
    program = _CANONICAL_PROGRAM
    if rounding == "ceil":
        program = program.replace(
            "(half-h (quotient bar-h 2))",
            "(half-h (quotient (+ bar-h 1) 2))",
        )
    if fill_side == "top":
        program = program.replace(
            "(cyan-start (- r2 (- half-h 1))))",
            "(cyan-end (+ r1 (- half-h 1))))",
        ).replace(
            "(if (>= r cyan-start) (set-cell gr r c 8) gr)",
            "(if (<= r cyan-end) (set-cell gr r c 8) gr)",
        )
    return program


def _rule_body(program: str) -> str:
    text = program.strip()
    if not text.startswith("(rule!") or not text.endswith(")"):
        raise ValueError("prototype program must be a (rule! BODY) form")
    return text[len("(rule!") : -1].strip()


def apply_racket(
    bridge: RacketBridge, program: str, grid: list[list[int]]
) -> list[list[int]]:
    """Execute one materialized rule in the protected Racket bridge."""
    bridge.define_grid("g", grid)
    body = _rule_body(program)
    return bridge.eval_text(f"({body} g)")


def build_episode(
    seed: int,
    *,
    fill_side: str | None = None,
    rounding: str | None = None,
) -> dict[str, Any]:
    """Build a complete episode with provisional Python labels."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if fill_side is None and rounding is None:
        fill_side, rounding = choose_setting(seed)
    elif fill_side is None or rounding is None:
        raise ValueError("fill_side and rounding must be supplied together")
    fill_side, rounding = _validate_setting(fill_side, rounding)

    generator = _load_generator()
    pairs = []
    # One canonical pulse and three off-floor profiles. Every generated grid has
    # both an odd-height and an even-height bar, so both parameters are visible.
    for sample_index in range(4):
        grid = generator.generate(seed, sample_index, difficulty="medium")
        pairs.append(
            {
                "input": grid,
                "output": apply_python(grid, fill_side, rounding),
            }
        )
    return {
        "train": pairs[:3],
        "test": pairs[3],
        "program": program_for(fill_side, rounding),
        "meta": {
            "seed": seed,
            "fill_side": fill_side,
            "rounding": rounding,
            "default_fill_side": DEFAULT_FILL_SIDE,
            "default_rounding": DEFAULT_ROUNDING,
            "sample_indices": [0, 1, 2, 3],
            "prototype_version": PROTOTYPE_VERSION,
        },
    }


def parameter_rival_findings(episode: dict[str, Any]) -> list[str]:
    """Check every other allowed setting against demonstrations and query."""
    actual = (
        episode["meta"]["fill_side"],
        episode["meta"]["rounding"],
    )
    findings: list[str] = []
    for rival in ALL_SETTINGS:
        if rival == actual:
            continue
        differing_demos = [
            index
            for index, pair in enumerate(episode["train"])
            if apply_python(pair["input"], *rival) != pair["output"]
        ]
        if not differing_demos:
            findings.append(f"rival setting {rival!r} fits every demonstration")
        if apply_python(episode["test"]["input"], *rival) == episode["test"]["output"]:
            findings.append(f"query does not distinguish rival setting {rival!r}")
    return findings


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _sha256_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return _sha256_text(payload)


def _find_seed_for(setting: tuple[str, str], start: int, used: set[int]) -> int:
    seed = start
    while seed in used or choose_setting(seed) != setting:
        seed += 1
    return seed


def _distinguishing_demo_indices(
    episode: dict[str, Any], rival: tuple[str, str]
) -> list[int]:
    return [
        index
        for index, pair in enumerate(episode["train"])
        if apply_python(pair["input"], *rival) != pair["output"]
    ]


def materialize(out_dir: Path, seed_start: int = 9100) -> dict[str, Any]:
    """Execute all settings with Racket and retain hidden/public evidence."""
    out_dir.mkdir(parents=True, exist_ok=True)
    public_dir = out_dir / "public"
    public_dir.mkdir(parents=True, exist_ok=True)
    source_path = Path(__file__).resolve()
    generator_path = source_path.parents[2] / "generator.py"

    used: set[int] = set()
    episodes = []
    bridge = RacketBridge(max_calls_before_restart=128)
    try:
        for setting_index, setting in enumerate(ALL_SETTINGS):
            seed = _find_seed_for(setting, seed_start + setting_index, used)
            used.add(seed)
            episode = build_episode(seed)
            assert (
                episode["meta"]["fill_side"],
                episode["meta"]["rounding"],
            ) == setting

            for pair in episode["train"]:
                pair["output"] = apply_racket(bridge, episode["program"], pair["input"])
                assert pair["output"] == apply_python(pair["input"], *setting)
            episode["test"]["output"] = apply_racket(
                bridge, episode["program"], episode["test"]["input"]
            )
            assert episode["test"]["output"] == apply_python(
                episode["test"]["input"], *setting
            )

            findings = parameter_rival_findings(episode)
            if findings:
                raise AssertionError(findings)
            rival_witnesses = {
                f"{rival[0]}+{rival[1]}": _distinguishing_demo_indices(episode, rival)
                for rival in ALL_SETTINGS
                if rival != setting
            }

            public = {
                "schema": "1a92a12bac06-parametric-public-v1",
                "train": copy.deepcopy(episode["train"]),
                "test": {"input": copy.deepcopy(episode["test"]["input"])},
            }
            public_path = public_dir / f"challenge_seed_{seed}.json"
            public_path.write_text(json.dumps(public, indent=2) + "\n")
            episodes.append(
                {
                    **episode,
                    "setting": {
                        "fill_side": setting[0],
                        "rounding": setting[1],
                    },
                    "program_sha256": _sha256_text(episode["program"]),
                    "parameter_rival_findings": findings,
                    "distinguishing_demo_indices": rival_witnesses,
                    "public_challenge": str(public_path.relative_to(out_dir)),
                    "public_challenge_sha256": _sha256_json(public),
                }
            )
    finally:
        bridge.shutdown()

    report = {
        "schema": "1a92a12bac06-parametric-evidence-v1",
        "status": "prototype",
        "task_id": TASK_ID,
        "parameters": [
            {
                "name": "fill_side",
                "allowed_values": list(ALLOWED_FILL_SIDES),
                "original_default": DEFAULT_FILL_SIDE,
                "meaning": "which end of each red bar supplies the recolored half",
            },
            {
                "name": "rounding",
                "allowed_values": list(ALLOWED_ROUNDINGS),
                "original_default": DEFAULT_ROUNDING,
                "meaning": "floor or ceil when half the bar height is non-integral",
            },
        ],
        "input_constraints": (
            "Inputs retain the selected task's separated red vertical bars. Every pair "
            "contains odd and even bar heights; top/bottom selection and floor/ceil "
            "therefore change observable output cells."
        ),
        "invariant_reasoning": [
            "find each 4-connected red object",
            "measure its vertical extent",
            "compute approximately half its height",
            "recolor that many cells cyan from the episode-selected end",
        ],
        "canonical_default": {
            "fill_side": DEFAULT_FILL_SIDE,
            "rounding": DEFAULT_ROUNDING,
            "program_sha256": _sha256_text(_CANONICAL_PROGRAM),
        },
        "prototype_source": str(source_path),
        "prototype_source_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
        "selected_generator_sha256": hashlib.sha256(generator_path.read_bytes()).hexdigest(),
        "episodes": episodes,
        "run_command": [
            "python3",
            "review.py",
            "run",
            "python3",
            "generators/1a92a12bac06/workspace/parametric/prototype.py",
            "--out",
            "../checks/parametric",
        ],
        "limitations": [
            "Prototype only; no setting is wired into production generation or approved as canonical authority.",
            "Evidence covers one deterministic episode per allowed setting and the three declared parameter rivals, not all seeds or all plausible rules.",
            "The family remains restricted to separated one-column red bars; arbitrary red shapes are outside this prototype.",
        ],
    }
    (out_dir / "evidence.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed-start", type=int, default=9100)
    args = parser.parse_args()
    report = materialize(args.out, args.seed_start)
    print(
        json.dumps(
            {
                "status": report["status"],
                "episodes": [
                    {
                        "seed": row["meta"]["seed"],
                        "setting": row["setting"],
                        "program_sha256": row["program_sha256"],
                        "distinguishing_demo_indices": row[
                            "distinguishing_demo_indices"
                        ],
                    }
                    for row in report["episodes"]
                ],
                "evidence": str(args.out / "evidence.json"),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
