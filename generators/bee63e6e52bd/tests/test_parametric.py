"""Prototype-only checks; these do not approve a production parametric API."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import random
import shutil
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
ADAPTER_PATH = ROOT / "generators" / TASK_ID / "workspace/parametric/adapter.py"
PROMOTION_PATH = ROOT / "generators" / TASK_ID / "workspace/parametric/promotion.json"


@lru_cache(maxsize=1)
def prototype():
    assert PROTO_PATH.is_file(), "the requested runnable parametric prototype is missing"
    spec = importlib.util.spec_from_file_location("bee63e6e52bd_parametric_prototype", PROTO_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@lru_cache(maxsize=1)
def adapter():
    assert ADAPTER_PATH.is_file(), "the native parametric adapter is missing"
    spec = importlib.util.spec_from_file_location("bee63e6e52bd_parametric_adapter", ADAPTER_PATH)
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
@pytest.mark.parametrize("side", ("left", "right", "top", "bottom"))
def test_python_claim_mirror_matches_hand_positions_and_protected_racket(
    runner, reach, side
):
    proto = prototype()
    grid = long_witness(side)
    expected = expected_long_witness(reach, side)
    assert proto.predict(grid, spout_reach=reach) == expected
    assert runner.apply(proto.program_source(reach), [grid])[0] == expected


@pytest.mark.parametrize("reach", ("full", 0, 2))
def test_episode_uses_one_rule_and_every_demo_refutes_each_declared_rival(runner, reach):
    proto = prototype()
    episode = proto.generate_episode(26023, spout_reach=reach, runner=runner)
    assert episode["parameters"] == {"spout_reach": reach}
    assert episode["program"] == proto.program_source(reach)
    assert episode["program_sha256"] == hashlib.sha256(episode["program"].encode()).hexdigest()
    assert len(episode["train"]) == 3 and len(episode["test"]) == 4
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
        assert rival["query_matches"] == [False, False, False, False]
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
    assert len(public_paths) == 3
    private = [json.loads(line) for line in (output / "private/episodes.jsonl").read_text().splitlines()]
    assert {row["parameters"]["spout_reach"] for row in private} == set(proto.ALLOWED_REACHES)
    assert {path.name for path in public_paths} == {proto.public_filename(row) for row in private}
    for index, episode in enumerate(private):
        path = output / episode["public_file"]
        public = json.loads(path.read_text())
        assert set(public) == {"train", "test"}
        assert len(public["train"]) == 3 and len(public["test"]) == 4
        assert all(set(pair) == {"input", "output"} for pair in public["train"])
        assert all(set(pair) == {"input"} for pair in public["test"])
        assert public["train"] == private[index]["train"]
        assert public["test"] == [{"input": pair["input"]} for pair in private[index]["test"]]
        source = output / private[index]["program_file"]
        assert source.read_text() == private[index]["program"]
        assert hashlib.sha256(source.read_bytes()).hexdigest() == private[index]["program_sha256"]
    with pytest.raises(FileExistsError):
        proto.write_evidence(output, base_seed=901, per_setting=1, runner=runner)


@pytest.mark.parametrize("n_train", (2, 6))
def test_demo_count_boundaries_keep_the_four_query_stream_fixed(runner, n_train):
    proto = prototype()
    baseline = proto.generate_episode(731, spout_reach=2, n_train=3, n_test=4, runner=runner)
    episode = proto.generate_episode(731, spout_reach=2, n_train=n_train, n_test=4, runner=runner)
    assert len(episode["train"]) == n_train
    assert len(episode["test"]) == 4
    assert [pair["input"] for pair in episode["test"]] == [
        pair["input"] for pair in baseline["test"]
    ]
    assert len({json.dumps(pair["input"]) for pair in episode["train"] + episode["test"]}) == n_train + 4


def test_query_count_prefix_and_first_turn_match_single_query_use(runner):
    proto = prototype()
    one = proto.generate_episode(991, spout_reach="full", n_train=3, n_test=1, runner=runner)
    four = proto.generate_episode(991, spout_reach="full", n_train=3, n_test=4, runner=runner)
    assert [pair["input"] for pair in four["test"][:1]] == [pair["input"] for pair in one["test"]]
    assert proto.first_turn(four) == proto.public_challenge(one)
    assert len(proto.first_turn(four)["test"]) == 1
    assert set(proto.first_turn(four)["test"][0]) == {"input"}


@pytest.mark.parametrize(
    "height,width,index",
    ((12, 12, 0), (12, 30, 1), (30, 12, 2), (30, 30, 3)),
)
def test_exact_size_draws_are_lawful_spread_and_have_four_step_rays(height, width, index, runner):
    proto = prototype()
    grid = proto.input_draw(41, index, height=height, width=width, stream="boundary")
    assert (len(grid), len(grid[0])) == (height, width)
    generator, _, _ = load_selected_generator(TASK_ID, root=ROOT)
    assert generator.self_check(grid) == []
    assert min(proto.ray_runways(grid)) >= 4
    facts = proto._reference_probe().shape_facts(grid)
    r0, c0, r1, c1 = facts["bbox"]
    bbox_h, bbox_w = r1 - r0 + 1, c1 - c0 + 1
    assert max(bbox_h / height, bbox_w / width) >= 0.5
    if (height, width) == (30, 30):
        assert bbox_h >= 20 and bbox_w >= 20
    output = runner.apply(proto.program_source("full"), [grid])[0]
    assert sum(cell == 4 for row in output for cell in row) >= (height * width) // 8


@pytest.mark.parametrize(
    "field,value",
    (
        ("seed", -1), ("seed", 2**63), ("seed", True),
        ("n_train", 1), ("n_train", 7), ("n_train", True), ("n_train", 3.0),
        ("n_test", 0), ("n_test", 5), ("n_test", False), ("n_test", 4.0),
        ("spout_reach", 1), ("spout_reach", True),
    ),
)
def test_invalid_episode_requests_fail_before_racket_start(field, value, monkeypatch):
    proto = prototype()
    kwargs = {"seed": 0, "spout_reach": "full", "n_train": 3, "n_test": 4}
    kwargs[field] = value

    class ForbiddenRunner:
        def __init__(self):
            raise AssertionError("invalid request reached Racket startup")

    monkeypatch.setattr(proto, "RacketRunner", ForbiddenRunner)
    with pytest.raises(ValueError):
        proto.generate_episode(**kwargs)


def test_native_adapter_and_promotion_contract(monkeypatch):
    proto = prototype()
    native = adapter()
    promotion = json.loads(PROMOTION_PATH.read_text())
    assert promotion == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/bee63e6e52bd/workspace/parametric/adapter.py",
        "parameters": {"spout_reach": ["full", 0, 2]},
        "default": {"spout_reach": "full"},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "resources": [
            "generators/bee63e6e52bd/workspace/parametric/prototype.py",
            "generators/bee63e6e52bd/workspace/parametric/canonical-full.rkt",
        ],
    }
    assert native.program({"spout_reach": "full"}) == canonical_source()
    assert native.program({"spout_reach": 2}) == proto.program_source(2)

    class ForbiddenRunner:
        def __init__(self):
            raise AssertionError("native candidate generation must not start Racket")

    monkeypatch.setattr(native._prototype, "RacketRunner", ForbiddenRunner)
    generated = native.generate(19, {"spout_reach": 0}, 2, 4)
    assert generated["program_solution"] == proto.program_source(0)
    assert (len(generated["train"]), len(generated["test"])) == (2, 4)
    with pytest.raises(ValueError):
        native.program({"spout_reach": False})
    with pytest.raises(ValueError):
        native.program({"spout_reach": "full", "extra": 1})


def test_current_export_verifier_rejects_private_answer_and_inventory_tampering(runner, tmp_path):
    proto = prototype()
    clean = tmp_path / "clean"
    report = proto.write_evidence(clean, base_seed=712, per_setting=1, runner=runner)
    assert report["status"] == "pass"
    verified = proto.verify_evidence(clean, runner=runner)
    assert verified["status"] == "pass"
    assert verified["episodes"] == 3
    assert verified["queries"] == 12

    answer_tamper = tmp_path / "answer-tamper"
    shutil.copytree(clean, answer_tamper)
    private = answer_tamper / "private/episodes.jsonl"
    episodes = [json.loads(line) for line in private.read_text().splitlines()]
    episodes[0]["test"][0]["output"][0][0] = (episodes[0]["test"][0]["output"][0][0] + 1) % 10
    private.write_text("".join(json.dumps(row, separators=(",", ":")) + "\n" for row in episodes))
    with pytest.raises(ValueError):
        proto.verify_evidence(answer_tamper, runner=runner)

    inventory_tamper = tmp_path / "inventory-tamper"
    shutil.copytree(clean, inventory_tamper)
    (inventory_tamper / "unexpected.txt").write_text("not declared")
    with pytest.raises(ValueError, match="inventory"):
        proto.verify_evidence(inventory_tamper, runner=runner)
