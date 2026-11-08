#!/usr/bin/env python3
"""Proposed episode-level ring-thickness parameter for ARC 78645c33b002.

This task-local authoring prototype never changes the selected canonical rule.
Every retained label is checked by the included protected Racket runtime.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import sys
from typing import Any

from reviewer_support import canonical_path, find_root, load_selected_generator


TASK_ID = "78645c33b002"
ROOT = find_root(__file__)
GENERATOR, GENERATOR_PATH, GENERATOR_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
ALLOWED_RING_THICKNESSES = (1, 2)
DEFAULT_RING_THICKNESS = 1
STATUS = "proposed prototype; not production-approved"
_PROFILES = ("public_2", "tall_offcenter", "repeated_colors", "six_layers")
_DIFFICULTIES = ("easy", "medium", "hard", None)


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical_program() -> str:
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row["program_solution"]
    raise KeyError(TASK_ID)


def _validate_thickness(ring_thickness: int) -> None:
    if type(ring_thickness) is not int or ring_thickness not in ALLOWED_RING_THICKNESSES:
        raise ValueError(f"ring_thickness must be one of {ALLOWED_RING_THICKNESSES}")


def program_for(ring_thickness: int = DEFAULT_RING_THICKNESS) -> str:
    """Materialize exact Racket for one bounded setting; default bytes are canonical."""
    _validate_thickness(ring_thickness)
    source = canonical_program()
    if ring_thickness == DEFAULT_RING_THICKNESS:
        return source

    old_size = "(out-size (- (* 2 n) 1))"
    new_size = (
        f"(ring-thickness {ring_thickness})\n"
        "                  (out-size (+ 1 (* 2 ring-thickness (- n 1))))"
    )
    old_index = "(list-ref layers-rev dist)"
    new_index = (
        "(list-ref layers-rev "
        "(quotient (+ dist (- ring-thickness 1)) ring-thickness))"
    )
    if source.count(old_size) != 1 or source.count(old_index) != 1:
        raise ValueError("canonical authority changed; ring-thickness prototype needs review")
    return source.replace(old_size, new_size).replace(old_index, new_index)


def apply_python(grid: list[list[int]], ring_thickness: int) -> list[list[int]]:
    """Small authoring mirror; retained evidence independently executes Racket."""
    _validate_thickness(ring_thickness)
    extracted = GENERATOR._extract_layers(grid)
    if extracted["errors"]:
        raise ValueError("; ".join(extracted["errors"]))
    colors = tuple(reversed(extracted["layers"]))  # inside -> outside
    size = 2 * ring_thickness * (len(colors) - 1) + 1
    middle = size // 2
    return [
        [
            colors[
                (max(abs(row - middle), abs(col - middle)) + ring_thickness - 1)
                // ring_thickness
            ]
            for col in range(size)
        ]
        for row in range(size)
    ]


def choose_ring_thickness(seed: int) -> int:
    if type(seed) is not int:
        raise ValueError("episode seed must be a literal integer")
    return random.Random(seed).choice(ALLOWED_RING_THICKNESSES)


def build_inputs(seed: int, count: int) -> list[list[list[int]]]:
    if type(seed) is not int:
        raise ValueError("episode seed must be a literal integer")
    if type(count) is not int or count < 1:
        raise ValueError("count must be a positive literal integer")
    inputs = []
    for index in range(count):
        profile = _PROFILES[index % len(_PROFILES)]
        difficulty = _DIFFICULTIES[index % len(_DIFFICULTIES)]
        inputs.append(
            GENERATOR.generate(
                seed * 1009 + 20_261_019 + index,
                index,
                difficulty=difficulty,
                scene_profile=profile,
            )
        )
    return inputs


def build_episode(seed: int, *, n_train: int = 3, n_test: int = 1) -> dict[str, Any]:
    if type(n_train) is not int or n_train < 1:
        raise ValueError("n_train must be a positive literal integer")
    if type(n_test) is not int or n_test < 1:
        raise ValueError("n_test must be a positive literal integer")
    ring_thickness = choose_ring_thickness(seed)
    inputs = build_inputs(seed, n_train + n_test)
    pairs = [
        {"input": grid, "output": apply_python(grid, ring_thickness)}
        for grid in inputs
    ]
    return {
        "train": pairs[:n_train],
        "test": pairs[n_train:],
        "private": {
            "seed": seed,
            "ring_thickness": ring_thickness,
            "program": program_for(ring_thickness),
            "program_sha256": sha256_bytes(program_for(ring_thickness).encode()),
            "generator_sha256": GENERATOR_SHA256,
        },
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    return {
        "train": [
            {"input": pair["input"], "output": pair["output"]}
            for pair in episode["train"]
        ],
        "test": [{"input": pair["input"]} for pair in episode["test"]],
    }


def _racket_callable(source: str) -> str:
    stripped = source.strip()
    if not stripped.startswith("(rule!") or not stripped.endswith(")"):
        raise ValueError("prototype program must be one (rule! EXPR) form")
    expression = stripped[len("(rule!") : -1].strip()
    if not expression.startswith("(lambda"):
        raise ValueError("prototype rule expression must be a lambda")
    return expression


def _grid_literal(grid: list[list[int]]) -> str:
    rows = " ".join("(" + " ".join(map(str, row)) + ")" for row in grid)
    return f"'({rows})"


def _application(source: str, grid: list[list[int]]) -> str:
    return f"({_racket_callable(source)} {_grid_literal(grid)})"


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def materialize(seeds: list[int], out_dir: Path) -> dict[str, Any]:
    from arc_repl.racket_bridge import RacketBridge

    if not seeds:
        raise ValueError("at least one seed is required")
    episodes = [build_episode(seed) for seed in seeds]
    represented = {episode["private"]["ring_thickness"] for episode in episodes}
    if represented != set(ALLOWED_RING_THICKNESSES):
        raise ValueError(
            f"retained seeds must cover both settings; observed {sorted(represented)}"
        )

    programs = {value: program_for(value) for value in ALLOWED_RING_THICKNESSES}
    checks = []
    bridge = RacketBridge(timeout=30, max_calls_before_restart=128)
    try:
        runtime_identity = bridge.runtime_identity
        for episode_index, episode in enumerate(episodes):
            selected = episode["private"]["ring_thickness"]
            for split in ("train", "test"):
                for pair_index, pair in enumerate(episode[split]):
                    outputs = {}
                    for candidate, source in programs.items():
                        output = bridge.eval_text(_application(source, pair["input"]))
                        if output != apply_python(pair["input"], candidate):
                            raise AssertionError(
                                f"Racket/Python mismatch: episode {episode_index} "
                                f"{split}[{pair_index}] setting {candidate}"
                            )
                        outputs[str(candidate)] = output
                    if outputs[str(selected)] != pair["output"]:
                        raise AssertionError("selected Racket output disagrees with episode label")
                    distinct = outputs["1"] != outputs["2"]
                    if split == "train" and not distinct:
                        raise AssertionError("demonstration does not distinguish both settings")
                    checks.append(
                        {
                            "episode_index": episode_index,
                            "episode_seed": episode["private"]["seed"],
                            "selected_ring_thickness": selected,
                            "split": split,
                            "pair_index": pair_index,
                            "input": pair["input"],
                            "outputs": outputs,
                            "settings_distinct": distinct,
                            "applications": {
                                str(candidate): _application(source, pair["input"])
                                for candidate, source in programs.items()
                            },
                        }
                    )
    finally:
        bridge.shutdown()

    out_dir.mkdir(parents=True, exist_ok=True)
    for thickness, source in programs.items():
        path = out_dir / "rules" / f"ring_thickness_{thickness}.rkt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding="utf-8")

    for index, episode in enumerate(episodes):
        _write_json(out_dir / "public" / f"episode-{index:03d}.json", public_challenge(episode))
        _write_json(out_dir / "private" / f"episode-{index:03d}.json", episode)

    witness = checks[0]
    shared_witness = {
        "input": witness["input"],
        "outputs": witness["outputs"],
        "applications": witness["applications"],
        "settings_distinct": witness["settings_distinct"],
    }
    _write_json(out_dir / "private" / "shared-witness.json", shared_witness)

    source_path = Path(__file__).resolve()
    manifest = {
        "schema": "78645c33b002-ring-thickness-prototype-v1",
        "status": STATUS,
        "task_id": TASK_ID,
        "parameter": {
            "name": "ring_thickness",
            "allowed_values": list(ALLOWED_RING_THICKNESSES),
            "default": DEFAULT_RING_THICKNESS,
            "chosen_once_per_episode": True,
            "input_constraints_depending_on_parameter": [],
            "meaning": (
                "Chebyshev thickness of each noncentral normalized output ring; "
                "the center remains one cell"
            ),
        },
        "invariant_reasoning": [
            "extract the strictly nested filled rectangles from outside inward",
            "preserve their ordered colors",
            "normalize the hierarchy to concentric square layers",
        ],
        "seeds": seeds,
        "programs": {
            str(value): {
                "source": source,
                "sha256": sha256_bytes(source.encode()),
                "normalized_sha256": sha256_bytes(" ".join(source.split()).encode()),
            }
            for value, source in programs.items()
        },
        "default_program_exactly_canonical": programs["1" if "1" in programs else 1] == canonical_program(),
        "generator_source": str(GENERATOR_PATH),
        "generator_sha256": GENERATOR_SHA256,
        "prototype_source_sha256": sha256_bytes(source_path.read_bytes()),
        "racket_runtime": runtime_identity,
        "cwd": os.getcwd(),
        "argv": sys.argv,
        "counts": {
            "episodes": len(episodes),
            "train_pairs": sum(len(episode["train"]) for episode in episodes),
            "test_pairs": sum(len(episode["test"]) for episode in episodes),
            "racket_executions": len(checks) * len(programs),
            "distinguishing_train_pairs": sum(
                row["settings_distinct"] for row in checks if row["split"] == "train"
            ),
        },
        "checks": checks,
        "limitations": [
            "This task-local prototype is not selected, catalog-approved, or admitted for training.",
            "Evidence covers two bounded settings and the retained seeds, not all possible variants.",
            "The demonstrations eliminate only the declared thickness rival, not every imaginable rule.",
            "Input sampling remains the canonical nested-rectangle grammar; no parameter is encoded in the query input.",
        ],
    }
    _write_json(out_dir / "private" / "manifest.json", manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", nargs="+", type=int, default=[1, 0])
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    manifest = materialize(args.seeds, Path(args.out))
    print(json.dumps({"status": "passed", "counts": manifest["counts"], "out": args.out}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
