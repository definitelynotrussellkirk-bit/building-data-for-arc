"""Prototype-only tests for the proposed recolor-origin rule parameter."""
from __future__ import annotations

from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
sys.path.insert(0, str(HOME / "workspace" / "parametric"))

from reference_probe import canonical, load_generator, racket_outputs, reference_output  # noqa: E402

GEN = load_generator()


def test_materialized_rule_texts_preserve_canonical_default():
    from prototype import load_programs

    programs = load_programs()
    canonical_program = canonical()["program_solution"]
    assert programs["opposite"] == canonical_program
    assert programs["aligned"] == canonical_program.replace(
        "(curr other-ep)", "(curr ep)", 1
    )
    assert programs["opposite"] != programs["aligned"]


def test_both_parameter_settings_execute_in_real_racket():
    from arc_repl.racket_bridge import racket_runtime_status
    from prototype import load_programs

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grid = GEN.generate(8111, 7, difficulty="hard")
    programs = load_programs()
    outputs = racket_outputs([grid], [programs["opposite"], programs["aligned"]])
    assert outputs[0][0] == reference_output(grid, recolor_origin="opposite")
    assert outputs[1][0] == reference_output(grid, recolor_origin="aligned")
    assert outputs[0][0] != outputs[1][0]


@pytest.mark.parametrize("parameter", ["opposite", "aligned"])
def test_complete_episode_uses_one_parameter_and_demos_distinguish_it(parameter):
    from prototype import build_episode

    episode = build_episode(seed=9101 if parameter == "opposite" else 9102, parameter=parameter)
    assert episode["parameter"] == parameter
    assert len(episode["train"]) == 3
    assert len(episode["test"]) == 4
    assert all(pair["selected_output"] == pair["outputs_by_parameter"][parameter] for pair in episode["pairs"])
    other = "aligned" if parameter == "opposite" else "opposite"
    assert any(
        pair["outputs_by_parameter"][parameter]
        != pair["outputs_by_parameter"][other]
        for pair in episode["pairs"][:3]
    )
    assert episode["rival_fits_all_demos"] is False
    public = episode["public_challenge"]
    assert all("output" in pair for pair in public["train"])
    assert all("output" not in pair for pair in public["test"])
    assert "parameter" not in public
