"""Focused public-projection and fail-closed tests for the reviewer exporter."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


PATH = Path(__file__).resolve().parents[1] / "workspace/parametric/audit.py"
SPEC = importlib.util.spec_from_file_location("corner_priority_export_test", PATH)
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


@pytest.mark.parametrize("settings", [{"corner_priority": "scan"}, {"corner_priority": "largest_component"}])
def test_current_turn_has_no_query_count_future_answer_or_private_fields(settings):
    adapter = AUDIT.load_adapter()
    four = adapter.generate(17, settings, demos=2, queries=4)
    four["settings"] = settings
    four["future_hint"] = "future material"
    first = AUDIT.public_first_turn(four)
    one = AUDIT.public_first_turn(adapter.generate(17, settings, demos=2, queries=1))
    assert first == one
    assert set(first) == {"train", "test"}
    assert len(first["test"]) == 1
    assert set(first["test"][0]) == {"input"}
    assert all(set(pair) == {"input", "output"} for pair in first["train"])
    assert AUDIT.SUPPORT.public_challenge_id(first) == AUDIT._sha(AUDIT.SUPPORT.public_challenge_bytes(first))
    for index in range(4):
        assert AUDIT.public_turn(four, index)["test"] == [{"input": four["test"][index]["input"]}]


def test_boolean_or_ragged_runtime_result_fails_instead_of_eliminating_a_rival():
    for value in (True, [[True]], [[0], [0, 1]], [], [[10]], "failure"):
        with pytest.raises(ValueError):
            AUDIT._grid(value)


def test_runtime_errors_propagate_instead_of_counting_as_rival_disagreement():
    class BrokenBridge:
        def eval_text(self, source):
            raise RuntimeError("synthetic evaluation failure")

    class Wrapper:
        @staticmethod
        def wrap_rule(source):
            return source

    with pytest.raises(RuntimeError, match="synthetic evaluation failure"):
        AUDIT.execute(BrokenBridge(), Wrapper(), "(lambda (g) g)", [[0]])


def test_existing_output_is_never_overwritten(tmp_path):
    protected = tmp_path / "already-present"
    protected.mkdir()
    marker = protected / "marker.json"
    marker.write_text(json.dumps({"retained": True}))
    with pytest.raises(FileExistsError):
        AUDIT.run(protected)
    assert json.loads(marker.read_text()) == {"retained": True}
