"""Bounded adversarial probe for the 204213f10aff source-bound family."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
TASK = "204213f10aff"
if str(REPO / "shared/runtime") not in sys.path:
    sys.path.insert(0, str(REPO / "shared/runtime"))
from reviewer_support import public_challenge_bytes, public_challenge_id


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def expect_failure(label: str, fn, failures: list[str]) -> None:
    try:
        fn()
    except (TypeError, ValueError, FileExistsError):
        return
    failures.append(label)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    prototype = load("_probe_parametric_204213f10aff", HERE / "prototype.py")
    generator = load("_probe_generator_204213f10aff", HERE.parents[1] / "generator.py")

    failures: list[str] = []
    production_cases = 0
    for difficulty in (None, "easy", "medium", "hard"):
        for seed in range(16):
            try:
                grid = generator.generate(seed, seed * 17 + 3, difficulty=difficulty)
                if generator.self_check(grid):
                    failures.append(f"production self_check {difficulty}/{seed}")
                analysis = generator.analyze(grid)
                if analysis["legend_positions"] == list(range(analysis["piece_count"])):
                    failures.append(f"production contiguous legend {difficulty}/{seed}")
                if analysis["distractor_count"] < 1:
                    failures.append(f"production missing distractor {difficulty}/{seed}")
                production_cases += 1
            except Exception as exc:  # retained verbatim in bounded evidence
                failures.append(f"production {difficulty}/{seed}: {type(exc).__name__}: {exc}")
    stress = generator.generate(917, 29, difficulty="hard", grid_h=30, grid_w=30,
                                piece_count=4, distractor_count=3)
    if generator.observe_overrides(stress) != {
        "grid_h": 30, "grid_w": 30, "piece_count": 4, "distractor_count": 3
    }:
        failures.append("production max override observation")

    episode_cases = 0
    rival_evaluations = 0
    query_dimension_sets: set[tuple[tuple[int, int], ...]] = set()
    public_invariance_checks = 0
    for seed in range(16):
        for mode in prototype.PIECE_ORDERS:
            for demos in (2, 6):
                try:
                    episode = prototype.generate(seed, {"piece_order": mode}, demos, 4)
                    certificate = prototype.certify(episode)
                    if certificate["rival_survivors"]:
                        failures.append(f"surviving rival {seed}/{mode}/{demos}")
                    for pair in episode["train"]:
                        for name in prototype.RIVALS:
                            prototype._grid(prototype._rival(name, pair["input"], mode))
                            rival_evaluations += 1
                    dims = tuple(sorted((len(pair["input"]), len(pair["input"][0]))
                                        for pair in episode["test"]))
                    query_dimension_sets.add(dims)
                    if (30, 30) not in dims:
                        failures.append(f"missing 30x30 query {seed}/{mode}/{demos}")
                    episode_cases += 1
                except Exception as exc:
                    failures.append(f"episode {seed}/{mode}/{demos}: {type(exc).__name__}: {exc}")

        left = prototype.generate(seed, {"piece_order": "legend"}, 2, 4)
        right = prototype.generate(seed, {"piece_order": "area_descending"}, 2, 4)
        if [p["input"] for p in left["train"] + left["test"]] != [
                p["input"] for p in right["train"] + right["test"]]:
            failures.append(f"setting-dependent inputs seed {seed}")
        small = prototype.generate(seed, {"piece_order": "legend"}, 2, 4)
        large = prototype.generate(seed, {"piece_order": "legend"}, 6, 4)
        if small["train"] != large["train"][:2] or small["test"] != large["test"]:
            failures.append(f"prefix instability seed {seed}")

    visible_episode = prototype.generate(31, {"piece_order": "area_descending"}, 3, 4)
    original = prototype.public_turn(visible_episode, 0)
    original_bytes = public_challenge_bytes(original)
    original_id = public_challenge_id(original)
    for mutation in ("settings", "program", "certificate", "answer", "future_input"):
        changed = copy.deepcopy(visible_episode)
        if mutation == "settings":
            changed["settings"] = {"piece_order": "legend"}
        elif mutation == "program":
            changed["program_solution"] = "private mutation"
        elif mutation == "certificate":
            changed["certificate"] = {"private": True}
        elif mutation == "answer":
            changed["test"][0]["output"] = [[9]]
        else:
            changed["test"][1]["input"] = [[9]]
        projected = prototype.public_turn(changed, 0)
        if public_challenge_bytes(projected) != original_bytes or public_challenge_id(projected) != original_id:
            failures.append(f"private field leaked into first turn: {mutation}")
        public_invariance_checks += 1
    changed = copy.deepcopy(visible_episode)
    changed["test"][0]["input"] = [[9]]
    if public_challenge_bytes(prototype.public_turn(changed, 0)) == original_bytes:
        failures.append("visible input positive control did not change public bytes")

    expect_failure("unknown setting", lambda: prototype.generate(0, {"piece_order": "bogus"}, 2, 4), failures)
    expect_failure("bool seed", lambda: prototype.generate(True, {"piece_order": "legend"}, 2, 4), failures)
    expect_failure("too few demos", lambda: prototype.generate(0, {"piece_order": "legend"}, 1, 4), failures)
    expect_failure("wrong queries", lambda: prototype.generate(0, {"piece_order": "legend"}, 2, 3), failures)
    forged = prototype.generate(3, {"piece_order": "legend"}, 2, 4)
    forged["certificate"]["rival_survivors"] = ["forged"]
    expect_failure("forged certificate", lambda: prototype.certify(forged), failures)
    duplicate = prototype.generate(4, {"piece_order": "legend"}, 2, 4)
    duplicate["test"][0] = copy.deepcopy(duplicate["train"][0])
    expect_failure("duplicate input", lambda: prototype.certify(duplicate), failures)
    bad_cell = prototype.generate(5, {"piece_order": "legend"}, 2, 4)
    bad_cell["train"][0]["input"][2][2] = True
    expect_failure("bool cell", lambda: prototype.certify(bad_cell), failures)

    racket_evaluations = 0
    runtime_identity: dict[str, Any] = {}
    with prototype.RacketRunner() as execute:
        runtime_identity = execute.identity
        for seed in (0, 17):
            episode = prototype.generate(seed, {"piece_order": "legend"}, 2, 4)
            inputs = [pair["input"] for pair in episode["train"] + episode["test"]]
            for grid in inputs:
                for mode in prototype.PIECE_ORDERS:
                    got = execute(prototype.program({"piece_order": mode}), grid)
                    if got != prototype.apply_rule(grid, mode):
                        failures.append(f"Racket/Python mismatch {seed}/{mode}/{prototype.digest(grid)}")
                    racket_evaluations += 1
            first_two = [pair["input"] for pair in episode["train"]]
            if all(execute((HERE / "bbox_area_descending.rkt").read_text(), grid)
                   == prototype.apply_rule(grid, "area_descending") for grid in first_two):
                failures.append(f"bbox-area wrong intermediate survives seed {seed}")
            racket_evaluations += len(first_two)
            if all(execute((HERE / "reverse_legend.rkt").read_text(), grid)
                   == prototype.apply_rule(grid, "legend") for grid in first_two):
                failures.append(f"reverse-legend wrong order survives seed {seed}")
            racket_evaluations += len(first_two)

    result = {
        "schema": "204213f10aff-adversarial-probe-v1",
        "status": "pass" if not failures else "fail",
        "finite_scope": {
            "production_cases": production_cases,
            "episode_cases": episode_cases,
            "seeds": list(range(16)),
            "settings": list(prototype.PIECE_ORDERS),
            "demo_counts": [2, 6],
            "queries_per_episode": 4,
            "rivals": list(prototype.RIVALS),
            "rival_evaluations": rival_evaluations,
            "protected_racket_seeds": [0, 17],
            "protected_racket_evaluations": racket_evaluations,
            "public_invariance_checks": public_invariance_checks,
        },
        "query_dimension_sets": [list(map(list, dims)) for dims in sorted(query_dimension_sets)],
        "runtime_identity": runtime_identity,
        "source_sha256": {
            str(path.relative_to(REPO)): sha(path)
            for path in (HERE.parents[1] / "generator.py", HERE / "prototype.py", HERE / "adapter.py",
                         HERE / "promotion.json", HERE / "canonical.rkt", HERE / "area_descending.rkt",
                         HERE / "bbox_area_descending.rkt", HERE / "reverse_legend.rkt")
        },
        "failures": failures,
        "limits": "Finite adversarial evidence only; owner source review, native acceptance, and training admission are separate.",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], **result["finite_scope"], "out": str(args.out)}, sort_keys=True))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
