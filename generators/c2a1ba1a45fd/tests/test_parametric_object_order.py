"""Focused contracts for the native object-order parametric family."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys
import types

import pytest

from arcpuzzles.catalog import Catalog
from arcpuzzles.parametric_worker import evaluate_contract
from reviewer_support import find_root, public_challenge_bytes, public_challenge_id

TASK_ID = "c2a1ba1a45fd"
ROOT = find_root(__file__)
PARAMETRIC = ROOT / "generators" / TASK_ID / "workspace" / "parametric"
FAMILY_PATH = PARAMETRIC / "family.py"
ADAPTER_PATH = PARAMETRIC / "adapter.py"
CONTRACT_PATH = PARAMETRIC / "promotion.json"
AUDIT_PATH = PARAMETRIC / "audit_lessons.py"


def _load(path: Path, name: str):
    assert path.is_file(), f"missing requested parametric source: {path}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def family():
    return _load(FAMILY_PATH, "task_c2a1ba1a45fd_parametric_family_test")


def _inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def _digest(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def test_canonical_program_is_hash_verified_once_per_module(family, monkeypatch):
    clear = getattr(family._canonical_program, "cache_clear", lambda: None)
    clear()
    real_canonical_path = family.canonical_path
    calls = 0

    class CountingPath:
        def __init__(self, path):
            self.path = path

        def open(self, *args, **kwargs):
            nonlocal calls
            calls += 1
            return self.path.open(*args, **kwargs)

    monkeypatch.setattr(
        family, "canonical_path", lambda root: CountingPath(real_canonical_path(root))
    )
    first = family._canonical_program()
    second = family._canonical_program()
    assert first == second
    assert calls == 1
    clear()


def test_program_contract_preserves_exact_canonical_default(family):
    variants = Catalog(ROOT)._variants()[TASK_ID]
    canonical = {row["program_solution"] for row in variants}
    assert len(canonical) == 1
    assert family.PARAMETER_NAME == "object_order"
    assert family.SETTINGS == ("row_major", "size_ascending")
    assert family.DEFAULT_SETTINGS == {"object_order": "row_major"}
    programs = {
        setting: family.program({"object_order": setting})
        for setting in family.SETTINGS
    }
    assert {programs["row_major"]} == canonical
    assert programs["size_ascending"] != programs["row_major"]
    assert "(obj-size o)" in programs["size_ascending"]


@pytest.mark.parametrize("demos", range(2, 7))
@pytest.mark.parametrize("queries", range(1, 5))
def test_counts_are_exact_setting_neutral_unique_and_prefix_stable(family, demos, queries):
    canonical = family.generate(17, {"object_order": "row_major"}, demos, queries)
    alternate = family.generate(17, {"object_order": "size_ascending"}, demos, queries)
    assert len(canonical["train"]) == demos
    assert len(canonical["test"]) == queries
    assert _inputs(canonical) == _inputs(alternate)
    assert len({_digest(grid) for grid in _inputs(canonical)}) == demos + queries
    assert canonical["program_solution"] == family.program({"object_order": "row_major"})
    assert alternate["program_solution"] == family.program({"object_order": "size_ascending"})

    longest = family.generate(17, {"object_order": "row_major"}, 6, 4)
    assert canonical["train"] == longest["train"][:demos]
    assert canonical["test"] == longest["test"][:queries]


@pytest.mark.parametrize("setting", ("row_major", "size_ascending"))
def test_two_demonstrations_identify_setting_and_refute_declared_shortcuts(family, setting):
    episode = family.generate(31, {"object_order": setting}, demos=2, queries=4)
    assert family.finite_program_survivors(episode["train"]) == [setting]
    reports = family.audit_shortcuts(episode["train"], selected=setting)
    assert reports
    assert all(row["refuted"] for row in reports), reports
    assert all(row["mismatching_demo_indices"] for row in reports), reports


@pytest.mark.parametrize("seed", (0, 17, 2**32 + 9))
def test_order_parameter_changes_only_the_selected_source_objects(family, seed):
    episode = family.generate(seed, {"object_order": "row_major"}, demos=2, queries=4)
    for pair in episode["train"] + episode["test"]:
        grid = pair["input"]
        facts = family.scene_facts(grid)
        row_major = family.transform(grid, "row_major")
        size_ascending = family.transform(grid, "size_ascending")
        assert row_major != size_ascending
        sizes = [item["size"] for item in facts["source_objects"]]
        assert len(sizes) == len(set(sizes)) == 4
        assert sizes != sorted(sizes)
        assert facts["row_major_indices"] == [0, 1, 2, 3]
        assert facts["size_ascending_indices"] == sorted(range(4), key=lambda i: sizes[i])

        source_cells = {
            tuple(cell)
            for item in facts["source_objects"]
            for cell in item["cells"]
        }
        changed_between_settings = {
            (row, col)
            for row in range(len(grid))
            for col in range(len(grid[0]))
            if row_major[row][col] != size_ascending[row][col]
        }
        assert changed_between_settings
        assert changed_between_settings <= source_cells
        assert all(
            row_major[row][col] == size_ascending[row][col] == grid[row][col]
            for row in range(len(grid))
            for col in range(len(grid[0]))
            if (row, col) not in source_cells
        )


@pytest.mark.parametrize("seed", (0, 17, 101))
def test_minimum_lesson_exposes_eight_connectivity_source_selection_and_dot_filtering(family, seed):
    episode = family.generate(seed, {"object_order": "size_ascending"}, demos=2, queries=1)
    for pair in episode["train"]:
        facts = family.scene_facts(pair["input"])
        assert facts["source_count"] > max(
            count
            for color, count in facts["outside_counts"].items()
            if color != facts["source_color"]
        )
        assert facts["source_colored_legend_cells"]
        assert all(
            (row, col) not in set(facts["source_colored_legend_cells"])
            for row, col, _ in facts["dots"]
        )
        assert any(
            family.cardinal_component_count(item["cells"]) > 1
            for item in facts["source_objects"]
        )


def test_four_queries_cover_large_fields_boundaries_and_substantive_30x30(family):
    episode = family.generate(101, {"object_order": "size_ascending"}, demos=3, queries=4)
    sizes = [(len(pair["input"]), len(pair["input"][0])) for pair in episode["test"]]
    assert sizes == [(20, 24), (24, 27), (28, 30), (30, 30)]
    grid = episode["test"][-1]["input"]
    facts = family.scene_facts(grid)
    source_cells = [cell for item in facts["source_objects"] for cell in item["cells"]]
    assert len(source_cells) >= 120
    assert facts["distractor_cell_count"] >= 8
    assert any(
        row in (0, 29) or col in (0, 29)
        for row, col in source_cells
    )
    assert family.transform(grid, "row_major") != family.transform(grid, "size_ascending")


def test_public_projection_masks_query_answers_and_private_rule_material(family):
    episode = family.generate(5, {"object_order": "size_ascending"}, demos=3, queries=4)
    public = family.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert len(public["train"]) == 3 and len(public["test"]) == 4
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    assert "program_solution" not in _digest(public)
    first_query = family.public_challenge(
        family.generate(5, {"object_order": "size_ascending"}, demos=3, queries=1)
    )
    assert public["train"] == first_query["train"]
    assert public["test"][:1] == first_query["test"]

    changed_private = deepcopy(episode)
    changed_private["test"][0]["output"][0][0] = (
        changed_private["test"][0]["output"][0][0] + 1
    ) % 10
    assert family.public_challenge(changed_private) == public
    assert public_challenge_bytes(family.public_challenge(changed_private)) == public_challenge_bytes(public)
    assert public_challenge_id(family.public_challenge(changed_private)) == public_challenge_id(public)


@pytest.mark.parametrize(
    "seed,settings,demos,queries",
    [
        (True, {"object_order": "row_major"}, 2, 4),
        (-1, {"object_order": "row_major"}, 2, 4),
        (0, {"object_order": "row_major"}, 1, 4),
        (0, {"object_order": "row_major"}, 7, 4),
        (0, {"object_order": "row_major"}, 2, 0),
        (0, {"object_order": "row_major"}, 2, 5),
        (0, {"object_order": "row_major"}, 2.0, 4),
        (0, {"object_order": "other"}, 2, 4),
        (0, {"mode": "row_major"}, 2, 4),
        (0, {"object_order": "row_major", "extra": 1}, 2, 4),
    ],
)
def test_invalid_requests_fail_without_partial_episode(family, seed, settings, demos, queries):
    with pytest.raises((TypeError, ValueError)):
        family.generate(seed, settings, demos, queries)


def test_adapter_uses_exact_adjacent_family_module(monkeypatch):
    foreign = types.ModuleType("family")
    foreign.program = lambda settings: "foreign"
    foreign.generate = lambda *args, **kwargs: {"foreign": True}
    monkeypatch.setitem(sys.modules, "family", foreign)
    adapter = _load(ADAPTER_PATH, "task_c2a1ba1a45fd_parametric_adapter_test")
    assert adapter.program({"object_order": "row_major"}) != "foreign"
    assert len(adapter.generate(7, {"object_order": "row_major"}, 2, 1)["train"]) == 2


def test_native_worker_executes_both_settings_through_protected_racket():
    assert CONTRACT_PATH.is_file(), "missing promotion contract"
    contract = json.loads(CONTRACT_PATH.read_text())
    jobs = [
        {"seed": 0, "settings": {"object_order": "row_major"}, "demos": 2, "queries": 4},
        {"seed": 0, "settings": {"object_order": "size_ascending"}, "demos": 2, "queries": 4},
    ]
    result = evaluate_contract(ROOT, TASK_ID, contract, jobs)
    assert result["racket"]["backend"] == "racket"
    assert result["racket"]["protected"] is True
    assert result["racket_evaluations"] >= 12
    assert [row["survivors"] for row in result["checks"]] == [
        [{"object_order": "row_major"}],
        [{"object_order": "size_ascending"}],
    ]



def test_audit_builder_regenerates_sweep_and_canonical_public_exports(tmp_path):
    audit = _load(AUDIT_PATH, "task_c2a1ba1a45fd_parametric_audit_test")
    paths = audit.write_evidence(tmp_path, seeds=[0, 17])
    assert {path.name for path in paths} == {
        "summary.json",
        "lesson-audit.json",
        "public-identity.json",
    }
    summary = json.loads((tmp_path / "summary.json").read_text())
    assert summary["schema"] == "c2a1ba1a45fd-object-order-audit-v1"
    assert summary["episode_count"] == 80
    assert summary["failure_count"] == 0
    assert summary["ambiguous_episode_count"] == 0
    assert summary["shortcut_survivor_count"] == 0
    assert summary["substantive_30x30_episode_count"] == 20

    public_files = sorted((tmp_path / "public").glob("challenge-*.json"))
    assert len(public_files) == 4
    for public_path in public_files:
        raw = public_path.read_bytes()
        assert public_path.stem == "challenge-" + __import__("hashlib").sha256(raw).hexdigest()
        public = json.loads(raw)
        assert len(public["train"]) == 3
        assert len(public["test"]) == 4
        assert all(set(pair) == {"input"} for pair in public["test"])


def test_audit_builder_rejects_duplicate_or_boolean_seeds(tmp_path):
    audit = _load(AUDIT_PATH, "task_c2a1ba1a45fd_parametric_audit_invalid_test")
    with pytest.raises(ValueError):
        audit.write_evidence(tmp_path, seeds=[0, 0])
    with pytest.raises(TypeError):
        audit.write_evidence(tmp_path, seeds=[True])
