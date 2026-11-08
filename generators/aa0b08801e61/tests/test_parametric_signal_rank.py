"""Focused contract tests for the symmetry signal-rank parametric family."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, canonical_path, public_challenge_bytes

TASK_ID = "aa0b08801e61"
HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]
PARAMETRIC = HOME / "workspace" / "parametric"
MODES = ("classify_all", "signal_rank")


def _load(filename: str):
    path = PARAMETRIC / filename
    assert path.is_file(), f"missing parametric source: {path}"
    name = "_aa0b_parametric_" + filename.replace(".", "_")
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    programs = {
        row["program_solution"]
        for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines()
        if line.strip()
        and (row := json.loads(line)).get("task_id") == TASK_ID
        and isinstance(row.get("program_solution"), str)
    }
    assert len(programs) == 1
    return next(iter(programs))


def _frozen(grid):
    return tuple(tuple(row) for row in grid)


def _inputs(episode, split):
    return [pair["input"] for pair in episode[split]]


def test_required_native_files_and_contract():
    for filename in (
        "adapter.py",
        "prototype.py",
        "promotion.json",
        "README.md",
        "canonical.rkt",
        "signal_rank.rkt",
        "audit_lessons.py",
    ):
        assert (PARAMETRIC / filename).is_file()
    contract = json.loads((PARAMETRIC / "promotion.json").read_text(encoding="utf-8"))
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/aa0b08801e61/workspace/parametric/adapter.py",
        "parameters": {"selection": list(MODES)},
        "default": {"selection": "classify_all"},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "resources": [
            "generators/aa0b08801e61/workspace/parametric/prototype.py",
            "generators/aa0b08801e61/workspace/parametric/canonical.rkt",
            "generators/aa0b08801e61/workspace/parametric/signal_rank.rkt",
        ],
    }


def test_default_program_is_byte_exact_canonical_and_alternate_is_distinct():
    adapter = _load("adapter.py")
    canonical = _canonical_program()
    assert adapter.program({"selection": "classify_all"}) == canonical
    assert adapter.program({"selection": "signal_rank"}) != canonical


def test_python_default_matches_every_labeled_canonical_pair():
    prototype = _load("prototype.py")
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert len(pairs) >= 3
    for pair in pairs:
        assert prototype.solve(pair["input"], {"selection": "classify_all"}) == pair["output"]


def test_independent_counts_literal_labels_and_distinct_inputs():
    adapter = _load("adapter.py")
    prototype = _load("prototype.py")
    for mode in MODES:
        settings = {"selection": mode}
        for demos in range(2, 7):
            for queries in range(1, 5):
                episode = adapter.generate(19, settings, demos, queries)
                assert (len(episode["train"]), len(episode["test"])) == (demos, queries)
                assert episode["program_solution"] == adapter.program(settings)
                pairs = episode["train"] + episode["test"]
                assert len({_frozen(pair["input"]) for pair in pairs}) == demos + queries
                for pair in pairs:
                    assert pair["output"] == prototype.solve(pair["input"], settings)
                    for grid in (pair["input"], pair["output"]):
                        assert type(grid) is list and 1 <= len(grid) <= 30
                        assert type(grid[0]) is list and 1 <= len(grid[0]) <= 30
                        assert all(type(row) is list and len(row) == len(grid[0]) for row in grid)
                        assert all(type(cell) is int and 0 <= cell <= 9 for row in grid for cell in row)
        assert settings == {"selection": mode}


def test_matched_inputs_determinism_and_prefix_stability():
    adapter = _load("adapter.py")
    episodes = [adapter.generate(7, {"selection": mode}, 3, 4) for mode in MODES]
    for split in ("train", "test"):
        assert _inputs(episodes[0], split) == _inputs(episodes[1], split)
    baseline = copy.deepcopy(episodes[0])
    assert adapter.generate(7, {"selection": MODES[0]}, 3, 4) == baseline
    assert _inputs(adapter.generate(7, {"selection": MODES[0]}, 2, 4), "test") == _inputs(baseline, "test")
    assert _inputs(adapter.generate(7, {"selection": MODES[0]}, 6, 4), "test") == _inputs(baseline, "test")
    for count in range(1, 5):
        assert adapter.generate(7, {"selection": MODES[0]}, 3, count)["test"] == baseline["test"][:count]
    episodes[0]["train"][0]["input"][0][0] = 9
    assert adapter.generate(7, {"selection": MODES[0]}, 3, 4) == baseline


def test_signal_rank_dependency_and_scene_contract():
    adapter = _load("adapter.py")
    prototype = _load("prototype.py")
    for seed in range(24):
        episode = adapter.generate(seed, {"selection": "signal_rank"}, 2, 4)
        for pair in episode["train"] + episode["test"]:
            facts = prototype.observables(pair["input"])
            assert facts["signal_color"] == 1
            assert 1 <= facts["signal_rank"] <= facts["payload_count"]
            assert facts["selected_source_color"] != facts["selected_class_color"]
            assert facts["selected_rank"] == facts["signal_rank"]
            assert pair["output"] == prototype.paint_selected(
                pair["input"], facts["payloads"][facts["signal_rank"] - 1]
            )


def test_two_demonstrations_identify_settings_and_bounded_shortcuts():
    adapter = _load("adapter.py")
    prototype = _load("prototype.py")
    for seed in range(64):
        for mode in MODES:
            episode = adapter.generate(seed, {"selection": mode}, 2, 4)
            other = MODES[1 - MODES.index(mode)]
            assert any(
                prototype.solve(pair["input"], {"selection": other}) != pair["output"]
                for pair in episode["train"]
            )
            for rival in prototype.RIVAL_NAMES:
                changes_query = any(
                    prototype.solve_rival(pair["input"], rival) != pair["output"]
                    for pair in episode["test"]
                )
                if changes_query:
                    assert any(
                        prototype.solve_rival(pair["input"], rival) != pair["output"]
                        for pair in episode["train"]
                    ), (seed, mode, rival)


def test_four_queries_are_distinct_shuffled_profiles_with_30x30_stress():
    adapter = _load("adapter.py")
    prototype = _load("prototype.py")
    observed_orders = set()
    for seed in range(16):
        episode = adapter.generate(seed, {"selection": "signal_rank"}, 3, 4)
        grids = [pair["input"] for pair in episode["test"]]
        shapes = tuple((len(grid), len(grid[0])) for grid in grids)
        observed_orders.add(shapes)
        assert set(shapes) == {(15, 17), (19, 22), (24, 27), (30, 30)}
        assert len({_frozen(grid) for grid in grids}) == 4
        stress = grids[shapes.index((30, 30))]
        facts = prototype.observables(stress)
        assert facts["payload_count"] >= 8
        assert sum(cell != 0 for row in stress for cell in row) >= 40
        h, w = len(stress), len(stress[0])
        assert any(stress[0][c] for c in range(w))
        assert any(stress[h - 1][c] for c in range(w))
        assert any(stress[r][0] for r in range(h))
        assert any(stress[r][w - 1] for r in range(h))
    assert len(observed_orders) > 1


def test_public_projection_masks_private_answers_and_future_queries():
    adapter = _load("adapter.py")
    full = adapter.generate(23, {"selection": "signal_rank"}, 3, 4)
    first = adapter.generate(23, {"selection": "signal_rank"}, 3, 1)
    assert public_challenge_bytes(first) == public_challenge_bytes({
        "train": full["train"],
        "test": full["test"][:1],
        "program_solution": "ignored",
        "settings": {"selection": "changed"},
    })
    changed = copy.deepcopy(full)
    changed["program_solution"] = "private replacement"
    changed["settings"] = {"selection": "classify_all"}
    for pair in changed["test"]:
        pair["output"] = [[9]]
    assert public_challenge_bytes(changed) == public_challenge_bytes(full)
    changed["train"][0]["output"][0][0] ^= 1
    assert public_challenge_bytes(changed) != public_challenge_bytes(full)


@pytest.mark.parametrize(
    "call",
    [
        lambda adapter: adapter.program({}),
        lambda adapter: adapter.program({"selection": "unknown"}),
        lambda adapter: adapter.program({"selection": "classify_all", "extra": 1}),
        lambda adapter: adapter.generate(True, {"selection": "classify_all"}, 2, 4),
        lambda adapter: adapter.generate(-1, {"selection": "classify_all"}, 2, 4),
        lambda adapter: adapter.generate(0, {"selection": "classify_all"}, 1, 4),
        lambda adapter: adapter.generate(0, {"selection": "classify_all"}, 7, 4),
        lambda adapter: adapter.generate(0, {"selection": "classify_all"}, 2, 0),
        lambda adapter: adapter.generate(0, {"selection": "classify_all"}, 2, 5),
        lambda adapter: adapter.generate(0, {"selection": "classify_all"}, 2.0, 4),
    ],
)
def test_malformed_controls_are_rejected(call):
    adapter = _load("adapter.py")
    with pytest.raises((TypeError, ValueError)):
        call(adapter)
