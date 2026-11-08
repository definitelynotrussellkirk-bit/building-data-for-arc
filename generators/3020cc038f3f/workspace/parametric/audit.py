"""Deterministic structural and protected-Racket audit for 3020cc038f3f."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

HERE = Path(__file__).resolve().parent
_PROTOTYPE_PATH = HERE / "prototype.py"
_SPEC = importlib.util.spec_from_file_location(
    "_arc_3020cc038f3f_parametric_audit_prototype", _PROTOTYPE_PATH
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load adjacent prototype at {_PROTOTYPE_PATH}")
prototype = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = prototype
_SPEC.loader.exec_module(prototype)

SCHEMA = "3020cc038f3f-larger-rotate-audit-v1"
SETTINGS = [{prototype.PARAMETER: value} for value in prototype.SETTINGS]
DEMO_COUNTS = list(range(prototype.MIN_DEMOS, prototype.MAX_DEMOS + 1))


def _freeze(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def _digest(value: Any) -> str:
    body = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(body).hexdigest()


def _diff_cells(first: list[list[int]], second: list[list[int]]) -> int:
    height = max(len(first), len(second))
    width = max(len(first[0]), len(second[0]))
    different = 0
    for row in range(height):
        for col in range(width):
            a = first[row][col] if row < len(first) and col < len(first[0]) else None
            b = second[row][col] if row < len(second) and col < len(second[0]) else None
            different += a != b
    return different


def structural_stress(seed_count: int = 24) -> dict[str, Any]:
    if type(seed_count) is not int or not 1 <= seed_count <= 10_000:
        raise ValueError("seed_count must be an exact integer in 1..10000")

    failures: list[dict[str, Any]] = []
    episodes = 0
    visible_pairs = 0
    matched_input_checks = 0
    prefix_checks = 0
    public_turn_checks = 0
    stress_30x30_checks = 0
    finite_rival_certificates = 0

    for seed in range(seed_count):
        for demos in DEMO_COUNTS:
            by_setting: dict[str, dict[str, Any]] = {}
            for settings in SETTINGS:
                selected = settings[prototype.PARAMETER]
                context = {"seed": seed, "demos": demos, "setting": selected}
                try:
                    episode = prototype.generate(seed, settings, demos=demos, queries=4)
                    by_setting[selected] = episode
                    episodes += 1
                    pairs = episode["train"] + episode["test"]
                    visible_pairs += len(pairs)
                    frozen = [_freeze(pair["input"]) for pair in pairs]
                    if len(frozen) != len(set(frozen)):
                        raise AssertionError("episode contains duplicate visible inputs")
                    certificate = episode["certificate"]
                    if certificate["survivors"] != [settings]:
                        raise AssertionError("demonstrations do not isolate the selected setting")
                    if not all(certificate["rival_refutations"].values()):
                        raise AssertionError("an authored finite rival survives demonstrations")
                    finite_rival_certificates += 1

                    short = prototype.generate(seed, settings, demos=2, queries=4)
                    one = prototype.generate(seed, settings, demos=demos, queries=1)
                    if episode["train"][:2] != short["train"]:
                        raise AssertionError("demonstration prefixes depend on requested count")
                    if episode["test"][0] != one["test"][0]:
                        raise AssertionError("first query depends on requested query count")
                    prefix_checks += 1

                    for query_index in range(4):
                        public = prototype.public_turn(episode, query_index)
                        if set(public) != {"train", "test"}:
                            raise AssertionError("public projection has unexpected top-level fields")
                        if public["train"] != episode["train"]:
                            raise AssertionError("public projection changed demonstrations")
                        if public["test"] != [{"input": episode["test"][query_index]["input"]}]:
                            raise AssertionError("public projection leaks or selects the wrong query")
                        public_turn_checks += 1

                    stress = episode["test"][3]["input"]
                    if (len(stress), len(stress[0])) != (30, 30):
                        raise AssertionError("fourth query is not exactly 30x30")
                    cells = [
                        (row, col)
                        for row, values in enumerate(stress)
                        for col, value in enumerate(values)
                        if value in (1, 2)
                    ]
                    row_span = max(row for row, _col in cells) - min(row for row, _col in cells) + 1
                    col_span = max(col for _row, col in cells) - min(col for _row, col in cells) + 1
                    boundary = any(
                        row in (0, 29) or col in (0, 29) for row, col in cells
                    )
                    if len(cells) < 100 or row_span < 24 or col_span < 24 or not boundary:
                        raise AssertionError(
                            f"30x30 stress is not substantive: cells={len(cells)}, "
                            f"span={row_span}x{col_span}, boundary={boundary}"
                        )
                    stress_30x30_checks += 1
                except Exception as exc:
                    failures.append({**context, "error": f"{type(exc).__name__}: {exc}"})

            if set(by_setting) == set(prototype.SETTINGS):
                identity = by_setting["identity"]["train"] + by_setting["identity"]["test"]
                rotated = by_setting["rotate_larger_cw"]["train"] + by_setting["rotate_larger_cw"]["test"]
                if [pair["input"] for pair in identity] != [pair["input"] for pair in rotated]:
                    failures.append(
                        {
                            "seed": seed,
                            "demos": demos,
                            "setting": "matched_inputs",
                            "error": "settings received different visible inputs",
                        }
                    )
                else:
                    matched_input_checks += 1

    return {
        "schema": SCHEMA,
        "scope": (
            "Python structural, matched-input, prefix-stability, public-projection, "
            "30x30 stress and finite-rival sweep. Protected Racket is reported separately."
        ),
        "seed_count": seed_count,
        "seed_range": [0, seed_count - 1],
        "settings": SETTINGS,
        "demo_counts": DEMO_COUNTS,
        "queries": 4,
        "episodes": episodes,
        "visible_pairs": visible_pairs,
        "matched_input_checks": matched_input_checks,
        "prefix_checks": prefix_checks,
        "public_turn_checks": public_turn_checks,
        "stress_30x30_checks": stress_30x30_checks,
        "finite_rival_certificates": finite_rival_certificates,
        "failures": failures,
    }


class RacketRunner:
    """One protected bridge with exact-program and input-result caching."""

    def __enter__(self):
        from arc_repl.racket_bridge import RacketBridge

        self.bridge = RacketBridge()
        self.identity = self.bridge.runtime_identity
        if self.identity.get("backend") != "racket" or self.identity.get("protected") is not True:
            self.bridge.close()
            raise RuntimeError("live protected Racket backend required")
        self.rule_cache: dict[str, str] = {}
        self.result_cache: dict[tuple[str, str], list[list[int]]] = {}
        self.requests = 0
        self.unique_evaluations = 0
        return self

    def __call__(self, source: str, grid: list[list[int]]) -> list[list[int]]:
        from puzzle_generators.rule_wrap import wrap_rule

        prototype._grid(grid)
        self.requests += 1
        key = (hashlib.sha256(source.encode()).hexdigest(), _digest(grid))
        if key in self.result_cache:
            return self.result_cache[key]
        if source not in self.rule_cache:
            self.rule_cache[source] = wrap_rule(source)
        literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
        result = self.bridge.eval_text(f"({self.rule_cache[source]} {literal})")
        self.result_cache[key] = result
        self.unique_evaluations += 1
        return result

    def __exit__(self, *_exc):
        self.bridge.close()


def protected_audit() -> tuple[dict[str, Any], dict[str, Any]]:
    jobs = []
    failures: list[dict[str, Any]] = []
    seeds = (0, 17)
    demo_counts = (2, 3, 6)

    with RacketRunner() as execute:
        for seed in seeds:
            for demos in demo_counts:
                for settings in SETTINGS:
                    selected = settings[prototype.PARAMETER]
                    context = {"seed": seed, "demos": demos, "setting": selected}
                    try:
                        episode = prototype.generate(seed, settings, demos=demos, queries=4)
                        pairs = episode["train"] + episode["test"]
                        mismatches = []
                        for index, pair in enumerate(pairs):
                            actual = execute(episode["program_solution"], pair["input"])
                            if actual != pair["output"]:
                                mismatches.append(index)
                        survivors = []
                        for candidate in SETTINGS:
                            source = prototype.program(candidate)
                            if all(
                                execute(source, pair["input"]) == pair["output"]
                                for pair in episode["train"]
                            ):
                                survivors.append(candidate)
                        if mismatches:
                            raise AssertionError(f"Racket/Python label mismatches at {mismatches}")
                        if survivors != [settings]:
                            raise AssertionError(f"Racket demo survivors are {survivors}")
                        jobs.append(
                            {
                                **context,
                                "pairs": len(pairs),
                                "program_sha256": hashlib.sha256(
                                    episode["program_solution"].encode()
                                ).hexdigest(),
                                "survivors": survivors,
                                "input_sha256": [_digest(pair["input"]) for pair in pairs],
                            }
                        )
                    except Exception as exc:
                        failures.append({**context, "error": f"{type(exc).__name__}: {exc}"})

        witness_episode = prototype.generate(
            17, {prototype.PARAMETER: "rotate_larger_cw"}, demos=3, queries=4
        )
        witness_pair = witness_episode["test"][0]
        analysis = prototype.analyze_input(witness_pair["input"])
        correct_source = prototype.program({prototype.PARAMETER: "rotate_larger_cw"})
        wrong_source = (HERE / "rotate_smaller_counterfactual.rkt").read_text(encoding="utf-8")
        correct = execute(correct_source, witness_pair["input"])
        wrong = execute(wrong_source, witness_pair["input"])
        expected_wrong = prototype.transform_with_selected_color(
            witness_pair["input"], analysis["smaller_color"]
        )
        if correct != witness_pair["output"]:
            failures.append({"witness": "correct", "error": "correct Racket output mismatches claim"})
        if wrong != expected_wrong:
            failures.append({"witness": "wrong", "error": "counterfactual Racket output mismatches Python"})
        if correct == wrong:
            failures.append({"witness": "causal", "error": "wrong intermediate did not change output"})

        witness = {
            "schema": "3020cc038f3f-causal-witness-v1",
            "task_id": prototype.TASK_ID,
            "setting": {prototype.PARAMETER: "rotate_larger_cw"},
            "seed": 17,
            "split": "query",
            "query_index": 0,
            "step_a": "normalize both operands and compare occupied cell counts",
            "input_dependent_intermediate": {
                "name": "selected_color",
                "correct": analysis["larger_color"],
                "wrong": analysis["smaller_color"],
                "sizes": analysis["sizes"],
            },
            "step_b": (
                "rotate only selected_color clockwise, then apply control-selected "
                "union/XOR/intersection to the transformed normalized masks"
            ),
            "why_b_depends_on_a": (
                "the selected color determines which normalized mask is rotated; changing only "
                "that intermediate changes the final Racket output"
            ),
            "input": witness_pair["input"],
            "control": analysis["ctrl"],
            "correct_program": correct_source,
            "correct_program_sha256": hashlib.sha256(correct_source.encode()).hexdigest(),
            "wrong_intermediate_program": wrong_source,
            "wrong_intermediate_program_sha256": hashlib.sha256(wrong_source.encode()).hexdigest(),
            "correct_output": correct,
            "wrong_intermediate_output": wrong,
            "different_cells_with_shape_padding": _diff_cells(correct, wrong),
            "input_sha256": _digest(witness_pair["input"]),
            "correct_output_sha256": _digest(correct),
            "wrong_output_sha256": _digest(wrong),
            "protected_racket": True,
            "runtime_identity": execute.identity,
        }
        execution = {
            "schema": "3020cc038f3f-protected-racket-audit-v1",
            "task_id": prototype.TASK_ID,
            "seeds": list(seeds),
            "demo_counts": list(demo_counts),
            "queries": 4,
            "jobs": jobs,
            "job_count": len(jobs),
            "requests": execute.requests,
            "unique_evaluations": execute.unique_evaluations,
            "programs_compiled": len(execute.rule_cache),
            "runtime_identity": execute.identity,
            "failures": failures,
        }
    return execution, witness


def write_json(path: Path, value: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=24, help="structural seeds starting at zero")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--witness-out", type=Path, required=True)
    args = parser.parse_args()

    structural = structural_stress(args.seeds)
    protected, witness = protected_audit()
    report = {
        "schema": SCHEMA,
        "task_id": prototype.TASK_ID,
        "structural": structural,
        "protected_racket": protected,
        "source_sha256": {
            "audit.py": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            **prototype.source_hashes(),
        },
    }
    write_json(args.out, report)
    write_json(args.witness_out, witness)
    failures = len(structural["failures"]) + len(protected["failures"])
    print(
        json.dumps(
            {
                "status": "pass" if failures == 0 else "fail",
                "episodes": structural["episodes"],
                "visible_pairs": structural["visible_pairs"],
                "protected_jobs": protected["job_count"],
                "racket_unique_evaluations": protected["unique_evaluations"],
                "witness_different_cells": witness["different_cells_with_shape_padding"],
                "failures": failures,
                "out": str(args.out),
                "witness_out": str(args.witness_out),
            },
            sort_keys=True,
        )
    )
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
