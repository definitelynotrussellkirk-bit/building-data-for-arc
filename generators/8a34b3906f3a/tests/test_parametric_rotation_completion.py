"""Native-contract and adversarial tests for the rotational completion family."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
from pathlib import Path

import pytest

from arcpuzzles import Catalog

TASK_ID = "8a34b3906f3a"
HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = HOME / "workspace" / "parametric"
_SPEC = importlib.util.spec_from_file_location(
    "_parametric_8a34b3906f3a_under_test", PARAMETRIC / "prototype.py"
)
assert _SPEC is not None and _SPEC.loader is not None
PROTOTYPE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(PROTOTYPE)


def _canonical_program() -> str:
    return Catalog(".").get(TASK_ID)["variants"][0]["program_solution"]


def _digest(value) -> str:
    return hashlib.sha256(PROTOTYPE._raw(value)).hexdigest()


def test_default_program_is_exact_canonical_and_alternate_is_distinct():
    canonical = _canonical_program()
    assert PROTOTYPE.program({"completion_style": "same_color"}) == canonical
    selected = PROTOTYPE.program({"completion_style": "contact_payload"})
    assert selected != canonical
    assert selected.startswith("(rule!")


def test_episode_counts_settings_and_inputs_are_strict_and_matched():
    for demos in range(2, 7):
        same = PROTOTYPE.generate(101 + demos, {"completion_style": "same_color"}, demos, 4)
        selected = PROTOTYPE.generate(
            101 + demos, {"completion_style": "contact_payload"}, demos, 4
        )
        assert len(same["train"]) == demos
        assert len(same["test"]) == 4
        assert [pair["input"] for pair in same["train"] + same["test"]] == [
            pair["input"] for pair in selected["train"] + selected["test"]
        ]
        hashes = [_digest(pair["input"]) for pair in same["train"] + same["test"]]
        assert len(hashes) == len(set(hashes))
        assert PROTOTYPE.certify(same)["survivors"] == [{"completion_style": "same_color"}]
        assert PROTOTYPE.certify(selected)["survivors"] == [
            {"completion_style": "contact_payload"}
        ]

    with pytest.raises((TypeError, ValueError), match="demos"):
        PROTOTYPE.generate(1, {"completion_style": "same_color"}, 1, 4)
    with pytest.raises((TypeError, ValueError), match="demos"):
        PROTOTYPE.generate(1, {"completion_style": "same_color"}, 7, 4)
    with pytest.raises((TypeError, ValueError), match="queries"):
        PROTOTYPE.generate(1, {"completion_style": "same_color"}, 3, 3)
    with pytest.raises((TypeError, ValueError), match="settings"):
        PROTOTYPE.generate(1, {"completion_style": "same_color", "extra": 1}, 3, 4)
    with pytest.raises((TypeError, ValueError), match="completion_style"):
        PROTOTYPE.generate(1, {"completion_style": "unknown"}, 3, 4)


def test_alternate_completes_then_selects_and_recolors_a_remote_payload():
    episode = PROTOTYPE.generate(17, {"completion_style": "contact_payload"}, 2, 4)
    for pair in episode["train"] + episode["test"]:
        source = pair["input"]
        output = pair["output"]
        scene = PROTOTYPE.analyze_parametric_scene(source)
        selected = scene["selected_color"]
        assert selected in PROTOTYPE.KEY_COLORS
        assert scene["selected_key_contacts_added"]
        assert scene["payload_sizes"] == {str(color): 4 for color in PROTOTYPE.KEY_COLORS}
        assert scene["color_counts"] == {str(color): 5 for color in PROTOTYPE.KEY_COLORS}

        completed = PROTOTYPE.complete_rotation(source)
        added = PROTOTYPE.added_cells(source)
        assert added
        assert all(completed[r][c] == 2 for r, c in added)
        assert all(output[r][c] == 2 for r, c in added)
        assert all(
            output[r][c] == 8
            for r, row in enumerate(source)
            for c, value in enumerate(row)
            if value == selected
        )
        assert all(
            output[r][c] == value
            for r, row in enumerate(source)
            for c, value in enumerate(row)
            if value in PROTOTYPE.KEY_COLORS and value != selected
        )
        assert PROTOTYPE.transform(source, {"completion_style": "contact_payload"}) == output
        assert PROTOTYPE.transform(source, {"completion_style": "same_color"}) == completed


def test_minimum_lesson_crosses_selected_color_at_fixed_size_and_equal_frequency():
    episode = PROTOTYPE.generate(41, {"completion_style": "contact_payload"}, 2, 4)
    scenes = [PROTOTYPE.analyze_parametric_scene(pair["input"]) for pair in episode["train"]]
    assert [scene["size"] for scene in scenes] == [15, 15]
    assert [scene["orbit_count"] for scene in scenes] == [4, 4]
    assert len({scene["selected_color"] for scene in scenes}) == 2
    for scene in scenes:
        assert len(set(scene["color_counts"].values())) == 1


def test_four_query_bank_has_boundary_spread_and_a_substantive_30_square():
    episode = PROTOTYPE.generate(23, {"completion_style": "same_color"}, 3, 4)
    sizes = [len(pair["input"]) for pair in episode["test"]]
    assert sizes == [21, 23, 25, 30]
    largest = PROTOTYPE.analyze_parametric_scene(episode["test"][-1]["input"])
    assert largest["size"] == 30
    assert largest["touches_boundary_band"]
    assert largest["red_bbox_height"] >= 27
    assert largest["red_bbox_width"] >= 27
    assert largest["orbit_count"] == 12


def test_public_turn_reveals_one_query_only_and_no_private_fields():
    episode = PROTOTYPE.generate(29, {"completion_style": "contact_payload"}, 3, 4)
    views = [PROTOTYPE.public_turn(episode, index) for index in range(4)]
    for index, view in enumerate(views):
        assert set(view) == {"train", "test"}
        assert len(view["test"]) == 1
        assert set(view["test"][0]) == {"input"}
        assert view["test"][0]["input"] == episode["test"][index]["input"]
        text = PROTOTYPE._raw(view)
        assert b"completion_style" not in text
        assert b"selected_color" not in text
        assert b"program" not in text
        assert b"query_outputs" not in text
    assert views[0] == PROTOTYPE.public_turn(episode, 0)


def test_certificate_rejects_forged_program_labels_duplicates_and_malformed_grids():
    episode = PROTOTYPE.generate(31, {"completion_style": "contact_payload"}, 2, 4)

    forged = copy.deepcopy(episode)
    forged["program_solution"] = PROTOTYPE.program({"completion_style": "same_color"})
    with pytest.raises(ValueError, match="program"):
        PROTOTYPE.certify(forged)

    wrong = copy.deepcopy(episode)
    wrong["train"][0]["output"][0][0] = 7
    with pytest.raises(ValueError, match="label"):
        PROTOTYPE.certify(wrong)

    duplicate = copy.deepcopy(episode)
    duplicate["test"][0]["input"] = copy.deepcopy(duplicate["train"][0]["input"])
    with pytest.raises(ValueError, match="distinct"):
        PROTOTYPE.certify(duplicate)

    malformed = copy.deepcopy(episode)
    malformed["test"][0]["input"][0][0] = True
    with pytest.raises(ValueError, match="integer"):
        PROTOTYPE.certify(malformed)

    stale = copy.deepcopy(episode)
    stale["train"][0]["input"][0][0] = 3
    with pytest.raises(ValueError, match="grammar|payload|key|color"):
        PROTOTYPE.certify(stale)


def test_declared_shortcuts_are_refuted_by_the_minimum_two_demonstrations():
    for seed in range(20):
        for setting in PROTOTYPE.SETTINGS:
            certificate = PROTOTYPE.certify(PROTOTYPE.generate(seed, setting, 2, 4))
            assert certificate["survivors"] == [setting]
            assert all(indices for indices in certificate["extra_refutations"].values())
            if setting["completion_style"] == "contact_payload":
                assert set(certificate["selector_refutations"]) == set(
                    PROTOTYPE.TEACHING_SELECTOR_RIVALS
                )
                assert all(indices for indices in certificate["selector_refutations"].values())
            else:
                assert certificate["selector_refutations"] == {}
