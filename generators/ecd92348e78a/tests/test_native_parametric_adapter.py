"""Native promotion regressions for the bar-chart rule family."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root


TASK_ID = "ecd92348e78a"
HOME = Path(__file__).parents[1]
PARAMETRIC = HOME / "workspace" / "parametric"
ADAPTER_PATH = PARAMETRIC / "adapter.py"
PROMOTION_PATH = PARAMETRIC / "promotion.json"


def _load(path: Path, name: str):
    assert path.is_file(), f"missing {path}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    rows = []
    with canonical_path(find_root(__file__)).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("content_hash") == TASK_ID:
                rows.append(row["program_solution"])
    assert len(rows) == 1
    return rows[0]


def _all_inputs(episode):
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def test_promotion_contract_declares_native_four_setting_family():
    promotion = json.loads(PROMOTION_PATH.read_text(encoding="utf-8"))

    assert promotion["schema"] == "arcpuzzles-parametric-adapter-v1"
    assert promotion["adapter"].endswith(f"generators/{TASK_ID}/workspace/parametric/adapter.py")
    assert promotion["parameters"] == {
        "sort_order": ["descending", "ascending"],
        "bar_alignment": ["top", "bottom"],
    }
    assert promotion["default"] == {"sort_order": "descending", "bar_alignment": "top"}
    assert promotion["limits"] == {"demos": [2, 6], "queries": [4, 4]}
    assert promotion["qualification_demos"] == 2
    assert promotion["base_review_policy"]["schema"] == "arcpuzzles-built-base-review-v1"


def test_default_program_is_exact_canonical_bytes():
    adapter = _load(ADAPTER_PATH, "ecd92348e78a_native_adapter_default")

    assert adapter.program({"sort_order": "descending", "bar_alignment": "top"}) == _canonical_program()


def test_every_demo_count_has_stable_four_queries_and_one_30x30_stress_case():
    adapter = _load(ADAPTER_PATH, "ecd92348e78a_native_adapter_counts")
    setting = {"sort_order": "ascending", "bar_alignment": "bottom"}
    query_banks = []

    for demos in range(2, 7):
        episode = adapter.generate(41, setting, demos=demos, queries=4)
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == 4
        assert episode["program_solution"] == adapter.program(setting)
        serialized = [json.dumps(grid, separators=(",", ":")) for grid in _all_inputs(episode)]
        assert len(serialized) == len(set(serialized))
        stress = [pair for pair in episode["test"] if len(pair["input"]) == 30 and len(pair["input"][0]) == 30]
        assert len(stress) == 1
        assert sum(cell != 0 for row in stress[0]["input"] for cell in row) >= 250
        query_banks.append(episode["test"])

    assert all(bank == query_banks[0] for bank in query_banks[1:])


def test_two_demonstrations_identify_each_setting_and_labels_match_python_oracle():
    adapter = _load(ADAPTER_PATH, "ecd92348e78a_native_adapter_teaching")
    prototype = _load(PARAMETRIC / "prototype.py", "ecd92348e78a_native_prototype_teaching")
    settings = [
        {"sort_order": sort_order, "bar_alignment": alignment}
        for sort_order in ("descending", "ascending")
        for alignment in ("top", "bottom")
    ]

    for index, selected in enumerate(settings):
        episode = adapter.generate(100 + index, selected, demos=2, queries=4)
        survivors = []
        for candidate in settings:
            outputs = [
                prototype.solve_variant(
                    pair["input"], candidate["sort_order"], candidate["bar_alignment"]
                )
                for pair in episode["train"]
            ]
            if outputs == [pair["output"] for pair in episode["train"]]:
                survivors.append(candidate)
        assert survivors == [selected]
        for split in ("train", "test"):
            assert [pair["output"] for pair in episode[split]] == [
                prototype.solve_variant(
                    pair["input"], selected["sort_order"], selected["bar_alignment"]
                )
                for pair in episode[split]
            ]


def test_wrong_intermediate_order_changes_a_nondefault_result():
    adapter = _load(ADAPTER_PATH, "ecd92348e78a_native_adapter_causal")
    selected = {"sort_order": "ascending", "bar_alignment": "bottom"}
    wrong = {"sort_order": "descending", "bar_alignment": "bottom"}
    episode = adapter.generate(19, selected, demos=2, queries=4)
    prototype = _load(PARAMETRIC / "prototype.py", "ecd92348e78a_native_prototype_causal")

    assert any(
        prototype.solve_variant(pair["input"], wrong["sort_order"], wrong["bar_alignment"])
        != pair["output"]
        for pair in episode["test"]
    )


@pytest.mark.parametrize(
    ("seed", "settings", "demos", "queries", "error"),
    [
        (True, {"sort_order": "descending", "bar_alignment": "top"}, 2, 4, TypeError),
        (0, {"sort_order": "descending"}, 2, 4, ValueError),
        (0, {"sort_order": "sideways", "bar_alignment": "top"}, 2, 4, ValueError),
        (0, {"sort_order": "descending", "bar_alignment": "top"}, 1, 4, ValueError),
        (0, {"sort_order": "descending", "bar_alignment": "top"}, 2, 3, ValueError),
    ],
)
def test_native_adapter_rejects_malformed_requests(seed, settings, demos, queries, error):
    adapter = _load(ADAPTER_PATH, f"ecd92348e78a_native_adapter_invalid_{demos}_{queries}")
    with pytest.raises(error):
        adapter.generate(seed, settings, demos=demos, queries=queries)
