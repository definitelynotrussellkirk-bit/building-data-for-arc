#!/usr/bin/env python3
"""Bounded adversarial and protected-Racket probe for the 4dd0 family."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Callable, Iterable

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
TASK_ID = "4dd0b3ed33ee"

_SPEC = importlib.util.spec_from_file_location(
    "parametric_4dd0_adversarial_prototype", HERE / "prototype.py"
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load task-local prototype")
prototype = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(prototype)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _expect_rejection(name: str, action: Callable[[], object]) -> dict:
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


def _scene_facts(grid: list[list[int]]) -> dict:
    summary = prototype.scene_summary(grid)
    components = summary["components"]
    matches = [components[index] for index in summary["matching_indices"]]
    areas = [int(component["area"]) for component in matches]
    first = components[summary["first_match_index"]]
    largest = components[summary["largest_area_match_index"]]
    return {
        "header_count": summary["header_count"],
        "matching_count": summary["matching_count"],
        "unique_largest_match": areas.count(max(areas)) == 1,
        "first_match_index": summary["first_match_index"],
        "largest_match_index": summary["largest_area_match_index"],
        "largest_match_rank": summary["matching_indices"].index(
            summary["largest_area_match_index"]
        ),
        "largest_match_color": largest["color"],
        "largest_match_top": largest["bbox"][0],
        "first_match_top": first["bbox"][0],
        "largest_overall_is_wrong_topology": (
            summary["largest_overall_index"] not in summary["matching_indices"]
        ),
        "largest_boundary_is_distinct": (
            summary["largest_boundary_match_index"]
            != summary["largest_area_match_index"]
        ),
        "smallest_is_distinct": (
            summary["smallest_area_match_index"] != summary["first_match_index"]
        ),
        "has_multi_cell_hole_match": any(
            int(component["missing_cells"]) > int(summary["header_count"])
            for component in matches
        ),
        "four_vs_eight_control": any(
            int(component["holes4"]) != int(component["holes8"])
            for component in matches
        ),
    }


def _pure_python_sweep(seed_count: int) -> dict:
    demo_counts = (2, 3, 6)
    episodes_checked = 0
    inputs_checked = 0
    rank_by_demo_shape: dict[str, set[int]] = {}
    color_by_demo_shape: dict[str, set[int]] = {}
    vertical_relations: set[str] = set()
    rows: dict[tuple[int, str, int], dict] = {}

    for seed in range(seed_count):
        for demos in demo_counts:
            by_setting: dict[str, dict] = {}
            for setting in prototype.SETTINGS:
                episode = prototype.generate(seed, setting, demos=demos, queries=4)
                certificate = episode["certificate"]
                if certificate["survivors"] != [setting] or certificate["shortcut_survivors"]:
                    raise AssertionError((seed, demos, setting, certificate))
                by_setting[setting["match_selector"]] = episode
                rows[(seed, setting["match_selector"], demos)] = episode
                episodes_checked += 1

                pairs = episode["train"] + episode["test"]
                if len({prototype.digest(pair["input"]) for pair in pairs}) != len(pairs):
                    raise AssertionError("duplicate inputs escaped certificate")
                for pair in pairs:
                    facts = _scene_facts(pair["input"])
                    if facts["matching_count"] != 4:
                        raise AssertionError(facts)
                    for required in (
                        "unique_largest_match",
                        "largest_overall_is_wrong_topology",
                        "largest_boundary_is_distinct",
                        "smallest_is_distinct",
                        "has_multi_cell_hole_match",
                    ):
                        if not facts[required]:
                            raise AssertionError((required, facts))
                    if prototype.transform(pair["input"], prototype.DEFAULT) == prototype.transform(
                        pair["input"], {"match_selector": "largest_area"}
                    ):
                        raise AssertionError("input does not distinguish the two settings")
                    inputs_checked += 1

                for index, pair in enumerate(episode["train"][:2]):
                    shape = f"demo{index}:{len(pair['input'])}x{len(pair['input'][0])}"
                    facts = _scene_facts(pair["input"])
                    rank_by_demo_shape.setdefault(shape, set()).add(facts["largest_match_rank"])
                    color_by_demo_shape.setdefault(shape, set()).add(facts["largest_match_color"])
                    vertical_relations.add(
                        "same_shelf"
                        if facts["largest_match_top"] == facts["first_match_top"]
                        else "different_shelf"
                    )

            canonical = by_setting["first"]
            alternate = by_setting["largest_area"]
            canonical_inputs = [
                pair["input"] for pair in canonical["train"] + canonical["test"]
            ]
            alternate_inputs = [
                pair["input"] for pair in alternate["train"] + alternate["test"]
            ]
            if canonical_inputs != alternate_inputs:
                raise AssertionError("matched-input contract drifted across settings")

        for setting in prototype.SETTINGS:
            short = rows[(seed, setting["match_selector"], 2)]
            long = rows[(seed, setting["match_selector"], 6)]
            if short["train"] != long["train"][:2] or short["test"] != long["test"]:
                raise AssertionError("count prefix/query independence drifted")

    if vertical_relations != {"same_shelf", "different_shelf"}:
        raise AssertionError(f"vertical shelf cue survived: {vertical_relations}")
    if any(len(values) < 2 for values in rank_by_demo_shape.values()):
        raise AssertionError(f"fixed-size rank cue survived: {rank_by_demo_shape}")
    if any(len(values) < 2 for values in color_by_demo_shape.values()):
        raise AssertionError(f"fixed-size colour cue survived: {color_by_demo_shape}")

    stress = prototype.generate(
        43,
        {"match_selector": "largest_area"},
        demos=2,
        queries=4,
    )["test"][-1]["input"]
    occupied = [
        (row, col)
        for row, values in enumerate(stress[1:], start=1)
        for col, value in enumerate(values)
        if value != 0
    ]
    boundary = {
        "shape": [len(stress), len(stress[0])],
        "nonzero_body_cells": len(occupied),
        "contacts": sorted(prototype.boundary_contacts(stress)),
    }
    if boundary["shape"] != [30, 30] or boundary["contacts"] != [
        "bottom",
        "left",
        "right",
        "top",
    ]:
        raise AssertionError(boundary)
    if boundary["nonzero_body_cells"] < 120:
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
        "finite_shortcuts_refuted": len(prototype.SHORTCUTS),
        "largest_match_ranks_by_fixed_demo_shape": {
            key: sorted(values) for key, values in sorted(rank_by_demo_shape.items())
        },
        "largest_match_colours_by_fixed_demo_shape": {
            key: sorted(values) for key, values in sorted(color_by_demo_shape.items())
        },
        "vertical_relations": sorted(vertical_relations),
        "stress_boundary": boundary,
    }


def _certificate_attacks() -> dict:
    setting = {"match_selector": "largest_area"}
    original = prototype.generate(13, setting, demos=2, queries=4)
    checks = []

    tampered = copy.deepcopy(original)
    tampered["program_solution"] = prototype.program(prototype.DEFAULT)
    checks.append(
        _expect_rejection(
            "program_setting_mismatch", lambda: prototype.certify(tampered)
        )
    )

    tampered = copy.deepcopy(original)
    tampered["program_sha256"] = "0" * 64
    checks.append(
        _expect_rejection("stale_program_hash", lambda: prototype.certify(tampered))
    )

    tampered = copy.deepcopy(original)
    tampered["train"][0]["output"][0][0] = 9
    checks.append(
        _expect_rejection(
            "corrupted_demonstration_label", lambda: prototype.certify(tampered)
        )
    )

    tampered = copy.deepcopy(original)
    tampered["test"][1]["input"] = copy.deepcopy(tampered["test"][0]["input"])
    checks.append(
        _expect_rejection("duplicate_query_input", lambda: prototype.certify(tampered))
    )

    tampered = copy.deepcopy(original)
    tampered["test"] = tampered["test"][:3]
    checks.append(
        _expect_rejection("missing_fourth_query", lambda: prototype.certify(tampered))
    )

    tampered = copy.deepcopy(original)
    tampered["train"][0]["input"][0][0] = True
    checks.append(
        _expect_rejection("boolean_grid_cell", lambda: prototype.certify(tampered))
    )

    tampered = copy.deepcopy(original)
    tampered["train"][0]["input"][0].pop()
    checks.append(_expect_rejection("ragged_grid", lambda: prototype.certify(tampered)))

    tampered = copy.deepcopy(original)
    tampered["train"][0]["private"] = "leak"
    checks.append(
        _expect_rejection("extra_pair_key", lambda: prototype.certify(tampered))
    )

    tampered = copy.deepcopy(original)
    tampered["settings"] = {"match_selector": "largest_area", "extra": "forged"}
    checks.append(
        _expect_rejection("extra_setting_key", lambda: prototype.certify(tampered))
    )

    checks.append(
        _expect_rejection(
            "boolean_seed",
            lambda: prototype.generate(True, setting, demos=2, queries=4),
        )
    )
    checks.append(
        _expect_rejection(
            "boolean_demo_count",
            lambda: prototype.generate(0, setting, demos=True, queries=4),
        )
    )
    checks.append(
        _expect_rejection(
            "boolean_query_count",
            lambda: prototype.generate(0, setting, demos=2, queries=True),
        )
    )

    forged = copy.deepcopy(original)
    forged["certificate"] = {
        "survivors": [prototype.DEFAULT],
        "shortcut_survivors": ["top_shelf_largest_match"],
    }
    recomputed = prototype.certify(forged)
    if recomputed["survivors"] != [setting] or recomputed["shortcut_survivors"]:
        raise AssertionError("embedded certificate was trusted instead of recomputed")
    checks.append(
        {
            "name": "forged_embedded_certificate_recomputed",
            "passed": True,
            "survivors": recomputed["survivors"],
        }
    )

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
                    for forbidden in (
                        b"settings",
                        b"program_solution",
                        b"program_sha256",
                        b"certificate",
                        b"seed",
                        b"schema",
                        b"task_id",
                    ):
                        if forbidden in body:
                            raise AssertionError(f"private key leaked: {forbidden!r}")

                    changed = copy.deepcopy(episode)
                    changed["settings"] = prototype.DEFAULT
                    changed["program_solution"] = "forged-private-program"
                    changed["program_sha256"] = "0" * 64
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


def _protected_racket_probe(examples_out: Path | None) -> dict:
    seeds = (0, 17, 43)
    demo_counts = (2, 6)
    episodes_checked = 0
    labels_executed = 0
    examples = []
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
                    if seed == 17 and demos == 2:
                        examples.append(
                            {
                                "settings": setting,
                                "episode": episode,
                                "racket_certificate": certificate,
                            }
                        )

    if runtime_identity.get("backend") != "racket" or runtime_identity.get("protected") is not True:
        raise AssertionError(runtime_identity)
    if len(examples) != len(prototype.SETTINGS):
        raise AssertionError("missing Racket-backed setting example")
    if examples_out is not None:
        payload = {
            "schema": "arcpuzzles-parametric-racket-examples-v1",
            "task_id": TASK_ID,
            "runtime_identity": runtime_identity,
            "examples": examples,
            "limits": (
                "Two finite four-query examples with demonstration-only teaching checks; "
                "they do not establish universal identifiability."
            ),
        }
        examples_out.parent.mkdir(parents=True, exist_ok=True)
        examples_out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    return {
        "name": "protected_racket_minimum_and_maximum_lessons",
        "passed": True,
        "seeds": list(seeds),
        "demo_counts": list(demo_counts),
        "settings": len(prototype.SETTINGS),
        "episodes_checked": episodes_checked,
        "labels_executed": labels_executed,
        "saved_four_query_examples": len(examples),
        "runtime_identity": runtime_identity,
    }


def run_probe(seed_count: int = 64, examples_out: Path | None = None) -> dict:
    if type(seed_count) is not int or seed_count < 1:
        raise ValueError("seed_count must be a positive exact integer")
    checks = [
        _pure_python_sweep(seed_count),
        _certificate_attacks(),
        _public_projection_attacks(),
        _protected_racket_probe(examples_out),
    ]
    source_paths = [
        REPO / "generators" / TASK_ID / "generator.py",
        HERE / "prototype.py",
        HERE / "adapter.py",
        HERE / "promotion.json",
        HERE / "canonical.rkt",
        HERE / "largest_area.rkt",
        HERE / "adversarial_probe.py",
        REPO / "generators" / TASK_ID / "tests" / "test_generator_4dd0b3ed33ee.py",
        REPO / "generators" / TASK_ID / "tests" / "test_parametric_match_selector.py",
    ]
    return {
        "schema": "arcpuzzles-parametric-bounded-adversarial-v1",
        "task_id": TASK_ID,
        "status": "passed",
        "checks": checks,
        "scope": [
            "minimum/ordinary/maximum demonstration counts over fresh seeds",
            "crossed fixed-size rank, colour, position, shelf, motif and topology controls",
            "twenty-plus finite selector/render/connectivity shortcuts",
            "strict malformed-count/type/program/hash/duplicate/certificate rejection",
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
    parser.add_argument("--examples-out", type=Path)
    args = parser.parse_args(list(argv) if argv is not None else None)
    report = run_probe(args.seeds, args.examples_out)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out is None:
        print(text, end="")
    else:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
