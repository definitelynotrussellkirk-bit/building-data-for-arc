"""Prototype-only checks; these do not approve a production parametric API."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import random
import sys
from functools import lru_cache
from pathlib import Path

import pytest

TASK_ID = "bee63e6e52bd"
HERE = Path(__file__).resolve()
for candidate in (HERE.parent, *HERE.parents):
    for support in (candidate / "reviewer_support.py", candidate / "shared/runtime/reviewer_support.py"):
        if support.is_file():
            if str(support.parent) not in sys.path:
                sys.path.insert(0, str(support.parent))
            break
    else:
        continue
    break
else:
    raise ImportError("cannot locate portable reviewer_support.py")

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

ROOT = find_root(__file__)
PROTO_PATH = ROOT / "generators" / TASK_ID / "workspace/parametric/prototype.py"


@lru_cache(maxsize=1)
def prototype():
    assert PROTO_PATH.is_file(), "the requested runnable parametric prototype is missing"
    spec = importlib.util.spec_from_file_location("bee63e6e52bd_parametric_prototype", PROTO_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_source():
    rows = [json.loads(line) for line in canonical_path(ROOT).read_text().splitlines() if line.strip()]
    programs = {row["program_solution"] for row in rows if row.get("task_id") == TASK_ID}
    assert len(programs) == 1
    return programs.pop()


@pytest.fixture(scope="module")
def runner():
    with prototype().RacketRunner() as instance:
        yield instance


def rotate(grid, side):
    if side == "left":
        return [row[:] for row in grid]
    if side == "right":
        return [row[::-1] for row in grid]
    transposed = [list(row) for row in zip(*grid)]
    if side == "top":
        return transposed
    assert side == "bottom"
    return transposed[::-1]


def long_witness(side="left"):
    """Independent asymmetric frame: top arm 1, bottom arm 3, gap rows 5..7."""
    grid = [[0] * 16 for _ in range(15)]
    for c in range(6, 13):
        grid[4][c] = grid[10][c] = 8
    for r in range(4, 11):
        grid[r][12] = 8
    for r in (4, 8, 9, 10):
        grid[r][6] = 8
    return rotate(grid, side)


def expected_long_witness(reach, side="left"):
    """Hand-positioned expected cells, independent of prototype geometry code."""
    out = long_witness()
    # The canonical flood is restricted to levels between the actual tips.
    for r in (5, 6, 7):
        for c in range(12):
            out[r][c] = 4
    out[4][5] = out[8][5] = 4
    for c in range(7, 12):
        out[8][c] = 4
    top_ray = [(3, 4), (2, 3), (1, 2), (0, 1)]
    bottom_ray = [(9, 4), (10, 3), (11, 2), (12, 1), (13, 0)]
    for ray in (top_ray, bottom_ray):
        for r, c in ray if reach == "full" else ray[:reach]:
            out[r][c] = 4
    return rotate(out, side)


def test_default_program_matches_selected_canonical_authority():
    proto = prototype()
    assert proto.ALLOWED_REACHES == ("full", 0, 2)
    assert proto.DEFAULT_REACH == "full"
    assert proto.program_source() == canonical_source()
    assert hashlib.sha256(proto.program_source().encode()).hexdigest() == (
        "8a119729a8cfa7e439377928fd01a88ca9dd9ba1d2b570f5a82bba7839c2fe0c"
    )


def test_default_executes_all_four_canonical_labels(runner):
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert len(pairs) == 4
    assert runner.apply(prototype().program_source(), [pair["input"] for pair in pairs]) == [
        pair["output"] for pair in pairs
    ]


@pytest.mark.parametrize("side", ("left", "right", "top", "bottom"))
def test_each_reach_executes_distinct_long_ray_geometry_with_actual_tips(runner, side):
    proto = prototype()
    generator, _, _ = load_selected_generator(TASK_ID, root=ROOT)
    grid = long_witness(side)
    assert generator.self_check(grid) == []
    assert generator.strict_canonical_like(grid)
    before = json.dumps(grid)
    outputs = {}
    for reach in proto.ALLOWED_REACHES:
        output = runner.apply(proto.program_source(reach), [grid])[0]
        assert output == expected_long_witness(reach, side)
        outputs[str(reach)] = output
    assert len({json.dumps(output) for output in outputs.values()}) == 3
    assert json.dumps(grid) == before


@pytest.mark.parametrize("reach", ("full", 0, 2))
def test_episode_uses_one_rule_and_every_demo_refutes_each_declared_rival(runner, reach):
    proto = prototype()
    episode = proto.generate_episode(26023, spout_reach=reach, runner=runner)
    assert episode["parameters"] == {"spout_reach": reach}
    assert episode["program"] == proto.program_source(reach)
    assert episode["program_sha256"] == hashlib.sha256(episode["program"].encode()).hexdigest()
    assert len(episode["train"]) == 3 and len(episode["test"]) == 1
    pairs = episode["train"] + episode["test"]
    assert runner.apply(episode["program"], [pair["input"] for pair in pairs]) == [
        pair["output"] for pair in pairs
    ]
    generator, _, _ = load_selected_generator(TASK_ID, root=ROOT)
    for pair in pairs:
        assert generator.self_check(pair["input"]) == []
        assert min(proto.ray_runways(pair["input"])) >= 4
    checks = proto.assess_identifiability(episode, runner=runner)
    assert checks["status"] == "pass"
    assert len(checks["rivals"]) == 2
    for rival in checks["rivals"]:
        assert rival["demo_matches"] == [False, False, False]
        assert rival["query_matches"] == [False]
        assert rival["demos_distinguish"] is True


def test_seed_choice_is_episode_scoped_deterministic_and_input_sampling_independent(runner):
    proto = prototype()
    random.seed(271828)
    before = random.getstate()
    first = proto.generate_episode(4444, runner=runner)
    second = proto.generate_episode(4444, runner=runner)
    assert first == second
    assert random.getstate() == before
    assert first["parameters"]["spout_reach"] == proto.choose_reach(4444)
    assert set(proto.choose_reach(seed) for seed in range(24)) == set(proto.ALLOWED_REACHES)
    alternatives = [proto.generate_episode(4444, spout_reach=reach, runner=runner) for reach in proto.ALLOWED_REACHES]
    assert len({json.dumps([pair["input"] for pair in e["train"] + e["test"]]) for e in alternatives}) == 1
    assert len({json.dumps([pair["output"] for pair in e["train"] + e["test"]]) for e in alternatives}) == 3


@pytest.mark.parametrize("invalid", (None, True, False, -1, 1, 3, "2", "unbounded"))
def test_unsupported_rule_values_fail_loudly(invalid):
    with pytest.raises((TypeError, ValueError), match="spout_reach"):
        prototype().program_source(invalid)


def test_export_keeps_query_labels_rule_and_parameters_private(runner, tmp_path):
    proto = prototype()
    output = tmp_path / "evidence"
    report = proto.write_evidence(output, base_seed=901, per_setting=1, runner=runner)
    assert report["status"] == "pass"
    assert report["episodes"] == 3
    assert report["canonical_parity"]["pairs"] == report["canonical_parity"]["matches"] == 4
    public_paths = sorted((output / "public").glob("*.json"))
    assert [path.name for path in public_paths] == [f"episode-{index:03d}.json" for index in range(3)]
    private = [json.loads(line) for line in (output / "private/episodes.jsonl").read_text().splitlines()]
    assert {row["parameters"]["spout_reach"] for row in private} == set(proto.ALLOWED_REACHES)
    for index, path in enumerate(public_paths):
        public = json.loads(path.read_text())
        assert set(public) == {"train", "test"}
        assert len(public["train"]) == 3 and len(public["test"]) == 1
        assert all(set(pair) == {"input", "output"} for pair in public["train"])
        assert all(set(pair) == {"input"} for pair in public["test"])
        assert public["train"] == private[index]["train"]
        assert public["test"] == [{"input": pair["input"]} for pair in private[index]["test"]]
        source = output / private[index]["program_file"]
        assert source.read_text() == private[index]["program"]
        assert hashlib.sha256(source.read_bytes()).hexdigest() == private[index]["program_sha256"]
    with pytest.raises(FileExistsError):
        proto.write_evidence(output, base_seed=901, per_setting=1, runner=runner)
