"""Task-local direction-scope prototype; not canonical sampler approval."""
from __future__ import annotations

import hashlib
import importlib.util
from functools import cache
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, find_root, load_selected_generator


ROOT = find_root(__file__)
PROTOTYPE = Path(__file__).resolve().parents[1] / "workspace/parametric/prototype.py"


@cache
def prototype():
    assert PROTOTYPE.is_file(), "Task-local parametric prototype is not implemented"
    spec = importlib.util.spec_from_file_location("direction_scope_prototype", PROTOTYPE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def bridge():
    with RacketBridge() as runtime:
        yield runtime


def _mixed_witness(height=6, width=8):
    grid = [[6] * width for _ in range(height)]
    grid[2][0] = grid[2][-1] = 4
    grid[0][3] = grid[-1][3] = 4
    grid[2][1:5] = [0, 8, 6, 7]
    grid[1][3] = 8
    grid[3][3] = 7
    return grid


def test_direction_scope_changes_executed_racket(bridge):
    """Collapsing rows/columns to union must fail these concrete witnesses."""
    module = prototype()
    grid = _mixed_witness()
    selected, _, _ = load_selected_generator(module.TASK_ID, root=ROOT)
    assert selected.self_check(grid) == []
    outputs = {
        scope: module.execute_program(module.materialize_program(scope), grid, bridge)
        for scope in module.SCOPES
    }
    assert len({tuple(map(tuple, output)) for output in outputs.values()}) == 3
    assert outputs["union"][2][1:5] == [8, 0, 7, 6]
    assert outputs["rows"][2][1:5] == [8, 0, 7, 6]
    assert outputs["columns"][2][1:5] == [0, 8, 7, 7]
    assert outputs["union"][1][3] == outputs["columns"][1][3] == 0
    assert outputs["rows"][1][3] == 8
    assert outputs["union"][3][3] == outputs["columns"][3][3] == 6
    assert outputs["rows"][3][3] == 7
    for scope, output in outputs.items():
        assert output[2][0] == output[2][-1] == output[0][3] == output[-1][3] == 4
        assert output[1][1] == grid[1][1]
        # An intersection is transformed once, including in union mode.
        assert output[2][3] == 7
        assert module.execute_program(module.materialize_program(scope), output, bridge) == grid


def test_default_matches_all_selected_canonical_pairs(bridge):
    module = prototype()
    pairs = canonical_pairs(module.TASK_ID, root=ROOT, labeled_only=True)
    assert len(pairs) == 4
    assert module.DEFAULT_SCOPE == "union"
    for pair in pairs:
        assert module.execute_program(module.materialize_program(), pair["input"], bridge) == pair["output"]


@pytest.mark.parametrize("scope", ("union", "rows", "columns"))
def test_complete_episode_has_one_rule_and_distinguishing_demonstrations(scope, bridge):
    module = prototype()
    episode = module.generate_episode(17, scope=scope, bridge=bridge)
    public, private = episode["public"], episode["private"]
    assert private["parameters"] == {"direction_scope": scope}
    assert private.get("parameter_selection") == "explicit_authoring_override"
    assert private["program"] == module.materialize_program(scope)
    assert private["program_sha256"] == hashlib.sha256(private["program"].encode()).hexdigest()
    assert len(public["train"]) == 3 and len(public["test"]) == 1
    for pair in public["train"]:
        assert module.execute_program(private["program"], pair["input"], bridge) == pair["output"]
    assert module.execute_program(private["program"], public["test"][0]["input"], bridge) == private["query_outputs"][0]
    assert private["identifiability"]["survivors"] == [scope]
    assert set(private["identifiability"]["rivals"]) == set(module.SCOPES)
    for rival, result in private["identifiability"]["rivals"].items():
        assert bool(result["mismatching_demonstrations"]) == (rival != scope)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    selected, source, digest = load_selected_generator(module.TASK_ID, root=ROOT)
    assert private["selected_generator"]["sha256"] == digest
    assert private["selected_generator"]["path"] == source.relative_to(ROOT).as_posix()
    for pair in public["train"] + public["test"]:
        assert selected.self_check(pair["input"]) == []


def test_seeded_rule_is_reproducible_and_input_schedule_is_parameter_independent(bridge):
    module = prototype()
    first = module.generate_episode(113, bridge=bridge)
    assert first == module.generate_episode(113, bridge=bridge)
    assert first["private"]["parameters"]["direction_scope"] == module.choose_scope(113)
    alternate = module.generate_episode(113, scope="rows", bridge=bridge)
    for split in ("train", "test"):
        assert [pair["input"] for pair in first["public"][split]] == [pair["input"] for pair in alternate["public"][split]]


@pytest.mark.parametrize("seed, expected", ((11, "union"), (2, "rows"), (17, "columns")))
@pytest.mark.parametrize("provide_bridge", (True, False))
def test_seed_selected_episode_records_origin_and_chooses_once(seed, expected, provide_bridge, bridge, monkeypatch):
    module = prototype()
    original_choose = module.choose_scope
    choices = []

    def counted_choose(value):
        choices.append(value)
        return original_choose(value)

    monkeypatch.setattr(module, "choose_scope", counted_choose)
    episode = module.generate_episode(seed, **({"bridge": bridge} if provide_bridge else {}))
    assert episode["private"].get("parameter_selection") == "deterministic_seed"
    assert episode["private"]["parameters"] == {"direction_scope": expected}
    assert episode["private"]["identifiability"]["survivors"] == [expected]
    assert choices == [seed]


def test_finite_rival_check_exposes_ambiguous_demonstrations(bridge):
    module = prototype()
    grid = [[6] * 8 for _ in range(6)]
    audit = module.audit_demonstrations([{"input": grid, "output": grid}], bridge)
    assert audit["survivors"] == list(module.SCOPES)
    assert all(not row["mismatching_demonstrations"] for row in audit["rivals"].values())


def test_materialized_rule_handles_arc_maximum_grid(bridge):
    module = prototype()
    grid = _mixed_witness(30, 30)
    output = module.execute_program(module.materialize_program(), grid, bridge)
    assert len(output) == 30 and all(len(row) == 30 for row in output)
    assert output[2][3] == 7 and output[1][3] == 0 and output[1][1] == 6


@pytest.mark.parametrize("scope", ("diagonal", "", None, 4))
def test_invalid_explicit_scope_is_rejected(scope):
    with pytest.raises(ValueError, match="direction_scope"):
        prototype().materialize_program(scope)


@pytest.mark.parametrize("seed", (-1, True, "17"))
def test_invalid_episode_seed_is_rejected(seed):
    with pytest.raises(ValueError, match="seed"):
        prototype().choose_scope(seed)
