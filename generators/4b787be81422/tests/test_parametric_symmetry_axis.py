"""Executed-label and privacy regressions for the native symmetry prototype."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


TASK_ID = "4b787be81422"
PROTOTYPE_PATH = (
    Path(__file__).resolve().parents[1] / "workspace" / "parametric" / "prototype.py"
)


def _load_prototype():
    assert PROTOTYPE_PATH.is_file(), "symmetry-axis prototype has not been implemented"
    spec = importlib.util.spec_from_file_location(
        f"parametric_{TASK_ID}_symmetry_axis", PROTOTYPE_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_parameter_contract_and_canonical_default_program() -> None:
    prototype = _load_prototype()

    assert prototype.PARAMETER["name"] == "symmetry_axis"
    assert prototype.PARAMETER["default"] == "left_right"
    assert prototype.PARAMETER["values"] == [
        "left_right", "top_bottom", "rotation_180", "bbox_major_axis"
    ]
    canonical = prototype.canonical_record()["program_solution"]
    assert prototype.program_for("left_right") == canonical
    assert '(symmetric? g "lr")' in prototype.program_for("left_right")
    assert '(symmetric? g "ud")' in prototype.program_for("top_bottom")
    assert '(symmetric? g "180")' in prototype.program_for("rotation_180")
    with pytest.raises(ValueError, match="symmetry_axis"):
        prototype.program_for("diagonal")


def test_bbox_choice_changes_the_reflection_and_uses_the_whole_canvas() -> None:
    prototype = _load_prototype()
    wide = [[0] * 8 for _ in range(8)]
    for r in range(2):
        for c in range(2, 6):
            wide[r][c] = 2
    assert prototype.python_output("left_right", wide) == [[1]]
    assert prototype.python_output("bbox_major_axis", wide) == [[7]]
    assert prototype.bbox_info(wide)["chosen_axis"] == "top_bottom"
    square = [[0] * 7 for _ in range(7)]
    for r in range(2, 5):
        for c in range(3):
            if r in (2, 4) or c in (0, 2):
                square[r][c] = 4
    assert prototype.bbox_info(square)["chosen_axis"] == "top_bottom"
    assert prototype.python_output("bbox_major_axis", square) == [[1]]
    assert prototype.python_output("left_right", square) == [[7]]


def test_live_racket_episodes_are_redacted_and_identifiable() -> None:
    prototype = _load_prototype()
    from arc_repl.racket_bridge import RacketBridge

    covered = set()
    with RacketBridge(timeout=20, max_calls_before_restart=128) as bridge:
        for axis in prototype.SYMMETRY_AXES:
            public, private = prototype.generate_episode(
                0, bridge, symmetry_axis=axis, demos=3, queries=4
            )
            covered.add(private["parameter"]["symmetry_axis"])

            assert len(public["train"]) == 3
            assert len(public["test"]) == 4
            assert all(set(pair) == {"input"} for pair in public["test"])
            assert "symmetry_axis" not in public
            assert private["checks"]["all_labels_from_live_racket"] is True
            assert private["checks"]["python_mirror_parity"] is True
            assert private["checks"]["canonical_default_parity"] is True
            assert private["teaching"]["passed"] is True
            assert private["checks"]["sequential_first_turn_equal"] is True

    assert covered == set(prototype.SYMMETRY_AXES)


def test_writer_hashes_only_visible_bytes(tmp_path) -> None:
    import copy
    import hashlib
    import json
    from reviewer_support import public_challenge_bytes, public_challenge_id

    prototype = _load_prototype()
    out = tmp_path / "evidence"
    manifest = prototype.write_evidence(out, seeds=(0,))
    assert manifest["passed"] is True
    paths = sorted((out / "public").glob("*.json"))
    assert len(paths) == len(prototype.SYMMETRY_AXES)
    for path in paths:
        public = json.loads(path.read_text())
        assert set(public) == {"train", "test"}
        assert path.read_bytes() == public_challenge_bytes(public)
        assert path.stem == hashlib.sha256(path.read_bytes()).hexdigest()
        altered = copy.deepcopy(public)
        altered["seed"] = 991
        altered["settings"] = {"symmetry_axis": "private"}
        altered["test"][0]["output"] = [[9]]
        assert public_challenge_id(altered) == path.stem
        altered["train"][0]["output"] = [[9]]
        assert public_challenge_id(altered) != path.stem


def test_query_count_preserves_independently_generated_first_turn() -> None:
    from reviewer_support import public_challenge_bytes

    prototype = _load_prototype()
    for axis in prototype.SYMMETRY_AXES:
        for demos in (3, 6):
            whole = prototype.generate_native(17, {"symmetry_axis": axis}, demos, 4)
            for queries in (1, 2, 3):
                prefix = prototype.generate_native(17, {"symmetry_axis": axis}, demos, queries)
                restricted = {"train": whole["train"], "test": whole["test"][:queries]}
                assert public_challenge_bytes(prefix) == public_challenge_bytes(restricted)
