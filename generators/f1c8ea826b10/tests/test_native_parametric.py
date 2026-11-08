from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from reviewer_support import find_root


ROOT = find_root(__file__)
HOME = ROOT / "generators/f1c8ea826b10/workspace/parametric"


def _load(name: str):
    path = HOME / f"{name}.py"
    assert path.is_file(), f"missing native parametric source: {path.name}"
    spec = importlib.util.spec_from_file_location(f"_test_f1c8_{name}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_contract_declares_bounded_phase_anchor_family():
    contract_path = HOME / "promotion.json"
    assert contract_path.is_file(), "missing native promotion contract"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/f1c8ea826b10/workspace/parametric/adapter.py",
        "resources": [
            "generators/f1c8ea826b10/workspace/parametric/native_family.py",
            "generators/f1c8ea826b10/workspace/parametric/canonical.rkt",
        ],
        "parameters": {
            "phase_anchor": ["bbox_top_left", "minimum_marker"],
        },
        "default": {"phase_anchor": "bbox_top_left"},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
    }
    family = _load("native_family")
    assert family.SETTINGS == (
        {"phase_anchor": "bbox_top_left"},
        {"phase_anchor": "minimum_marker"},
    )
    assert family.DEFAULT == {"phase_anchor": "bbox_top_left"}


def _canonical_program() -> str:
    from reviewer_support import canonical_path

    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        programs = {
            row["program_solution"]
            for row in map(json.loads, handle)
            if row.get("task_id") == "f1c8ea826b10"
            and isinstance(row.get("program_solution"), str)
        }
    assert len(programs) == 1
    return next(iter(programs))


def test_program_preserves_exact_canonical_default_and_has_marker_anchor_variant():
    family = _load("native_family")
    canonical = _canonical_program()
    assert family.program({"phase_anchor": "bbox_top_left"}) == canonical
    alternative = family.program({"phase_anchor": "minimum_marker"})
    assert alternative != canonical
    assert alternative.startswith("(rule!")
    assert "min-marker" in alternative
    assert "bbox-of-cells" in alternative

    for bad in (
        {"phase_anchor": "unknown"},
        {"phase_anchor": True},
        {},
        {"phase_anchor": "bbox_top_left", "extra": 1},
    ):
        try:
            family.program(bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"invalid settings accepted: {bad!r}")

    adapter = _load("adapter")
    assert adapter.program({"phase_anchor": "bbox_top_left"}) == canonical


def test_reference_uses_selected_marker_coordinate_to_choose_checker_phase():
    family = _load("native_family")
    grid = [
        [5, 5, 5, 5, 5, 5, 5, 5],
        [5, 0, 1, 0, 5, 3, 0, 5],
        [5, 2, 0, 0, 5, 0, 0, 5],
        [5, 0, 0, 0, 5, 0, 0, 5],
        [5, 5, 5, 5, 5, 5, 5, 5],
    ]
    canonical = family.reference(grid, {"phase_anchor": "bbox_top_left"})
    marker = family.reference(grid, {"phase_anchor": "minimum_marker"})
    assert canonical == [
        [5, 5, 5, 5, 5, 5, 5, 5],
        [5, 1, 2, 1, 5, 3, 3, 5],
        [5, 2, 1, 2, 5, 3, 3, 5],
        [5, 1, 2, 1, 5, 3, 3, 5],
        [5, 5, 5, 5, 5, 5, 5, 5],
    ]
    assert marker == [
        [5, 5, 5, 5, 5, 5, 5, 5],
        [5, 2, 1, 2, 5, 3, 3, 5],
        [5, 1, 2, 1, 5, 3, 3, 5],
        [5, 2, 1, 2, 5, 3, 3, 5],
        [5, 5, 5, 5, 5, 5, 5, 5],
    ]
    assert grid[1][2] == 1
    assert canonical != marker


def test_generation_is_matched_prefix_stable_and_has_four_complementary_queries():
    family = _load("native_family")
    for seed in (0, 17):
        episodes = {
            setting["phase_anchor"]: family.generate(seed, setting, 2, 4)
            for setting in family.SETTINGS
        }
        inputs = {
            name: [pair["input"] for pair in episode["train"] + episode["test"]]
            for name, episode in episodes.items()
        }
        assert inputs["bbox_top_left"] == inputs["minimum_marker"]
        assert len({json.dumps(grid) for grid in inputs["bbox_top_left"]}) == 6
        for setting in family.SETTINGS:
            episode = episodes[setting["phase_anchor"]]
            assert episode["program_solution"] == family.program(setting)
            assert [
                (len(pair["input"]), len(pair["input"][0]))
                for pair in episode["test"]
            ] == [(9, 11), (15, 17), (23, 27), (30, 30)]
            for pair in episode["train"] + episode["test"]:
                assert pair["output"] == family.reference(pair["input"], setting)
            assert family.generate(seed, setting, 6, 4)["train"][:2] == episode["train"]
            assert family.generate(seed, setting, 2, 1)["test"] == episode["test"][:1]
            assert family.generate(seed, setting, 2, 1)["train"] == episode["train"]
        assert episodes["bbox_top_left"]["train"] != episodes["minimum_marker"]["train"]


def test_two_demonstrations_reject_every_declared_finite_rival():
    family = _load("native_family")
    for seed in (0, 17, 31):
        for setting in family.SETTINGS:
            episode = family.generate(seed, setting, 2, 4)
            for rival in family.rivals(setting):
                demo_outputs = [
                    family.rival_reference(pair["input"], setting, rival)
                    for pair in episode["train"]
                ]
                assert any(
                    output != pair["output"]
                    for output, pair in zip(demo_outputs, episode["train"])
                ), (seed, setting, rival)


def test_large_query_is_substantive_and_covers_rule_branches():
    family = _load("native_family")
    episode = family.generate(23, family.DEFAULT, 2, 4)
    grid = episode["test"][-1]["input"]
    assert len(grid) == len(grid[0]) == 30
    nonwalls = [(r, c, value) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 5]
    markers = [(r, c, value) for r, c, value in nonwalls if value != 0]
    blockers = sum(value == 5 for row in grid[1:-1] for value in row[1:-1])
    assert len(nonwalls) > 500
    assert len(markers) >= 20
    assert blockers > 100
    assert all(
        any((r >= 15) == bottom and (c >= 15) == right for r, c, _ in markers)
        for bottom, right in ((False, False), (False, True), (True, False), (True, True))
    )
    summary = family.scene_summary(grid)
    assert summary["solid_regions"] >= 1
    assert summary["checker_regions"] >= 1
    assert summary["three_color_regions"] >= 1
    assert summary["blocked_regions"] >= 1
    assert summary["minimum_marker_even_regions"] >= 1
    assert summary["minimum_marker_odd_regions"] >= 1


def test_counts_settings_and_grid_types_are_strict():
    family = _load("native_family")
    for key, value in (
        ("seed", True),
        ("demos", True),
        ("queries", False),
        ("seed", -1),
        ("demos", 1),
        ("demos", 7),
        ("queries", 0),
        ("queries", 5),
    ):
        args = {
            "seed": 0,
            "settings": family.DEFAULT,
            "demos": 2,
            "queries": 4,
        }
        args[key] = value
        try:
            family.generate(**args)
        except ValueError:
            pass
        else:
            raise AssertionError(f"invalid request accepted: {key}={value!r}")
    for grid in ([], [[True]], [[10]], [[-1]], [[1], [1, 2]], [[0] * 31]):
        try:
            family.reference(grid, family.DEFAULT)
        except ValueError:
            pass
        else:
            raise AssertionError(f"invalid grid accepted: {grid!r}")


def test_every_finite_rival_has_a_distinct_executable_program_claim():
    family = _load("native_family")
    for setting in family.SETTINGS:
        chosen = family.program(setting)
        programs = []
        for name in family.rivals(setting):
            source = family.rival_program(setting, name)
            assert source.startswith("(rule!")
            assert source != chosen
            programs.append(source)
        assert len(programs) == len(set(programs))


def test_audit_public_projection_is_exact_one_query_and_private_invariant():
    from copy import deepcopy
    from reviewer_support import public_challenge_bytes, public_challenge_id

    family = _load("native_family")
    audit = _load("audit_native")
    episode = family.generate(17, {"phase_anchor": "minimum_marker"}, 2, 4)
    visible = audit.first_bytes(episode)
    assert visible == public_challenge_bytes(
        {"train": episode["train"], "test": episode["test"][:1]}
    )
    assert audit.digest(visible) == public_challenge_id(
        {"train": episode["train"], "test": episode["test"][:1]}
    )
    assert visible == audit.first_bytes(
        family.generate(17, {"phase_anchor": "minimum_marker"}, 2, 1)
    )

    changed = deepcopy(episode)
    changed["settings"] = {"private": "changed"}
    changed["program_solution"] = "PRIVATE"
    changed["sampling"] = {"private": "changed"}
    changed["test"] = [dict(pair, output=[[9]]) for pair in changed["test"]]
    assert audit.first_bytes(changed) == visible
    changed["test"][1:] = [{"input": [[8]], "output": [[7]]}]
    assert audit.first_bytes(changed) == visible


def test_audit_causal_case_binds_wrong_marker_intermediate_to_changed_output():
    family = _load("native_family")
    audit = _load("audit_native")
    case = audit.causal_case(seed=0)
    settings = {"phase_anchor": "minimum_marker"}
    assert case["settings"] == settings
    assert case["program"] == family.program(settings)
    assert case["output"] == family.reference(case["input"], settings)
    assert case["counterfactual_program"] == family.rival_program(
        settings, "maximum_marker"
    )
    assert case["counterfactual_output"] == family.rival_reference(
        case["input"], settings, "maximum_marker"
    )
    assert case["output"] != case["counterfactual_output"]
    assert case["ablation"] == "wrong_intermediate"
    regions = case["intermediate_value"]["multi_color_regions"]
    assert regions
    assert any(
        item["minimum_marker_parity"] != item["maximum_marker_parity"]
        for item in regions
    )
