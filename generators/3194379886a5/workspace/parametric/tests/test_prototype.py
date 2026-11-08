from __future__ import annotations

from collections import Counter
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root

TASK = "3194379886a5"
HERE = Path(__file__).resolve().parents[1]
ROOT = find_root(__file__)


def load_module():
    path = HERE / "prototype.py"
    spec = importlib.util.spec_from_file_location("parametric_3194379886a5", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def canonical_program() -> str:
    for line in canonical_path(ROOT).read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK:
            return row["program_solution"]
    raise AssertionError(TASK)


def signature(cells):
    rows = tuple(sorted(Counter(row for row, _ in cells).values()))
    cols = tuple(sorted(Counter(col for _, col in cells).values()))
    return tuple(sorted((rows, cols)))


def test_default_program_is_exact_canonical():
    module = load_module()
    assert module.program({"selection_rule": "matched_prototype"}) == canonical_program()


def test_counts_distinctness_and_setting_neutral_inputs():
    module = load_module()
    for seed in (0, 17):
        for demos in (2, 3, 6):
            canonical = module.generate(
                seed,
                {"selection_rule": "matched_prototype"},
                demos=demos,
                queries=4,
            )
            pointer = module.generate(
                seed,
                {"selection_rule": "matched_color_pointer"},
                demos=demos,
                queries=4,
            )
            assert len(canonical["train"]) == demos
            assert len(canonical["test"]) == 4
            assert [pair["input"] for pair in canonical["train"] + canonical["test"]] == [
                pair["input"] for pair in pointer["train"] + pointer["test"]
            ]
            inputs = [
                json.dumps(pair["input"], separators=(",", ":"))
                for pair in canonical["train"] + canonical["test"]
            ]
            assert len(inputs) == len(set(inputs))


def test_pointer_dependency_changes_every_constructed_label():
    module = load_module()
    for seed in (0, 3, 17, 99):
        canonical = module.generate(seed, {"selection_rule": "matched_prototype"}, 6, 4)
        pointer = module.generate(seed, {"selection_rule": "matched_color_pointer"}, 6, 4)
        for direct_pair, pointer_pair in zip(
            canonical["train"] + canonical["test"],
            pointer["train"] + pointer["test"],
        ):
            facts = module.analyze(direct_pair["input"])
            assert facts["pointer_index"] != facts["match_index"]
            assert facts["pointer_color"] == facts["prototype_colors"][facts["match_index"]]
            assert direct_pair["output"] == module.finish_python(
                direct_pair["input"], {"selection_rule": "matched_prototype"}
            )
            assert pointer_pair["output"] == module.finish_python(
                direct_pair["input"], {"selection_rule": "matched_color_pointer"}
            )
            assert direct_pair["output"] != pointer_pair["output"]


def test_teaching_bank_contains_projection_collisions_and_shortcut_failures():
    module = load_module()
    episode = module.generate(0, {"selection_rule": "matched_prototype"}, 6, 4)
    failures = 0
    for pair in episode["train"] + episode["test"]:
        facts = module.analyze(pair["input"])
        query_signature = signature(facts["query_cells"])
        matches = [
            index
            for index, cells in enumerate(facts["prototype_cells"])
            if signature(cells) == query_signature
        ]
        assert len(matches) >= 2
        failures += matches[0] != facts["match_index"]
    assert failures >= 6


def test_first_two_demonstrations_identify_the_finite_setting():
    module = load_module()
    settings = [
        {"selection_rule": "matched_prototype"},
        {"selection_rule": "matched_color_pointer"},
    ]
    for selected in settings:
        episode = module.generate(17, selected, demos=2, queries=4)
        survivors = [
            candidate
            for candidate in settings
            if all(
                module.finish_python(pair["input"], candidate) == pair["output"]
                for pair in episode["train"]
            )
        ]
        assert survivors == [selected]


def test_query_bank_reaches_lawful_maximum_canvas():
    module = load_module()
    episode = module.generate(5, {"selection_rule": "matched_color_pointer"}, 3, 4)
    shapes = {(len(pair["input"]), len(pair["input"][0])) for pair in episode["test"]}
    assert (6, 27) in shapes
    assert all(width == 4 * height + 3 for height, width in shapes)


def test_strict_argument_validation():
    module = load_module()
    with pytest.raises(ValueError):
        module.generate(True, {"selection_rule": "matched_prototype"}, 3, 4)
    with pytest.raises(ValueError):
        module.generate(0, {"selection_rule": "bad"}, 3, 4)
    with pytest.raises(ValueError):
        module.generate(0, {"selection_rule": "matched_prototype", "extra": 1}, 3, 4)
    with pytest.raises(ValueError):
        module.generate(0, {"selection_rule": "matched_prototype"}, 1, 4)
    with pytest.raises(ValueError):
        module.generate(0, {"selection_rule": "matched_prototype"}, 3, 5)



def test_first_two_demonstrations_reject_declared_panel_shortcuts():
    module = load_module()

    def predict(name, grid):
        facts = module.analyze(grid)
        if name == "fixed_0":
            selected = 0
        elif name == "fixed_1":
            selected = 1
        elif name == "fixed_2":
            selected = 2
        elif name == "projection_first":
            selected = facts["projection_matches"][0]
        elif name == "cyclic_next":
            selected = (facts["match_index"] + 1) % 3
        elif name == "cyclic_previous":
            selected = (facts["match_index"] - 1) % 3
        else:
            raise AssertionError(name)
        return module._paint(
            facts["prototype_cells"][selected],
            facts["panel_size"],
            facts["query_color"],
        )

    for seed in range(32):
        episode = module.generate(
            seed, {"selection_rule": "matched_color_pointer"}, demos=2, queries=4
        )
        for rival in (
            "fixed_0",
            "fixed_1",
            "fixed_2",
            "projection_first",
            "cyclic_next",
            "cyclic_previous",
        ):
            assert any(
                predict(rival, pair["input"]) != pair["output"]
                for pair in episode["train"]
            ), (seed, rival)

def test_bounded_audit_rejects_declared_shortcuts():
    path = HERE / "audit.py"
    spec = importlib.util.spec_from_file_location("audit_3194379886a5", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    report = module.run_audit(seeds=range(8), demo_counts=(2, 3, 6))
    assert report["status"] == "pass"
    assert report["jobs"] == 48
    assert report["pairs"] == 368
    assert report["settings_survivors"] == 48
    assert report["projection_shortcut_failures"] >= 200
    assert report["rival_survivors"] == {}
