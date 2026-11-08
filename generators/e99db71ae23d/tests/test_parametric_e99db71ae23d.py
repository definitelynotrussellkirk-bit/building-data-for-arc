from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root, public_challenge_bytes


TASK_ID = "e99db71ae23d"
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


def _inputs(episode: dict) -> list[list[list[int]]]:
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def _shape(grid: list[list[int]]) -> tuple[int, int]:
    return len(grid), len(grid[0])


def test_programs_and_contract_preserve_exact_canonical_default():
    prototype = _load("_e99_parametric_prototype_contract", "prototype.py")
    adapter = _load("_e99_parametric_adapter_contract", "adapter.py")
    contract = json.loads((PARAMETRIC / "promotion.json").read_text())

    canonical = {"direction_policy": "gray_toward_red_away"}
    alternate = {"direction_policy": "gray_away_red_toward"}
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        "parameters": {
            "direction_policy": [
                "gray_toward_red_away",
                "gray_away_red_toward",
            ]
        },
        "default": canonical,
        "limits": {"demos": [2, 6], "queries": [4, 4]},
        "resources": [
            f"generators/{TASK_ID}/workspace/parametric/prototype.py"
        ],
    }
    assert adapter.program(canonical) == _canonical_program()
    assert prototype.program_for("gray_toward_red_away") == _canonical_program()
    assert adapter.program(alternate) == prototype.program_for(
        "gray_away_red_toward"
    )
    assert adapter.program(alternate) != _canonical_program()


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_matched_inputs_identify_each_setting_with_four_distinct_queries(demos):
    prototype = _load("_e99_parametric_prototype_lessons", "prototype.py")
    adapter = _load("_e99_parametric_adapter_lessons", "adapter.py")
    settings = [
        {"direction_policy": "gray_toward_red_away"},
        {"direction_policy": "gray_away_red_toward"},
    ]
    episodes = [adapter.generate(107, setting, demos, 4) for setting in settings]

    assert _inputs(episodes[0]) == _inputs(episodes[1])
    for setting, episode in zip(settings, episodes):
        policy = setting["direction_policy"]
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == 4
        assert episode["program_solution"] == adapter.program(setting)
        frozen = [json.dumps(grid, separators=(",", ":")) for grid in _inputs(episode)]
        assert len(frozen) == len(set(frozen))
        assert all(
            pair["output"] == prototype.apply_policy(pair["input"], policy)
            for split in ("train", "test")
            for pair in episode[split]
        )
        certificate = prototype.lesson_certificate(episode)
        assert certificate["declared_survivors"] == [policy]
        assert certificate["plausible_survivors"] == [policy]
        assert certificate["identifiable"] is True
        assert all(certificate["query_disagreements"].values())

    public = {
        "train": episodes[0]["train"],
        "test": [{"input": pair["input"]} for pair in episodes[0]["test"]],
    }
    payload = json.loads(public_challenge_bytes(public))
    assert all("output" not in pair for pair in payload["test"])
    assert "program_solution" not in payload
    assert "direction_policy" not in payload


def test_opening_intermediate_is_load_bearing_and_not_a_fixed_diagonal_shortcut():
    prototype = _load("_e99_parametric_prototype_causal", "prototype.py")
    for policy in prototype.DIRECTION_POLICIES:
        episode = prototype.generate_episode(991, policy=policy, demos=3, queries=4)
        changed = 0
        opening_support = set()
        for grid in _inputs(episode):
            analysis = prototype.analyze_scene(grid)
            opening_support.update(tuple(vector) for vector in analysis["opening_vectors"])
            forced = prototype.apply_with_forced_opening(grid, policy, (1, 1))
            if forced != prototype.apply_policy(grid, policy):
                changed += 1
        assert opening_support == {(-1, -1), (-1, 1), (1, -1), (1, 1)}
        assert changed == len(_inputs(episode))


def test_four_query_roles_include_dual_collision_dense_and_30x30_stress():
    prototype = _load("_e99_parametric_prototype_stress", "prototype.py")
    episode = prototype.generate_episode(
        31337,
        policy="gray_toward_red_away",
        demos=3,
        queries=4,
    )
    assert [_shape(pair["input"]) for pair in episode["test"]] == [
        (10, 13),
        (16, 18),
        (21, 24),
        (30, 30),
    ]

    dual = prototype.analyze_scene(episode["test"][1]["input"])
    assert dual["collision_cells"]["gray_toward_red_away"] > 0
    assert dual["collision_cells"]["gray_away_red_toward"] > 0

    large_grid = episode["test"][-1]["input"]
    large = prototype.analyze_scene(large_grid)
    assert large["piece_count"] == 16
    assert large["orientation_support"]["2"] == [0, 1, 2, 3]
    assert large["orientation_support"]["5"] == [0, 1, 2, 3]
    assert large["collision_cells"]["gray_toward_red_away"] > 0
    assert large["collision_cells"]["gray_away_red_toward"] > 0
    assert large["clipped_cells"]["gray_toward_red_away"] > 0
    assert large["clipped_cells"]["gray_away_red_toward"] > 0
    assert large["source_span"] == {"rows": [0, 29], "cols": [0, 29]}
    quadrants = prototype.occupied_quadrants(large_grid)
    assert quadrants == [0, 1, 2, 3]


def test_generation_is_deterministic_fresh_and_strictly_bounded():
    adapter = _load("_e99_parametric_adapter_bounds", "adapter.py")
    setting = {"direction_policy": "gray_away_red_toward"}
    first = adapter.generate(5, setting, 3, 4)
    second = adapter.generate(5, setting, 3, 4)
    assert first == second
    assert first is not second
    first["train"][0]["input"][0][0] = 0
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
        (0, {"direction_policy": "gray_toward_red_away", "extra": 1}, 3, 4),
        (0, {"direction_policy": "unknown"}, 3, 4),
    ]
    for seed, settings, demos, queries in bad_calls:
        with pytest.raises(ValueError):
            adapter.generate(seed, settings, demos, queries)


def test_audit_tool_exposes_bounded_program_set_and_strict_public_projection():
    audit = _load("_e99_parametric_audit_contract", "audit.py")
    adapter = _load("_e99_parametric_adapter_audit", "adapter.py")
    setting = {"direction_policy": "gray_toward_red_away"}
    episode = adapter.generate(23, setting, 3, 4)
    programs = audit.program_map()
    assert set(programs) == {
        "gray_toward_red_away",
        "gray_away_red_toward",
        "both_toward",
        "both_away",
        "canonical_yellow_wins",
        "swapped_yellow_wins",
        "canonical_fixed_southeast",
        "swapped_fixed_southeast",
    }
    public = audit.public_projection(episode)
    assert public == {
        "train": episode["train"],
        "test": [{"input": pair["input"]} for pair in episode["test"]],
    }
    assert "program_solution" not in public
    assert all("output" not in pair for pair in public["test"])
