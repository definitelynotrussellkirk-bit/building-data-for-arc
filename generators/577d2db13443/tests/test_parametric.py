"""Native parametric endpoint-cap family regressions for 577d2db13443."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]
PARAMETRIC = HOME / "workspace" / "parametric"


def load():
    path = PARAMETRIC / "adapter.py"
    name = "_parametric_577d2db13443_" + hashlib.sha256(str(path).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def canonical_program() -> str:
    for line in (ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == "577d2db13443":
            return row["program_solution"]
    raise AssertionError("canonical task missing")


def witness_grid() -> list[list[int]]:
    """Dense 6-cell target versus a sparse 5-cell larger-bbox distractor."""
    grid = [[0] * 13 for _ in range(9)]
    # A visible long run proves interiors survive the endpoint pass.
    grid[0][4:9] = [6] * 5
    # Target cap component: a 2x3 rectangle encoded as pair+singleton rows.
    grid[2][1:4] = [2, 2, 3]
    grid[3][1:4] = [4, 5, 5]
    # Bbox distractor: a 3x3 L, five endpoint cells after capping.
    grid[5][8] = 6
    grid[6][8] = 7
    grid[7][8:11] = [9, 9, 2]
    return grid


def test_default_program_is_exact_canonical_bytes() -> None:
    module = load()
    default = {"finish": "caps_only"}
    source = canonical_program()
    assert module.SETTINGS[0] == default
    assert module.program(default) == source
    assert (PARAMETRIC / "canonical.rkt").read_text() == source
    assert hashlib.sha256(source.encode()).hexdigest() == (
        "a811558a15fb8476dc33ee271dc391ab53717b42ff625990feffa515ddda14c9"
    )


def test_sequential_transform_uses_post_cap_connectivity_not_bbox_area() -> None:
    module = load()
    grid = witness_grid()
    capped = module.transform(grid, {"finish": "caps_only"})
    highlighted = module.transform(grid, {"finish": "highlight_largest_cap_component"})
    bbox_rival = module.rival_output(
        grid, {"finish": "highlight_largest_cap_component"}, "largest_cap_bbox"
    )

    stats = module.cap_component_stats(grid)
    assert sorted(item["size"] for item in stats)[-2:] == [5, 6]
    assert max(stats, key=lambda item: item["size"])["bbox_area"] == 6
    assert max(stats, key=lambda item: item["bbox_area"])["bbox_area"] == 9
    assert highlighted != capped
    assert bbox_rival != highlighted
    assert sum(value == 8 for row in highlighted for value in row) == 6
    assert sum(value == 8 for row in bbox_rival for value in row) == 5
    assert highlighted[0][4] == highlighted[0][8] == 1
    assert highlighted[0][5:8] == [6, 6, 6]


def test_racket_programs_match_python_on_witness_and_large_query() -> None:
    module = load()
    sys.path[:0] = [str(ROOT / "src"), str(ROOT / "shared" / "runtime")]
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    def apply(bridge, program, grid):
        literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
        return bridge.eval_text(f"({wrap_rule(program)} {literal})")

    large = next(
        pair["input"]
        for pair in module.generate(
            17, {"finish": "highlight_largest_cap_component"}, 2, 4
        )["test"]
        if (len(pair["input"]), len(pair["input"][0])) == (30, 30)
    )
    bridge = RacketBridge(timeout=30)
    try:
        for grid in (witness_grid(), large):
            for setting in module.SETTINGS:
                assert apply(bridge, module.program(setting), grid) == module.transform(grid, setting)
            assert apply(bridge, module.rival_program(
                {"finish": "highlight_largest_cap_component"}, "largest_cap_bbox"
            ), grid) == module.rival_output(
                grid, {"finish": "highlight_largest_cap_component"}, "largest_cap_bbox"
            )
    finally:
        bridge.shutdown()


@pytest.mark.parametrize("seed", [0, 1, 17, 97])
@pytest.mark.parametrize("demos", [2, 3, 6])
def test_episode_counts_labels_teaching_and_matched_inputs(seed: int, demos: int) -> None:
    module = load()
    episodes = [module.generate(seed, setting, demos, 4) for setting in module.SETTINGS]
    assert [[pair["input"] for pair in episode["train"] + episode["test"]]
            for episode in episodes][0] == [
        [pair["input"] for pair in episode["train"] + episode["test"]]
        for episode in episodes
    ][1]

    all_inputs = [pair["input"] for pair in episodes[0]["train"] + episodes[0]["test"]]
    serialized = [json.dumps(grid, separators=(",", ":")) for grid in all_inputs]
    assert len(serialized) == len(set(serialized))

    for setting, episode in zip(module.SETTINGS, episodes):
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == 4
        assert episode["program_solution"] == module.program(setting)
        assert all(pair["output"] == module.transform(pair["input"], setting)
                   for pair in episode["train"] + episode["test"])
        teaching = module.teaching_check(episode, setting)
        assert teaching["survivors"] == [setting]
        assert teaching["surviving_rivals"] == []
        assert all(module.rival_output(pair["input"], setting, "largest_cap_bbox")
                   != pair["output"] for pair in episode["train"] + episode["test"]
                   if setting["finish"] == "highlight_largest_cap_component")

    large = next(pair["input"] for pair in episodes[0]["test"]
                 if (len(pair["input"]), len(pair["input"][0])) == (30, 30))
    occupied = [(r, c) for r, row in enumerate(large) for c, value in enumerate(row) if value]
    assert len(occupied) >= 100
    assert min(r for r, _ in occupied) <= 2 and max(r for r, _ in occupied) >= 27
    assert min(c for _, c in occupied) <= 2 and max(c for _, c in occupied) >= 27
    assert {value for row in large for value in row if value} == {2, 3, 4, 5, 6, 7, 9}


def test_demo_and_query_prefixes_are_independent_and_setting_neutral() -> None:
    module = load()
    for seed in (0, 17):
        full = {json.dumps(setting, sort_keys=True): module.generate(seed, setting, 6, 4)
                for setting in module.SETTINGS}
        for setting in module.SETTINGS:
            key = json.dumps(setting, sort_keys=True)
            for demos in range(2, 7):
                for queries in range(1, 5):
                    episode = module.generate(seed, setting, demos, queries)
                    assert episode["train"] == full[key]["train"][:demos]
                    assert episode["test"] == full[key]["test"][:queries]
        first, second = (full[json.dumps(setting, sort_keys=True)] for setting in module.SETTINGS)
        assert [p["input"] for p in first["train"] + first["test"]] == [
            p["input"] for p in second["train"] + second["test"]
        ]


def test_query_size_order_is_not_a_private_setting_or_fixed_position_hint() -> None:
    module = load()
    orders = set()
    large_positions = set()
    for seed in range(12):
        per_setting = []
        for setting in module.SETTINGS:
            episode = module.generate(seed, setting, 2, 4)
            order = tuple((len(pair["input"]), len(pair["input"][0])) for pair in episode["test"])
            per_setting.append(order)
        assert per_setting[0] == per_setting[1]
        orders.add(per_setting[0])
        large_positions.add(per_setting[0].index((30, 30)))
    assert len(orders) > 1
    assert len(large_positions) > 1


def test_public_turn_reveals_one_query_without_private_or_future_fields() -> None:
    module = load()
    setting = {"finish": "highlight_largest_cap_component"}
    episode = module.generate(4, setting, 3, 4)
    for index in range(4):
        visible = module.public_turn(episode, index)
        assert visible["train"] == episode["train"]
        assert visible["test"] == [{"input": episode["test"][index]["input"]}]
        raw = json.dumps(visible, sort_keys=True)
        assert "program_solution" not in raw
        assert "highlight_largest" not in raw
        assert "settings" not in raw
        assert "seed" not in raw
        assert "query_count" not in raw


@pytest.mark.parametrize(
    "seed,setting,demos,queries",
    [
        (True, {"finish": "caps_only"}, 2, 4),
        (-1, {"finish": "caps_only"}, 2, 4),
        (0, {"finish": "unknown"}, 2, 4),
        (0, {"finish": "caps_only", "extra": 1}, 2, 4),
        (0, {"finish": "caps_only"}, 1, 4),
        (0, {"finish": "caps_only"}, 7, 4),
        (0, {"finish": "caps_only"}, 2, True),
        (0, {"finish": "caps_only"}, 2, 5),
    ],
)
def test_invalid_requests_fail_explicitly(seed, setting, demos, queries) -> None:
    with pytest.raises(ValueError):
        load().generate(seed, setting, demos, queries)


@pytest.mark.parametrize("grid", [[], [[]], [[True]], [[5.0]], [[-1]], [[10]], [[5], [0, 5]]])
def test_transform_rejects_malformed_or_coerced_grids(grid) -> None:
    module = load()
    with pytest.raises(ValueError):
        module.transform(grid, {"finish": "caps_only"})
