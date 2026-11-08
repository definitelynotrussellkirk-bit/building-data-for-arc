"""Focused saved-public projection checks, independent of the Racket runtime."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import tempfile
import unittest


HOME = Path(__file__).resolve().parents[1]


def audit_module():
    path = HOME / "workspace/parametric/audit.py"
    assert path.is_file(), "Task-local public export implementation is missing"
    spec = importlib.util.spec_from_file_location("_f812_export_tests_audit", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def episode():
    return {"settings": {"selection": "all"}, "program": "private program",
            "train": [{"input": [[0]], "output": [[7]]}],
            "test": [{"input": [[1]], "output": [[7]]},
                     {"input": [[2]], "output": [[7]]}]}


def test_public_bytes_ignore_settings_answers_and_extra_metadata():
    audit = audit_module()
    original = episode()
    changed = copy.deepcopy(original)
    changed.update(settings={"selection": "largest"}, program="different private program",
                   total_queries=100, final_turn=True)
    for pair in changed["test"]:
        pair.update(output=[[3]], private_hint="hidden")
    assert audit.project_episode(original) == audit.project_episode(changed)
    raw, digest = audit.project_episode(original)
    assert hashlib.sha256(raw).hexdigest() == digest
    assert raw.endswith(b"\n")
    assert json.loads(raw) == {"train": original["train"],
                               "test": [{"input": [[1]]}, {"input": [[2]]}]}


def test_first_turn_is_identical_when_future_queries_change():
    audit = audit_module()
    original = episode()
    changed = copy.deepcopy(original)
    changed["test"] = changed["test"][:1] + [{"input": [[9]], "output": [[0]]}]
    changed["total_queries"] = 999
    assert audit.first_turn(original) == audit.first_turn(changed)
    assert set(audit.first_turn(original)) == {"train", "test"}
    assert audit.first_turn(original)["test"] == [{"input": [[1]]}]


def test_writer_saves_exact_hash_bytes_and_private_episode():
    audit = audit_module()
    source = episode()
    with tempfile.TemporaryDirectory() as temp:
        output = Path(temp) / "exports"
        rows = audit.write_exports([source], output)
        raw, digest = audit.project_episode(source)
        assert (output / "public" / f"{digest}.json").read_bytes() == raw
        assert json.loads((output / "private.json").read_bytes()) == [source]
        assert rows[0]["sha256"] == digest
        with unittest.TestCase().assertRaises(FileExistsError):
            audit.write_exports([source], output)


def test_writer_rejects_same_visible_challenge_before_creating_output():
    audit = audit_module()
    source = episode()
    changed = copy.deepcopy(source)
    changed["test"][0]["output"] = [[5]]
    with tempfile.TemporaryDirectory() as temp:
        output = Path(temp) / "duplicate"
        with unittest.TestCase().assertRaisesRegex(ValueError, "Duplicate visible"):
            audit.write_exports([source, changed], output)
        assert not output.exists()


def test_writer_orders_public_batch_by_visible_hash():
    audit = audit_module()
    first, second = episode(), episode()
    second["test"][0]["input"] = [[4]]
    source = sorted([first, second], key=lambda e: audit.project_episode(e)[1], reverse=True)
    with tempfile.TemporaryDirectory() as temp:
        rows = audit.write_exports(source, Path(temp) / "ordered")
        ids = [row["sha256"] for row in rows]
        assert ids == sorted(ids)
        for row in rows:
            assert audit.project_episode(source[row["episode_index"]])[1] == row["sha256"]


def load_tests(_loader, _tests, _pattern):
    return unittest.TestSuite(unittest.FunctionTestCase(value) for name, value in globals().items()
                              if name.startswith("test_") and callable(value))


if __name__ == "__main__":
    unittest.main()
