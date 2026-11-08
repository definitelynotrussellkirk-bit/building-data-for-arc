"""Focused regressions and prototype checks added by review-cfeefa5f2b4d2d06."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import pytest

from reviewer_support import find_root, load_selected_generator

TASK_ID = "1c1ef857c9e2"
ROOT = find_root(__file__)
gen, GEN_SOURCE, GEN_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
TASK_HOME = Path(__file__).resolve().parent.parent


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module



@pytest.mark.parametrize("entrypoint", [gen.generate, gen.schedule_profile])
def test_sample_index_requires_a_nonnegative_literal_integer(entrypoint):
    with pytest.raises(ValueError, match="sample_index"):
        entrypoint(7, -1, difficulty="easy")

PARAMETRIC = TASK_HOME / "workspace" / "parametric"
PROTOTYPE = PARAMETRIC / "prototype.py"


def _prototype():
    assert PROTOTYPE.is_file(), "parametric prototype must be retained"
    return _load(PROTOTYPE, "parametric_1c1ef857c9e2")


def test_parametric_space_preserves_the_canonical_default():
    proto = _prototype()
    assert proto.MEASURE_MODES == ("sections", "separators")
    assert proto.AXIS_ORDERS == ("row_col", "col_row")
    assert proto.DEFAULT_PARAMETERS == {
        "measure_mode": "sections",
        "axis_order": "row_col",
    }
    assert proto.parameter_for_seed(0) == proto.DEFAULT_PARAMETERS
    assert len({tuple(sorted(proto.parameter_for_seed(seed).items())) for seed in range(4)}) == 4


def test_parameters_are_fixed_per_episode_and_every_demo_refutes_all_other_settings():
    proto = _prototype()
    all_settings = list(proto.all_parameter_settings())
    assert len(all_settings) == 4

    for seed in range(4):
        episode = proto.build_episode(seed)
        chosen = episode["parameter"]
        assert chosen == proto.parameter_for_seed(seed)
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 1

        for pair in episode["train"] + episode["test"]:
            assert pair["output"] == proto.python_mirror(pair["input"], **chosen)
            for rival in all_settings:
                if rival == chosen:
                    continue
                assert proto.python_mirror(pair["input"], **rival) != pair["output"]


def test_public_challenge_hides_rule_parameters_and_query_answers():
    proto = _prototype()
    public = proto.public_challenge(proto.build_episode(3))
    assert "parameter" not in public
    assert len(public["train"]) == 3 and len(public["test"]) == 1
    assert all("output" in pair for pair in public["train"])
    assert all("output" not in pair for pair in public["test"])


def test_materialized_racket_sources_match_exact_program_text(tmp_path):
    proto = _prototype()
    paths = proto.materialize_rules(tmp_path)
    assert len(paths) == 4
    for setting in proto.all_parameter_settings():
        path = paths[proto.setting_slug(setting)]
        assert path.read_text(encoding="utf-8") == proto.rule_source(**setting)
        assert path.suffix == ".rkt"


def test_canonical_default_matches_all_four_canonical_pairs():
    proto = _prototype()
    rows = proto.canonical_parity_python()
    assert len(rows) == 4
    assert all(row["matches_canonical_output"] for row in rows)
    assert {tuple(row["input_shape"]) for row in rows} == {
        (11, 11),
        (15, 15),
        (22, 22),
        (27, 27),
    }
