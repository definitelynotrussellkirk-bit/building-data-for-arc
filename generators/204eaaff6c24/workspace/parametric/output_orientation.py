#!/usr/bin/env python3
"""Isolated episode-level output-orientation prototype for 204eaaff6c24.

The hidden parameter is selected once per episode.  Inputs always preserve the
canonical reasoning pattern: find the sole nonzero color and count its cells.
Only the orientation of the resulting monochrome bar changes.  Every retained
label and alternative prediction is executed by the included Racket bridge.
This module is not imported by the selected production generator.
"""
from __future__ import annotations

import argparse
from contextlib import nullcontext
import hashlib
import json
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge, racket_runtime_status
from puzzle_generators.base import gen_ctx
from puzzle_generators.rule_wrap import strip_rule_wrapper
from reviewer_support import canonical_path, find_root, normalize_grid

TASK_ID = "204eaaff6c24"
VERSION = "0.1.0-prototype"
ORIENTATIONS = ("horizontal", "vertical")
DEFAULT_ORIENTATION = "horizontal"

_VERTICAL_PROGRAM = """(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((color (find-first (lambda (v) (!= v 0)) (grid-colors g)))
                  (n (count-color g color)))
             (transpose (encode-bar n n color))))))"""


def _root(root=None) -> Path:
    return Path(root).resolve() if root is not None else find_root(__file__)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def canonical_record(root=None) -> dict[str, Any]:
    matches = []
    with canonical_path(_root(root)).open(encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("task_id") == TASK_ID:
                matches.append(record)
    if len(matches) != 1:
        raise ValueError(f"expected one canonical record for {TASK_ID}, found {len(matches)}")
    return matches[0]


def materialize_program(orientation=DEFAULT_ORIENTATION, *, root=None) -> str:
    if type(orientation) is not str or orientation not in ORIENTATIONS:
        raise ValueError(f"output_orientation must be one of {ORIENTATIONS}")
    if orientation == DEFAULT_ORIENTATION:
        return canonical_record(root)["program_solution"]
    return _VERTICAL_PROGRAM


def choose_orientation(seed, selection="seeded") -> str:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative integer (not bool)")
    if selection == "seeded":
        digest = hashlib.sha256(f"{TASK_ID}:{VERSION}:{seed}:orientation".encode()).digest()
        return ORIENTATIONS[int.from_bytes(digest[:8], "big") % len(ORIENTATIONS)]
    if type(selection) is not str or selection not in ORIENTATIONS:
        raise ValueError("orientation must be horizontal, vertical, or seeded")
    return selection


def execute_program(bridge: RacketBridge, program: str, grid) -> list[list[int]]:
    """Execute an exact `(rule! (lambda ...))` program on one normalized grid."""
    body = strip_rule_wrapper(program)
    if not body.lstrip().startswith(("(lambda", "(λ")):
        raise ValueError("prototype expects a lambda-bodied rule")
    bridge.define_grid("__orientation_input__", normalize_grid(grid))
    return normalize_grid(bridge.eval_text(f"({body} __orientation_input__)"))


def _bridge_context(bridge):
    return nullcontext(bridge) if bridge is not None else RacketBridge(timeout=10, startup_timeout=60)


def _input(seed: int, pair_index: int) -> list[list[int]]:
    """Create a one-color counting input independent of the hidden orientation."""
    ctx = gen_ctx(
        seed=seed,
        sample_index=pair_index,
        version=VERSION,
        task_id=f"{TASK_ID}-orientation-prototype",
        difficulty="medium",
    )
    h = ctx.draw_int_strict("grid_h", 3, 6)
    w = ctx.draw_int_strict("grid_w", 3, 6)
    color = ctx.draw_color_strict("fg_color", exclude=(0,))
    n = ctx.draw_int_strict("n_cells", 2, min(8, h * w - 1))
    cells = [(r, c) for r in range(h) for c in range(w)]
    ctx.draw_rng("placement").shuffle(cells)
    chosen = set(cells[:n])
    return [[color if (r, c) in chosen else 0 for c in range(w)] for r in range(h)]


def generate_episode(seed, *, orientation="seeded", root=None, bridge=None) -> dict[str, Any]:
    """Generate three demonstrations and one query under one fixed setting."""
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative integer (not bool)")
    selected = choose_orientation(seed, orientation)
    programs = {name: materialize_program(name, root=root) for name in ORIENTATIONS}
    inputs = [_input(seed, pair_index) for pair_index in range(4)]

    with _bridge_context(bridge) as active:
        predictions = {
            name: [execute_program(active, program, grid) for grid in inputs]
            for name, program in programs.items()
        }

    selected_outputs = predictions[selected]
    rivals = {}
    for name in ORIENTATIONS:
        rivals[name] = {
            "demo_refutations": [
                index for index in range(3)
                if predictions[name][index] != selected_outputs[index]
            ],
            "query_differs": predictions[name][3] != selected_outputs[3],
        }
    identified = all(
        rivals[name]["demo_refutations"]
        for name in ORIENTATIONS
        if name != selected
    )
    query_separates = all(
        rivals[name]["query_differs"]
        for name in ORIENTATIONS
        if name != selected
    )

    return {
        "schema": "count-bar-output-orientation-episode-v1",
        "task_id": TASK_ID,
        "prototype_version": VERSION,
        "seed": seed,
        "parameter": {"output_orientation": selected},
        "program": programs[selected],
        "program_sha256": _sha256_text(programs[selected]),
        "train": [
            {"input": inputs[index], "output": selected_outputs[index]}
            for index in range(3)
        ],
        "test": [{"input": inputs[3], "output": selected_outputs[3]}],
        "all_setting_outputs": predictions,
        "assessment": {
            "identified": bool(identified),
            "query_separates_settings": bool(query_separates),
            "rivals": rivals,
        },
    }


def _public_episode(episode: dict[str, Any]) -> dict[str, Any]:
    return {
        "train": [
            {"input": pair["input"], "output": pair["output"]}
            for pair in episode["train"]
        ],
        "test": [{"input": pair["input"]} for pair in episode["test"]],
    }


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_evidence(seed, out_dir, *, root=None) -> dict[str, Any]:
    """Run both settings and retain private evidence plus solver-safe exports."""
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative integer (not bool)")
    out = Path(out_dir)
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"refusing to overwrite nonempty evidence directory: {out}")
    out.mkdir(parents=True, exist_ok=True)

    programs = {name: materialize_program(name, root=root) for name in ORIENTATIONS}
    with RacketBridge(timeout=10, startup_timeout=60) as bridge:
        episodes = [
            generate_episode(seed + index, orientation=name, root=root, bridge=bridge)
            for index, name in enumerate(ORIENTATIONS)
        ]
        witness_input = [[0, 4, 0], [4, 0, 0], [0, 0, 0]]
        witness_outputs = {
            name: execute_program(bridge, program, witness_input)
            for name, program in programs.items()
        }

    for name, program in programs.items():
        rule_path = out / "private" / "rules" / f"{name}.rkt"
        rule_path.parent.mkdir(parents=True, exist_ok=True)
        rule_path.write_text(program, encoding="utf-8")

    for index, episode in enumerate(episodes):
        _write_json(out / "private" / f"episode-{index:03d}.json", episode)
        _write_json(out / "public" / f"episode-{index:03d}.json", _public_episode(episode))

    witness = {"input": witness_input, "outputs": witness_outputs}
    _write_json(out / "private" / "differing-witness.json", witness)

    root_path = _root(root)
    source = Path(__file__).resolve()
    identified = sum(bool(episode["assessment"]["identified"]) for episode in episodes)
    separated = sum(bool(episode["assessment"]["query_separates_settings"]) for episode in episodes)
    report = {
        "schema": "count-bar-output-orientation-evidence-v1",
        "status": "pass" if identified == 2 and separated == 2 and len(set(map(json.dumps, witness_outputs.values()))) == 2 else "fail",
        "task_id": TASK_ID,
        "prototype": "proposed; isolated; not selected or approved",
        "parameter": {
            "name": "output_orientation",
            "allowed_values": list(ORIENTATIONS),
            "default": DEFAULT_ORIENTATION,
            "resolution": "once per episode",
            "input_constraint": "every episode pair has at least two foreground cells so orientation is observable",
            "invariant_reasoning": "find the sole nonzero color and count all of its cells",
        },
        "episodes_identified": identified,
        "episodes_total": len(episodes),
        "query_separation_count": separated,
        "episode_seeds": [episode["seed"] for episode in episodes],
        "programs": {
            name: {"sha256": _sha256_text(program), "path": f"private/rules/{name}.rkt"}
            for name, program in programs.items()
        },
        "differing_witness": "private/differing-witness.json",
        "source": {
            "path": str(source.relative_to(root_path)),
            "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "canonical_rule_sha256": _sha256_text(canonical_record(root)["program_solution"]),
        },
        "runtime": racket_runtime_status(),
        "limitations": [
            "Only horizontal and vertical bars are assessed.",
            "The finite two-episode run checks only the opposite parameter setting as a rival.",
            "Inputs use the canonical one-color counting grammar with n>=2; n=1 cannot reveal orientation.",
            "This prototype does not alter production generation, canonical authority, or approval state.",
        ],
    }
    _write_json(out / "report.json", report)
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("evidence", "episode"))
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--orientation", default="seeded", choices=("seeded",) + ORIENTATIONS)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    if args.command == "evidence":
        payload = build_evidence(args.seed, args.out)
        printable = payload
    else:
        payload = generate_episode(args.seed, orientation=args.orientation)
        _write_json(Path(args.out), payload)
        printable = payload["assessment"]
    print(json.dumps(printable, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
