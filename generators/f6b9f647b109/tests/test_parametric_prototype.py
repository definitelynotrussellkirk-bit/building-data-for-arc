"""Executable checks for the task-local path-order parameter prototype."""
from __future__ import annotations

from functools import lru_cache
import hashlib
import importlib.util
import json
from pathlib import Path

from reviewer_support import canonical_path, find_root


TASK_ID = "f6b9f647b109"
PROTOTYPE_PATH = Path(__file__).parents[1] / "workspace" / "parametric" / "prototype.py"


@lru_cache(maxsize=1)
def _prototype():
    assert PROTOTYPE_PATH.is_file(), "parametric prototype has not been implemented"
    spec = importlib.util.spec_from_file_location(
        "task_f6b9f647b109_parametric",
        PROTOTYPE_PATH,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    with canonical_path(find_root(__file__)).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row["program_solution"]
    raise AssertionError(TASK_ID)


def _seed_by_setting(prototype) -> dict[str, int]:
    found: dict[str, int] = {}
    for seed in range(64):
        setting = prototype.choose_parameters(seed)[prototype.PARAMETER_NAME]
        found.setdefault(setting, seed)
        if set(found) == set(prototype.POSITION_VALUES):
            return found
    raise AssertionError("could not find deterministic seeds for every setting")


def test_canonical_program_is_exact_and_alternative_changes_only_phase_order():
    prototype = _prototype()
    canonical = _canonical_program()
    default_program = prototype.program_for(
        prototype.CANONICAL_DEFAULT,
        root=find_root(__file__),
    )
    alternative = prototype.program_for("before_diagonals", root=find_root(__file__))

    assert default_program == canonical
    assert canonical.count(prototype.CANONICAL_PHASE_FRAGMENT) == 1
    assert prototype.STRAIGHT_FIRST_PHASE_FRAGMENT not in canonical
    assert alternative == canonical.replace(
        prototype.CANONICAL_PHASE_FRAGMENT,
        prototype.STRAIGHT_FIRST_PHASE_FRAGMENT,
        1,
    )


def test_parameter_is_chosen_once_and_both_settings_have_racket_verified_episodes():
    prototype = _prototype()
    seeds = _seed_by_setting(prototype)

    assert set(seeds) == set(prototype.POSITION_VALUES)
    for setting, seed in seeds.items():
        evidence = prototype.materialize_episode(
            seed,
            difficulty="easy",
            root=find_root(__file__),
        )

        assert evidence["parameter"] == {
            prototype.PARAMETER_NAME: setting,
            "allowed": list(prototype.POSITION_VALUES),
            "canonical_default": prototype.CANONICAL_DEFAULT,
        }
        assert evidence["racket_verified"] is True
        assert len(evidence["private"]["train"]) == prototype.N_TRAIN == 4
        assert len(evidence["private"]["test"]) == prototype.N_TEST == 1
        assert evidence["demonstration_difference_indices"]
        assert evidence["query_difference_indices"] == [0]

        for name, program in evidence["programs"].items():
            assert name in prototype.POSITION_VALUES
            assert program["sha256"] == hashlib.sha256(program["text"].encode()).hexdigest()

        public = evidence["public"]
        assert set(public) == {"schema", "task_id", "train", "test"}
        assert all(set(pair) == {"input", "output"} for pair in public["train"])
        assert all(set(pair) == {"input"} for pair in public["test"])
        serialized = json.dumps(public, sort_keys=True)
        assert prototype.PARAMETER_NAME not in serialized
        assert "program_solution" not in serialized
        assert "query_output" not in serialized
