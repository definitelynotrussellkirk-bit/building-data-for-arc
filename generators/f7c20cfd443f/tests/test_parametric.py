"""Focused contract tests for the separate halo-selection family."""
import copy
import importlib.util
import json
from pathlib import Path
import random
import pytest

HOME = Path(__file__).resolve().parents[1]


def load():
    path = HOME / "workspace/parametric/adapter.py"
    assert path.is_file(), "native parametric adapter is missing"
    spec = importlib.util.spec_from_file_location("f7_halo_adapter_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_native_default_preserves_exact_canonical_source():
    from arcpuzzles import Catalog
    a = load()
    root = HOME.parents[1]
    canonical = {v["program_solution"] for v in Catalog(root)._variants()["f7c20cfd443f"]}
    assert {a.program({"selection": "all"})} == canonical


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_counts_matched_inputs_identification_and_prefix(demos):
    a = load()
    before = random.getstate()
    episodes = [a.generate(17, {"selection": s}, demos, 4) for s in ("all", "largest", "smallest")]
    for chosen, episode in zip(("all", "largest", "smallest"), episodes):
        assert len(episode["train"]) == demos and len(episode["test"]) == 4
        pairs = episode["train"] + episode["test"]
        assert len({json.dumps(p["input"]) for p in pairs}) == demos + 4
        for pair in pairs:
            assert all(type(v) is int for row in pair["input"] for v in row)
            a.validate_grid(pair["input"])
        survivors = [s for s in ("all", "largest", "smallest") if all(a.transform(p["input"], s) == p["output"] for p in episode["train"])]
        assert survivors == [chosen]
        single = a.generate(17, {"selection": chosen}, demos, 1)
        assert a.public_turn(single, 0) == a.public_turn(episode, 0)
        assert set(a.public_turn(episode, 0)) == {"train", "test"}
        assert len(a.public_turn(episode, 0)["test"]) == 1
        assert set(a.public_turn(episode, 0)["test"][0]) == {"input"}
    assert random.getstate() == before
    assert [[p["input"] for p in e["train"] + e["test"]] for e in episodes].count([p["input"] for p in episodes[0]["train"] + episodes[0]["test"]]) == 3
    assert any(len(p["input"]) == len(p["input"][0]) == 30 and sum(v == 5 for row in p["input"] for v in row) >= 30 for p in episodes[0]["test"])


def test_component_ranking_ties_and_clipping_are_taught_in_two_demos():
    a = load()
    episode = a.generate(0, {"selection": "all"}, 2, 4)
    areas = [sorted(len(c) for c in a.components(a.dilate(p["input"]))) for p in episode["train"]]
    assert areas[0] == [24, 24, 25]
    assert areas[1] == [8, 8, 9, 16, 24, 24]
    for mode in ("largest", "smallest"):
        chosen = a.generate(0, {"selection": mode}, 2, 4)
        assert a.teaching_check(chosen)["query_ambiguities"] == []
        assert a.teaching_check(chosen)["surviving_rivals"] == []


@pytest.mark.parametrize("options", [
    {"seed": True}, {"seed": -1}, {"demos": 1}, {"demos": 7}, {"demos": 2.0},
    {"queries": 0}, {"queries": 5}, {"settings": {}}, {"settings": {"selection": "bogus"}},
    {"settings": {"selection": "all", "extra": 1}}, {"settings": {"selection": True}},
])
def test_invalid_requests_fail_explicitly(options):
    a = load()
    request = dict(seed=0, settings={"selection": "all"}, demos=3, queries=4)
    request.update(options)
    with pytest.raises(ValueError):
        a.generate(**request)


def test_public_projection_is_copy_and_ignores_private_changes():
    a = load()
    e = a.generate(42, {"selection": "largest"}, 3, 4)
    public = a.public_turn(e, 0)
    changed = copy.deepcopy(e)
    changed["settings"] = {"selection": "secret"}
    changed["seed"] = 999
    changed["program_solution"] = "private"
    for pair in changed["test"]:
        pair["output"] = [[9]]
    changed["test"][1]["input"] = [[8]]
    assert public == a.public_turn(changed, 0)
    public["train"][0]["input"][0][0] = 9
    assert e["train"][0]["input"][0][0] != 9
    with pytest.raises(ValueError):
        a.public_turn(e, True)


@pytest.mark.parametrize("bad", [[[False]*7]*7, [[0]*7]*6, [[0]*7]*7, [[5]*7]*7, [[0]*7, [0]*8]])
def test_invalid_grid_grammar(bad):
    with pytest.raises(ValueError):
        load().validate_grid(bad)


def test_hash_named_writer_never_serializes_private_metadata(tmp_path):
    a = load()
    path = HOME / "workspace/parametric/audit_family.py"
    assert path.is_file(), "reusable executed-label audit/export tool is missing"
    spec = importlib.util.spec_from_file_location("f7_audit_test", path)
    audit = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(audit)
    episode = a.generate(0, {"selection": "largest"}, 2, 4)
    output = tmp_path / "export"
    manifest = audit.write_examples([episode], output)
    import hashlib
    for file in (output / "public").glob("*.json"):
        payload = file.read_bytes()
        assert file.stem == hashlib.sha256(payload).hexdigest()
        visible = json.loads(payload)
        assert set(visible) == {"train", "test"}
        assert len(visible["test"]) == 1
        assert set(visible["test"][0]) == {"input"}
    assert len(manifest["private_episodes"][0]["public_ids"]) == 4
    with pytest.raises(FileExistsError):
        audit.write_examples([episode], output)


def test_first_query_requires_a_selection_decision():
    a = load()
    for seed in (0, 1, 7, 17):
        e = a.generate(seed, {"selection": "all"}, 2, 4)
        grid = e["test"][0]["input"]
        assert len({len(c) for c in a.components(a.dilate(grid))}) >= 2
