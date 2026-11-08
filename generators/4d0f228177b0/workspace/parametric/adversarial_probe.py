"""Bounded adversarial audit for the 4d0f228177b0 parametric prototype.

This is intentionally reusable by later reviewers.  It attacks the declared
minimum lesson, matched-setting sampler, count prefixes, semantic rivals,
crossed controls, certificate mutations, and the 30x30/boundary surfaces.  It
can additionally bind a protected-Racket worker receipt produced separately.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

HOME = Path(__file__).resolve().parent


def _load(name: str, filename: str):
    path = HOME / filename
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _raw(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def _normalized_payload_geometry(grid: list[list[int]]) -> list[list[int]]:
    return [[7 if cell in (7, 9) else cell for cell in row] for row in grid]


def run(seeds: int, racket_execution: Path | None = None) -> dict[str, Any]:
    if type(seeds) is not int or not 1 <= seeds <= 512:
        raise ValueError("seeds must be an integer in 1..512")
    proto = _load("_probe_proto_4d0", "prototype.py")
    adapter = _load("_probe_adapter_4d0", "adapter.py")
    failures: list[dict[str, Any]] = []
    profile_counts: dict[str, int] = {}
    rival_refutations = {name: 0 for name in proto.RIVALS}
    episodes_checked = 0
    pairs_checked = 0
    max_grid = [0, 0]
    boundary_scenes = 0
    inactive_scenes = 0

    for seed in range(seeds):
        try:
            full = {
                finish: adapter.generate(seed, {"finish": finish}, 6, 4)
                for finish in ("canonical", "first_hit_payload")
            }
            visible = lambda episode: [p["input"] for p in episode["train"] + episode["test"]]
            if visible(full["canonical"]) != visible(full["first_hit_payload"]):
                failures.append({"seed": seed, "check": "matched_inputs"})
            for finish, episode in full.items():
                setting = {"finish": finish}
                errors = adapter.certificate_errors(episode, setting, demos=6, queries=4)
                if errors:
                    failures.append({"seed": seed, "check": "certificate", "setting": finish, "errors": errors})
                for demos in (2, 3, 6):
                    for queries in (1, 4):
                        candidate = adapter.generate(seed, setting, demos, queries)
                        episodes_checked += 1
                        pairs_checked += demos + queries
                        if candidate["train"] != episode["train"][:demos]:
                            failures.append({"seed": seed, "check": "demo_prefix", "setting": finish,
                                             "demos": demos, "queries": queries})
                        if candidate["test"] != episode["test"][:queries]:
                            failures.append({"seed": seed, "check": "query_prefix", "setting": finish,
                                             "demos": demos, "queries": queries})
                        errors = adapter.certificate_errors(candidate, setting, demos=demos, queries=queries)
                        if errors:
                            failures.append({"seed": seed, "check": "lesson", "setting": finish,
                                             "demos": demos, "queries": queries, "errors": errors})
                for pair in episode["train"] + episode["test"]:
                    facts = proto.scene_facts(pair["input"])
                    max_grid = [max(max_grid[0], facts["height"]), max(max_grid[1], facts["width"])]
                    boundary_scenes += int(facts["boundary_payload"])
                    inactive_scenes += int(not facts["active"])
                    key = json.dumps({k: facts[k] for k in (
                        "height", "vertical_color", "active", "first_hit_color", "later_hit_color",
                        "boundary_payload")}, sort_keys=True)
                    profile_counts[key] = profile_counts.get(key, 0) + 1

            min_episode = full["first_hit_payload"]
            demos = min_episode["train"][:2]
            for name, rival in proto.RIVALS.items():
                if any(rival(pair["input"]) != pair["output"] for pair in demos):
                    rival_refutations[name] += 1
                else:
                    failures.append({"seed": seed, "check": "rival_survived_minimum", "rival": name})
        except Exception as exc:
            failures.append({"seed": seed, "check": "exception", "type": type(exc).__name__, "message": str(exc)})

    # Crossed control 1: hold all coordinates and nuisance geometry fixed while
    # swapping which payload color is encountered first.
    fixed7 = proto._active_scene(size=20, vertical_color=6, selected=7, first_k=3,
                                 later_k=7, variant=2, include_one=True)
    fixed9 = proto._active_scene(size=20, vertical_color=6, selected=9, first_k=3,
                                 later_k=7, variant=2, include_one=True)
    crossed_intermediate = {
        "normalized_geometry_equal": _normalized_payload_geometry(fixed7) == _normalized_payload_geometry(fixed9),
        "first_hit": [proto.scene_facts(fixed7)["first_hit_color"], proto.scene_facts(fixed9)["first_hit_color"]],
        "outputs_differ": proto.apply(fixed7, {"finish": "first_hit_payload"})
                          != proto.apply(fixed9, {"finish": "first_hit_payload"}),
    }
    if crossed_intermediate != {"normalized_geometry_equal": True, "first_hit": [7, 9], "outputs_differ": True}:
        failures.append({"check": "crossed_intermediate", "actual": crossed_intermediate})

    # Crossed control 2: hold the derived first-hit color fixed while changing
    # vertical cue, dimensions, hit distances, and distractor layout.
    nuisance_a = proto._active_scene(size=18, vertical_color=3, selected=7, first_k=2,
                                     later_k=6, variant=0)
    nuisance_b = proto._active_scene(size=30, vertical_color=6, selected=7, first_k=5,
                                     later_k=11, variant=3, include_one=True,
                                     boundary_payload=True, dense=True)
    nuisance_facts = [proto.scene_facts(nuisance_a), proto.scene_facts(nuisance_b)]
    crossed_nuisance = {
        "first_hit": [f["first_hit_color"] for f in nuisance_facts],
        "vertical_colors": [f["vertical_color"] for f in nuisance_facts],
        "sizes": [[f["height"], f["width"]] for f in nuisance_facts],
        "selected_payloads_recolored": all(
            all(
                output[r][c] == 8
                for r, row in enumerate(intermediate)
                for c, value in enumerate(row)
                if value == 7
            )
            for scene, intermediate, output in (
                (
                    nuisance_a,
                    proto.apply(nuisance_a, {"finish": "canonical"}),
                    proto.apply(nuisance_a, {"finish": "first_hit_payload"}),
                ),
                (
                    nuisance_b,
                    proto.apply(nuisance_b, {"finish": "canonical"}),
                    proto.apply(nuisance_b, {"finish": "first_hit_payload"}),
                ),
            )
        ),
    }
    if (
        crossed_nuisance["first_hit"] != [7, 7]
        or crossed_nuisance["vertical_colors"] != [3, 6]
        or crossed_nuisance["selected_payloads_recolored"] is not True
    ):
        failures.append({"check": "crossed_nuisance", "actual": crossed_nuisance})

    # Authored-certificate attacks.
    setting = {"finish": "first_hit_payload"}
    clean = adapter.generate(31, setting, 2, 4)
    attacks = {}
    forged = copy.deepcopy(clean)
    forged["test"][0]["output"][0][0] = (forged["test"][0]["output"][0][0] + 1) % 10
    attacks["forged_output"] = bool(adapter.certificate_errors(forged, setting, demos=2, queries=4))
    duplicate = copy.deepcopy(clean)
    duplicate["test"][0]["input"] = copy.deepcopy(duplicate["train"][0]["input"])
    attacks["duplicate_input"] = bool(adapter.certificate_errors(duplicate, setting, demos=2, queries=4))
    boolean = copy.deepcopy(clean)
    boolean["train"][0]["input"][0][0] = False
    attacks["boolean_cell"] = bool(adapter.certificate_errors(boolean, setting, demos=2, queries=4))
    wrong_program = copy.deepcopy(clean)
    wrong_program["program_solution"] = adapter.program({"finish": "canonical"})
    attacks["wrong_program"] = bool(adapter.certificate_errors(wrong_program, setting, demos=2, queries=4))
    attacks["wrong_counts"] = bool(adapter.certificate_errors(clean, setting, demos=3, queries=4))
    for name, rejected in attacks.items():
        if not rejected:
            failures.append({"check": "certificate_attack_not_rejected", "attack": name})

    racket = None
    if racket_execution is not None:
        data = json.loads(racket_execution.read_text(encoding="utf-8"))
        racket = {
            "path": str(racket_execution),
            "sha256": hashlib.sha256(racket_execution.read_bytes()).hexdigest(),
            "protected": data.get("racket", {}).get("protected") is True,
            "backend": data.get("racket", {}).get("backend"),
            "evaluations": data.get("racket_evaluations"),
            "episodes": len(data.get("episodes", [])),
            "all_single_survivor": all(len(check.get("survivors", [])) == 1 for check in data.get("checks", [])),
        }
        if not (racket["protected"] and racket["backend"] == "racket"
                and isinstance(racket["evaluations"], int) and racket["evaluations"] > 0
                and racket["all_single_survivor"]):
            failures.append({"check": "racket_receipt", "actual": racket})

    return {
        "schema": "4d0f228177b0-parametric-adversarial-probe-v1",
        "status": "passed" if not failures else "failed",
        "seed_range": [0, seeds - 1],
        "episodes_checked": episodes_checked,
        "pairs_checked": pairs_checked,
        "minimum_demonstrations": 2,
        "rival_refutations_at_minimum": rival_refutations,
        "crossed_intermediate": crossed_intermediate,
        "crossed_nuisance": crossed_nuisance,
        "certificate_attacks_rejected": attacks,
        "max_grid": max_grid,
        "boundary_scenes": boundary_scenes,
        "inactive_scenes": inactive_scenes,
        "profile_counts": profile_counts,
        "racket": racket,
        "failures": failures,
        "finite_limit": (
            "This bounded rival bank and finite seed range do not prove universal uniqueness; "
            "a solver can still geometrically predict the canonical ray without literally materializing it."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=64)
    parser.add_argument("--racket-execution", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.seeds, args.racket_execution)
    if args.out.exists() or args.out.is_symlink():
        raise FileExistsError(args.out)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(_raw(report))
    print(json.dumps({k: report[k] for k in (
        "status", "seed_range", "episodes_checked", "pairs_checked", "max_grid",
        "boundary_scenes", "inactive_scenes")}, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
