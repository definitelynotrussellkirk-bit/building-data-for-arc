"""Focused tests for the native row-corridor parametric family."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest


TASK_ID = "628b4a2c24c1"
CANONICAL_SHA256 = "5ac6fbbb3b3dddc964628cb88665dcaae3bfa10c6dc7973fe7a7eb0afdb36c27"
RIGHTWARD = {"sweep_policy": "rightward"}
WIDEST = {"sweep_policy": "widest_corridor"}


def _prototype():
    for ancestor in Path(__file__).resolve().parents:
        helper = ancestor / "shared/runtime/reviewer_support.py"
        if helper.is_file():
            if str(helper.parent) not in sys.path:
                sys.path.insert(0, str(helper.parent))
            from reviewer_support import find_root

            root = find_root(__file__)
            source = root / "generators" / TASK_ID / "workspace/parametric/prototype.py"
            assert source.is_file(), "parametric prototype is missing"
            spec = importlib.util.spec_from_file_location("row_corridor_parametric", source)
            assert spec and spec.loader
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)
            return module
    raise AssertionError("no local reviewer runtime found")


@pytest.fixture(scope="module")
def p():
    return _prototype()


def test_default_program_is_exact_canonical_source(p):
    source = p.program(RIGHTWARD)
    assert hashlib.sha256(source.encode()).hexdigest() == CANONICAL_SHA256
    assert source == p.CANONICAL_PROGRAM
    assert p.DEFAULT == RIGHTWARD
    assert p.program(WIDEST) != source


@pytest.mark.parametrize("settings", [
    None,
    {},
    {"sweep_policy": "leftward"},
    {"sweep_policy": 1},
    {"sweep_policy": True},
    {"sweep_policy": "rightward", "extra": 1},
    "rightward",
])
def test_malformed_settings_fail_loudly(p, settings):
    with pytest.raises(ValueError):
        p.program(settings)


@pytest.mark.parametrize("settings", [RIGHTWARD, WIDEST])
@pytest.mark.parametrize("demos,queries", [(2, 1), (2, 4), (6, 1), (6, 4)])
def test_demo_query_count_boundaries_are_independent(p, settings, demos, queries):
    episode = p.generate(17, settings, demos=demos, queries=queries)
    assert len(episode["train"]) == demos
    assert len(episode["test"]) == queries
    assert episode["program_solution"] == p.program(settings)
    assert episode["settings"] == settings
    serialized = [json.dumps(pair["input"], separators=(",", ":"))
                  for pair in episode["train"] + episode["test"]]
    assert len(serialized) == len(set(serialized))


def test_same_seed_matches_inputs_across_settings_and_prefixes(p):
    right = p.generate(17, RIGHTWARD, demos=6, queries=4)
    widest = p.generate(17, WIDEST, demos=6, queries=4)
    for split in ("train", "test"):
        assert [pair["input"] for pair in right[split]] == [pair["input"] for pair in widest[split]]

    short_demos = p.generate(17, RIGHTWARD, demos=2, queries=4)
    short_queries = p.generate(17, RIGHTWARD, demos=6, queries=1)
    assert short_demos["train"] == right["train"][:2]
    assert short_demos["test"] == right["test"]
    assert short_queries["train"] == right["train"]
    assert short_queries["test"] == right["test"][:1]


def test_dependency_intermediate_controls_downstream_direction(p):
    grid = [[0] * 12 for _ in range(5)]
    # left corridor 6, right corridor 1 -> widest chooses left
    grid[1][1], grid[1][8], grid[1][10] = 8, 4, 8
    # left corridor 1, right corridor 6 -> widest chooses right
    grid[2][1], grid[2][3], grid[2][10] = 8, 4, 8
    # equal corridors -> documented right tie-break
    grid[3][1], grid[3][6], grid[3][11] = 8, 4, 8

    before = deepcopy(grid)
    intermediate = p.dependency_intermediate(grid)
    assert [row["direction"] for row in intermediate["seed_rows"]] == ["left", "right", "right"]
    assert [(row["left_gap"], row["right_gap"]) for row in intermediate["seed_rows"]] == [(6, 1), (1, 6), (4, 4)]

    widest = p.solve(grid, WIDEST)
    right = p.solve(grid, RIGHTWARD)
    assert widest[1][2:9] == [4] * 7
    assert widest[1][9] == 0
    assert widest[2][3:10] == [4] * 7
    assert widest[3][6:11] == [4] * 5
    assert right[1][8:10] == [4, 4]
    assert right != widest
    assert grid == before


@pytest.mark.parametrize("settings", [RIGHTWARD, WIDEST])
def test_two_demos_identify_policy_and_refute_named_shortcuts(p, settings):
    episode = p.generate(0, settings, demos=2, queries=4)
    certificate = p.teaching_check(episode)
    assert certificate["status"] == "identified"
    assert certificate["surviving_rivals"] == []
    assert "wall_required_right" in certificate["refuted_by"]
    assert "other_setting" in certificate["refuted_by"]
    assert set(certificate["refuted_by"]) == set(p.rival_programs(settings))

    # The known historical shortcut is refuted by a visible wall-free seed row.
    index = certificate["refuted_by"]["wall_required_right"]
    pair = episode["train"][index]
    assert p.rival_outputs(pair["input"], settings)["wall_required_right"] != pair["output"]
    assert any(row["right_stop"] == len(pair["input"][0])
               for row in p.dependency_intermediate(pair["input"])["seed_rows"])


def test_teaching_check_uses_demonstrations_only(p):
    episode = p.generate(0, WIDEST, demos=2, queries=4)
    expected = p.teaching_check(episode)
    assert p.teaching_check({**episode, "test": []}) == expected
    assert p.teaching_check({**episode, "test": [{"input": None, "output": object()}]}) == expected


def test_queries_cover_boundaries_and_substantive_30_by_30_content(p):
    episode = p.generate(0, WIDEST, demos=6, queries=4)
    shapes = [(len(pair["input"]), len(pair["input"][0])) for pair in episode["test"]]
    assert shapes == [(9, 14), (16, 22), (24, 30), (30, 30)]
    large = episode["test"][-1]["input"]
    nonzero = [(r, c) for r, row in enumerate(large) for c, value in enumerate(row) if value]
    assert min(r for r, _ in nonzero) <= 2
    assert max(r for r, _ in nonzero) >= 27
    assert min(c for _, c in nonzero) <= 2
    assert max(c for _, c in nonzero) >= 27
    metrics = p.analyze(large)
    assert metrics["active_rows"] >= 8
    assert {"left", "right"} <= set(metrics["widest_directions"])
    assert metrics["wall_free_right_rows"] >= 1


def test_public_projection_reveals_one_query_without_private_hints(p):
    episode = p.generate(9, WIDEST, demos=3, queries=4)
    first = p.public_challenge(episode, 0)
    only = p.public_challenge(p.generate(9, WIDEST, demos=3, queries=1), 0)
    assert first == only
    assert set(first) == {"train", "test"}
    assert len(first["train"]) == 3 and len(first["test"]) == 1
    assert set(first["test"][0]) == {"input"}
    text = json.dumps(first, sort_keys=True)
    for forbidden in ("sweep_policy", "program", "seed", "query_index", "query_count", "widest_corridor"):
        assert forbidden not in text
    first["train"][0]["input"][0][0] = 9
    assert episode["train"][0]["input"][0][0] != 9


def test_export_batch_hashes_only_visible_bytes_and_rejects_duplicate_payloads(p, tmp_path):
    output = tmp_path / "export"
    report = p.export_batch(output, count=2, seed=20, settings=WIDEST, demos=3, queries=4)
    assert report["count"] == 2
    public_files = sorted((output / "public").glob("*.json"))
    private_files = sorted((output / "private").glob("*.json"))
    assert len(public_files) == len(private_files) == 2
    for public in public_files:
        raw = public.read_bytes()
        assert public.stem == hashlib.sha256(raw).hexdigest()
        visible = json.loads(raw)
        assert all(set(pair) == {"input"} for pair in visible["test"])
        private = json.loads((output / "private" / public.name).read_text())
        assert private["public_id"] == public.stem
        assert private["episode"]["settings"] == WIDEST
        assert private["episode"]["program_solution"] == p.program(WIDEST)

    with pytest.raises(FileExistsError):
        p.export_batch(output, count=1, seed=0, settings=WIDEST, demos=3, queries=4)
    with pytest.raises(ValueError, match="duplicate visible"):
        p.export_batch(tmp_path / "duplicates", count=2, seed=20, settings=WIDEST,
                       demos=3, queries=4, seed_step=0)


@pytest.mark.parametrize("name,value", [
    ("seed", -1), ("seed", 2**63), ("seed", True), ("seed", 0.0),
    ("demos", 1), ("demos", 7), ("demos", True), ("demos", 2.0),
    ("queries", 0), ("queries", 5), ("queries", False), ("queries", 1.0),
])
def test_invalid_controls_are_rejected(p, name, value):
    kwargs = {"seed": 0, "settings": RIGHTWARD, "demos": 3, "queries": 4}
    kwargs[name] = value
    with pytest.raises(ValueError):
        p.generate(**kwargs)
