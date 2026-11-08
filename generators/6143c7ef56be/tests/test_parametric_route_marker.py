from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import find_root


TASK_ID = "6143c7ef56be"
ROOT = find_root(__file__)
SOURCE = ROOT / f"generators/{TASK_ID}/workspace/parametric/prototype.py"
ADAPTER = SOURCE.with_name("adapter.py")
PROMOTION = SOURCE.with_name("promotion.json")


@pytest.fixture(scope="module")
def prototype():
    assert SOURCE.is_file(), f"missing native parametric prototype: {SOURCE}"
    name = "parametric_6143c7ef56be_prototype"
    spec = importlib.util.spec_from_file_location(name, SOURCE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def racket_bridge():
    with RacketBridge(max_calls_before_restart=128, timeout=20) as bridge:
        yield bridge


def hand_witness():
    grid = [[0] * 12 for _ in range(11)]
    for row in (4, 5):
        for col in (5, 6):
            grid[row][col] = 8
    for row, col, color in (
        (1, 2, 2),  # TL, distance 6
        (3, 9, 3),  # TR, distance 4: unique nearest
        (9, 1, 4),  # BL, distance 8: unique farthest
        (8, 9, 6),  # BR, distance 6
    ):
        grid[row][col] = color
    return grid


def expected_canonical():
    out = [[0] * 12 for _ in range(11)]
    out[4][5:7] = [2, 3]
    out[5][5:7] = [4, 6]
    return out


def expected_nearest():
    out = expected_canonical()
    out[3][9] = 3
    for col in range(6, 10):
        out[4][col] = 3
    return out


def expected_farthest():
    out = expected_canonical()
    for row in range(5, 10):
        out[row][1] = 4
    for col in range(1, 6):
        out[5][col] = 4
    return out


def test_default_program_is_exact_canonical_and_settings_fail_closed(prototype):
    canonical = prototype.canonical_source(root=ROOT)
    assert prototype.ALLOWED_ROUTE_MARKERS == ("none", "nearest", "farthest")
    assert prototype.DEFAULT_ROUTE_MARKER == "none"
    assert prototype.program_for("none", root=ROOT) == canonical
    assert prototype.program_for() == canonical
    assert prototype.program_for("nearest", root=ROOT) != canonical
    assert prototype.program_for("farthest", root=ROOT) != canonical
    assert prototype.program_for("nearest", root=ROOT) != prototype.program_for(
        "farthest", root=ROOT
    )
    for invalid in (None, "closest", 0, True):
        with pytest.raises(ValueError, match="route_marker"):
            prototype.program_for(invalid, root=ROOT)


def test_hand_derived_sequential_outputs_match_python_and_protected_racket(
    prototype, racket_bridge
):
    grid = hand_witness()
    expected = {
        "none": expected_canonical(),
        "nearest": expected_nearest(),
        "farthest": expected_farthest(),
    }
    assert prototype.validate_input(grid) == []
    trace_near = prototype.sequential_trace(grid, route_marker="nearest")
    trace_far = prototype.sequential_trace(grid, route_marker="farthest")
    assert trace_near["intermediate_value"] == {
        "quadrant": "tr",
        "color": 3,
        "source": [3, 9],
        "target": [4, 6],
        "manhattan_distance": 4,
    }
    assert trace_far["intermediate_value"] == {
        "quadrant": "bl",
        "color": 4,
        "source": [9, 1],
        "target": [5, 5],
        "manhattan_distance": 8,
    }
    for setting, wanted in expected.items():
        program = prototype.program_for(setting, root=ROOT)
        assert prototype.python_apply(grid, route_marker=setting) == wanted
        assert prototype.execute_rule(program, grid, bridge=racket_bridge) == wanted


def test_episode_is_paired_identifying_deterministic_and_has_real_30x30_query(
    prototype, racket_bridge
):
    episodes = {
        setting: prototype.make_episode(
            17,
            route_marker=setting,
            demos=3,
            queries=4,
            root=ROOT,
            bridge=racket_bridge,
        )
        for setting in prototype.ALLOWED_ROUTE_MARKERS
    }
    replay = prototype.make_episode(
        17,
        route_marker="nearest",
        demos=3,
        queries=4,
        root=ROOT,
        bridge=racket_bridge,
    )
    assert episodes["nearest"] == replay

    reference_inputs = [
        pair["input"]
        for pair in episodes["none"]["train"] + episodes["none"]["test"]
    ]
    assert len({prototype.grid_sha256(grid) for grid in reference_inputs}) == 7
    assert (len(reference_inputs[-1]), len(reference_inputs[-1][0])) == (30, 30)

    for setting, episode in episodes.items():
        assert episode["parameters"] == {"route_marker": setting}
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 4
        assert [
            pair["input"] for pair in episode["train"] + episode["test"]
        ] == reference_inputs
        assert episode["audit"]["finite_survivors"] == [setting]
        assert episode["audit"]["corner_copy"]["status"] == (
            "refuted_by_demonstrations"
        )
        assert episode["audit"]["fixed_top_left_route"]["status"] == (
            "refuted_by_demonstrations"
        )
        assert episode["ambiguities"] == []
        for pair in episode["train"] + episode["test"]:
            assert prototype.validate_input(pair["input"]) == []
            assert pair["output"] == prototype.python_apply(
                pair["input"], route_marker=setting
            )

    for index in range(3):
        outputs = {
            json.dumps(episodes[setting]["train"][index]["output"])
            for setting in prototype.ALLOWED_ROUTE_MARKERS
        }
        assert len(outputs) == 3, "each demonstration must separate all finite settings"


def test_first_query_is_invariant_to_requested_query_count(prototype, racket_bridge):
    single = prototype.make_episode(
        53,
        route_marker="farthest",
        demos=3,
        queries=1,
        root=ROOT,
        bridge=racket_bridge,
    )
    four = prototype.make_episode(
        53,
        route_marker="farthest",
        demos=3,
        queries=4,
        root=ROOT,
        bridge=racket_bridge,
    )
    assert single["train"] == four["train"]
    assert single["test"][0] == four["test"][0]
    assert prototype.public_challenge(single) == prototype.public_turn(four, 0)


def test_public_projection_hides_rule_setting_seed_and_query_labels(
    prototype, racket_bridge
):
    episode = prototype.make_episode(
        29,
        route_marker="nearest",
        demos=3,
        queries=4,
        root=ROOT,
        bridge=racket_bridge,
    )
    public = prototype.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])

    public_id = prototype.public_id(episode)
    private_change = copy.deepcopy(episode)
    private_change["seed"] = 999_999
    private_change["program"] = "private replacement"
    private_change["parameters"]["route_marker"] = "farthest"
    private_change["test"][0]["output"][0][0] ^= 1
    assert prototype.public_id(private_change) == public_id

    visible_change = copy.deepcopy(episode)
    visible_change["train"][0]["output"][0][0] ^= 1
    assert prototype.public_id(visible_change) != public_id

    before = copy.deepcopy(episode)
    public["train"][0]["input"][0][0] = 9
    assert episode == before


def test_evidence_writer_binds_racket_labels_and_opaque_public_files(
    prototype, racket_bridge, tmp_path
):
    out = tmp_path / "route-marker-evidence"
    report = prototype.write_evidence(
        seed=37,
        out=out,
        demos=3,
        queries=4,
        root=ROOT,
        bridge=racket_bridge,
    )
    assert report["schema"] == "arcpuzzles-parametric-route-marker-evidence-v1"
    assert report["status"] == "proposed_unapproved"
    assert report["approved"] is False
    assert report["parameter"] == {
        "name": "route_marker",
        "allowed_values": ["none", "nearest", "farthest"],
        "original_default": "none",
        "selection_scope": "once_per_episode",
        "input_constraints_depend_on_parameter": False,
    }
    assert report["counts"] == {
        "episodes": 3,
        "train_pairs": 9,
        "query_pairs": 12,
        "distinct_input_grids": 7,
        "settings_exercised": 3,
        "ambiguous_parameter_rivals": 0,
        "shortcut_rivals_refuted": 6,
    }
    assert report["canonical_default"]["all_match"] is True

    manifest = json.loads((out / "manifest.json").read_text())
    assert manifest["schema"] == "arcpuzzles-parametric-evidence-manifest-v1"
    for row in manifest["files"]:
        path = out / row["path"]
        assert path.is_file()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row["sha256"]

    for row in report["episodes"]:
        public_path = out / row["public_path"]
        private = json.loads((out / row["private_path"]).read_text())
        public = json.loads(public_path.read_text())
        assert public_path.name == f"challenge-{prototype.public_id(private)}.json"
        assert public == prototype.public_challenge(private)
        assert all("output" not in pair for pair in public["test"])
        assert len(private["train"]) == 3 and len(private["test"]) == 4

    with pytest.raises(FileExistsError):
        prototype.write_evidence(
            seed=37,
            out=out,
            demos=3,
            queries=4,
            root=ROOT,
            bridge=racket_bridge,
        )


def test_promotion_adapter_is_thin_bounded_and_native_positional(prototype, racket_bridge):
    assert ADAPTER.is_file() and PROMOTION.is_file()
    assert json.loads(PROMOTION.read_text()) == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/6143c7ef56be/workspace/parametric/adapter.py",
        "parameters": {"route_marker": ["none", "nearest", "farthest"]},
        "default": {"route_marker": "none"},
        "limits": {"demos": [2, 6], "queries": [1, 8]},
    }

    name = "parametric_6143c7ef56be_adapter"
    spec = importlib.util.spec_from_file_location(name, ADAPTER)
    assert spec is not None and spec.loader is not None
    adapter = importlib.util.module_from_spec(spec)
    sys.modules[name] = adapter
    spec.loader.exec_module(adapter)

    assert adapter.program({"route_marker": "none"}) == prototype.canonical_source(
        root=ROOT
    )
    generated = adapter.generate(
        43, {"route_marker": "nearest"}, 2, 1, bridge=racket_bridge
    )
    assert set(generated) == {"train", "test", "program_solution"}
    assert len(generated["train"]) == 2 and len(generated["test"]) == 1
    assert generated["program_solution"] == adapter.program(
        {"route_marker": "nearest"}
    )


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


def test_seed_and_setting_validation_rejects_bool_and_unknown_values(prototype):
    for seed in (-1, 1.5, True, "7"):
        with pytest.raises(ValueError, match="seed"):
            prototype.make_episode(seed, root=ROOT)
    for setting in (None, "closest", 1, False):
        with pytest.raises(ValueError, match="route_marker"):
            prototype.make_episode(1, route_marker=setting, root=ROOT)
