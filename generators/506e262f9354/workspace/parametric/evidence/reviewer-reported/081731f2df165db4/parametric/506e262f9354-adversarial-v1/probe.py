#!/usr/bin/env python3
"""Bounded adversarial probe for the proposed expansion-direction prototype."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys
import time

REPO = Path.cwd().resolve()
SOURCE = REPO / "generators/506e262f9354/workspace/parametric/prototype.py"
OUT = (REPO / "../checks/parametric/506e262f9354-adversarial-v1").resolve()
SUMMARY = OUT / "summary.json"
MAX_EVIDENCE = OUT / "max-count-evidence"


def load_prototype():
    spec = importlib.util.spec_from_file_location("parametric_probe_target", SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {SOURCE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def all_cells_are_exact_ints(grid) -> bool:
    return all(type(value) is int for row in grid for value in row)


def assert_public_boundary(module, episode) -> dict[str, object]:
    public = module.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    assert all(all_cells_are_exact_ints(pair["input"]) for pair in public["train"])
    assert all(all_cells_are_exact_ints(pair["output"]) for pair in public["train"])
    assert all(all_cells_are_exact_ints(pair["input"]) for pair in public["test"])

    original_id = module.public_id(episode)
    private_mutation = copy.deepcopy(episode)
    private_mutation["seed"] += 10_000
    private_mutation["program"] = "hidden program changed"
    private_mutation["parameters"]["expansion_direction"] = (
        "down"
        if episode["parameters"]["expansion_direction"] == "up"
        else "up"
    )
    private_mutation["test"][0]["output"][0][0] ^= 1
    assert module.public_id(private_mutation) == original_id

    visible_mutation = copy.deepcopy(episode)
    visible_mutation["train"][0]["output"][0][0] ^= 1
    assert module.public_id(visible_mutation) != original_id
    return {
        "public_id": original_id,
        "visible_bytes_sha256": hashlib.sha256(module.public_bytes(episode)).hexdigest(),
        "train_count": len(public["train"]),
        "query_count": len(public["test"]),
    }


def expect_value_error(callable_, label: str) -> str:
    try:
        callable_()
    except ValueError as exc:
        return f"{label}: {exc}"
    raise AssertionError(f"{label}: expected ValueError")


def main() -> int:
    started = time.monotonic()
    module = load_prototype()
    random_before = random.getstate()
    sweep_rows = []
    public_rows = []
    invalid_rows = []
    racket_evaluations = 0

    for bad_seed in (-1, True, 1.5, "1"):
        invalid_rows.append(
            expect_value_error(lambda value=bad_seed: module.select_setting(value), f"seed={bad_seed!r}")
        )
    for bad_train in (2, 9, True, 3.0):
        invalid_rows.append(
            expect_value_error(
                lambda value=bad_train: module.make_episode(
                    0, train_count=value, query_count=4
                ),
                f"train_count={bad_train!r}",
            )
        )
    for bad_query in (0, 9, True, 4.0):
        invalid_rows.append(
            expect_value_error(
                lambda value=bad_query: module.make_episode(
                    0, train_count=3, query_count=value
                ),
                f"query_count={bad_query!r}",
            )
        )

    with module.RacketBridge() as bridge:
        programs = {
            direction: module.program_for(direction, root=REPO)
            for direction in module.ALLOWED_DIRECTIONS
        }
        for difficulty in ("easy", "medium", "hard"):
            for seed in (0, 17, 2_147_483_647):
                samples = module._sample_inputs(seed, 7, difficulty)
                assert len(samples) == 7
                assert len({row["input_sha256"] for row in samples}) == 7
                max_sample_index = max(row["sample_index"] for row in samples)
                setting_hashes = {direction: [] for direction in module.ALLOWED_DIRECTIONS}
                for sample in samples:
                    grid = sample["grid"]
                    assert all_cells_are_exact_ints(grid)
                    outputs = {}
                    for direction in module.ALLOWED_DIRECTIONS:
                        output = module.execute_rule(
                            programs[direction], grid, bridge=bridge
                        )
                        racket_evaluations += 1
                        assert output == module.python_mirror(
                            grid, expansion_direction=direction
                        )
                        assert all_cells_are_exact_ints(output)
                        outputs[direction] = output
                        setting_hashes[direction].append(module.grid_sha256(output))
                    assert outputs["up"] != outputs["down"]
                sweep_rows.append(
                    {
                        "difficulty": difficulty,
                        "seed": seed,
                        "distinct_inputs": len(samples),
                        "max_sample_index": max_sample_index,
                        "up_output_sha256": setting_hashes["up"],
                        "down_output_sha256": setting_hashes["down"],
                    }
                )

        for seed, direction, difficulty in (
            (5, "up", "easy"),
            (29, "down", "medium"),
            (2_147_483_647, "up", "hard"),
        ):
            episode = module.make_episode(
                seed,
                expansion_direction=direction,
                difficulty=difficulty,
                train_count=3,
                query_count=4,
                root=REPO,
                bridge=bridge,
            )
            racket_evaluations += 14
            rival = episode["parameter_rivals"][0]
            assert rival["status"] == "refuted_by_demonstrations"
            assert rival["demonstration_mismatch_indices"] == [0, 1, 2]
            assert rival["query_mismatch_indices"] == [0, 1, 2, 3]
            public_rows.append(assert_public_boundary(module, episode))

        if MAX_EVIDENCE.exists():
            raise FileExistsError(MAX_EVIDENCE)
        max_report = module.write_evidence(
            seed=41,
            out=MAX_EVIDENCE,
            root=REPO,
            difficulty="hard",
            train_count=8,
            query_count=8,
            bridge=bridge,
        )
        racket_evaluations += 72

    # Attack the sampler's retry/validation boundary without invoking Racket.
    original_generator = module._GEN
    try:
        witness = [
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 7, 0, 0, 0],
            [0, 0, 0, 7, 0, 0, 0],
            [0, 0, 0, 7, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
        ]

        class DuplicateGenerator:
            calls = 0

            def generate(self, *_args, **_kwargs):
                self.calls += 1
                return copy.deepcopy(witness)

            @staticmethod
            def self_check(_grid):
                return []

        duplicate = DuplicateGenerator()
        module._GEN = duplicate
        try:
            module._sample_inputs(3, 2, "easy")
        except RuntimeError as exc:
            duplicate_error = str(exc)
        else:
            raise AssertionError("duplicate sampler should exhaust its bounded retries")
        assert duplicate.calls == 40
        assert "within 40 attempts" in duplicate_error

        class InvalidGenerator:
            calls = 0

            def generate(self, *_args, **_kwargs):
                self.calls += 1
                return copy.deepcopy(witness)

            @staticmethod
            def self_check(_grid):
                return ["synthetic invalid grid"]

        invalid = InvalidGenerator()
        module._GEN = invalid
        try:
            module._sample_inputs(3, 1, "easy")
        except RuntimeError as exc:
            invalid_error = str(exc)
        else:
            raise AssertionError("invalid generated grid should fail immediately")
        assert invalid.calls == 1
        assert "synthetic invalid grid" in invalid_error
    finally:
        module._GEN = original_generator

    assert random.getstate() == random_before
    assert max_report["counts"] == {
        "episodes": 2,
        "train_pairs": 16,
        "query_pairs": 16,
        "distinct_input_grids": 16,
        "settings_exercised": 2,
        "canonical_pairs_checked": 6,
        "ambiguous_parameter_rivals": 0,
    }

    elapsed = time.monotonic() - started
    result = {
        "schema": "arcpuzzles-parametric-adversarial-probe-v1",
        "status": "pass",
        "task_id": module.TASK_ID,
        "prototype_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "surfaces": [
            "sampler/count/retry boundaries",
            "parameter/Racket parity and public/private export",
        ],
        "elapsed_seconds": round(elapsed, 3),
        "difficulty_seed_combinations": len(sweep_rows),
        "distinct_inputs_exercised": sum(row["distinct_inputs"] for row in sweep_rows),
        "racket_evaluations": racket_evaluations,
        "max_observed_sample_index": max(row["max_sample_index"] for row in sweep_rows),
        "invalid_numeric_type_rejections": invalid_rows,
        "bounded_retry": {
            "duplicate_attempts": duplicate.calls,
            "duplicate_error": duplicate_error,
            "invalid_attempts": invalid.calls,
            "invalid_error": invalid_error,
        },
        "public_projection_checks": public_rows,
        "max_count_evidence": {
            "path": "max-count-evidence/report.json",
            "counts": max_report["counts"],
            "report_sha256": hashlib.sha256(
                (MAX_EVIDENCE / "report.json").read_bytes()
            ).hexdigest(),
        },
        "sweep": sweep_rows,
        "limitations": [
            "bounded to three seeds per difficulty and one max-count evidence write",
            "declared-rival checks do not prove uniqueness against undeclared programs",
        ],
    }
    SUMMARY.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({key: result[key] for key in (
        "status", "difficulty_seed_combinations", "distinct_inputs_exercised",
        "racket_evaluations", "max_observed_sample_index", "elapsed_seconds"
    )}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
