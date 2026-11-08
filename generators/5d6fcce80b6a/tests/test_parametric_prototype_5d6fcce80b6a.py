"""Tests for the task-local parametric rule prototype."""
from __future__ import annotations

import importlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from reviewer_support import find_root, load_selected_generator

ROOT = find_root(__file__)
TASK_ROOT = ROOT / "generators/5d6fcce80b6a"
if (ROOT / "shared/runtime/puzzle_generators").is_dir():
    sys.path.insert(0, str(ROOT / "shared/runtime"))
elif (ROOT / "puzzle_generators").is_dir():
    sys.path.insert(0, str(ROOT))
else:
    raise FileNotFoundError(f"No local puzzle_generators runtime under {ROOT}")

from puzzle_generators.rule_wrap import wrap_rule

GEN, _GEN_PATH, _GEN_SHA256 = load_selected_generator(
    "5d6fcce80b6a", root=ROOT
)


PROTO_PATH = TASK_ROOT / "workspace/parametric/prototype.py"


def _load_proto():
    assert PROTO_PATH.is_file(), "parametric prototype module is missing"
    spec = importlib.util.spec_from_file_location(
        "parametric_prototype_5d6fcce80b6a_tests", PROTO_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _grid_literal(grid: list[list[int]]) -> str:
    rows = " ".join("(" + " ".join(str(v) for v in row) + ")" for row in grid)
    return f"'({rows})"


def _eval_program(bridge, program: str, grid: list[list[int]]):
    return bridge.eval_text(f"({wrap_rule(program)} {_grid_literal(grid)})")


def test_parameter_contract_and_seed_selection_are_episode_level() -> None:
    proto = _load_proto()
    assert proto.CANONICAL_SETTING == proto.RuleSetting("main", "through_last")
    assert set(proto.ALL_SETTINGS) == {
        proto.RuleSetting("main", "through_last"),
        proto.RuleSetting("anti", "through_last"),
        proto.RuleSetting("main", "strict_between"),
        proto.RuleSetting("anti", "strict_between"),
    }
    assert proto.PARAMETERS["copy_diagonal"]["default"] == "main"
    assert proto.PARAMETERS["separator_policy"]["default"] == "through_last"

    representative = proto.representative_seeds()
    assert set(representative) == set(proto.ALL_SETTINGS)
    for setting, seed in representative.items():
        assert proto.setting_from_seed(seed) == setting
        assert proto.setting_from_seed(seed) == proto.setting_from_seed(seed)


def test_canonical_setting_matches_selected_python_authority() -> None:
    proto = _load_proto()
    for band in ("easy", "medium", "hard"):
        for sample_index in range(4):
            grid = GEN.generate(20261022, sample_index, difficulty=band)
            assert proto.apply_python(grid, proto.CANONICAL_SETTING) == GEN.rule_mirror(grid)


def test_each_parameter_has_a_causal_witness_with_other_parameter_fixed() -> None:
    proto = _load_proto()
    leading = GEN.generate(
        901,
        1,
        difficulty="medium",
        scene_profile="leading_control",
        palette_profile="pair_12",
    )

    canonical = proto.apply_python(leading, proto.RuleSetting("main", "through_last"))
    anti = proto.apply_python(leading, proto.RuleSetting("anti", "through_last"))
    between = proto.apply_python(leading, proto.RuleSetting("main", "strict_between"))

    assert anti != canonical
    assert between != canonical
    assert proto.changed_cells(canonical, anti) > 0
    assert proto.changed_cells(canonical, between) > 0

    # The separator-policy contrast must be caused by leading blank rows, not
    # by a simultaneous copy-layout change.
    assert leading[0] == [0] * len(leading[0])
    assert set(canonical[0]) == {3}
    assert set(between[0]) == {0}


def test_all_program_settings_match_python_mirror_in_racket(
    protected_racket_bridge,
) -> None:
    proto = _load_proto()
    inputs = [
        GEN.generate(77, 0, difficulty="easy", scene_profile="internal_anchor"),
        GEN.generate(77, 1, difficulty="medium", scene_profile="leading_control"),
        GEN.generate(77, 2, difficulty="hard", scene_profile="trailing_control"),
    ]
    for setting in proto.ALL_SETTINGS:
        program = proto.program_for(setting)
        for grid in inputs:
            assert _eval_program(
                protected_racket_bridge, program, grid
            ) == proto.apply_python(grid, setting)


def test_materialized_public_challenges_hide_rule_and_query_answer(tmp_path: Path) -> None:
    proto = _load_proto()
    report = proto.materialize(tmp_path)
    assert report["schema"] == "arc-parametric-prototype-evidence-v1"
    assert report["task_id"] == GEN.TASK_ID
    assert report["passed"] is True
    assert len(report["episodes"]) == len(proto.ALL_SETTINGS)

    observed_settings = set()
    for episode in report["episodes"]:
        observed_settings.add(
            proto.RuleSetting(
                episode["setting"]["copy_diagonal"],
                episode["setting"]["separator_policy"],
            )
        )
        episode_dir = tmp_path / episode["directory"]
        challenge = json.loads((episode_dir / "challenge.json").read_text())
        answer = json.loads((episode_dir / "answer.json").read_text())

        assert set(challenge) == {"train", "test"}
        assert len(challenge["train"]) == 4
        assert len(challenge["test"]) == 1
        assert all(set(pair) == {"input", "output"} for pair in challenge["train"])
        assert all(set(pair) == {"input"} for pair in challenge["test"])
        rendered = json.dumps(challenge)
        assert "copy_diagonal" not in rendered
        assert "separator_policy" not in rendered
        assert "program" not in rendered
        assert answer["query_output"] == episode["query_output"]
        assert answer["program_sha256"] == episode["program_sha256"]

    assert observed_settings == set(proto.ALL_SETTINGS)
    witness = report["parameter_witnesses"]
    assert witness["copy_diagonal"]["changed_cells"] > 0
    assert witness["separator_policy"]["changed_cells"] > 0


def test_standalone_cli_bootstraps_required_rule_wrap_tools(tmp_path: Path) -> None:
    env = dict(os.environ)
    completed = subprocess.run(
        [sys.executable, str(PROTO_PATH), "--out", str(tmp_path / "cli")],
        cwd=str(TASK_ROOT),
        env=env,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    report = json.loads((tmp_path / "cli/report.json").read_text())
    assert report["passed"] is True
