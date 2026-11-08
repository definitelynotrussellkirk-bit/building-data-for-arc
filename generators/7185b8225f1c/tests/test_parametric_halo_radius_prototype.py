from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


TASK = "7185b8225f1c"
TASK_DIR = Path(__file__).resolve().parents[1]
PROTOTYPE_PATH = TASK_DIR / "workspace" / "parametric" / "prototype.py"


def load_prototype():
    spec = importlib.util.spec_from_file_location(
        f"parametric_{TASK}", PROTOTYPE_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load prototype at {PROTOTYPE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_program() -> str:
    try:
        from reviewer_support import canonical_path, find_root
    except ImportError as exc:  # pragma: no cover - staged runtime provides this
        raise RuntimeError("reviewer_support is required") from exc
    path = canonical_path(find_root(__file__))
    programs = {
        row["program_solution"]
        for line in path.read_text(encoding="utf-8").splitlines()
        for row in [json.loads(line)]
        if row.get("task_id") == TASK
    }
    assert len(programs) == 1
    return programs.pop().strip()


def test_default_rule_is_exact_canonical_program():
    module = load_prototype()
    assert module.DEFAULT_HALO_RADIUS == 1
    assert module.rule_source(1).strip() == canonical_program()
    assert module.rule_source(2) != module.rule_source(1)


@pytest.mark.parametrize("bad", [True, False, 1.0, "1", 0, 3, None])
def test_radius_validation_fails_closed(bad):
    module = load_prototype()
    with pytest.raises(ValueError):
        module.rule_source(bad)


def test_seed_selection_and_episode_rule_are_deterministic():
    module = load_prototype()
    selection = module.select_seeds(20261020)
    assert set(selection["by_halo_radius"]) == {"1", "2"}
    for radius_text, seed in selection["by_halo_radius"].items():
        first = module.sample_episode(seed)
        second = module.sample_episode(seed)
        assert first == second
        assert first["parameters"] == {"halo_radius": int(radius_text)}
        assert first["program"] == module.rule_source(int(radius_text))
        assert len(first["inputs"]) == module.PAIR_COUNT == 4


def test_every_pair_distinguishes_both_radius_settings():
    module = load_prototype()
    for seed in module.select_seeds(20261020)["seeds"]:
        for grid in module.sample_inputs(seed):
            assert module.validate_prototype_input(grid) == []
            assert module.python_mirror(grid, 1) != module.python_mirror(grid, 2)


def test_all_query_rotations_refute_the_alternate_radius():
    module = load_prototype()
    for seed in module.select_seeds(20261020)["seeds"]:
        episode = module.sample_episode(seed)
        chosen = episode["parameters"]["halo_radius"]
        predictions = {
            radius: [module.python_mirror(grid, radius) for grid in episode["inputs"]]
            for radius in module.ALLOWED_HALO_RADII
        }
        for query_index in range(module.PAIR_COUNT):
            result = module.score_rotation(predictions, chosen, query_index)
            assert result["query_index"] == query_index
            assert all(
                rival["status"] == "refuted_by_demonstrations"
                for rival in result["rivals"]
            )


def test_public_challenge_hides_rule_and_query_answer():
    module = load_prototype()
    seed = module.select_seeds(20261020)["seeds"][0]
    episode = module.sample_episode(seed)
    radius = episode["parameters"]["halo_radius"]
    pairs = [
        {"input": grid, "output": module.python_mirror(grid, radius)}
        for grid in episode["inputs"]
    ]
    public = module.public_challenge(pairs, query_index=1)
    assert len(public["train"]) == 3
    assert len(public["test"]) == 1
    assert set(public["test"][0]) == {"input"}
    serialized = json.dumps(public, sort_keys=True)
    assert "halo_radius" not in serialized
    assert "program" not in serialized
