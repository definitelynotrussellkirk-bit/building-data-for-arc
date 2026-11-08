"""Focused tests for the proposed stamp-mask rule parameter."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import find_root


HOME = Path(__file__).resolve().parents[1]
PROTOTYPE_PATH = HOME / "workspace" / "parametric" / "prototype.py"


def load_prototype():
    assert PROTOTYPE_PATH.is_file(), f"missing runnable prototype: {PROTOTYPE_PATH}"
    spec = importlib.util.spec_from_file_location(
        "task_0f5fbe0de38e_parametric_prototype", PROTOTYPE_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_parameter_contract_and_canonical_default_are_exact():
    proto = load_prototype()
    root = find_root(__file__)
    canonical = proto.canonical_program(root)

    assert proto.STAMP_MASKS == ("fill_cells", "template_holes")
    assert proto.DEFAULT_STAMP_MASK == "fill_cells"
    assert proto.choose_stamp_mask(0) == "template_holes"
    assert proto.choose_stamp_mask(1) == "fill_cells"
    assert proto.instantiate(canonical) == canonical
    assert proto.instantiate(canonical, "template_holes") != canonical
    for stamp_mask in proto.STAMP_MASKS:
        assert proto.retained_rule_path(stamp_mask).read_text() == proto.instantiate(
            canonical, stamp_mask
        )


@pytest.mark.parametrize("value", [None, True, 0, "fills", "template_cells"])
def test_unsupported_parameter_values_are_rejected(value):
    proto = load_prototype()
    canonical = proto.canonical_program(find_root(__file__))
    with pytest.raises(ValueError, match="stamp_mask"):
        proto.instantiate(canonical, value)


def test_public_projection_masks_parameter_program_and_query_answer():
    proto = load_prototype()
    private = {
        "seed": 1,
        "parameters": {"stamp_mask": "fill_cells"},
        "program": "secret",
        "program_sha256": "secret",
        "train": [{"input": [[0]], "output": [[1]]}],
        "test": [{"input": [[2]], "output": [[3]]}],
        "rivals": [],
    }
    public = proto.public_challenge(private)
    assert public == {
        "train": [{"input": [[0]], "output": [[1]]}],
        "test": [{"input": [[2]]}],
    }


def test_materialized_episodes_use_racket_labels_and_distinguish_the_parameter(tmp_path):
    proto = load_prototype()
    out = tmp_path / "stamp-mask"
    report = proto.materialize(out)

    assert report["status"] == "prototype"
    assert report["default_program_exact"] is True
    assert report["episode_count"] == 2
    assert report["racket_label_count"] == 8
    assert report["racket_rival_label_count"] == 8
    assert report["racket_output_count"] == 16
    assert report["settings_seen"] == ["fill_cells", "template_holes"]
    assert report["production_lessons_identifiable"] == 2

    for index in range(2):
        public = json.loads((out / "public" / f"episode-{index}.json").read_text())
        private = json.loads((out / "private" / f"episode-{index}.json").read_text())
        assert "parameters" not in public
        assert "program" not in public
        assert len(public["train"]) == 3
        assert len(public["test"]) == 1
        assert "output" not in public["test"][0]
        assert all(row["status"] == "distinguished" for row in private["rivals"])
        assert all(row["demo_differences"] for row in private["rivals"])
        assert all(row["query_differs"] for row in private["rivals"])
        rule_path = out / private["program_path"]
        assert hashlib.sha256(rule_path.read_bytes()).hexdigest() == private["program_sha256"]

    witness = json.loads((out / "private" / "cross-setting-witness.json").read_text())
    assert witness["outputs_distinct"] is True
