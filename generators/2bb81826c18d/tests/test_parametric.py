"""Prototype-only contracts; these tests do not approve the rule variants."""
from __future__ import annotations

import copy
import importlib.util
import json
import random
import sys
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator
from arc_repl.racket_bridge import RacketBridge


TASK_ID = "2bb81826c18d"
ROOT = find_root(__file__)
GENERATOR, GENERATOR_PATH, _ = load_selected_generator(TASK_ID, root=ROOT)


def test_prototype_is_present_in_selected_tree():
    assert any(path.is_file() for path in (
        GENERATOR_PATH.parent / "workspace/parametric/prototype.py",
        ROOT / f"generators/{TASK_ID}/workspace/parametric/prototype.py",
    )), "The separate runnable parametric prototype must be transported"


@pytest.fixture(scope="module")
def prototype():
    candidates = (
        GENERATOR_PATH.parent / "workspace/parametric/prototype.py",
        ROOT / f"generators/{TASK_ID}/workspace/parametric/prototype.py",
    )
    path = next((candidate for candidate in candidates if candidate.is_file()), candidates[0])
    assert path.is_file(), "The separate parametric prototype must exist"
    spec = importlib.util.spec_from_file_location("rectangle_parametric_prototype", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def bridge():
    with RacketBridge(timeout=15) as value:
        yield value


def rectangle_grid():
    grid = [[0] * 17 for _ in range(16)]
    for top, left, height, width, color in ((0, 0, 5, 6, 9), (7, 8, 6, 5, 1)):
        for row in range(top, top + height):
            for col in range(left, left + width):
                grid[row][col] = color
    return grid


def test_exact_parameter_domain_and_strict_scalars(prototype):
    assert prototype.SETTINGS == ((2, 0), (2, 1), (3, 0), (3, 1), (3, 2))
    assert prototype.CANONICAL == (2, 0)
    for setting in prototype.SETTINGS:
        assert prototype.validate_setting(*setting) == setting
    for setting in ((True, 0), (2, False), (2.0, 0), (2, "0"), (1, 0), (4, 0), (2, 2), (3, -1)):
        with pytest.raises(ValueError):
            prototype.validate_setting(*setting)


def test_five_executed_rules_differ_and_preserve_borders(prototype, bridge):
    grid = rectangle_grid()
    before = copy.deepcopy(grid)
    outputs = [prototype.execute_racket(prototype.racket_program(*s), [grid], bridge=bridge)[0]
               for s in prototype.SETTINGS]
    assert len({json.dumps(output) for output in outputs}) == 5
    assert grid == before
    assert outputs[2][1][1:5] == [0, 9, 9, 0]
    assert outputs[3][1][1:5] == [9, 0, 9, 9]
    assert outputs[4][1][1:5] == [9, 9, 0, 9]
    for output in outputs:
        assert len(output) == len(grid) and len(output[0]) == len(grid[0])
        for top, left, height, width, color in ((0, 0, 5, 6, 9), (7, 8, 6, 5, 1)):
            assert all(output[top][col] == output[top + height - 1][col] == color
                       for col in range(left, left + width))
            assert all(output[row][left] == output[row][left + width - 1] == color
                       for row in range(top, top + height))
        assert all(output[row][col] == 0 for row in range(16) for col in range(17)
                   if grid[row][col] == 0)


def test_canonical_setting_matches_all_available_canonical_pairs(prototype, bridge):
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert pairs
    inputs = [pair["input"] for pair in pairs]
    canonical = prototype.execute_racket(prototype.canonical_program(ROOT), inputs, bridge=bridge)
    proposed = prototype.execute_racket(prototype.racket_program(*prototype.CANONICAL), inputs, bridge=bridge)
    assert canonical == proposed == [pair["output"] for pair in pairs]


def test_each_episode_has_one_fixed_rule_and_refutes_every_parameter_rival(prototype, bridge):
    for setting in prototype.SETTINGS:
        episode = prototype.generate_episode(19, setting=setting, bridge=bridge)
        assert episode["parameters"] == {"period": setting[0], "phase": setting[1]}
        assert len(episode["train"]) == 3 and len(episode["test"]) == 1
        assert len({json.dumps(p["input"]) for p in episode["train"] + episode["test"]}) == 4
        for pair in episode["train"] + episode["test"]:
            assert GENERATOR.self_check(pair["input"]) == []
        outputs = prototype.execute_racket(episode["program"],
                                           [p["input"] for p in episode["train"] + episode["test"]],
                                           bridge=bridge)
        assert outputs == [p["output"] for p in episode["train"] + episode["test"]]
        rivals = prototype.check_parameter_rivals(episode, bridge=bridge)
        assert len(rivals) == 4
        assert all(row["status"] == "refuted_by_demonstration" for row in rivals)
        assert all(row["first_refuting_demo"] == 0 for row in rivals)


def test_episode_sampling_is_reproducible_and_public_view_has_no_hidden_fields(prototype, bridge):
    global_state = random.getstate()
    first = prototype.generate_episode(27, bridge=bridge)
    assert first == prototype.generate_episode(27, bridge=bridge)
    assert random.getstate() == global_state
    assert first["parameters"] == dict(zip(("period", "phase"), prototype.choose_setting(27)))
    assert {prototype.choose_setting(seed) for seed in range(100)} == set(prototype.SETTINGS)
    public = prototype.public_challenge(first)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    public["train"][0]["input"][0][0] = 99
    assert first["train"][0]["input"][0][0] != 99


def test_small_ambiguous_demos_are_reported_without_claiming_identifiability(prototype, bridge):
    grid = [[0] * 10 for _ in range(10)]
    for row in range(1, 4):
        for col in range(1, 4):
            grid[row][col] = 2
    program = prototype.racket_program(2, 0)
    output = prototype.execute_racket(program, [grid], bridge=bridge)[0]
    episode = {"parameters": {"period": 2, "phase": 0}, "program": program,
               "train": [{"input": grid, "output": output}],
               "test": [{"input": rectangle_grid(),
                         "output": prototype.execute_racket(program, [rectangle_grid()], bridge=bridge)[0]}]}
    rivals = prototype.check_parameter_rivals(episode, bridge=bridge)
    assert next(row for row in rivals if row["parameters"] == {"period": 3, "phase": 0})["status"] == "ambiguous_query"


def test_public_view_uses_only_visible_fields_even_with_extra_private_pair_metadata(prototype):
    grid = rectangle_grid()
    episode = {"train": [{"input": grid, "output": grid,
                          "parameters": {"period": 3, "phase": 2}, "program": "private"}],
               "test": [{"input": grid, "output": grid, "seed": 17}]}
    public = prototype.public_challenge(episode)
    assert set(public["train"][0]) == {"input", "output"}
    assert set(public["test"][0]) == {"input"}


def test_evidence_manifest_never_hashes_itself_or_unrelated_files(prototype, tmp_path, monkeypatch):
    monkeypatch.setitem(sys.modules, "prototype", prototype)
    spec = importlib.util.spec_from_file_location("rectangle_parametric_probe", Path(prototype.__file__).with_name("probe.py"))
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)
    expected = {"canonical-equality.private.json", "challenges.public.jsonl", "episodes.private.jsonl",
                "programs.private.json", "witness.private.json"}
    for name in expected | {"report.json", "unrelated.json"}:
        (tmp_path / name).write_text("{}\n")
    manifest = probe.artifact_manifest(tmp_path)
    assert {entry["path"] for entry in manifest} == expected
    (tmp_path / "report.json").write_text("updated receipt\n")
    assert probe.artifact_manifest(tmp_path) == manifest


def test_invalid_episode_controls_and_nonrectangular_input_fail_visibly(prototype, bridge):
    for options in ({"n_train": 0}, {"n_test": 0}, {"n_train": True}, {"n_test": 9}, {"setting": (3, 3)}):
        with pytest.raises(ValueError):
            prototype.generate_episode(0, bridge=bridge, **options)
    for seed in (True, "7", 2.1):
        with pytest.raises(ValueError):
            prototype.choose_setting(seed)
    malformed = rectangle_grid()
    malformed[2][2] = 0
    with pytest.raises(ValueError, match="solid"):
        prototype.execute_racket(prototype.racket_program(2, 0), [malformed], bridge=bridge)
