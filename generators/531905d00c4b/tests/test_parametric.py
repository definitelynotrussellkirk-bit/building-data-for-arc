"""Focused regressions for neighbor-mass reflection; no production repair."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]
PARAMETRIC = HOME / "workspace/parametric"
POLICIES = ("canonical", "larger_left", "larger_right")


def load_adapter():
    path = PARAMETRIC / "adapter.py"
    assert path.is_file(), "MAIN needs the native parametric adapter"
    spec = importlib.util.spec_from_file_location("test_531905d00c4b_adapter", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def adapter():
    return load_adapter()


def fixture_grid():
    # 8 has 5 occupied cells, 2 has 9, and 5 is a narrow shifted L (3 cells).
    # Numeric color ordering disagrees with component-mass ordering.
    return [
        [8, 0, 0, 0, 0, 0, 0, 2, 2, 2],
        [8, 0, 0, 0, 5, 0, 0, 2, 2, 2],
        [8, 8, 8, 0, 5, 5, 0, 2, 2, 2],
        [0] * 10,
        [0] * 10,
        [0, 8, 5, 2, 0, 0, 0, 0, 0, 0],
        [0, 2, 5, 8, 0, 0, 0, 0, 0, 0],
    ]


def tile(output, row, col, height=3, width=3):
    return [r[col * width:(col + 1) * width]
            for r in output[row * height:(row + 1) * height]]


def test_native_adapter_and_exact_canonical_authority():
    adapter = load_adapter()
    rows = [json.loads(line) for line in
            (ROOT / "shared/data/canonical/puzzles.jsonl").read_text().splitlines()]
    canonical = next(row for row in rows if row["task_id"] == "531905d00c4b")
    assert adapter.program({"reflection_policy": "canonical"}) == canonical["program_solution"]
    tests = canonical["test"] if isinstance(canonical["test"], list) else [canonical["test"]]
    for pair in canonical["train"] + tests:
        assert adapter.prototype.label(pair["input"], {"reflection_policy": "canonical"}) == pair["output"]


def test_promotion_resource_closure_is_natively_admissible():
    from arcpuzzles.parametric_manifest import _contract
    contract, sources = _contract(ROOT, HOME)
    assert contract["default"] == {"reflection_policy": "canonical"}
    assert all(path.is_file() for path in sources)


def test_same_token_changes_orientation_with_resolved_neighbor_mass(adapter):
    g = fixture_grid()
    left = adapter.prototype.label(g, {"reflection_policy": "larger_left"})
    right = adapter.prototype.label(g, {"reflection_policy": "larger_right"})
    original = [[5, 0, 0], [5, 5, 0], [0, 0, 0]]
    reflected_crop = [[0, 5, 0], [5, 5, 0], [0, 0, 0]]
    assert tile(left, 0, 1) == original
    assert tile(left, 1, 1) == reflected_crop
    assert tile(right, 0, 1) == reflected_crop
    assert tile(right, 1, 1) == original
    assert len(left) == 6 and len(left[0]) == 9


def test_ties_keep_orientation_and_missing_neighbor_has_zero_mass(adapter):
    g = fixture_grid()
    g[-1] = [0, 8, 5, 8, 0, 0, 0, 0, 0, 0]
    for policy in POLICIES:
        out = adapter.prototype.label(g, {"reflection_policy": policy})
        assert tile(out, 1, 1) == [[5, 0, 0], [5, 5, 0], [0, 0, 0]]
    out = adapter.prototype.label(g, {"reflection_policy": "larger_right"})
    assert tile(out, 0, 0) == [[0, 0, 8], [0, 0, 8], [8, 8, 8]]


@pytest.mark.parametrize("demos", [2, 3, 6])
@pytest.mark.parametrize("queries", [1, 4])
def test_count_boundaries_distinct_inputs_and_matched_rule_settings(adapter, demos, queries):
    all_inputs = []
    for policy in POLICIES:
        episode = adapter.generate(17, {"reflection_policy": policy}, demos, queries)
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == queries
        inputs = [pair["input"] for pair in episode["train"] + episode["test"]]
        assert len({json.dumps(g) for g in inputs}) == demos + queries
        assert episode["program_solution"] == adapter.program({"reflection_policy": policy})
        for split in ("train", "test"):
            for pair in episode[split]:
                for g in (pair["input"], pair["output"]):
                    assert 1 <= len(g) <= 30 and 1 <= len(g[0]) <= 30
                    assert all(len(row) == len(g[0]) for row in g)
                    assert all(type(v) is int and 0 <= v <= 9 for row in g for v in row)
        all_inputs.append(inputs)
    assert all_inputs[0] == all_inputs[1] == all_inputs[2]


def test_two_demonstrations_identify_each_declared_setting(adapter):
    for seed in (0, 17, 91):
        for policy in POLICIES:
            chosen = {"reflection_policy": policy}
            episode = adapter.generate(seed, chosen, 2, 4)
            survivors = [other for other in POLICIES if all(
                adapter.prototype.label(pair["input"], {"reflection_policy": other}) == pair["output"]
                for pair in episode["train"])]
            assert survivors == [policy]


def test_teaching_includes_distinct_color_equal_mass_ties(adapter):
    for seed in (0, 17, 91):
        e = adapter.generate(seed, {"reflection_policy": "larger_left"}, 2, 4)
        parts = adapter.prototype.parse(e["train"][1]["input"])
        witnessed = False
        for row in parts["index"]:
            for c in range(1, len(row) - 1):
                a, b = row[c - 1], row[c + 1]
                crop = parts["crops"][row[c]]
                if (a != b and parts["masses"][a] == parts["masses"][b]
                        and crop != [line[::-1] for line in crop]):
                    witnessed = True
        assert witnessed, "strict ties must be taught across distinct legend colors"


def test_teaching_breaks_both_numeric_color_order_correlations(adapter):
    for seed in (0, 17, 91):
        e = adapter.generate(seed, {"reflection_policy": "larger_left"}, 2, 4)
        signs = set()
        for pair in e["train"]:
            parts = adapter.prototype.parse(pair["input"])
            low, target, high = parts["index"][0][:3]
            assert parts["masses"][low] < parts["masses"][high]
            signs.add(low < high)
        assert signs == {False, True}, "both numerical color-order shortcuts need counterexamples"


def test_prototype_geometry_varies_beyond_colors_and_reflections(adapter):
    shapes = set()
    for seed in range(12):
        e = adapter.generate(seed, {"reflection_policy": "canonical"}, 2, 1)
        parts = adapter.prototype.parse(e["train"][0]["input"])
        token = parts["index"][0][1]
        mask = tuple(tuple(int(v != 0) for v in row) for row in parts["crops"][token])
        variants = [mask, mask[::-1], tuple(row[::-1] for row in mask),
                    tuple(row[::-1] for row in mask[::-1])]
        shapes.add(min(variants))
    assert len(shapes) >= 2, "new episodes must vary actual connected shape structure"


def test_large_query_is_real_30_by_30_input_and_output(adapter):
    for policy in POLICIES:
        pair = adapter.generate(0, {"reflection_policy": policy}, 3, 4)["test"][3]
        assert (len(pair["input"]), len(pair["input"][0])) == (30, 30)
        assert (len(pair["output"]), len(pair["output"][0])) == (30, 30)
        # Four staggered 6x6 objects occupy rows 0..23; row 24 separates
        # a dense 5x5 index. These are semantic regions, not blank padding.
        assert all(any(row) for row in pair["input"][:24])
        assert any(row[29] for row in pair["input"][:24])
        assert any(pair["input"][0]) and any(pair["input"][23])
        assert all(v == 0 for v in pair["input"][24])
        assert all(any(row) for row in pair["input"][25:])
        assert sum(v != 0 for row in pair["input"] for v in row) > 100


def test_query_stream_and_first_turn_do_not_depend_on_future_counts(adapter):
    settings = {"reflection_policy": "larger_left"}
    one = adapter.generate(41, settings, 3, 1)
    four = adapter.generate(41, settings, 3, 4)
    six = adapter.generate(41, settings, 6, 4)
    assert one["train"] == four["train"] == six["train"][:3]
    assert one["test"][0] == four["test"][0] == six["test"][0]
    visible = adapter.prototype.public_turn(four, 0)
    assert visible == adapter.prototype.public_turn(one, 0)
    assert set(visible) == {"train", "test"}
    assert len(visible["test"]) == 1
    assert set(visible["test"][0]) == {"input"}


def test_public_bytes_ignore_private_fields_and_reject_boolean_cells(adapter):
    from reviewer_support import public_challenge_bytes, public_challenge_id
    import hashlib
    e = adapter.generate(3, {"reflection_policy": "canonical"}, 3, 4)
    public = adapter.prototype.public_turn(e, 0)
    raw = public_challenge_bytes(public)
    modified = deepcopy(e)
    modified.update(settings={"reflection_policy": "private"}, seed=-999, program_solution="PRIVATE")
    for pair in modified["test"]:
        pair["output"] = [[9]]
    assert public_challenge_bytes(adapter.prototype.public_turn(modified, 0)) == raw
    assert public_challenge_id(public) == hashlib.sha256(raw).hexdigest()
    public["test"][0]["input"][0][0] = True
    with pytest.raises(ValueError):
        public_challenge_bytes(public)


@pytest.mark.parametrize("settings", [None, {}, {"reflection_policy": True},
    {"reflection_policy": "bad"}, {"reflection_policy": "canonical", "extra": 1}])
def test_invalid_settings_are_rejected(adapter, settings):
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(0, settings, 3, 4)


@pytest.mark.parametrize("field,value", [("seed", True), ("seed", -1), ("seed", 1.5),
    ("demos", 1), ("demos", 7), ("demos", True), ("demos", 3.0),
    ("queries", 0), ("queries", 5), ("queries", False)])
def test_invalid_request_types_and_bounds_fail_instead_of_coercing(adapter, field, value):
    kwargs = dict(seed=0, settings={"reflection_policy": "canonical"}, demos=3, queries=4)
    kwargs[field] = value
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(**kwargs)


def test_invalid_sequential_query_index_is_rejected(adapter):
    e = adapter.generate(0, {"reflection_policy": "canonical"}, 3, 4)
    for index in (-1, 4, True, 0.0):
        with pytest.raises((TypeError, ValueError)):
            adapter.prototype.public_turn(e, index)
