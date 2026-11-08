"""Focused regression tests for the bee63e6e52bd frame-pour generator."""
from __future__ import annotations

import ast
import copy
import importlib.util
import hashlib
import itertools
import json
import random
import sys
from pathlib import Path

import pytest

TASK_ID = "bee63e6e52bd"
HERE = Path(__file__).resolve()
for candidate in (HERE.parent, *HERE.parents):
    for support in (candidate / "reviewer_support.py", candidate / "shared" / "runtime" / "reviewer_support.py"):
        if support.is_file():
            if str(support.parent) not in sys.path:
                sys.path.insert(0, str(support.parent))
            break
    else:
        continue
    break
else:  # pragma: no cover - collection error is intentionally explicit
    raise ImportError("cannot locate portable reviewer_support.py")

from reviewer_support import find_root  # noqa: E402

ROOT = find_root(__file__)


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEN_PATH = ROOT / "generators" / TASK_ID / "generator.py"
GEN = _load(GEN_PATH, f"review_generator_{TASK_ID}")
ORACLE = _load(
    ROOT / "generators" / TASK_ID / "workspace" / "reference_probe.py",
    f"review_oracle_{TASK_ID}",
)
CANONICAL = ORACLE.labeled_canonical_pairs()
BANDS = (None, "easy", "medium", "hard")
PROFILES = ("6x6", "7x7", "9x9", "10x10")
SIDES = ("left", "right", "top", "bottom")
ARM_PROFILES = ("canonical_2_2", "short_1_1", "asym_1_3", "asym_3_1")
COLORS = (1, 2, 3, 5, 6, 7, 8, 9)


def _pair(seed: int, sample_index: int, band):
    grid = GEN.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": ORACLE.intended_output(grid)}


def test_rule_pin_axis_contract_and_all_canonical_pairs():
    assert GEN.RULE_HASH == "eedba8f59365"
    assert GEN.VERSION == "3.1.0"
    assert set(GEN.AXES) == {"scene_profile", "open_side", "arm_profile", "color"}
    assert GEN.EXAMPLES_NEEDED == 3
    assert GEN.MIN_STRICT_FRAC == 1.0
    assert len(CANONICAL) == 4
    for pair in CANONICAL:
        before = copy.deepcopy(pair)
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert ORACLE.shape_facts(pair["input"])["arm_before"] == 2
        assert ORACLE.shape_facts(pair["input"])["arm_after"] == 2
        assert ORACLE.intended_output(pair["input"]) == pair["output"]
        assert GEN._apply_intended(pair["input"]) == pair["output"]
        assert GEN.CANONICAL_SHORTCUTS["fixed_two_arms"](pair["input"]) == pair["output"]
        assert pair == before


def test_axes_are_static_literals_for_review_tooling():
    tree = ast.parse(GEN_PATH.read_text(encoding="utf-8"))
    assignment = next(
        node for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "AXES" for target in node.targets)
    )
    literal = ast.literal_eval(assignment.value)
    assert set(literal) == {"scene_profile", "open_side", "arm_profile", "color"}


@pytest.mark.parametrize("band", BANDS)
def test_every_exact_override_combination_is_observable_and_valid(band):
    case = 0
    # Full structural product, two representative colors, then all colors on a
    # fixed geometry.  This keeps the test fast while exercising every value.
    for profile, side, arms, color in itertools.product(PROFILES, SIDES, ARM_PROFILES, (1, 9)):
        requested = {
            "scene_profile": profile,
            "open_side": side,
            "arm_profile": arms,
            "color": color,
        }
        grid = GEN.generate(9100 + case, case, difficulty=band, **requested)
        assert GEN.self_check(grid, difficulty=band, meta={"overrides": requested}) == []
        assert GEN.strict_canonical_like(grid) == []
        assert GEN.observe_overrides(grid) == requested
        assert ORACLE.shape_facts(grid)["open_side"] == side
        assert ORACLE.intended_output(grid) == GEN._apply_intended(grid)
        case += 1
    for color in COLORS:
        requested = {
            "scene_profile": "7x7",
            "open_side": "right",
            "arm_profile": "asym_1_3",
            "color": color,
        }
        grid = GEN.generate(9800 + color, color, difficulty=band, **requested)
        assert GEN.observe_overrides(grid) == requested


@pytest.mark.parametrize(
    "kwargs,exception,match",
    [
        ({"unknown": 1}, ValueError, "unknown override"),
        ({"scene_profile": 6}, TypeError, "scene_profile"),
        ({"scene_profile": "8x8"}, ValueError, "scene_profile"),
        ({"open_side": 1}, TypeError, "open_side"),
        ({"open_side": "diagonal"}, ValueError, "open_side"),
        ({"arm_profile": 1}, TypeError, "arm_profile"),
        ({"arm_profile": "2x3"}, ValueError, "arm_profile"),
        ({"color": True}, TypeError, "color"),
        ({"color": 4}, ValueError, "color"),
        ({"difficulty": "extreme"}, ValueError, "difficulty"),
    ],
)
def test_invalid_generation_requests_fail_loudly(kwargs, exception, match):
    with pytest.raises(exception, match=match):
        GEN.generate(1, 0, **kwargs)


def test_schedule_is_period_four_and_every_three_demo_window_breaks_shortcut():
    assert tuple(GEN.SCHEDULE_PROFILES) == ARM_PROFILES
    assert GEN.LESSON_SCHEDULE_PERIOD == 4
    for band in BANDS:
        for seed in range(4):
            observed = [GEN.schedule_profile(seed, index, difficulty=band) for index in range(12)]
            assert observed == [ARM_PROFILES[index % 4] for index in range(12)]
            for start in range(8):
                demos = [_pair(seed, index, band) for index in range(start, start + 3)]
                query = _pair(seed, start + 3, band)
                assert GEN.lesson_identifiable(demos, query) == []
                for name, rival in GEN.LESSON_COMPETITORS.items():
                    assert any(rival(pair["input"]) != pair["output"] for pair in demos), (
                        band,
                        seed,
                        start,
                        name,
                    )


def test_all_four_query_rotations_leave_a_shortcut_refuting_demo():
    for band in BANDS:
        for start in range(8):
            pairs = [_pair(700 + start, index, band) for index in range(start, start + 4)]
            for held_out in range(4):
                demos = [pair for index, pair in enumerate(pairs) if index != held_out]
                query = pairs[held_out]
                assert GEN.lesson_identifiable(demos, query) == []
                for rival in GEN.LESSON_COMPETITORS.values():
                    assert any(rival(pair["input"]) != pair["output"] for pair in demos)


def test_declared_shortcut_is_real_and_exact_witness_refutes_it():
    assert set(GEN.CANONICAL_SHORTCUTS) == {"fixed_two_arms"}
    assert set(GEN.SEMANTIC_RIVALS) == {"fixed_two_arms", "no_diagonal_spouts"}
    assert set(GEN.LESSON_COMPETITORS) == {"fixed_two_arms", "no_diagonal_spouts"}
    assert GEN.WITNESS_RIVALS == {
        "noncanonical_arm_lengths": ["fixed_two_arms"],
        "visible_diagonal_spouts": ["no_diagonal_spouts"],
    }
    rival = GEN.CANONICAL_SHORTCUTS["fixed_two_arms"]
    for pair in CANONICAL:
        assert rival(pair["input"]) == pair["output"]
    witness = ORACLE.witness_input()
    before = copy.deepcopy(witness)
    assert GEN.self_check(witness) == []
    assert GEN.SEMANTIC_WITNESSES["noncanonical_arm_lengths"](witness) is True
    assert GEN._apply_intended(witness) == ORACLE.intended_output(witness)
    assert rival(witness) == ORACLE.fixed_two_arms(witness)
    assert rival(witness) != GEN._apply_intended(witness)
    assert witness == before


def test_default_distribution_is_valid_deterministic_fresh_and_broad():
    random.seed(271828)
    state = random.getstate()
    for band in BANDS:
        seen = set()
        counts = {"scene_profile": set(), "open_side": set(), "arm_profile": set(), "color": set()}
        for index in range(160):
            seed = 100_000 + index
            grid = GEN.generate(seed, index, difficulty=band)
            assert random.getstate() == state
            again = GEN.generate(seed, index, difficulty=band)
            assert grid == again
            assert grid is not again
            assert all(a is not b for a, b in zip(grid, again))
            assert GEN.self_check(grid, difficulty=band) == []
            assert GEN.strict_canonical_like(grid) == []
            assert ORACLE.intended_output(grid) == GEN._apply_intended(grid)
            assert GEN.CANONICAL_SHORTCUTS["fixed_two_arms"](grid) != GEN._apply_intended(grid) or (
                GEN.observe_overrides(grid)["arm_profile"] == "canonical_2_2"
            )
            observed = GEN.observe_overrides(grid)
            for axis in counts:
                counts[axis].add(observed[axis])
            seen.add(repr(grid))
        assert len(seen) >= 100
        assert counts["scene_profile"] == set(PROFILES)
        assert counts["open_side"] == set(SIDES)
        assert counts["arm_profile"] == set(ARM_PROFILES)
        assert counts["color"] == set(COLORS)


def test_self_check_returns_diagnostics_without_mutation_or_exceptions():
    valid = GEN.generate(4, 1)
    cases = {
        "empty": [],
        "ragged": [[0, 0], [0]],
        "bool": [[False, 0], [0, 0]],
        "out_of_range": [[10]],
        "blank": [[0] * 6 for _ in range(6)],
        "fill_color_input": [[4] * 3 for _ in range(3)],
        "closed": [[1, 1, 1], [1, 0, 1], [1, 1, 1]],
        "interior_noise": copy.deepcopy(valid),
        "mouth_on_border": copy.deepcopy(valid),
    }
    facts = ORACLE.shape_facts(valid)
    r0, c0, r1, c1 = facts["bbox"]
    cases["interior_noise"][(r0 + r1) // 2][(c0 + c1) // 2] = facts["color"]
    # Move the shape one cell toward its mouth boundary by cropping away the
    # guaranteed outward margin.  This remains rectangular but must be rejected.
    side = facts["open_side"]
    if side == "left":
        cases["mouth_on_border"] = [row[c0:] for row in valid]
    elif side == "right":
        cases["mouth_on_border"] = [row[: c1 + 1] for row in valid]
    elif side == "top":
        cases["mouth_on_border"] = valid[r0:]
    else:
        cases["mouth_on_border"] = valid[: r1 + 1]
    for name, grid in cases.items():
        before = copy.deepcopy(grid)
        result = GEN.self_check(grid)
        assert isinstance(result, list) and result, name
        assert all(isinstance(reason, str) for reason in result), name
        assert grid == before, name


def test_mirrors_and_semantic_hooks_are_input_pure():
    for index in range(16):
        grid = GEN.generate(123, index)
        before = copy.deepcopy(grid)
        GEN._apply_intended(grid)
        for solve in GEN.SEMANTIC_RIVALS.values():
            solve(grid)
        for witness in GEN.SEMANTIC_WITNESSES.values():
            witness(grid)
        GEN.observe_overrides(grid)
        GEN.strict_canonical_like(grid)
        assert grid == before

def test_reference_probe_and_retained_counterexample_are_replayable():
    report = ORACLE.audit(GEN, count=20)
    assert report["status"] == "pass"
    assert report["canonical"]["oracle_matches"] == report["canonical"]["pairs"] == 4
    assert report["canonical"]["fixed_two_matches"] == 4
    for values in report["bands"].values():
        assert values["draws"] == values["valid"] == values["deterministic"] == 20
        assert values["canonical_arm_draws"] == 5
        assert values["counterexample_draws"] == values["shortcut_disagreement"] == 15

    record_path = ROOT / "generators" / TASK_ID / "counterexamples" / "fixed-two-arms.json"
    record = json.loads(record_path.read_text(encoding="utf-8"))
    # This immutable witness belongs to v3.0.0. Its original provenance must
    # not be relabelled with new bytes, nor must a versioned sampler be forced
    # to reproduce an old seed. Replay the retained pixels against today's
    # validator, mirror, rival and unchanged rule authority.
    assert record["generator_sha256"] == "9ff3ab296a273b534f701a0f46591266a73e8003827f76765588cc14c14ebcb1"
    assert record["rule_hash"] == GEN.RULE_HASH
    source = record["source"]
    grid = record["input"]
    assert GEN.self_check(grid, difficulty=source["difficulty"], meta={"overrides": source["overrides"]}) == []
    assert GEN.observe_overrides(grid) == record["observed_axes"]
    assert GEN._apply_intended(grid) == record["racket_output"]
    assert GEN.CANONICAL_SHORTCUTS[record["rival_name"]](grid) == record["rival_output"]
    assert record["rival_output"] != record["racket_output"]

