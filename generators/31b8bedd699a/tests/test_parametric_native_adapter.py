"""Native promotion contract for the token-size / spatial-order family."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest

for _ancestor in Path(__file__).resolve().parents:
    _runtime = _ancestor / "shared" / "runtime"
    if (_ancestor / "reviewer_support.py").is_file():
        sys.path.insert(0, str(_ancestor))
        break
    if (_runtime / "reviewer_support.py").is_file():
        sys.path.insert(0, str(_runtime))
        break
else:
    raise ImportError("The test tree does not contain reviewer_support.py")

from reviewer_support import find_root


TASK_ID = "31b8bedd699a"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID / "workspace" / "parametric"
DEFAULT = {"token_size": 4, "order": "ascending"}
DESCENDING_FIVE = {"token_size": 5, "order": "descending"}


def _load(name: str):
    path = HOME / f"{name}.py"
    assert path.is_file(), f"missing {path.relative_to(ROOT)}"
    spec = importlib.util.spec_from_file_location(f"test_{TASK_ID}_{name}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _inputs(episode: dict) -> list:
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def test_contract_and_exact_canonical_default():
    adapter = _load("adapter")
    prototype = _load("prototype")
    contract = json.loads((HOME / "promotion.json").read_text())
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        "parameters": {
            "token_size": [3, 4, 5],
            "order": ["ascending", "descending"],
        },
        "default": DEFAULT,
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "qualification_demos": 3,
        "resources": [
            f"generators/{TASK_ID}/workspace/parametric/native_family.py",
            f"generators/{TASK_ID}/workspace/parametric/prototype.py",
        ],
    }
    canonical = prototype.canonical_record(root=ROOT)["program_solution"]
    assert adapter.program(DEFAULT) == canonical
    assert adapter.program(DESCENDING_FIVE) != canonical


def test_settings_and_requests_are_strict():
    adapter = _load("adapter")
    bad_settings = (
        None,
        {},
        {"token_size": 4},
        {"token_size": 4, "order": "ascending", "extra": 1},
        {"token_size": True, "order": "ascending"},
        {"token_size": 6, "order": "ascending"},
        {"token_size": 4, "order": "sideways"},
    )
    for settings in bad_settings:
        with pytest.raises((TypeError, ValueError)):
            adapter.program(settings)
        with pytest.raises((TypeError, ValueError)):
            adapter.generate(0, settings, 3, 4)

    valid = {"seed": 0, "settings": DEFAULT, "demos": 3, "queries": 4}
    for name, values in {
        "seed": (-1, True, 1.0, "0", 2**63),
        "demos": (1, 7, True, 3.0, "3"),
        "queries": (0, 5, True, 4.0, "4"),
    }.items():
        for value in values:
            with pytest.raises((TypeError, ValueError)):
                adapter.generate(**{**valid, name: value})


def test_counts_are_prefix_stable_and_query_stream_is_demo_count_independent():
    adapter = _load("adapter")
    smallest = adapter.generate(17, DEFAULT, 2, 1)
    four_queries = adapter.generate(17, DEFAULT, 2, 4)
    six_demos = adapter.generate(17, DEFAULT, 6, 4)
    assert smallest["train"] == four_queries["train"] == six_demos["train"][:2]
    assert smallest["test"] == four_queries["test"][:1]
    assert four_queries["test"] == six_demos["test"]
    assert len(six_demos["train"]) == 6
    assert len(six_demos["test"]) == 4


def test_inputs_are_identical_across_settings_and_all_are_distinct():
    adapter = _load("adapter")
    canonical = adapter.generate(29, DEFAULT, 3, 4)
    alternate = adapter.generate(29, DESCENDING_FIVE, 3, 4)
    assert _inputs(canonical) == _inputs(alternate)
    keys = [json.dumps(grid, separators=(",", ":")) for grid in _inputs(canonical)]
    assert len(keys) == len(set(keys)) == 7
    assert canonical["program_solution"] == adapter.program(DEFAULT)
    assert alternate["program_solution"] == adapter.program(DESCENDING_FIVE)


def test_two_demo_prefix_rejects_fixed_axis_and_reverse_order_shortcuts():
    adapter = _load("adapter")
    family = _load("native_family")
    for settings in (DEFAULT, DESCENDING_FIVE):
        episode = adapter.generate(11, settings, 2, 4)
        assert [family.axis_intermediate(pair["input"])["axis"] for pair in episode["train"]] == [
            "vertical",
            "horizontal",
        ]
        rivals = {
            "always_vertical": lambda grid: family.solve_with_axis(
                grid, settings["token_size"], "vertical", settings["order"]
            ),
            "always_horizontal": lambda grid: family.solve_with_axis(
                grid, settings["token_size"], "horizontal", settings["order"]
            ),
            "reverse_order": lambda grid: family.solve(
                grid,
                {
                    "token_size": settings["token_size"],
                    "order": "descending" if settings["order"] == "ascending" else "ascending",
                },
            ),
        }
        for name, rival in rivals.items():
            assert not all(rival(pair["input"]) == pair["output"] for pair in episode["train"]), name
        assert family.minimum_lesson_ambiguities(
            [pair["input"] for pair in episode["train"]], settings
        ) == []


def test_four_query_profiles_include_a_substantive_30x30_case():
    adapter = _load("adapter")
    episode = adapter.generate(0, DEFAULT, 3, 4)
    queries = [pair["input"] for pair in episode["test"]]
    assert len(queries) == 4
    large = [grid for grid in queries if len(grid) == 30 and len(grid[0]) == 30]
    assert len(large) == 1
    grid = large[0]
    nonzero = sum(cell != 0 for row in grid for cell in row)
    colors = {cell for row in grid for cell in row if cell}
    assert nonzero >= 50
    assert len(colors) >= 4
    assert any(grid[0]) or any(grid[-1]) or any(row[0] or row[-1] for row in grid)


def test_axis_intermediate_drives_sort_axis_and_changes_output_when_forced_wrong():
    prototype = _load("prototype")
    episode = prototype.generate_episode(
        0, token_size=4, tie_policy="horizontal", demo_count=3, query_count=4, root=ROOT
    )
    candidates = episode["train"] + episode["test"]
    pair = next(pair for pair in candidates if pair["profile"] == "vertical")
    state = prototype.axis_intermediate(pair["input"], "horizontal")
    assert state["axis"] == "vertical"
    assert state["row_range"] > state["col_range"]
    correct = prototype.apply_python(pair["input"], 4, "horizontal")
    wrong = prototype.apply_with_axis(pair["input"], 4, "horizontal")
    assert correct != wrong


def test_reusable_native_audit_covers_supported_prefixes_and_finite_rivals(tmp_path):
    audit = _load("audit_native_family")
    out = tmp_path / "audit.json"
    summary = audit.run_audit(out, seeds=range(4))
    assert summary["status"] == "pass"
    assert summary["seed_count"] == 4
    assert summary["setting_count"] == 6
    assert summary["episode_count"] == 24
    assert summary["supported_demo_counts"] == [2, 3, 4, 5, 6]
    assert summary["supported_query_counts"] == [1, 2, 3, 4]
    assert summary["dangerous_ambiguities"] == []
    assert summary["minimum_lesson_rivals"] == list(audit.family.TEACHING_RIVALS)
    assert summary["all_settings_share_inputs"] is True
    assert summary["all_inputs_distinct"] is True
    assert summary["all_minimum_lessons_identify_setting"] is True
    assert summary["all_query_sets_include_30x30"] is True
    assert json.loads(out.read_text()) == summary
    with pytest.raises(FileExistsError):
        audit.run_audit(out, seeds=range(1))


def test_native_audit_samples_setting_blind_inputs_once_per_seed(tmp_path, monkeypatch):
    audit = _load("audit_native_family")
    original = audit.family._full_inputs
    calls = []

    def counted(seed):
        calls.append(seed)
        return original(seed)

    monkeypatch.setattr(audit.family, "_full_inputs", counted)
    summary = audit.run_audit(tmp_path / "audit-once.json", seeds=[2, 5])
    assert summary["status"] == "pass"
    assert calls == [2, 5]
