"""Bounded adversarial self-audit for the commanded-ray/border-hook family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import time

TASK_ID = "e8504fcc371b"
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def _load_prototype():
    path = HERE / "prototype.py"
    spec = importlib.util.spec_from_file_location("_audit_e850_hook", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _candidate_output(proto, grid, *, hook_length: int, clockwise: bool = True):
    facts = proto.scene_facts(grid)
    output = [list(row) for row in grid]
    for row, col in proto.ray_cells(grid):
        if output[row][col] == 0:
            output[row][col] = facts["seed_color"]
    border = proto.perimeter(grid)
    endpoint_index = border.index(tuple(facts["endpoint"]))
    direction = 1 if clockwise else -1
    for offset in range(1, hook_length + 1):
        row, col = border[(endpoint_index + direction * offset) % len(border)]
        if output[row][col] == 0:
            output[row][col] = facts["seed_color"]
    return output


def run(output: Path) -> int:
    if output.exists() or output.is_symlink():
        raise FileExistsError(output)
    started = time.monotonic()
    proto = _load_prototype()
    contract = json.loads((HERE / "promotion.json").read_text())
    jobs = [
        {"seed": seed, "settings": {"trail_mode": mode}, "demos": demos, "queries": 4}
        for seed in (0, 17)
        for demos in (2, 3, 6)
        for mode in proto.MODES
    ]

    from arcpuzzles.parametric_worker import evaluate_contract

    native = evaluate_contract(ROOT, TASK_ID, contract, jobs)
    matched_inputs = 0
    first_turn_checks = 0
    straight_only_refutations = 0
    fixed_length_refutations = 0
    counterclockwise_refutations = 0
    stress = []
    for seed in (0, 17, 31):
        for demos in (2, 3, 6):
            episodes = {
                mode: proto.generate(seed, {"trail_mode": mode}, demos, 4)
                for mode in proto.MODES
            }
            for split in ("train", "test"):
                left = [pair["input"] for pair in episodes[proto.MODES[0]][split]]
                right = [pair["input"] for pair in episodes[proto.MODES[1]][split]]
                if left != right:
                    raise ValueError("hidden setting changed input sampling")
            matched_inputs += 1

            one = proto.generate(seed, {"trail_mode": "border_hook"}, demos, 1)
            if one["test"] != episodes["border_hook"]["test"][:1]:
                raise ValueError("one-query prefix differs from four-query generation")
            first_turn_checks += 1

            hooked = episodes["border_hook"]["train"]
            ray_lengths = [proto.intermediate_value(pair["input"])["ray_length"] for pair in hooked]
            if len(set(ray_lengths[:2])) != 2:
                raise ValueError("two demonstrations leave a fixed hook length viable")
            for pair in hooked:
                straight = proto.transform(pair["input"], {"trail_mode": "straight_to_border"})
                if straight == pair["output"]:
                    raise ValueError("straight-only shortcut survived a hooked lesson")
                straight_only_refutations += 1
            for fixed in (1, 2):
                if all(
                    _candidate_output(proto, pair["input"], hook_length=fixed) == pair["output"]
                    for pair in hooked
                ):
                    raise ValueError(f"fixed hook length {fixed} fits every lesson")
                fixed_length_refutations += 1
            if all(
                _candidate_output(
                    proto,
                    pair["input"],
                    hook_length=proto.intermediate_value(pair["input"])["ray_length"],
                    clockwise=False,
                ) == pair["output"]
                for pair in hooked
            ):
                raise ValueError("counterclockwise shortcut fits every lesson")
            counterclockwise_refutations += 1

        pair = proto.generate(seed, {"trail_mode": "border_hook"}, 3, 4)["test"][-1]
        changed = proto.changed_cells(pair["input"], pair["output"])
        rows = [row for row, _ in changed]
        cols = [col for _, col in changed]
        border_nonzero = sum(
            pair["output"][row][col] != 0
            for row in range(30)
            for col in range(30)
            if row in (0, 29) or col in (0, 29)
        )
        record = {
            "seed": seed,
            "shape": [30, 30],
            "input_nonzero": sum(cell != 0 for row in pair["input"] for cell in row),
            "changed_cells": len(changed),
            "changed_bbox": [min(rows), min(cols), max(rows), max(cols)],
            "border_nonzero": border_nonzero,
            "intermediate": proto.intermediate_value(pair["input"]),
        }
        if (
            record["input_nonzero"] != 2
            or record["changed_cells"] < 40
            or record["changed_bbox"][2] - record["changed_bbox"][0] < 20
            or record["changed_bbox"][3] - record["changed_bbox"][1] < 20
            or border_nonzero < 20
        ):
            raise ValueError(f"30x30 stress case lacks global output extent: {record}")
        stress.append(record)

    with proto.RacketEngine() as engine:
        causal_episode = proto.generate(7, {"trail_mode": "border_hook"}, 3, 4)
        pair = next(
            pair
            for pair in causal_episode["test"]
            if proto.intermediate_value(pair["input"])["ray_length"] > 2
        )
        actual = engine.apply(proto.program({"trail_mode": "border_hook"}), pair["input"])
        counterfactual = engine.apply(proto.counterfactual_program(1), pair["input"])
        if actual != pair["output"] or actual == counterfactual:
            raise ValueError("protected wrong-intermediate witness did not change the final output")
        causal = {
            "intermediate": proto.intermediate_value(pair["input"]),
            "actual_changed_cells": len(proto.changed_cells(pair["input"], actual)),
            "counterfactual_changed_cells": len(proto.changed_cells(pair["input"], counterfactual)),
            "changed": True,
        }

    source_names = (
        "prototype.py",
        "adapter.py",
        "promotion.json",
        "canonical.rkt",
        "border_hook.rkt",
        "probe.py",
    )
    sources = {
        path.relative_to(ROOT).as_posix(): _sha(path)
        for path in [HERE / name for name in source_names]
    }
    report = {
        "schema": "arcpuzzles-border-hook-bounded-audit-v1",
        "task_id": TASK_ID,
        "status": "passed",
        "scope": "Finite author self-audit; not owner qualification, acceptance, or training admission.",
        "native_jobs": len(native["checks"]),
        "native_racket_evaluations": native["racket_evaluations"],
        "native_checks": native["checks"],
        "racket": native["racket"],
        "matched_input_checks": matched_inputs,
        "first_turn_prefix_checks": first_turn_checks,
        "straight_only_refutations": straight_only_refutations,
        "fixed_length_refutations": fixed_length_refutations,
        "counterclockwise_refutations": counterclockwise_refutations,
        "stress_30x30": stress,
        "causal_wrong_intermediate": causal,
        "source_sha256": sources,
        "elapsed_seconds": round(time.monotonic() - started, 4),
        "limitations": [
            "The finite settings pool and explicit shortcuts are not a proof against all conceivable rules.",
            "The canonical source requires the deliberately narrow two-marker input domain.",
            "Seeds 0, 17 and 31 plus demo counts 2, 3 and 6 are bounded observations.",
            "Owner source review, native acceptance and training admission remain separate.",
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    print(
        json.dumps(
            {
                "status": report["status"],
                "native_jobs": report["native_jobs"],
                "racket_evaluations": report["native_racket_evaluations"],
                "elapsed_seconds": report["elapsed_seconds"],
            }
        )
    )
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    raise SystemExit(run(parser.parse_args().out))
