#!/usr/bin/env python3
"""Isolated episode-level stamp-size prototype for bf8910eef99b.

The selected production generator and canonical authority remain unchanged.  A
hidden ``stamp_size`` value is selected once per complete episode: 2 is the
canonical/default 2x2 opposite-quadrant stamp, while 1 proposes a 1x1 stamp at
the nearest cell in each same target quadrant.  Source roles, diagonal-opposite
mapping, clipping, and preservation of the 2x2 source block remain invariant.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from contextlib import nullcontext
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge, racket_runtime_status
from puzzle_generators.rule_wrap import strip_rule_wrapper
from reviewer_support import canonical_path, find_root, normalize_grid

TASK_ID = "bf8910eef99b"
VERSION = "0.1.0-prototype"
STAMP_SIZES = (1, 2)
DEFAULT_STAMP_SIZE = 2
_PROFILES = ("top_clip", "right_clip", "bottom_clip", "left_clip")

_SINGLE_CELL_PROGRAM = """(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((nz (find-first (lambda (rc) (!= (at g (fst rc) (snd rc)) 0))
                                  (flatmap (lambda (r)
                                             (map (lambda (c) (cons r c)) (range 0 w)))
                                           (range 0 h))))
                  (br (fst nz))
                  (bc (snd nz))
                  (tl (at g br bc))
                  (tr (at g br (+ bc 1)))
                  (bl (at g (+ br 1) bc))
                  (brr (at g (+ br 1) (+ bc 1))))
             (cellmap g
                      (r c v)
                      (let ((v v))
                        (if (!= v 0)
                            v
                            (cond
                              ((and (= r (+ br 2)) (= c (+ bc 2))) tl)
                              ((and (= r (+ br 2)) (= c (- bc 1))) tr)
                              ((and (= r (- br 1)) (= c (+ bc 2))) bl)
                              ((and (= r (- br 1)) (= c (- bc 1))) brr)
                              (else 0)))))))))"""


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


def _validate_stamp_size(stamp_size) -> int:
    if type(stamp_size) is not int or stamp_size not in STAMP_SIZES:
        raise ValueError(f"stamp_size must be one of {STAMP_SIZES}")
    return stamp_size


def materialize_program(stamp_size=DEFAULT_STAMP_SIZE, *, root=None) -> str:
    selected = _validate_stamp_size(stamp_size)
    if selected == DEFAULT_STAMP_SIZE:
        return canonical_record(root)["program_solution"]
    return _SINGLE_CELL_PROGRAM


def choose_stamp_size(seed, selection="seeded") -> int:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative integer (not bool)")
    if selection == "seeded":
        digest = hashlib.sha256(f"{TASK_ID}:{VERSION}:{seed}:stamp-size".encode()).digest()
        return STAMP_SIZES[int.from_bytes(digest[:8], "big") % len(STAMP_SIZES)]
    return _validate_stamp_size(selection)


def execute_program(bridge: RacketBridge, program: str, grid) -> list[list[int]]:
    """Execute one exact ``(rule! (lambda ...))`` program on a grid."""
    body = strip_rule_wrapper(program)
    if not body.lstrip().startswith(("(lambda", "(λ")):
        raise ValueError("prototype expects a lambda-bodied rule")
    bridge.define_grid("__stamp_size_input__", normalize_grid(grid))
    return normalize_grid(bridge.eval_text(f"({body} __stamp_size_input__)"))


def _bridge_context(bridge):
    return nullcontext(bridge) if bridge is not None else RacketBridge(
        timeout=10, startup_timeout=60
    )


def _production_generator():
    source = Path(__file__).resolve().parents[2] / "generator.py"
    spec = importlib.util.spec_from_file_location("bf8910eef99b_selected_generator", source)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load selected generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _input(seed: int, pair_index: int) -> list[list[int]]:
    """Sample canonical input grammar independently of the hidden stamp size."""
    generator = _production_generator()
    return generator.generate(
        seed,
        pair_index,
        difficulty="medium",
        grid_h=6,
        grid_w=6,
        placement_profile=_PROFILES[pair_index % len(_PROFILES)],
        palette_id=(seed + pair_index) % len(generator.PALETTES),
    )


def generate_episode(seed, *, stamp_size="seeded", root=None, bridge=None) -> dict[str, Any]:
    """Generate three demonstrations and one query under one fixed setting."""
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative integer (not bool)")
    selected = choose_stamp_size(seed, stamp_size)
    programs = {size: materialize_program(size, root=root) for size in STAMP_SIZES}
    inputs = [_input(seed, pair_index) for pair_index in range(4)]

    with _bridge_context(bridge) as active:
        predictions = {
            size: [execute_program(active, programs[size], grid) for grid in inputs]
            for size in STAMP_SIZES
        }

    selected_outputs = predictions[selected]
    rivals = {
        str(size): {
            "demo_refutations": [
                index for index in range(3)
                if predictions[size][index] != selected_outputs[index]
            ],
            "query_differs": predictions[size][3] != selected_outputs[3],
        }
        for size in STAMP_SIZES
    }
    identified = all(
        rivals[str(size)]["demo_refutations"]
        for size in STAMP_SIZES
        if size != selected
    )
    query_separates = all(
        rivals[str(size)]["query_differs"]
        for size in STAMP_SIZES
        if size != selected
    )

    return {
        "schema": "opposite-quadrant-stamp-size-episode-v1",
        "task_id": TASK_ID,
        "prototype_version": VERSION,
        "seed": seed,
        "parameter": {"stamp_size": selected},
        "program": programs[selected],
        "program_sha256": hashlib.sha256(programs[selected].encode()).hexdigest(),
        "train": [
            {"input": inputs[index], "output": selected_outputs[index]}
            for index in range(3)
        ],
        "test": [{"input": inputs[3], "output": selected_outputs[3]}],
        "all_setting_outputs": {
            str(size): outputs for size, outputs in predictions.items()
        },
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

    programs = {size: materialize_program(size, root=root) for size in STAMP_SIZES}
    with RacketBridge(timeout=10, startup_timeout=60) as bridge:
        episodes = [
            generate_episode(seed + index, stamp_size=size, root=root, bridge=bridge)
            for index, size in enumerate(STAMP_SIZES)
        ]
        witness_input = [
            [0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0],
            [0, 0, 1, 2, 0, 0],
            [0, 0, 3, 4, 0, 0],
            [0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0],
        ]
        witness_outputs = {
            str(size): execute_program(bridge, program, witness_input)
            for size, program in programs.items()
        }

    for size, program in programs.items():
        rule_path = out / "private" / "rules" / f"stamp-size-{size}.rkt"
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
    witness_distinct = len({json.dumps(output, sort_keys=True) for output in witness_outputs.values()}) == len(STAMP_SIZES)
    report = {
        "schema": "opposite-quadrant-stamp-size-evidence-v1",
        "status": "pass" if identified == 2 and separated == 2 and witness_distinct else "fail",
        "task_id": TASK_ID,
        "prototype": "proposed; isolated; not selected or approved",
        "parameter": {
            "name": "stamp_size",
            "allowed_values": list(STAMP_SIZES),
            "default": DEFAULT_STAMP_SIZE,
            "resolution": "once per episode",
            "input_constraint": "all inputs are legal canonical 2x2-source scenes; every retained pair distinguishes the two settings",
            "invariant_reasoning": "preserve the four source roles, diagonal-opposite mapping, grid clipping, and the source block",
        },
        "episodes_identified": identified,
        "episodes_total": len(episodes),
        "query_separation_count": separated,
        "witness_outputs_distinct": witness_distinct,
        "episode_seeds": [episode["seed"] for episode in episodes],
        "programs": {
            str(size): {
                "sha256": _sha256_text(program),
                "path": f"private/rules/stamp-size-{size}.rkt",
            }
            for size, program in programs.items()
        },
        "differing_witness": "private/differing-witness.json",
        "source": {
            "path": str(source.relative_to(root_path)),
            "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "canonical_rule_sha256": _sha256_text(canonical_record(root)["program_solution"]),
        },
        "runtime": racket_runtime_status(),
        "limitations": [
            "Only stamp sizes 1 and 2 are assessed.",
            "The finite two-episode run checks only the opposite parameter setting as a rival.",
            "The production generator, canonical authority, and approval state remain unchanged.",
            "Passing evidence establishes executable separation for sampled episodes, not universal induction or training approval.",
        ],
    }
    _write_json(out / "report.json", report)
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("evidence", "episode"))
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--stamp-size", default="seeded", choices=("seeded", "1", "2"))
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    selection = "seeded" if args.stamp_size == "seeded" else int(args.stamp_size)
    if args.command == "evidence":
        payload = build_evidence(args.seed, args.out)
        printable = payload
    else:
        payload = generate_episode(args.seed, stamp_size=selection)
        _write_json(Path(args.out), payload)
        printable = payload["assessment"]
    print(json.dumps(printable, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
