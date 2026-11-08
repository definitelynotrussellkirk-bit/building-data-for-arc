"""Executable regressions for the proposed bar-chart rule parameters."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from reviewer_support import canonical_path, find_root


TASK_ID = "ecd92348e78a"
PROTOTYPE_PATH = Path(__file__).parents[1] / "workspace" / "parametric" / "prototype.py"


def _load_prototype():
    assert PROTOTYPE_PATH.is_file(), "the task-local parametric prototype is missing"
    spec = importlib.util.spec_from_file_location("ecd92348e78a_parametric", PROTOTYPE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    matches = []
    with canonical_path(find_root(__file__)).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("content_hash") == TASK_ID:
                matches.append(row["program_solution"])
    assert len(matches) == 1
    return matches[0]


def test_parameter_choice_is_once_per_episode_and_four_seeds_cover_all_settings():
    prototype = _load_prototype()
    observed = [prototype.choose_parameters(seed) for seed in range(4)]

    assert observed == list(prototype.SETTINGS)
    assert prototype.choose_parameters(2) == observed[2]
    assert prototype.DEFAULT_PARAMETERS == {
        "sort_order": "descending",
        "bar_alignment": "top",
    }


def test_default_program_is_exact_canonical_and_variants_change_only_required_fragments():
    prototype = _load_prototype()
    canonical = _canonical_program()
    default = prototype.program_for("descending", "top", root=find_root(__file__))
    ascending = prototype.program_for("ascending", "top", root=find_root(__file__))
    bottom = prototype.program_for("descending", "bottom", root=find_root(__file__))
    combined = prototype.program_for("ascending", "bottom", root=find_root(__file__))

    assert default == canonical
    assert ascending == canonical.replace(
        prototype.DESCENDING_FRAGMENT,
        prototype.ASCENDING_FRAGMENT,
        1,
    ).replace(
        prototype.FIRST_BAR_HEIGHT_FRAGMENT,
        prototype.TRUE_MAX_HEIGHT_FRAGMENT,
        1,
    )
    assert bottom == canonical.replace(
        prototype.TOP_ALIGNMENT_FRAGMENT,
        prototype.BOTTOM_ALIGNMENT_FRAGMENT,
        1,
    )
    assert combined == ascending.replace(
        prototype.TOP_ALIGNMENT_FRAGMENT,
        prototype.BOTTOM_ALIGNMENT_FRAGMENT,
        1,
    )


def test_python_variants_are_pairwise_distinct_on_a_lawful_witness():
    prototype = _load_prototype()
    grid = [
        [1, 1, 0, 2, 0, 3],
        [1, 0, 0, 2, 0, 0],
        [1, 0, 0, 0, 0, 0],
    ]
    outputs = {
        setting: prototype.solve_variant(grid, *setting)
        for setting in prototype.SETTINGS
    }

    assert len({prototype.freeze(output) for output in outputs.values()}) == 4
    assert outputs[("descending", "top")] == [
        [1, 2, 3],
        [1, 2, 0],
        [1, 0, 0],
    ]


def test_racket_materialization_uses_one_setting_and_every_rival_is_taught():
    prototype = _load_prototype()
    episode = prototype.materialize_episode(0, root=find_root(__file__))
    assert episode["parameters"] == prototype.DEFAULT_PARAMETERS
    assert len(episode["private"]["train"]) == 3
    assert len(episode["private"]["test"]) == 1
    assert episode["racket_verified"] is True
    assert set(episode["rival_demonstration_differences"]) == {
        prototype.setting_key(setting)
        for setting in prototype.SETTINGS
        if setting != ("descending", "top")
    }
    assert all(episode["rival_demonstration_differences"].values())
    assert all(episode["rival_query_differs"].values())


def test_public_challenge_redacts_parameters_programs_and_query_answer():
    prototype = _load_prototype()
    episode = prototype.materialize_episode(0, root=find_root(__file__))
    public = episode["public"]
    assert set(public) == {"schema", "task_id", "train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    serialized = json.dumps(public, sort_keys=True)
    assert "sort_order" not in serialized
    assert "bar_alignment" not in serialized
    assert "program_solution" not in serialized
