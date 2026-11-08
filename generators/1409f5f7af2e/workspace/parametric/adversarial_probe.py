#!/usr/bin/env python3
"""Bounded adversarial and protected-Racket probe for the 1409 family."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Iterable

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
TASK_ID = "1409f5f7af2e"

_SPEC = importlib.util.spec_from_file_location(
    "parametric_1409_adversarial_prototype", HERE / "prototype.py"
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load task-local prototype")
prototype = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(prototype)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _expect_rejection(name: str, action) -> dict:
    try:
        action()
    except (ValueError, KeyError, TypeError) as exc:
        return {
            "name": name,
            "passed": True,
            "rejected_with": type(exc).__name__,
            "message": str(exc),
        }
    raise AssertionError(f"{name} was accepted")


def _winner_facts(grid: list[list[int]]) -> dict:
    stage = prototype.stage_a(grid)
    targets = prototype._targets(grid)
    counts = [sum(col == candidate for _, col in targets) for candidate in range(len(grid[0]))]
    winner = prototype.busiest_activated_column(stage)
    endpoints = {
        endpoint
        for row, col in targets
        if col == winner
        for endpoint in ((row - 1, col), (row + 1, col))
    }
    off_chain = [
        [row, winner]
        for row in range(len(grid))
        if grid[row][winner] == 3 and (row, winner) not in endpoints
    ]
    usage: dict[tuple[int, int], int] = {}
    for row, col in targets:
        for endpoint in ((row - 1, col), (row + 1, col)):
            usage[endpoint] = usage.get(endpoint, 0) + 1
    return {
        "winner": winner,
        "winner_count": counts[winner],
        "second_count": max(count for col, count in enumerate(counts) if col != winner),
        "target_count": len(targets),
        "unique_winner": counts.count(counts[winner]) == 1,
        "shared_endpoint": any(count > 1 for count in usage.values()),
        "off_chain_green": off_chain,
    }


def _pure_python_sweep(seed_count: int) -> dict:
    demo_counts = (2, 3, 6)
    episodes_checked = 0
    inputs_checked = 0
    winners_by_shape: dict[str, set[int]] = {}
    query_digests: dict[tuple[int, int], list[str]] = {}
    prefix_rows: dict[tuple[int, str, int], dict] = {}

    for seed in range(seed_count):
        for demos in demo_counts:
            by_setting = {}
            for setting in prototype.SETTINGS:
                episode = prototype.generate(seed, setting, demos=demos, queries=4)
                certificate = episode["certificate"]
                if certificate["survivors"] != [setting] or certificate["shortcut_survivors"]:
                    raise AssertionError((seed, demos, setting, certificate))
                by_setting[setting["endpoint_treatment"]] = episode
                episodes_checked += 1

                pairs = episode["train"] + episode["test"]
                if len({prototype.digest(pair["input"]) for pair in pairs}) != len(pairs):
                    raise AssertionError("duplicate inputs escaped certificate")
                for pair in pairs:
                    facts = _winner_facts(pair["input"])
                    if not facts["unique_winner"]:
                        raise AssertionError("tie escaped admitted grammar")
                    if not facts["shared_endpoint"]:
                        raise AssertionError("scene lacks a shared-endpoint target chain")
                    if not facts["off_chain_green"]:
                        raise AssertionError("scene lacks an off-chain winner-column green")
                    if not 3 <= facts["target_count"] <= 6:
                        raise AssertionError(f"target count out of scope: {facts}")
                    inputs_checked += 1

                for pair in episode["test"]:
                    shape = f"{len(pair['input'])}x{len(pair['input'][0])}"
                    winners_by_shape.setdefault(shape, set()).add(
                        prototype.busiest_activated_column(prototype.stage_a(pair["input"]))
                    )
                query_digests[(seed, demos)] = [
                    prototype.digest(pair["input"]) for pair in episode["test"]
                ]
                prefix_rows[(seed, setting["endpoint_treatment"], demos)] = episode

            preserve = by_setting["preserve"]
            alternate = by_setting["highlight_busiest"]
            preserve_inputs = [pair["input"] for pair in preserve["train"] + preserve["test"]]
            alternate_inputs = [pair["input"] for pair in alternate["train"] + alternate["test"]]
            if preserve_inputs != alternate_inputs:
                raise AssertionError("matched-input contract drifted across settings")
            if any(
                left["output"] == right["output"]
                for left, right in zip(
                    preserve["train"] + preserve["test"],
                    alternate["train"] + alternate["test"],
                )
            ):
                raise AssertionError("a pair does not distinguish the settings")

        for setting in prototype.SETTINGS:
            short = prefix_rows[(seed, setting["endpoint_treatment"], 2)]
            long = prefix_rows[(seed, setting["endpoint_treatment"], 6)]
            if short["train"] != long["train"][:2] or short["test"] != long["test"]:
                raise AssertionError("count prefix/query independence drifted")
        if query_digests[(seed, 2)] != query_digests[(seed, 6)]:
            raise AssertionError("queries depend on demonstration count")

    required_movement = min(4, seed_count)
    if any(len(columns) < required_movement for columns in winners_by_shape.values()):
        raise AssertionError(f"insufficient winner movement: {winners_by_shape}")

    stress = prototype.generate(
        43,
        {"endpoint_treatment": "highlight_busiest"},
        demos=2,
        queries=4,
    )["test"][-1]["input"]
    occupied = [
        (row, col)
        for row, values in enumerate(stress)
        for col, value in enumerate(values)
        if value != 0
    ]
    boundary = {
        "shape": [len(stress), len(stress[0])],
        "nonzero_cells": len(occupied),
        "touches_rows": [min(row for row, _ in occupied), max(row for row, _ in occupied)],
        "touches_columns": [min(col for _, col in occupied), max(col for _, col in occupied)],
    }
    if boundary["shape"] != [30, 30] or boundary["touches_rows"] != [0, 29] or boundary["touches_columns"] != [0, 29]:
        raise AssertionError(boundary)

    return {
        "name": "python_seed_count_geometry_sweep",
        "passed": True,
        "seeds": seed_count,
        "settings": len(prototype.SETTINGS),
        "demo_counts": list(demo_counts),
        "episodes_checked": episodes_checked,
        "inputs_checked": inputs_checked,
        "queries_per_episode": 4,
        "winner_columns_by_query_shape": {
            shape: sorted(columns) for shape, columns in sorted(winners_by_shape.items())
        },
        "stress_boundary": boundary,
    }


def _certificate_attacks() -> dict:
    setting = {"endpoint_treatment": "highlight_busiest"}
    original = prototype.generate(13, setting, demos=2, queries=4)
    checks = []

    tampered = copy.deepcopy(original)
    tampered["program_solution"] = prototype.program(prototype.DEFAULT)
    checks.append(_expect_rejection("program_setting_mismatch", lambda: prototype.certify(tampered)))

    tampered = copy.deepcopy(original)
    tampered["train"][0]["output"][0][0] = 9
    checks.append(_expect_rejection("corrupted_demonstration_label", lambda: prototype.certify(tampered)))

    tampered = copy.deepcopy(original)
    tampered["test"][1]["input"] = copy.deepcopy(tampered["test"][0]["input"])
    checks.append(_expect_rejection("duplicate_query_input", lambda: prototype.certify(tampered)))

    tampered = copy.deepcopy(original)
    tampered["test"] = tampered["test"][:3]
    checks.append(_expect_rejection("missing_fourth_query", lambda: prototype.certify(tampered)))

    tampered = copy.deepcopy(original)
    tampered["train"][0]["input"][0][0] = True
    checks.append(_expect_rejection("boolean_grid_cell", lambda: prototype.certify(tampered)))

    tampered = copy.deepcopy(original)
    tampered["settings"] = {"endpoint_treatment": "highlight_busiest", "extra": "forged"}
    checks.append(_expect_rejection("extra_setting_key", lambda: prototype.certify(tampered)))

    checks.append(_expect_rejection(
        "boolean_seed",
        lambda: prototype.generate(True, setting, demos=2, queries=4),
    ))
    checks.append(_expect_rejection(
        "boolean_demo_count",
        lambda: prototype.generate(0, setting, demos=True, queries=4),
    ))

    forged = copy.deepcopy(original)
    forged["certificate"] = {
        "survivors": [prototype.DEFAULT],
        "shortcut_survivors": ["dimension_lookup"],
    }
    recomputed = prototype.certify(forged)
    if recomputed["survivors"] != [setting] or recomputed["shortcut_survivors"]:
        raise AssertionError("authored certificate was trusted instead of recomputed")
    checks.append({
        "name": "forged_embedded_certificate_recomputed",
        "passed": True,
        "survivors": recomputed["survivors"],
    })

    return {
        "name": "certificate_and_type_rejection",
        "passed": True,
        "checks": checks,
    }


def _public_projection_attacks() -> dict:
    turns_checked = 0
    private_mutations = 0
    visible_change_controls = 0
    for seed in (0, 43):
        for demos in (2, 6):
            for setting in prototype.SETTINGS:
                episode = prototype.generate(seed, setting, demos=demos, queries=4)
                for turn in range(4):
                    visible = prototype.public_turn(episode, turn)
                    if set(visible) != {"train", "test"} or len(visible["test"]) != 1:
                        raise AssertionError("public turn shape drifted")
                    if set(visible["test"][0]) != {"input"}:
                        raise AssertionError("query output leaked")
                    body = prototype.public_challenge_bytes(visible)
                    identifier = prototype.public_challenge_id(visible)
                    for forbidden in (b"settings", b"program_solution", b"certificate", b"seed"):
                        if forbidden in body:
                            raise AssertionError(f"private key leaked: {forbidden!r}")

                    changed = copy.deepcopy(episode)
                    changed["settings"] = prototype.DEFAULT
                    changed["program_solution"] = "forged-private-program"
                    changed["certificate"] = {"forged": True}
                    changed["seed"] = -999
                    for pair in changed["test"]:
                        pair["output"] = [[9]]
                    for future in range(4):
                        if future != turn:
                            changed["test"][future]["input"] = [[9]]
                    changed_visible = prototype.public_turn(changed, turn)
                    if prototype.public_challenge_bytes(changed_visible) != body:
                        raise AssertionError("private/future mutation changed public bytes")
                    if prototype.public_challenge_id(changed_visible) != identifier:
                        raise AssertionError("private/future mutation changed public id")
                    private_mutations += 1

                    changed = copy.deepcopy(episode)
                    current = changed["test"][turn]["input"]
                    current[0][0] = 9 if current[0][0] != 9 else 8
                    changed_visible = prototype.public_turn(changed, turn)
                    if prototype.public_challenge_bytes(changed_visible) == body:
                        raise AssertionError("visible query mutation did not change bytes")
                    if prototype.public_challenge_id(changed_visible) == identifier:
                        raise AssertionError("visible query mutation did not change id")
                    visible_change_controls += 1
                    turns_checked += 1

    return {
        "name": "sequential_public_private_projection",
        "passed": True,
        "turns_checked": turns_checked,
        "private_future_mutations": private_mutations,
        "visible_change_controls": visible_change_controls,
        "queries_exposed_per_turn": 1,
        "total_count_hint_exposed": False,
    }


def _protected_racket_probe() -> dict:
    seeds = (0, 43, 199)
    demo_counts = (2, 6)
    episodes_checked = 0
    labels_executed = 0
    with prototype.RacketRunner() as runner:
        runtime_identity = dict(runner.identity)

        def execute(source, grid):
            nonlocal labels_executed
            labels_executed += 1
            return runner(source, grid)

        for seed in seeds:
            for demos in demo_counts:
                for setting in prototype.SETTINGS:
                    episode = prototype.generate(seed, setting, demos=demos, queries=4)
                    certificate = prototype.certify(episode, execute=execute)
                    if not certificate["racket_checked"] or certificate["shortcut_survivors"]:
                        raise AssertionError(certificate)
                    episodes_checked += 1

    if runtime_identity.get("backend") != "racket" or runtime_identity.get("protected") is not True:
        raise AssertionError(runtime_identity)
    return {
        "name": "protected_racket_minimum_and_maximum_lessons",
        "passed": True,
        "seeds": list(seeds),
        "demo_counts": list(demo_counts),
        "settings": len(prototype.SETTINGS),
        "episodes_checked": episodes_checked,
        "labels_executed": labels_executed,
        "runtime_identity": runtime_identity,
    }


def run_probe(seed_count: int = 64) -> dict:
    if type(seed_count) is not int or seed_count < 1:
        raise ValueError("seed_count must be a positive exact integer")
    checks = [
        _pure_python_sweep(seed_count),
        _certificate_attacks(),
        _public_projection_attacks(),
        _protected_racket_probe(),
    ]
    source_paths = [
        REPO / "generators" / TASK_ID / "generator.py",
        HERE / "prototype.py",
        HERE / "adapter.py",
        HERE / "promotion.json",
        HERE / "canonical.rkt",
        HERE / "highlight_busiest.rkt",
        HERE / "adversarial_probe.py",
        REPO / "generators" / TASK_ID / "tests" / "test_generator_1409f5f7af2e.py",
        REPO / "generators" / TASK_ID / "tests" / "test_parametric_busiest_column.py",
    ]
    return {
        "schema": "arcpuzzles-parametric-bounded-adversarial-v1",
        "task_id": TASK_ID,
        "status": "passed",
        "checks": checks,
        "scope": [
            "minimum/ordinary/maximum demonstration counts over fresh seeds",
            "fixed-size selector movement and ten-plus finite shortcut families",
            "shared-endpoint, rank, nonlocal, diagonal and endpoint-only controls",
            "strict malformed-count/type/program/duplicate/certificate rejection",
            "sequential one-query public projection under private/future mutations",
            "protected-Racket replay for both settings at two and six demonstrations",
        ],
        "source_sha256": {
            path.relative_to(REPO).as_posix(): _sha256(path) for path in source_paths
        },
        "remaining_failures": [],
        "finite_limit": (
            "The bounded seeds and named rivals do not prove universal uniqueness or "
            "learning benefit; owner source review, native qualification and acceptance remain pending."
        ),
    }


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=64)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(list(argv) if argv is not None else None)
    report = run_probe(args.seeds)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out is None:
        print(text, end="")
    else:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
