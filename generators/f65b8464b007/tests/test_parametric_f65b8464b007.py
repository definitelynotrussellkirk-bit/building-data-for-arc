from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root, public_challenge_bytes


TASK_ID = "f65b8464b007"
ROOT = find_root(__file__)
PARAMETRIC = ROOT / "generators" / TASK_ID / "workspace" / "parametric"


def _load(name: str, filename: str):
    path = PARAMETRIC / filename
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row["program_solution"]
    raise KeyError(TASK_ID)


def _shape(grid: list[list[int]]) -> tuple[int, int]:
    return len(grid), len(grid[0])


def _inputs(episode: dict) -> list[list[list[int]]]:
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def test_programs_and_promotion_preserve_the_exact_canonical_default():
    prototype = _load("_f65_parametric_prototype_contract", "prototype.py")
    adapter = _load("_f65_parametric_adapter_contract", "adapter.py")
    contract = json.loads((PARAMETRIC / "promotion.json").read_text())

    canonical = {"shift_rule": "next"}
    alternate = {"shift_rule": "densest_index"}
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        "parameters": {"shift_rule": ["next", "densest_index"]},
        "default": canonical,
        "limits": {"demos": [2, 6], "queries": [4, 4]},
        "resources": [
            f"generators/{TASK_ID}/workspace/parametric/prototype.py"
        ],
    }
    assert adapter.program(canonical) == _canonical_program()
    assert prototype.program(canonical) == _canonical_program()
    assert adapter.program(alternate) == prototype.program(alternate)
    assert adapter.program(alternate) != _canonical_program()


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_setting_neutral_inputs_identify_each_rule_with_four_distinct_queries(demos):
    prototype = _load("_f65_parametric_prototype_lessons", "prototype.py")
    adapter = _load("_f65_parametric_adapter_lessons", "adapter.py")
    settings = [
        {"shift_rule": "next"},
        {"shift_rule": "densest_index"},
    ]
    episodes = [adapter.generate(107, setting, demos, 4) for setting in settings]

    assert [_inputs(episode) for episode in episodes[:1]] == [
        _inputs(episodes[1])
    ]
    for setting, episode in zip(settings, episodes):
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == 4
        assert episode["program_solution"] == adapter.program(setting)
        serialized = [
            json.dumps(grid, separators=(",", ":"))
            for grid in _inputs(episode)
        ]
        assert len(serialized) == len(set(serialized))
        certificate = prototype.lesson_certificate(episode)
        assert certificate["survivors"] == [setting["shift_rule"]]
        assert certificate["identifiable"] is True
        assert all(certificate["query_disagreements"].values())

    # The four fixed query roles cover ordinary, wider, boundary, and maximum
    # lawful stress. Exact 30x30 is impossible for 3-row bands separated by
    # blank rows; 29x29 is the largest square under this grammar.
    assert [_shape(pair["input"]) for pair in episodes[0]["test"]] == [
        (9, 11),
        (13, 19),
        (17, 29),
        (29, 29),
    ]
    large = episodes[0]["test"][-1]["input"]
    assert sum(cell != 0 for row in large for cell in row) >= 250

    # Public projection includes demonstrations and only query inputs.
    public = {
        "train": episodes[0]["train"],
        "test": [{"input": pair["input"]} for pair in episodes[0]["test"]],
    }
    payload = json.loads(public_challenge_bytes(public))
    assert all("output" not in pair for pair in payload["test"])
    assert "program_solution" not in payload
    assert "shift_rule" not in payload


def test_densest_index_is_a_real_input_dependent_shift_and_not_a_fixed_shortcut():
    prototype = _load("_f65_parametric_prototype_causal", "prototype.py")
    episode = prototype.generate_episode(
        991,
        shift_rule="densest_index",
        demos=3,
        queries=4,
    )
    demo_shifts = []
    for pair in episode["train"]:
        analysis = prototype.analyze(pair["input"])
        demo_shifts.append(analysis["densest_index"])
        assert analysis["densest_index"] >= 2
        assert pair["output"] == prototype.transform(
            pair["input"], {"shift_rule": "densest_index"}
        )
        assert pair["output"] != prototype.transform(
            pair["input"], {"shift_rule": "next"}
        )
    assert len(set(demo_shifts)) >= 2

    # Every input band still exhibits the source task's one-section cyclic
    # progression; the alternative output performs a separately taught,
    # selector-derived rotation on the final band.
    for grid in _inputs(episode):
        analysis = prototype.analyze(grid)
        for index in range(1, len(analysis["patterns"])):
            previous = analysis["patterns"][index - 1]
            expected = tuple(
                previous[(section + 1) % analysis["n_sections"]]
                for section in range(analysis["n_sections"])
            )
            assert analysis["patterns"][index] == expected


def test_generation_is_deterministic_fresh_and_strictly_bounded():
    prototype = _load("_f65_parametric_prototype_bounds", "prototype.py")
    adapter = _load("_f65_parametric_adapter_bounds", "adapter.py")
    setting = {"shift_rule": "densest_index"}
    first = adapter.generate(5, setting, 3, 4)
    second = adapter.generate(5, setting, 3, 4)
    assert first == second
    assert first is not second
    first["train"][0]["input"][0][0] = 9
    assert first != second
    assert adapter.generate(5, setting, 3, 4) == second

    bad_calls = [
        (True, setting, 3, 4),
        (-1, setting, 3, 4),
        (0, setting, 1, 4),
        (0, setting, 7, 4),
        (0, setting, 3, 3),
        (0, setting, 3, 5),
        (0, {}, 3, 4),
        (0, {"shift_rule": "next", "extra": 1}, 3, 4),
        (0, {"shift_rule": "unknown"}, 3, 4),
    ]
    for seed, settings, demos, queries in bad_calls:
        with pytest.raises(ValueError):
            adapter.generate(seed, settings, demos, queries)

    for name in prototype.RIVAL_NAMES:
        assert isinstance(prototype.rival_program(name), str)
        assert prototype.rival_program(name).strip().startswith("(rule!")
