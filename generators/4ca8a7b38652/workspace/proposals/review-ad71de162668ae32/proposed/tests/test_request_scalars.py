"""The request boundary must not coerce malformed reproducibility controls."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from reviewer_support import find_root, load_selected_generator


GEN, _, _ = load_selected_generator("4ca8a7b38652", root=find_root(__file__))


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    ("argument", "value"),
    [("seed", True), ("seed", False), ("sample_index", True),
     ("sample_index", False), ("sample_index", -1)],
)
def test_invalid_scalar_controls_are_rejected(argument, value, difficulty):
    """Removing either boundary guard reproduces the linter's accepted calls."""
    arguments = {"seed": 991, "sample_index": 0, "difficulty": difficulty}
    arguments[argument] = value
    with pytest.raises((TypeError, ValueError), match=argument):
        GEN.generate(**arguments)


@pytest.mark.parametrize("argument", ["seed", "sample_index"])
@pytest.mark.parametrize("value", [1.0, "1", None, [], {}])
def test_other_non_integer_controls_report_the_invalid_field(argument, value):
    arguments = {"seed": 991, "sample_index": 0}
    arguments[argument] = value
    with pytest.raises((TypeError, ValueError), match=argument):
        GEN.generate(**arguments)


def test_valid_calls_preserve_the_pre_repair_random_stream():
    """A request-validation repair must not resample already-valid requests."""
    fixture = json.loads(Path(__file__).with_name("valid_request_fingerprint.json").read_text())
    actual = [GEN.generate(**arguments) for arguments in fixture["requests"]]
    encoded = json.dumps(actual, sort_keys=True, separators=(",", ":")).encode()
    assert hashlib.sha256(encoded).hexdigest() == fixture["outputs_sha256"]
