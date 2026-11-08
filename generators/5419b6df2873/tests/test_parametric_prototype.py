"""Native parametric contract tests for the contact-color relay family."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
ROOT = next(p for p in HOME.parents if (p / "shared/runtime").exists())
PARAMETRIC = HOME / "workspace/parametric"
TASK_ID = "5419b6df2873"
SETTINGS = ("columns_only", "contact_color_rows")


def _load(name: str):
    path = PARAMETRIC / f"{name}.py"
    assert path.is_file(), f"missing parametric implementation: {path}"
    spec = importlib.util.spec_from_file_location(f"test_5419_{name}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    path = ROOT / "shared/data/canonical/puzzles.jsonl"
    for line in path.open(encoding="utf-8"):
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row["program_solution"]
    raise AssertionError("canonical task missing")


def _inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def _query_inputs(episode):
    return [pair["input"] for pair in episode["test"]]


def test_default_program_is_exact_canonical_and_alternative_is_distinct():
    """Catches a reformatted/default program or a collapsed two-setting family."""
    adapter = _load("adapter")
    programs = {mode: adapter.program({"relay_mode": mode}) for mode in SETTINGS}
    assert programs["columns_only"] == _canonical_program()
    assert programs["contact_color_rows"] != programs["columns_only"]
    assert all(program.startswith("(rule!") for program in programs.values())


@pytest.mark.parametrize("seed", [0, 17])
@pytest.mark.parametrize("demos", [2, 3, 6])
def test_matched_inputs_counts_labels_and_demo_only_setting_identification(seed, demos):
    """Catches setting-conditioned sampling, wrong counts, labels, or ambiguous settings."""
    prototype = _load("prototype")
    episodes = {
        mode: prototype.generate_episode(seed, mode, demos=demos, queries=4)
        for mode in SETTINGS
    }
    common_inputs = _inputs(episodes["columns_only"])
    assert len(common_inputs) == demos + 4
    assert len({json.dumps(grid, separators=(",", ":")) for grid in common_inputs}) == demos + 4
    assert all(_inputs(episode) == common_inputs for episode in episodes.values())
    for mode, episode in episodes.items():
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == 4
        assert episode["program_solution"] == prototype.program_for(mode)
        assert all(
            pair["output"] == prototype.output_for(pair["input"], mode)
            for pair in episode["train"] + episode["test"]
        )
        audit = prototype.audit_episode(episode, mode)
        assert audit["declared_survivors"] == [mode]
        assert audit["ambiguous_query_rivals"] == []


def test_first_two_demos_refute_every_query_relevant_declared_shortcut():
    """Catches a two-demo lesson that leaves a tested wrong rule alive on a query."""
    prototype = _load("prototype")
    for seed in (0, 17, 63):
        for mode in SETTINGS:
            episode = prototype.generate_episode(seed, mode, demos=2, queries=4)
            audit = prototype.audit_episode(episode, mode)
            assert audit["declared_survivors"] == [mode]
            assert audit["ambiguous_query_rivals"] == []
            assert audit["tested_rivals"] >= 10


def test_dependency_uses_post_fill_contact_to_select_remote_payload_rows():
    """Catches a cosmetic chain, pre-fill selector, or payload-independent row fill."""
    prototype = _load("prototype")
    episode = prototype.generate_episode(0, "contact_color_rows", demos=2, queries=4)
    grid = episode["train"][0]["input"]
    info = prototype.dependency_intermediate(grid)
    assert info["selected_color"] in range(1, 9)
    assert len(info["active_probes"]) == 1
    assert len(info["selected_payload_rows"]) >= 2
    assert info["selected_color"] not in {9, 0}
    base = prototype.output_for(grid, "columns_only")
    relay = prototype.output_for(grid, "contact_color_rows")
    wrong_order = prototype.wrong_order_output(grid)
    assert wrong_order == base
    assert relay != base
    for row in info["selected_payload_rows"]:
        assert relay[row] == [info["selected_color"]] * len(relay[row])
    assert any(
        relay[row] != [info["selected_color"]] * len(relay[row])
        for row in info["nonselected_payload_rows"]
    )


def test_every_probe_is_inert_before_column_expansion():
    """Catches adjacent probes or payload cells that let wrong-order infer a color early."""
    prototype = _load("prototype")
    episode = prototype.generate_episode(19, "columns_only", demos=2, queries=4)
    for pair in episode["train"] + episode["test"]:
        grid = pair["input"]
        for row_index, row in enumerate(grid[1:], start=1):
            for column, value in enumerate(row):
                if value != 9:
                    continue
                left = grid[row_index][column - 1] if column > 0 else 0
                right = grid[row_index][column + 1] if column + 1 < len(row) else 0
                assert left == right == 0
        assert prototype.wrong_order_output(grid) == prototype.columns_only_output(grid)


def test_queries_are_prefix_stable_and_include_substantive_30x30_boundary_case():
    """Catches query drift with demo count and a padded rather than substantive max case."""
    prototype = _load("prototype")
    short = prototype.generate_episode(23, "columns_only", demos=2, queries=4)
    long = prototype.generate_episode(23, "contact_color_rows", demos=6, queries=4)
    assert _query_inputs(short) == _query_inputs(long)
    shapes = [(len(grid), len(grid[0])) for grid in _query_inputs(short)]
    assert shapes == [(11, 14), (14, 18), (22, 25), (30, 30)]
    boundary = long["test"][-1]["input"]
    nonzero = [(r, c) for r, row in enumerate(boundary) for c, value in enumerate(row) if value]
    assert min(r for r, _ in nonzero) == 0 and max(r for r, _ in nonzero) == 29
    assert min(c for _, c in nonzero) == 0 and max(c for _, c in nonzero) == 29
    assert len(nonzero) >= 30
    relay = prototype.output_for(boundary, "contact_color_rows")
    canonical = prototype.output_for(boundary, "columns_only")
    assert relay != canonical
    assert sum(bool(value) for row in relay for value in row) >= 180


def test_public_turns_hide_private_fields_future_queries_and_query_answers():
    """Catches leakage or identifiers that depend on private answers/settings."""
    prototype = _load("prototype")
    episode = prototype.generate_episode(41, "contact_color_rows", demos=3, queries=4)
    original = prototype.public_turn_bytes(episode, 0)
    visible = json.loads(original)
    assert set(visible) == {"train", "test"}
    assert len(visible["train"]) == 3 and len(visible["test"]) == 1
    assert set(visible["test"][0]) == {"input"}
    assert visible["test"][0]["input"] == episode["test"][0]["input"]
    assert episode["test"][1]["input"] not in [pair["input"] for pair in visible["test"]]

    mutated = copy.deepcopy(episode)
    mutated["private"] = {"relay_mode": "columns_only", "secret": "changed"}
    mutated["test"][0]["output"][0][0] = (mutated["test"][0]["output"][0][0] + 1) % 10
    assert prototype.public_turn_bytes(mutated, 0) == original
    assert prototype.public_turn_id(mutated, 0) == hashlib.sha256(original).hexdigest()
    assert prototype.public_turn_bytes(episode, 1) != original


def test_bounded_audit_tool_summarizes_real_episodes_and_public_turns(tmp_path):
    """Catches a report-only audit that skips generation or emits nonpublic files."""
    audit = _load("audit")
    report = audit.run_sweep(seeds=range(2), demo_counts=(2,))
    assert report["status"] == "passed"
    assert report["episodes"] == 4
    assert report["labeled_pairs"] == 24
    assert report["failures"] == []
    assert report["tested_rivals"] >= 10
    rows = audit.write_public_samples(tmp_path, seed=0, demos=3)
    assert len(rows) == 8
    assert len({row["sha256"] for row in rows}) == 8
    assert {path.suffix for path in tmp_path.iterdir()} == {".json"}
    assert all(set(json.loads(path.read_text())) == {"train", "test"} for path in tmp_path.iterdir())


@pytest.mark.parametrize(
    "call",
    [
        lambda adapter: adapter.program({}),
        lambda adapter: adapter.program({"relay_mode": "unknown"}),
        lambda adapter: adapter.generate(True, {"relay_mode": "columns_only"}, 3, 4),
        lambda adapter: adapter.generate(0, {"relay_mode": "columns_only"}, 1, 4),
        lambda adapter: adapter.generate(0, {"relay_mode": "columns_only"}, 7, 4),
        lambda adapter: adapter.generate(0, {"relay_mode": "columns_only"}, 3, 3),
        lambda adapter: adapter.generate(0, {"relay_mode": "columns_only"}, 3, 5),
    ],
)
def test_invalid_native_contract_values_fail_closed(call):
    """Catches permissive settings/count/seed handling in the native adapter."""
    adapter = _load("adapter")
    with pytest.raises((TypeError, ValueError)):
        call(adapter)
