"""Focused tests for the native reflection-policy parametric family."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root, load_selected_generator

TASK_ID = "b8aea529acfd"
ROOT = find_root(__file__)
TASK_DIR = Path(__file__).resolve().parents[1]
PARAMETRIC = TASK_DIR / "workspace" / "parametric"
PROTOTYPE_PATH = PARAMETRIC / "prototype.py"
ADAPTER_PATH = PARAMETRIC / "adapter.py"
PROMOTION_PATH = PARAMETRIC / "promotion.json"
POLICIES = ("left_right", "top_bottom", "long_dimension", "short_dimension")


def _load(name: str, path: Path):
    if not path.is_file():
        pytest.fail(f"missing implementation file: {path.relative_to(ROOT)}")
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    matches = []
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            matches.append(row["program_solution"])
    assert len(matches) == 1
    return matches[0]


def _freeze(grid):
    return tuple(tuple(row) for row in grid)


def test_programs_preserve_exact_canonical_default_and_define_four_nearby_policies():
    prototype = _load("reflection_policy_programs", PROTOTYPE_PATH)

    assert prototype.POLICIES == POLICIES
    assert prototype.program_for("left_right") == _canonical_program()
    assert prototype.program_for("top_bottom") == (
        "(rule! (lambda (g) (flip-ud (crop-to-content g))))"
    )
    assert "(cols body)" in prototype.program_for("long_dimension")
    assert "(rows body)" in prototype.program_for("long_dimension")
    assert prototype.program_for("long_dimension") != prototype.program_for("short_dimension")


@pytest.mark.parametrize("demos", range(2, 7))
def test_episode_inputs_are_distinct_canonical_grammar_and_cover_both_aspects(demos):
    prototype = _load(f"reflection_policy_inputs_{demos}", PROTOTYPE_PATH)
    generator, _path, _sha = load_selected_generator(TASK_ID, root=ROOT)

    grids = prototype.episode_inputs(17, demos=demos, queries=4)
    assert len(grids) == demos + 4
    assert len({_freeze(grid) for grid in grids}) == len(grids)
    assert all(generator.self_check(grid) == [] for grid in grids)

    demo_aspects = {prototype.analyze_input(grid)["aspect"] for grid in grids[:demos]}
    assert demo_aspects == {"wide", "tall"}
    assert all(prototype.analyze_input(grid)["aspect"] in {"wide", "tall"} for grid in grids)
    assert all(
        prototype.flip_lr(prototype.crop(grid)) != prototype.flip_ud(prototype.crop(grid))
        for grid in grids
    )

    query_shapes = [(len(grid), len(grid[0])) for grid in grids[demos:]]
    assert query_shapes.count((30, 30)) == 2
    assert all(max(shape) > 20 for shape in query_shapes)
    assert all(sum(cell != 0 for row in grid for cell in row) >= 150 for grid in grids[demos:])


def test_each_policy_is_identified_by_demonstrations_only_and_queries_share_inputs():
    prototype = _load("reflection_policy_identification", PROTOTYPE_PATH)
    episodes = {
        policy: prototype.generate_episode(23, reflection_policy=policy, demos=3, queries=4)
        for policy in POLICIES
    }

    input_sets = [
        [pair["input"] for pair in episode["train"] + episode["test"]]
        for episode in episodes.values()
    ]
    assert input_sets[1:] == input_sets[:-1]

    for chosen, episode in episodes.items():
        survivors = []
        for candidate in POLICIES:
            if all(
                prototype.apply_policy(pair["input"], candidate) == pair["output"]
                for pair in episode["train"]
            ):
                survivors.append(candidate)
        assert survivors == [chosen]
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 4
        assert episode["program_solution"] == prototype.program_for(chosen)


@pytest.mark.parametrize("policy", ("long_dimension", "short_dimension"))
def test_demonstrations_refute_using_canvas_aspect_as_the_intermediate(policy):
    """Catches episodes where the canvas and cropped body teach the same branch."""
    prototype = _load(f"reflection_policy_canvas_rival_{policy}", PROTOTYPE_PATH)
    episode = prototype.generate_episode(
        19, reflection_policy=policy, demos=3, queries=4
    )

    rival_outputs = []
    for pair in episode["train"]:
        grid = pair["input"]
        body = prototype.crop(grid)
        canvas_is_wide = len(grid[0]) >= len(grid)
        use_lr = canvas_is_wide if policy == "long_dimension" else not canvas_is_wide
        rival_outputs.append(
            prototype.flip_lr(body) if use_lr else prototype.flip_ud(body)
        )

    assert any(
        rival != pair["output"]
        for rival, pair in zip(rival_outputs, episode["train"], strict=True)
    )


def test_policy_signatures_require_crop_derived_aspect_intermediate():
    prototype = _load("reflection_policy_dependency", PROTOTYPE_PATH)
    wide, tall = prototype.episode_inputs(5, demos=2, queries=4)[:2]

    wide_outputs = {policy: prototype.apply_policy(wide, policy) for policy in POLICIES}
    tall_outputs = {policy: prototype.apply_policy(tall, policy) for policy in POLICIES}

    assert wide_outputs["long_dimension"] == wide_outputs["left_right"]
    assert wide_outputs["short_dimension"] == wide_outputs["top_bottom"]
    assert tall_outputs["long_dimension"] == tall_outputs["top_bottom"]
    assert tall_outputs["short_dimension"] == tall_outputs["left_right"]
    assert wide_outputs["long_dimension"] != wide_outputs["short_dimension"]
    assert tall_outputs["long_dimension"] != tall_outputs["short_dimension"]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"seed": True},
        {"seed": -1},
        {"demos": True},
        {"demos": 1},
        {"demos": 7},
        {"queries": 3},
        {"queries": 5},
        {"queries": 4.0},
        {"reflection_policy": "diagonal"},
    ],
)
def test_episode_api_rejects_invalid_counts_and_settings(kwargs):
    prototype = _load("reflection_policy_invalid", PROTOTYPE_PATH)
    call = {"seed": 0, "reflection_policy": "left_right", "demos": 3, "queries": 4}
    call.update(kwargs)
    with pytest.raises((TypeError, ValueError)):
        prototype.generate_episode(**call)


def test_public_projection_hides_settings_program_and_all_query_answers():
    prototype = _load("reflection_policy_public", PROTOTYPE_PATH)
    episode = prototype.generate_episode(
        31, reflection_policy="long_dimension", demos=3, queries=4
    )
    public = prototype.public_payload(episode)
    serialized = json.dumps(public, sort_keys=True)

    assert "long_dimension" not in serialized
    assert episode["program_solution"] not in serialized
    assert all(set(pair) == {"input"} for pair in public["test"])
    assert public["train"] == episode["train"]

    first_turn = prototype.first_turn_payload(episode)
    assert first_turn == {
        "train": episode["train"],
        "test": [{"input": episode["test"][0]["input"]}],
    }
    mutated = deepcopy(episode)
    mutated["test"][1]["input"][0][0] = 9
    mutated["test"][0]["output"][0][0] = (mutated["test"][0]["output"][0][0] + 1) % 10
    mutated["reflection_policy"] = "short_dimension"
    assert prototype.first_turn_payload(mutated) == first_turn


def test_promotion_adapter_is_thin_strict_and_bounded_to_four_queries():
    prototype = _load("reflection_policy_promotion_prototype", PROTOTYPE_PATH)
    adapter = _load("reflection_policy_adapter", ADAPTER_PATH)
    promotion = json.loads(PROMOTION_PATH.read_text(encoding="utf-8"))

    assert promotion == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/b8aea529acfd/workspace/parametric/adapter.py",
        "parameters": {"reflection_policy": list(POLICIES)},
        "default": {"reflection_policy": "left_right"},
        "limits": {"demos": [2, 6], "queries": [4, 4]},
    }
    assert adapter.program({"reflection_policy": "left_right"}) == _canonical_program()
    generated = adapter.generate(41, {"reflection_policy": "short_dimension"}, 2, 4)
    assert generated["program_solution"] == prototype.program_for("short_dimension")
    assert len(generated["train"]) == 2
    assert len(generated["test"]) == 4

    for settings in ({}, None, {"reflection_policy": "left_right", "extra": 1}):
        with pytest.raises(ValueError, match="exactly reflection_policy"):
            adapter.program(settings)
