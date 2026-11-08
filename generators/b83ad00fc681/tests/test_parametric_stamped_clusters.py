from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest
from reviewer_support import find_root


HERE = find_root(__file__) / "generators" / "b83ad00fc681" / "workspace" / "parametric"
CANONICAL_SHA256 = "46157a601fce9d70e7669dc2c4ab64f6364540d8009bc32a99cb0bad6456c781"


def load_prototype():
    path = HERE / "prototype.py"
    spec = importlib.util.spec_from_file_location("_test_b83_parametric", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_program_contract_preserves_exact_canonical_bytes():
    p = load_prototype()
    canonical = p.program({"finish": "stamp_only"})
    assert hashlib.sha256(canonical.encode()).hexdigest() == CANONICAL_SHA256
    assert canonical == (HERE / "canonical.rkt").read_text(encoding="utf-8")
    assert p.program({"finish": "highlight_largest_stamped_cluster"}) != canonical


def test_all_demo_counts_generate_four_distinct_matched_queries():
    p = load_prototype()
    for demos in range(2, 7):
        left = p.generate(17, {"finish": "stamp_only"}, demos, 4)
        right = p.generate(17, {"finish": "highlight_largest_stamped_cluster"}, demos, 4)
        assert len(left["train"]) == len(right["train"]) == demos
        assert len(left["test"]) == len(right["test"]) == 4
        left_inputs = [pair["input"] for pair in left["train"] + left["test"]]
        right_inputs = [pair["input"] for pair in right["train"] + right["test"]]
        assert left_inputs == right_inputs
        assert len({json.dumps(grid) for grid in left_inputs}) == demos + 4
        assert all(a["output"] != b["output"] for a, b in zip(left["train"], right["train"], strict=True))
        assert [len(left["test"][-1]["input"]), len(left["test"][-1]["input"][0])] == [30, 30]


def test_prefixes_are_count_independent_and_returns_are_fresh():
    p = load_prototype()
    short = p.sample_inputs(97, 2, 1)
    long = p.sample_inputs(97, 6, 4)
    assert short["train"] == long["train"][:2]
    assert short["test"] == long["test"][:1]
    changed = deepcopy(short)
    changed["train"][0][0][0] = 8
    assert p.sample_inputs(97, 2, 1) != changed


def test_intermediate_has_unique_binary_winner_and_defeats_color_sensitive_proxy():
    p = load_prototype()
    for split in ("train", "test"):
        for grid in p.sample_inputs(0, 6, 4)[split]:
            info = p.intermediate(grid)
            sizes = sorted(info["cluster_sizes"], reverse=True)
            assert len(sizes) >= 3 and sizes[0] > sizes[1]
            correct = p.solve(grid, finish="highlight_largest_stamped_cluster")
            wrong = p.rival_solve(grid, "largest_same_color")
            assert correct != wrong


def test_public_turn_hides_answers_settings_program_and_future_queries():
    p = load_prototype()
    episode = p.generate(5, {"finish": "highlight_largest_stamped_cluster"}, 3, 4)
    visible = p.public_turn(episode, 2)
    assert len(visible["train"]) == 3
    assert visible["test"] == [{"input": episode["test"][2]["input"]}]
    payload = json.dumps(visible, sort_keys=True)
    assert "program_solution" not in payload
    assert "finish" not in payload
    assert episode["test"][3]["input"] != visible["test"][0]["input"]


@pytest.mark.parametrize(
    "call,error",
    [
        (lambda p: p.program({}), ValueError),
        (lambda p: p.program({"finish": "other"}), ValueError),
        (lambda p: p.sample_inputs(True, 3, 4), TypeError),
        (lambda p: p.sample_inputs(0, 1, 4), ValueError),
        (lambda p: p.sample_inputs(0, 3, 5), ValueError),
    ],
)
def test_invalid_contract_values_reject(call, error):
    p = load_prototype()
    with pytest.raises(error):
        call(p)


def test_two_demonstrations_eliminate_first_cluster_proxy_for_audit_seeds():
    p = load_prototype()
    settings = {"finish": "highlight_largest_stamped_cluster"}
    for seed in (0, 17, 97):
        episode = p.generate(seed, settings, 2, 4)
        check = p.teaching_check(episode, settings)
        assert check["survivors"] == ["highlight_largest_stamped_cluster"]
        assert check["harmful_survivors"] == []
