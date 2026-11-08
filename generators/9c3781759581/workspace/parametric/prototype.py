#!/usr/bin/env python3
"""Proposed episode-level target-color variant; no production integration.

Run through WORK/run_with_racket.py. Every retained label and parameter rival
prediction comes from the existing Racket verifier; Python crops only cross-check
those results. This module does not import the selected generator or rule ledger.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import sys

from puzzle_generators import stable_rng
from reviewer_support import find_root, normalize_grid


TASK_ID = "9c3781759581"
VERSION = "target-color-prototype-v1"
ALLOWED_TARGET_COLORS = (2, 5, 9)
DEFAULT_TARGET_COLOR = 9
PROFILE_NAMES = ("unequal_boxes", "equal_size_offsets", "point_row_column", "full_span")
N_TRAIN = 3
N_PAIRS = 4
LIMITATIONS = [
    "Proposed task-local prototype only; no production parameter API or approval is added.",
    "The default program is the original inclusive crop expression with target_color=9.",
    "Only target_color in {2,5,9} is supported; zero/background and absent-target rules are excluded.",
    "Every sampled input contains all three candidate colors with distinct bounding boxes and outputs.",
    "Inputs use four constructed geometry profiles and an 11..17 cell grid side; this is not all lawful inputs.",
    "One setting is selected once from each seed; input RNG draws do not depend on that selected setting.",
    "Evidence covers only the retained seeds and the other two declared target-color rivals.",
    "Query rotations reuse the same four labeled pairs and are not independent generated episodes.",
    "Finite rival refutation does not prove identification against arbitrary rules or training suitability.",
    "The one-cell execution canary is runtime plumbing, not an episode demonstration.",
]


def _sha_bytes(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def json_sha256(value) -> str:
    return _sha_bytes(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def _validate_seed(seed: int) -> None:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative integer")


def rule_source(target_color: int = DEFAULT_TARGET_COLOR) -> str:
    if type(target_color) is not int or target_color not in ALLOWED_TARGET_COLORS:
        raise ValueError("target_color must be one of 2, 5, 9")
    return (
        f"(rule! (let ((bb (bbox-of-cells (find-color g {target_color})))) "
        "(subgrid g (first bb) (second bb) (third bb) (fourth bb))))"
    )


def target_for_seed(seed: int) -> int:
    _validate_seed(seed)
    return stable_rng(seed, f"{TASK_ID}:episode-target", VERSION).choice(ALLOWED_TARGET_COLORS)


def select_seeds(base_seed: int, per_setting: int) -> dict:
    """Bounded deterministic seed selection to retain every allowed setting."""
    _validate_seed(base_seed)
    if type(per_setting) is not int or not 1 <= per_setting <= 4:
        raise ValueError("per_setting must be an integer in 1..4")
    buckets = {color: [] for color in ALLOWED_TARGET_COLORS}
    for offset in range(10000):
        seed = base_seed + offset
        color = target_for_seed(seed)
        if len(buckets[color]) < per_setting:
            buckets[color].append(seed)
        if all(len(seeds) == per_setting for seeds in buckets.values()):
            return {"base_seed": base_seed, "per_setting": per_setting,
                    "examined_seeds": offset + 1,
                    "seeds": sorted(seed for seeds in buckets.values() for seed in seeds)}
    raise RuntimeError("The bounded seed search did not cover every parameter setting")


def bbox(grid: list[list[int]], target_color: int) -> tuple[int, int, int, int]:
    rule_source(target_color)
    points = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
              if value == target_color]
    if not points:
        raise ValueError(f"target_color={target_color} must occur in the input")
    return (min(r for r, _ in points), min(c for _, c in points),
            max(r for r, _ in points), max(c for _, c in points))


def python_crop(grid: list[list[int]], target_color: int = DEFAULT_TARGET_COLOR) -> list[list[int]]:
    """Independent mirror for parity checks; never the authority for saved labels."""
    grid = normalize_grid(grid)
    r0, c0, r1, c1 = bbox(grid, target_color)
    return [row[c0:c1 + 1] for row in grid[r0:r1 + 1]]


def _extrema(rng, box, corners: bool):
    r0, c0, r1, c1 = box
    if corners:
        return {(r0, c0), (r0, c1), (r1, c0), (r1, c1)}
    return {(r0, rng.randint(c0, c1)), (r1, rng.randint(c0, c1)),
            (rng.randint(r0, r1), c0), (rng.randint(r0, r1), c1)}


def _sample_input(seed: int, pair_index: int) -> list[list[int]]:
    rng = stable_rng(seed, f"{TASK_ID}:input:{pair_index}", VERSION)
    height, width = rng.randint(11, 17), rng.randint(11, 17)
    dimensions = [
        [(3, 4), (5, 3), (4, 6)],
        [(4, 4), (4, 4), (4, 4)],
        [(1, 1), (1, 5), (5, 1)],
        [(height, width), (5, 6), (6, 5)],
    ][pair_index]
    colors = list(ALLOWED_TARGET_COLORS)
    rng.shuffle(colors)  # Independent of the episode's hidden target color.
    marker_cells = {}
    boxes = {}
    for color, (box_height, box_width) in zip(colors, dimensions):
        for _ in range(256):
            r0 = rng.randint(0, height - box_height)
            c0 = rng.randint(0, width - box_width)
            box = (r0, c0, r0 + box_height - 1, c0 + box_width - 1)
            points = _extrema(rng, box, corners=pair_index in (1, 3))
            if box not in boxes.values() and points.isdisjoint(marker_cells):
                boxes[color] = box
                marker_cells.update({point: color for point in points})
                break
        else:
            raise RuntimeError("Bounded marker placement exhausted")
    fillers = (1, 3, 4, 6, 7, 8)
    grid = [[rng.choice(fillers) if rng.random() < 0.16 else 0
             for _ in range(width)] for _ in range(height)]
    for (r, c), color in marker_cells.items():
        grid[r][c] = color
    # Keep visible non-marker contents and zero cells inside nontrivial crops.
    # Filler colors never belong to the candidate palette, so extrema stay fixed.
    for box in boxes.values():
        r0, c0, r1, c1 = box
        available = [(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)
                     if (r, c) not in marker_cells]
        rng.shuffle(available)
        if available:
            r, c = available[0]
            grid[r][c] = rng.choice(fillers)
        if len(available) >= 2:
            r, c = available[1]
            grid[r][c] = 0
    observed_boxes = [bbox(grid, color) for color in ALLOWED_TARGET_COLORS]
    outputs = [json_sha256(python_crop(grid, color)) for color in ALLOWED_TARGET_COLORS]
    if len(set(observed_boxes)) != 3 or len(set(outputs)) != 3:
        raise RuntimeError("Input fails the declared cross-setting discrimination constraint")
    return grid


def sample_episode(seed: int) -> dict:
    """Select the rule once; generate three demonstrations and one query input."""
    target_color = target_for_seed(seed)
    inputs = [_sample_input(seed, pair_index) for pair_index in range(N_PAIRS)]
    return {
        "episode_id": "episode-" + json_sha256(inputs)[:16],
        "seed": seed, "parameters": {"target_color": target_color},
        "program": rule_source(target_color), "inputs": inputs,
        "profiles": list(PROFILE_NAMES), "train_count": N_TRAIN,
    }


def public_challenge(pairs: list[dict], query_index: int = N_TRAIN) -> dict:
    if type(query_index) is not int or not 0 <= query_index < len(pairs) or len(pairs) < 2:
        raise ValueError("A query index within at least two labeled pairs is required")
    return copy.deepcopy({
        "train": [{"input": pair["input"], "output": pair["output"]}
                  for index, pair in enumerate(pairs) if index != query_index],
        "test": [{"input": pairs[query_index]["input"]}],
    })


def score_rotation(predictions: dict[int, list], chosen_color: int, query_index: int) -> dict:
    """Score already executed predictions; report survival separately from ambiguity."""
    rule_source(chosen_color)
    if set(predictions) != set(ALLOWED_TARGET_COLORS):
        raise ValueError("Predictions for every declared parameter setting are required")
    length = len(predictions[chosen_color])
    if length < 2 or not 0 <= query_index < length or any(len(x) != length for x in predictions.values()):
        raise ValueError("Inconsistent predictions or query index")
    demos = [index for index in range(length) if index != query_index]
    rivals = []
    for color in ALLOWED_TARGET_COLORS:
        if color == chosen_color:
            continue
        mismatches = [index for index in demos
                      if predictions[color][index] != predictions[chosen_color][index]]
        query_disagrees = predictions[color][query_index] != predictions[chosen_color][query_index]
        status = ("refuted_by_demonstrations" if mismatches else
                  "ambiguous_query" if query_disagrees else "survived_all")
        rivals.append({"target_color": color, "status": status,
                       "demonstration_mismatches": mismatches,
                       "query_disagrees": query_disagrees})
    return {"query_pair_index": query_index, "demonstration_pair_indices": demos,
            "is_production_query": query_index == N_TRAIN, "rivals": rivals}


def _write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def _source_bindings() -> dict:
    from arc_repl import isolated_verifier, racket_bridge
    from puzzle_generators import base
    here = Path(__file__).resolve()
    root = find_root(here)
    task_home = here.parents[2]
    paths = [here, here.with_name("README.md"),
             task_home / "tests/test_parametric_marker_crop.py",
             Path(base.__file__).resolve(), Path(isolated_verifier.__file__).resolve(),
             Path(racket_bridge.__file__).resolve(),
             Path(racket_bridge.__file__).with_name("executor.py").resolve(),
             Path(racket_bridge.__file__).parent / "racket_prelude/arc-prelude.rkt"]
    return {path.relative_to(root).as_posix(): _sha_bytes(path.read_bytes()) for path in paths}


def run_evidence(out: Path, *, base_seed: int = 20261019, per_setting: int = 1,
                 racket_path: str | None = None) -> dict:
    """Generate and retain bounded real-Racket evidence in a new directory.

    Runtime failures leave a report and the returned failure receipt. Public
    labels are written only after all programs execute and match the mirror.
    """
    from arc_repl.isolated_verifier import Limits, verify_candidate
    selection = select_seeds(base_seed, per_setting)
    out = Path(out).absolute()
    out.mkdir(parents=True, exist_ok=False)
    (out / "public").mkdir()
    (out / "private/rules").mkdir(parents=True)
    (out / "private/racket").mkdir()
    report = {
        "schema": "parametric-marker-crop-evidence-v1", "status": "running",
        "task_id": TASK_ID, "prototype_version": VERSION,
        "parameter_contract": {"name": "target_color", "allowed_values": list(ALLOWED_TARGET_COLORS),
                               "original_default": DEFAULT_TARGET_COLOR,
                               "sampling_unit": "once per episode from its seed"},
        "seed_selection": selection, "rules": [], "episodes": [],
        "limitations": LIMITATIONS,
        "invocation": {"cwd": str(Path.cwd()), "python_executable": sys.executable,
                       "argv": list(sys.argv), "python_version": sys.version},
    }
    _write_json(out / "report.json", report)
    try:
        report["source_sha256"] = _source_bindings()
        chosen_racket = racket_path if racket_path is not None else os.environ.get("RACKET_PATH", "")
        binary = Path(chosen_racket) if chosen_racket else None
        report["runtime"] = {
            "backend": "racket", "public_api": "arc_repl.isolated_verifier.verify_candidate",
            "racket_path": str(binary.resolve()) if binary else None,
            "racket_sha256": _sha_bytes(binary.read_bytes()) if binary and binary.is_file() else None,
        }
        episodes = [sample_episode(seed) for seed in selection["seeds"]]
        execution_inputs = [{"episode_id": episode["episode_id"], "pair_index": index,
                             "input": grid, "input_sha256": json_sha256(grid)}
                            for episode in episodes for index, grid in enumerate(episode["inputs"])]
        _write_json(out / "private/execution_inputs.json", execution_inputs)
        predictions = {}
        parity_matches = 0
        for color in ALLOWED_TARGET_COLORS:
            program = rule_source(color)
            source_path = f"private/rules/target_color_{color}.rkt"
            execution_path = f"private/racket/target_color_{color}.json"
            (out / source_path).write_text(program, encoding="utf-8")
            rule_row = {"parameters": {"target_color": color}, "source": program,
                        "sha256": _sha_bytes(program.encode()), "path": source_path,
                        "execution_path": execution_path}
            report["rules"].append(rule_row)
            # This one-cell known label is execution plumbing, outside every episode.
            canary = {"input": [[color]], "output": [[color]]}
            task = {"train": [canary], "test": [{"input": row["input"]} for row in execution_inputs]}
            receipt = verify_candidate(task, program, racket_path=chosen_racket,
                                       limits=Limits(max_pairs=64, max_output_bytes=4 * 1024 * 1024))
            execution = {"program": program, "program_sha256": rule_row["sha256"],
                         "canary": canary, "episode_input_order": "../execution_inputs.json",
                         "input_sha256": [row["input_sha256"] for row in execution_inputs],
                         "receipt": receipt}
            _write_json(out / execution_path, execution)
            _write_json(out / "report.json", report)
            if receipt.get("status") != "pass" or receipt.get("backend") != "racket":
                raise RuntimeError(f"Racket execution failed for target_color={color}: {receipt.get('error')}")
            predictions[color] = receipt["test_outputs"]
            for row, observed in zip(execution_inputs, predictions[color], strict=True):
                expected = python_crop(row["input"], color)
                if observed != expected:
                    _write_json(out / "private/parity_failure.json", {
                        "target_color": color, "input": row["input"],
                        "racket_output": observed, "python_mirror": expected})
                    raise RuntimeError("Executed Racket output disagrees with the independent Python crop")
                parity_matches += 1
        rotation_rows = []
        for episode_index, episode in enumerate(episodes):
            offset = episode_index * N_PAIRS
            per_color = {color: outputs[offset:offset + N_PAIRS] for color, outputs in predictions.items()}
            color = episode["parameters"]["target_color"]
            pairs = [{"input": grid, "output": per_color[color][index]}
                     for index, grid in enumerate(episode["inputs"])]
            rotations = [score_rotation(per_color, color, query_index) for query_index in range(N_PAIRS)]
            rotation_rows.extend(rotations)
            public_path = f"public/{episode['episode_id']}.json"
            private_path = f"private/episodes/{episode['episode_id']}.json"
            _write_json(out / public_path, public_challenge(pairs))
            private = {"episode_id": episode["episode_id"], "seed": episode["seed"],
                       "parameters": episode["parameters"], "program": episode["program"],
                       "program_sha256": _sha_bytes(episode["program"].encode()),
                       "source_sha256": report["source_sha256"],
                       "train": pairs[:N_TRAIN], "test": pairs[N_TRAIN:],
                       "profiles": episode["profiles"], "rotations": rotations,
                       "cross_setting_outputs": {str(k): v for k, v in per_color.items()},
                       "public_path": public_path,
                       "public_sha256": _sha_bytes((out / public_path).read_bytes())}
            _write_json(out / private_path, private)
            report["episodes"].append({
                "episode_id": episode["episode_id"], "seed": episode["seed"],
                "parameters": episode["parameters"], "public_path": public_path,
                "public_sha256": private["public_sha256"], "private_path": private_path,
                "private_sha256": _sha_bytes((out / private_path).read_bytes()),
            })
        witness_grid = execution_inputs[0]["input"]
        _write_json(out / "private/cross_setting_witness.json", {
            "input": witness_grid, "input_sha256": json_sha256(witness_grid),
            "episode_id": execution_inputs[0]["episode_id"], "pair_index": 0,
            "settings": [{"target_color": color, "bbox": list(bbox(witness_grid, color)),
                          "program": rule_source(color),
                          "program_sha256": _sha_bytes(rule_source(color).encode()),
                          "output": predictions[color][0]}
                         for color in ALLOWED_TARGET_COLORS],
            "pairwise_outputs_distinct": len({json_sha256(predictions[c][0]) for c in ALLOWED_TARGET_COLORS}) == 3,
        })
        rival_rows = [rival for rotation in rotation_rows for rival in rotation["rivals"]]
        report["summary"] = {
            "episodes": len(episodes), "episode_pairs": len(execution_inputs),
            "racket_rule_applications": len(execution_inputs) * len(ALLOWED_TARGET_COLORS),
            "racket_canaries": len(ALLOWED_TARGET_COLORS), "python_mirror_matches": parity_matches,
            "production_rival_checks": len(episodes) * 2, "query_rotations": len(rotation_rows),
            "rotation_rival_checks": len(rival_rows),
            "refuted_rotation_rivals": sum(row["status"] == "refuted_by_demonstrations" for row in rival_rows),
            "ambiguous_rotation_rivals": sum(row["status"] == "ambiguous_query" for row in rival_rows),
            "survived_rotation_rivals": sum(row["status"] == "survived_all" for row in rival_rows),
        }
        if _source_bindings() != report["source_sha256"]:
            raise RuntimeError("Bound source files changed during this execution")
        report["status"] = ("pass" if all(row["status"] == "refuted_by_demonstrations" for row in rival_rows)
                            else "ambiguity" if any(row["status"] == "ambiguous_query" for row in rival_rows)
                            else "survived_rivals")
    except Exception as exc:
        report["status"] = "error"
        report["error"] = {"type": type(exc).__name__, "message": str(exc)}
    _write_json(out / "report.json", report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="New evidence directory; existing paths are refused")
    parser.add_argument("--base-seed", type=int, default=20261019)
    parser.add_argument("--per-setting", type=int, default=1, help="Episodes per setting, bounded to 1..4")
    args = parser.parse_args(argv)
    try:
        report = run_evidence(args.out, base_seed=args.base_seed, per_setting=args.per_setting)
    except (ValueError, FileExistsError, OSError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}), file=sys.stderr)
        return 2
    print(json.dumps({"status": report["status"], "report": str(args.out / "report.json"),
                      "summary": report.get("summary"), "error": report.get("error")}, sort_keys=True))
    return 0 if report["status"] == "pass" else 2 if report["status"] == "error" else 1


if __name__ == "__main__":
    raise SystemExit(main())
