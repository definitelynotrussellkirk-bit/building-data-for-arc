"""Prototype-only tests for a fixed-per-episode triangle render mode.

The production generator and canonical Racket authority remain fixed to the
``outline`` rule.  These tests cover only the separate authoring prototype in
``workspace/parametric``.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root, load_selected_generator


ROOT = find_root(__file__)
PROTOTYPE_PATH = (
    Path(__file__).resolve().parents[1] / "workspace" / "parametric" / "prototype.py"
)


def _load_prototype():
    assert PROTOTYPE_PATH.is_file(), "parametric render-mode prototype is not implemented"
    spec = importlib.util.spec_from_file_location(
        "triangle_render_mode_prototype", PROTOTYPE_PATH
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_parameter_contract_and_strict_once_per_episode_selection() -> None:
    prototype = _load_prototype()
    assert prototype.ALLOWED_RENDER_MODES == ("outline", "solid")
    assert prototype.DEFAULT_RENDER_MODE == "outline"
    assert prototype.choose_render_mode(18) == "outline"
    assert prototype.choose_render_mode(19) == "solid"
    assert prototype.choose_render_mode(20) == "outline"
    for bad_seed in (True, False, 1.5, "18", None):
        with pytest.raises(TypeError, match="seed"):
            prototype.choose_render_mode(bad_seed)


def _canonical_source() -> str:
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == "1238481b674b":
                return str(row["program_solution"])
    raise AssertionError("selected canonical source not found")


def test_exact_racket_sources_and_materialization_preserve_default_authority() -> None:
    prototype = _load_prototype()
    outline = prototype.racket_source("outline", root=ROOT)
    solid = prototype.racket_source("solid", root=ROOT)

    assert outline == _canonical_source()
    assert prototype.normalized_hash(outline) == "cbabe9d66374"
    assert solid != outline
    assert prototype.normalized_hash(solid) != prototype.normalized_hash(outline)
    with pytest.raises(ValueError, match="render_mode"):
        prototype.racket_source("striped", root=ROOT)

    hashes = prototype.materialize_rules(root=ROOT)
    assert set(hashes) == {"outline", "solid"}
    for mode, source in (("outline", outline), ("solid", solid)):
        retained = prototype.rule_path(mode).read_text(encoding="utf-8")
        assert retained == source
        assert hashes[mode] == hashlib.sha256(source.encode("utf-8")).hexdigest()


def _top_left_missing_witness() -> list[list[int]]:
    grid = [[7] * 7 for _ in range(7)]
    for r, c in ((1, 5), (5, 1), (5, 5), (2, 2)):
        grid[r][c] = 5
    return grid


def test_python_mirror_changes_only_triangle_rendering_and_preserves_clues() -> None:
    prototype = _load_prototype()
    grid = _top_left_missing_witness()
    frozen = [row[:] for row in grid]

    outline = prototype.python_transform(grid, "outline")
    solid = prototype.python_transform(grid, "solid")

    assert grid == frozen
    assert outline[1][1] == 8 and solid[1][1] == 8  # inferred missing apex
    assert outline[3][2] == 7 and solid[3][2] == 8  # strict triangle interior
    assert outline[2][2] == 5 and solid[2][2] == 5  # distractor preserved
    assert all(
        solid[r][c] == outline[r][c] or (outline[r][c] == 7 and solid[r][c] == 8)
        for r in range(len(grid))
        for c in range(len(grid[0]))
    )

    generator, _, _ = load_selected_generator("1238481b674b", root=ROOT)
    for index, missing in enumerate(
        ("top_left", "top_right", "bottom_left", "bottom_right")
    ):
        generated = generator.generate(7700 + index, index, difficulty="medium",
            grid_h=10, grid_w=10, side_len=6, missing_corner=missing,
            row_offset=1, col_offset=1, distractor_variant="near_missing")
        assert prototype.python_transform(generated, "outline") == generator.rule_mirror(generated)
        assert prototype.python_transform(generated, "solid") == generator._rival_solid_triangle(generated)

    with pytest.raises(ValueError, match="four gray"):
        prototype.python_transform([[7, 7], [7, 7]], "outline")

    edge_distractor = [[7] * 7 for _ in range(7)]
    for r, c in ((1, 5), (5, 1), (5, 5), (1, 3)):
        edge_distractor[r][c] = 5
    with pytest.raises(ValueError, match="strictly interior"):
        prototype.python_transform(edge_distractor, "outline")


def test_complete_episodes_use_one_racket_labelled_mode_and_public_files_redact_it() -> None:
    prototype = _load_prototype()
    for mode, seed in (("outline", 18), ("solid", 19)):
        episode = prototype.build_episode(root=ROOT, seed=seed)
        assert episode["parameter"] == {"render_mode": mode}
        assert episode["label_authority"] == "executed_racket"
        assert [pair["sample_index"] for pair in episode["train"]] == [0, 1, 2, 3]
        assert [pair["sample_index"] for pair in episode["test"]] == [4]
        assert all(pair["render_mode"] == mode for pair in [*episode["train"], *episode["test"]])

        alternative = "solid" if mode == "outline" else "outline"
        for pair in [*episode["train"], *episode["test"]]:
            assert pair["output"] == prototype.python_transform(pair["input"], mode)
            assert pair["output"] != prototype.python_transform(pair["input"], alternative)

        public = prototype.public_challenge(episode)
        assert set(public) == {"schema", "train", "test"}
        assert len(public["train"]) == 4 and len(public["test"]) == 1
        assert all(set(pair) == {"input", "output"} for pair in public["train"])
        assert all(set(pair) == {"input"} for pair in public["test"])
        assert "render_mode" not in json.dumps(public)
        assert "racket" not in json.dumps(public).lower()


def test_evidence_report_retains_exact_execution_and_distinguishing_rivals() -> None:
    prototype = _load_prototype()
    report = prototype.build_report(
        root=ROOT, seeds={"outline": 18, "solid": 19}
    )
    assert report["schema"] == "arcpuzzles-parametric-triangle-render-evidence-v1"
    assert report["status"] == "prototype"
    assert report["parameter"]["canonical_default"] == "outline"
    assert report["parameter"]["allowed_values"] == ["outline", "solid"]
    assert report["all_retained_pairs_distinguish_settings"] is True
    assert report["selected_generator_sha256"] == (
        "907a296f355d90e454437e2c4e74b50d8d40f0541194fff99d3b847b2503a311"
    )
    assert report["racket_runtime"]["sha256"]

    for mode, setting in report["settings"].items():
        assert setting["racket_text"] == prototype.rule_path(mode).read_text(encoding="utf-8")
        assert setting["all_pairs_match_python_and_racket"] is True
        assert setting["every_demo_refutes_alternative_setting"] is True
        assert setting["query_requires_setting"] is True
        assert len(setting["executed_pairs"]) == 5
        assert all(row["settings_disagree"] for row in setting["executed_pairs"])
        assert all(row["input_sha256"] and row["output_sha256"] for row in setting["executed_pairs"])

    for challenge in report["public_challenges"].values():
        assert set(challenge["test"][0]) == {"input"}
        assert "render_mode" not in json.dumps(challenge)

    with pytest.raises(ValueError, match="exactly keys"):
        prototype.build_report(root=ROOT, seeds={"outline": 18})
