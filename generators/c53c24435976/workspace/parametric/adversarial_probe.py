#!/usr/bin/env python3
"""Bounded adversarial review for c53c24435976's command-chain family.

This is intentionally task-local and source-bound.  It attacks the declared
minimum lesson, sampler boundaries, stage dependency, certificates, and public
projection.  Finite success is evidence, not a uniqueness proof.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any, Callable

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


proto = _load(HERE / "prototype.py", "_c53_adversarial_prototype")
base = _load(HERE.parents[1] / "generator.py", "_c53_adversarial_base")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _rejects(label: str, episode: dict, mutate: Callable[[dict], None]) -> dict[str, str]:
    altered = copy.deepcopy(episode)
    mutate(altered)
    try:
        proto.certify(altered)
    except ValueError as exc:
        return {"attack": label, "status": "rejected", "error": str(exc)}
    raise AssertionError(f"certificate accepted forged case: {label}")


def _old_shortcut_coverage(grids: list[list[list[int]]], settings: dict[str, str]) -> bool:
    chosen = [proto.transform(grid, settings) for grid in grids]
    names = [name for name in proto.shortcut_outputs(grids[0], settings)
             if not name.startswith("stat_")]
    return all(any(proto.shortcut_outputs(grid, settings)[name] != expected
                   for grid, expected in zip(grids, chosen)) for name in names)


def _legacy_pair(seed: int) -> list[list[list[int]]]:
    first = [proto._candidate(seed, "demo", 0, offset) for offset in range(32)]
    second = [proto._candidate(seed, "demo", 1, offset) for offset in range(32)]
    for left in first:
        for right in second:
            pair = [left, right]
            if all(_old_shortcut_coverage(pair, setting) for setting in proto.SETTINGS):
                return pair
    raise AssertionError("legacy pair could not be reconstructed")


def run() -> dict[str, Any]:
    python_jobs = 0
    command_coverage = {"outer": set(), "inner": set()}
    dimensions: set[tuple[int, int]] = set()
    density = []
    shortcut_counts = []
    for seed in range(64):
        for setting in proto.SETTINGS:
            for demos in (2, 3, 6):
                episode = proto.generate(seed, setting, demos, 4)
                python_jobs += 1
                certificate = episode["certificate"]
                if certificate["survivors"] != [setting] or certificate["surviving_shortcuts"]:
                    raise AssertionError((seed, setting, demos, certificate))
                shortcut_counts.append(len(certificate["shortcut_refutations"]))
                for pair in episode["train"] + episode["test"]:
                    grid = pair["input"]
                    dimensions.add((len(grid), len(grid[0])))
                    command_coverage["outer"].add(grid[0][0])
                    command_coverage["inner"].add(
                        proto.selected_inner_command(proto.stage_one(grid)))
                    density.append(sum(value != 0 for row in grid for value in row) /
                                   (len(grid) * len(grid[0])))

    if command_coverage != {"outer": {1, 2, 3, 4}, "inner": {1, 2, 3, 4}}:
        raise AssertionError(command_coverage)
    if (30, 30) not in dimensions or min(dimensions) != (8, 9):
        raise AssertionError(sorted(dimensions))

    controls = []
    for seed in range(32):
        result = proto.crossed_controls(seed)
        inner_a, inner_b = result["vary_inner_command"]
        if ([[v != 0 for v in row] for row in inner_a] !=
                [[v != 0 for v in row] for row in inner_b]):
            raise AssertionError("inner control changed occupancy")
        if proto.selected_inner_command(proto.stage_one(inner_a)) == \
                proto.selected_inner_command(proto.stage_one(inner_b)):
            raise AssertionError("inner control did not change intermediate command")
        if proto.transform(inner_a, proto.CHAINED) == proto.transform(inner_b, proto.CHAINED):
            raise AssertionError("inner control did not change chained output")
        nuisance_a, nuisance_b = result["vary_canvas_and_position"]
        if proto.stage_one(nuisance_a) != proto.stage_one(nuisance_b):
            raise AssertionError("canvas/position nuisance changed stage one")
        if proto.transform(nuisance_a, proto.CHAINED) != proto.transform(nuisance_b, proto.CHAINED):
            raise AssertionError("canvas/position nuisance changed output")
        controls.append(seed)

    representative = proto.generate(59, proto.CHAINED, 3, 4)
    certificate_attacks = [
        _rejects("duplicate_input", representative,
                 lambda e: e["test"][0].update(input=copy.deepcopy(e["train"][0]["input"]))),
        _rejects("forged_demo_output", representative,
                 lambda e: e["train"][0].update(output=[[9]])),
        _rejects("wrong_program", representative,
                 lambda e: e.update(program_solution="(rule! g)")),
        _rejects("bool_cell", representative,
                 lambda e: e["test"][0]["input"][0].__setitem__(0, True)),
    ]

    from reviewer_support import public_challenge_bytes, public_challenge_id
    visible = proto.public_turn(representative, 0)
    public_bytes = public_challenge_bytes(visible)
    public_id = public_challenge_id(visible)
    private_change = copy.deepcopy(representative)
    private_change["settings"] = proto.DEFAULT
    private_change["program_solution"] = "private"
    private_change["test"][0]["output"] = [[9]]
    private_change["test"][1]["input"] = [[9]]
    if public_challenge_bytes(proto.public_turn(private_change, 0)) != public_bytes:
        raise AssertionError("private/future change altered first turn")
    public_change = copy.deepcopy(representative)
    public_change["test"][0]["input"][0][0] = (public_change["test"][0]["input"][0][0] % 4) + 1
    if public_challenge_bytes(proto.public_turn(public_change, 0)) == public_bytes:
        raise AssertionError("visible query change did not alter first turn")
    if any(token in public_bytes for token in (b"settings", b"program_solution", b"output\":[]")):
        raise AssertionError("private metadata leaked into public bytes")

    for code in (1, 2, 3, 4):
        grid = base.generate(0, 0, difficulty="medium", code=code)
        if grid[0][0] != code or base.self_check(grid):
            raise AssertionError(f"base override failed for code {code}")
    try:
        base.generate(0, 0, misspelled_axis=1)
    except ValueError:
        pass
    else:
        raise AssertionError("base accepted unknown override")

    legacy = _legacy_pair(0)
    legacy_outputs = [proto.transform(grid, proto.DEFAULT) for grid in legacy]
    last_command_predictions = [
        proto.shortcut_outputs(grid, proto.DEFAULT)["stat_last_command"] for grid in legacy]
    if last_command_predictions != legacy_outputs:
        raise AssertionError("expected reconstructed pre-repair last-command shortcut")
    current = proto.generate(0, proto.DEFAULT, 2, 4)
    current_refutation = current["certificate"]["shortcut_refutations"]["stat_last_command"]
    if not current_refutation:
        raise AssertionError("repaired lesson still admits last-command shortcut")

    racket_evaluations = 0
    racket_certificates = []
    counterfactual = None
    skip_source = (HERE / "counterfactual_skip_outer.rkt").read_text(encoding="utf-8")
    with proto.RacketRunner() as execute:
        racket_identity = execute.identity
        for seed in (0, 17, 73):
            for setting in proto.SETTINGS:
                episode = proto.generate(seed, setting, 2, 4)
                checked = proto.certify(episode, execute=execute)
                racket_evaluations += 2 * len(episode["train"]) + len(episode["test"])
                racket_certificates.append({"seed": seed, "settings": setting,
                                            "survivors": checked["survivors"]})
        witness_episode = proto.generate(73, proto.CHAINED, 2, 4)
        witness_grid = witness_episode["test"][-1]["input"]
        actual = execute(proto.program(proto.CHAINED), witness_grid)
        skipped = execute(skip_source, witness_grid)
        racket_evaluations += 2
        if actual == skipped:
            raise AssertionError("skip-A counterfactual did not change final output")
        counterfactual = {
            "input": witness_grid,
            "intermediate": proto.stage_one(witness_grid),
            "actual_output": actual,
            "skip_a_output": skipped,
            "actual_sha256": proto.digest(actual),
            "skip_a_sha256": proto.digest(skipped),
        }

    paths = [
        HERE.parents[1] / "generator.py",
        HERE / "prototype.py",
        HERE / "adapter.py",
        HERE / "promotion.json",
        HERE / "canonical.rkt",
        HERE / "chained.rkt",
        HERE / "counterfactual_skip_outer.rkt",
        HERE.parents[1] / "tests/test_generator_c53c24435976.py",
        HERE.parents[1] / "tests/test_parametric_command_chain.py",
    ]
    return {
        "schema": "c53c24435976-command-chain-adversarial-review-v1",
        "status": "passed",
        "task_id": proto.TASK_ID,
        "source_hashes": {path.relative_to(REPO).as_posix(): _sha(path) for path in paths},
        "base_repair": {
            "code_override_values": [1, 2, 3, 4],
            "unknown_override_rejected": True,
            "canonical_same-color_and_three-cell_inputs_now_accepted_by_self_check": True,
        },
        "python_sweep": {
            "jobs": python_jobs,
            "seeds": 64,
            "settings": len(proto.SETTINGS),
            "demo_counts": [2, 3, 6],
            "queries_per_job": 4,
            "dimensions": [list(value) for value in sorted(dimensions)],
            "outer_commands": sorted(command_coverage["outer"]),
            "inner_commands": sorted(command_coverage["inner"]),
            "density_min": min(density),
            "density_max": max(density),
            "shortcut_hypotheses_min": min(shortcut_counts),
            "shortcut_hypotheses_max": max(shortcut_counts),
        },
        "crossed_controls": {
            "seeds": controls,
            "vary_inner_at_fixed_occupancy": "changed selected command and final output",
            "vary_canvas_position_at_fixed_object": "preserved intermediate and final output",
        },
        "repaired_finding": {
            "description": "The original two-demo selector did not test frequency/rank rivals; seed 0 canonical admitted the last command-colored cell as a wrong selector.",
            "legacy_seed": 0,
            "legacy_setting": proto.DEFAULT,
            "legacy_demo_inputs": legacy,
            "legacy_input_sha256": [proto.digest(grid) for grid in legacy],
            "rival": "stat_last_command",
            "repair": "Added eight frequency/rank attacks to the certificate and selected the first two demonstrations only when all declared settings refute every attack.",
            "current_refuting_demo_indices": current_refutation,
        },
        "certificate_attacks": certificate_attacks,
        "public_projection": {
            "first_turn_sha256": hashlib.sha256(public_bytes).hexdigest(),
            "first_turn_id": public_id,
            "private_and_future_changes_invariant": True,
            "visible_query_change_detected": True,
        },
        "racket": {
            "identity": racket_identity,
            "certificate_jobs": racket_certificates,
            "evaluations": racket_evaluations,
            "skip_a_counterfactual": counterfactual,
        },
        "limits": [
            "Finite seeds and named shortcut classes do not prove universal uniqueness.",
            "The family remains pending owner source review, native qualification replay, and acceptance.",
            "No training admission or measured model-learning claim is made.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists() or args.out.is_symlink():
        raise FileExistsError(args.out)
    report = run()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"],
                      "python_jobs": report["python_sweep"]["jobs"],
                      "racket_evaluations": report["racket"]["evaluations"],
                      "repaired_rival": report["repaired_finding"]["rival"],
                      "out": str(args.out)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
