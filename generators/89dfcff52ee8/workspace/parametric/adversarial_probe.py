"""Bounded adversarial audit for the 89dfcff52ee8 parametric family.

This is intentionally task-local and source-bound.  It attacks the declared
minimum lesson, common shortcut rules, crossed controls, malformed episodes,
public projection, and the row-closure intermediate with protected Racket.
It is evidence for review, not a proof of universal uniqueness or acceptance.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any, Iterable, Sequence

HERE = Path(__file__).resolve().parent
TASK_HOME = HERE.parents[1]
DEFAULT_SWEEP_SEEDS = tuple(range(32))
DEFAULT_RACKET_CASES = (
    (0, "rows_only", 2),
    (0, "rows_then_columns", 2),
    (17, "rows_only", 3),
    (17, "rows_then_columns", 3),
    (43, "rows_only", 6),
    (43, "rows_then_columns", 6),
)


def _load_prototype():
    path = HERE / "prototype.py"
    name = "arcpuzzles_89dfcff52ee8_probe_prototype"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha256(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def _expect_rejected(prototype, episode: dict[str, Any]) -> str:
    try:
        prototype.certify(episode)
    except (TypeError, ValueError) as exc:
        return f"{type(exc).__name__}: {exc}"
    raise AssertionError("malformed episode was accepted")


def _pure_sampler_sweep(prototype, seeds: Iterable[int]) -> dict[str, Any]:
    episodes = 0
    minimum = 0
    max_size = 0
    query_hashes: set[str] = set()
    setting_counts = {setting["closure"]: 0 for setting in prototype.SETTINGS}
    for seed in seeds:
        for setting in prototype.SETTINGS:
            for demos in (2, 6):
                episode = prototype.generate(seed, setting, demos=demos, queries=4)
                certificate = prototype.certify(episode)
                if certificate["survivors"] != [setting]:
                    raise AssertionError("declared setting did not uniquely survive")
                if set(certificate["extra_refutations"]) != set(prototype.RIVAL_NAMES):
                    raise AssertionError("shortcut inventory drifted")
                if any(not indices for indices in certificate["extra_refutations"].values()):
                    raise AssertionError("a shortcut rival survived the demonstrations")
                episodes += 1
                minimum += demos == 2
                setting_counts[setting["closure"]] += 1
                inputs = [pair["input"] for pair in episode["train"] + episode["test"]]
                if len({prototype.digest(grid) for grid in inputs}) != len(inputs):
                    raise AssertionError("episode contains duplicate inputs")
                for pair in episode["test"]:
                    rows, cols = len(pair["input"]), len(pair["input"][0])
                    max_size = max(max_size, rows * cols)
                    query_hashes.add(prototype.digest(pair["input"]))
                    if not prototype.profile(pair["input"])["sequentially_decisive"]:
                        raise AssertionError("query collapses the sequential dependency")
    return {
        "seeds": list(seeds),
        "demo_counts": [2, 6],
        "episodes": episodes,
        "minimum_demo_episodes": minimum,
        "setting_counts": setting_counts,
        "distinct_query_inputs": len(query_hashes),
        "largest_grid_cells": max_size,
        "all_certified": True,
    }


def _crossed_controls(prototype) -> tuple[dict[str, Any], dict[str, list[list[int]]]]:
    episode = prototype.generate(
        31, {"closure": "rows_then_columns"}, demos=2, queries=4
    )
    original = episode["test"][1]["input"]
    recolored = prototype.recolor_markers(original)
    shifted = prototype.shift_one_endpoint(original)
    nuisance_same_positions = (
        prototype.marker_positions(original) == prototype.marker_positions(recolored)
    )
    nuisance_same_intermediate = (
        prototype.row_intermediate(original) == prototype.row_intermediate(recolored)
    )
    nuisance_same_output = prototype.transform(
        original, {"closure": "rows_then_columns"}
    ) == prototype.transform(recolored, {"closure": "rows_then_columns"})
    endpoint_same_frame = (
        prototype.profile(original)["dimensions"]
        == prototype.profile(shifted)["dimensions"]
        and prototype.profile(original)["active_rows"]
        == prototype.profile(shifted)["active_rows"]
    )
    endpoint_changed_intermediate = (
        prototype.row_intermediate(original) != prototype.row_intermediate(shifted)
    )
    endpoint_changed_output = prototype.transform(
        original, {"closure": "rows_then_columns"}
    ) != prototype.transform(shifted, {"closure": "rows_then_columns"})
    if not all(
        (
            nuisance_same_positions,
            nuisance_same_intermediate,
            nuisance_same_output,
            endpoint_same_frame,
            endpoint_changed_intermediate,
            endpoint_changed_output,
        )
    ):
        raise AssertionError("crossed-control invariant failed")
    return (
        {
            "seed": 31,
            "query_index": 1,
            "nuisance_preserved_positions": nuisance_same_positions,
            "nuisance_preserved_intermediate": nuisance_same_intermediate,
            "nuisance_preserved_output": nuisance_same_output,
            "endpoint_preserved_dimensions_and_active_rows": endpoint_same_frame,
            "endpoint_changed_intermediate": endpoint_changed_intermediate,
            "endpoint_changed_output": endpoint_changed_output,
            "original_input_sha256": prototype.digest(original),
            "recolored_input_sha256": prototype.digest(recolored),
            "shifted_input_sha256": prototype.digest(shifted),
        },
        {"original": original, "recolored": recolored, "shifted": shifted},
    )


def _tamper_rejections(prototype) -> dict[str, Any]:
    episode = prototype.generate(7, prototype.DEFAULT, demos=2, queries=4)
    malformed: dict[str, dict[str, Any]] = {}

    wrong_label = copy.deepcopy(episode)
    wrong_label["train"][0]["output"] = [[9]]
    malformed["wrong_label"] = wrong_label

    duplicate = copy.deepcopy(episode)
    duplicate["test"][0]["input"] = copy.deepcopy(duplicate["train"][0]["input"])
    malformed["duplicate_input"] = duplicate

    bool_cell = copy.deepcopy(episode)
    bool_cell["test"][0]["input"][0][0] = True
    malformed["bool_cell"] = bool_cell

    forged_program = copy.deepcopy(episode)
    forged_program["program_solution"] = prototype.program(
        {"closure": "rows_then_columns"}
    )
    malformed["forged_program"] = forged_program

    wrong_query_count = copy.deepcopy(episode)
    wrong_query_count["test"] = wrong_query_count["test"][:-1]
    malformed["wrong_query_count"] = wrong_query_count

    forged_settings = copy.deepcopy(episode)
    forged_settings["settings"] = {"closure": "both"}
    malformed["forged_settings"] = forged_settings

    rejected = {name: _expect_rejected(prototype, value) for name, value in malformed.items()}

    # The saved certificate is advisory only: certification recomputes from pairs,
    # settings and exact program instead of trusting this mutable field.
    forged_certificate = copy.deepcopy(episode)
    forged_certificate["certificate"] = {"survivors": [{"closure": "both"}]}
    recomputed = prototype.certify(forged_certificate)
    certificate_not_trusted = recomputed["survivors"] == [prototype.DEFAULT]
    if not certificate_not_trusted:
        raise AssertionError("saved certificate influenced certification")
    return {
        "rejected": rejected,
        "all_rejected": len(rejected) == len(malformed),
        "saved_certificate_recomputed": certificate_not_trusted,
    }


def _public_projection(prototype) -> dict[str, Any]:
    episode = prototype.generate(
        19, {"closure": "rows_then_columns"}, demos=3, queries=4
    )
    first = prototype.public_turn(episode, 0)
    second = prototype.public_turn(episode, 1)
    private_keys = {"settings", "program_solution", "certificate", "seed", "task_id"}
    first_keys = set(first)
    first_test = first.get("test")
    future_hidden = (
        first_keys == {"train", "test"}
        and isinstance(first_test, list)
        and len(first_test) == 1
        and set(first_test[0]) == {"input"}
        and first_test[0]["input"] == episode["test"][0]["input"]
        and second["test"][0]["input"] == episode["test"][1]["input"]
        and second["test"][0]["input"] != first_test[0]["input"]
    )
    private_absent = not private_keys.intersection(first_keys)
    first_turn_stable = first == prototype.public_turn(episode, 0)
    if not (future_hidden and private_absent and first_turn_stable):
        raise AssertionError("public projection leaked private or future state")
    return {
        "future_queries_hidden": future_hidden,
        "private_fields_absent": private_absent,
        "first_turn_deterministic": first_turn_stable,
        "visible_demo_count": len(first["train"]),
        "visible_query_count": len(first["test"]),
        "public_sha256": prototype.digest(first),
    }


def _protected_racket(
    prototype,
    cases: Sequence[tuple[int, str, int]],
    controls: dict[str, list[list[int]]],
) -> dict[str, Any]:
    from arc_repl.racket_bridge import RacketBridge

    evaluations = 0
    episode_rows: list[dict[str, Any]] = []
    with RacketBridge(timeout=60) as bridge:
        identity = copy.deepcopy(bridge.runtime_identity)
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            raise RuntimeError("protected Racket backend required")

        def execute(source: str, grid: list[list[int]]) -> list[list[int]]:
            nonlocal evaluations
            evaluations += 1
            return prototype.execute_rule(source, grid, bridge=bridge)

        for seed, closure, demos in cases:
            setting = {"closure": closure}
            episode = prototype.generate(seed, setting, demos=demos, queries=4)
            certificate = prototype.certify(episode, execute=execute)
            episode_rows.append(
                {
                    "seed": seed,
                    "settings": setting,
                    "demos": demos,
                    "queries": 4,
                    "survivors": certificate["survivors"],
                    "rivals_refuted": sorted(certificate["extra_refutations"]),
                    "query_output_sha256": [
                        row["output_sha256"] for row in certificate["queries"]
                    ],
                }
            )

        selected_program = prototype.program({"closure": "rows_then_columns"})
        original = execute(selected_program, controls["original"])
        recolored = execute(selected_program, controls["recolored"])
        shifted = execute(selected_program, controls["shifted"])
        if original != recolored or original == shifted:
            raise AssertionError("Racket crossed-control behavior failed")

        stress = prototype.generate(
            53, {"closure": "rows_then_columns"}, demos=2, queries=4
        )["test"][-1]["input"]
        intended = execute(selected_program, stress)
        skipped = execute(prototype.SKIP_ROW_CLOSURE_PROGRAM, stress)
        wrong_order = execute(prototype.COLUMNS_THEN_ROWS_PROGRAM, stress)
        if intended == skipped or intended == wrong_order:
            raise AssertionError("counterfactual failed to change final output")

    return {
        "status": "passed",
        "runtime": identity,
        "evaluations": evaluations,
        "episodes": episode_rows,
        "crossed_controls": {
            "recolor_same_output": original == recolored,
            "shifted_endpoint_changed_output": original != shifted,
        },
        "causal_counterfactual": {
            "seed": 53,
            "query_index": 3,
            "dimensions": [len(stress), len(stress[0])],
            "intended_output_sha256": prototype.digest(intended),
            "skip_a_output_sha256": prototype.digest(skipped),
            "wrong_order_output_sha256": prototype.digest(wrong_order),
            "skip_a_changes_final": intended != skipped,
            "wrong_order_changes_final": intended != wrong_order,
        },
    }


def _source_hashes() -> dict[str, str]:
    paths = {
        "generator": TASK_HOME / "generator.py",
        "prototype": HERE / "prototype.py",
        "adapter": HERE / "adapter.py",
        "promotion": HERE / "promotion.json",
        "probe": HERE / "adversarial_probe.py",
        "tests": TASK_HOME / "tests" / "test_generator_89dfcff52ee8.py",
    }
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError("missing source-bound inputs: " + ", ".join(missing))
    return {name: _sha256(path) for name, path in paths.items()}


def run_probe(
    *,
    prototype=None,
    sweep_seeds: Iterable[int] = DEFAULT_SWEEP_SEEDS,
    racket_cases: Sequence[tuple[int, str, int]] = DEFAULT_RACKET_CASES,
    include_racket: bool = True,
) -> dict[str, Any]:
    prototype = _load_prototype() if prototype is None else prototype
    seeds = tuple(sweep_seeds)
    if not seeds or any(type(seed) is not int or seed < 0 for seed in seeds):
        raise ValueError("sweep_seeds must contain nonnegative exact integers")
    pure = _pure_sampler_sweep(prototype, seeds)
    crossed, controls = _crossed_controls(prototype)
    tamper = _tamper_rejections(prototype)
    public = _public_projection(prototype)
    if include_racket:
        racket = _protected_racket(prototype, tuple(racket_cases), controls)
    else:
        racket = {
            "status": "not_run",
            "reason": "run_probe(include_racket=False) requested a pure contract check",
            "evaluations": 0,
        }
    return {
        "schema": "arcpuzzles-89df-adversarial-probe-v1",
        "task_id": prototype.TASK_ID,
        "status": "passed",
        "source_sha256": _source_hashes(),
        "pure_sampler_sweep": pure,
        "crossed_controls": crossed,
        "tamper_rejections": tamper,
        "public_projection": public,
        "protected_racket": racket,
        "finite_scope": (
            "Bounded seeds, two declared settings and eight authored shortcut rivals; "
            "this is not universal uniqueness, owner qualification, acceptance, or training admission."
        ),
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument(
        "--sweep-seeds",
        type=int,
        default=len(DEFAULT_SWEEP_SEEDS),
        help="pure-Python seed prefix length (default: 32)",
    )
    args = parser.parse_args(argv)
    if not 1 <= args.sweep_seeds <= 256:
        parser.error("--sweep-seeds must be in 1..256")
    output = args.out
    if output.exists():
        raise FileExistsError(f"refusing to overwrite {output}")
    report = run_probe(sweep_seeds=range(args.sweep_seeds))
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False)
        handle.write("\n")
    print(
        json.dumps(
            {
                "status": report["status"],
                "output": str(output.resolve()),
                "episodes": report["pure_sampler_sweep"]["episodes"],
                "racket_evaluations": report["protected_racket"]["evaluations"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
