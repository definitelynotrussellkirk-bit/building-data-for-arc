from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
from reviewer_support import canonical_path, find_root


TASK_ID = "ff76baf6c2d9"
ROOT = find_root(__file__)
PARAMETRIC = ROOT / f"generators/{TASK_ID}/workspace/parametric"
POLICIES = ("anchor_is_2", "anchor_is_not_2")


def _load(name: str):
    path = PARAMETRIC / f"{name}.py"
    assert path.is_file(), f"missing {path.relative_to(ROOT)}"
    spec = importlib.util.spec_from_file_location(f"_{TASK_ID}_{name}_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row["program_solution"]
    raise KeyError(TASK_ID)


def _frozen(grid):
    return tuple(tuple(row) for row in grid)


def _inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def test_default_program_is_exact_canonical_and_alternative_is_distinct():
    adapter = _load("adapter")
    canonical = adapter.program({"mirror_when": "anchor_is_2"})
    alternative = adapter.program({"mirror_when": "anchor_is_not_2"})
    assert canonical == _canonical_program()
    assert alternative.strip()
    assert alternative != canonical


def test_promotion_contract_declares_bounded_native_family():
    contract = json.loads((PARAMETRIC / "promotion.json").read_text(encoding="utf-8"))
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        "parameters": {"mirror_when": ["anchor_is_2", "anchor_is_not_2"]},
        "default": {"mirror_when": "anchor_is_2"},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "resources": [
            f"generators/{TASK_ID}/workspace/parametric/canonical.rkt",
            f"generators/{TASK_ID}/workspace/parametric/mirror_non_two.rkt",
        ],
    }


@pytest.mark.parametrize(
    "settings",
    [
        {},
        {"mirror_when": "anchor_is_2", "extra": 1},
        {"mirror_when": "all"},
        {"mirror_when": 2},
        {"mirror_when": True},
        None,
    ],
)
def test_adapter_rejects_malformed_or_undeclared_settings(settings):
    adapter = _load("adapter")
    with pytest.raises(ValueError, match="mirror_when"):
        adapter.program(settings)


@pytest.mark.parametrize(
    "seed,demos,queries",
    [
        (True, 3, 4),
        (1.0, 3, 4),
        (-1, 3, 4),
        (2**63, 3, 4),
        (0, True, 4),
        (0, 1, 4),
        (0, 7, 4),
        (0, 3, True),
        (0, 3, 0),
        (0, 3, 5),
    ],
)
def test_generate_rejects_count_and_seed_coercions(seed, demos, queries):
    adapter = _load("adapter")
    with pytest.raises(ValueError):
        adapter.generate(seed, {"mirror_when": "anchor_is_2"}, demos, queries)


def test_counts_are_prefix_stable_inputs_are_distinct_and_setting_neutral():
    adapter = _load("adapter")
    short = adapter.generate(17, {"mirror_when": "anchor_is_2"}, 2, 1)
    full = adapter.generate(17, {"mirror_when": "anchor_is_2"}, 6, 4)
    other = adapter.generate(17, {"mirror_when": "anchor_is_not_2"}, 6, 4)

    assert short["train"] == full["train"][:2]
    assert short["test"] == full["test"][:1]
    assert _inputs(other) == _inputs(full)
    assert len({_frozen(grid) for grid in _inputs(full)}) == 10


def test_every_pair_has_both_anchor_classes_and_two_asymmetric_templates():
    prototype = _load("prototype")
    episode = prototype.generate(31, {"mirror_when": "anchor_is_2"}, 6, 4)
    for pair in episode["train"] + episode["test"]:
        facts = prototype.scene_facts(pair["input"])
        assert facts["source_count"] == 2
        assert facts["anchor_colors"][0] == 2 or facts["anchor_colors"][1] == 2
        assert any(color != 2 for color in facts["anchor_colors"])
        assert facts["asymmetric_source_count"] == 2
        assert facts["target_counts"][2] >= 1
        assert sum(count for color, count in facts["target_counts"].items() if color != 2) >= 1


def test_minimum_demos_identify_each_setting_and_reject_global_orientation_shortcuts():
    prototype = _load("prototype")
    for selected in POLICIES:
        episode = prototype.generate(5, {"mirror_when": selected}, 2, 4)
        chosen = [pair["output"] for pair in episode["train"]]
        other = "anchor_is_not_2" if selected == "anchor_is_2" else "anchor_is_2"
        rivals = {
            "other_setting": [
                prototype.apply_rule(pair["input"], mirror_when=other)
                for pair in episode["train"]
            ],
            "always_preserve": [
                prototype.apply_rival(pair["input"], mode="always_preserve")
                for pair in episode["train"]
            ],
            "always_mirror": [
                prototype.apply_rival(pair["input"], mode="always_mirror")
                for pair in episode["train"]
            ],
            "identity": [pair["input"] for pair in episode["train"]],
        }
        assert all(outputs != chosen for outputs in rivals.values())
        assert all(
            pair["output"] == prototype.apply_rule(pair["input"], mirror_when=selected)
            for pair in episode["train"] + episode["test"]
        )


def test_fourth_query_is_substantive_30_by_30_boundary_stress():
    adapter = _load("adapter")
    episode = adapter.generate(91, {"mirror_when": "anchor_is_not_2"}, 3, 4)
    pair = episode["test"][3]
    grid, output = pair["input"], pair["output"]
    assert (len(grid), len(grid[0])) == (30, 30)
    changed = [
        (row, col)
        for row in range(30)
        for col in range(30)
        if grid[row][col] != output[row][col]
    ]
    assert len(changed) >= 16
    occupied = [
        (row, col)
        for row in range(30)
        for col in range(30)
        if grid[row][col] != 0
    ]
    assert max(row for row, _ in occupied) - min(row for row, _ in occupied) >= 25
    assert max(col for _, col in occupied) - min(col for _, col in occupied) >= 25


def test_public_turn_hides_private_rule_answers_future_queries_and_total_count():
    prototype = _load("prototype")
    one = prototype.generate(7, {"mirror_when": "anchor_is_2"}, 3, 1)
    four = prototype.generate(7, {"mirror_when": "anchor_is_2"}, 3, 4)
    first_one = prototype.public_turn(one, 0)
    first_four = prototype.public_turn(four, 0)
    assert first_one == first_four
    assert set(first_four) == {"train", "test"}
    assert len(first_four["test"]) == 1
    assert set(first_four["test"][0]) == {"input"}
    text = json.dumps(first_four, sort_keys=True)
    for forbidden in ("mirror_when", "program", "settings", "answer", "query_count", "final"):
        assert forbidden not in text


def test_adapter_loads_its_adjacent_prototype_even_when_generic_name_is_cached(monkeypatch):
    import sys
    import types

    fake = types.ModuleType("prototype")
    fake.native_program = lambda _settings: "wrong"
    fake.native_generate = lambda *_args: {"wrong": True}
    monkeypatch.setitem(sys.modules, "prototype", fake)
    adapter = _load("adapter")
    assert adapter.program({"mirror_when": "anchor_is_2"}) == _canonical_program()


def test_audit_counterfactual_changes_only_the_input_derived_anchor_origin():
    audit = _load("audit")
    canonical = _canonical_program()
    counterfactual = audit.wrong_origin_program(canonical)
    assert counterfactual != canonical
    assert canonical.count("(let ((anchor (fst anchors)))") == 1
    assert counterfactual.count("(let ((anchor (fst cells)))") == 1
    assert counterfactual.replace(
        "(let ((anchor (fst cells)))",
        "(let ((anchor (fst anchors)))",
    ) == canonical


def test_audit_declares_finite_named_racket_shortcuts():
    audit = _load("audit")
    programs = audit.shortcut_programs(_canonical_program())
    assert set(programs) == {
        "always_preserve",
        "always_mirror",
        "mirror_left_source",
        "mirror_right_source",
        "identity",
    }
    assert all(isinstance(program, str) and program.strip() for program in programs.values())
    assert len(set(programs.values())) == len(programs)
    assert _canonical_program() not in programs.values()


def test_minimum_demos_alternate_which_row_major_source_has_color_two():
    prototype = _load("prototype")
    for seed in range(64):
        episode = prototype.generate(seed, {"mirror_when": "anchor_is_2"}, 2, 1)
        sides = [
            prototype.scene_facts(pair["input"])["anchor_colors"].index(2)
            for pair in episode["train"]
        ]
        assert sides[0] != sides[1], (seed, sides)
