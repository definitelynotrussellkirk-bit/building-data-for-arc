#!/usr/bin/env python3
"""Proposed episode-level variants for ARC family 760b3cac.

The canonical production rule remains untouched.  This prototype varies two
small semantics once per episode:

* ``copy_style``: horizontally mirror the cyan support (canonical) or translate
  it without reversing columns;
* ``gap``: place the copy immediately beside the support (canonical) or leave
  one blank column.

Racket execution is the label authority.  The Python transform is retained only
as an independent assertion and authoring aid.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import random
import sys
from pathlib import Path
from typing import Any, Iterable

from arc_repl.racket_bridge import RacketBridge, racket_runtime_status

TASK_ID = "0ed4fa8c0b40"
SOURCE_TASK_ID = "760b3cac"
PROTOTYPE_VERSION = "1.0.0"
ALLOWED_COPY_STYLES = ("mirror", "translate")
ALLOWED_GAPS = (0, 1)
DEFAULT_PARAMETERS = {"copy_style": "mirror", "gap": 0}
SETTINGS = tuple(
    (copy_style, gap)
    for copy_style in ALLOWED_COPY_STYLES
    for gap in ALLOWED_GAPS
)

ROOT = Path(__file__).resolve().parent
TASK_ROOT = ROOT.parents[1]
REPO_ROOT = ROOT.parents[3]
GENERATOR_PATH = TASK_ROOT / "generator.py"
RULE_DIR = ROOT / "rules"


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_text(text: str) -> str:
    return _sha256_bytes(text.encode("utf-8"))


def _json_sha256(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return _sha256_bytes(payload)


def validate_parameters(copy_style: str, gap: int) -> tuple[str, int]:
    if type(copy_style) is not str:
        raise TypeError("copy_style must be a literal string")
    if copy_style not in ALLOWED_COPY_STYLES:
        raise ValueError(f"copy_style must be one of {ALLOWED_COPY_STYLES}")
    if type(gap) is not int:
        raise TypeError("gap must be a literal Python integer")
    if gap not in ALLOWED_GAPS:
        raise ValueError(f"gap must be one of {ALLOWED_GAPS}")
    return copy_style, gap


def _validate_seed(seed: int) -> int:
    if type(seed) is not int:
        raise TypeError("seed must be a literal Python integer")
    return seed


def parameters_for_seed(seed: int) -> dict[str, Any]:
    """Choose one hidden setting for the entire episode."""
    _validate_seed(seed)
    copy_style, gap = random.Random(seed).choice(SETTINGS)
    return {"copy_style": copy_style, "gap": gap}


def setting_id(copy_style: str, gap: int) -> str:
    style, distance = validate_parameters(copy_style, gap)
    return f"{style}-gap{distance}"


def _arrow_cells(top: int, center: int, direction: int) -> set[tuple[int, int]]:
    return {
        (top, center + direction),
        (top + 1, center - 1),
        (top + 1, center),
        (top + 1, center + 1),
        (top + 2, center),
    }


def _authored_grid(direction: int, mask: Iterable[tuple[int, int]], *, height: int, width: int) -> list[list[int]]:
    if direction not in (-1, 1):
        raise ValueError("direction must be -1 or 1")
    if height < 8 or width < 17:
        raise ValueError("prototype fixtures require at least an 8x17 grid")
    grid = [[0 for _ in range(width)] for _ in range(height)]
    arrow_top = 0
    arrow_center = width // 2
    for row, column in _arrow_cells(arrow_top, arrow_center, direction):
        grid[row][column] = 4

    cyan_top = height - 4
    cyan_left = 2 if direction == 1 else width - 5
    for row, column in mask:
        if not (0 <= row < 3 and 0 <= column < 3):
            raise ValueError("cyan mask must fit in a 3x3 local box")
        grid[cyan_top + row][cyan_left + column] = 8
    return grid


def episode_inputs(seed: int) -> list[list[list[int]]]:
    """Return three demonstrations and one query, independent of hidden parameters."""
    _validate_seed(seed)
    specifications = [
        (1, {(0, 0), (0, 1), (1, 1), (2, 1), (2, 2)}, 8, 17),
        (-1, {(0, 2), (1, 0), (1, 1), (1, 2), (2, 0)}, 9, 18),
        (1, {(0, 0), (1, 0), (1, 1), (2, 0), (2, 2)}, 10, 19),
        (-1, {(0, 1), (0, 2), (1, 1), (2, 0), (2, 1)}, 8, 20),
    ]
    rng = random.Random(seed ^ 0x760B3CAC)
    rng.shuffle(specifications)
    return [
        _authored_grid(direction, mask, height=height, width=width)
        for direction, mask, height, width in specifications
    ]


def _decode_scene(grid: list[list[int]]) -> dict[str, Any]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("grid must be a non-empty rectangular list")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid cells must be integer ARC colors 0..9")

    yellows = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 4}
    matches: list[tuple[int, int, int]] = []
    for top in range(len(grid) - 2):
        for center in range(1, width - 1):
            for direction in (-1, 1):
                if _arrow_cells(top, center, direction) == yellows:
                    matches.append((top, center, direction))
    if len(matches) != 1:
        raise ValueError("grid must contain exactly one five-cell horizontal arrow")

    cyans = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 8]
    if not cyans:
        raise ValueError("grid must contain cyan cells")
    columns = [column for _, column in cyans]
    return {
        "direction": matches[0][2],
        "cyans": cyans,
        "cyan_left": min(columns),
        "cyan_right": max(columns),
        "cyan_width": max(columns) - min(columns) + 1,
    }


def python_transform(grid: list[list[int]], copy_style: str, gap: int) -> list[list[int]]:
    """Independent assertion mirror for one materialized parameter setting."""
    style, distance = validate_parameters(copy_style, gap)
    scene = _decode_scene(grid)
    output = copy.deepcopy(grid)
    width = len(grid[0])
    direction = scene["direction"]
    for row, column in scene["cyans"]:
        if style == "mirror":
            if direction == 1:
                target = 2 * scene["cyan_right"] + 1 + distance - column
            else:
                target = 2 * scene["cyan_left"] - 1 - distance - column
        elif direction == 1:
            target = column + scene["cyan_width"] + distance
        else:
            target = column - scene["cyan_width"] - distance
        if not 0 <= target < width:
            raise ValueError("parameterized cyan copy falls outside the grid")
        output[row][target] = 8
    return output


def racket_source(copy_style: str, gap: int) -> str:
    """Return one exact complete ``(rule! ...)`` program."""
    style, distance = validate_parameters(copy_style, gap)
    if style == "mirror":
        right_target = f"(+ cc-max 1 {distance} (- cc-max c))"
        left_target = f"(- cc-min 1 {distance} (- c cc-min))"
    else:
        right_target = f"(+ c cyan-width {distance})"
        left_target = f"(- c cyan-width {distance})"
    return f'''(rule! (lambda (g)
         (let* ((w (cols g))
                (cyans (find-color g 8))
                (yellows (find-color g 4))
                (yr-min (min-of fst yellows))
                (pointer-col (snd (find (lambda (p) (= (fst p) yr-min)) yellows)))
                (yc-center (quotient (+ (min-of snd yellows) (max-of snd yellows)) 2))
                (go-right (> pointer-col yc-center))
                (cc-min (min-of snd cyans))
                (cc-max (max-of snd cyans))
                (cyan-width (+ 1 (- cc-max cc-min))))
           (reduce (lambda (acc p)
                     (let* ((r (fst p))
                            (c (snd p))
                            (nc (if go-right
                                    {right_target}
                                    {left_target})))
                       (if (and (>= nc 0) (< nc w))
                           (set-cell acc r nc 8)
                           acc)))
                   g
                   cyans))))'''


def _rule_callable(source: str) -> str:
    text = source.strip()
    prefix = "(rule! "
    if not text.startswith(prefix) or not text.endswith(")"):
        raise ValueError("expected exactly one (rule! <lambda>) program")
    body = text[len(prefix):-1].strip()
    if not body.startswith("(lambda (g)"):
        raise ValueError("prototype rule must be a lambda over g")
    return body


def _racket_literal(value: Any) -> str:
    if isinstance(value, list):
        return "(" + " ".join(_racket_literal(item) for item in value) + ")"
    if type(value) is not int or not 0 <= value <= 9:
        raise ValueError(f"not an ARC grid literal: {value!r}")
    return str(value)


def execute_rule(source: str, grid: list[list[int]], *, bridge: RacketBridge | None = None) -> list[list[int]]:
    expression = f"({_rule_callable(source)} '{_racket_literal(grid)})"
    if bridge is None:
        with RacketBridge(timeout=30) as owned:
            result = owned.eval_text(expression)
    else:
        result = bridge.eval_text(expression)
    if not isinstance(result, list) or not result or not all(isinstance(row, list) for row in result):
        raise RuntimeError(f"Racket returned a non-grid result: {result!r}")
    return result


def materialize_rules(output_root: Path | str = ROOT) -> dict[str, dict[str, str]]:
    root = Path(output_root)
    rule_dir = root / "rules"
    rule_dir.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, dict[str, str]] = {}
    for copy_style, gap in SETTINGS:
        identifier = setting_id(copy_style, gap)
        source = racket_source(copy_style, gap)
        path = rule_dir / f"{identifier}.rkt"
        path.write_text(source, encoding="utf-8")
        manifest[identifier] = {
            "relative_path": str(path.relative_to(root)),
            "sha256": _sha256_text(source),
        }
    return manifest


def _normalize_parameters(parameters: dict[str, Any] | None, seed: int) -> dict[str, Any]:
    chosen = parameters_for_seed(seed) if parameters is None else dict(parameters)
    if set(chosen) != {"copy_style", "gap"}:
        raise ValueError("parameters must contain exactly copy_style and gap")
    copy_style, gap = validate_parameters(chosen["copy_style"], chosen["gap"])
    return {"copy_style": copy_style, "gap": gap}


def build_episode(
    *,
    seed: int,
    parameters: dict[str, Any] | None = None,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    """Build three labelled demonstrations and one labelled query using Racket."""
    _validate_seed(seed)
    chosen = _normalize_parameters(parameters, seed)
    source = racket_source(chosen["copy_style"], chosen["gap"])
    grids = episode_inputs(seed)

    def build(active: RacketBridge) -> list[dict[str, Any]]:
        return [
            {
                "input": copy.deepcopy(grid),
                "output": execute_rule(source, grid, bridge=active),
            }
            for grid in grids
        ]

    if bridge is None:
        with RacketBridge(timeout=30) as owned:
            pairs = build(owned)
    else:
        pairs = build(bridge)
    return {
        "schema": "arcpuzzles-parametric-copy-episode-v1",
        "status": "prototype",
        "prototype_version": PROTOTYPE_VERSION,
        "task_id": TASK_ID,
        "source_task_id": SOURCE_TASK_ID,
        "seed": seed,
        "parameter": chosen,
        "racket_sha256": _sha256_text(source),
        "train": pairs[:3],
        "test": pairs[3:],
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Return labelled demonstrations and an unlabelled query only."""
    return {
        "schema": "arcpuzzles-parametric-copy-public-v1",
        "train": copy.deepcopy(episode["train"]),
        "test": [{"input": copy.deepcopy(pair["input"])} for pair in episode["test"]],
    }


def _load_selected_generator_sha() -> str:
    return _sha256_bytes(GENERATOR_PATH.read_bytes())


def build_evidence(*, seed: int, output_root: Path | str = ROOT) -> dict[str, Any]:
    """Execute every setting and retain bounded discrimination evidence."""
    _validate_seed(seed)
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    rule_manifest = materialize_rules(root)
    settings_report: dict[str, Any] = {}
    inputs = episode_inputs(seed)

    with RacketBridge(timeout=30) as bridge:
        runtime_identity = bridge.runtime_identity
        all_outputs: dict[str, list[list[list[int]]]] = {}
        for copy_style, gap in SETTINGS:
            identifier = setting_id(copy_style, gap)
            source = racket_source(copy_style, gap)
            all_outputs[identifier] = [
                execute_rule(source, grid, bridge=bridge)
                for grid in inputs
            ]

        for copy_style, gap in SETTINGS:
            identifier = setting_id(copy_style, gap)
            source = racket_source(copy_style, gap)
            outputs = all_outputs[identifier]
            python_outputs = [python_transform(grid, copy_style, gap) for grid in inputs]
            pairs = [
                {"input": copy.deepcopy(grid), "output": copy.deepcopy(output)}
                for grid, output in zip(inputs, outputs, strict=True)
            ]
            episode = {
                "schema": "arcpuzzles-parametric-copy-episode-v1",
                "status": "prototype",
                "prototype_version": PROTOTYPE_VERSION,
                "task_id": TASK_ID,
                "source_task_id": SOURCE_TASK_ID,
                "seed": seed,
                "parameter": {"copy_style": copy_style, "gap": gap},
                "racket_sha256": _sha256_text(source),
                "train": pairs[:3],
                "test": pairs[3:],
            }
            rival_witnesses: dict[str, Any] = {}
            for rival_style, rival_gap in SETTINGS:
                rival_id = setting_id(rival_style, rival_gap)
                if rival_id == identifier:
                    continue
                differing = [
                    index
                    for index in range(3)
                    if all_outputs[rival_id][index] != outputs[index]
                ]
                rival_witnesses[rival_id] = {
                    "distinguished": bool(differing),
                    "first_differing_demo_index": differing[0] if differing else None,
                    "chosen_output_sha256": _json_sha256(outputs[differing[0]]) if differing else None,
                    "rival_output_sha256": _json_sha256(all_outputs[rival_id][differing[0]]) if differing else None,
                }
            settings_report[identifier] = {
                "parameter": {"copy_style": copy_style, "gap": gap},
                "is_canonical_default": {"copy_style": copy_style, "gap": gap} == DEFAULT_PARAMETERS,
                "racket_relative_path": rule_manifest[identifier]["relative_path"],
                "racket_sha256": rule_manifest[identifier]["sha256"],
                "racket_text": source,
                "episode": episode,
                "public_challenge": public_challenge(episode),
                "all_pairs_match_exact_racket": True,
                "all_pairs_match_python_assertion": outputs == python_outputs,
                "rival_demo_witnesses": rival_witnesses,
                "demos_refute_all_other_parameter_settings": all(
                    item["distinguished"] for item in rival_witnesses.values()
                ),
            }

    return {
        "schema": "arcpuzzles-parametric-copy-evidence-v1",
        "status": "prototype",
        "task_id": TASK_ID,
        "source_task_id": SOURCE_TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "seed": seed,
        "parameters": {
            "copy_style": {
                "allowed": list(ALLOWED_COPY_STYLES),
                "default": DEFAULT_PARAMETERS["copy_style"],
            },
            "gap": {
                "allowed": list(ALLOWED_GAPS),
                "default": DEFAULT_PARAMETERS["gap"],
            },
        },
        "selection_for_seed": parameters_for_seed(seed),
        "prototype_sha256": _sha256_bytes(Path(__file__).read_bytes()),
        "selected_generator_sha256": _load_selected_generator_sha(),
        "racket_runtime": runtime_identity,
        "racket_preflight": racket_runtime_status(),
        "settings": settings_report,
        "limitations": [
            "Prototype only; it does not alter or approve the canonical production rule.",
            "Evidence covers four bounded settings and one retained episode seed, not every possible input.",
            "The authored inputs keep the original arrow/cyan roles and reserve enough horizontal margin for gap=1.",
            "Declared parameter rivals are exhaustive only within copy_style x gap; undeclared algorithms may fit finite demos.",
        ],
    }


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=760)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--write-public", type=Path)
    args = parser.parse_args(argv)

    report = build_evidence(seed=args.seed, output_root=ROOT)
    report["command"] = [sys.executable, *sys.argv]
    _write_json(args.out, report)
    if args.write_public is not None:
        args.write_public.mkdir(parents=True, exist_ok=True)
        for identifier, setting in report["settings"].items():
            _write_json(
                args.write_public / f"{identifier}_public.json",
                setting["public_challenge"],
            )
    print(json.dumps({
        "status": report["status"],
        "seed": report["seed"],
        "settings": {
            key: value["demos_refute_all_other_parameter_settings"]
            for key, value in report["settings"].items()
        },
        "out": str(args.out),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
