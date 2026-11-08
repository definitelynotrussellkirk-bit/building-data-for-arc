#!/usr/bin/env python3
"""Task-local parametric prototype for ascending vs descending size order.

The canonical production generator and authority remain unchanged.  This module
chooses one ``sort_order`` per episode, materializes the corresponding exact
Racket program, builds three demonstrations plus one query, and can execute both
the chosen program and its parameter rival through the packet's Racket bridge.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from functools import lru_cache
from pathlib import Path
from typing import Any

TASK_ID = "ee64b9b0fe20"
PROTOTYPE_VERSION = "1.0.0"
PARAMETER = "sort_order"
SETTINGS = ("ascending", "descending")
CANONICAL_SETTING = "ascending"
COMPARATOR_ASC = "(< (obj-size a) (obj-size b))"
COMPARATOR_DESC = "(> (obj-size a) (obj-size b))"

HERE = Path(__file__).resolve()
TASK_HOME = HERE.parents[2]
REPO = HERE.parents[4]
GENERATOR_PATH = TASK_HOME / "generator.py"
CANONICAL_PATH = REPO / "shared/data/canonical/puzzles.jsonl"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


@lru_cache(maxsize=1)
def load_generator():
    spec = importlib.util.spec_from_file_location("ee64b9b0fe20_parametric_source", GENERATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@lru_cache(maxsize=1)
def canonical_program() -> str:
    programs = set()
    with CANONICAL_PATH.open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                programs.add(row["program_solution"])
    if len(programs) != 1:
        raise RuntimeError(f"expected one canonical program for {TASK_ID}, found {len(programs)}")
    program = programs.pop()
    if program.count(COMPARATOR_ASC) != 1:
        raise RuntimeError("canonical comparator changed; refusing an unreviewed textual mutation")
    return program


def _validate_setting(sort_order: str) -> str:
    if sort_order not in SETTINGS:
        raise ValueError(f"sort_order must be one of {SETTINGS!r}, not {sort_order!r}")
    return sort_order


def program_for(sort_order: str) -> str:
    """Return exact Racket for one episode setting.

    Ascending is byte-for-byte the canonical authority.  Descending changes only
    the size comparator, preserving object extraction, frame filtering, placement,
    and all other reasoning steps.
    """
    sort_order = _validate_setting(sort_order)
    program = canonical_program()
    if sort_order == CANONICAL_SETTING:
        return program
    changed = program.replace(COMPARATOR_ASC, COMPARATOR_DESC, 1)
    if changed == program or changed.count(COMPARATOR_DESC) != 1:
        raise RuntimeError("failed to materialize the descending comparator exactly once")
    return changed


def setting_for_seed(seed: int) -> str:
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise TypeError(f"seed must be an integer, not {seed!r}")
    return SETTINGS[seed % len(SETTINGS)]


def alternative_setting(sort_order: str) -> str:
    sort_order = _validate_setting(sort_order)
    return "descending" if sort_order == "ascending" else "ascending"


def apply_python(grid: list[list[int]], sort_order: str) -> list[list[int]]:
    """Diagnostic mirror for construction/tests; Racket remains evidence authority."""
    sort_order = _validate_setting(sort_order)
    gen = load_generator()
    _, _, background, _, shapes = gen._analyze(grid)
    sign = 1 if sort_order == "ascending" else -1
    return gen._pack(grid, shapes, background, key=lambda item: sign * len(item[1]))


def build_episode(seed: int, *, difficulty: str = "medium", pair_count: int = 4) -> dict[str, Any]:
    """Build one private episode with the parameter fixed across every pair."""
    if isinstance(pair_count, bool) or not isinstance(pair_count, int) or pair_count < 4:
        raise ValueError("pair_count must be an integer >= 4")
    setting = setting_for_seed(seed)
    rival = alternative_setting(setting)
    gen = load_generator()
    pairs: list[dict[str, Any]] = []
    attempted_indices: list[int] = []

    # Distinct object sizes are already part of the canonical domain.  Retain
    # only inputs where reversing the order changes the full output, so every
    # demonstration—not merely the episode aggregate—teaches the parameter.
    for sample_index in range(128):
        grid = gen.generate(seed, sample_index, difficulty=difficulty)
        output = apply_python(grid, setting)
        other = apply_python(grid, rival)
        attempted_indices.append(sample_index)
        if output == other:
            continue
        pairs.append({
            "input": grid,
            "output": output,
            "alternative_output": other,
            "sample_index": sample_index,
        })
        if len(pairs) == pair_count:
            break
    if len(pairs) != pair_count:
        raise RuntimeError(
            f"could not build {pair_count} parameter-distinguishing pairs from 128 candidates"
        )

    train_count = pair_count - 1
    return {
        "schema": "arcpuzzles-task-local-parametric-episode-v1",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "train": pairs[:train_count],
        "test": pairs[train_count:],
        "program": program_for(setting),
        "alternative_program": program_for(rival),
        "meta": {
            "parameter": PARAMETER,
            "allowed_values": list(SETTINGS),
            "canonical_setting": CANONICAL_SETTING,
            "sort_order": setting,
            "alternative_sort_order": rival,
            "parameter_fixed_for_episode": True,
            "difficulty": difficulty,
            "seed": seed,
            "pair_count": pair_count,
            "accepted_sample_indices": [pair["sample_index"] for pair in pairs],
            "attempted_sample_indices": attempted_indices,
            "all_pairs_distinguish_alternative": all(
                pair["output"] != pair["alternative_output"] for pair in pairs
            ),
            "input_constraints": [
                "canonical ee64b9b0fe20 domain",
                "at least two non-frame objects with distinct cell counts",
                "packed bounding-box widths fit the canvas",
                "each retained pair changes when size order is reversed",
            ],
            "invariant_reasoning": [
                "infer the nonzero modal background",
                "find monochromatic four-connected components",
                "discard a whole-canvas-bounding-box frame",
                "sort objects by distinct cell count",
                "bottom-align and left-pack object bounding boxes",
            ],
        },
    }


def _grid_literal(grid: list[list[int]]) -> str:
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def execute_racket(
    programs: dict[str, str], grids: list[list[list[int]]]
) -> tuple[dict[str, list[list[list[int]]]], dict[str, Any]]:
    """Execute programs in an official copied runtime, not the authoring layout.

    The source tree intentionally lacks the runtime-only ``scripts`` package used
    by ``wrap_rule``.  Preparing the mapped runtime and launching a fresh child
    process prevents already-imported authoring packages from shadowing it.
    """
    sys.path.insert(0, str(REPO / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime

    runtime = Path(tempfile.mkdtemp(prefix="ee64-parametric-runtime-"))
    request_path = runtime / "parametric_request.json"
    response_path = runtime / "parametric_response.json"
    try:
        manifest = prepare_runtime(Catalog(REPO), runtime, task_ids=[TASK_ID])
        write_json(request_path, {"programs": programs, "grids": grids})
        worker = r'''
import json
import sys
from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule

request_path, response_path = sys.argv[1:3]
request = json.load(open(request_path, encoding="utf-8"))

def literal(grid):
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"

bridge = RacketBridge(timeout=30)
try:
    outputs = {}
    for name, program in request["programs"].items():
        wrapped = wrap_rule(program)
        outputs[name] = [
            bridge.eval_text(f"({wrapped} {literal(grid)})")
            for grid in request["grids"]
        ]
finally:
    bridge.close()

json.dump(outputs, open(response_path, "w", encoding="utf-8"), sort_keys=True)
'''
        env = os.environ.copy()
        inherited = env.get("PYTHONPATH")
        env["PYTHONPATH"] = str(runtime) + (os.pathsep + inherited if inherited else "")
        result = subprocess.run(
            [sys.executable, "-c", worker, str(request_path), str(response_path)],
            cwd=runtime,
            env=env,
            capture_output=True,
            text=True,
            timeout=240,
        )
        if result.returncode != 0:
            raise RuntimeError(
                "copied-runtime Racket worker failed\n"
                f"stdout:\n{result.stdout}\n"
                f"stderr:\n{result.stderr}"
            )
        outputs = json.loads(response_path.read_text(encoding="utf-8"))
        return outputs, manifest
    finally:
        shutil.rmtree(runtime, ignore_errors=True)


def materialize_episode(seed: int, *, difficulty: str = "medium", pair_count: int = 4) -> dict[str, Any]:
    """Build and verify one episode against both real Racket parameter settings."""
    episode = build_episode(seed, difficulty=difficulty, pair_count=pair_count)
    pairs = episode["train"] + episode["test"]
    grids = [pair["input"] for pair in pairs]
    executed, runtime_manifest = execute_racket(
        {"chosen": episode["program"], "alternative": episode["alternative_program"]}, grids
    )
    chosen = executed["chosen"]
    alternative = executed["alternative"]
    for index, pair in enumerate(pairs):
        if chosen[index] != pair["output"]:
            raise AssertionError(f"chosen Racket/Python mismatch at pair {index}")
        if alternative[index] != pair["alternative_output"]:
            raise AssertionError(f"alternative Racket/Python mismatch at pair {index}")

    episode["verification"] = {
        "authority": "real_racket_bridge",
        "chosen_matches_python": True,
        "alternative_matches_python": True,
        "chosen_program_sha256": sha256_text(episode["program"]),
        "alternative_program_sha256": sha256_text(episode["alternative_program"]),
        "all_train_pairs_distinguish_parameter_rival": all(
            pair["output"] != pair["alternative_output"] for pair in episode["train"]
        ),
        "query_distinguishes_parameter_rival": all(
            pair["output"] != pair["alternative_output"] for pair in episode["test"]
        ),
        "runtime_manifest": runtime_manifest,
        "runtime_manifest_sha256": sha256_text(
            json.dumps(runtime_manifest, sort_keys=True, separators=(",", ":"))
        ),
    }
    return episode


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Strip hidden parameter, programs, alternative labels, and query answers."""
    return {
        "schema": "arcpuzzles-parametric-public-challenge-v1",
        "task_id": TASK_ID,
        "prototype": "sort-order",
        "train": [
            {"input": pair["input"], "output": pair["output"]}
            for pair in episode["train"]
        ],
        "test": [{"input": pair["input"]} for pair in episode["test"]],
    }


def public_filename(episode: dict[str, Any]) -> str:
    """Opaque identifier derived only from model-visible puzzle content."""
    raw = json.dumps(public_challenge(episode), sort_keys=True, separators=(",", ":")).encode()
    return "challenge-" + hashlib.sha256(raw).hexdigest() + ".json"


def private_receipt(episode: dict[str, Any]) -> dict[str, Any]:
    return episode


def _seed_for_setting(start: int, desired: str) -> int:
    for seed in range(start, start + 1000):
        if setting_for_seed(seed) == desired:
            return seed
    raise RuntimeError(f"could not find seed for setting {desired}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed-base", type=int, default=0)
    parser.add_argument("--difficulty", choices=("easy", "medium", "hard"), default="medium")
    parser.add_argument("--pair-count", type=int, default=4)
    args = parser.parse_args(argv)

    out = args.out.resolve()
    if out.exists():
        parser.error("output path already exists; preserve evidence and choose a new path")
    out.mkdir(parents=True)

    command = {"cwd": str(Path.cwd()), "argv": [sys.executable, *sys.argv]}
    episodes = {}
    for setting in SETTINGS:
        seed = _seed_for_setting(args.seed_base, setting)
        episode = materialize_episode(seed, difficulty=args.difficulty, pair_count=args.pair_count)
        if episode["meta"]["sort_order"] != setting:
            raise AssertionError("seed-to-setting selection drifted")
        setting_dir = out / "private" / setting
        setting_dir.mkdir(parents=True)
        write_json(setting_dir / "episode_private.json", private_receipt(episode))
        write_json(out / "public" / public_filename(episode), public_challenge(episode))
        (setting_dir / "program.rkt").write_text(episode["program"] + "\n", encoding="utf-8")
        episodes[setting] = {
            "seed": seed,
            "difficulty": args.difficulty,
            "accepted_sample_indices": episode["meta"]["accepted_sample_indices"],
            "program_path": f"private/{setting}/program.rkt",
            "program_sha256": episode["verification"]["chosen_program_sha256"],
            "alternative_program_sha256": episode["verification"]["alternative_program_sha256"],
            "all_train_pairs_distinguish_parameter_rival": episode["verification"][
                "all_train_pairs_distinguish_parameter_rival"
            ],
            "query_distinguishes_parameter_rival": episode["verification"][
                "query_distinguishes_parameter_rival"
            ],
            "public_challenge": f"public/{public_filename(episode)}",
            "private_receipt": f"private/{setting}/episode_private.json",
        }

    summary = {
        "schema": "ee64b9b0fe20-sort-order-prototype-evidence-v1",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "status": "proposed",
        "parameter": {
            "name": PARAMETER,
            "allowed_values": list(SETTINGS),
            "canonical_setting": CANONICAL_SETTING,
            "chosen_once_per_episode": True,
            "changes_executed_transformation": True,
        },
        "source_hashes": {
            "prototype_sha256": sha256_file(HERE),
            "canonical_generator_sha256": sha256_file(GENERATOR_PATH),
            "canonical_ledger_sha256": sha256_file(CANONICAL_PATH),
            "canonical_program_sha256": sha256_text(canonical_program()),
        },
        "command": command,
        "episodes": episodes,
        "limitations": [
            "task-local prototype only; production generation and canonical authority are unchanged",
            "two bounded order settings only; ties remain outside the demonstrated domain",
            "finite two-episode Racket evidence is not training approval or universal identifiability",
        ],
    }
    write_json(out / "summary.json", summary)
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
