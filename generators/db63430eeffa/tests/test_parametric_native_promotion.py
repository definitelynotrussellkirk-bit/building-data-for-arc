from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import types

import pytest

from reviewer_support import canonical_path, find_root


TASK_ID = "db63430eeffa"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID
PARAMETRIC = HOME / "workspace" / "parametric"
ADAPTER_PATH = PARAMETRIC / "adapter.py"
PROMOTION_PATH = PARAMETRIC / "promotion.json"


def _ledger_program() -> str:
    programs = []
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                programs.append(row["program_solution"])
    assert len(set(programs)) == 1
    return programs[0]


def _load_adapter():
    assert ADAPTER_PATH.is_file(), f"missing native adapter: {ADAPTER_PATH}"
    spec = importlib.util.spec_from_file_location(
        "_db63430eeffa_native_adapter_test", ADAPTER_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_native_contract_and_adapter_bind_the_exact_canonical_default(monkeypatch):
    assert PROMOTION_PATH.is_file(), f"missing promotion contract: {PROMOTION_PATH}"
    contract = json.loads(PROMOTION_PATH.read_text(encoding="utf-8"))
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/db63430eeffa/workspace/parametric/adapter.py",
        "parameters": {
            "path_policy": ["both", "diagonal_first", "straight_first"]
        },
        "default": {"path_policy": "both"},
        "limits": {"demos": [2, 6], "queries": [4, 4]},
    }

    # A generic cached module named ``prototype`` must not be able to replace
    # the exact adjacent task-local implementation.
    fake = types.ModuleType("prototype")
    fake.program_for = lambda *_args, **_kwargs: "WRONG CACHED PROTOTYPE"
    monkeypatch.setitem(sys.modules, "prototype", fake)
    adapter = _load_adapter()
    assert adapter.program({"path_policy": "both"}) == _ledger_program()

    for bad in (
        None,
        {},
        {"path_policy": "bogus"},
        {"path_policy": "both", "extra": 1},
    ):
        with pytest.raises((TypeError, ValueError)):
            adapter.program(bad)


def _load_prototype():
    path = PARAMETRIC / "prototype.py"
    spec = importlib.util.spec_from_file_location(
        "_db63430eeffa_native_prototype_test", path
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def prototype():
    return _load_prototype()


@pytest.fixture(scope="module")
def racket_bridge():
    from arc_repl.racket_bridge import RacketBridge

    with RacketBridge() as bridge:
        yield bridge


def _inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def _dimensions(grid):
    return len(grid), len(grid[0])


def test_episode_supports_two_to_six_demos_and_exactly_four_queries(
    prototype, racket_bridge
):
    episodes = [
        prototype.build_episode(
            41,
            "both",
            demonstration_count=demos,
            query_count=4,
            root=ROOT,
            bridge=racket_bridge,
        )
        for demos in (2, 6)
    ]
    assert [(len(row["train"]), len(row["test"])) for row in episodes] == [
        (2, 4),
        (6, 4),
    ]
    for episode in episodes:
        assert len({json.dumps(grid) for grid in _inputs(episode)}) == len(
            _inputs(episode)
        )
        dimensions = {_dimensions(grid) for grid in _inputs(episode)}
        assert (7, 7) in dimensions
        assert (30, 30) in dimensions

    for demos in (1, 7, True):
        with pytest.raises(ValueError):
            prototype.build_episode(
                41,
                "both",
                demonstration_count=demos,
                query_count=4,
                root=ROOT,
                bridge=racket_bridge,
            )
    for queries in (1, 3, 5, 8, True):
        with pytest.raises(ValueError):
            prototype.build_episode(
                41,
                "both",
                demonstration_count=3,
                query_count=queries,
                root=ROOT,
                bridge=racket_bridge,
            )


def test_demo_and_query_streams_are_independent_and_prefix_stable(
    prototype, racket_bridge
):
    short = prototype.build_episode(
        57,
        "diagonal_first",
        demonstration_count=2,
        query_count=4,
        root=ROOT,
        bridge=racket_bridge,
    )
    long = prototype.build_episode(
        57,
        "diagonal_first",
        demonstration_count=6,
        query_count=4,
        root=ROOT,
        bridge=racket_bridge,
    )
    assert short["train"] == long["train"][:2]
    assert short["test"] == long["test"]


def test_two_demonstrations_refute_declared_feature_shortcuts(
    prototype, racket_bridge
):
    for policy in prototype.PATH_POLICIES:
        episode = prototype.build_episode(
            91,
            policy,
            demonstration_count=2,
            query_count=4,
            root=ROOT,
            bridge=racket_bridge,
        )
        checks = episode["shortcut_rivals"]
        assert len(checks) == 8
        assert {row["feature"] for row in checks} == {
            "orientation_left_to_right",
            "major_axis_row",
            "border_contact",
            "large_grid",
        }
        assert all(row["status"] == "refuted_by_demonstrations" for row in checks)
        assert all(row["demonstration_mismatch_indices"] for row in checks)
        assert all(row["query_mismatch_indices"] for row in checks)
        verification = prototype.verify_episode(
            episode, root=ROOT, bridge=racket_bridge
        )
        assert verification["passed"] is True
        assert verification["shortcut_survivors"] == []


def test_sequential_dependency_witness_flips_a_real_intermediate(
    prototype, racket_bridge
):
    episode = prototype.build_episode(
        117,
        "both",
        demonstration_count=2,
        query_count=4,
        root=ROOT,
        bridge=racket_bridge,
    )
    witness = prototype.build_sequential_dependency_witness(
        episode["train"][0]["input"],
        "both",
        root=ROOT,
        bridge=racket_bridge,
    )
    assert witness["step_a"] == (
        "read the ordered color-8 endpoints and decompose their signed delta"
    )
    assert witness["intermediate"]["major_is_row"] is True
    assert witness["wrong_intermediate"]["major_is_row"] is False
    assert witness["step_b"] == (
        "draw the selected diagonal/straight segment order using that decomposition"
    )
    assert witness["correct_output"] != witness["wrong_intermediate_output"]
    assert witness["differing_cell_count"] > 0
    assert witness["racket"]["protected"] is True


def test_admission_witness_matches_native_replay_schema(prototype, racket_bridge):
    from arcpuzzles.review_parametric_admission import validate_sequential_witness

    episode = prototype.build_episode(
        117,
        "both",
        demonstration_count=2,
        query_count=4,
        root=ROOT,
        bridge=racket_bridge,
    )
    detailed = prototype.build_sequential_dependency_witness(
        episode["train"][0]["input"],
        "both",
        root=ROOT,
        bridge=racket_bridge,
    )
    source_binding = {
        "task_id": TASK_ID,
        "files": [
            {
                "path": "generators/db63430eeffa/workspace/parametric/prototype.py",
                "sha256": "0" * 64,
            }
        ],
    }
    witness = prototype.build_admission_witness(detailed, source_binding)

    dependency = {
        "step_a": "read the ordered color-8 endpoints and decompose their signed delta",
        "intermediate": (
            "ordered endpoints, signed row/column deltas, row/column step signs, "
            "diagonal_steps, straight_steps, and major_is_row"
        ),
        "step_b": (
            "draw the selected diagonal/straight segment order using that decomposition"
        ),
        "why_b_depends_on_a": (
            "B needs the endpoint-derived step signs, diagonal/straight lengths, "
            "and major axis; flipping only major_is_row changes the protected "
            "Racket output."
        ),
        "witness_path": "witness.json",
    }
    qualification = {
        "source_binding": source_binding,
        "programs": {
            json.dumps(
                detailed["setting"],
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
                allow_nan=False,
            ): detailed["correct_program_sha256"]
        },
    }
    payload = (json.dumps(witness, sort_keys=True) + "\n").encode("utf-8")
    result = validate_sequential_witness(
        {"sequential_dependency": dependency},
        qualification,
        lambda name: payload if name == "witness.json" else b"",
    )

    assert witness["source_binding"] == source_binding
    assert witness["racket"] == {"backend": "racket", "protected": True}
    assert witness["intermediate"] == dependency["intermediate"]
    assert len(witness["cases"]) == 1
    assert witness["cases"][0]["ablation"] == "wrong_intermediate"
    assert result["status"] == "source_bound_reviewer_reported"


def test_native_adapter_generates_the_bounded_episode(prototype, racket_bridge):
    del prototype, racket_bridge  # Adapter owns its protected Racket execution.
    adapter = _load_adapter()
    episode = adapter.generate(
        131,
        {"path_policy": "straight_first"},
        2,
        4,
    )
    assert set(episode) == {"train", "test", "program_solution"}
    assert len(episode["train"]) == 2
    assert len(episode["test"]) == 4
    assert episode["program_solution"] == adapter.program(
        {"path_policy": "straight_first"}
    )
