"""Behavioral regressions for the proposed block-voting episode family."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
REPO = HOME.parents[1]


def load(path, name):
    assert path.is_file(), f"Missing requested implementation: {path.name}"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def family():
    return load(HOME / "workspace/parametric/prototype.py", "block_vote_prototype")


@pytest.fixture(scope="module")
def labeler(family):
    with family.RacketLabeler() as oracle:
        yield oracle


def test_lawful_diagnostics_are_declared_and_remain_lawful():
    generator = load(HOME / "generator.py", "block_vote_canonical")
    declared = set(getattr(generator, "LAWFUL_DEGENERATE_TEXTURES", ()))
    assert set(generator.DEGENERATE_TEXTURES) <= declared
    for texture in generator.DEGENERATE_TEXTURES:
        grid = generator.generate(17, 0, texture=texture)
        assert generator.self_check(grid) == []


@pytest.mark.parametrize("unit,tie,want", [
    ("objects", False, [True, False, False, True]),
    ("objects", True, [True, False, True, True]),
    ("cells", False, [False, True, False, False]),
    ("cells", True, [False, True, False, True]),
])
def test_four_witnesses_have_hand_checked_decisions(family, labeler, unit, tie, want):
    settings = {"vote_unit": unit, "keep_on_tie": tie}
    profiles = [(1, 1, 7, 4, 6), (5, 5, 2, 2, 2, 6),
                (1, 3, 2, 4), (1, 1, 1, 1, 2)]
    for index, sides in enumerate(profiles):
        grid = family.sample_scene(10 + index, sides, height=20, width=20)
        original = deepcopy(grid)
        output = labeler(family.materialize_program(settings), grid)
        scene = family.analyze(grid)
        marker = scene["marker_color"]
        assert all(output[r][c] == (marker if want[index] else 7)
                   for r, c in scene["plus"])
        assert output == family.python_output(grid, settings)
        assert grid == original
        for square in scene["squares"]:
            r, c, side = square
            if side % 2:
                assert output[r + side // 2][c + side // 2] == marker


def test_default_matches_all_four_canonical_labels(family, labeler):
    path = REPO / "shared/data/canonical/puzzles.jsonl"
    row = next(json.loads(line) for line in path.read_text().splitlines()
               if json.loads(line).get("task_id") == "a2d9d069c7d5")
    pairs = row["train"] + row["test"]
    assert len(pairs) == 4
    for pair in pairs:
        assert labeler(family.materialize_program(family.DEFAULT), pair["input"]) == pair["output"]


@pytest.mark.parametrize("seed", [17, 29])
def test_episodes_identify_all_settings_without_query_answers(family, labeler, seed):
    scenes = None
    for setting in family.SETTINGS:
        episode = family.build_episode(seed, setting, demos=4, queries=4, labeler=labeler)
        assert len(episode["train"]) == 4 and len(episode["test"]) == 4
        inputs = [p["input"] for p in episode["train"] + episode["test"]]
        assert len({json.dumps(g) for g in inputs}) == 8
        if scenes is None:
            scenes = inputs
        assert inputs == scenes, "Hidden rule parameters must not control the input scenes"
        certificate = family.certify(episode["train"], episode["test"])
        assert certificate["surviving_settings"] == [setting]
        assert all(q["identifiable"] for q in certificate["queries"])
        hidden_changed = deepcopy(episode["test"])
        for pair in hidden_changed:
            pair["output"] = [[0]]
        assert family.certify(episode["train"], hidden_changed) == certificate


def test_underspecified_demos_do_not_receive_identifiable_certificate(family, labeler):
    episode = family.build_episode(17, family.DEFAULT, labeler=labeler)
    # A single object/cell disagreement cannot distinguish strict from inclusive ties.
    certificate = family.certify(episode["train"][:1], episode["test"])
    assert len(certificate["surviving_settings"]) > 1
    assert any(not q["identifiable"] for q in certificate["queries"])


@pytest.mark.parametrize("settings", [
    {"vote_unit": "pixels", "keep_on_tie": False},
    {"vote_unit": "objects", "keep_on_tie": 1},
    {"vote_unit": "objects", "keep_on_tie": "false"},
    {"vote_unit": "objects"},
    {"vote_unit": "objects", "keep_on_tie": False, "secret": 1},
])
def test_invalid_settings_fail_closed(family, settings):
    with pytest.raises(ValueError):
        family.materialize_program(settings)


@pytest.mark.parametrize("kwargs", [
    {"demos": 3}, {"demos": True}, {"demos": 21},
    {"queries": 0}, {"queries": True}, {"queries": 33},
    {"height": 15}, {"width": 31}, {"height": 20.0},
])
def test_invalid_episode_controls_reject_before_sampling(family, kwargs):
    with pytest.raises(ValueError):
        family.build_episode(17, family.DEFAULT, **kwargs)


def test_public_ids_ignore_private_fields_and_batch_order(family, labeler, tmp_path):
    from reviewer_support import public_challenge_bytes, public_challenge_id
    first = family.build_episode(17, family.DEFAULT, labeler=labeler)
    second = family.build_episode(19, family.SETTINGS[-1], labeler=labeler)
    changed = deepcopy(first)
    changed["parameters"] = {"arbitrary": "private"}
    changed["seed"] = "changed"
    changed["program"] = "private"
    changed["test"][0]["output"] = [[9]]
    assert public_challenge_bytes(first) == public_challenge_bytes(changed)
    assert public_challenge_id(first) == public_challenge_id(changed)
    report = family.write_batch([second, first], tmp_path / "one")
    other = family.write_batch([first, second], tmp_path / "two")
    assert report["public_ids"] == sorted(report["public_ids"])
    assert report["public_ids"] == other["public_ids"]
    for public_id in report["public_ids"]:
        path = tmp_path / "one/public" / (public_id + ".json")
        assert path.read_bytes() == (tmp_path / "two/public" / path.name).read_bytes()
        public = json.loads(path.read_bytes())
        assert set(public) == {"train", "test"}
        assert all(set(pair) == {"input"} for pair in public["test"])
    with pytest.raises(ValueError, match="duplicate"):
        family.write_batch([first, first], tmp_path / "duplicates")
    assert not (tmp_path / "duplicates").exists()


def test_exact_numeric_public_grid_types(family, labeler, tmp_path):
    episode = family.build_episode(17, family.DEFAULT, labeler=labeler)
    episode["train"][0]["input"][0][0] = True
    with pytest.raises(ValueError):
        family.write_batch([episode], tmp_path / "bad")
    assert not (tmp_path / "bad").exists()


def test_all_queries_reach_large_grid_with_independent_counts(family, labeler):
    episode = family.build_episode(31, family.SETTINGS[-1], demos=5, queries=7,
                                   height=30, width=23, labeler=labeler)
    assert len(episode["train"]) == 5 and len(episode["test"]) == 7
    assert all(len(p["input"]) == 30 and len(p["input"][0]) == 23
               for p in episode["train"] + episode["test"])
    assert len({json.dumps(p["input"]) for p in episode["train"] + episode["test"]}) == 12


def test_tampered_label_rejected_by_racket_replay(family, labeler):
    episode = family.build_episode(17, family.DEFAULT, labeler=labeler)
    episode["test"][0]["output"][0][0] = 9
    with pytest.raises(ValueError, match="label"):
        family.verify_episode(episode, labeler=labeler)


def test_non_integer_query_label_rejected_even_when_numerically_equal(family, labeler, tmp_path):
    episode = family.build_episode(17, family.DEFAULT, labeler=labeler)
    episode["test"][0]["output"][0][0] = float(episode["test"][0]["output"][0][0])
    with pytest.raises(ValueError, match="label"):
        family.verify_episode(episode, labeler=labeler)
    with pytest.raises(ValueError, match="label"):
        family.write_batch([episode], tmp_path / "bad-private-label")
    assert not (tmp_path / "bad-private-label").exists()


def test_non_integer_demo_label_cannot_pass_certificate(family, labeler):
    episode = family.build_episode(17, family.DEFAULT, labeler=labeler)
    output = episode["train"][0]["output"]
    r, c = next((r, c) for r, row in enumerate(output) for c, value in enumerate(row)
                if value in (0, 1))
    output[r][c] = bool(output[r][c])
    with pytest.raises(ValueError, match="label"):
        family.certify(episode["train"], episode["test"])
    with pytest.raises(ValueError, match="label"):
        family.verify_episode(episode, labeler=labeler)
