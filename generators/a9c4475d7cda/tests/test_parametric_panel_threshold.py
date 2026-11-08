"""Prototype-only tests for an episode-level panel-count threshold."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
import re
import sys
from pathlib import Path

import pytest
from arc_repl.racket_bridge import RacketBridge
from reviewer_support import find_root, load_selected_generator

TASK_ID = "a9c4475d7cda"
ROOT = find_root(__file__)
HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = HOME / "workspace" / "parametric"
PROTOTYPE = PARAMETRIC / "prototype.py"
ADAPTER = PARAMETRIC / "adapter.py"
PROMOTION = PARAMETRIC / "promotion.json"


def load_prototype():
    assert PROTOTYPE.is_file(), f"missing prototype: {PROTOTYPE}"
    spec = importlib.util.spec_from_file_location(
        "parametric_panel_threshold_prototype",
        PROTOTYPE,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_default_program_is_exact_canonical_and_alternative_changes_only_threshold():
    prototype = load_prototype()
    canonical = prototype.canonical_program(ROOT)

    assert prototype.ALLOWED_MIN_PANEL_COUNTS == (1, 2, 3)
    assert prototype.DEFAULT_MIN_PANEL_COUNT == 2
    assert prototype.render_program(canonical, 2) == canonical

    alternative = prototype.render_program(canonical, 3)
    assert alternative != canonical
    assert canonical.count(prototype.CANONICAL_THRESHOLD_FORM) == 1
    assert alternative.count(prototype.ALTERNATE_THRESHOLD_FORM) == 1
    assert alternative.replace(
        prototype.ALTERNATE_THRESHOLD_FORM,
        prototype.CANONICAL_THRESHOLD_FORM,
        1,
    ) == canonical


def test_episode_setting_selection_is_deterministic_and_covers_both_values():
    prototype = load_prototype()
    assert prototype.select_min_panel_count(0) == 2
    assert prototype.select_min_panel_count(1) == 3
    assert prototype.select_min_panel_count(2) == 1
    assert prototype.select_min_panel_count(3) == 2


@pytest.mark.parametrize("value", [True, False, 2.0, "2", 0, 4, None])
def test_invalid_threshold_values_are_rejected(value):
    prototype = load_prototype()
    canonical = prototype.canonical_program(ROOT)
    with pytest.raises((TypeError, ValueError)):
        prototype.render_program(canonical, value)


@pytest.mark.parametrize("seed", [True, False, 1.0, "1", -1])
def test_invalid_episode_seeds_are_rejected(seed):
    prototype = load_prototype()
    with pytest.raises((TypeError, ValueError)):
        prototype.select_min_panel_count(seed)



def _panel_counts(grid):
    height = len(grid)
    width = len(grid[0])
    separator_rows = [
        row for row in range(height) if all(value == 8 for value in grid[row])
    ]
    separator_cols = [
        col
        for col in range(width)
        if all(grid[row][col] == 8 for row in range(height))
    ]
    assert len(separator_rows) == len(separator_cols) == 2
    row_bands = (
        (0, separator_rows[0]),
        (separator_rows[0] + 1, separator_rows[1]),
        (separator_rows[1] + 1, height),
    )
    col_bands = (
        (0, separator_cols[0]),
        (separator_cols[0] + 1, separator_cols[1]),
        (separator_cols[1] + 1, width),
    )
    return [
        [
            sum(
                grid[row][col] == 6
                for row in range(row_start, row_end)
                for col in range(col_start, col_end)
            )
            for col_start, col_end in col_bands
        ]
        for row_start, row_end in row_bands
    ]


def _expected_output(grid, threshold):
    return [[int(count >= threshold) for count in row] for row in _panel_counts(grid)]


def test_claimed_episode_has_independent_counts_distinct_lawful_pairs_and_fixed_setting():
    prototype = load_prototype()
    generator, _path, _digest = load_selected_generator(TASK_ID, root=ROOT)
    episode = prototype.build_claimed_episode(
        24,
        min_panel_count=2,
        demos=3,
        queries=4,
        root=ROOT,
    )

    assert episode["parameters"] == {"min_panel_count": 2}
    assert episode["setting_selected_once"] is True
    assert len(episode["train"]) == 3
    assert len(episode["test"]) == 4
    assert episode["rival"]["status"] == "distinguished"
    assert episode["rival"]["demo_differences"] == [0, 1, 2]
    assert episode["rival"]["query_differences"] == [0, 1, 2, 3]

    all_pairs = episode["train"] + episode["test"]
    serialized_inputs = {
        json.dumps(pair["input"], sort_keys=True, separators=(",", ":"))
        for pair in all_pairs
    }
    assert len(serialized_inputs) == 7
    for pair in all_pairs:
        assert generator.self_check(pair["input"]) == []
        flat_counts = {count for row in _panel_counts(pair["input"]) for count in row}
        assert {2, 3} <= flat_counts
        assert pair["output"] == _expected_output(pair["input"], 2)


def test_auto_setting_is_fixed_for_all_pairs_and_both_settings_are_supported():
    prototype = load_prototype()
    episodes = [prototype.build_claimed_episode(seed, root=ROOT) for seed in (0, 1, 2)]
    assert {row["parameters"]["min_panel_count"] for row in episodes} == {1, 2, 3}
    for episode in episodes:
        threshold = episode["parameters"]["min_panel_count"]
        assert all(
            pair["output"] == _expected_output(pair["input"], threshold)
            for pair in episode["train"] + episode["test"]
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("demos", 0),
        ("demos", 17),
        ("demos", True),
        ("queries", 0),
        ("queries", 17),
        ("queries", 1.5),
    ],
)
def test_demo_and_query_count_boundaries_are_enforced(field, value):
    prototype = load_prototype()
    kwargs = {"demos": 3, "queries": 4, field: value}
    with pytest.raises((TypeError, ValueError)):
        prototype.build_claimed_episode(5, root=ROOT, **kwargs)


def test_public_bytes_and_id_ignore_private_fields_and_query_answers_but_bind_visible_data():
    prototype = load_prototype()
    episode = prototype.build_claimed_episode(24, min_panel_count=2, root=ROOT)
    original_bytes = prototype.public_bytes(episode)
    original_id = prototype.public_id(episode)

    private_mutation = deepcopy(episode)
    private_mutation["seed"] = 999999
    private_mutation["parameters"]["min_panel_count"] = 3
    private_mutation["program_solution"] = "private program changed"
    private_mutation["test"][0]["output"] = [[9, 9, 9], [9, 9, 9], [9, 9, 9]]
    assert prototype.public_bytes(private_mutation) == original_bytes
    assert prototype.public_id(private_mutation) == original_id

    visible_mutation = deepcopy(episode)
    visible_mutation["train"][0]["output"][0][0] ^= 1
    assert prototype.public_bytes(visible_mutation) != original_bytes
    assert prototype.public_id(visible_mutation) != original_id

    public = prototype.public_challenge(episode)
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    public_text = original_bytes.decode("utf-8")
    assert "min_panel_count" not in public_text
    assert "rule!" not in public_text
    assert str(episode["seed"]) not in public_text



@pytest.fixture(scope="module")
def bridge():
    with RacketBridge(timeout=30, max_calls_before_restart=128) as runtime:
        yield runtime


def _canonical_pairs():
    rows = []
    with (ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                rows.extend(row["train"])
                test = row.get("test", [])
                rows.extend(test if isinstance(test, list) else [test])
    return rows


def test_racket_execution_replays_canonical_and_matches_both_thresholds_on_seven_pairs(bridge):
    prototype = load_prototype()
    canonical = prototype.canonical_program(ROOT)
    programs = {
        threshold: prototype.render_program(canonical, threshold)
        for threshold in prototype.ALLOWED_MIN_PANEL_COUNTS
    }
    for pair in _canonical_pairs():
        assert prototype.execute(bridge, programs[2], pair["input"]) == pair["output"]

    for threshold in prototype.ALLOWED_MIN_PANEL_COUNTS:
        episode = prototype.build_claimed_episode(
            60 + threshold,
            min_panel_count=threshold,
            demos=3,
            queries=4,
            root=ROOT,
        )
        for pair in episode["train"] + episode["test"]:
            assert prototype.execute(bridge, programs[threshold], pair["input"]) == pair["output"]
            rival = 3 if threshold == 2 else 2
            assert prototype.execute(bridge, programs[rival], pair["input"]) != pair["output"]


def test_materializer_retains_two_racket_backed_four_query_episodes_and_visible_ids(tmp_path):
    prototype = load_prototype()
    out = tmp_path / "gallery"
    report = prototype.materialize(out, seed=2600, demos=3, queries=4, root=ROOT)

    assert report["status"] == "proposed_prototype"
    assert report["default_program_exact_canonical"] is True
    assert report["canonical_pairs_all_match"] is True
    assert report["complete_episodes"] == 3
    assert report["pairs_per_episode"] == {"train": 3, "test": 4}
    assert report["all_labels_and_rivals_executed_in_racket"] is True
    assert report["all_queries_identified_from_demonstrations"] is True
    assert set(report["episode_parameters"]) == {"1", "2", "3"}

    public_files = sorted((out / "public").glob("challenge-*.json"))
    private_files = sorted((out / "private").glob("episode-threshold-*.json"))
    assert len(public_files) == len(private_files) == 3
    default_program_path = out / "private" / "program-threshold-2.rkt"
    alternative_program_path = out / "private" / "program-threshold-3.rkt"
    assert default_program_path.is_file()
    assert alternative_program_path.is_file()
    assert default_program_path.read_text(encoding="utf-8") == prototype.canonical_program(ROOT)
    assert alternative_program_path.read_text(encoding="utf-8") == prototype.render_program(
        prototype.canonical_program(ROOT),
        3,
    )
    assert (out / "private" / "setting-difference-witness.json").is_file()
    assert (out / "manifest.json").is_file()

    for path in public_files:
        assert re.fullmatch(r"challenge-[0-9a-f]{64}\.json", path.name)
        public = json.loads(path.read_text())
        assert len(public["train"]) == 3
        assert len(public["test"]) == 4
        assert all(set(pair) == {"input", "output"} for pair in public["train"])
        assert all(set(pair) == {"input"} for pair in public["test"])
        text = path.read_text()
        assert "min_panel_count" not in text
        assert "rule!" not in text

    for path in private_files:
        episode = json.loads(path.read_text())
        assert len(episode["test"]) == 4
        assert len(episode["label_checks"]) == 7
        assert all(
            row["consistent_settings"] == [episode["parameters"]["min_panel_count"]]
            and row["query_answer_used_for_demo_fit"] is False
            for row in episode["query_identification"]
        )


def _load_adapter(monkeypatch):
    assert ADAPTER.is_file(), f"missing adapter: {ADAPTER}"
    monkeypatch.syspath_prepend(str(PARAMETRIC))
    sys.modules.pop("prototype", None)
    spec = importlib.util.spec_from_file_location("panel_threshold_adapter", ADAPTER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_promotion_adapter_reuses_prototype_and_declares_bounded_interface(monkeypatch):
    adapter = _load_adapter(monkeypatch)
    prototype = load_prototype()
    canonical = prototype.canonical_program(ROOT)

    assert adapter.program({"min_panel_count": 2}) == canonical
    assert adapter.program({"min_panel_count": 3}) == prototype.render_program(canonical, 3)
    generated = adapter.generate(
        77,
        {"min_panel_count": 3},
        demos=2,
        queries=4,
    )
    assert set(generated) == {"train", "test", "program_solution"}
    assert len(generated["train"]) == 2
    assert len(generated["test"]) == 4
    assert all(
        pair["output"] == _expected_output(pair["input"], 3)
        for pair in generated["train"] + generated["test"]
    )

    promotion = json.loads(PROMOTION.read_text())
    assert promotion == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/a9c4475d7cda/workspace/parametric/adapter.py",
        "parameters": {"min_panel_count": [1, 2, 3]},
        "default": {"min_panel_count": 2},
        "limits": {"demos": [1, 16], "queries": [1, 16]},
        "resources": [f"generators/a9c4475d7cda/workspace/parametric/programs/threshold-{t}.rkt" for t in (1, 2, 3)],
    }


@pytest.mark.parametrize(
    "settings",
    [
        {},
        {"min_panel_count": 2, "extra": 1},
        {"min_panel_count": True},
        {"min_panel_count": 4},
    ],
)
def test_promotion_adapter_rejects_missing_unknown_or_invalid_settings(monkeypatch, settings):
    adapter = _load_adapter(monkeypatch)
    with pytest.raises((TypeError, ValueError)):
        adapter.program(settings)
