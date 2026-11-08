"""Focused checks for the proposed episode-level marker-order prototype."""
from __future__ import annotations

from functools import cache
import importlib
import importlib.util
from pathlib import Path

import pytest

from reviewer_support import find_root, load_selected_generator


TASK = "1034300a135f"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
REPO_ROOT = find_root(__file__)
_SELECTED, SELECTED_SOURCE, _SOURCE_SHA = load_selected_generator(TASK, root=REPO_ROOT)
MANIFEST = REPO_ROOT / "RUNTIME_MANIFEST.json"
if MANIFEST.is_file():
    import json
    identity = f"generators/{TASK}/workspace/parametric/prototype.py"
    entries = [
        row for row in json.loads(MANIFEST.read_text())["files"]
        if row.get("library_path") == identity
    ]
    entries.sort(key=lambda row: row.get("runtime_path") == identity)
    PROTOTYPE_PATH = REPO_ROOT / entries[0]["runtime_path"] if entries else SELECTED_SOURCE.parent / "workspace/parametric/prototype.py"
else:
    PROTOTYPE_PATH = SELECTED_SOURCE.parent / "workspace/parametric/prototype.py"


@cache
def prototype():
    assert PROTOTYPE_PATH.is_file(), "marker-order prototype is missing"
    spec = importlib.util.spec_from_file_location(
        "generator_1034300a135f_marker_order_prototype",
        PROTOTYPE_PATH,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_parameter_contract_and_seed_choice_are_episode_level():
    p = prototype()
    assert p.PARAMETER_NAME == "marker_order"
    assert p.ALLOWED_MARKER_ORDERS == ("near_to_far", "far_to_near")
    assert p.DEFAULT_MARKER_ORDER == "near_to_far"
    assert {p.choose_parameters(seed)[p.PARAMETER_NAME] for seed in range(8)} == {
        "near_to_far",
        "far_to_near",
    }
    assert p.choose_parameters(17) == p.choose_parameters(17)
    with pytest.raises(TypeError, match="episode seed"):
        p.choose_parameters(True)


def test_shared_inputs_distinguish_settings_and_default_matches_canonical():
    p = prototype()
    seen = set()
    for seed in range(6):
        for pair_index in range(3):
            grid = p.build_input(seed, pair_index)
            seen.add(tuple(map(tuple, grid)))
            assert GEN.self_check(grid) == []
            near = p.python_reference(grid, marker_order="near_to_far")
            far = p.python_reference(grid, marker_order="far_to_near")
            assert near == GEN.rule_mirror(grid)
            assert near != far
    assert len(seen) == 18


def test_episode_public_redaction_and_rival_checks_are_complete():
    p = prototype()
    for marker_order in p.ALLOWED_MARKER_ORDERS:
        episode = p.build_episode(19, marker_order=marker_order)
        public = p.public_challenge(episode)
        assert episode["parameter"] == {"marker_order": marker_order}
        assert set(public) == {"schema", "train", "test"}
        assert len(public["train"]) == 2
        assert len(public["test"]) == 1
        assert set(public["test"][0]) == {"input"}
        assert "parameter" not in repr(public)
        assert "marker_order" not in repr(public)
        other = next(
            value for value in p.ALLOWED_MARKER_ORDERS if value != marker_order
        )
        assert all(
            p.python_reference(pair["input"], marker_order=other) != pair["output"]
            for pair in episode["train"]
        )


def test_racket_programs_are_distinct_setting_specific_and_hashable():
    p = prototype()
    programs = {
        marker_order: p.racket_program(marker_order)
        for marker_order in p.ALLOWED_MARKER_ORDERS
    }
    assert programs["near_to_far"] != programs["far_to_near"]
    assert "MARKER-ORDER 'near_to_far" in programs["near_to_far"]
    assert "MARKER-ORDER 'far_to_near" in programs["far_to_near"]
    for marker_order, program in programs.items():
        assert p.rule_sha256(marker_order) == p.sha256_text(program)
