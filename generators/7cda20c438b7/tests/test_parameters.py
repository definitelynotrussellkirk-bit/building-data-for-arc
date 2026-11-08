"""Behavioral tests for the proposed neighborhood family, not canonical approval."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root, public_challenge_bytes


HOME = Path(__file__).resolve().parents[1]
PROTOTYPE = HOME / "workspace/parametric/prototype.py"


def load_prototype():
    assert PROTOTYPE.is_file(), "The assigned runnable parametric prototype is missing"
    spec = importlib.util.spec_from_file_location("x_neighborhood_test_subject", PROTOTYPE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def p():
    return load_prototype()


@pytest.fixture(scope="module")
def reference(p):
    with p.Reference() as runtime:
        yield runtime


def test_runnable_prototype_exists():
    load_prototype()


def test_default_is_exact_canonical_program(p):
    rows = [json.loads(line) for line in canonical_path(find_root(__file__)).read_text().splitlines()]
    sources = {row["program_solution"] for row in rows if row["task_id"] == "7cda20c438b7"}
    assert sources == {p.program({"neighborhood": "diagonal"})}


def test_shared_arms_are_filled_by_racket_and_cross_is_different(p, reference):
    grid = [[3, 0, 3, 0, 3], [0, 0, 0, 0, 0], [3, 0, 3, 0, 3]]
    want = [[3, 0, 3, 0, 3], [0, 4, 0, 4, 0], [3, 0, 3, 0, 3]]
    diagonal = {"neighborhood": "diagonal"}
    orthogonal = {"neighborhood": "orthogonal"}
    assert reference.apply(p.program(diagonal), grid) == want
    assert p.transform(grid, diagonal) == want
    assert reference.apply(p.program(orthogonal), grid) == grid
    cross = [[0, 3, 0], [3, 0, 3], [0, 3, 0]]
    assert reference.apply(p.program(orthogonal), cross) == [[0, 3, 0], [3, 4, 3], [0, 3, 0]]
    blocked = [[3, 0, 3], [0, 6, 0], [3, 0, 3]]
    assert reference.apply(p.program(diagonal), blocked) == blocked


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_counts_and_demo_only_identifiability(p, reference, demos):
    for neighborhood in ("diagonal", "orthogonal"):
        episode = p.generate(17, {"neighborhood": neighborhood}, demos, 4)
        certificate = p.verify_episode(episode, reference)
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == 4
        assert certificate["survivors"] == ["setting:" + neighborhood]
        assert len(certificate["query_checks"]) == 4
        assert all(item["identified_from_demonstrations"] for item in certificate["query_checks"])


def test_inputs_are_setting_independent_and_first_turn_is_count_independent(p):
    a = p.generate(23, {"neighborhood": "diagonal"}, 3, 4)
    b = p.generate(23, {"neighborhood": "orthogonal"}, 3, 4)
    one = p.generate(23, {"neighborhood": "diagonal"}, 3, 1)
    for split in ("train", "test"):
        assert [x["input"] for x in a[split]] == [x["input"] for x in b[split]]
    assert a["train"] != b["train"]
    first = {"train": a["train"], "test": [{"input": a["test"][0]["input"]}]}
    assert public_challenge_bytes(first) == public_challenge_bytes(one)


def test_minimum_and_30_square_have_real_content_and_racket_labels(p, reference):
    for size in (7, 30):
        grid = p.sample_input(4, "boundary", 0, size, size)
        assert len(grid) == size and all(len(row) == size for row in grid)
        for setting in ("diagonal", "orthogonal"):
            settings = {"neighborhood": setting}
            assert reference.apply(p.program(settings), grid) == p.transform(grid, settings)
        if size == 30:
            for r0 in (0, 15):
                for c0 in (0, 15):
                    assert sum(cell != 0 for row in grid[r0:r0+15] for cell in row[c0:c0+15]) >= 15


@pytest.mark.parametrize("kwargs", [
    {"demos": 1}, {"demos": 7}, {"demos": True},
    {"queries": 0}, {"queries": 5}, {"queries": 1.0}, {"seed": True},
    {"settings": {"neighborhood": "wrong"}},
    {"settings": {"neighborhood": "diagonal", "unknown": 1}},
])
def test_invalid_requests_are_rejected(p, kwargs):
    request = {"seed": 0, "settings": {"neighborhood": "diagonal"}, "demos": 3, "queries": 4}
    request.update(kwargs)
    with pytest.raises(ValueError):
        p.generate(**request)


def test_verifier_rejects_corruption_and_underteaching(p, reference):
    original = p.generate(8, {"neighborhood": "diagonal"}, 2, 4)
    changes = []
    bad = deepcopy(original)
    bad["test"][0]["output"][0][0] = 9
    changes.append(bad)
    bad = deepcopy(original)
    bad["test"][0]["input"][0][0] = True
    changes.append(bad)
    bad = deepcopy(original)
    bad["test"][0] = deepcopy(bad["train"][0])
    changes.append(bad)
    bad = deepcopy(original)
    bad["program_solution"] = p.program({"neighborhood": "orthogonal"})
    changes.append(bad)
    bad = deepcopy(original)
    # Two distinct blank demonstrations cannot teach either neighborhood rule.
    bad["train"] = [{"input": [[0]*n for _ in range(n)], "output": [[0]*n for _ in range(n)]}
                    for n in (7, 8)]
    changes.append(bad)
    for bad in changes:
        with pytest.raises(ValueError):
            p.verify_episode(bad, reference)


def test_writer_uses_visible_ids_and_refuses_duplicates_before_writing(p, reference, tmp_path):
    episode = p.generate(2, {"neighborhood": "diagonal"}, 2, 4)
    changed = deepcopy(episode)
    changed["seed"] = 888
    changed["private_note"] = "must not be visible"
    changed["test"][0]["output"][0][0] = 9
    assert public_challenge_bytes(changed) == public_challenge_bytes(episode)
    destination = tmp_path / "batch"
    with pytest.raises(ValueError, match="duplicate"):
        p.write_batch([episode, deepcopy(episode)], destination, reference)
    assert not destination.exists()
    second = p.generate(2, {"neighborhood": "orthogonal"}, 2, 4)
    p.write_batch([second, episode], destination, reference)
    private = [json.loads(line) for line in (destination / "private.jsonl").read_text().splitlines()]
    assert [row["id"] for row in private] == sorted(row["id"] for row in private)
    for row in private:
        path = destination / "public" / (row["id"] + ".json")
        raw = path.read_bytes()
        assert hashlib.sha256(raw).hexdigest() == row["id"]
        public = json.loads(raw)
        assert set(public) == {"train", "test"}
        assert all(set(pair) == {"input"} for pair in public["test"])
    with pytest.raises(FileExistsError):
        p.write_batch([episode], destination, reference)


def test_native_adapter_has_same_behavior_when_another_prototype_is_cached(p):
    import sys
    import types
    previous = sys.modules.get("prototype")
    sys.modules["prototype"] = types.ModuleType("prototype")
    try:
        spec = importlib.util.spec_from_file_location("x_native_adapter_test", HOME / "workspace/parametric/adapter.py")
        adapter = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(adapter)
        settings = {"neighborhood": "diagonal"}
        assert adapter.program(settings) == p.program(settings)
        assert adapter.generate(6, settings, 2, 4) == p.generate(6, settings, 2, 4)
    finally:
        if previous is None:
            sys.modules.pop("prototype", None)
        else:
            sys.modules["prototype"] = previous
