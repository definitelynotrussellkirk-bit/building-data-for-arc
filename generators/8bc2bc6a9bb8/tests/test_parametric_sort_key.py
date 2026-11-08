"""Focused tests for the proposed occupied-area/bbox-area parametric family."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root

ROOT = find_root(__file__)
TASK_HOME = Path(__file__).resolve().parents[1]
SOURCE = TASK_HOME / "workspace" / "parametric" / "prototype.py"
TASK_ID = "8bc2bc6a9bb8"


@pytest.fixture(scope="module")
def prototype():
    assert SOURCE.is_file(), "the task-local parametric prototype must exist"
    spec = importlib.util.spec_from_file_location("parametric_8bc2bc6a9bb8", SOURCE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def racket_bridge(prototype):
    with prototype.RacketBridge(max_calls_before_restart=128) as bridge:
        yield bridge


def _canonical_program() -> str:
    rows = [
        json.loads(line)
        for line in canonical_path(ROOT).read_text().splitlines()
        if line.strip() and json.loads(line).get("task_id") == TASK_ID
    ]
    assert len(rows) == 1
    return rows[0]["program_solution"]


def _order_reversal_witness() -> list[list[int]]:
    grid = [[0] * 12 for _ in range(10)]
    grid[0][0], grid[0][2], grid[0][4] = 2, 4, 6
    for col in range(5):
        grid[2][col] = 8
    for row, col in ((4, 8), (5, 8), (6, 8), (6, 9)):
        grid[row][col] = 8
    grid[8][3] = 8
    return grid


def test_programs_preserve_exact_default_and_materialize_guarded_alternate(prototype):
    canonical = _canonical_program()
    assert prototype.canonical_source(root=ROOT) == canonical
    assert prototype.program_for("occupied_area", root=ROOT) == canonical

    alternate = prototype.program_for("bbox_area", root=ROOT)
    assert alternate != canonical
    assert "e8b-footprint" in alternate
    assert alternate.count("e8b-footprint") >= 3
    assert hashlib.sha256(prototype.program_for("occupied_area", root=ROOT).encode()).hexdigest() == hashlib.sha256(canonical.encode()).hexdigest()

    for bad in ("size", "footprint", "", None, 0, True):
        with pytest.raises(ValueError, match="sort_key"):
            prototype.program_for(bad, root=ROOT)


def test_literal_witness_reverses_the_first_two_objects_in_real_racket(
    prototype, racket_bridge
):
    grid = _order_reversal_witness()
    expected_area = [
        [0, 0, 0, 0, 0, 0, 4, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 4, 0, 0, 0],
        [2, 2, 2, 2, 2, 0, 4, 4, 0, 6],
    ]
    expected_bbox = [
        [2, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [2, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [2, 2, 0, 4, 4, 4, 4, 4, 0, 6],
    ]

    assert prototype.validate_input(grid) == []
    assert prototype.python_apply(grid, sort_key="occupied_area") == expected_area
    assert prototype.python_apply(grid, sort_key="bbox_area") == expected_bbox
    assert prototype.execute_rule(
        prototype.program_for("occupied_area", root=ROOT), grid, bridge=racket_bridge
    ) == expected_area
    assert prototype.execute_rule(
        prototype.program_for("bbox_area", root=ROOT), grid, bridge=racket_bridge
    ) == expected_bbox


def test_episode_is_fixed_deterministic_distinct_and_setting_neutral(
    prototype, racket_bridge
):
    area = prototype.make_episode(
        17,
        sort_key="occupied_area",
        demos=3,
        queries=4,
        root=ROOT,
        bridge=racket_bridge,
    )
    bbox = prototype.make_episode(
        17,
        sort_key="bbox_area",
        demos=3,
        queries=4,
        root=ROOT,
        bridge=racket_bridge,
    )
    replay = prototype.make_episode(
        17,
        sort_key="occupied_area",
        demos=3,
        queries=4,
        root=ROOT,
        bridge=racket_bridge,
    )

    assert area == replay
    assert area["parameters"] == {"sort_key": "occupied_area"}
    assert bbox["parameters"] == {"sort_key": "bbox_area"}
    assert len(area["train"]) == len(bbox["train"]) == 3
    assert len(area["test"]) == len(bbox["test"]) == 4

    area_pairs = area["train"] + area["test"]
    bbox_pairs = bbox["train"] + bbox["test"]
    assert [pair["input"] for pair in area_pairs] == [
        pair["input"] for pair in bbox_pairs
    ]
    assert len({prototype.grid_sha256(pair["input"]) for pair in area_pairs}) == 7
    assert [len(pair["input"]) for pair in area["test"]][-1] == 30
    assert [len(pair["input"][0]) for pair in area["test"]][-1] == 30

    for setting, episode, rival_episode in (
        ("occupied_area", area, bbox),
        ("bbox_area", bbox, area),
    ):
        for index, pair in enumerate(episode["train"] + episode["test"]):
            assert prototype.validate_input(pair["input"]) == []
            assert pair["output"] == prototype.python_apply(
                pair["input"], sort_key=setting
            )
            rival_pair = (rival_episode["train"] + rival_episode["test"])[index]
            assert pair["output"] != rival_pair["output"]
        rival, = episode["parameter_rivals"]
        assert rival["status"] == "refuted_by_demonstrations"
        assert rival["demonstration_mismatch_indices"] == [0, 1, 2]
        assert rival["query_mismatch_indices"] == [0, 1, 2, 3]
        assert episode["ambiguities"] == []


def test_single_query_use_matches_the_first_turn_of_four_query_use(
    prototype, racket_bridge
):
    single = prototype.make_episode(
        53,
        sort_key="bbox_area",
        demos=3,
        queries=1,
        root=ROOT,
        bridge=racket_bridge,
    )
    sequential = prototype.make_episode(
        53,
        sort_key="bbox_area",
        demos=3,
        queries=4,
        root=ROOT,
        bridge=racket_bridge,
    )

    assert single["train"] == sequential["train"]
    assert single["test"][0] == sequential["test"][0]
    assert prototype.public_challenge(single) == prototype.public_turn(sequential, 0)


def test_public_projection_is_sequential_private_invariant_and_detached(
    prototype, racket_bridge
):
    import copy

    episode = prototype.make_episode(
        29, sort_key="bbox_area", demos=3, queries=4, root=ROOT, bridge=racket_bridge
    )
    public = prototype.public_challenge(episode)
    first_turn = prototype.public_turn(episode, 0)

    assert set(public) == {"train", "test"}
    assert len(public["train"]) == 3 and len(public["test"]) == 4
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    assert first_turn == {"train": public["train"], "test": [public["test"][0]]}
    assert set(first_turn) == {"train", "test"}

    public_id = prototype.public_id(episode)
    private_change = copy.deepcopy(episode)
    private_change["seed"] = 999_999
    private_change["program"] = "private replacement"
    private_change["parameters"]["sort_key"] = "occupied_area"
    private_change["test"][0]["output"][0][0] ^= 1
    assert prototype.public_id(private_change) == public_id

    visible_change = copy.deepcopy(episode)
    visible_change["train"][0]["output"][0][0] ^= 1
    assert prototype.public_id(visible_change) != public_id

    before = copy.deepcopy(episode)
    public["train"][0]["input"][0][0] = 9
    assert episode == before


@pytest.mark.parametrize(
    "kwargs",
    [
        {"demos": 1},
        {"demos": 7},
        {"demos": True},
        {"demos": 3.0},
        {"queries": 0},
        {"queries": 9},
        {"queries": False},
        {"queries": 4.0},
    ],
)
def test_count_boundaries_reject_non_exact_or_out_of_range_values(prototype, kwargs):
    with pytest.raises(ValueError):
        prototype.make_episode(1, root=ROOT, **kwargs)


def test_thirty_by_thirty_query_has_real_edge_contacts_spread_and_exact_cells(
    prototype, racket_bridge
):
    episode = prototype.make_episode(
        31, sort_key="occupied_area", demos=3, queries=4, root=ROOT, bridge=racket_bridge
    )
    grid = episode["test"][-1]["input"]
    occupied = [
        (row, col)
        for row in range(2, len(grid))
        for col in range(len(grid[0]))
        if grid[row][col] == 8
    ]
    assert (len(grid), len(grid[0])) == (30, 30)
    assert {min(row for row, _ in occupied), max(row for row, _ in occupied)} == {2, 29}
    assert {min(col for _, col in occupied), max(col for _, col in occupied)} == {0, 29}
    assert len(occupied) >= 30
    assert all(type(cell) is int and 0 <= cell <= 9 for row in grid for cell in row)


def test_evidence_writer_and_promotion_adapter_are_complete(
    prototype, racket_bridge, tmp_path
):
    out = tmp_path / "sort-key-evidence"
    report = prototype.write_evidence(
        seed=37, out=out, demos=3, queries=4, root=ROOT, bridge=racket_bridge
    )
    assert report["status"] == "proposed_unapproved"
    assert report["approved"] is False
    assert report["parameter"] == {
        "name": "sort_key",
        "allowed_values": ["occupied_area", "bbox_area"],
        "original_default": "occupied_area",
        "selection_scope": "once_per_episode",
        "input_constraints_depend_on_parameter": False,
    }
    assert report["counts"]["episodes"] == 2
    assert report["counts"]["train_pairs"] == 6
    assert report["counts"]["query_pairs"] == 8
    assert report["counts"]["ambiguous_parameter_rivals"] == 0
    assert report["canonical_default"]["all_match"] is True

    manifest = json.loads((out / "manifest.json").read_text())
    assert manifest["schema"] == "arcpuzzles-parametric-evidence-manifest-v1"
    for row in manifest["files"]:
        path = out / row["path"]
        assert path.is_file()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row["sha256"]

    public_ids = set()
    for row in report["episodes"]:
        private = json.loads((out / row["private_path"]).read_text())
        public_path = out / row["public_path"]
        public = json.loads(public_path.read_text())
        assert public == prototype.public_challenge(private)
        assert public_path.name == f"challenge-{prototype.public_id(private)}.json"
        assert all("output" not in pair for pair in public["test"])
        assert len(private["train"]) == 3 and len(private["test"]) == 4
        public_ids.add(row["public_id"])
    assert len(public_ids) == 2

    with pytest.raises(FileExistsError):
        prototype.write_evidence(
            seed=37, out=out, demos=3, queries=4, root=ROOT, bridge=racket_bridge
        )

    adapter_path = SOURCE.parent / "adapter.py"
    promotion_path = SOURCE.parent / "promotion.json"
    assert adapter_path.is_file() and promotion_path.is_file()
    assert json.loads(promotion_path.read_text()) == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/8bc2bc6a9bb8/workspace/parametric/adapter.py",
        "parameters": {"sort_key": ["occupied_area", "bbox_area"]},
        "default": {"sort_key": "occupied_area"},
        "limits": {"demos": [2, 6], "queries": [1, 8]},
    }

    spec = importlib.util.spec_from_file_location("sort_key_adapter", adapter_path)
    assert spec is not None and spec.loader is not None
    adapter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(adapter)
    generated = adapter.generate(
        41,
        {"sort_key": "bbox_area"},
        demos=2,
        queries=1,
        bridge=racket_bridge,
    )
    assert set(generated) == {"train", "test", "program_solution"}
    assert len(generated["train"]) == 2 and len(generated["test"]) == 1
    assert generated["program_solution"] == adapter.program({"sort_key": "bbox_area"})

def test_promotion_adapter_accepts_native_positional_count_contract(
    prototype, racket_bridge
):
    adapter_path = SOURCE.parent / "adapter.py"
    spec = importlib.util.spec_from_file_location("sort_key_adapter_positional", adapter_path)
    assert spec is not None and spec.loader is not None
    adapter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(adapter)

    generated = adapter.generate(
        43,
        {"sort_key": "occupied_area"},
        2,
        1,
        bridge=racket_bridge,
    )
    assert len(generated["train"]) == 2
    assert len(generated["test"]) == 1
    assert generated["program_solution"] == adapter.program(
        {"sort_key": "occupied_area"}
    )

