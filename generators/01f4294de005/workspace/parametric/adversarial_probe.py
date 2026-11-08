#!/usr/bin/env python3
"""Bounded adversarial review for the 01f4294de005 native family."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile

from arcpuzzles.parametric_worker import evaluate_contract
from reviewer_support import find_root, load_selected_generator

HERE = Path(__file__).resolve().parent
TASK_ID = "01f4294de005"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _expect_rejection(callable_):
    try:
        callable_()
    except (TypeError, ValueError):
        return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--seeds", type=int, default=128)
    args = parser.parse_args()
    if args.out.exists() or args.out.is_symlink():
        raise FileExistsError(args.out)
    if not 1 <= args.seeds <= 1024:
        raise ValueError("--seeds must be in 1..1024")

    root = find_root(__file__)
    prototype = _load(HERE / "prototype.py", "_size_marker_echo_adversarial")
    contract = json.loads((HERE / "promotion.json").read_text())
    base, _, _ = load_selected_generator(TASK_ID, root=root)

    rival_survivals = {name: [] for name in prototype.RIVAL_NAMES}
    input_mismatches = []
    duplicate_episodes = []
    source_slots = {size: set() for size in range(1, 5)}
    marker_slots = {size: set() for size in range(1, 5)}
    dimensions = set()
    labelled_pairs = 0

    for seed in range(args.seeds):
        direct = prototype.generate(seed, {"echo_mode": "none"}, 2, 4)
        echo = prototype.generate(seed, {"echo_mode": "matching_marker"}, 2, 4)
        direct_inputs = [pair["input"] for split in ("train", "test") for pair in direct[split]]
        echo_inputs = [pair["input"] for split in ("train", "test") for pair in echo[split]]
        if direct_inputs != echo_inputs:
            input_mismatches.append(seed)
        encoded = [json.dumps(grid, separators=(",", ":")) for grid in direct_inputs]
        if len(encoded) != len(set(encoded)):
            duplicate_episodes.append(seed)
        labelled_pairs += len(direct_inputs) * 2
        for grid in direct_inputs:
            dimensions.add((len(grid), len(grid[0])))
            prototype.analyze_scene(grid)
        for name in prototype.RIVAL_NAMES:
            if all(
                prototype.apply_rival(pair["input"], name) == pair["output"]
                for pair in echo["train"]
            ):
                rival_survivals[name].append(seed)

        facts = prototype.analyze_scene(echo["train"][0]["input"])
        marker_by_color = {
            marker["color"]: next(iter(marker["cells"])) for marker in facts["markers"]
        }
        for component in facts["orange_components"]:
            size = len(component)
            if size <= 4:
                source_slots[size].add(min(component))
                marker_slots[size].add(marker_by_color[facts["palette"][size - 1]])

    row1_contacts = []
    for difficulty in ("easy", "medium", "hard"):
        for seed in range(96):
            grid = base.generate(90_000 + seed, seed, difficulty=difficulty)
            if base.self_check(grid):
                raise AssertionError(f"base self-check failed at {difficulty=} {seed=}")
            row1_contacts.append(any(value != 0 for value in grid[1]))

    strict_attacks = {
        "bool_seed": _expect_rejection(lambda: prototype.generate(True, {"echo_mode": "none"}, 2, 4)),
        "low_demo_count": _expect_rejection(lambda: prototype.generate(0, {"echo_mode": "none"}, 1, 4)),
        "high_demo_count": _expect_rejection(lambda: prototype.generate(0, {"echo_mode": "none"}, 7, 4)),
        "high_query_count": _expect_rejection(lambda: prototype.generate(0, {"echo_mode": "none"}, 2, 5)),
        "extra_setting": _expect_rejection(lambda: prototype.generate(0, {"echo_mode": "none", "x": 1}, 2, 4)),
        "unknown_setting": _expect_rejection(lambda: prototype.generate(0, {"echo_mode": "nearest"}, 2, 4)),
        "base_unknown_override": _expect_rejection(lambda: base.generate(0, 0, typo_axis=1)),
        "base_bool_count": _expect_rejection(lambda: base.generate(0, 0, n_blobs=True)),
    }
    malformed = prototype.sample_input(0, "train", 0)
    malformed[1][0] = False
    strict_attacks["boolean_cell"] = _expect_rejection(lambda: prototype.apply_rule(malformed, "none"))

    jobs = [
        {"seed": seed, "settings": {"echo_mode": mode}, "demos": demos, "queries": 4}
        for seed in (0, 17, 73)
        for demos in (2, 3, 6)
        for mode in ("none", "matching_marker")
    ]
    executed = evaluate_contract(root, TASK_ID, contract, jobs)

    failures = {
        "input_mismatch_seeds": input_mismatches,
        "duplicate_episode_seeds": duplicate_episodes,
        "rival_survivals": {name: values for name, values in rival_survivals.items() if values},
        "strict_attacks_not_rejected": [name for name, passed in strict_attacks.items() if not passed],
    }
    if any(failures.values()):
        raise AssertionError(json.dumps(failures, indent=2, sort_keys=True))
    if not any(row1_contacts) or all(row1_contacts):
        raise AssertionError("base row-one morphology did not vary")
    if any(len(source_slots[size]) < 4 or len(marker_slots[size]) < 4 for size in source_slots):
        raise AssertionError("crossed-control positions did not vary enough")

    report = {
        "schema": "arcpuzzles-01f4294de005-adversarial-v1",
        "task_id": TASK_ID,
        "status": "passed",
        "seeds": args.seeds,
        "minimum_demo_episodes": args.seeds * 2,
        "labelled_pairs_checked": labelled_pairs,
        "rival_survivals": {name: len(values) for name, values in rival_survivals.items()},
        "crossed_controls": {
            "source_positions_by_size": {str(k): len(v) for k, v in source_slots.items()},
            "marker_positions_by_size": {str(k): len(v) for k, v in marker_slots.items()},
            "meaning": "At fixed train dimensions, each area occupied varied source and marker positions; nuisance position changed while the size->legend intermediate stayed fixed.",
        },
        "dimensions": [list(item) for item in sorted(dimensions)],
        "base_row1": {
            "draws": len(row1_contacts),
            "contact": sum(row1_contacts),
            "blank": len(row1_contacts) - sum(row1_contacts),
        },
        "strict_rejections": strict_attacks,
        "protected_racket": {
            "jobs": len(jobs),
            "evaluations": executed["racket_evaluations"],
            "identity": executed["racket"],
            "survivors": [row["survivors"] for row in executed["checks"]],
        },
        "limits": [
            "Finite rivals and seeds do not prove universal uniqueness.",
            "The causal interpretation is reviewer-authored; owner review remains required.",
        ],
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix="01f-adversarial-", dir=args.out.parent))
    try:
        (temp / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        temp.rename(args.out)
    except BaseException:
        shutil.rmtree(temp, ignore_errors=True)
        raise
    print(json.dumps({"out": str(args.out), "status": "passed", "jobs": len(jobs), "seeds": args.seeds}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
