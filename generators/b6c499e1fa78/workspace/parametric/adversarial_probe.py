"""Finite adversarial self-review for the b6c499e1fa78 parametric family."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

from reviewer_support import public_challenge_bytes, public_challenge_id

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
TASK = "b6c499e1fa78"


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
    except (TypeError, ValueError, RuntimeError):
        return
    failures.append(label)


def old_decoy_regression(prototype) -> dict[str, Any]:
    """Small retained reproducer for the repaired T-opening/plus alias."""
    def make(opening):
        g = [[0] * 10 for _ in range(10)]
        for r in range(1, 4):
            for c in range(10):
                g[r][c] = 1
        for r, c in opening:
            g[2 + r][3 + c] = 0
        plus = ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1))
        for r, c in plus:
            g[6 + r][3 + c] = 5
        return g

    old_t = ((0, 1), (1, 0), (1, 1), (1, 2))
    repaired_j = ((0, 0), (0, 1), (0, 2), (1, 0))
    old = make(old_t)
    repaired = make(repaired_j)
    old_a = prototype.analyze_scene(old)
    new_a = prototype.analyze_scene(repaired)
    return {
        "finding": "A T-shaped decoy opening exactly matched the top two rows of the five-cell plus branch.",
        "root_cause": "The decoy opening bank was not checked against every branch-key top slice.",
        "repair": "Replace the T decoy with an asymmetric J opening and retain role-profile regressions.",
        "old_input": old,
        "repaired_input": repaired,
        "old_matched_piece_areas": old_a["matched_piece_areas"],
        "repaired_matched_piece_areas": new_a["matched_piece_areas"],
        "old_output": prototype.apply_rule(old, "matched_area"),
        "repaired_output": prototype.apply_rule(repaired, "matched_area"),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--regression-out", required=True, type=Path)
    args = parser.parse_args()

    prototype = load("_b6c499e1fa78_probe_parametric", HERE / "prototype.py")
    generator = load("_b6c499e1fa78_probe_generator", HERE.parents[1] / "generator.py")
    failures: list[str] = []

    # Base-generator repair surface: ordinary draws plus exact min/max controls.
    production_cases = 0
    production_profiles: set[tuple[Any, ...]] = set()
    for difficulty in (None, "easy", "medium", "hard"):
        for seed in range(32):
            try:
                grid = generator.generate(seed, seed * 19 + 7, difficulty=difficulty)
                errors = generator.self_check(grid, difficulty=difficulty)
                if errors:
                    failures.append(f"production self_check {difficulty}/{seed}: {errors}")
                a = generator.analyze(grid)
                if not (a["n_match"] >= 1 and a["n_branch_only"] == 1
                        and a["n_negative"] >= 1 and a["n_match_and_branch"] == 0):
                    failures.append(f"production role collapse {difficulty}/{seed}: {a}")
                production_profiles.add((difficulty, len(grid), len(a["openings"]),
                                         a["n_match"], a["n_negative"]))
                production_cases += 1
            except Exception as exc:
                failures.append(f"production {difficulty}/{seed}: {type(exc).__name__}: {exc}")

    forced_profiles = [
        {"grid_size": 10, "wall_top": 1, "n_openings": 1, "n_match": 1, "n_negative": 1},
        {"grid_size": 30, "wall_top": 12, "n_openings": 3, "n_match": 2, "n_negative": 3},
        {"grid_size": 10, "wall_top": 1, "n_openings": 1, "n_match": 1,
         "n_negative": 1, "texture": "compact"},
        {"grid_size": 30, "wall_top": 12, "n_openings": 3, "n_match": 2,
         "n_negative": 3, "texture": "spread"},
    ]
    for index, controls in enumerate(forced_profiles):
        try:
            grid = generator.generate(1001 + index, index, difficulty="hard", **controls)
            observed = generator.observe_overrides(grid)
            expected = {k: v for k, v in controls.items() if k != "texture"}
            if observed != expected:
                failures.append(f"forced controls {index}: {observed} != {expected}")
            if generator.self_check(grid):
                failures.append(f"forced controls self_check {index}")
        except Exception as exc:
            failures.append(f"forced controls {index}: {type(exc).__name__}: {exc}")

    for label, kwargs in (
        ("bool grid size", {"grid_size": True}),
        ("float wall top", {"wall_top": 2.0}),
        ("stale match style", {"match_style": "direct"}),
        ("unknown control", {"bogus": 1}),
        ("infeasible wall", {"grid_size": 10, "wall_top": 12}),
    ):
        expect_failure(label, lambda kwargs=kwargs: generator.generate(0, 0, **kwargs), failures)

    # Parametric sampler, minimum lesson, finite rivals, and crossed controls.
    episode_cases = 0
    rival_evaluations = 0
    setting_neutral_checks = 0
    prefix_checks = 0
    query_intermediates: dict[int, set[tuple[int, ...]]] = {0: set(), 1: set(), 2: set(), 3: set()}
    nuisance_by_intermediate: dict[tuple[int, tuple[int, ...]], set[str]] = {}
    query_dimension_sets: set[tuple[tuple[int, int], ...]] = set()
    for seed in range(24):
        for policy in prototype.BRANCH_POLICIES:
            for demos in (2, 6):
                try:
                    episode = prototype.generate(seed, {"branch_policy": policy}, demos, 4)
                    certificate = prototype.certify(episode)
                    if certificate["rival_survivors"]:
                        failures.append(f"surviving rival {seed}/{policy}/{demos}")
                    for pair in episode["train"]:
                        for name in prototype.RIVALS:
                            prototype._grid(prototype._rival(name, pair["input"], policy))
                            rival_evaluations += 1
                    dims = tuple((len(pair["input"]), len(pair["input"][0]))
                                 for pair in episode["test"])
                    query_dimension_sets.add(dims)
                    if dims != ((17, 17), (21, 21), (25, 25), (30, 30)):
                        failures.append(f"query dimensions {seed}/{policy}/{demos}: {dims}")
                    large = prototype.analyze_scene(episode["test"][3]["input"])
                    gray = set(large["gray_cells"])
                    if not (len(large["pieces"]) >= 10 and len(large["openings"]) >= 4
                            and len(gray) >= 45 and {0, 29} <= {c for _, c in gray}
                            and 29 in {r for r, _ in gray}):
                        failures.append(f"weak 30x30 stress {seed}/{policy}/{demos}")
                    episode_cases += 1
                except Exception as exc:
                    failures.append(f"episode {seed}/{policy}/{demos}: {type(exc).__name__}: {exc}")

        left = prototype.generate(seed, {"branch_policy": "unconditional"}, 2, 4)
        right = prototype.generate(seed, {"branch_policy": "matched_area"}, 2, 4)
        if [x["input"] for x in left["train"] + left["test"]] != [
                x["input"] for x in right["train"] + right["test"]]:
            failures.append(f"setting-dependent inputs seed {seed}")
        setting_neutral_checks += 1
        small = prototype.generate(seed, {"branch_policy": "matched_area"}, 2, 4)
        large = prototype.generate(seed, {"branch_policy": "matched_area"}, 6, 4)
        if small["train"] != large["train"][:2] or small["test"] != large["test"]:
            failures.append(f"prefix instability seed {seed}")
        prefix_checks += 1
        for index, pair in enumerate(left["test"]):
            a = prototype.analyze_scene(pair["input"])
            intermediate = tuple(sorted(set(a["matched_piece_areas"])))
            query_intermediates[index].add(intermediate)
            nuisance_by_intermediate.setdefault((index, intermediate), set()).add(prototype.digest(pair["input"]))

    # At fixed 17/21/25 dimensions and profile slots, intended intermediates
    # must vary across seeds; for a fixed intermediate, geometry must also vary.
    for index in range(3):
        if query_intermediates[index] != {(4,), (5,), (6,)}:
            failures.append(f"dimension/profile shortcut survives at query {index}: {query_intermediates[index]}")
        for intermediate in ((4,), (5,), (6,)):
            if len(nuisance_by_intermediate.get((index, intermediate), set())) < 2:
                failures.append(f"nuisance variation missing query {index}/{intermediate}")
    if query_intermediates[3] != {(4, 5, 6)}:
        failures.append(f"30x30 intended intermediate drift: {query_intermediates[3]}")
    if len(nuisance_by_intermediate.get((3, (4, 5, 6)), set())) < 12:
        failures.append("30x30 fixed-intermediate nuisance variation too small")

    # Certificate, type, count, duplicate, and export/privacy attacks.
    expect_failure("unknown setting", lambda: prototype.generate(0, {"branch_policy": "bogus"}, 2, 4), failures)
    expect_failure("bool seed", lambda: prototype.generate(True, {"branch_policy": "unconditional"}, 2, 4), failures)
    expect_failure("too few demos", lambda: prototype.generate(0, {"branch_policy": "unconditional"}, 1, 4), failures)
    expect_failure("too many demos", lambda: prototype.generate(0, {"branch_policy": "unconditional"}, 7, 4), failures)
    expect_failure("wrong query count", lambda: prototype.generate(0, {"branch_policy": "unconditional"}, 2, 3), failures)

    forged = prototype.generate(3, {"branch_policy": "unconditional"}, 2, 4)
    forged["certificate"]["rival_survivors"] = ["forged"]
    expect_failure("forged certificate", lambda: prototype.certify(forged), failures)
    duplicate = prototype.generate(4, {"branch_policy": "unconditional"}, 2, 4)
    duplicate["test"][0]["input"] = copy.deepcopy(duplicate["train"][0]["input"])
    duplicate["test"][0]["output"] = prototype.apply_rule(duplicate["test"][0]["input"], "unconditional")
    expect_failure("duplicate input", lambda: prototype.certify(duplicate), failures)
    bad_cell = prototype.generate(5, {"branch_policy": "unconditional"}, 2, 4)
    bad_cell["train"][0]["input"][0][0] = True
    expect_failure("bool cell", lambda: prototype.certify(bad_cell), failures)

    public_invariance_checks = 0
    visible_episode = prototype.generate(31, {"branch_policy": "matched_area"}, 3, 4)
    visible = prototype.public_turn(visible_episode, 0)
    original_bytes = public_challenge_bytes(visible)
    original_id = public_challenge_id(visible)
    for mutation in ("settings", "program", "certificate", "answer", "future_input"):
        changed = copy.deepcopy(visible_episode)
        if mutation == "settings":
            changed["settings"] = {"branch_policy": "unconditional"}
        elif mutation == "program":
            changed["program_solution"] = "private"
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

    # Protected Racket parity and two causal counterfactuals on final bytes.
    racket_evaluations = 0
    counterfactual_changes = {"opening_area_gate": 0, "match_only": 0}
    runtime_identity: dict[str, Any] = {}
    with prototype.RacketRunner() as execute:
        runtime_identity = execute.identity
        for seed in (0, 17):
            neutral = prototype.generate(seed, {"branch_policy": "unconditional"}, 2, 4)
            inputs = [p["input"] for p in neutral["train"] + neutral["test"]]
            for grid in inputs:
                for policy in prototype.BRANCH_POLICIES:
                    got = execute(prototype.program({"branch_policy": policy}), grid)
                    if got != prototype.apply_rule(grid, policy):
                        failures.append(f"Racket/Python mismatch {seed}/{policy}/{prototype.digest(grid)}")
                    racket_evaluations += 1
            target_program = prototype.program({"branch_policy": "matched_area"})
            for grid in inputs:
                target = execute(target_program, grid)
                for name, path in (
                    ("opening_area_gate", HERE / "opening_area_gate.rkt"),
                    ("match_only", HERE / "match_only.rkt"),
                ):
                    wrong = execute(path.read_text(encoding="utf-8"), grid)
                    racket_evaluations += 1
                    if wrong != target:
                        counterfactual_changes[name] += 1
        if any(count == 0 for count in counterfactual_changes.values()):
            failures.append(f"counterfactual did not change any output: {counterfactual_changes}")

    regression = old_decoy_regression(prototype)
    if regression["old_matched_piece_areas"] != [5] or regression["repaired_matched_piece_areas"] != []:
        failures.append("retained T-opening/plus regression no longer reproduces")
    args.regression_out.parent.mkdir(parents=True, exist_ok=True)
    args.regression_out.write_text(json.dumps(regression, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    result = {
        "schema": "b6c499e1fa78-adversarial-probe-v1",
        "status": "pass" if not failures else "fail",
        "finite_scope": {
            "production_cases": production_cases,
            "production_profiles": len(production_profiles),
            "forced_boundary_profiles": len(forced_profiles),
            "episode_cases": episode_cases,
            "seeds": list(range(24)),
            "settings": list(prototype.BRANCH_POLICIES),
            "demo_counts": [2, 6],
            "queries_per_episode": 4,
            "rivals": list(prototype.RIVALS),
            "rival_evaluations": rival_evaluations,
            "setting_neutral_checks": setting_neutral_checks,
            "prefix_checks": prefix_checks,
            "public_invariance_checks": public_invariance_checks,
            "protected_racket_seeds": [0, 17],
            "protected_racket_evaluations": racket_evaluations,
            "counterfactual_changes": counterfactual_changes,
        },
        "crossed_controls": {
            "fixed_query_dimensions": [[17, 17], [21, 21], [25, 25], [30, 30]],
            "intermediates_by_query_index": {
                str(k): [list(x) for x in sorted(v)] for k, v in query_intermediates.items()
            },
            "nuisance_variants_per_fixed_intermediate": {
                f"query-{index}:{','.join(map(str, intermediate))}": len(digests)
                for (index, intermediate), digests in sorted(nuisance_by_intermediate.items())
            },
        },
        "query_dimension_sets": [[list(x) for x in dims] for dims in sorted(query_dimension_sets)],
        "retained_regression": str(args.regression_out),
        "runtime_identity": runtime_identity,
        "source_sha256": {
            str(path.relative_to(REPO)): sha(path)
            for path in (
                HERE.parents[1] / "generator.py",
                HERE / "prototype.py",
                HERE / "adapter.py",
                HERE / "promotion.json",
                HERE / "canonical.rkt",
                HERE / "matched_area.rkt",
                HERE / "opening_area_gate.rkt",
                HERE / "match_only.rkt",
                HERE.parents[1] / "tests" / "test_generator_parametric.py",
            )
        },
        "failures": failures,
        "limits": (
            "Finite adversarial evidence against the named rivals and sampled controls only; "
            "it is not a proof of universal lesson uniqueness. Owner source review, fresh native "
            "qualification/acceptance, and training admission remain separate."
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], **result["finite_scope"], "out": str(args.out)}, sort_keys=True))
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
