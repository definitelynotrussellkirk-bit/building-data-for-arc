from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root


ROOT = find_root(__file__)
TASK_ROOT = Path(__file__).resolve().parents[1]
PROTOTYPE_PATH = TASK_ROOT / "workspace" / "parametric" / "prototype.py"
CANONICAL_PATH = canonical_path(ROOT)


def _load_prototype():
    assert PROTOTYPE_PATH.is_file(), "parametric prototype has not been implemented"
    spec = importlib.util.spec_from_file_location("parametric_four_region_color", PROTOTYPE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program():
    with CANONICAL_PATH.open() as handle:
        rows = [json.loads(line) for line in handle if line.strip()]
    return next(row["program_solution"] for row in rows if row["task_id"] == "9d52c9d09009")


def test_default_parameter_is_byte_exact_canonical_and_alternative_is_narrow():
    module = _load_prototype()
    canonical = _canonical_program()
    assert module.render_program(canonical, 7) == canonical
    alternative = module.render_program(canonical, 4)
    assert alternative != canonical
    assert alternative.count("(define (map-color n) (if (= n 4) 4 n))") == 1
    assert canonical.count("(define (map-color n) (if (= n 4) 7 n))") == 1


@pytest.mark.parametrize("value", [True, False, 3, 5, 7.0, "7"])
def test_parameter_validation_rejects_values_outside_declared_domain(value):
    module = _load_prototype()
    with pytest.raises((TypeError, ValueError)):
        module.render_program(_canonical_program(), value)


def test_fixture_episode_uses_lawful_generated_inputs_that_distinguish_settings():
    module = _load_prototype()
    grids = module.fixture_inputs(73)
    assert len(grids) == 4
    assert len({json.dumps(grid, separators=(",", ":")) for grid in grids}) == 4
    generator = module.generator_module()
    for grid in grids:
        assert generator.self_check(grid) == []
        assert generator._has_four_vs_eight_connectivity_witness(grid)
        facts = generator._analysis(grid)["facts"]
        assert 4 in facts["hole_signature"]


def test_public_challenge_masks_parameter_program_and_query_answer():
    module = _load_prototype()
    episode = {
        "parameters": {"four_region_color": 4},
        "program": "secret",
        "train": [{"input": [[0]], "output": [[0]]}],
        "test": [{"input": [[8]], "output": [[4]]}],
    }
    public = module.public_challenge(episode)
    assert public == {
        "train": [{"input": [[0]], "output": [[0]]}],
        "test": [{"input": [[8]]}],
    }
    assert "parameters" not in public and "program" not in public
