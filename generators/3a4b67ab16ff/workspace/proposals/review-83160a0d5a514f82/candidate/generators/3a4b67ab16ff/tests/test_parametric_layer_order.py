"""Focused tests for the isolated 3a4b67ab16ff layer-order prototype."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

import pytest

from reviewer_support import canonical_pairs, canonical_path, find_root

TASK_ID = "3a4b67ab16ff"
ROOT = find_root(__file__)
PROTOTYPE_PATH = (
    Path(__file__).resolve().parents[1] / "workspace" / "parametric" / "prototype.py"
)


def _load_prototype():
    spec = importlib.util.spec_from_file_location(
        "task_3a4b67ab16ff_parametric_layer_order", PROTOTYPE_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def prototype():
    return _load_prototype()


def _canonical_program() -> str:
    rows = [
        json.loads(line)
        for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    found = [row["program_solution"] for row in rows if row.get("task_id") == TASK_ID]
    assert len(found) == 1
    return found[0]


def _grid_digest(grid) -> str:
    return hashlib.sha256(
        json.dumps(grid, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def test_parameter_contract_is_strict_and_default_program_is_exact_canonical(prototype):
    assert prototype.PARAMETER_NAME == "layer_order"
    assert prototype.ALLOWED_SETTINGS == ("ascending", "descending")
    assert prototype.DEFAULT_SETTING == "ascending"
    assert prototype.choose_setting(0) == "ascending"
    assert prototype.choose_setting(1) == "descending"
    assert prototype.choose_setting(17) == prototype.choose_setting(17)
    with pytest.raises(TypeError):
        prototype.choose_setting(True)
    for invalid in (None, True, 0, "reverse", "Ascending"):
        error = TypeError if type(invalid) is not str else ValueError
        with pytest.raises(error):
            prototype.program_for(invalid)

    canonical = _canonical_program()
    assert prototype.program_for("ascending") == canonical
    descending = prototype.program_for("descending")
    assert descending != canonical
    marker = "(list 9 8 7 6 5 4 3 2 1)"
    assert descending.count(marker) == 1
    assert descending.replace(marker, "(range 1 10)") == canonical


def test_default_python_reference_matches_every_labelled_canonical_pair(prototype):
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert len(pairs) == 4
    for pair in pairs:
        assert prototype.apply_python(pair["input"], "ascending") == pair["output"]


def test_layer_order_changes_only_the_overlap_winner(prototype):
    generator = prototype.selected_generator(ROOT)
    grid = generator.generate(
        20261023,
        0,
        difficulty="medium",
        scene_profile="overlap_priority",
    )
    facts = generator._analysis(grid)["facts"]
    low, high = facts["active_colors"]
    overlap = (
        generator._rect_cells(facts["colors"][low]["intersection"])
        & generator._rect_cells(facts["colors"][high]["intersection"])
    )
    assert overlap

    ascending = prototype.apply_python(grid, "ascending")
    descending = prototype.apply_python(grid, "descending")
    assert ascending != descending
    assert all(ascending[row][col] == high for row, col in overlap)
    assert all(descending[row][col] == low for row, col in overlap)
    assert all(
        ascending[row][col] == descending[row][col]
        for row in range(len(grid))
        for col in range(len(grid[0]))
        if (row, col) not in overlap
    )
    assert grid == generator.generate(
        20261023,
        0,
        difficulty="medium",
        scene_profile="overlap_priority",
    )


def test_episode_has_one_setting_three_demos_and_four_distinct_queries(prototype):
    for seed, expected in ((0, "ascending"), (1, "descending")):
        episode = prototype.build_episode(seed, demo_count=3, query_count=4, root=ROOT)
        assert episode == prototype.build_episode(
            seed, demo_count=3, query_count=4, root=ROOT
        )
        assert episode["meta"][prototype.PARAMETER_NAME] == expected
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 4
        pairs = episode["train"] + episode["test"]
        assert len({_grid_digest(pair["input"]) for pair in pairs}) == 7
        rival = next(value for value in prototype.ALLOWED_SETTINGS if value != expected)
        assert all(
            pair["output"] == prototype.apply_python(pair["input"], expected)
            for pair in pairs
        )
        assert all(
            pair["output"] != prototype.apply_python(pair["input"], rival)
            for pair in pairs
        )


def test_public_export_uses_only_visible_content_and_returns_fresh_data(prototype):
    episode = prototype.build_episode(
        23, setting="descending", demo_count=3, query_count=4, root=ROOT
    )
    name = prototype.public_filename(episode)
    assert re.fullmatch(r"challenge-[0-9a-f]{64}\.json", name)

    changed_private = deepcopy(episode)
    changed_private["meta"] = {"layer_order": "ascending", "episode_seed": 999}
    for pair in changed_private["test"]:
        pair["output"] = [[0 for _ in row] for row in pair["output"]]
    assert prototype.public_filename(changed_private) == name

    changed_visible = deepcopy(episode)
    changed_visible["train"][0]["output"][0][0] = (
        changed_visible["train"][0]["output"][0][0] + 1
    ) % 10
    assert prototype.public_filename(changed_visible) != name

    public = prototype.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    serialized = json.dumps(public, sort_keys=True)
    for forbidden in ("layer_order", "episode_seed", "rule!", "program"):
        assert forbidden not in serialized
    before = deepcopy(episode)
    public["train"][0]["input"][0][0] = 9
    assert episode == before


def test_racket_evidence_covers_both_settings_queries_canonical_and_split_extrema(
    prototype, tmp_path
):
    destination = tmp_path / "evidence"
    report = prototype.write_evidence(
        destination,
        seeds=(0, 1),
        demo_count=3,
        query_count=4,
        root=ROOT,
    )
    assert report["status"] == "passed"
    assert report["canonical_default_exact_program_match"] is True
    assert report["canonical_pairs_checked_with_default_racket"] == 4
    assert report["canonical_pairs_passed_with_default_racket"] == 4
    assert report["split_extrema"]["checked"] == 4
    assert report["split_extrema"]["all_racket_matches"] is True
    assert set(report["episodes"]) == set(prototype.ALLOWED_SETTINGS)

    public_names = []
    for setting, row in report["episodes"].items():
        assert row["selected_setting"] == setting
        assert row["demo_count"] == 3
        assert row["query_count"] == 4
        assert row["distinct_input_count"] == 7
        assert row["all_demos_distinguish_rival"] is True
        assert row["all_queries_distinguish_rival"] is True
        public_path = destination / row["public_path"]
        private_path = destination / row["private_path"]
        assert public_path.is_file() and private_path.is_file()
        assert re.fullmatch(r"challenge-[0-9a-f]{64}\.json", public_path.name)
        private = json.loads(private_path.read_text(encoding="utf-8"))
        assert public_path.name == prototype.public_filename(private["episode"])
        assert json.loads(public_path.read_text(encoding="utf-8")) == (
            prototype.public_challenge(private["episode"])
        )
        public_names.append(public_path.name)
    assert len(set(public_names)) == 2

    manifest = json.loads((destination / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["report"] == "report.json"
    assert manifest["files"]
    with pytest.raises(FileExistsError):
        prototype.write_evidence(destination, seeds=(0, 1), root=ROOT)
