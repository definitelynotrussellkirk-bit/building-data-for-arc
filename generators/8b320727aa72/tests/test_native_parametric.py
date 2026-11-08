"""Native recovered-component contract; reference labels come from Racket."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import find_root, public_challenge_bytes, public_challenge_id

ROOT = find_root(__file__)
HOME = Path(__file__).resolve().parents[1]
ADAPTER = HOME / "workspace/parametric/adapter.py"


def load_adapter():
    assert ADAPTER.is_file(), "the native parametric adapter must exist"
    spec = importlib.util.spec_from_file_location("native_disagreement_adapter_test", ADAPTER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def tiled(consensus, erased, corrupt=0, copies=5, gap=1, sep=3, bg=8):
    size = len(consensus)
    side = copies * size + (copies - 1) * gap
    grid = [[sep] * side for _ in range(side)]
    for k in range(copies * copies):
        tr, tc = divmod(k, copies)
        for r in range(size):
            for c in range(size):
                grid[tr * (size + gap) + r][tc * (size + gap) + c] = (
                    bg if k == corrupt and (r, c) in erased else consensus[r][c]
                )
    return grid


CONSENSUS = [
    [2, 2, 2, 8, 4],
    [8, 8, 2, 8, 8],
    [8, 8, 2, 5, 8],
    [8, 8, 8, 2, 8],
    [2, 8, 6, 6, 8],
]
COMPONENT_OUTPUT = [
    [1, 1, 1, 8, 4],
    [8, 8, 1, 8, 8],
    [8, 8, 1, 5, 8],
    [8, 8, 8, 2, 8],
    [2, 8, 6, 6, 8],
]


def test_reconstruct_before_connectivity_and_keep_disconnected_distractors():
    adapter = load_adapter()
    grid = tiled(CONSENSUS, {(1, 2)})
    before = deepcopy(grid)
    expected_mark = deepcopy(CONSENSUS)
    expected_mark[1][2] = 1
    with RacketBridge() as bridge:
        outputs = {
            action: adapter.execute(adapter.program({"disagreement_action": action}), grid, bridge)
            for action in ("mark", "restore", "mark_component")
        }
    assert outputs == {"mark": expected_mark, "restore": CONSENSUS, "mark_component": COMPONENT_OUTPUT}
    assert grid == before


def test_exact_canonical_default():
    adapter = load_adapter()
    assert adapter.program({"disagreement_action": "mark"}) == adapter.legacy.canonical_program(root=ROOT)


@pytest.mark.parametrize("action", ["mark", "restore", "mark_component"])
@pytest.mark.parametrize("demos", [2, 3, 6])
def test_independent_counts_distinct_pairs_and_no_future_query_leak(action, demos):
    adapter = load_adapter()
    setting = {"disagreement_action": action}
    one = adapter.generate(17, setting, demos, 1)
    four = adapter.generate(17, setting, demos, 4)
    assert len(four["train"]) == demos and len(four["test"]) == 4
    assert one["train"] == four["train"]
    assert one["test"] == four["test"][:1]
    inputs = [json.dumps(p["input"]) for p in four["train"] + four["test"]]
    assert len(inputs) == len(set(inputs))
    first = {"train": four["train"], "test": four["test"][:1]}
    payload, identity = public_challenge_bytes(first), public_challenge_id(first)
    altered = deepcopy(four)
    altered["settings"] = {"disagreement_action": "private-other"}
    altered["seed"] = -999
    for pair in altered["test"]:
        pair["output"] = [[9]]
    for pair in altered["test"][1:]:
        pair["input"] = [[7]]
    later = {"train": altered["train"], "test": altered["test"][:1]}
    assert public_challenge_bytes(later) == payload
    assert public_challenge_id(later) == identity
    assert public_challenge_bytes({"train": one["train"], "test": one["test"]}) == payload
    assert all(set(p) == {"input"} for p in json.loads(payload)["test"])


@pytest.mark.parametrize("args", [
    (True, {"disagreement_action": "mark"}, 3, 4),
    (-1, {"disagreement_action": "mark"}, 3, 4),
    (0, {"disagreement_action": "mark"}, True, 4),
    (0, {"disagreement_action": "mark"}, 1, 4),
    (0, {"disagreement_action": "mark"}, 7, 4),
    (0, {"disagreement_action": "mark"}, 3, 0),
    (0, {"disagreement_action": "mark"}, 3, 5),
    (0, {"disagreement_action": "mark", "other": 1}, 3, 4),
    (0, {"disagreement_action": "unknown"}, 3, 4),
])
def test_invalid_requests_fail_before_sampling(args):
    adapter = load_adapter()
    with pytest.raises(ValueError):
        adapter.generate(*args)


def test_component_rule_uses_full_thirty_canvas_and_real_six_cell_tiles():
    adapter = load_adapter()
    episode = adapter.generate(17, {"disagreement_action": "mark_component"}, 2, 4)
    pair = episode["test"][3]
    assert len(pair["input"]) == len(pair["input"][0]) == 30
    assert len(pair["output"]) == len(pair["output"][0]) == 6
    info = adapter.analyze(pair["input"])
    assert len(info["tiles"]) == 16
    assert len(info["disagreements"]) >= 2
    bg = info["background"]
    assert sum(v != bg for row in info["consensus"] for v in row) >= 15
    assert all(any(info["consensus"][r][c] != bg for r, c in border) for border in (
        [(0, c) for c in range(6)], [(5, c) for c in range(6)],
        [(r, 0) for r in range(6)], [(r, 5) for r in range(6)],
    ))
    with RacketBridge() as bridge:
        assert adapter.execute(episode["program_solution"], pair["input"], bridge) == pair["output"]


def test_malformed_separator_or_copy_is_rejected_by_input_contract():
    adapter = load_adapter()
    grid = tiled(CONSENSUS, {(1, 2)})
    grid[5][0] = 4
    with pytest.raises(ValueError):
        adapter.analyze(grid)
    grid = tiled(CONSENSUS, {(1, 2)})
    grid[6][0] = 7
    with pytest.raises(ValueError):
        adapter.analyze(grid)
